"""Operational-risk value objects, weights, and downtime cost basis (CV4.E1).

Deterministic risk model (``risk-v1``). Risk = likelihood (supply-side) x
consequence (criticality). Design + weights in [ADR-029].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

RISK_VERSION = "risk-v1"

PERIOD_DAYS = 30
DEFAULT_CRITICALITY = 3
DEFAULT_ON_TIME_RATE = 0.9
DEFAULT_LEAD_TIME_DAYS = 30

# Likelihood = weighted supply-side risk of not having the part when needed.
LIKELIHOOD_WEIGHTS: dict[str, float] = {
    "stockout": 0.55,  # current cover vs lead-time demand
    "lead_time": 0.20,  # longer lead time = slower recovery
    "supplier": 0.25,  # supplier delivery unreliability
}
# Consequence floor so even a moderate-criticality item carries some weight.
CONSEQUENCE_FLOOR = 0.3

# Downtime cost ($/day) escalates with criticality 1..5 (a documented assumption).
DOWNTIME_COST_PER_DAY: dict[int, float] = {1: 500, 2: 2000, 3: 8000, 4: 25000, 5: 80000}

# Rule-based critical-spare threshold (CV4.E2.S1).
CRITICAL_SPARE_CRITICALITY = 4

# Risk-class band thresholds. The score is risk-weighted exposure
# (P(disruptive stockout) x consequence), so a well-stocked portfolio clusters
# low by construction; these absolute cutoffs flag the genuinely exposed tail.
CRITICAL_AT = 45
HIGH_AT = 25
MODERATE_AT = 12


class RiskClass(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass(frozen=True)
class RiskInput:
    criticality: int | None = None  # 1..5
    on_hand: float = 0.0
    demand_rate: float = 0.0  # per period (from the forecast)
    reorder_point: float | None = None  # from the CV3 policy, if any
    lead_time_days: float = DEFAULT_LEAD_TIME_DAYS
    on_time_rate: float | None = None  # supplier delivery reliability [0,1]
    unit_cost: float | None = None
    single_source: bool = False


@dataclass(frozen=True)
class RiskResult:
    score: int  # 0..100, higher = riskier
    risk_class: RiskClass
    likelihood: float  # 0..1
    consequence: float  # 0..1
    downtime_exposure: float  # $ expected exposure
    is_critical_spare: bool
    critical_reason: str | None
    breakdown: dict[str, float] = field(default_factory=dict)
    version: str = RISK_VERSION
