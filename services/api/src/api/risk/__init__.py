"""Operational-risk package (CV4.E1/E2).

Deterministic risk scoring + rule-based critical-spare identification. Risk is
likelihood (supply-side) x consequence (criticality / downtime), all explainable
and versioned (``risk-v1``). The graph/GNN variant is deferred to CV14, the
gradient-boosted critical-spare classifier to ``critical-v2`` (ADR-029).
Mirrors the scoring package: ``model`` / ``engine`` / ``service``.
"""
