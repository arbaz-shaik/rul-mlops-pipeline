"""Compute and persist the reference feature distribution for drift detection.

Runs once. Produces the baseline that Evidently compares incoming batches
against. Does not import Evidently: this module only builds the reference.
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import FEATURE_COLUMNS, settings


def build_reference():
    """Load training windows, validate against the scaler, persist reference."""
    processed_dir = Path(settings.processed_data_dir)
    x_train_path = processed_dir / "X_train.npy"
    scaler_path = processed_dir / "scaler.pkl"
    reference_path = Path(settings.reference_data_path)

    x_train = np.load(x_train_path)
    assert x_train.ndim == 3, f"expected 3D X_train, got shape {x_train.shape}"
    assert x_train.shape[1] == settings.window_size, (
        f"expected window {settings.window_size}, got {x_train.shape[1]}"
    )
    assert x_train.shape[2] == len(FEATURE_COLUMNS), (
        f"expected {len(FEATURE_COLUMNS)} features, got {x_train.shape[2]}"
    )

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    scaler_features = list(scaler.feature_names_in_)
    assert scaler_features == FEATURE_COLUMNS, (
        "scaler feature order does not match FEATURE_COLUMNS: "
        f"{scaler_features} vs {FEATURE_COLUMNS}"
    )

    flattened = x_train.reshape(-1, x_train.shape[2])
    assert flattened.shape[1] == len(FEATURE_COLUMNS), (
        f"last dim {flattened.shape[1]} does not match {len(FEATURE_COLUMNS)}"
    )

    reference = pd.DataFrame(flattened, columns=FEATURE_COLUMNS)

    try:
        reference.to_parquet(reference_path, engine="pyarrow", index=False)
    except Exception as e:
        fallback_path = reference_path.with_suffix(".pkl")
        reference.to_pickle(fallback_path)
        print(f"parquet write failed ({e}), wrote pickle fallback to {fallback_path}")

    return reference


if __name__ == "__main__":
    build_reference()
