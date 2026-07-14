import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

def create_windowed_features(df, feature_cols, window_size=30):
    sensor_data = df[feature_cols].to_numpy()
    rul_data = df['RUL'].to_numpy()

    x = []
    y = []

    for engine_id in df['unit'].unique():
        engine_data = sensor_data[df['unit'] == engine_id]
        engine_rul = rul_data[df['unit'] == engine_id]

        for i in range(len(engine_data) - window_size + 1):
            x.append(engine_data[i:i + window_size])
            y.append(engine_rul[i + window_size - 1])

    return np.array(x), np.array(y)

def apply_scaler(df,scaler, feature_cols):
    df = df.copy()
    df[feature_cols] = scaler.transform(df[feature_cols])
    return df


def fit_scaler(df, feature_cols):
    scaler = MinMaxScaler()
    scaler.fit(df[feature_cols])
    return scaler



RAW_COLUMNS = ["unit", "cycle", "os1", "os2", "os3"] + [f"s{i}" for i in range(1, 22)]


def load_raw(path):
    """Load a headerless space-delimited CMAPSS file with canonical column names.

    Single source of truth for raw CMAPSS loading. Names match the original
    EDA preprocessing: unit, cycle, os1..os3, s1..s21.
    """
    return pd.read_csv(path, sep=r"\s+", header=None, names=RAW_COLUMNS)