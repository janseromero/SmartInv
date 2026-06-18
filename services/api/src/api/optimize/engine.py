"""The pure inventory-optimization functions (CV3.E2.S1-S4).

Closed-form inventory theory + a seeded Monte-Carlo stockout estimator. The
only randomness is the Monte-Carlo draw, which is fully reproducible from
``MONTE_CARLO_SEED``. Everything else is deterministic. Fully unit-tested.
"""

from __future__ import annotations

import random

from api.optimize.model import (
    HOLDING_RATE,
    MONTE_CARLO_N,
    MONTE_CARLO_SEED,
    OPT_VERSION,
    ORDERING_COST,
    PARETO_SERVICE_LEVELS,
    PERIOD_DAYS,
    PERIODS_PER_YEAR,
    Z_BY_SERVICE_LEVEL,
    Action,
    OptimizeInput,
    OptimizeResult,
    ParetoPoint,
)


def z_for(service_level: float) -> float:
    """Nearest tabulated standard-normal quantile for a service level."""
    return float(min(Z_BY_SERVICE_LEVEL.items(), key=lambda kv: abs(kv[0] - service_level))[1])


def _sigma_lead_time(inp: OptimizeInput, lt_periods: float) -> float:
    """Std dev of demand over the lead time (demand + lead-time variability)."""
    sigma_demand = inp.demand_rate * inp.demand_cv
    sigma_lt_periods = lt_periods * inp.lead_time_cv
    # Variance of lead-time demand = LT·σ_d² + d²·σ_LT² (standard formula).
    variance = lt_periods * sigma_demand**2 + (inp.demand_rate**2) * (sigma_lt_periods**2)
    return float(variance**0.5)


def _eoq(annual_demand: float, unit_cost: float | None, fallback: float) -> float:
    holding = HOLDING_RATE * unit_cost if unit_cost else 0.0
    if holding <= 0 or annual_demand <= 0:
        return fallback
    return float((2.0 * annual_demand * ORDERING_COST / holding) ** 0.5)


def monte_carlo_stockout(
    mean_lt: float,
    sigma_lt: float,
    reorder_point: float,
    *,
    seed: int = MONTE_CARLO_SEED,
    n: int = MONTE_CARLO_N,
) -> float:
    """Fraction of lead-time cycles whose demand exceeds the reorder point."""
    if sigma_lt <= 0:
        return 0.0 if mean_lt <= reorder_point else 1.0
    rng = random.Random(seed)  # noqa: S311 — simulation, not crypto
    stockouts = 0
    for _ in range(n):
        demand = rng.gauss(mean_lt, sigma_lt)
        if demand > reorder_point:
            stockouts += 1
    return round(stockouts / n, 4)


def _action(inp: OptimizeInput, min_level: float, max_level: float) -> Action:
    # Physical stock first (buy / liquidate), then policy caps (max / min).
    if inp.on_hand <= min_level:
        return Action.BUY
    if inp.on_hand > max_level * 2:
        return Action.REDUCE_EXCESS
    if inp.current_max is not None and inp.current_max > max_level * 1.3:
        return Action.LOWER_MAX
    if inp.current_min is not None and inp.current_min < min_level * 0.7:
        return Action.RAISE_MIN
    return Action.HOLD


def _confidence(inp: OptimizeInput) -> float:
    signal = min(1.0, inp.demand_events / 12.0)
    noise = min(1.0, inp.demand_cv)
    return round(max(0.3, min(0.95, 0.45 + 0.4 * signal - 0.25 * noise)), 4)


def optimize_item(inp: OptimizeInput) -> OptimizeResult:
    """Return the recommended min/max + reorder policy for one item."""
    lt_periods = max(0.0, inp.lead_time_days / PERIOD_DAYS)
    mean_lt = inp.demand_rate * lt_periods
    sigma_lt = _sigma_lead_time(inp, lt_periods)

    z = z_for(inp.service_level)
    safety_stock = z * sigma_lt
    reorder_point = mean_lt + safety_stock

    annual_demand = inp.demand_rate * PERIODS_PER_YEAR
    eoq = _eoq(annual_demand, inp.unit_cost, fallback=max(mean_lt, 1.0))

    min_level = reorder_point
    max_level = reorder_point + eoq

    stockout = monte_carlo_stockout(mean_lt, sigma_lt, reorder_point)
    current_rop = inp.current_min if inp.current_min is not None else 0.0
    current_stockout = monte_carlo_stockout(mean_lt, sigma_lt, current_rop)

    unit_cost = inp.unit_cost or 0.0
    capital_delta = (max_level - (inp.current_max or 0.0)) * unit_cost

    pareto: list[ParetoPoint] = []
    for sl in PARETO_SERVICE_LEVELS:
        ss = z_for(sl) * sigma_lt
        rop = mean_lt + ss
        capital = (rop + eoq) * unit_cost
        pareto.append(
            ParetoPoint(service_level=sl, capital=round(capital, 2), stockout_prob=round(1 - sl, 4))
        )

    return OptimizeResult(
        min_level=round(min_level),
        max_level=round(max_level),
        reorder_point=round(reorder_point),
        safety_stock=round(safety_stock),
        eoq=round(eoq),
        recommended_action=_action(inp, min_level, max_level),
        stockout_prob=stockout,
        current_stockout_prob=current_stockout,
        capital_delta=round(capital_delta, 2),
        confidence=_confidence(inp),
        pareto=pareto,
        version=OPT_VERSION,
    )
