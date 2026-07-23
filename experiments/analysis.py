"""Analyse the floor matrix results: five metrics with CIs, tables, and figures.

Reads the latest matrix_sudden_medium_*.json, computes per-condition summaries
with bootstrap/Wilson CIs, writes a summary JSON and CSV, and renders figures
for the dissertation. Pure post-processing: no stack, no pipeline runs.

Metric coverage from the floor matrix:
  1. Drift-detection latency  -> A/C = 0s (fire at onset batch); B = N/A.
  2. Deployment latency       -> deployment_latency_s per fire.
  3. False-promotion rate     -> C: promotions that were worse than baseline.
  4. Accuracy retention       -> ci_point (production_RMSE - challenger_RMSE).
  5. p95 serving latency       -> NOT captured in this matrix (needs a separate
                                  serving-under-replay-load measurement). Flagged.
"""
import csv
import glob
import json
from pathlib import Path

import numpy as np

RESULTS_DIR = Path("experiments/results")


def _latest_matrix():
    files = sorted(glob.glob(str(RESULTS_DIR / "matrix_sudden_medium_*.json")))
    if not files:
        raise FileNotFoundError("no matrix results found")
    return files[-1]


def _bootstrap_ci(values, n_resamples=1000, ci_level=0.95, seed=42):
    """Bootstrap CI of the mean. Returns (lower, mean, upper)."""
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (float("nan"), float("nan"), float("nan"))
    if len(values) == 1:
        v = float(values[0])
        return (v, v, v)
    rng = np.random.default_rng(seed)
    means = [rng.choice(values, size=len(values), replace=True).mean()
             for _ in range(n_resamples)]
    alpha = (1 - ci_level) / 2
    lo = float(np.quantile(means, alpha))
    hi = float(np.quantile(means, 1 - alpha))
    return (lo, float(values.mean()), hi)


