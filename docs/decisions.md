# Design Decisions Log

One entry per design decision. Written at time of decision.
Format: [Date] [Component] Decision: chose X over Y because Z.

---

## Entries

[2026-06-08] Project: chose CMAPSS FD001 over other RUL datasets
because it is the standard benchmark for turbofan RUL prediction
with published RMSE baselines for direct comparison.

[2026-06-09] Drift Detection: chose PSI over KL divergence as the
primary drift metric because PSI is more interpretable for tabular
sensor data and maps directly to Evidently AI built-in reporting
without custom implementation.

[2026-06-10] Safe Deployment: chose shadow validation over canary
deployment because shadow mode requires no traffic splitting logic
and allows full parallel evaluation of the candidate model before
any production exposure.

[2026-06-17] Serving: chose FastAPI over Flask because async 
support is needed for concurrent prediction requests and 
Prometheus instrumentation via prometheus-fastapi-instrumentator 
is simpler.

[2026-06-17] Containerisation: chose Docker Compose over 
Kubernetes because the project runs locally on a laptop with 
no cloud dependency and Kubernetes adds orchestration overhead 
with no benefit at this scale.

[2026-06-17] Docker layers: dependencies copied and installed 
before application code in all Dockerfiles because Docker 
caches layers independently and code changes more frequently 
than dependencies, making rebuilds faster.

[2026-06-17] Healthchecks: using condition: service_healthy 
in depends_on rather than plain depends_on because depends_on 
alone only waits for container start, not service readiness. 
Without healthchecks the api crashes if MLflow is still 
initialising when the api tries to connect.

[2026-06-20] Experiment tracking: chose MLflow over manual 
logging because MLflow provides a model registry with 
alias-based loading, experiment comparison UI, and artifact 
storage in a single tool that runs locally without cloud 
dependencies.

[2026-06-20] Model registry: using MLflow 3.x alias pattern 
(@champion) instead of stage labels (Production/Staging) 
because stage transitions are deprecated in MLflow 3.x. 
The predictor loads the production LSTM model via alias 
at startup.

[2026-06-20] Training loop: creating a fresh model and 
optimizer for each hyperparameter run because shared weights 
across runs produce meaningless results. Each run must start 
from random initialisation.

[2026-06-22] MLflow in Docker: MLflow tracking server runs 
as a Docker service using ghcr.io/mlflow/mlflow image with 
a named volume for persistence. Scripts on the host log to 
it via localhost:5000. Scripts inside the Docker network 
log to it via the service name mlflow:5000.

[2026-06-30] Data: capped RUL labels at 125 because engines early
in life show no degradation signal, and predicting RUL above 125
adds noise that dominates MSE loss. Standard practice in all
published CMAPSS benchmarks (Wu 2019, Li 2018, SJSU 2024).

