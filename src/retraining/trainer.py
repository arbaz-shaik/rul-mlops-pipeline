"""LSTM training and drift-triggered retraining.

train_model is pure: it takes prepared (X, y), trains, and returns the model
plus metrics. It does not load data, register, or write files. Both the
baseline entry point and run_retraining call it, so training behaviour has a
single source of truth.
"""
import copy
import time

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

from src.config import settings
from src.model.lstm import RULModel
from src.retraining.registry import register_model


def train_model(X, y, settings):
    """Train the LSTM on prepared (X, y). Returns (model, best_rmse, history).

    Pure: no MLflow, no registration, no file writes. Restores the best-epoch
    weights in memory (not via disk) so the returned model is the best epoch,
    not the last.
    """
    # Defensive, idempotent RUL cap. The window arrives already capped
    # (Fork 1), and the baseline arrays are raw; capping twice is a no-op.
    y = np.minimum(y, settings.rul_cap)

    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    y_tr = y_tr.reshape(-1, 1)
    y_val = y_val.reshape(-1, 1)

    train_loader = DataLoader(
        TensorDataset(
            torch.tensor(X_tr, dtype=torch.float32),
            torch.tensor(y_tr, dtype=torch.float32),
        ),
        batch_size=settings.batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(
            torch.tensor(X_val, dtype=torch.float32),
            torch.tensor(y_val, dtype=torch.float32),
        ),
        batch_size=settings.batch_size,
        shuffle=False,
    )

    model = RULModel(
        input_size=X.shape[2],
        hidden_size_1=settings.lstm_hidden_size_1,
        hidden_size_2=settings.lstm_hidden_size_2,
        dropout=settings.lstm_dropout,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=settings.adam_lr)
    loss_fn = torch.nn.MSELoss()

    best_rmse = float("inf")
    best_state = None
    patience_counter = 0
    history = []

    for epoch in range(settings.max_epochs):
        model.train()
        running_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = loss_fn(outputs, batch_y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        train_loss = running_loss / len(train_loader)

        model.eval()
        preds, targets = [], []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                out = model(batch_x)
                preds.extend(out.cpu().numpy())
                targets.extend(batch_y.cpu().numpy())
        val_rmse = np.sqrt(mean_squared_error(targets, preds))

        history.append({"epoch": epoch, "train_loss": train_loss, "val_rmse": val_rmse})

        if val_rmse < best_rmse:
            best_rmse = val_rmse
            best_state = copy.deepcopy(model.state_dict())  # in memory, not disk
            patience_counter = 0
        else:
            patience_counter += 1
        if patience_counter >= settings.early_stopping_patience:
            break

    model.load_state_dict(best_state)  # restore best epoch
    return model, best_rmse, history


def train_baseline():
    """Train on the full prepared arrays and register the baseline version."""
    import mlflow
    from pathlib import Path

    mlflow.set_experiment(settings.mlflow_experiment_name)
    processed = Path(settings.processed_data_dir)
    X = np.load(processed / "x_train.npy")
    y = np.load(processed / "y_train.npy")

    model, best_rmse, _ = train_model(X, y, settings)

    register_model(
        model,
        params={
            "lr": settings.adam_lr,
            "batch_size": settings.batch_size,
            "hidden_size_1": settings.lstm_hidden_size_1,
            "hidden_size_2": settings.lstm_hidden_size_2,
            "dropout": settings.lstm_dropout,
            "max_epochs": settings.max_epochs,
            "rul_cap": settings.rul_cap,
        },
        metrics={"best_val_rmse": best_rmse},
    )
    print(f"baseline best_val_rmse: {best_rmse:.4f}")
    return best_rmse


def run_retraining(X_window, y_window, drift_score):
    """Retrain on a recent window and register the new version with provenance."""
    import mlflow

    mlflow.set_experiment(settings.mlflow_experiment_name)
    start = time.time()
    model, best_rmse, _ = train_model(X_window, y_window, settings)
    duration = time.time() - start

    info = register_model(
        model,
        params={
            "lr": settings.adam_lr,
            "batch_size": settings.batch_size,
            "hidden_size_1": settings.lstm_hidden_size_1,
            "hidden_size_2": settings.lstm_hidden_size_2,
            "dropout": settings.lstm_dropout,
            "max_epochs": settings.max_epochs,
            "rul_cap": settings.rul_cap,
            "drift_score": drift_score,
            "window_rows": int(X_window.shape[0]),
            "window_shape": str(X_window.shape),
            "training_duration_s": round(duration, 2),
        },
        metrics={"best_val_rmse": best_rmse},
    )
    version = info.registered_model_version if hasattr(info, "registered_model_version") else None
    print(f"retrained version {version}, best_val_rmse {best_rmse:.4f}, drift {drift_score}")
    return version


if __name__ == "__main__":
    train_baseline()
