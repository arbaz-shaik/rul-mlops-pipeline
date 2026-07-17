"""PSI drift detection against the frozen reference distribution.

Measures only: computes per-feature PSI for an incoming batch versus the
Block 37 reference, and returns the aggregate (max) drift score. Does not
apply a threshold or emit a boolean; that is trigger.py (Block 40).
"""
import pandas as pd
from evidently.report import Report
from evidently.metrics import ColumnDriftMetric

from src.config import FEATURE_COLUMNS, settings

# Reference loaded once at import, not per call.
_reference = pd.read_parquet(settings.reference_data_path)


def compute_drift(current_batch: pd.DataFrame):
    """Per-feature PSI of current_batch versus the reference distribution.

    current_batch must already be selected to FEATURE_COLUMNS, scaled with
    the fitted scaler, and column-named s2...s21. Returns (per_feature, aggregate)
    where per_feature is a dict keyed by feature name and aggregate is the max PSI.
    """
    assert list(current_batch.columns) == FEATURE_COLUMNS, (
        f"batch columns {list(current_batch.columns)} != {FEATURE_COLUMNS}"
    )

    metrics = [ColumnDriftMetric(column_name=c, stattest="psi") for c in FEATURE_COLUMNS]
    report = Report(metrics=metrics)
    report.run(reference_data=_reference, current_data=current_batch)

    per_feature = {}
    for m in report.as_dict()["metrics"]:
        result = m["result"]
        per_feature[result["column_name"]] = result["drift_score"]

    aggregate = max(per_feature.values())
    return per_feature, aggregate
