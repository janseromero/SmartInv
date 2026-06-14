"""Deterministic inventory health scoring (CV2.E3).

A pure, versioned 0–100 score per item combining excess, slow-moving, obsolete
(dead stock), stockout risk, and data-quality flags. No LLM involvement
(AGENTS non-negotiable #3). Same inputs + same version => same score.
"""

from api.scoring.engine import badges_from_dimensions, score_item
from api.scoring.model import (
    SCORE_VERSION,
    WEIGHTS,
    Classification,
    ScoreInput,
    ScoreResult,
)

__all__ = [
    "SCORE_VERSION",
    "WEIGHTS",
    "Classification",
    "ScoreInput",
    "ScoreResult",
    "badges_from_dimensions",
    "score_item",
]
