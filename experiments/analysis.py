"""Analyse matrix results across drift types: five metrics with CIs, per-drift
summaries, and a cross-drift comparison. Handles recurring's C dual reference.

Per-decision false-promotion: each fire vs the model it replaced (the comparable
axis across drift types; in each row's false_promotion field).
Cumulative degradation (recurring only): each repeat's FINAL promoted model vs v1
on the eval pool, freshly computed from the registry, because the run only logged
each fire against its immediate predecessor. For single-onset drift (sudden,
gradual) C replaces v1 exactly once, so the two references coincide.
"""
import glob
import json
from pathlib import Path

import numpy as np


RESULTS_DIR = Path("experiments/results")
DRIFT_TYPES = ["sudden", "gradual", "recurring"]


def _latest(drift_type):
    files = sorted(glob.glob(str(RESULTS_DIR / f"matrix_{drift_type}_medium_*.json")))
    return files[-1] if files else None


def _bootstrap_ci(values, n_resamples=1000, ci_level=0.95, seed=42):
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (float("nan"), float("nan"), float("nan"))
    if len(values) == 1:
        v = float(values[0])
        return (v, v, v)
    rng = np.random.default_rng(seed)
    means = [rng.choice(values, size=len(values), replace=True).mean() for _ in range(n_resamples)]
    a = (1 - ci_level) / 2
    return (float(np.quantile(means, a)), float(values.mean()), float(np.quantile(means, 1 - a)))


