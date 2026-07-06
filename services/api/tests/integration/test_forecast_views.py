"""Integration tests for the demand-forecasting read endpoints (CV3.E1)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.session import tenant_session
from api.forecast.model import FORECAST_VERSION
from api.forecast.service import run_forecast
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from fastapi.testclient import TestClient

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv3_forecast_views"
ITEMS = 150


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
                "VALUES (%s, 'CV3Forecast', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=23), tenant_id=tid, connector_id=connector.id
        )
    with tenant_session(str(tid)) as session:
        run_forecast(session, tid)
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


def test_summary_reports_method_mix(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["finance"])
    summary = client.get("/forecast/summary").json()

    assert summary["model_version"] == FORECAST_VERSION
    assert summary["forecasted"] >= 1
    assert 0 <= summary["coverage_pct"] <= 100
    assert 0.0 <= summary["avg_cv"]
    # Every item gets a prediction, so method counts sum to the forecasted total.
    assert sum(summary["by_method"].values()) == summary["forecasted"]
    assert set(summary["by_method"]) == {"croston", "tsb", "naive", "empty"}


def test_items_ranked_by_demand_rate(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    page = client.get("/forecast/items").json()

    assert page["total"] >= 1
    rates = [r["rate"] for r in page["items"]]
    assert rates == sorted(rates, reverse=True)  # highest demand first
    assert {"method", "p50", "p80", "p95", "cv"} <= set(page["items"][0])


def test_items_filter_by_method(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    page = client.get("/forecast/items?method=empty").json()
    assert all(r["method"] == "empty" for r in page["items"])


def test_detail_pairs_bands_with_history(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    # Pick an active item so the bands are non-trivial.
    items = client.get("/forecast/items").json()["items"]
    item_id = items[0]["id"]

    detail = client.get(f"/forecast/items/{item_id}").json()
    assert detail["horizon"] >= 1
    assert len(detail["history"]) >= 1
    # Bands are ordered p50 <= p80 <= p95 (quantile monotonicity).
    assert detail["p50"] <= detail["p80"] <= detail["p95"]
    assert "diagnostics" in detail


def test_detail_unknown_item_is_404(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    resp = client.get(f"/forecast/items/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_summary_requires_auth() -> None:
    assert TestClient(app).get("/forecast/summary").status_code == 401
