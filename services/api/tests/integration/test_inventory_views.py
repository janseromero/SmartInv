"""Integration tests for the inventory catalog/summary endpoints (CV2.E2)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.session import tenant_session
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from fastapi.testclient import TestClient

ADMIN = get_settings().effective_admin_database_url
SLUG = "e2_views"
ITEMS = 30


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture(scope="module")
def seeded_tenant() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'Views', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=7), tenant_id=tid, connector_id=connector.id
        )
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


@pytest.fixture
def client(seeded_tenant: uuid.UUID) -> TestClient:
    token = mint_dev_token(sub="dev", tenant_id=seeded_tenant, roles=["planner"])
    test_client = TestClient(app)
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    return test_client


def test_summary_counts_items(client: TestClient) -> None:
    body = client.get("/inventory/summary").json()
    assert body["total_items"] == ITEMS
    assert body["inventory_value"] >= 0
    assert 0 <= body["completeness_pct"] <= 100


def test_items_paginate(client: TestClient) -> None:
    body = client.get("/inventory/items", params={"page_size": 10}).json()
    assert body["total"] == ITEMS
    assert len(body["items"]) == 10
    assert body["page"] == 1


def test_items_search_filters(client: TestClient) -> None:
    body = client.get("/inventory/items", params={"search": "ITEM-1000"}).json()
    numbers = [i["item_number"] for i in body["items"]]
    assert "ITEM-1000" in numbers


def test_locations_listed(client: TestClient) -> None:
    codes = {loc["location_code"] for loc in client.get("/inventory/locations").json()}
    assert "LOC-CENTRAL" in codes


def test_requires_auth() -> None:
    assert TestClient(app).get("/inventory/items").status_code == 401
