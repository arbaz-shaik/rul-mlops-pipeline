"""Deterministic drift injection on the s9 sensor column.

Base of the replay harness. Given clean scaled rows, returns rows with a
constant offset added to s9 only, from row D onward (sudden), or unchanged
(none). Offset = k * sigma_s9, sigma measured in the same normalised space the
detector compares in, so intensity is in sensor-sigma units, independent of raw
scale. Never touches RUL labels: labels travel separately, so true RUL is
unchanged and only the sensor reading shifts. Byte-identical for fixed inputs.
"""
import numpy as np

from src.config import FEATURE_COLUMNS

S9_INDEX = FEATURE_COLUMNS.index("s9")  # resolved, not hardcoded (currently 5)


def compute_sigma_s9(x_train_rows):
    """Std of the s9 column across all scaled rows.

    x_train_rows: (N, 14) float in normalised space. Returns a scalar float.
    Computed once by the harness and passed into inject, so one sigma is reused
    for every scenario and logged with the run.
    """
    return float(np.std(x_train_rows[:, S9_INDEX]))


def inject(clean_rows, drift_type, k, D, sigma_s9, seed=42, s9_index=S9_INDEX):
    """Return rows with drift applied. clean_rows (N,14) is not mutated.

    none:   unchanged copy.
    sudden: copy, then rows[D:, s9_index] += k * sigma_s9.
    other:  ValueError (gradual/recurring are a later block; fail loud rather
            than silently no-op).

    Returns a fresh array (copy), never a view, so the caller can reuse
    clean_rows for the paired none/sudden scenarios. seed is accepted for a
    uniform signature across the harness; sudden/none injection is a pure
    deterministic array op with no RNG.
    """
    rows = np.array(clean_rows, dtype=np.float64, copy=True)
    if drift_type == "none":
        return rows
    if drift_type == "sudden":
        rows[D:, s9_index] += k * sigma_s9
        return rows
    raise ValueError(f"unsupported drift_type {drift_type!r} (expected none|sudden)")
