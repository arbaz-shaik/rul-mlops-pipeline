"""Data-quality blend gate for drift-triggered retraining.

Sits between receiving a drifted window and training on it. If too much of
the window falls outside the training baseline distribution, blend in original
training data so the retrained model does not overfit to transient drift
(Wong and Perumal 2025). Otherwise pass the window through unchanged.

OOD is measured against the Block 37 reference distribution (2D, flattened
timesteps). Blending draws from the original training WINDOWS (x_train.npy),
because train_model consumes 3D windows, not flattened rows.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import FEATURE_COLUMNS, settings


def _ood_proportion(X_window):
    """Fraction of window timesteps that fall outside the reference range.

    METHODOLOGY ASSUMPTION (flag for Phase Planner):
    - Reference bounds are the per-feature [min, max] of reference_data.parquet.
    - A flattened timestep row is OOD if ANY of its 14 features is outside that
      feature's reference range.
    - ood_proportion = OOD rows / total rows.
    Alternatives (not chosen): percentile bounds instead of min/max;
    majority-of-features instead of any-feature.
    """
    reference = pd.read_parquet(settings.reference_data_path)
    lo = reference[FEATURE_COLUMNS].min().to_numpy()
    hi = reference[FEATURE_COLUMNS].max().to_numpy()

    # (n, 30, 14) -> (n*30, 14) for the distributional check
    flat = X_window.reshape(-1, X_window.shape[2])
    outside = (flat < lo) | (flat > hi)      # per-cell OOD, shape (n*30, 14)
    row_is_ood = outside.any(axis=1)          # any feature outside -> row OOD
    return float(row_is_ood.mean())


def apply_blend_gate(X_window, y_window, settings):
    """Conditionally blend the window with original training data.

    Returns (X, y, ood_proportion, blend_applied). run_retraining logs the
    last two into the model's MLflow run for provenance.
    """
    ood = _ood_proportion(X_window)

    # Gate: only blend when the window is drift-dominated.
    if ood <= 0.5:
        return X_window, y_window, ood, False

    # Blend. Load original training WINDOWS (not the flattened parquet).
    processed = Path(settings.processed_data_dir)
    X_orig = np.load(processed / "x_train.npy")
    y_orig = np.load(processed / "y_train.npy")

    # RATIO ASSUMPTION (flag): original data forms retraining_blend_ratio of the
    # FINAL set. For a window of n rows and target ratio r, add m originals where
    # m / (n + m) = r  ->  m = n * r / (1 - r).
    n = X_window.shape[0]
    r = settings.retraining_blend_ratio
    m = int(round(n * r / (1 - r)))
    m = min(m, X_orig.shape[0])  # cannot sample more than exist

    rng = np.random.default_rng(42)  # seeded for reproducibility
    idx = rng.choice(X_orig.shape[0], size=m, replace=False)

    X_blend = np.concatenate([X_window, X_orig[idx]], axis=0)
    y_blend = np.concatenate([y_window, y_orig[idx]], axis=0)

    # Shuffle the blended set (seeded) so originals are not all at the tail.
    perm = rng.permutation(X_blend.shape[0])
    return X_blend[perm], y_blend[perm], ood, True
