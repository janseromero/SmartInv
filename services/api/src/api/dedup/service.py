"""Duplicate-detection orchestration: gather, block, score, persist, register.

Loads canonical item facts, blocks them to cap comparisons, runs the pure
engine on within-block pairs, upserts candidate pairs into
``ml.duplicate_candidates``, and registers the model version in
``ml.model_registry`` for reproducibility. Recompute is on-demand (CLI / admin
endpoint); a nightly Dramatiq schedule is deferred (mirrors CV2.E3).

A "merge" decision never mutates source rows: it records the planner's verdict
on the candidate and emits a ``ml.recommendations`` envelope routed through CV6
approval (AGENTS.md non-negotiable #2 — agents/engines propose, deterministic
workflow disposes). CV6 does not exist yet, so the envelope is staged with
``status='proposed'`` and the actual merge is wired when CV6 lands.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.inventory import Item
from api.db.models.ml import DuplicateCandidate, ModelRegistry, Recommendation
from api.dedup.engine import blocking_key, score_pair
from api.dedup.model import DEDUP_VERSION, WEIGHTS, Band, ItemFacts, PairResult

DedupSummary = dict[str, int]

# A block bigger than this is a too-coarse key; skip to keep dedup bounded.
_MAX_BLOCK = 400


def ensure_dedup_version(session: Session) -> None:
    """Register the active dedup version in the model registry (idempotent)."""
    stmt = (
        pg_insert(ModelRegistry)
        .values(
            name="duplicate_detection",
            version=DEDUP_VERSION,
            task="dedup",
            framework="deterministic",
            params=WEIGHTS,
            metrics={},
            status="active",
        )
        .on_conflict_do_nothing(index_elements=["name", "version"])
    )
    session.execute(stmt)


def _facts(session: Session) -> dict[str, ItemFacts]:
    rows = session.execute(
        select(
            Item.id,
            Item.item_number,
            Item.description,
            Item.uom,
            Item.item_type,
            Item.unit_cost,
        )
    ).all()
    return {
        str(r.id): ItemFacts(
            item_id=str(r.id),
            item_number=r.item_number,
            description=r.description,
            uom=r.uom,
            item_type=r.item_type,
            unit_cost=float(r.unit_cost) if r.unit_cost is not None else None,
        )
        for r in rows
    }


def detect_pairs(facts: dict[str, ItemFacts]) -> list[PairResult]:
    """Pure: block items, score within-block pairs, return candidate pairs."""
    blocks: dict[tuple[str, str, str], list[ItemFacts]] = defaultdict(list)
    for fact in facts.values():
        blocks[blocking_key(fact)].append(fact)

    pairs: list[PairResult] = []
    for members in blocks.values():
        if len(members) < 2 or len(members) > _MAX_BLOCK:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                result = score_pair(members[i], members[j])
                if result is not None:
                    pairs.append(result)
    return pairs


def run_dedup(session: Session, tenant_id: uuid.UUID) -> DedupSummary:
    ensure_dedup_version(session)
    now = datetime.now(UTC)

    pairs = detect_pairs(_facts(session))

    summary: DedupSummary = {
        "candidates": len(pairs),
        str(Band.PROBABLE): 0,
        str(Band.POSSIBLE): 0,
    }
    for pair in pairs:
        summary[str(pair.band)] += 1
        stmt = (
            pg_insert(DuplicateCandidate)
            .values(
                tenant_id=tenant_id,
                item_a_id=uuid.UUID(pair.item_a),
                item_b_id=uuid.UUID(pair.item_b),
                confidence=pair.confidence,
                band=str(pair.band),
                features=pair.features,
                model_version=pair.version,
                status="open",
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_duplicate_candidates_pair",
                set_={
                    "confidence": pair.confidence,
                    "band": str(pair.band),
                    "features": pair.features,
                    "model_version": pair.version,
                    "updated_at": now,
                },
                # Preserve a planner's decision: only refresh still-open pairs.
                where=DuplicateCandidate.status == "open",
            )
        )
        session.execute(stmt)

    return summary


def propose_merge(
    session: Session,
    tenant_id: uuid.UUID,
    candidate: DuplicateCandidate,
    keep_item_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> Recommendation:
    """Record a merge verdict and stage a CV6-bound approval envelope (S6).

    Never mutates the source items. The merge is a *proposal*: a governance
    envelope (claim, evidence, confidence, model_version, approval_path) with
    ``status='proposed'``. The deterministic CV6 workflow performs the actual
    merge once approved.
    """
    merge_item_id = (
        candidate.item_b_id if keep_item_id == candidate.item_a_id else candidate.item_a_id
    )
    model = session.scalar(
        select(ModelRegistry).where(
            ModelRegistry.name == "duplicate_detection",
            ModelRegistry.version == candidate.model_version,
        )
    )
    recommendation = Recommendation(
        tenant_id=tenant_id,
        model_id=model.id if model else None,
        type="item_merge",
        target_type="item",
        target_id=keep_item_id,
        claim=f"Merge item {merge_item_id} into {keep_item_id} (probable duplicate).",
        payload={
            "keep_item_id": str(keep_item_id),
            "merge_item_id": str(merge_item_id),
            "candidate_id": str(candidate.id),
        },
        confidence=candidate.confidence,
        evidence={"features": candidate.features, "band": candidate.band},
        assumptions={},
        model_version=candidate.model_version,
        approval_path="cv6_workflow",
        status="proposed",
    )
    session.add(recommendation)

    candidate.status = "merged"
    candidate.reviewed_by = user_id
    candidate.reviewed_at = datetime.now(UTC)
    return recommendation
