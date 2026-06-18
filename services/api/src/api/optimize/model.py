"""Inventory-optimization value objects, policy constants, and z-table (CV3.E2).

Deterministic closed-form model (``optimize-eoq-v1``). Design in [ADR-028].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

OPT_VERSION = "optimize-eoq-v1"

# Policy assumptions (carried into every recommendation's envelope).
HOLDING_RATE = 0.25  # annual holding cost as a fraction of unit cost
ORDERING_COST = 75.0  # fixed cost per purchase order ($)
DEFAULT_SERVICE_LEVEL = 0.95
PERIOD_DAYS = 30
PERIODS_PER_YEAR = 365.0 / PERIOD_DAYS
DEFAULT_LEAD_TIME_DAYS = 30
LEAD_TIME_CV = 0.3  # lead-time variability when not otherwise known

# Seeded Monte-Carlo settings (reproducible stockout estimate).
MONTE_CARLO_N = 4000
MONTE_CARLO_SEED = 42

# Standard-normal inverse CDF at common service levels.
Z_BY_SERVICE_LEVEL: dict[float, float] = {
    0.80: 0.8416,
    0.90: 1.2816,
    0.95: 1.6449,
    0.975: 1.9600,
    0.99: 2.3263,
}
PARETO_SERVICE_LEVELS = (0.90, 0.95, 0.975, 0.99)


class Action(StrEnum):
    BUY = "buy"
    RAISE_MIN = "raise_min"
    LOWER_MAX = "lower_max"
    REDUCE_EXCESS = "reduce_excess"
    HOLD = "hold"


@dataclass(frozen=True)
class OptimizeInput:
    demand_rate: float  # P50 demand per period (from the forecast)
    demand_cv: float
    unit_cost: float | None
    on_hand: float
    current_min: float | None = None
    current_max: float | None = None
    lead_time_days: float = DEFAULT_LEAD_TIME_DAYS
    lead_time_cv: float = LEAD_TIME_CV
    service_level: float = DEFAULT_SERVICE_LEVEL
    demand_events: int = 0


@dataclass(frozen=True)
class ParetoPoint:
    service_level: float
    capital: float
    stockout_prob: float


@dataclass(frozen=True)
class OptimizeResult:
    min_level: int
    max_level: int
    reorder_point: int
    safety_stock: int
    eoq: int
    recommended_action: Action
    stockout_prob: float  # of the recommended policy (Monte Carlo)
    current_stockout_prob: float
    capital_delta: float  # change in capital at the max level vs current
    confidence: float
    pareto: list[ParetoPoint] = field(default_factory=list)
    version: str = OPT_VERSION
