"""Metric 5: p95 serving latency under sensor-replay load.

Fires many /predict requests (each a real (30,14) sensor window) at the serving
endpoint under concurrency, records per-request response time, reports p95 (plus
p50/p99/mean and throughput). This measures the deployed model's steady-state
serving latency under load, a single pipeline-serving characteristic independent
of the ablation conditions (serving latency does not depend on how a model was
promoted). The served model is models:/RULModel@production (the baseline).

A warm-up batch is discarded so p95 reflects steady state, not cold start.
"""
import json
import time
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import requests

from src.config import settings

PREDICT_URL = "http://localhost:8000/predict"
RESULTS_DIR = Path("experiments/results")

N_REQUESTS = 1000
CONCURRENCY = 10
WARMUP = 50


def _load_windows(n):
    """Real (30,14) windows from x_train to replay. Content does not affect
    serving latency (same forward pass), but faithful input is used."""
    X = np.load(Path(settings.processed_data_dir) / "x_train.npy")
    idx = np.random.default_rng(42).choice(X.shape[0], size=n, replace=True)
    return [X[i].tolist() for i in idx]


def _one_request(window):
    t0 = time.perf_counter()
    r = requests.post(PREDICT_URL, json={"data": window}, timeout=30)
    r.raise_for_status()
    return time.perf_counter() - t0


def run(n_requests=N_REQUESTS, concurrency=CONCURRENCY, warmup=WARMUP):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    h = requests.get("http://localhost:8000/health", timeout=10)
    h.raise_for_status()
    print(f"serving healthy; measuring p95 over {n_requests} requests at concurrency {concurrency}")

    windows = _load_windows(n_requests + warmup)

    print(f"warming up ({warmup} requests, discarded)...")
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        list(ex.map(_one_request, windows[:warmup]))

    latencies = []
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(_one_request, w) for w in windows[warmup:]]
        for fut in as_completed(futures):
            latencies.append(fut.result())
    wall = time.perf_counter() - t_start

    latencies_ms = sorted(x * 1000 for x in latencies)
    n = len(latencies_ms)

    def pct(p):
        return latencies_ms[min(n - 1, int(p / 100 * n))]

    result = {
        "n_requests": n,
        "concurrency": concurrency,
        "served_model": f"{settings.model_registry_name}@{settings.model_alias}",
        "p50_ms": round(statistics.median(latencies_ms), 2),
        "p95_ms": round(pct(95), 2),
        "p99_ms": round(pct(99), 2),
        "mean_ms": round(statistics.mean(latencies_ms), 2),
        "min_ms": round(latencies_ms[0], 2),
        "max_ms": round(latencies_ms[-1], 2),
        "throughput_rps": round(n / wall, 1),
        "wall_time_s": round(wall, 2),
    }

    print("\n=== Serving latency under replay load ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

    out = RESULTS_DIR / "serving_latency_p95.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}")
    print(f"\nMETRIC 5: p95 serving latency = {result['p95_ms']} ms "
          f"at concurrency {concurrency}, throughput {result['throughput_rps']} req/s")
    return result


if __name__ == "__main__":
    run()
