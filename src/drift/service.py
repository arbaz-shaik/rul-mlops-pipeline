"""Continuous drift-detector service.

The always-on watcher. On an interval it reads the current stream window, runs
drift detection, and on drift POSTs a thin signal to the retrainer's /retrain
endpoint (fire-and-block: waits for the decision, logs it, resumes). It never
sends its window; the retrainer fetches its own data.

Two modes:
  PRODUCTION (default): reads live stream via _read_stream_window on an interval.
  EXPERIMENT (SCENARIO_PATH set): replays a scenario's detection batches, one per
  loop tick, firing on the first threshold-crossing batch. Records drift-detection
  latency = (crossing_batch - onset_batch) * batch_interval and passes it, plus
  the scenario path and experiment flag, in the fire payload so the retrainer uses
  the replay (P2) path and MLflow captures latency.
"""
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from src.config import FEATURE_COLUMNS, settings
from src.drift.detector import compute_drift
from src.drift.trigger import check_drift

logging.basicConfig(level=settings.log_level)
log = logging.getLogger(__name__)


def _read_stream_window():
    """PRODUCTION stand-in: a slice of prepared arrays as a FEATURE_COLUMNS
    DataFrame (2D flattened, matching the reference). Unused on the experiment
    path; retained for the production loop and its tests."""
    processed = Path(settings.processed_data_dir)
    X = np.load(processed / "x_train.npy")
    window = X[-settings.shadow_min_predictions:]
    flat = window.reshape(-1, window.shape[2])
    return pd.DataFrame(flat, columns=FEATURE_COLUMNS)


def _fire(drift_score, scenario_path=None, experiment=False, detection_latency_s=None):
    """POST the thin drift signal to the retrainer and block for the decision.

    On the experiment path, carries scenario_path (so the retrainer replays the
    same scenario), the experiment flag (so it uses the P2 path), and the measured
    detection latency (so MLflow records metric 1 at the seam).
    """
    payload = {
        "drift_score": float(drift_score),
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "experiment": bool(experiment),
        "scenario_path": scenario_path,
        "detection_latency_s": detection_latency_s,
    }
    log.info("drift fired (score %.4f), POSTing to %s", drift_score, settings.retrainer_url)
    resp = requests.post(settings.retrainer_url, json=payload, timeout=1800)
    resp.raise_for_status()
    decision = resp.json()
    log.info("retrainer decision: %s", decision)
    return decision


def run_experiment_loop(scenario_path):
    """Replay a scenario's detection batches, fire on first crossing batch.

    One batch per tick. Latency is quantised to the batch interval:
    (crossing_batch - onset_batch) * batch_interval_s. Fires once, returns the
    decision (experiments run one onset per scenario).
    """
    from pipeline.replay import load_scenario, ReplayCursor

    scenario = load_scenario(scenario_path)
    cursor = ReplayCursor(scenario)
    onset = cursor.onset_batch()
    interval = scenario["batch_interval_s"]
    log.info("experiment replay: %d batches, onset at %d, interval %ss",
             cursor.n_batches(), onset, interval)

    for i in range(cursor.n_batches()):
        per_feature, aggregate = compute_drift(cursor.detector_batch(i))
        fired = check_drift(per_feature, aggregate)
        log.info("batch %d aggregate PSI %.4f fired=%s", i, aggregate, fired)
        if fired:
            latency = max(0, i - onset) * interval
            log.info("crossing batch %d, detection latency %.1fs", i, latency)
            return _fire(aggregate, scenario_path=scenario_path,
                         experiment=True, detection_latency_s=latency)
        time.sleep(0)  # no real wait in replay; interval is the metric unit
    log.warning("no batch crossed threshold; no fire")
    return None


def run_detector_loop():
    """PRODUCTION loop: check drift on an interval, fire-and-block on drift."""
    log.info("drift-detector starting, interval %ss, target %s",
             settings.drift_check_interval_s, settings.retrainer_url)
    while True:
        window = _read_stream_window()
        per_feature, aggregate = compute_drift(window)
        if check_drift(per_feature, aggregate):
            _fire(aggregate)
        else:
            log.info("no drift (aggregate %.4f), sleeping %ss",
                     aggregate, settings.drift_check_interval_s)
        time.sleep(settings.drift_check_interval_s)


if __name__ == "__main__":
    scenario_path = os.environ.get("SCENARIO_PATH")
    if scenario_path:
        run_experiment_loop(scenario_path)
    else:
        run_detector_loop()
