"""Retrainer service HTTP endpoint: the closed-loop seam.

On drift (A) or schedule (B), the detector POSTs a thin signal here. This
endpoint runs the proven stages, retrain the challenger, shadow-validate against
production, promote or reject, then returns the decision plus timestamps for
end-to-end deployment latency.

Paths:
  PRODUCTION (experiment=False, default): _fetch_window then _temporal_split.
  EXPERIMENT (experiment=True): fetch train windows and pooled eval from the
  named scenario via replay, skip _temporal_split. Logs a per-fire experiment
  record tagged with condition (A/B/C) and fire_index so B's metric series is
  queryable alongside A's single point. Carries the detector's drift-detection
  latency (null for B).
"""
from datetime import datetime, timezone

import numpy as np
import mlflow
from fastapi import FastAPI
from pydantic import BaseModel

from src.config import settings
from src.retraining.trainer import run_retraining
from src.shadow.validator import validate
from src.shadow.promoter import promote_or_reject

app = FastAPI()


class RetrainSignal(BaseModel):
    drift_score: float
    triggered_at: str  # ISO timestamp from the detector when the fire occurred
    experiment: bool = False
    scenario_path: str | None = None
    detection_latency_s: float | None = None
    condition: str = "A"
    fire_index: int = 0


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

    Eval is the newer max(shadow_min_predictions, 30%) rows. Not called on the
    experiment path (which supplies train and eval as separate pooled objects).
    """
    n = len(X)
    eval_n = max(settings.shadow_min_predictions, int(n * 0.3))
    eval_n = min(eval_n, n)
    split = n - eval_n
    return X[:split], y[:split], X[split:], y[split:]


def _log_experiment_record(signal, result, eval_rows):
    """Per-fire experiment record: one MLflow run tagged with condition and
    fire_index, holding the five-metric-relevant values in hand at the seam.
    Gives B's per-fire series (and A's single point) a queryable label without
    touching the promoter or trainer signatures.
    """
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    with mlflow.start_run(run_name=f"exp-{signal.condition}-fire{signal.fire_index}"):
        mlflow.set_tags({
            "event": "experiment_fire",
            "condition": signal.condition,
            "fire_index": str(signal.fire_index),
            "decision": result["decision"],
            "status": result["status"],
        })
        mlflow.log_param("challenger_version", result["version"])
        mlflow.log_param("eval_rows", eval_rows)
        if signal.detection_latency_s is not None:
            mlflow.log_metric("detection_latency_s", signal.detection_latency_s)
        if result.get("ci"):
            lower, upper, point = result["ci"]
            mlflow.log_metric("ci_lower", lower)
            mlflow.log_metric("ci_upper", upper)
            mlflow.log_metric("ci_point", point)


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
    result = {
        "decision": decision,
        "version": version,
        "ci": outcome.get("ci"),
        "status": outcome.get("status"),
        "eval_rows": int(len(X_eval)),
        "triggered_at": signal.triggered_at,
        "completed_at": completed_at,
        "detection_latency_s": signal.detection_latency_s,
        "condition": signal.condition,
        "fire_index": signal.fire_index,
    }

    if signal.experiment:
        _log_experiment_record(signal, result, int(len(X_eval)))

    return result


@app.get("/health")
def health():
    return {"status": "healthy"}
