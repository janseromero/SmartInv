"""Duplicate-detection value objects, weights, and thresholds (CV2.E4.S1/S3).

Deterministic blocked-similarity model (``dedup-v1``). Same inputs + same
version always produce the same pair confidence. Design + weights in
[ADR-026]. The embedding + gradient-boosting variant is deferred to
``dedup-v2`` once CV5 fixes the embedding model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

DEDUP_VERSION = "dedup-v1"

# Confidence band thresholds.
PROBABLE_THRESHOLD = 0.85  # >= this -> "probable" (Done Condition target)
POSSIBLE_THRESHOLD = 0.60  # [this, probable) -> "possible"; below -> dropped

# Feature weights (must sum to 1.0 — the pair confidence is their weighted mean).
# The normalized description is the primary dedup signal and must dominate:
# manufacturer part numbers are often absent in messy item masters, so they
# act as a confidence *bonus*, not a baseline the score depends on. A perfect
# description + UoM + item-type + cost match (no MPN) reaches the 0.85
# "probable" bar; an MPN match on top pushes toward 1.0.
WEIGHTS: dict[str, float] = {
    "description": 0.70,  # token-set similarity on the normalized description
    "manufacturer": 0.10,  # manufacturer part-number prefix match (bonus)
    "uom": 0.08,  # unit-of-measure match
    "item_type": 0.07,  # commodity / item-type match
    "unit_cost": 0.05,  # unit-cost proximity (tie-breaker)
}


class Band(StrEnum):
    PROBABLE = "probable"
    POSSIBLE = "possible"


@dataclass(frozen=True)
class ItemFacts:
    """The per-item facts the matcher needs (one canonical record)."""

    item_id: str
    item_number: str
    description: str | None = None
    uom: str | None = None
    item_type: str | None = None
    unit_cost: float | None = None
    manufacturer_part: str | None = None  # parsed MPN, when available


@dataclass(frozen=True)
class PairResult:
    """A scored candidate pair (canonical ordering: item_a < item_b)."""

    item_a: str
    item_b: str
    confidence: float
    band: Band
    features: dict[str, float] = field(default_factory=dict)
    version: str = DEDUP_VERSION
