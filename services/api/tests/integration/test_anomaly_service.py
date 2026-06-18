"""Integration test for the anomaly service: persistence + registry (CV2.E5)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.anomaly.model import ANOMALY_VERSION
from api.anomaly.service import run_anomaly_scan
from api.config import get_settings
from api.db.models.ml import Anomaly, ModelRegistry
from api.db.session import tenant_session
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "e5_anomaly"
ITEMS = 200


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
                "VALUES (%s, 'Anomaly', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=5), tenant_id=tid, connector_id=connector.id
        )
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def test_scan_detects_all_three_anomaly_types(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        summary = run_anomaly_scan(session, tenant_id)

    # The enriched fixtures inject all three kinds across 200 items.
    assert summary["consumption_spike"] >= 1
    assert summary["price_jump"] >= 1
    assert summary["negative_balance"] >= 1
    assert summary["anomalies"] == sum(
        summary[k] for k in ("consumption_spike", "price_jump", "negative_balance")
    )

    with tenant_session(str(tenant_id)) as session:
        persisted = session.scalar(select(func.count()).select_from(Anomaly)) or 0
        assert persisted == summary["anomalies"]
        sample = session.scalars(select(Anomaly)).first()
        assert sample is not None
        assert sample.model_version == ANOMALY_VERSION
        assert "cause" in sample.evidence


def test_scan_is_idempotent_and_preserves_reviews(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        first = run_anomaly_scan(session, tenant_id)
        flagged = session.scalars(select(Anomaly)).first()
        assert flagged is not None
        flagged.status = "dismissed"

    with tenant_session(str(tenant_id)) as session:
        second = run_anomaly_scan(session, tenant_id)
        # Re-running upserts, never duplicates.
        total = session.scalar(select(func.count()).select_from(Anomaly)) or 0
        assert total == first["anomalies"] == second["anomalies"]
        # A reviewed anomaly keeps its decision.
        dismissed = session.scalar(
            select(func.count()).select_from(Anomaly).where(Anomaly.status == "dismissed")
        )
        assert dismissed == 1


def test_anomaly_version_registered(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_anomaly_scan(session, tenant_id)
        registered = session.scalar(
            select(func.count())
            .select_from(ModelRegistry)
            .where(
                ModelRegistry.name == "anomaly_detection",
                ModelRegistry.version == ANOMALY_VERSION,
            )
        )
    assert registered == 1
