"""Reusable MLflow model registration.

Single registration path shared by the baseline registration and the Day 2
retrainer, so the two cannot diverge. Registers a PyTorch model into the
MLflow registry under the configured name, logging any provenance (params,
tags, metrics) into the same run as the model.
"""
import mlflow
import mlflow.pytorch

from src.config import settings


def register_model(model, name=None, input_example=None,
                   params=None, tags=None, metrics=None):
    """Log and register a PyTorch model into the MLflow registry.

    Uses pickle serialization: pt2 (the 3.x default) fails on the LSTM
    dynamic sequence shapes, per Phase 4. Provenance (params, tags, metrics)
    is logged into the same run as the model so it stays attached to the
    registered version. Registration target is settings.mlflow_tracking_uri.
    """
    name = name or settings.model_registry_name
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    with mlflow.start_run():
        if params:
            mlflow.log_params(params)
        if tags:
            mlflow.set_tags(tags)
        if metrics:
            mlflow.log_metrics(metrics)
        model_info = mlflow.pytorch.log_model(
            pytorch_model=model,
            artifact_path="model",
            serialization_format="pickle",
            registered_model_name=name,
            input_example=input_example,
        )
    return model_info


if __name__ == "__main__":
    from src.model.lstm import RULModel
    import torch

    model = RULModel()
    model.load_state_dict(torch.load("best_model.pth", map_location="cpu"))
    model.eval()
    info = register_model(model)
    print("registered:", info.registered_model_version if hasattr(info, "registered_model_version") else info)
