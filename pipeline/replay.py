"""Replay harness: build one drift scenario, serve separable objects.

Detection, challenger-training, and shadow-evaluation are distinct, and the
training and eval pools are ENGINE-DISJOINT to prevent train/test leakage:

  DETECTION STREAM: multi-engine distributional batches, clean then drifted,
  onset on a batch boundary. Clean batch reads PSI ~0.1, drifted ~0.5.

  DRIFTED TRAINING POOL: post-onset drifted windows from the TRAINING engine
  subset (the 95 smaller-yield engines). The challenger trains on these, so it
  adapts to the drift (restores the 15 July retrain-on-drift design). Drifted
  input raises OOD, firing the existing blend gate for size.

  DRIFTED EVAL POOL: post-onset drifted windows from the EVAL engine subset (the
  5 largest-yield engines, >=500 windows). The shadow stage validates on these.

  Engine-disjoint by construction: no engine contributes to both training and
  eval, so the shadow comparison is leak-free and its numbers are meaningful.

Features from scaled x_train (gate-verified). Raw read solely for labels. Served
labels capped (B'). Latency quantised to batch interval.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import FEATURE_COLUMNS, settings
from pipeline.drift_inject import inject, compute_sigma_s9, S9_INDEX
from pipeline.labels import reconstruct_per_row, derive_served_labels

SCENARIO_DIR = Path("data/drift_scenarios")
_WIN = settings.window_size
_BATCH = settings.drift_batch_size
N_CLEAN = 5
N_DRIFT = 10
_EVAL_ENGINE_COUNT = 5  # largest-yield engines reserved for eval (679 windows, clears 500+margin)


def _window_stream(rows, row_rul):
    """(R,14)+(R,) -> ((R-_WIN+1,_WIN,14),(R-_WIN+1,)). Contiguous, stride 1."""
    n = rows.shape[0] - _WIN + 1
    if n <= 0:
        raise ValueError(f"run too short: {rows.shape[0]} < window {_WIN}")
    X = np.stack([rows[i:i + _WIN] for i in range(n)])
    y = np.array([row_rul[i + _WIN - 1] for i in range(n)])
    return X, y


def _load_engines():
    """reconstruct_per_row grouped into per-engine (id, feats, uncapped_rul)."""
    units, feats, rul = reconstruct_per_row()
    engines = []
    for u in pd.unique(units):
        idx = np.where(units == u)[0]
        engines.append((int(u), feats[idx], rul[idx]))
    return engines


def _post_onset_window_yield(feats):
    d = len(feats) // 2
    tail = len(feats) - d
    return max(0, tail - _WIN + 1)


def _partition_engines(engines):
    """Largest-yield _EVAL_ENGINE_COUNT engines -> eval subset; rest -> train.

    Returns (eval_engines, train_engines), disjoint by construction.
    """
    ordered = sorted(engines, key=lambda e: _post_onset_window_yield(e[1]), reverse=True)
    eval_engines = ordered[:_EVAL_ENGINE_COUNT]
    train_engines = ordered[_EVAL_ENGINE_COUNT:]
    return eval_engines, train_engines


# Recurring schedule over 15 batches: clean, drift, clean, drift (2 onsets).
_RECUR_SCHEDULE = [("clean", 3), ("drift", 4), ("clean", 3), ("drift", 5)]


def _recur_drift_batches():
    """Drifted batch indices under _RECUR_SCHEDULE, plus onset and clear batches."""
    drift_idx, onsets, clears = set(), [], []
    b = 0
    prev = None
    for phase, n in _RECUR_SCHEDULE:
        if phase == "drift":
            onsets.append(b)
            for j in range(b, b + n):
                drift_idx.add(j)
        elif phase == "clean" and prev == "drift":
            clears.append(b)
        prev = phase
        b += n
    return drift_idx, onsets, clears


def _build_detection_batches(all_feats, drift_type, k, sigma, seed):
    """Clean/drifted multi-engine detection batches.

    sudden:    N_CLEAN clean then N_DRIFT drifted at full k. Onset = N_CLEAN.
    gradual:   drifted batch b at k*(b-N_CLEAN+1)/N_DRIFT (ramp). Onset = N_CLEAN.
    recurring: clean/drift/clean/drift per _RECUR_SCHEDULE (2 onsets), each drift
               phase full k. Onset (singular) = first drift-phase start.
    """
    if drift_type == "recurring":
        drift_idx, onsets, _ = _recur_drift_batches()
        total = sum(n for _, n in _RECUR_SCHEDULE)
        batches = []
        for b in range(total):
            rng = np.random.default_rng(seed + b)
            idx = rng.choice(all_feats.shape[0], size=_BATCH, replace=False)
            batch = all_feats[idx]
            if b in drift_idx:
                batch = inject(batch, "recurring", k, 0, sigma, seed=seed + b, s9_index=S9_INDEX)
            batches.append(batch)
        return batches, onsets[0]

    batches = []
    for b in range(N_CLEAN + N_DRIFT):
        rng = np.random.default_rng(seed + b)
        idx = rng.choice(all_feats.shape[0], size=_BATCH, replace=False)
        batch = all_feats[idx]
        if b >= N_CLEAN and drift_type == "sudden":
            batch = inject(batch, "sudden", k, 0, sigma, seed=seed + b, s9_index=S9_INDEX)
        elif b >= N_CLEAN and drift_type == "gradual":
            frac = (b - N_CLEAN + 1) / N_DRIFT
            batch = inject(batch, "gradual", k * frac, 0, sigma, seed=seed + b, s9_index=S9_INDEX)
        batches.append(batch)
    return batches, N_CLEAN

def _pool_drifted_windows(engine_subset, drift_type, k, sigma, seed, target):
    """Pool post-onset drifted stride-1 windows from a subset, until >= target.

    Each window wholly within one engine's post-onset tail (zero straddle).
    Returns (X, y, provenance, engine_ids_used).
    """
    Xs, ys, prov = [], [], []
    order = list(range(len(engine_subset)))
    rng = np.random.default_rng(seed)
    rng.shuffle(order)
    used = []
    for ei in order:
        u, feats, rul = engine_subset[ei]
        d = len(feats) // 2
        tail_feats = feats[d:]
        tail_rul = rul[d:]
        if tail_feats.shape[0] < _WIN:
            continue
        drifted = inject(tail_feats, drift_type, k, 0, sigma, seed=seed, s9_index=S9_INDEX)
        Xw, yw = _window_stream(drifted, derive_served_labels(tail_rul))
        Xs.append(Xw)
        ys.append(yw)
        prov.extend([u] * len(yw))
        used.append(u)
        if sum(len(a) for a in ys) >= target:
            break
    if not Xs:
        raise ValueError("no engine tail long enough to window")
    X = np.concatenate(Xs, axis=0)
    y = np.concatenate(ys, axis=0)
    if len(y) < target:
        raise ValueError(f"pooled only {len(y)} windows, need {target}")
    return X, y, np.array(prov, dtype=np.int64), used


def build_scenario(drift_type, intensity, k, seed):
    """Build detection batches + disjoint drifted train/eval pools + metadata."""
    engines = _load_engines()
    units, all_feats, all_rul = reconstruct_per_row()
    sigma = compute_sigma_s9(all_feats)

    batches, onset = _build_detection_batches(all_feats, drift_type, k, sigma, seed)

    eval_engines, train_engines = _partition_engines(engines)

    eval_target = settings.shadow_min_predictions
    eval_X, eval_y, eval_prov, eval_ids = _pool_drifted_windows(
        eval_engines, drift_type, k, sigma, seed + 1, eval_target)

    train_target = 2 * settings.shadow_min_predictions  # bounded; larger than eval, blend adds more
    train_X, train_y, train_prov, train_ids = _pool_drifted_windows(
        train_engines, drift_type, k, sigma, seed + 2, train_target)

    # HARD REQUIREMENT: engine-disjoint train vs eval (leak-free shadow comparison)
    overlap = set(eval_ids) & set(train_ids)
    assert not overlap, f"LEAK: engines in both train and eval: {overlap}"

    ramp_n_drift = N_DRIFT if drift_type == "gradual" else 0
    ramp_slope = (float(k) / N_DRIFT) if drift_type == "gradual" else 0.0
    if drift_type == "recurring":
        _, _recur_onsets, _recur_clears = _recur_drift_batches()
    else:
        _recur_onsets, _recur_clears = [onset], []
    return {
        "recur_onsets": np.array(_recur_onsets, dtype=np.int64),
        "recur_clears": np.array(_recur_clears, dtype=np.int64),
        "recur_cycles": int(len(_recur_onsets)),
        "drift_type": drift_type,
        "k": float(k),
        "seed": int(seed),
        "sigma_s9": float(sigma),
        "ramp_n_drift": int(ramp_n_drift),
        "ramp_slope": float(ramp_slope),
        "det_batches": np.stack(batches),
        "onset_batch": int(onset),
        "batch_size": int(_BATCH),
        "batch_interval_s": float(settings.drift_batch_interval_s),
        "eval_X": eval_X,
        "eval_y": eval_y,
        "eval_provenance": eval_prov,
        "eval_n": int(len(eval_y)),
        "eval_engines": np.array(sorted(eval_ids), dtype=np.int64),
        "train_X": train_X,
        "train_y": train_y,
        "train_provenance": train_prov,
        "train_n": int(len(train_y)),
        "train_engines": np.array(sorted(train_ids), dtype=np.int64),
    }


def _scenario_path(drift_type, intensity, seed):
    return SCENARIO_DIR / f"{drift_type}_{intensity}_seed{seed}.npz"


def save_scenario(scenario, intensity):
    """One self-describing .npz, atomic (temp-in-same-dir then os.replace)."""
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    path = _scenario_path(scenario["drift_type"], intensity, scenario["seed"])
    tmp = path.with_name(path.name + ".tmp")
    np.savez(
        tmp,
        drift_type=scenario["drift_type"], k=scenario["k"], seed=scenario["seed"],
        sigma_s9=scenario["sigma_s9"],
        ramp_n_drift=scenario["ramp_n_drift"], ramp_slope=scenario["ramp_slope"],
        recur_onsets=scenario["recur_onsets"], recur_clears=scenario["recur_clears"],
        recur_cycles=scenario["recur_cycles"],
        det_batches=scenario["det_batches"], onset_batch=scenario["onset_batch"],
        batch_size=scenario["batch_size"], batch_interval_s=scenario["batch_interval_s"],
        eval_X=scenario["eval_X"], eval_y=scenario["eval_y"],
        eval_provenance=scenario["eval_provenance"], eval_n=scenario["eval_n"],
        eval_engines=scenario["eval_engines"],
        train_X=scenario["train_X"], train_y=scenario["train_y"],
        train_provenance=scenario["train_provenance"], train_n=scenario["train_n"],
        train_engines=scenario["train_engines"],
    )
    written = tmp if tmp.exists() else tmp.with_name(tmp.name + ".npz")
    os.replace(written, path)
    return path


def load_scenario(path):
    """allow_pickle=False; scalars cast off 0-d arrays."""
    d = np.load(path, allow_pickle=False)
    return {
        "drift_type": str(d["drift_type"]), "k": float(d["k"]), "seed": int(d["seed"]),
        "sigma_s9": float(d["sigma_s9"]),
        "ramp_n_drift": int(d["ramp_n_drift"]) if "ramp_n_drift" in d else 0,
        "ramp_slope": float(d["ramp_slope"]) if "ramp_slope" in d else 0.0,
        "recur_onsets": d["recur_onsets"] if "recur_onsets" in d else np.array([], dtype=np.int64),
        "recur_clears": d["recur_clears"] if "recur_clears" in d else np.array([], dtype=np.int64),
        "recur_cycles": int(d["recur_cycles"]) if "recur_cycles" in d else 1,
        "det_batches": d["det_batches"], "onset_batch": int(d["onset_batch"]),
        "batch_size": int(d["batch_size"]), "batch_interval_s": float(d["batch_interval_s"]),
        "eval_X": d["eval_X"], "eval_y": d["eval_y"],
        "eval_provenance": d["eval_provenance"], "eval_n": int(d["eval_n"]),
        "eval_engines": d["eval_engines"],
        "train_X": d["train_X"], "train_y": d["train_y"],
        "train_provenance": d["train_provenance"], "train_n": int(d["train_n"]),
        "train_engines": d["train_engines"],
    }


class ReplayCursor:
    """Serves detection batches, drifted train pool, and drifted eval pool."""

    def __init__(self, scenario):
        self.s = scenario

    def n_batches(self):
        return self.s["det_batches"].shape[0]

    def onset_batch(self):
        return self.s["onset_batch"]

    def detector_batch(self, i):
        return pd.DataFrame(self.s["det_batches"][i], columns=FEATURE_COLUMNS)

    def retrain_train_fetch(self):
        """(X,y) DRIFTED training windows from the training engine subset.
        Disjoint from the eval pool by engine, so the shadow comparison is
        leak-free. Drifted input fires the blend gate in run_retraining."""
        return self.s["train_X"], self.s["train_y"]

    def eval_pool(self):
        """(X,y) DRIFTED eval windows from the eval engine subset (>=500)."""
        return self.s["eval_X"], self.s["eval_y"]
