"""Per-row RUL reconstruction, the provenance gate, and capped served labels.

TWO OPERATIONS, ORDER FIXED (do not collapse):
  Step 1 provenance gate (UNCAPPED): reconstruct per-row RUL uncapped
    (max_cycle - cycle), window stride-1 per engine, terminal-row label, assert
    element-wise equality against raw y_train.npy. Proves the reconstruction is
    the correct function AND that row-to-label alignment is right. Must be
    uncapped: raw y_train.npy is uncapped, and capping would flatten the ~30% of
    windows above the cap to a constant, blinding the alignment check there.
  Step 2 served labels (CAPPED): only after Step 1 passes, apply
    np.minimum(reconstructed_rul, settings.rul_cap) to produce the labels the
    harness serves. This matches the capped target every model is trained and
    evaluated against (B' ruling).

Also runs the FEATURE gate (scaler.pkl reproduces x_train.npy), confirmed 0.0.

CHANNELS (both explicit): features come from raw -> FEATURE_COLUMNS ->
scaler.transform (verified bit-identical to x_train.npy). Labels come from raw
cycle counts (no scaler). Raw is read solely for label reconstruction.
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import FEATURE_COLUMNS, settings
from pipeline.preprocess import load_raw

_WIN = settings.window_size
_PROCESSED = Path(settings.processed_data_dir)


def reconstruct_per_row(raw_train_filename="train_FD001.txt"):
    """Return (units (R,), scaled_features (R,14), rul_uncapped (R,)) in raw order.

    features: raw[FEATURE_COLUMNS] -> current scaler.pkl transform.
    labels:   per engine, RUL(row) = max_cycle - cycle  (UNCAPPED; the cap is a
              separate later step, never applied here).
    """
    raw_path = Path(settings.raw_data_dir) / raw_train_filename
    df = load_raw(raw_path)

    with open(_PROCESSED / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    assert list(scaler.feature_names_in_) == FEATURE_COLUMNS, (
        f"scaler order {list(scaler.feature_names_in_)} != {FEATURE_COLUMNS}"
    )
    feats = scaler.transform(df[FEATURE_COLUMNS]).astype(np.float64)

    rul = np.empty(len(df), dtype=np.int64)
    for u in pd.unique(df["unit"]):
        mask = (df["unit"] == u).to_numpy()
        cyc = df.loc[mask, "cycle"].to_numpy()
        rul[mask] = cyc.max() - cyc            # UNCAPPED
    return df["unit"].to_numpy(), feats, rul


def _window_per_engine(units, rows, rul):
    """Window stride-1 within each engine (matches create_windowed_features).

    y = terminal-row RUL, engines in pandas unique() order. This is the GATE
    windowing (engine-aware). The scenario stream windowing is different
    (contiguous, no engines); do not reuse this for the scenario.
    """
    Xs, ys = [], []
    for u in pd.unique(units):
        idx = np.where(units == u)[0]
        er, el = rows[idx], rul[idx]
        for i in range(len(er) - _WIN + 1):
            Xs.append(er[i:i + _WIN])
            ys.append(el[i + _WIN - 1])
    return np.stack(Xs), np.array(ys, dtype=np.int64)


def run_gates():
    """Step 1 provenance gate (uncapped) + feature gate. Raise on failure.

    Returns (units, feats, rul_uncapped) for downstream capped-label derivation,
    plus a printed report. Does NOT cap anything; capping is derive_served_labels.
    """
    units, feats, rul = reconstruct_per_row()
    Xr, yr = _window_per_engine(units, feats, rul)

    x_train = np.load(_PROCESSED / "x_train.npy")
    y_train = np.load(_PROCESSED / "y_train.npy")   # raw, uncapped on disk

    assert Xr.shape == x_train.shape, f"window shape differs: {Xr.shape} vs {x_train.shape}"
    assert yr.shape == y_train.shape, f"label count differs: {yr.shape} vs {y_train.shape}"

    label_ok = bool(np.array_equal(yr, y_train))          # UNCAPPED vs raw y_train
    feat_maxdiff = float(np.abs(Xr - x_train).max())
    feature_ok = feat_maxdiff <= 1e-6

    print("GATE REPORT:", {
        "nwin": int(len(yr)), "label_ok": label_ok,
        "feature_ok": feature_ok, "feat_maxdiff": feat_maxdiff,
    })

    if not label_ok:
        first = int(np.argmax(yr != y_train))
        raise AssertionError(
            f"STEP 1 PROVENANCE GATE FAILED at window {first}: "
            f"recon={int(yr[first])} y_train={int(y_train[first])}."
        )
    if not feature_ok:
        raise AssertionError(f"FEATURE GATE FAILED: max abs diff {feat_maxdiff} > 1e-6")
    return units, feats, rul


def derive_served_labels(rul_uncapped):
    """Step 2: cap the provenance-verified uncapped per-row RUL to the served
    target. Call ONLY after run_gates has passed."""
    return np.minimum(rul_uncapped, settings.rul_cap)


if __name__ == "__main__":
    _units, _feats, _rul = run_gates()
    _served = derive_served_labels(_rul)
    print("Step 2 served labels: capped at", settings.rul_cap,
          "| max served", int(_served.max()),
          "| max uncapped", int(_rul.max()),
          "| count capped", int((_rul > settings.rul_cap).sum()))
