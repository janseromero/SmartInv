"""Unit tests for the deterministic duplicate-detection engine (CV2.E4)."""

from __future__ import annotations

from api.dedup.engine import blocking_key, normalize, score_pair
from api.dedup.model import DEDUP_VERSION, Band, ItemFacts


def _facts(item_id: str, **kw: object) -> ItemFacts:
    base: dict[str, object] = {"item_number": item_id, "item_type": "SPARE", "uom": "EA"}
    base.update(kw)
    return ItemFacts(item_id=item_id, **base)  # type: ignore[arg-type]


def test_normalize_strips_punctuation_and_stopwords() -> None:
    assert normalize("Bearing, 6204-2RS for Pump") == ["2rs", "6204", "bearing", "pump"]
    assert normalize(None) == []
    assert normalize("") == []


def test_blocking_key_groups_by_type_uom_prefix() -> None:
    a = _facts("a", manufacturer_part="SKF-6204")
    b = _facts("b", manufacturer_part="SKF-6205")
    assert blocking_key(a) == blocking_key(b)  # same type+uom+prefix


def test_near_identical_descriptions_are_probable() -> None:
    a = _facts("11111111-1111-1111-1111-111111111111", description="Ball bearing 6204 2RS sealed")
    b = _facts("22222222-2222-2222-2222-222222222222", description="Bearing ball 6204 2RS sealed")
    result = score_pair(a, b)
    assert result is not None
    assert result.band is Band.PROBABLE
    assert result.confidence >= 0.85
    assert result.version == DEDUP_VERSION


def test_canonical_ordering_is_stable() -> None:
    a = _facts("bbbb", description="Hydraulic filter 10 micron")
    b = _facts("aaaa", description="Hydraulic filter 10 micron")
    result = score_pair(a, b)
    assert result is not None
    assert result.item_a == "aaaa"
    assert result.item_b == "bbbb"


def test_manufacturer_exact_match_lifts_confidence() -> None:
    a = _facts("a", description="Seal kit", manufacturer_part="PARKER-PK1234")
    b = _facts("b", description="Seal kit", manufacturer_part="PARKER-PK1234")
    with_mfr = score_pair(a, b)
    without = score_pair(_facts("a", description="Seal kit"), _facts("b", description="Seal kit"))
    assert with_mfr is not None and without is not None
    assert with_mfr.confidence > without.confidence
    assert with_mfr.features["manufacturer"] == 1.0


def test_unrelated_items_drop_below_floor() -> None:
    a = _facts("a", description="Hydraulic pump assembly", unit_cost=1200.0)
    b = _facts("b", description="Safety gloves nitrile", unit_cost=3.0)
    assert score_pair(a, b) is None


def test_partial_manufacturer_prefix_is_half() -> None:
    a = _facts("a", description="Gasket", manufacturer_part="MANN-W7123")
    b = _facts("b", description="Gasket", manufacturer_part="MANN-W7123-XL")
    result = score_pair(a, b)
    assert result is not None
    assert result.features["manufacturer"] == 0.5


def test_scoring_is_deterministic() -> None:
    a = _facts("a", description="Coupling spider element L100")
    b = _facts("b", description="Coupling spider element L100 spare")
    assert score_pair(a, b) == score_pair(a, b)


def test_cost_proximity_rewards_close_prices() -> None:
    a = _facts("a", description="V-belt drive", unit_cost=100.0)
    b = _facts("b", description="V-belt drive", unit_cost=105.0)
    result = score_pair(a, b)
    assert result is not None
    assert result.features["unit_cost"] > 0.9
