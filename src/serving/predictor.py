import numpy as np
import torch
import mlflow
import mlflow.pytorch

from src.config import settings


def load_model():
    """Load the production model from the MLflow registry by alias.

    No local fallback. A failure raises loudly at startup rather than
    silently serving stale weights.
    """
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    uri = f"models:/{settings.model_registry_name}@{settings.model_alias}"
    model = mlflow.pytorch.load_model(uri).eval()
    client = mlflow.MlflowClient()
    version = client.get_model_version_by_alias(
        settings.model_registry_name, settings.model_alias
    ).version
    return model, version


model, served_version = load_model()


def predict_rul(input_data: np.ndarray) -> float:
    with torch.no_grad():
        input_tensor = torch.tensor(input_data, dtype=torch.float32)
        if input_tensor.dim() == 2:
            input_tensor = input_tensor.unsqueeze(0)
        prediction = model(input_tensor)
        return prediction.item()
