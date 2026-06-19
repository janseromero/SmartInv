"""Integration test for the risk-scoring service (CV4.E1/E2)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.config import get_settings
from api.db.models.inventory import Item
from api.db.models.ml import ModelRegistry
from api.db.session import tenant_session
from api.forecast.service import run_forecast
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.optimize.service import run_optimization
from api.risk.model import RISK_VERSION
from api.risk.service import run_risk_scan
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv4_service"
ITEMS = 150


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
                "VALUES (%s, 'CV4', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=17), tenant_id=tid, connector_id=connector.id
        )
    with tenant_session(str(tid)) as session:
        run_forecast(session, tid)
        run_optimization(session, tid)
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def test_risk_scan_scores_and_flags(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        summary = run_risk_scan(session, tenant_id)

    assert summary["scored"] == ITEMS
    assert summary["critical_spares"] >= 1

    with tenant_session(str(tenant_id)) as session:
        scored = session.scalar(
            select(func.count()).select_from(Item).where(Item.risk_version == RISK_VERSION)
        )
        assert scored == ITEMS
        sample = session.scalars(select(Item).where(Item.is_critical_spare.is_(True))).first()
        assert sample is not None
        assert sample.critical_reason
        assert sample.risk_breakdown is not None
        assert "downtime_exposure" in sample.risk_breakdown
        registered = session.scalar(
            select(func.count())
            .select_from(ModelRegistry)
            .where(ModelRegistry.name == "operational_risk", ModelRegistry.version == RISK_VERSION)
        )
        assert registered == 1


def test_risk_is_reproducible(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_risk_scan(session, tenant_id)
        first = {
            i.id: i.risk_score
            for i in session.scalars(select(Item)).all()
            if i.risk_score is not None
        }
    with tenant_session(str(tenant_id)) as session:
        run_risk_scan(session, tenant_id)
        second = {
            i.id: i.risk_score
            for i in session.scalars(select(Item)).all()
            if i.risk_score is not None
        }
    assert first == second  # same inputs + version -> same scores
