"""Retrainer service HTTP endpoint: the closed-loop seam.

On drift, the detector POSTs a thin signal here. This endpoint runs the three
proven stages in sequence, retrain the challenger, shadow-validate it against
production, and promote or reject, then returns the decision plus the timestamps
needed to measure end-to-end deployment latency.
"""
from datetime import datetime, timezone

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

from src.config import settings
from src.retraining.trainer import run_retraining
from src.shadow.validator import validate
from src.shadow.promoter import promote_or_reject

app = FastAPI()


class RetrainSignal(BaseModel):
    drift_score: float
    triggered_at: str  # ISO timestamp from the detector when drift fired


def _fetch_window():
    """Fetch the recent stream window.

    STAND-IN: loads a slice of the prepared arrays. The replay-harness block
    will replace this function body with a pull from the replay buffer; keeping
    the fetch isolated here makes that swap a one-function change.
    """
    from pathlib import Path
    processed = Path(settings.processed_data_dir)
    X = np.load(processed / "x_train.npy")
    y = np.load(processed / "y_train.npy")
    # a recent-ish window large enough that a temporal split leaves >=500 for eval
    return X[-3000:], y[-3000:]


def _temporal_split(X, y):
    """Older portion trains, newer portion evaluates (Fork 2, option b).

    Eval is the newer max(shadow_min_predictions, 30%) rows so the shadow stage
    clears its N-gate when the window is large enough.
    """
    n = len(X)
    eval_n = max(settings.shadow_min_predictions, int(n * 0.3))
    eval_n = min(eval_n, n)  # cannot exceed what exists
    split = n - eval_n
    X_train, y_train = X[:split], y[:split]
    X_eval, y_eval = X[split:], y[split:]
    return X_train, y_train, X_eval, y_eval


@app.post("/retrain")
def retrain(signal: RetrainSignal):
    X, y = _fetch_window()
    X_train, y_train, X_eval, y_eval = _temporal_split(X, y)

    version = run_retraining(X_train, y_train, signal.drift_score)
    outcome = validate(version, X_eval, y_eval)
    decision = promote_or_reject(outcome)

    completed_at = datetime.now(timezone.utc).isoformat()
    return {
        "decision": decision,
        "version": version,
        "ci": outcome.get("ci"),
        "status": outcome.get("status"),
        "eval_rows": int(len(X_eval)),
        "triggered_at": signal.triggered_at,
        "completed_at": completed_at,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
