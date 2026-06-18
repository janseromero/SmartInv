"""Anomaly-detection package (CV2.E5).

Deterministic statistical detectors that surface unusual events for planner
review: consumption spikes (robust z-score on issue quantities), unit-price
jumps (robust z-score / SPC on the price series), and negative available
balances (a reservation-integrity rule). Mirrors the scoring/dedup packages:
pure value objects (``model``), a pure deterministic core (``engine``), and an
orchestration service (``service``). Isolation Forest is deliberately *not*
used \u2014 see ADR-027.
"""
