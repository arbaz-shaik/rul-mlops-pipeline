"""Retrainer service HTTP endpoint: the closed-loop seam.

Paths:
  PRODUCTION (experiment=False): _fetch_window then _temporal_split.
  EXPERIMENT A/B (experiment=True, condition A or B): fetch disjoint train +
    eval pools from the scenario, retrain, shadow-validate (gate), promote/reject.
  EXPERIMENT C (condition C): keep the drift trigger, retrain, but promote the
    challenger DIRECTLY with no shadow gate. After the latency clock stops, run a
    post-hoc challenger-vs-replaced-baseline comparison PURELY to measure whether
    the promotion was a false promotion, without gating. This isolates the gate's
    contribution: C shows the cost of promoting every challenger.
"""
from datetime import datetime, timezone

import numpy as np
import torch
import mlflow
import mlflow.pytorch
from fastapi import FastAPI
from pydantic import BaseModel

from src.config import settings
from src.retraining.trainer import run_retraining
from src.shadow.validator import validate
from src.shadow.bootstrap import bootstrap_rmse_diff
from src.shadow.promoter import promote_or_reject

app = FastAPI()


class RetrainSignal(BaseModel):
    drift_score: float
    triggered_at: str
    experiment: bool = False
    scenario_path: str | None = None
    detection_latency_s: float | None = None
    condition: str = "A"
    fire_index: int = 0


def _fetch_window():
    """PRODUCTION stand-in. Unused on experiment paths."""
    from pathlib import Path
    processed = Path(settings.processed_data_dir)
    X = np.load(processed / "x_train.npy")
    y = np.load(processed / "y_train.npy")
    return X[-3000:], y[-3000:]


def _temporal_split(X, y):
    """Production path only. Not called on experiment paths."""
    n = len(X)
    eval_n = max(settings.shadow_min_predictions, int(n * 0.3))
    eval_n = min(eval_n, n)
    split = n - eval_n
    return X[:split], y[:split], X[split:], y[split:]


def _current_production_version():
    """Version the production alias currently points at (what C will replace)."""
    c = mlflow.MlflowClient()
    return c.get_model_version_by_alias(settings.model_registry_name, settings.model_alias).version


def _promote_directly(challenger_version):
    """C's ungated promotion: the same alias move A uses, unconditional."""
    c = mlflow.MlflowClient()
    c.set_registered_model_alias(
        settings.model_registry_name, settings.model_alias, str(challenger_version)
    )


def _predict(uri, X):
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    model = mlflow.pytorch.load_model(uri).eval()
    with torch.no_grad():
        out = model(torch.tensor(X, dtype=torch.float32))
    return out.cpu().numpy().ravel()


def _posthoc_false_promotion_check(challenger_version, replaced_version, X_eval, y_eval):
    """OFF the latency clock. Compare the promoted challenger against the baseline
    it REPLACED on the eval pool, purely to record whether the promotion was bad.
    Does not gate (C already promoted). Returns the measurement dict.
    """
    y_true = np.minimum(np.asarray(y_eval, dtype=float).ravel(), settings.rul_cap)
    challenger_preds = _predict(
        f"models:/{settings.model_registry_name}/{challenger_version}", X_eval)
    baseline_preds = _predict(
        f"models:/{settings.model_registry_name}/{replaced_version}", X_eval)
    # CI of replaced_baseline_RMSE - challenger_RMSE: positive => challenger better.
    ci = bootstrap_rmse_diff(
        challenger_preds, baseline_preds, y_true,
        n_resamples=settings.bootstrap_resamples, ci_level=settings.bootstrap_ci_level,
    )
    lower, upper, point = ci
    # False promotion: challenger was NOT better than what it replaced.
    false_promotion = not (lower > 0)
    return {"ci": ci, "false_promotion": bool(false_promotion),
            "replaced_version": replaced_version}


