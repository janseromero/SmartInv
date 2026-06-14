"""The pure health-scoring function (CV2.E3.S2).

Deterministic: no I/O, no randomness, no clock — ``days_since_movement`` is
passed in. Fully unit-tested; this is the model-deterministic core.
"""

from __future__ import annotations

from api.scoring.model import (
    OBSOLETE_DAYS,
    OBSOLETE_STATUSES,
    SCORE_VERSION,
    SLOW_DAYS,
    WEIGHTS,
    Classification,
    ScoreInput,
    ScoreResult,
)

_BADGE_LABELS = {
    "excess": "Excess",
    "slow_moving": "Slow-moving",
    "obsolete": "Obsolete",
    "stockout": "Stockout risk",
    "dq": "DQ risk",
}


def _severities(inp: ScoreInput) -> dict[str, float]:
    on_hand = inp.on_hand
    days = inp.days_since_movement if inp.days_since_movement is not None else 10**6
    is_retired = inp.status is not None and inp.status.upper() in OBSOLETE_STATUSES

    obsolete = 1.0 if (on_hand > 0 and (days >= OBSOLETE_DAYS or is_retired)) else 0.0

    if on_hand <= 0:
        stockout = 1.0
    elif inp.min_level is not None and on_hand <= inp.min_level:
        stockout = 0.5
    else:
        stockout = 0.0

    if inp.max_level is not None and inp.max_level > 0 and on_hand > inp.max_level:
        excess = min(1.0, ((on_hand - inp.max_level) / inp.max_level) / 3.0)
    else:
        excess = 0.0

    slow = 1.0 if (on_hand > 0 and not obsolete and SLOW_DAYS <= days < OBSOLETE_DAYS) else 0.0

    missing = (0 if inp.has_description else 1) + (0 if inp.unit_cost is not None else 1)
    dq = missing / 2.0

    return {
        "obsolete": obsolete,
        "stockout": stockout,
        "excess": excess,
        "slow_moving": slow,
        "dq": dq,
    }


def badges_from_dimensions(dimensions: dict[str, float]) -> list[str]:
    """Active badge labels for a (possibly persisted) dimension breakdown."""
    return [_BADGE_LABELS[k] for k in _BADGE_LABELS if dimensions.get(k, 0.0) > 0]


def _classify(sev: dict[str, float]) -> Classification:
    if sev["obsolete"] > 0 or sev["stockout"] >= 1.0:
        return Classification.OBSOLETE_RISK
    if sev["excess"] > 0 or sev["slow_moving"] > 0:
        return Classification.EXCESS_SLOW
    if sev["dq"] > 0:
        return Classification.DQ_RISK
    return Classification.HEALTHY


def score_item(inp: ScoreInput) -> ScoreResult:
    """Return the 0–100 health score and breakdown for one item."""
    sev = _severities(inp)
    penalty = min(1.0, sum(WEIGHTS[k] * sev[k] for k in WEIGHTS))
    score = round(100 * (1 - penalty))
    return ScoreResult(
        score=score,
        classification=_classify(sev),
        badges=badges_from_dimensions(sev),
        dimensions=sev,
        version=SCORE_VERSION,
    )
