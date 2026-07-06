"""Unit tests for the grounding validator — the CV5 trust contract (ADR-014)."""

from __future__ import annotations

from api.agent.grounding import check_grounded, expand_allowed, extract_numbers


def test_extracts_plain_currency_percent_and_compact() -> None:
    nums = extract_numbers("We freed $1.2M across 1,240 items at 45% coverage and 0.86 score.")
    assert 1_200_000.0 in nums
    assert 1240.0 in nums
    assert 45.0 in nums
    assert 0.86 in nums


def test_grounded_answer_passes() -> None:
    result = check_grounded(
        "There are 1240 items and 37 critical spares.",
        allowed_values=[1240.0, 37.0],
    )
    assert result.grounded
    assert result.ungrounded == []


def test_ungrounded_number_is_rejected() -> None:
    result = check_grounded(
        "There are 1240 items and 999 critical spares.",
        allowed_values=[1240.0, 37.0],
    )
    assert not result.grounded
    assert 999.0 in result.ungrounded


def test_trivial_small_integers_are_not_flagged() -> None:
    # "3 plants" is prose, not a claim to ground.
    result = check_grounded("Across 3 plants the exposure is 5000.", allowed_values=[5000.0])
    assert result.grounded


def test_formatting_tolerance_matches_compact_and_full() -> None:
    result = check_grounded("Downtime exposure is $1.2M.", allowed_values=[1_200_000.0])
    assert result.grounded


def test_percentage_grounds_against_ratio_via_expand() -> None:
    allowed = expand_allowed([0.9])  # a ratio the model may restate as 90%
    result = check_grounded("Coverage is 90%.", allowed_values=allowed)
    assert result.grounded


def test_fabricated_dollar_figure_is_caught() -> None:
    result = check_grounded(
        "Total downtime exposure is $4,500,000.",
        allowed_values=[1_200_000.0],
    )
    assert not result.grounded
