"""Integration test for the scoring service persistence + registry (CV2.E3)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.config import get_settings
from api.db.models.inventory import Item
from api.db.models.ml import ModelRegistry
from api.db.session import tenant_session
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.scoring.model import SCORE_VERSION
from api.scoring.service import run_scoring
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "e3_score"
ITEMS = 40


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture
def tenant_id() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'Score', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=3), tenant_id=tid, connector_id=connector.id
        )
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def test_scoring_persists_and_classifies(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        summary = run_scoring(session, tenant_id)

    assert summary["scored"] == ITEMS
    assert (
        sum(summary.get(k, 0) for k in ("healthy", "excess_slow", "obsolete_risk", "dq_risk"))
        == ITEMS
    )

    with tenant_session(str(tenant_id)) as session:
        scored = session.scalar(
            select(func.count()).select_from(Item).where(Item.health_score.isnot(None))
        )
        versions = session.scalar(
            select(func.count()).select_from(Item).where(Item.score_version == SCORE_VERSION)
        )
    assert scored == ITEMS
    assert versions == ITEMS


def test_score_version_registered(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_scoring(session, tenant_id)
        registered = session.scalar(
            select(func.count())
            .select_from(ModelRegistry)
            .where(ModelRegistry.name == "health_score", ModelRegistry.version == SCORE_VERSION)
        )
    assert registered == 1