def _wilson_ci(successes, n, z=1.96):
    """Wilson score interval for a proportion. Returns (lower, point, upper)."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, centre - margin), p, min(1.0, centre + margin))


def analyse():
    path = _latest_matrix()
    rows = json.load(open(path))
    print(f"analysing {path} ({len(rows)} rows)\n")

    conditions = ["A", "B", "C"]
    summary = {}

    for cond in conditions:
        crows = [r for r in rows if r["condition"] == cond]
        n_fires = len(crows)

        # --- Metric 3: false-promotion rate ---
        promotions = [r for r in crows if r["decision"] in ("promoted", "promoted_no_gate")]
        false_promos = [r for r in promotions if r.get("false_promotion") is True]
        n_promo = len(promotions)
        n_false = len(false_promos)
        fp_rate = _wilson_ci(n_false, n_promo) if n_promo > 0 else (0.0, 0.0, 0.0)

        # Correct-decision rate: did the decision match the post-hoc truth?
        # A/B reject; correct if the challenger was actually worse (ci_point < 0).
        # C promotes; correct-to-promote would need ci_point > 0 (never here).
        correct = 0
        for r in crows:
            worse = r["ci_point"] < 0  # challenger worse than baseline
            if r["decision"] in ("rejected",) and worse:
                correct += 1
            elif r["decision"] in ("promoted", "promoted_no_gate") and not worse:
                correct += 1
        correct_rate = _wilson_ci(correct, n_fires)

        # --- Metric 4: accuracy retention (ci_point = prod_RMSE - challenger_RMSE) ---
        ci_points = [r["ci_point"] for r in crows if r["ci_point"] is not None]
        retention = _bootstrap_ci(ci_points)

        # --- Metric 2: deployment latency ---
        dep = [r["deployment_latency_s"] for r in crows if r["deployment_latency_s"] is not None]
        dep_ci = _bootstrap_ci(dep)

        # --- Metric 1: drift-detection latency ---
        det_vals = [r["detection_latency_s"] for r in crows if r["detection_latency_s"] is not None]
        det = _bootstrap_ci(det_vals) if det_vals else None  # None for B

        summary[cond] = {
            "n_fires": n_fires,
            "n_promotions": n_promo,
            "n_false_promotions": n_false,
            "false_promotion_rate": {"lower": fp_rate[0], "point": fp_rate[1], "upper": fp_rate[2]},
            "correct_decision_rate": {"lower": correct_rate[0], "point": correct_rate[1], "upper": correct_rate[2]},
            "accuracy_retention_ci_point": {"lower": retention[0], "mean": retention[1], "upper": retention[2]},
            "deployment_latency_s": {"lower": dep_ci[0], "mean": dep_ci[1], "upper": dep_ci[2]},
            "detection_latency_s": (
                {"lower": det[0], "mean": det[1], "upper": det[2]} if det else "N/A (no drift trigger)"
            ),
        }

    # --- print table ---
    print("=" * 78)
    print(f"{'Condition':<12}{'Fires':<7}{'FalsePromo%':<14}{'CorrectDecision%':<18}{'DeployLat(s)':<14}")
    print("-" * 78)
    for cond in conditions:
        s = summary[cond]
        fp = s["false_promotion_rate"]["point"] * 100
        cd = s["correct_decision_rate"]["point"] * 100
        dl = s["deployment_latency_s"]["mean"]
        print(f"{cond:<12}{s['n_fires']:<7}{fp:<14.1f}{cd:<18.1f}{dl:<14.1f}")
    print("=" * 78)
    print("\nAccuracy retention (RMSE delta = prod - challenger; negative = challenger worse):")
    for cond in conditions:
        r = summary[cond]["accuracy_retention_ci_point"]
        print(f"  {cond}: {r['mean']:.2f}  [{r['lower']:.2f}, {r['upper']:.2f}]")
    print("\nDrift-detection latency:")
    for cond in conditions:
        d = summary[cond]["detection_latency_s"]
        if isinstance(d, dict):
            print(f"  {cond}: {d['mean']:.1f}s")
        else:
            print(f"  {cond}: {d}")
    print("\nMetric 5 (p95 serving latency under replay load): NOT CAPTURED in the")
    print("  floor matrix. Requires a separate serving-under-load measurement.")

    # --- write outputs ---
    out_json = RESULTS_DIR / "analysis_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))

    out_csv = RESULTS_DIR / "analysis_summary.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition", "n_fires", "false_promotion_rate", "correct_decision_rate",
                    "accuracy_retention_mean", "accuracy_retention_lower", "accuracy_retention_upper",
                    "deployment_latency_mean"])
        for cond in conditions:
            s = summary[cond]
            w.writerow([cond, s["n_fires"],
                        round(s["false_promotion_rate"]["point"], 4),
                        round(s["correct_decision_rate"]["point"], 4),
                        round(s["accuracy_retention_ci_point"]["mean"], 3),
                        round(s["accuracy_retention_ci_point"]["lower"], 3),
                        round(s["accuracy_retention_ci_point"]["upper"], 3),
                        round(s["deployment_latency_s"]["mean"], 1)])

    print(f"\nwrote {out_json}")
    print(f"wrote {out_csv}")

    # --- figures ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

        # False-promotion rate
        fps = [summary[c]["false_promotion_rate"]["point"] * 100 for c in conditions]
        axes[0].bar(conditions, fps, color=["#4c72b0", "#55a868", "#c44e52"])
        axes[0].set_title("False-promotion rate by condition")
        axes[0].set_ylabel("False-promotion rate (%)")
        axes[0].set_ylim(0, 105)

        # Accuracy retention with CI
        means = [summary[c]["accuracy_retention_ci_point"]["mean"] for c in conditions]
        los = [summary[c]["accuracy_retention_ci_point"]["mean"] - summary[c]["accuracy_retention_ci_point"]["lower"] for c in conditions]
        his = [summary[c]["accuracy_retention_ci_point"]["upper"] - summary[c]["accuracy_retention_ci_point"]["mean"] for c in conditions]
        axes[1].bar(conditions, means, yerr=[los, his], capsize=6, color=["#4c72b0", "#55a868", "#c44e52"])
        axes[1].set_title("Accuracy retention (RMSE delta, prod - challenger)")
        axes[1].set_ylabel("RMSE delta (negative = challenger worse)")
        axes[1].axhline(0, color="k", lw=0.8)

        # Deployment latency
        dls = [summary[c]["deployment_latency_s"]["mean"] for c in conditions]
        axes[2].bar(conditions, dls, color=["#4c72b0", "#55a868", "#c44e52"])
        axes[2].set_title("Mean deployment latency by condition")
        axes[2].set_ylabel("Deployment latency (s)")

        fig.tight_layout()
        fig_path = RESULTS_DIR / "analysis_figures.png"
        fig.savefig(fig_path, dpi=150)
        print(f"wrote {fig_path}")
    except ImportError:
        print("matplotlib not available; skipped figures")


if __name__ == "__main__":
    analyse()
