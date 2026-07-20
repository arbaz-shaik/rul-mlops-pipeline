"""Promotion/rejection decision and action.

Consumes the validator's outcome dict, decides promote/reject/insufficient,
acts on the registry (moves the production alias on promote only), and logs
the decision to MLflow and Prometheus. Moving the alias is what closes the
loop: serving adopts the challenger with no redeploy.
"""
import logging

import mlflow

from src.config import settings
from src.serving.metrics import shadow_promotions_total, shadow_rejections_total

log = logging.getLogger(__name__)


def _log_decision(decision, outcome):
    """Record the decision to MLflow (a short run) with CI and version."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    with mlflow.start_run(run_name=f"promotion-{decision}"):
        mlflow.set_tags({"event": "shadow_decision", "decision": decision})
        mlflow.log_param("status", outcome.get("status"))
        if outcome.get("status") == "sufficient":
            lower, upper, point = outcome["ci"]
            mlflow.log_metric("ci_lower", lower)
            mlflow.log_metric("ci_upper", upper)
            mlflow.log_metric("ci_point", point)
            mlflow.log_param("challenger_version", outcome.get("challenger_version"))


def promote_or_reject(outcome):
    """Act on the validator outcome. Returns 'promoted'/'rejected'/'insufficient'."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    status = outcome.get("status")

    # Branch C: insufficient — no decision, no counter, distinct from reject.
    if status == "insufficient":
        log.info("shadow decision: insufficient data (n=%s required=%s), production retained",
                 outcome.get("n"), outcome.get("required"))
        _log_decision("insufficient", outcome)
        return "insufficient"

    lower, upper, point = outcome["ci"]

    # Branch A: sufficient and challenger statistically better (pessimistic tail > 0).
    if lower > 0:
        challenger_version = outcome["challenger_version"]  # read ONLY here
        client = mlflow.MlflowClient()
        client.set_registered_model_alias(
            settings.model_registry_name, settings.model_alias, str(challenger_version)
        )
        log.info("shadow decision: PROMOTED v%s (CI lower %.4f > 0)", challenger_version, lower)
        _log_decision("promoted", outcome)
        shadow_promotions_total.inc()
        return "promoted"

    # Branch B: sufficient but not better (CI includes zero or negative).
    log.info("shadow decision: REJECTED (CI lower %.4f <= 0), production retained", lower)
    _log_decision("rejected", outcome)
    shadow_rejections_total.inc()
    return "rejected"

