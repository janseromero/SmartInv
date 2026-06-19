"""The pure operational-risk functions (CV4.E1/E2).

Deterministic: no I/O, no randomness, no clock. Risk = likelihood x consequence;
the dollar exposure is downtime cost x lead time x stockout likelihood. Fully
unit-tested; this is the model-deterministic core.
"""

from __future__ import annotations

from api.risk.model import (
    CONSEQUENCE_FLOOR,
    CRITICAL_AT,
    CRITICAL_SPARE_CRITICALITY,
    DEFAULT_CRITICALITY,
    DEFAULT_ON_TIME_RATE,
    DOWNTIME_COST_PER_DAY,
    HIGH_AT,
    LIKELIHOOD_WEIGHTS,
    MODERATE_AT,
    PERIOD_DAYS,
    RISK_VERSION,
    RiskClass,
    RiskInput,
    RiskResult,
)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _stockout_severity(inp: RiskInput, lead_time_demand: float) -> float:
    """How exposed we are to a stockout: cover vs lead-time demand."""
    if inp.demand_rate <= 0:
        return 0.0  # no demand -> no stockout risk
    if inp.reorder_point is not None and inp.reorder_point > 0:
        # Below the reorder point is the clearest signal.
        return _clamp(1.0 - inp.on_hand / inp.reorder_point)
    if lead_time_demand <= 0:
        return 0.0
    return _clamp(1.0 - inp.on_hand / lead_time_demand)


def _classify(score: int) -> RiskClass:
    if score >= CRITICAL_AT:
        return RiskClass.CRITICAL
    if score >= HIGH_AT:
        return RiskClass.HIGH
    if score >= MODERATE_AT:
        return RiskClass.MODERATE
    return RiskClass.LOW


def _critical_spare(
    inp: RiskInput, criticality: int, stockout_sev: float
) -> tuple[bool, str | None]:
    """Rule-based critical-spare flag with a human-readable reason (S1)."""
    if criticality >= CRITICAL_SPARE_CRITICALITY:
        return True, f"Item criticality {criticality} (downtime/safety impact)."
    if criticality == 3 and inp.single_source and stockout_sev >= 0.5:
        return True, "Single-source item at stockout risk."
    return False, None


def score_risk(inp: RiskInput) -> RiskResult:
    """Return the 0-100 operational-risk score and breakdown for one item."""
    criticality = inp.criticality if inp.criticality is not None else DEFAULT_CRITICALITY
    on_time = inp.on_time_rate if inp.on_time_rate is not None else DEFAULT_ON_TIME_RATE
    lt_periods = max(0.0, inp.lead_time_days / PERIOD_DAYS)
    lead_time_demand = inp.demand_rate * lt_periods

    stockout_sev = _stockout_severity(inp, lead_time_demand)
    lead_time_sev = _clamp(inp.lead_time_days / 90.0)
    supplier_sev = _clamp(1.0 - on_time)

    likelihood = (
        LIKELIHOOD_WEIGHTS["stockout"] * stockout_sev
        + LIKELIHOOD_WEIGHTS["lead_time"] * lead_time_sev
        + LIKELIHOOD_WEIGHTS["supplier"] * supplier_sev
    )
    consequence = CONSEQUENCE_FLOOR + (1.0 - CONSEQUENCE_FLOOR) * ((criticality - 1) / 4.0)

    score = round(100 * _clamp(likelihood) * _clamp(consequence))
    risk_class = _classify(score)

    cost_per_day = DOWNTIME_COST_PER_DAY.get(
        criticality, DOWNTIME_COST_PER_DAY[DEFAULT_CRITICALITY]
    )
    downtime_exposure = round(cost_per_day * inp.lead_time_days * stockout_sev, 2)

    is_critical, reason = _critical_spare(inp, criticality, stockout_sev)

    return RiskResult(
        score=score,
        risk_class=risk_class,
        likelihood=round(likelihood, 4),
        consequence=round(consequence, 4),
        downtime_exposure=downtime_exposure,
        is_critical_spare=is_critical,
        critical_reason=reason,
        breakdown={
            "criticality": float(criticality),
            "stockout": round(stockout_sev, 4),
            "lead_time": round(lead_time_sev, 4),
            "supplier": round(supplier_sev, 4),
            "single_source": 1.0 if inp.single_source else 0.0,
        },
        version=RISK_VERSION,
    )
