"""Prometheus metric objects.

Central definition point for metric objects so each is registered exactly
once and shared by every module that reads or sets it. Defining a metric in
two modules raises a duplicate-timeseries error; importing from here avoids
that and guarantees the object set by producers is the object exposed on the
/metrics endpoint and scraped into Grafana.
"""
from prometheus_client import Gauge

drift_score_current = Gauge(
    "drift_score_current",
    "Current aggregate (max) PSI drift score from the latest drift check",
)
