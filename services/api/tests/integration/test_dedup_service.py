"""Integration test for the dedup service: persistence, registry, merge proposal (CV2.E4)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.config import get_settings
from api.db.models.inventory import Item
from api.db.models.ml import DuplicateCandidate, ModelRegistry, Recommendation
from api.db.session import tenant_session
from api.dedup.model import DEDUP_VERSION
from api.dedup.service import propose_merge, run_dedup
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "e4_dedup"


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


def _make_item(session: object, tid: uuid.UUID, number: str, desc: str) -> Item:
    item = Item(
        tenant_id=tid,
        source_system="FIXTURE",
        source_id=number,
        item_number=number,
        description=desc,
        uom="EA",
        item_type="SPARE",
        unit_cost=100.0,
    )
    session.add(item)  # type: ignore[attr-defined]
    return item


@pytest.fixture
def tenant_id() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'Dedup', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        # Two near-identical bearings (a probable pair) + one unrelated item.
        _make_item(session, tid, "B-001", "Ball bearing 6204 2RS sealed")
        _make_item(session, tid, "B-002", "Bearing ball 6204 2RS sealed")
        _make_item(session, tid, "G-001", "Safety gloves nitrile large")
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def test_dedup_persists_probable_pair(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        summary = run_dedup(session, tenant_id)

    assert summary["candidates"] >= 1
    assert summary["probable"] >= 1

    with tenant_session(str(tenant_id)) as session:
        pairs = session.scalars(select(DuplicateCandidate)).all()
    assert len(pairs) >= 1
    pair = pairs[0]
    assert pair.item_a_id < pair.item_b_id  # canonical ordering
    assert float(pair.confidence) >= 0.85
    assert pair.model_version == DEDUP_VERSION
    assert pair.status == "open"


def test_dedup_version_registered(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_dedup(session, tenant_id)
        registered = session.scalar(
            select(func.count())
            .select_from(ModelRegistry)
            .where(
                ModelRegistry.name == "duplicate_detection",
                ModelRegistry.version == DEDUP_VERSION,
            )
        )
    assert registered == 1


def test_rerun_preserves_reviewed_decisions(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_dedup(session, tenant_id)
        cand = session.scalars(select(DuplicateCandidate)).first()
        assert cand is not None
        cand.status = "not_duplicate"

    # Second run must NOT reopen the reviewed pair.
    with tenant_session(str(tenant_id)) as session:
        run_dedup(session, tenant_id)
        cand = session.scalars(select(DuplicateCandidate)).first()
        assert cand is not None
        assert cand.status == "not_duplicate"


def test_propose_merge_creates_envelope_without_mutating_items(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_dedup(session, tenant_id)
        cand = session.scalars(
            select(DuplicateCandidate).where(DuplicateCandidate.band == "probable")
        ).first()
        assert cand is not None
        keep_id = cand.item_a_id
        merge_id = cand.item_b_id

        rec = propose_merge(session, tenant_id, cand, keep_id, None)
        session.flush()

        assert rec.type == "item_merge"
        assert rec.status == "proposed"
        assert rec.approval_path == "cv6_workflow"
        assert rec.target_id == keep_id
        assert cand.status == "merged"

        # Source items are untouched — merge is a proposal, not a mutation.
        assert session.get(Item, merge_id) is not None
        assert session.get(Item, keep_id) is not None

    with tenant_session(str(tenant_id)) as session:
        recs = session.scalars(
            select(Recommendation).where(Recommendation.type == "item_merge")
        ).all()
    assert len(recs) == 1
