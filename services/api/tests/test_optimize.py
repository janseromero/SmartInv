"""Unit tests for the deterministic inventory-optimization engine (CV3.E2)."""

from __future__ import annotations

from typing import Any

from api.optimize.engine import monte_carlo_stockout, optimize_item, z_for
from api.optimize.model import OPT_VERSION, Action, OptimizeInput, OptimizeResult


def _opt(**kw: Any) -> OptimizeResult:
    base: dict[str, Any] = {
        "demand_rate": 20.0,
        "demand_cv": 0.3,
        "unit_cost": 50.0,
        "on_hand": 60.0,
        "current_min": 5.0,
        "current_max": 40.0,
        "lead_time_days": 30.0,
        "demand_events": 10,
    }
    base.update(kw)
    return optimize_item(OptimizeInput(**base))


def test_safety_stock_grows_with_service_level() -> None:
    low = _opt(service_level=0.90)
    high = _opt(service_level=0.99)
    assert high.safety_stock > low.safety_stock
    assert high.reorder_point > low.reorder_point


def test_reorder_point_covers_lead_time_demand() -> None:
    result = _opt(demand_rate=20.0, lead_time_days=30.0)  # ~20 units over 1 period
    # ROP = mean lead-time demand (~20) + safety stock (> 0).
    assert result.reorder_point >= 20
    assert result.version == OPT_VERSION


def test_monte_carlo_is_deterministic_and_matches_service_level() -> None:
    a = monte_carlo_stockout(20.0, 6.0, 30.0)
    b = monte_carlo_stockout(20.0, 6.0, 30.0)
    assert a == b  # same seed -> same result
    # At a reorder point well above mean, stockout probability is small.
    assert 0.0 <= a < 0.1


def test_buy_action_when_on_hand_below_reorder() -> None:
    result = _opt(on_hand=1.0, demand_rate=30.0, lead_time_days=45.0)
    assert result.recommended_action is Action.BUY


def test_reduce_excess_when_massively_overstocked() -> None:
    result = _opt(on_hand=5000.0, current_max=4000.0, demand_rate=2.0, demand_cv=0.2)
    assert result.recommended_action is Action.REDUCE_EXCESS


def test_pareto_frontier_is_monotonic() -> None:
    result = _opt()
    assert len(result.pareto) == 4
    # Higher service level -> lower stockout, higher (or equal) capital.
    for i in range(len(result.pareto) - 1):
        earlier, later = result.pareto[i], result.pareto[i + 1]
        assert later.service_level > earlier.service_level
        assert later.stockout_prob < earlier.stockout_prob
        assert later.capital >= earlier.capital


def test_z_for_picks_nearest_service_level() -> None:
    assert z_for(0.95) == 1.6449
    assert z_for(0.99) == 2.3263


def test_confidence_in_bounds() -> None:
    weak = _opt(demand_events=1, demand_cv=1.4)
    strong = _opt(demand_events=24, demand_cv=0.1)
    assert 0.3 <= weak.confidence <= strong.confidence <= 0.95
