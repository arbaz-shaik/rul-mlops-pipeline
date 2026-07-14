"""Re-fit the MinMaxScaler under pinned scikit-learn 1.4.2 from the raw source.

The processed x_train.npy is already normalised to [0,1], so it cannot fit a
scaler. The raw FD001 training file is the only valid fit source. This removes
the InconsistentVersionWarning by regenerating the artefact in the pinned env.
"""
import pickle
import shutil
from pathlib import Path

import numpy as np

from src.config import FEATURE_COLUMNS, settings
from pipeline.preprocess import load_raw, fit_scaler


def refit_scaler():
    raw_path = Path(settings.raw_data_dir) / "train_FD001.txt"
    scaler_path = Path(settings.processed_data_dir) / "scaler.pkl"
    x_train_path = Path(settings.processed_data_dir) / "x_train.npy"

    if scaler_path.exists():
        shutil.copy(scaler_path, scaler_path.with_suffix(".pkl.bak"))

    df = load_raw(raw_path)
    scaler = fit_scaler(df, FEATURE_COLUMNS)

    assert list(scaler.feature_names_in_) == FEATURE_COLUMNS, (
        f"scaler features {list(scaler.feature_names_in_)} != {FEATURE_COLUMNS}"
    )

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    transformed = scaler.transform(df[FEATURE_COLUMNS].to_numpy())
    assert transformed.min() >= -1e-6 and transformed.max() <= 1 + 1e-6, (
        f"re-fit scaler produced out-of-range values: "
        f"min {transformed.min()}, max {transformed.max()}"
    )
    x_train = np.load(x_train_path)
    print(
        f"re-fit transformed range [{transformed.min():.4f}, {transformed.max():.4f}], "
        f"X_train range [{x_train.min():.4f}, {x_train.max():.4f}]"
    )

    return scaler


if __name__ == "__main__":
    refit_scaler()


