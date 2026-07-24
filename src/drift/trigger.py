"""PSI drift trigger.

Consumes detector's drift score, applies the configured PSI threshold, and
emits the retrain signal. Detector measures; trigger decides. Single PSI
condition only: no residual EMA (that is a later dual-trigger change).

check_drift is the stateless per-batch primitive used in production. For
experiment replay over a batch SEQUENCE, find_rising_crossings applies an
edge-trigger over the sequence (below->above transitions), used for the
recurring condition where drift arrives, clears, and returns. Single-onset
scenarios (sudden, gradual) yield exactly one rising crossing through it, so it
is regression-safe for those by construction.
"""
import logging

from src.config import settings
from src.serving.metrics import drift_score_current

log = logging.getLogger(__name__)


def check_drift(per_feature: dict, aggregate: float) -> bool:
    """Apply the PSI threshold to the aggregate drift score.

    Sets the drift_score_current gauge to the aggregate on every check, then
    returns True when aggregate exceeds settings.psi_drift_threshold.
    """
    drift_score_current.set(aggregate)
    fired = aggregate > settings.psi_drift_threshold
    if fired:
        worst = max(per_feature, key=per_feature.get)
        log.info(
            "drift trigger FIRED: max PSI %.4f on feature %s (threshold %.2f)",
            aggregate, worst, settings.psi_drift_threshold,
        )
    else:
        log.info(
            "drift trigger clear: max PSI %.4f (threshold %.2f)",
            aggregate, settings.psi_drift_threshold,
        )
    return fired


def find_rising_crossings(psi_values, threshold=None):
    """Edge-triggered rising crossings over a PSI sequence.

    Returns the list of indices where PSI rises from at/below the threshold to
    above it, re-arming only after PSI returns at/below threshold. A sustained
    above-threshold run yields ONE crossing (the rising edge), not one per batch.

    Single-onset (sudden, gradual): PSI starts below, crosses once, stays above
    -> exactly one crossing (regression-safe). Recurring: crosses, clears
    (re-arms), crosses again -> one crossing per onset.
    """
    thr = settings.psi_drift_threshold if threshold is None else threshold
    crossings = []
    armed = True  # armed while PSI is at/below threshold, ready for a rising edge
    for i, psi in enumerate(psi_values):
        if psi > thr and armed:
            crossings.append(i)
            armed = False
        elif psi <= thr:
            armed = True
    return crossings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
