import numpy as np
import torch
import os

MODEL_NAME = "RULModel"
MODEL_VERSION = "1"

def load_model():
    """Load model from MLflow or fallback to local file."""
    try:
        import mlflow.pytorch
        model = mlflow.pytorch.load_model(f"models:/{MODEL_NAME}/{MODEL_VERSION}")
    except Exception:
        from src.model.lstm import RULModel
        model = RULModel()
        model.load_state_dict(torch.load("best_model.pth", map_location="cpu"))
    return model.eval()

model = load_model()

def predict_rul(input_data: np.ndarray) -> float:
    with torch.no_grad():
        input_tensor = torch.tensor(input_data, dtype=torch.float32)
        if input_tensor.dim() == 2:
            input_tensor = input_tensor.unsqueeze(0)  # add batch dimension
        prediction = model(input_tensor)
        return prediction.item()