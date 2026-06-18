"""Integration tests for the anomaly queue endpoints (CV2.E5)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.anomaly.service import run_anomaly_scan
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.session import tenant_session
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from fastapi.testclient import TestClient

ADMIN = get_settings().effective_admin_database_url
SLUG = "e5_views"
ITEMS = 200


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture
def seeded_tenant() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'AnomalyViews', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=5), tenant_id=tid, connector_id=connector.id
        )
    with tenant_session(str(tid)) as session:
        run_anomaly_scan(session, tid)
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def _client(tid: uuid.UUID, roles: list[str]) -> TestClient:
    token = mint_dev_token(sub="dev", tenant_id=tid, roles=roles)
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_summary_and_list(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])

    summary = client.get("/anomalies/summary").json()
    assert summary["open"] >= 1
    assert summary["by_type"]

    page = client.get("/anomalies").json()
    assert page["total"] >= 1
    row = page["anomalies"][0]
    assert row["type"] in ("consumption_spike", "price_jump", "negative_balance")
    assert row["cause"]


def test_window_filter_returns_recent_only(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    last7 = client.get("/anomalies?window_days=7&type=consumption_spike").json()
    # Injected spikes are dated in the last 7 days, so the window keeps them.
    assert last7["total"] >= 1


def test_detail_drills_down_to_transaction(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    spike = client.get("/anomalies?type=consumption_spike").json()["anomalies"][0]
    detail = client.get(f"/anomalies/{spike['id']}").json()
    assert detail["transaction"] is not None
    assert detail["transaction"]["source_id"]
    assert detail["transaction"]["item_number"]
    assert "cause" in detail["evidence"]


def test_review_acknowledges(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    anomaly_id = client.get("/anomalies").json()["anomalies"][0]["id"]
    result = client.post(f"/anomalies/{anomaly_id}/review", json={"decision": "acknowledge"}).json()
    assert result["status"] == "acknowledged"
    # It drops out of the default open list.
    open_ids = [a["id"] for a in client.get("/anomalies").json()["anomalies"]]
    assert anomaly_id not in open_ids


def test_review_requires_review_role(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["finance"])
    anomaly_id = client.get("/anomalies").json()["anomalies"][0]["id"]
    resp = client.post(f"/anomalies/{anomaly_id}/review", json={"decision": "dismiss"})
    assert resp.status_code == 403


def test_list_requires_auth() -> None:
    assert TestClient(app).get("/anomalies").status_code == 401
