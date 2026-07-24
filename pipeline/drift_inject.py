"""Deterministic drift injection on the s9 sensor column.

Given clean scaled rows, returns rows with an offset added to s9 only. Offset =
k * sigma_s9, sigma in the normalised space the detector compares in, so
intensity is in sensor-sigma units. Never touches RUL labels. Byte-identical for
fixed inputs.

Modes:
  none:    unchanged.
  sudden:  step offset k*sigma from row D onward.
  gradual: same mechanism as sudden, but the CALLER passes the per-batch ramped
           k. inject applies whatever k it is given as a step on this batch;
           _build_detection_batches computes the linear ramp k*(b-onset+1)/n_drift
           per drifted batch and calls inject with that scaled k. The ramp lives
           in the caller (which knows the batch index); inject just applies the
           given offset. This keeps the ramp schedule and the offset application
           in one place each, and lets inject stop raising on 'gradual'.
"""
import numpy as np

from src.config import FEATURE_COLUMNS

S9_INDEX = FEATURE_COLUMNS.index("s9")  # resolved, not hardcoded (currently 5)


def compute_sigma_s9(x_train_rows):
    """Std of the s9 column across all scaled rows. Returns a scalar float."""
    return float(np.std(x_train_rows[:, S9_INDEX]))


def inject(clean_rows, drift_type, k, D, sigma_s9, seed=42, s9_index=S9_INDEX):
    """Return rows with drift applied. clean_rows (N,14) is not mutated.

    none:            unchanged copy.
    sudden | gradual: copy, then rows[D:, s9_index] += k * sigma_s9. For gradual
                      the caller passes the per-batch ramped k; inject applies it
                      as a step on the batch it is given.
    other:           ValueError (recurring/concept are later blocks; fail loud).

    Returns a fresh array (copy), never a view.
    """
    rows = np.array(clean_rows, dtype=np.float64, copy=True)
    if drift_type == "none":
        return rows
    if drift_type in ("sudden", "gradual", "recurring"):
        rows[D:, s9_index] += k * sigma_s9
        return rows
    raise ValueError(
        f"unsupported drift_type {drift_type!r} (expected none|sudden|gradual|recurring)")
