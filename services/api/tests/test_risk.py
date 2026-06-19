"""Unit tests for the deterministic operational-risk engine (CV4.E1/E2)."""

from __future__ import annotations

from api.risk.engine import score_risk
from api.risk.model import RISK_VERSION, RiskClass, RiskInput, RiskResult


def _risk(**kw: object) -> RiskResult:
    base: dict[str, object] = {
        "criticality": 3,
        "on_hand": 50.0,
        "demand_rate": 20.0,
        "reorder_point": 30.0,
        "lead_time_days": 30.0,
        "on_time_rate": 0.9,
        "unit_cost": 100.0,
    }
    base.update(kw)
    return score_risk(RiskInput(**base))  # type: ignore[arg-type]


def test_well_stocked_critical_item_is_low_risk() -> None:
    result = _risk(criticality=5, on_hand=500.0, reorder_point=30.0)
    assert result.risk_class is RiskClass.LOW
    assert result.version == RISK_VERSION


def test_risk_rises_when_below_reorder_point() -> None:
    stocked = _risk(on_hand=100.0, reorder_point=30.0)
    short = _risk(on_hand=5.0, reorder_point=30.0)
    assert short.score > stocked.score
    assert short.breakdown["stockout"] > stocked.breakdown["stockout"]


def test_criticality_amplifies_consequence() -> None:
    low = _risk(criticality=1, on_hand=5.0, reorder_point=30.0)
    high = _risk(criticality=5, on_hand=5.0, reorder_point=30.0)
    assert high.score > low.score
    assert high.consequence > low.consequence


def test_critical_spare_flag_fires_on_high_criticality() -> None:
    result = _risk(criticality=4)
    assert result.is_critical_spare is True
    assert result.critical_reason and "criticality 4" in result.critical_reason


def test_single_source_midcriticality_at_risk_is_critical_spare() -> None:
    result = _risk(criticality=3, on_hand=2.0, reorder_point=30.0, single_source=True)
    assert result.is_critical_spare is True
    assert "Single-source" in (result.critical_reason or "")


def test_no_demand_means_no_stockout_component() -> None:
    result = _risk(demand_rate=0.0, on_hand=0.0)
    assert result.breakdown["stockout"] == 0.0


def test_downtime_exposure_scales_with_criticality_and_shortage() -> None:
    low = _risk(criticality=2, on_hand=1.0, reorder_point=40.0, lead_time_days=30.0)
    high = _risk(criticality=5, on_hand=1.0, reorder_point=40.0, lead_time_days=60.0)
    assert high.downtime_exposure > low.downtime_exposure > 0


def test_risk_is_deterministic() -> None:
    a = _risk(criticality=4, on_hand=10.0, reorder_point=30.0)
    b = _risk(criticality=4, on_hand=10.0, reorder_point=30.0)
    assert a == b


def test_unreliable_supplier_raises_risk() -> None:
    reliable = _risk(on_hand=10.0, reorder_point=30.0, on_time_rate=0.99)
    flaky = _risk(on_hand=10.0, reorder_point=30.0, on_time_rate=0.6)
    assert flaky.score >= reliable.score
    assert flaky.breakdown["supplier"] > reliable.breakdown["supplier"]
