"""Duplicate-detection package (CV2.E4).

A deterministic blocked-similarity engine that surfaces probable item-master
duplicates. Mirrors the scoring package's shape: pure value objects
(``model``), a pure deterministic core (``engine``), and an orchestration
service (``service``). The embedding + classifier variant is deferred to a
``dedup-v2`` once CV5 fixes the embedding model (ADR-026).
"""
