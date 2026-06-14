# rul-mlops-pipeline

Drift-Aware Retraining and Shadow-Validated Deployment
for Remaining-Useful-Life Prediction on Industrial Sensor Streams.

MSc Computer Science Dissertation Project
Newcastle University, CSC8099
Supervised by Dr Bo Wei

---

## What this project does

Builds and empirically evaluates a closed-loop MLOps pipeline that:
- Predicts remaining useful life (RUL) on NASA CMAPSS FD001 sensor data
- Detects data drift using Evidently AI with PSI threshold 0.2
- Triggers automatic LSTM retraining when drift is detected
- Validates new model candidates in shadow mode before promotion
- Promotes new models only if bootstrap CI on RMSE difference passes
- Logs all experiments to MLflow with full provenance
- Exposes metrics to Prometheus and Grafana

---

## Stack

Python, PyTorch, FastAPI, MLflow, Evidently AI,
Prometheus, Grafana, Docker, Docker Compose,
GitHub Actions, pytest

---

## Quickstart

Prerequisites: Docker Desktop installed and running.

Start the full stack:

    docker-compose up --build

Services available after startup:
- FastAPI serving:   http://localhost:8000
- MLflow UI:         http://localhost:5000
- Prometheus:        http://localhost:9090
- Grafana:           http://localhost:3000

---

## Repo structure

    src/          source code for all pipeline layers
    pipeline/     data ingestion, preprocessing, drift injection
    experiments/  experiment runner and analysis scripts
    tests/        pytest test suite
    monitoring/   Prometheus config and Grafana dashboard
    data/         raw and processed CMAPSS data
    notebooks/    exploratory data analysis
    docs/         design decisions log

---

## Running tests

    make test

## Running the linter

    make lint

---

## Data

NASA CMAPSS FD001 dataset.
Download from: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data
Place files in: data/raw/

---

## Reproducibility

The entire pipeline runs with a single command:

    docker-compose up --build

No paid cloud services required.
No GPU required. CPU-only training throughout.
