"""Replay harness: build one drift scenario, serve TWO separable objects.

Per the final ruling, detection and evaluation are distinct objects:

  DETECTION STREAM: a sequence of multi-engine distributional batches. The first
  n_clean batches are representative draws across engines with no injection; the
  next n_drift batches are representative draws with the s9 offset applied. Drift
  onset is a batch boundary (onset_batch = n_clean); no batch straddles onset.
  A clean multi-engine batch reads PSI ~0.1 against the pooled reference; a
  drifted batch at k reads in-band. Single-engine batches were rejected: one
  engine occupies a narrow band of the pooled manifold and reads ~3.3 clean.

  EVAL POOL: 500+ per-engine stride-1 windows, each wholly inside one engine
  (zero cross-engine straddle), drawn from post-onset engine tails so each window
  carries drift. Pooled to clear shadow_min_predictions.

  RETRAIN-TRAIN FETCH: the challenger trains on pre-onset (clean) windows.

Features come only from scaled x_train (via labels.reconstruct_per_row scaler
transform, gate-verified bit-identical). Raw is read solely for labels. Served/
evaluated labels are capped (B'); uncapped stored for the on-manifold proof.
Latency is quantised to the batch interval: (crossing_batch - onset) * interval.
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


def _window_stream(rows, row_rul):
    """(R,14)+(R,) -> ((R-_WIN+1,_WIN,14),(R-_WIN+1,)). Contiguous, stride 1.

    Label = terminal-row RUL, matching create_windowed_features. Injection is
    applied to rows BEFORE this call.
    """
    n = rows.shape[0] - _WIN + 1
    if n <= 0:
        raise ValueError(f"run too short: {rows.shape[0]} < window {_WIN}")
    X = np.stack([rows[i:i + _WIN] for i in range(n)])
    y = np.array([row_rul[i + _WIN - 1] for i in range(n)])
    return X, y


def _load_engines():
    """reconstruct_per_row grouped into per-engine (feats, uncapped_rul) in order."""
    units, feats, rul = reconstruct_per_row()
    engines = []
    for u in pd.unique(units):
        idx = np.where(units == u)[0]
        engines.append((int(u), feats[idx], rul[idx]))
    return engines


# Detection stream: sequence of multi-engine batches, clean then drifted.
def _build_detection_batches(all_feats, drift_type, k, sigma, seed):
    """Return (batches list of (_BATCH,14) arrays, onset_batch).

    First N_CLEAN batches are clean multi-engine draws; next N_DRIFT batches are
    multi-engine draws with s9 offset applied across the whole batch. Each batch
    seeded from seed + its index so the sequence is deterministic and every batch
    is an independent representative draw. Onset is a boundary (= N_CLEAN); no
    batch straddles.
    """
    batches = []
    total = N_CLEAN + N_DRIFT
    for b in range(total):
        rng = np.random.default_rng(seed + b)
        idx = rng.choice(all_feats.shape[0], size=_BATCH, replace=False)
        batch = all_feats[idx]
        if b >= N_CLEAN and drift_type == "sudden":
            batch = inject(batch, "sudden", k, 0, sigma, seed=seed + b, s9_index=S9_INDEX)
        batches.append(batch)
    return batches, N_CLEAN


# Eval pool: per-engine drifted-tail windows, pooled >=500, zero straddle.
def _build_eval_pool(engines, drift_type, k, sigma, seed, target):
    """Pool single-engine stride-1 windows from post-onset drifted tails.

    Each window comes wholly from one engine's post-onset tail (zero cross-engine
    straddle). Collect until >= target windows.
    """
    Xs, ys, provenance = [], [], []
    order = list(range(len(engines)))
    rng = np.random.default_rng(seed + 1)
    rng.shuffle(order)

    for ei in order:
        u, feats, rul = engines[ei]
        run_len = len(feats)
        d = run_len // 2
        tail_feats = feats[d:]
        tail_rul = rul[d:]
        if tail_feats.shape[0] < _WIN:
            continue
        drifted_tail = inject(tail_feats, drift_type, k, 0, sigma, seed=seed, s9_index=S9_INDEX)
        Xw, yw = _window_stream(drifted_tail, derive_served_labels(tail_rul))
        Xs.append(Xw)
        ys.append(yw)
        provenance.extend([u] * len(yw))
        if sum(len(a) for a in ys) >= target:
            break

    if not Xs:
        raise ValueError("no engine tail long enough to window")
    X = np.concatenate(Xs, axis=0)
    y = np.concatenate(ys, axis=0)
    prov = np.array(provenance, dtype=np.int64)
    if len(y) < target:
        raise ValueError(f"pooled only {len(y)} eval windows, need {target}")
    return X, y, prov


def _build_train_fetch(all_feats, all_rul, seed, target):
    """Clean multi-engine windows the challenger trains on (pre-onset regime).

    Draws a contiguous-per-engine set is unnecessary here; the challenger trains
    on clean windows, so pool clean per-engine windows the same way as eval but
    WITHOUT injection, from pre-onset (early) engine portions.
    """
    engines = _load_engines()
    Xs, ys = [], []
    rng = np.random.default_rng(seed + 2)
    order = list(range(len(engines)))
    rng.shuffle(order)
    for ei in order:
        u, feats, rul = engines[ei]
        d = len(feats) // 2
        head_feats = feats[:d]          # pre-onset (clean) portion
        head_rul = rul[:d]
        if head_feats.shape[0] < _WIN:
            continue
        Xw, yw = _window_stream(head_feats, derive_served_labels(head_rul))
        Xs.append(Xw)
        ys.append(yw)
        if sum(len(a) for a in ys) >= target:
            break
    X = np.concatenate(Xs, axis=0)
    y = np.concatenate(ys, axis=0)
    return X, y


def build_scenario(drift_type, intensity, k, seed):
    """Build detection batches + eval pool + train fetch + metadata. Does not save."""
    engines = _load_engines()
    units, all_feats, all_rul = reconstruct_per_row()
    sigma = compute_sigma_s9(all_feats)

    batches, onset = _build_detection_batches(all_feats, drift_type, k, sigma, seed)
    target = settings.shadow_min_predictions
    eval_X, eval_y, eval_prov = _build_eval_pool(engines, drift_type, k, sigma, seed, target)
    train_X, train_y = _build_train_fetch(all_feats, all_rul, seed, target)

    # batches stored as one stacked array (n_batches, _BATCH, 14) for the .npz
    det_batches = np.stack(batches)

    return {
        "drift_type": drift_type,
        "k": float(k),
        "seed": int(seed),
        "sigma_s9": float(sigma),
        "det_batches": det_batches,
        "onset_batch": int(onset),
        "batch_size": int(_BATCH),
        "batch_interval_s": float(settings.drift_batch_interval_s),
        "eval_X": eval_X,
        "eval_y": eval_y,
        "eval_provenance": eval_prov,
        "eval_n": int(len(eval_y)),
        "train_X": train_X,
        "train_y": train_y,
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
        det_batches=scenario["det_batches"], onset_batch=scenario["onset_batch"],
        batch_size=scenario["batch_size"], batch_interval_s=scenario["batch_interval_s"],
        eval_X=scenario["eval_X"], eval_y=scenario["eval_y"],
        eval_provenance=scenario["eval_provenance"], eval_n=scenario["eval_n"],
        train_X=scenario["train_X"], train_y=scenario["train_y"],
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
        "det_batches": d["det_batches"], "onset_batch": int(d["onset_batch"]),
        "batch_size": int(d["batch_size"]), "batch_interval_s": float(d["batch_interval_s"]),
        "eval_X": d["eval_X"], "eval_y": d["eval_y"],
        "eval_provenance": d["eval_provenance"], "eval_n": int(d["eval_n"]),
        "train_X": d["train_X"], "train_y": d["train_y"],
    }


class ReplayCursor:
    """Serves detection batches, train fetch, and eval pool from one scenario."""

    def __init__(self, scenario):
        self.s = scenario

    def n_batches(self):
        return self.s["det_batches"].shape[0]

    def onset_batch(self):
        return self.s["onset_batch"]

    def detector_batch(self, i):
        """Batch i as DataFrame[FEATURE_COLUMNS] for compute_drift."""
        return pd.DataFrame(self.s["det_batches"][i], columns=FEATURE_COLUMNS)

    def retrain_train_fetch(self):
        """(X,y) clean pre-onset windows the challenger trains on."""
        return self.s["train_X"], self.s["train_y"]

    def eval_pool(self):
        """(eval_X (n,_WIN,14), eval_y (n,)) pooled drifted single-engine windows."""
        return self.s["eval_X"], self.s["eval_y"]
