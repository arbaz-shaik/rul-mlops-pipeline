"""Matrix experiment runner: 3 conditions x 5 repeats on sudden-medium."""
import json
import os as _os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import mlflow
from mlflow import MlflowClient

from src.config import settings
from src.drift.detector import compute_drift
from src.drift.trigger import check_drift, find_rising_crossings
from pipeline.replay import build_scenario, save_scenario, load_scenario, ReplayCursor

RETRAIN_URL = "http://localhost:8001/retrain"
_SCENARIO_NAME = _os.environ.get("SCENARIO_NAME", "sudden_medium_seed0")
SCENARIO_HOST_PATH = f"data/drift_scenarios/{_SCENARIO_NAME}.npz"
SCENARIO_CONTAINER_PATH = f"/app/data/drift_scenarios/{_SCENARIO_NAME}.npz"
_DRIFT_LABEL = _SCENARIO_NAME.split("_")[0]
CONDITIONS = ["A", "B", "C"]
REPEATS = 5
SCENARIO_SEED = 0
RESULTS_DIR = Path("experiments/results")

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
_client = MlflowClient()


def _baseline_version():
    return _client.get_model_version_by_alias(
        settings.model_registry_name, settings.model_alias).version


def _reset_alias(version):
    _client.set_registered_model_alias(
        settings.model_registry_name, settings.model_alias, str(version))


def _ensure_scenario():
    if not Path(SCENARIO_HOST_PATH).exists():
        s = build_scenario("sudden", "medium", settings.drift_medium_k, SCENARIO_SEED)
        save_scenario(s, "medium")
    return load_scenario(SCENARIO_HOST_PATH)


def _find_crossing(cursor):
    onset = cursor.onset_batch()
    for i in range(cursor.n_batches()):
        per_feature, aggregate = compute_drift(cursor.detector_batch(i))
        if check_drift(per_feature, aggregate):
            latency = max(0, i - onset) * cursor.s["batch_interval_s"]
            return i, float(aggregate), latency
    return None, None, None


def _all_crossings(cursor):
    """All edge-triggered rising crossings over the batch sequence. Returns
    [(batch, agg, latency), ...]. Single-onset scenarios yield one crossing
    (regression-safe); recurring yields one per onset. Latency is measured from
    the nearest preceding onset (recur_onsets for recurring, else onset_batch)."""
    psi = []
    for i in range(cursor.n_batches()):
        _, aggregate = compute_drift(cursor.detector_batch(i))
        psi.append(float(aggregate))
    cross_idx = find_rising_crossings(psi)
    onsets = list(cursor.s.get("recur_onsets", []))
    if not len(onsets):
        onsets = [cursor.onset_batch()]
    interval = cursor.s["batch_interval_s"]
    out = []
    for ci in cross_idx:
        preceding = [o for o in onsets if o <= ci]
        base = max(preceding) if preceding else onsets[0]
        latency = max(0, ci - base) * interval
        out.append((ci, psi[ci], latency))
    return out


def _post(condition, fire_index, drift_score, detection_latency_s):
    payload = {
        "drift_score": drift_score,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "experiment": True,
        "scenario_path": SCENARIO_CONTAINER_PATH,
        "detection_latency_s": detection_latency_s,
        "condition": condition,
        "fire_index": fire_index,
    }
    r = requests.post(RETRAIN_URL, json=payload, timeout=1800)
    r.raise_for_status()
    return r.json()


def _extract(resp):
    ci = resp.get("ci")
    triggered = resp.get("triggered_at")
    completed = resp.get("completed_at")
    deploy_latency = None
    if triggered and completed:
        t = datetime.fromisoformat(triggered)
        c = datetime.fromisoformat(completed)
        deploy_latency = (c - t).total_seconds()
    return {
        "decision": resp.get("decision"),
        "version": resp.get("version"),
        "ci_lower": ci[0] if ci else None,
        "ci_upper": ci[1] if ci else None,
        "ci_point": ci[2] if ci else None,
        "false_promotion": resp.get("false_promotion"),
        "status": resp.get("status"),
        "detection_latency_s": resp.get("detection_latency_s"),
        "deployment_latency_s": deploy_latency,
        "eval_rows": resp.get("eval_rows"),
    }


def _run_A(cursor, repeat):
    rows = []
    for fi, (crossing, agg, latency) in enumerate(_all_crossings(cursor)):
        resp = _post("A", fi, agg, latency)
        rows.append({"repeat": repeat, "condition": "A", "fire_index": fi,
                     "crossing_batch": crossing, **_extract(resp)})
    return rows


def _run_C(cursor, repeat):
    rows = []
    for fi, (crossing, agg, latency) in enumerate(_all_crossings(cursor)):
        resp = _post("C", fi, agg, latency)
        rows.append({"repeat": repeat, "condition": "C", "fire_index": fi,
                     "crossing_batch": crossing, **_extract(resp)})
    return rows


def _run_B(cursor, repeat):
    k = settings.drift_cron_k
    rows = []
    fire_index = 0
    for i in range(cursor.n_batches()):
        per_feature, aggregate = compute_drift(cursor.detector_batch(i))
        if i > 0 and i % k == 0:
            resp = _post("B", fire_index, float(aggregate), None)
            rows.append({"repeat": repeat, "condition": "B", "fire_index": fire_index,
                         "fire_batch": i, **_extract(resp)})
            fire_index += 1
    return rows


_RUNNERS = {"A": _run_A, "B": _run_B, "C": _run_C}


def run_matrix():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_scenario()
    baseline = _baseline_version()
    print(f"baseline version (reset target): v{baseline}")
    all_rows = []
    for condition in CONDITIONS:
        for repeat in range(REPEATS):
            _reset_alias(baseline)
            cursor = ReplayCursor(load_scenario(SCENARIO_HOST_PATH))
            t0 = time.time()
            rows = _RUNNERS[condition](cursor, repeat)
            _reset_alias(baseline)
            dur = time.time() - t0
            for row in rows:
                row["wall_time_s"] = round(dur, 1)
            all_rows.extend(rows)
            print(f"[{condition} repeat {repeat}] {len(rows)} fire(s), {round(dur,1)}s, "
                  f"decisions={[r['decision'] for r in rows]}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / f"matrix_{_DRIFT_LABEL}_medium_{stamp}.json"
    out.write_text(json.dumps(all_rows, indent=2))
    _reset_alias(baseline)
    print(f"\nwrote {out} ({len(all_rows)} rows). alias reset -> v{baseline}")
    return out


if __name__ == "__main__":
    run_matrix()
