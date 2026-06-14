"""Unit tests for the deterministic health-scoring engine (CV2.E3)."""

from __future__ import annotations

from api.scoring.engine import score_item
from api.scoring.model import SCORE_VERSION, Classification, ScoreInput


def test_healthy_item_scores_high() -> None:
    result = score_item(
        ScoreInput(
            on_hand=50,
            min_level=10,
            max_level=100,
            unit_cost=20.0,
            has_description=True,
            days_since_movement=30,
        )
    )
    assert result.score == 100
    assert result.classification is Classification.HEALTHY
    assert result.badges == []
    assert result.version == SCORE_VERSION


def test_obsolete_when_no_movement_24_months() -> None:
    result = score_item(
        ScoreInput(on_hand=40, max_level=100, unit_cost=10.0, days_since_movement=800)
    )
    assert "Obsolete" in result.badges
    assert result.classification is Classification.OBSOLETE_RISK
    assert result.is_disposal_candidate is True
    assert result.score < 50


def test_never_moved_with_stock_is_obsolete() -> None:
    result = score_item(ScoreInput(on_hand=10, unit_cost=5.0, days_since_movement=None))
    assert result.is_disposal_candidate is True


def test_retired_status_is_obsolete() -> None:
    result = score_item(
        ScoreInput(on_hand=5, unit_cost=5.0, days_since_movement=10, status="RETIRED")
    )
    assert "Obsolete" in result.badges


def test_excess_scales_with_overstock() -> None:
    mild = score_item(ScoreInput(on_hand=120, max_level=100, unit_cost=1.0, days_since_movement=10))
    severe = score_item(
        ScoreInput(on_hand=500, max_level=100, unit_cost=1.0, days_since_movement=10)
    )
    assert "Excess" in mild.badges
    assert severe.dimensions["excess"] > mild.dimensions["excess"]
    assert severe.score < mild.score
    assert mild.classification is Classification.EXCESS_SLOW


def test_stockout_when_empty() -> None:
    result = score_item(ScoreInput(on_hand=0, min_level=5, unit_cost=1.0, days_since_movement=10))
    assert "Stockout risk" in result.badges
    assert result.classification is Classification.OBSOLETE_RISK  # severe stockout
    assert result.dimensions["obsolete"] == 0.0  # empty != dead stock


def test_below_min_is_partial_stockout() -> None:
    result = score_item(ScoreInput(on_hand=3, min_level=5, unit_cost=1.0, days_since_movement=10))
    assert result.dimensions["stockout"] == 0.5


def test_slow_moving_between_6_and_24_months() -> None:
    result = score_item(ScoreInput(on_hand=10, unit_cost=1.0, days_since_movement=300))
    assert "Slow-moving" in result.badges
    assert result.dimensions["obsolete"] == 0.0


def test_data_quality_penalty_for_missing_fields() -> None:
    result = score_item(
        ScoreInput(
            on_hand=50, max_level=100, has_description=False, unit_cost=None, days_since_movement=10
        )
    )
    assert result.dimensions["dq"] == 1.0
    assert "DQ risk" in result.badges
    assert result.classification is Classification.DQ_RISK


def test_score_is_clamped_and_deterministic() -> None:
    worst = ScoreInput(
        on_hand=1000, max_level=10, has_description=False, unit_cost=None, days_since_movement=900
    )
    a = score_item(worst)
    b = score_item(worst)
    assert 0 <= a.score <= 100
    assert a == b  # deterministic
