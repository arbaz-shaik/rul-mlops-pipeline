"""Prometheus metric objects.

Central definition point so each metric is registered exactly once and shared
by every module that reads or sets it. Defining a metric in two modules raises
a duplicate-timeseries error; importing from here avoids that and guarantees
the object producers set is the object exposed on /metrics and scraped into
Grafana.
"""
from prometheus_client import Gauge, Counter

drift_score_current = Gauge(
    "drift_score_current",
    "Current aggregate (max) PSI drift score from the latest drift check",
)

shadow_min_predictions_hit = Counter(
    "shadow_min_predictions_hit",
    "Times the shadow validation window (min predictions) was reached",
)
