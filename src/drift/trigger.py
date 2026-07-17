"""PSI drift trigger.

Consumes detector's drift score, applies the configured PSI threshold, and
emits the retrain signal. Detector measures; trigger decides. Single PSI
condition only: no residual EMA (that is a later dual-trigger change).
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
