"""Health-scoring value objects, weights, and thresholds (CV2.E3.S1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

SCORE_VERSION = "health-v1"

# Thresholds (days).
OBSOLETE_DAYS = 730  # no usage in 24 months -> obsolete / disposal candidate
SLOW_DAYS = 180  # no usage in 6–24 months -> slow-moving

# Severity weights per dimension (penalty contribution).
WEIGHTS: dict[str, float] = {
    "obsolete": 0.6,
    "stockout": 0.4,
    "excess": 0.3,
    "slow_moving": 0.2,
    "dq": 0.15,
}

OBSOLETE_STATUSES = {"OBSOLETE", "RETIRED", "INACTIVE"}


class Classification(StrEnum):
    HEALTHY = "healthy"
    EXCESS_SLOW = "excess_slow"
    OBSOLETE_RISK = "obsolete_risk"
    DQ_RISK = "dq_risk"


@dataclass(frozen=True)
class ScoreInput:
    """The per-item facts the scorer needs (aggregated across sites)."""

    on_hand: float
    min_level: float | None = None
    max_level: float | None = None
    unit_cost: float | None = None
    has_description: bool = True
    days_since_movement: int | None = None  # None = never moved
    status: str | None = None


@dataclass(frozen=True)
class ScoreResult:
    score: int
    classification: Classification
    badges: list[str] = field(default_factory=list)
    dimensions: dict[str, float] = field(default_factory=dict)
    version: str = SCORE_VERSION

    @property
    def is_disposal_candidate(self) -> bool:
        return self.dimensions.get("obsolete", 0.0) > 0.0
