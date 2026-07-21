"""Retrainer service HTTP endpoint: the closed-loop seam.

On drift, the detector POSTs a thin signal here. This endpoint runs the three
proven stages in sequence, retrain the challenger, shadow-validate it against
production, and promote or reject, then returns the decision plus the timestamps
needed to measure end-to-end deployment latency.

Two paths (P2 ruling):
  PRODUCTION (experiment=False, default): _fetch_window then _temporal_split,
  exactly as before. Unchanged.
  EXPERIMENT (experiment=True): fetch train windows and the pooled eval set from
  the named scenario via the replay cursor, skipping _temporal_split. Carries the
  detector's measured drift-detection latency into the response for MLflow.
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
    experiment: bool = False
    scenario_path: str | None = None
    detection_latency_s: float | None = None


def _fetch_window():
    """PRODUCTION stand-in: a slice of the prepared arrays. Unused on the
    experiment path; retained for the production path and its tests."""
    from pathlib import Path
    processed = Path(settings.processed_data_dir)
    X = np.load(processed / "x_train.npy")
    y = np.load(processed / "y_train.npy")
    return X[-3000:], y[-3000:]


def _temporal_split(X, y):
    """Older portion trains, newer portion evaluates. Production path only.

    Eval is the newer max(shadow_min_predictions, 30%) rows so the shadow stage
    clears its N-gate when the window is large enough. Not called on the
    experiment path (which supplies train and eval as separate pooled objects).
    """
    n = len(X)
    eval_n = max(settings.shadow_min_predictions, int(n * 0.3))
    eval_n = min(eval_n, n)
    split = n - eval_n
    X_train, y_train = X[:split], y[:split]
    X_eval, y_eval = X[split:], y[split:]
    return X_train, y_train, X_eval, y_eval


@app.post("/retrain")
def retrain(signal: RetrainSignal):
    if signal.experiment:
        from pipeline.replay import load_scenario, ReplayCursor
        scenario = load_scenario(signal.scenario_path)
        cursor = ReplayCursor(scenario)
        X_train, y_train = cursor.retrain_train_fetch()
        X_eval, y_eval = cursor.eval_pool()
    else:
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
        "detection_latency_s": signal.detection_latency_s,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
