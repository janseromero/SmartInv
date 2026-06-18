"""Anomaly-detection value objects and thresholds (CV2.E5).

Deterministic statistical model (``anomaly-v1``). Same inputs + same version
always produce the same flags. Design + thresholds in [ADR-027]. Isolation
Forest is deliberately not used: a robust-z / SPC approach is reproducible,
dependency-free, and satisfies the Done Condition.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

ANOMALY_VERSION = "anomaly-v1"

# Robust z-score threshold (median + k·scaled-MAD). 3.5 is the common SPC choice.
Z_THRESHOLD = 3.5
# A flag at/above this z is "crit"; between Z_THRESHOLD and this is "warn".
CRIT_Z = 7.0
# Minimum history before a baseline is trustworthy (else we don't flag).
MIN_HISTORY = 5
# Consistency constant making MAD a consistent estimator of the std dev.
MAD_SCALE = 1.4826

# Practical-significance floors: a flag must be statistically unusual (z above
# threshold) AND materially large. Without these, a 7% price wiggle or a 1.5x
# usage trips the z-test on a very tight series — statistically true but
# operationally noise. These guards mirror how real SPC alerting works.
MIN_SPIKE_RATIO = 3.0  # consumption must be >= 3x the median to flag
PRICE_RATIO_HI = 2.0  # price >= 2x median ...
PRICE_RATIO_LO = 0.5  # ... or <= 0.5x median to flag


class AnomalyType(StrEnum):
    CONSUMPTION_SPIKE = "consumption_spike"
    PRICE_JUMP = "price_jump"
    NEGATIVE_BALANCE = "negative_balance"


class Severity(StrEnum):
    WARN = "warn"
    CRIT = "crit"


@dataclass(frozen=True)
class IssueEvent:
    """One issue/usage transaction for an item."""

    txn_id: uuid.UUID
    source_id: str
    quantity: float
    unit_cost: float | None
    txn_date: datetime | None


@dataclass(frozen=True)
class BalanceState:
    """A per-item-per-location stock balance."""

    balance_id: uuid.UUID
    on_hand: float
    available: float
    reserved: float


@dataclass(frozen=True)
class AnomalyResult:
    """A detected anomaly, ready to persist."""

    type: AnomalyType
    target_type: str  # "transaction" | "balance"
    target_id: uuid.UUID
    source_record_id: str | None
    score: float  # robust z (or magnitude for rule-based)
    severity: Severity
    detected_for: datetime | None
    evidence: dict[str, Any] = field(default_factory=dict)
    version: str = ANOMALY_VERSION
