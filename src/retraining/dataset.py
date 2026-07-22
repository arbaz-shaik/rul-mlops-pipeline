"""Data-quality blend gate for drift-triggered retraining.

Sits between receiving a drifted window and training on it. If the retrain was
triggered by detected drift, blend in original training data so the retrained
model does not overfit to a small, drift-narrow window (Wong and Perumal 2025).

Blend TRIGGER (corrected): keyed on the drift signal that fired retraining
(drift_score vs the PSI threshold), the SAME drift notion the detector uses, not
on a min/max out-of-distribution range test. The range test (_ood_proportion)
is retained and logged for provenance, but it does NOT gate: the s9 offset that
shifts the distribution enough to fire PSI does not push features outside the
reference min/max range, so the range test reads ~0 on genuinely drifted windows
and would never blend. Keying on drift_score makes the gate fire on the drift
the pipeline actually detects.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import FEATURE_COLUMNS, settings


def _ood_proportion(X_window):
    """Fraction of window timesteps outside the reference per-feature [min,max].

    Retained for provenance/logging only. Does NOT gate blending (see module
    docstring): PSI-detected drift does not necessarily exceed the min/max range,
    so this reads ~0 on drifted windows and is not a reliable blend trigger.
    """
    reference = pd.read_parquet(settings.reference_data_path)
    lo = reference[FEATURE_COLUMNS].min().to_numpy()
    hi = reference[FEATURE_COLUMNS].max().to_numpy()
    flat = X_window.reshape(-1, X_window.shape[2])
    outside = (flat < lo) | (flat > hi)
    row_is_ood = outside.any(axis=1)
    return float(row_is_ood.mean())


def apply_blend_gate(X_window, y_window, settings, drift_score):
    """Conditionally blend the window with original training data.

    Blend TRIGGER: drift_score > settings.psi_drift_threshold (the same drift
    signal the detector uses). ood_proportion is still computed and returned for
    provenance but does not gate.

    Returns (X, y, ood_proportion, blend_applied). run_retraining logs the last
    two into the model's MLflow run.
    """
    ood = _ood_proportion(X_window)  # logged for evidence, not gating
    drift_triggered = drift_score > settings.psi_drift_threshold

    if not drift_triggered:
        # Clean retrain (drift_score below threshold): no blend. Coherent for a
        # clean window, e.g. an ablation-B pre-onset scheduled fire.
        return X_window, y_window, ood, False

    # Drift-triggered: blend original training data in for size and stability.
    processed = Path(settings.processed_data_dir)
    X_orig = np.load(processed / "x_train.npy")
    y_orig = np.load(processed / "y_train.npy")

    # Original data forms retraining_blend_ratio of the FINAL set:
    # m / (n + m) = r  ->  m = n * r / (1 - r).
    n = X_window.shape[0]
    r = settings.retraining_blend_ratio
    m = int(round(n * r / (1 - r)))
    m = min(m, X_orig.shape[0])

    rng = np.random.default_rng(42)  # seeded for reproducibility
    idx = rng.choice(X_orig.shape[0], size=m, replace=False)

    X_blend = np.concatenate([X_window, X_orig[idx]], axis=0)
    y_blend = np.concatenate([y_window, y_orig[idx]], axis=0)
    perm = rng.permutation(X_blend.shape[0])
    return X_blend[perm], y_blend[perm], ood, True
