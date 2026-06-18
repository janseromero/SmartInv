"""Demand-forecasting package (CV3.E1).

Probabilistic intermittent-demand forecasting tuned for MRO patterns. The MVP
baseline is deterministic Croston / TSB (no LightGBM) with quantile bands
derived from historical dispersion. Mirrors the scoring/dedup/anomaly packages:
pure value objects (``model``), a pure deterministic core (``engine``), and an
orchestration service (``service``). LightGBM is deferred to ``forecast-v2``
(ADR-028).
"""