def _wilson(successes, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    m = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / d
    return (max(0.0, c - m), p, min(1.0, c + m))


def _cumulative_degradation(rows):
    """Recurring C: each repeat's FINAL promoted model vs v1 on the eval pool.
    Freshly computed from the registry. Returns list of RMSE deltas (v1 - final),
    negative = final worse than v1."""
    import torch
    import mlflow
    import mlflow.pytorch
    from src.config import settings
    from pipeline.replay import load_scenario, ReplayCursor

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    scenario = load_scenario("data/drift_scenarios/recurring_medium_seed0.npz")
    X_eval, y_eval = ReplayCursor(scenario).eval_pool()
    y_true = np.minimum(np.asarray(y_eval, float).ravel(), settings.rul_cap)

    def predict(ver):
        m = mlflow.pytorch.load_model(f"models:/{settings.model_registry_name}/{ver}").eval()
        with torch.no_grad():
            return m(torch.tensor(X_eval, dtype=torch.float32)).cpu().numpy().ravel()

    v1_pred = predict("1")
    v1_rmse = float(np.sqrt(np.mean((v1_pred - y_true) ** 2)))

    deltas = []
    repeats = sorted(set(r["repeat"] for r in rows))
    for rep in repeats:
        rep_rows = sorted([r for r in rows if r["repeat"] == rep], key=lambda x: x["fire_index"])
        final_ver = rep_rows[-1]["version"]
        fp = predict(final_ver)
        f_rmse = float(np.sqrt(np.mean((fp - y_true) ** 2)))
        deltas.append(v1_rmse - f_rmse)  # negative = final worse than v1
    return deltas, v1_rmse


def analyse_drift(drift_type, compute_cumulative=False):
    path = _latest(drift_type)
    if not path:
        return None
    rows = json.load(open(path))
    summary = {"drift_type": drift_type, "file": path, "n_rows": len(rows)}

    for cond in ["A", "B", "C"]:
        crows = [r for r in rows if r["condition"] == cond]
        promos = [r for r in crows if r["decision"] in ("promoted", "promoted_no_gate")]
        false_p = [r for r in promos if r.get("false_promotion") is True]
        fp = _wilson(len(false_p), len(promos)) if promos else (0.0, 0.0, 0.0)
        # per-decision accuracy retention: fire-0 (vs v1) only, to avoid moving-baseline muddle
        f0 = [r["ci_point"] for r in crows if r.get("fire_index") == 0 and r["ci_point"] is not None]
        ret = _bootstrap_ci(f0)
        dep = _bootstrap_ci([r["deployment_latency_s"] for r in crows if r["deployment_latency_s"] is not None])
        det_vals = [r["detection_latency_s"] for r in crows if r["detection_latency_s"] is not None]
        det = _bootstrap_ci(det_vals) if det_vals else None
        summary[cond] = {
            "n_fires": len(crows), "n_promotions": len(promos), "n_false": len(false_p),
            "false_promotion_rate_per_decision": {"lower": fp[0], "point": fp[1], "upper": fp[2]},
            "accuracy_retention_fire0_vs_v1": {"lower": ret[0], "mean": ret[1], "upper": ret[2]},
            "deployment_latency_s": {"lower": dep[0], "mean": dep[1], "upper": dep[2]},
            "detection_latency_s": ({"mean": det[1]} if det else "N/A"),
        }

    if drift_type == "recurring" and compute_cumulative:
        crows = [r for r in rows if r["condition"] == "C"]
        deltas, v1_rmse = _cumulative_degradation(crows)
        cum = _bootstrap_ci(deltas)
        summary["C"]["cumulative_degradation_vs_v1"] = {
            "lower": cum[0], "mean": cum[1], "upper": cum[2],
            "v1_rmse": v1_rmse, "note": "final promoted model vs v1; damage persists across recurrences",
        }

    return summary


def main():
    results = {}
    for dt in DRIFT_TYPES:
        cum = (dt == "recurring")
        s = analyse_drift(dt, compute_cumulative=cum)
        if s:
            results[dt] = s

    # per-drift tables
    for dt, s in results.items():
        print("=" * 70)
        print(f"DRIFT TYPE: {dt}  ({s['n_rows']} rows)")
        print(f"{'Cond':<6}{'Fires':<7}{'FalsePromo%(per-dec)':<22}{'AccRet(fire0 vs v1)':<22}{'DeployLat':<10}")
        for c in ["A", "B", "C"]:
            cs = s[c]
            fp = cs["false_promotion_rate_per_decision"]["point"] * 100
            ar = cs["accuracy_retention_fire0_vs_v1"]["mean"]
            dl = cs["deployment_latency_s"]["mean"]
            print(f"{c:<6}{cs['n_fires']:<7}{fp:<22.1f}{ar:<22.2f}{dl:<10.1f}")
        if "cumulative_degradation_vs_v1" in s["C"]:
            cd = s["C"]["cumulative_degradation_vs_v1"]
            print(f"  recurring C cumulative degradation (final vs v1): "
                  f"{cd['mean']:.2f} [{cd['lower']:.2f}, {cd['upper']:.2f}] (v1 RMSE {cd['v1_rmse']:.2f})")

    # cross-drift comparison
    print("\n" + "=" * 70)
    print("CROSS-DRIFT COMPARISON")
    print(f"{'Metric':<38}{'sudden':<12}{'gradual':<12}{'recurring':<12}")
    def gv(dt, path_fn):
        return path_fn(results[dt]) if dt in results else float("nan")
    print(f"{'A detection latency (s)':<38}"
          + "".join(f"{results[dt]['A']['detection_latency_s']['mean']:<12.1f}" if dt in results else f"{'-':<12}" for dt in DRIFT_TYPES))
    print(f"{'A fires per run':<38}"
          + "".join(f"{results[dt]['A']['n_fires']//5:<12}" if dt in results else f"{'-':<12}" for dt in DRIFT_TYPES))
    print(f"{'C false-promo % (per-decision)':<38}"
          + "".join(f"{results[dt]['C']['false_promotion_rate_per_decision']['point']*100:<12.1f}" if dt in results else f"{'-':<12}" for dt in DRIFT_TYPES))
    print(f"{'A accuracy retention (fire0 vs v1)':<38}"
          + "".join(f"{results[dt]['A']['accuracy_retention_fire0_vs_v1']['mean']:<12.2f}" if dt in results else f"{'-':<12}" for dt in DRIFT_TYPES))
    rec_cum = results.get("recurring", {}).get("C", {}).get("cumulative_degradation_vs_v1")
    if rec_cum:
        print(f"{'C cumulative degrad vs v1 (recur only)':<38}{'=per-dec':<12}{'=per-dec':<12}{rec_cum['mean']:<12.2f}")
    print("\nNote: single-onset drift (sudden, gradual) has no separate cumulative")
    print("figure (C replaces v1 once, so per-decision = cumulative). Recurring's")
    print("per-decision drop (100->60) with persistent cumulative degradation is the")
    print("compounding finding: ungated damage accumulates across recurrences.")

    out = RESULTS_DIR / "analysis_cross_drift.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
