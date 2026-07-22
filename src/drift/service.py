"""Continuous drift-detector service.

The always-on watcher. On an interval it reads the current stream window, runs
drift detection, and on drift POSTs a thin signal to the retrainer's /retrain
endpoint (fire-and-block: waits for the decision, logs it, resumes). It never
sends its window; the retrainer fetches its own data.

Modes:
  PRODUCTION (default): reads live stream via _read_stream_window on an interval.
  EXPERIMENT A (SCENARIO_PATH set, default): replays a scenario's detection
  batches, fires on the first PSI crossing, records drift-detection latency.
  ABLATION B (SCENARIO_PATH + CRON set): replays the same batches but fires on a
  fixed schedule (every drift_cron_k batches), NOT on drift. Fires multiple times,
  one full retrain/shadow/promote cycle per fire, so B logs a metric SERIES where
  A logs a point. Drift-detection latency is null for B (no trigger). B keeps the
  shadow gate; it differs from A only at initiation timing.
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


def _fire(drift_score, scenario_path=None, experiment=False, detection_latency_s=None,
          condition="A", fire_index=0):
    """POST the thin signal to the retrainer and block for the decision.

    Carries scenario_path (retrainer replays the same scenario), experiment flag
    (P2 path), detection latency (null for B), and the condition/fire_index so the
    retrainer tags each MLflow run, giving B's per-fire series a queryable label.
    """
    payload = {
        "drift_score": float(drift_score),
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "experiment": bool(experiment),
        "scenario_path": scenario_path,
        "detection_latency_s": detection_latency_s,
        "condition": condition,
        "fire_index": int(fire_index),
    }
    log.info("fire (cond %s idx %d, score %.4f), POSTing to %s",
             condition, fire_index, drift_score, settings.retrainer_url)
    resp = requests.post(settings.retrainer_url, json=payload, timeout=1800)
    resp.raise_for_status()
    decision = resp.json()
    log.info("retrainer decision: %s", decision)
    return decision


def run_experiment_loop(scenario_path):
    """CONDITION A: replay batches, fire on first PSI crossing, record latency.

    Fires once, returns the decision (one onset per scenario)."""
    from pipeline.replay import load_scenario, ReplayCursor

    scenario = load_scenario(scenario_path)
    cursor = ReplayCursor(scenario)
    onset = cursor.onset_batch()
    interval = scenario["batch_interval_s"]
    log.info("A replay: %d batches, onset at %d, interval %ss",
             cursor.n_batches(), onset, interval)

    for i in range(cursor.n_batches()):
        per_feature, aggregate = compute_drift(cursor.detector_batch(i))
        fired = check_drift(per_feature, aggregate)
        log.info("batch %d PSI %.4f fired=%s", i, aggregate, fired)
        if fired:
            latency = max(0, i - onset) * interval
            log.info("A crossing batch %d, detection latency %.1fs", i, latency)
            return _fire(aggregate, scenario_path=scenario_path, experiment=True,
                         detection_latency_s=latency, condition="A", fire_index=0)
    log.warning("A: no batch crossed threshold; no fire")
    return None


def run_cron_loop(scenario_path):
    """ABLATION B: replay batches, fire on a fixed schedule (every drift_cron_k),
    NOT on drift. Fires multiple times, one full cycle per fire, returns the list
    of per-fire decisions (B's series). Drift-detection latency null throughout.

    B keeps the shadow gate; it differs from A only at initiation. The PSI trigger
    is not consulted here (check_drift is never called), so no drift-initiated
    retrain can contaminate B. The batch PSI is still computed and logged for
    provenance, but it does not gate the fire.
    """
    from pipeline.replay import load_scenario, ReplayCursor

    scenario = load_scenario(scenario_path)
    cursor = ReplayCursor(scenario)
    onset = cursor.onset_batch()
    k = settings.drift_cron_k
    log.info("B cron: %d batches, onset at %d, firing every %d batches (no drift gate)",
             cursor.n_batches(), onset, k)

    decisions = []
    fire_index = 0
    for i in range(cursor.n_batches()):
        # compute PSI for provenance/logging only; it does NOT gate the fire
        per_feature, aggregate = compute_drift(cursor.detector_batch(i))
        is_fire_batch = (i > 0 and i % k == 0)
        pre_onset = i < onset
        if is_fire_batch:
            log.info("B fire at batch %d (idx %d, PSI %.4f, %s)",
                     i, fire_index, aggregate,
                     "PRE-ONSET clean" if pre_onset else "post-onset drifted")
            decision = _fire(aggregate, scenario_path=scenario_path, experiment=True,
                             detection_latency_s=None, condition="B", fire_index=fire_index)
            decisions.append({"fire_index": fire_index, "batch": i,
                              "pre_onset": pre_onset, "decision": decision})
            fire_index += 1
    log.info("B complete: %d fires at batches %s",
             len(decisions), [d["batch"] for d in decisions])
    return decisions


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
    cron = os.environ.get("CRON")
    if scenario_path and cron:
        run_cron_loop(scenario_path)
    elif scenario_path:
        run_experiment_loop(scenario_path)
    else:
        run_detector_loop()
