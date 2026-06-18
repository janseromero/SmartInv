"""The pure duplicate-detection functions (CV2.E4.S2/S3).

Deterministic: no I/O, no randomness, no clock. ``normalize`` and
``blocking_key`` shrink the O(n²) comparison to within-block pairs;
``score_pair`` returns a calibrated-by-construction confidence in [0, 1].
Fully unit-tested; this is the model-deterministic core.
"""

from __future__ import annotations

import re

from api.dedup.model import (
    DEDUP_VERSION,
    POSSIBLE_THRESHOLD,
    PROBABLE_THRESHOLD,
    WEIGHTS,
    Band,
    ItemFacts,
    PairResult,
)

# Tokens shorter than this are ignored unless purely alphanumeric codes.
_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Common MRO noise words that carry no discriminative signal.
_STOPWORDS = frozenset({"the", "a", "an", "of", "for", "with", "and", "or", "to", "in", "by", "mm"})


def normalize(text: str | None) -> list[str]:
    """Lowercase, strip punctuation, split into a deduped, sorted token list."""
    if not text:
        return []
    tokens = _TOKEN_RE.findall(text.lower())
    return sorted({t for t in tokens if t not in _STOPWORDS})


def _block_prefix(facts: ItemFacts) -> str:
    """A coarse term true duplicates share.

    Prefers the manufacturer part-number prefix when present (the strongest
    block), but MPNs are absent in raw item masters (extraction is CV7), so we
    fall back to the first 4 chars of the alphabetically-first description
    token. Item numbers are deliberately *not* used: duplicates carry
    different item numbers, so blocking on them would never co-locate a pair.
    """
    if facts.manufacturer_part:
        cleaned = re.sub(r"[^a-z0-9]", "", facts.manufacturer_part.lower())
        if cleaned:
            return cleaned[:4]
    tokens = normalize(facts.description)
    return tokens[0][:4] if tokens else ""


def blocking_key(facts: ItemFacts) -> tuple[str, str, str]:
    """Coarse key capping candidate pairs: (item_type, uom, block-prefix) (S2)."""
    return (
        (facts.item_type or "").upper(),
        (facts.uom or "").upper(),
        _block_prefix(facts),
    )


def _jaccard(a: list[str], b: list[str]) -> float:
    if not a and not b:
        return 0.0
    sa, sb = set(a), set(b)
    union = sa | sb
    return len(sa & sb) / len(union) if union else 0.0


def _manufacturer_match(a: ItemFacts, b: ItemFacts) -> float:
    pa, pb = a.manufacturer_part, b.manufacturer_part
    if not pa or not pb:
        return 0.0
    na = re.sub(r"[^a-z0-9]", "", pa.lower())
    nb = re.sub(r"[^a-z0-9]", "", pb.lower())
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return 0.5 if (na.startswith(nb) or nb.startswith(na)) else 0.0


def _cost_proximity(a: ItemFacts, b: ItemFacts) -> float:
    ca, cb = a.unit_cost, b.unit_cost
    if ca is None or cb is None:
        return 0.0
    hi = max(ca, cb)
    if hi <= 0:
        return 1.0 if ca == cb else 0.0
    return max(0.0, 1.0 - abs(ca - cb) / hi)


def pair_features(a: ItemFacts, b: ItemFacts) -> dict[str, float]:
    """Per-dimension similarity in [0, 1] for an item pair."""
    return {
        "description": _jaccard(normalize(a.description), normalize(b.description)),
        "manufacturer": _manufacturer_match(a, b),
        "uom": 1.0 if (a.uom and b.uom and a.uom.upper() == b.uom.upper()) else 0.0,
        "item_type": (
            1.0
            if (a.item_type and b.item_type and a.item_type.upper() == b.item_type.upper())
            else 0.0
        ),
        "unit_cost": _cost_proximity(a, b),
    }


def score_pair(a: ItemFacts, b: ItemFacts) -> PairResult | None:
    """Return a scored pair, or ``None`` if below the "possible" floor.

    Canonical ordering guarantees ``item_a < item_b`` so a pair is stored once.
    """
    features = pair_features(a, b)
    confidence = round(sum(WEIGHTS[k] * features[k] for k in WEIGHTS), 4)
    if confidence < POSSIBLE_THRESHOLD:
        return None

    band = Band.PROBABLE if confidence >= PROBABLE_THRESHOLD else Band.POSSIBLE
    lo, hi = sorted((a.item_id, b.item_id))
    return PairResult(
        item_a=lo,
        item_b=hi,
        confidence=confidence,
        band=band,
        features=features,
        version=DEDUP_VERSION,
    )
