from fastapi import FastAPI
import numpy as np
from datetime import datetime
from src.serving.predictor import predict_rul, MODEL_NAME, MODEL_VERSION
from pydantic import BaseModel
from prometheus_client import Gauge,Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator



class PredictRequest(BaseModel):
    data: list



app = FastAPI()
Instrumentator().instrument(app).expose(app)

prediction_latency_seconds  = Histogram(
    "prediction_latency_seconds",
    "Time taken for prediction in seconds",
    buckets=(0.1, 0.5, 1, 2, 5, 10)
)

prediction_requests_total = Counter(
    "prediction_requests_total",   
    "Total number of prediction requests"
)   

model_version_current = Gauge(
    "model_version_current",
    "Current version of the deployed model"
)


model_version = MODEL_VERSION
model_name = MODEL_NAME

@app.on_event("startup")
def startup_event():
    model_version_current.set(int(model_version))  

@app.post("/predict")
def predict_endpoint(request: PredictRequest):
    input_data = np.array(request.data, dtype=np.float32)
    before_prediction_time = datetime.now()
    prediction = predict_rul(input_data)
    after_prediction_time = datetime.now()
    prediction_time = (after_prediction_time - before_prediction_time).total_seconds()  

    prediction_requests_total.inc()
    prediction_latency_seconds.observe(prediction_time)
    return {
        "predicted_rul": prediction,
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "model_version": model_version
    }

@app.get("/health")
def health_check():
    return({"status": "healthy"})
