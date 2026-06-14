# Design Decisions Log

One entry per design decision. Written at time of decision.
Format: [Date] [Component] Decision: chose X over Y because Z.

---

## Entries

[2026-06-08] Project: chose CMAPSS FD001 over other RUL datasets
because it is the standard benchmark for turbofan RUL prediction
with published RMSE baselines for direct comparison.

[2026-06-09] Drift Detection: chose PSI over KL divergence as the
primary drift metric because PSI is more interpretable for tabular
sensor data and maps directly to Evidently AI built-in reporting
without custom implementation.

[2026-06-10] Safe Deployment: chose shadow validation over canary
deployment because shadow mode requires no traffic splitting logic
and allows full parallel evaluation of the candidate model before
any production exposure.
