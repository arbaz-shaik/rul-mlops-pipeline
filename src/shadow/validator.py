"""Shadow validation orchestrator.

Runs the challenger and the current production model on the same evaluation
batch, collects paired predictions, and (if enough predictions) computes the
RMSE-difference CI via bootstrap_rmse_diff. Gathers evidence only; the promoter
decides promote/reject/rollback.
"""
import numpy as np
import torch
import mlflow.pytorch

from src.config import settings
from src.shadow.bootstrap import bootstrap_rmse_diff
from src.serving.metrics import shadow_min_predictions_hit


def _load(uri):
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    return mlflow.pytorch.load_model(uri).eval()


def _predict(model, X):
    with torch.no_grad():
        out = model(torch.tensor(X, dtype=torch.float32))
    return out.cpu().numpy().ravel()


def validate(challenger_version, X_eval, y_eval):
    """Run production and challenger on X_eval, return a first-class outcome.

    Returns one of:
      {"status": "insufficient", "n": <int>, "required": <int>}
      {"status": "sufficient", "ci": (lower, upper, point),
       "challenger_version": <int>}
    Both are normal returns; insufficient is not an exception.
    """
    n = len(X_eval)
    required = settings.shadow_min_predictions
    if n < required:
        return {"status": "insufficient", "n": n, "required": required}

    # Window met: mark it on the Prometheus counter (object owned by metrics.py).
    shadow_min_predictions_hit.inc()

    production = _load(f"models:/{settings.model_registry_name}@{settings.model_alias}")
    challenger = _load(f"models:/{settings.model_registry_name}/{challenger_version}")

    production_preds = _predict(production, X_eval)
    shadow_preds = _predict(challenger, X_eval)

    # Evaluate on the CAPPED target. Every registered model (champion v3 and all
    # challengers) is trained via train_model, which caps labels at
    # settings.rul_cap. The RMSE comparison must use the same capped target the
    # models learned, or it would score them against a target neither was trained
    # on and bias production_RMSE - shadow_RMSE by an unknown amount.
    y_true = np.minimum(np.asarray(y_eval, dtype=float).ravel(), settings.rul_cap)

    ci = bootstrap_rmse_diff(
        shadow_preds, production_preds, y_true,
        n_resamples=settings.bootstrap_resamples,
        ci_level=settings.bootstrap_ci_level,
    )
    return {
        "status": "sufficient",
        "ci": ci,                       # (lower, upper, point); positive = challenger better
        "challenger_version": challenger_version,
    }