def _log_c_record(signal, challenger_version, promoted_at, posthoc):
    """Per-fire C record: ungated promotion + post-hoc false-promotion truth."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    with mlflow.start_run(run_name=f"exp-C-fire{signal.fire_index}"):
        mlflow.set_tags({
            "event": "experiment_fire", "condition": "C",
            "fire_index": str(signal.fire_index),
            "gated": "false",
            "false_promotion": str(posthoc["false_promotion"]),
        })
        mlflow.log_param("challenger_version", challenger_version)
        mlflow.log_param("replaced_version", posthoc["replaced_version"])
        if signal.detection_latency_s is not None:
            mlflow.log_metric("detection_latency_s", signal.detection_latency_s)
        lower, upper, point = posthoc["ci"]
        mlflow.log_metric("posthoc_ci_lower", lower)
        mlflow.log_metric("posthoc_ci_upper", upper)
        mlflow.log_metric("posthoc_ci_point", point)


def _log_experiment_record(signal, result, eval_rows):
    """A/B per-fire record (gated)."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    with mlflow.start_run(run_name=f"exp-{signal.condition}-fire{signal.fire_index}"):
        mlflow.set_tags({
            "event": "experiment_fire", "condition": signal.condition,
            "fire_index": str(signal.fire_index),
            "decision": result["decision"], "status": result["status"],
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
    if not signal.experiment:
        X, y = _fetch_window()
        X_train, y_train, X_eval, y_eval = _temporal_split(X, y)
        version = run_retraining(X_train, y_train, signal.drift_score)
        outcome = validate(version, X_eval, y_eval)
        decision = promote_or_reject(outcome)
        return {
            "decision": decision, "version": version, "ci": outcome.get("ci"),
            "status": outcome.get("status"), "eval_rows": int(len(X_eval)),
            "triggered_at": signal.triggered_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "detection_latency_s": signal.detection_latency_s,
        }

    # Experiment paths: disjoint pools from the scenario.
    from pipeline.replay import load_scenario, ReplayCursor
    scenario = load_scenario(signal.scenario_path)
    cursor = ReplayCursor(scenario)
    X_train, y_train = cursor.retrain_train_fetch()
    X_eval, y_eval = cursor.eval_pool()

    if signal.condition == "C":
        # C: capture what we're about to replace, retrain, promote DIRECTLY (no gate).
        replaced_version = _current_production_version()
        version = run_retraining(X_train, y_train, signal.drift_score)
        _promote_directly(version)
        completed_at = datetime.now(timezone.utc).isoformat()  # LATENCY CLOCK STOPS HERE
        # Post-hoc (OFF the clock): was the promotion a false promotion?
        posthoc = _posthoc_false_promotion_check(version, replaced_version, X_eval, y_eval)
        _log_c_record(signal, version, completed_at, posthoc)
        return {
            "decision": "promoted_no_gate", "version": version,
            "ci": posthoc["ci"], "status": "sufficient",
            "false_promotion": posthoc["false_promotion"],
            "replaced_version": posthoc["replaced_version"],
            "eval_rows": int(len(X_eval)),
            "triggered_at": signal.triggered_at, "completed_at": completed_at,
            "detection_latency_s": signal.detection_latency_s,
            "condition": "C", "fire_index": signal.fire_index,
        }

    # A / B: gated.
    version = run_retraining(X_train, y_train, signal.drift_score)
    outcome = validate(version, X_eval, y_eval)
    decision = promote_or_reject(outcome)
    completed_at = datetime.now(timezone.utc).isoformat()
    result = {
        "decision": decision, "version": version, "ci": outcome.get("ci"),
        "status": outcome.get("status"), "eval_rows": int(len(X_eval)),
        "triggered_at": signal.triggered_at, "completed_at": completed_at,
        "detection_latency_s": signal.detection_latency_s,
        "condition": signal.condition, "fire_index": signal.fire_index,
    }
    _log_experiment_record(signal, result, int(len(X_eval)))
    return result


@app.get("/health")
def health():
    return {"status": "healthy"}
