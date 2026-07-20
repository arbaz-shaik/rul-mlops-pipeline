"""Bootstrap confidence interval on the RMSE difference between two models.

Pure statistics: no MLflow, no model loading. Given paired predictions from
the production and shadow models on the same points, plus the true labels,
returns a CI on (production_RMSE - shadow_RMSE). Positive means shadow is
better. The promoter uses the lower bound to decide promotion.
"""
import numpy as np

from src.config import settings


def _rmse(pred, true):
    return np.sqrt(np.mean((pred - true) ** 2))


def bootstrap_rmse_diff(shadow_preds, production_preds, y_true,
                        n_resamples=None, ci_level=None, seed=None):
    """Bootstrap CI on production_RMSE - shadow_RMSE (positive = shadow better).

    Resamples INDICES once per iteration and applies the same index array to
    all three inputs, so each (shadow, production, truth) triple stays paired.
    Independent resampling of each array would destroy the pairing and make the
    difference meaningless.

    seed makes the resampling reproducible: the experiment runner can fix or
    vary it per repeat so promotion decisions are deterministic (needed for the
    Phase 6 false-promotion-rate measurement). Defaults to settings.bootstrap_seed
    if present, else 42.

    Returns (lower_bound, upper_bound, point_estimate).
    """
    shadow_preds = np.asarray(shadow_preds, dtype=float).ravel()
    production_preds = np.asarray(production_preds, dtype=float).ravel()
    y_true = np.asarray(y_true, dtype=float).ravel()

    n = len(y_true)
    assert len(shadow_preds) == n and len(production_preds) == n, (
        "shadow_preds, production_preds, y_true must be the same length"
    )

    B = n_resamples if n_resamples is not None else settings.bootstrap_resamples
    level = ci_level if ci_level is not None else settings.bootstrap_ci_level
    if seed is None:
        seed = getattr(settings, "bootstrap_seed", 42)

    rng = np.random.default_rng(seed)
    diffs = np.empty(B, dtype=float)
    for b in range(B):
        idx = rng.integers(0, n, size=n)          # resample INDICES with replacement
        prod_rmse = _rmse(production_preds[idx], y_true[idx])
        shad_rmse = _rmse(shadow_preds[idx], y_true[idx])
        diffs[b] = prod_rmse - shad_rmse           # positive => shadow better

    alpha = 1.0 - level
    lower = float(np.percentile(diffs, 100 * (alpha / 2)))        # 2.5th
    upper = float(np.percentile(diffs, 100 * (1 - alpha / 2)))    # 97.5th
    point = float(diffs.mean())
    return lower, upper, point
