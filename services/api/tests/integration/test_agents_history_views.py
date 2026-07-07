"""Integration tests for conversation persistence (CV5.E2.S5)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.agent.orchestrator import KeywordPlanner, TemplateComposer
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.session import tenant_session
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from api.risk.service import run_risk_scan
from api.routers.agents import Analyst, get_analyst
from api.scoring.service import run_scoring
from fastapi.testclient import TestClient

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv5_agents_history"
ITEMS = 100


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
                "VALUES (%s, 'CV5History', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=41), tenant_id=tid, connector_id=connector.id
        )
    with tenant_session(str(tid)) as session:
        run_scoring(session, tid)
        run_risk_scan(session, tid)
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def _client(tid: uuid.UUID) -> TestClient:
    token = mint_dev_token(sub="dev", tenant_id=tid, roles=["planner"])
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _stub_analyst() -> Analyst:
    return Analyst(planner=KeywordPlanner(), composer=TemplateComposer(), model="stub-model")


def test_first_turn_creates_conversation(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant)
        body = client.post("/agents/run", json={"question": "inventory and risk summary"}).json()
        assert "conversation_id" in body
        assert body["grounded"] is True
    finally:
        app.dependency_overrides.clear()


def test_second_turn_continues_same_conversation(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant)
        first = client.post("/agents/run", json={"question": "inventory summary"}).json()
        cid = first["conversation_id"]
        client.post("/agents/run", json={"question": "risk summary", "conversation_id": cid})

        detail = client.get(f"/agents/conversations/{cid}").json()
        assert detail["id"] == cid
        assert len(detail["turns"]) == 2
        assert detail["turns"][0]["question"] == "inventory summary"
        assert "grounded" in detail["turns"][0]["answer"]
    finally:
        app.dependency_overrides.clear()


def test_list_returns_conversations_with_turn_counts(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant)
        cid = client.post("/agents/run", json={"question": "inventory summary"}).json()[
            "conversation_id"
        ]
        client.post("/agents/run", json={"question": "risk summary", "conversation_id": cid})

        convos = client.get("/agents/conversations").json()
        mine = next(c for c in convos if c["id"] == cid)
        assert mine["turns"] == 2
        assert mine["title"]
    finally:
        app.dependency_overrides.clear()


def test_unknown_conversation_is_404(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant)
        assert client.get(f"/agents/conversations/{uuid.uuid4()}").status_code == 404
        resp = client.post(
            "/agents/run",
            json={"question": "risk summary", "conversation_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_conversations_require_auth() -> None:
    assert TestClient(app).get("/agents/conversations").status_code == 401
