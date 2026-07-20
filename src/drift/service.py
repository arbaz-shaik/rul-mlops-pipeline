"""Continuous drift-detector service.

The always-on watcher. On an interval it reads the current stream window,
runs drift detection, and on drift POSTs a thin signal to the retrainer's
/retrain endpoint (fire-and-block: it waits for the decision, logs it, then
resumes). It never sends its window; the retrainer fetches its own data.
"""
import logging
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
    """Read the current stream window to check for drift.

    STAND-IN: returns a slice of the prepared arrays as a DataFrame labelled
    with FEATURE_COLUMNS, which is what compute_drift expects (same 2D flattened
    form as the Block 37 reference). The replay-harness block replaces this body
    with a pull from the replay buffer; keeping it isolated makes that a
    one-function swap. This is a separate fetch from the retrainer's own window
    (thin-POST design: detector detects, retrainer sources its own data).
    """
    processed = Path(settings.processed_data_dir)
    X = np.load(processed / "x_train.npy")
    window = X[-settings.shadow_min_predictions:]
    flat = window.reshape(-1, window.shape[2])       # (n,30,14) -> (n*30,14)
    return pd.DataFrame(flat, columns=FEATURE_COLUMNS)


def _fire(drift_score):
    """POST the thin drift signal to the retrainer and block for the decision."""
    payload = {
        "drift_score": float(drift_score),
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }
    log.info("drift fired (score %.4f), POSTing to %s", drift_score, settings.retrainer_url)
    resp = requests.post(settings.retrainer_url, json=payload, timeout=1800)
    resp.raise_for_status()
    decision = resp.json()
    log.info("retrainer decision: %s", decision)
    return decision


def run_detector_loop():
    """Continuous loop: check drift on an interval, fire-and-block on drift."""
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
    run_detector_loop()
