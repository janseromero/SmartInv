"""Integration tests for the governed conversational analyst (CV5.E2).

The analyst dependency is overridden with the deterministic stub so the full
governed path (plan -> scoped/audited tools -> compose -> grounding) is exercised
without a live model. A separate case injects an ungrounded composer to prove the
orchestrator fails closed.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.agent.orchestrator import Fact, KeywordPlanner, TemplateComposer
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.models.audit import Event as AgentEvent
from api.db.session import tenant_session
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from api.risk.service import run_risk_scan
from api.routers.agents import Analyst, get_analyst
from api.scoring.service import run_scoring
from fastapi.testclient import TestClient
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv5_agents_views"
ITEMS = 120


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
                "VALUES (%s, 'CV5Agents', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=31), tenant_id=tid, connector_id=connector.id
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


def _stub_analyst() -> Analyst:
    return Analyst(planner=KeywordPlanner(), composer=TemplateComposer(), model="stub-model")


def _client(tid: uuid.UUID, roles: list[str]) -> TestClient:
    token = mint_dev_token(sub="dev", tenant_id=tid, roles=roles)
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_grounded_answer_with_evidence(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant, ["planner"])
        resp = client.post("/agents/run", json={"question": "How is inventory health and risk?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["grounded"] is True
        assert body["model"] == "stub-model"
        assert len(body["tool_calls"]) >= 1
        assert len(body["evidence"]) >= 1
        # The stub composer restates tool facts verbatim, so it must ground.
        assert body["confidence"] > 0
    finally:
        app.dependency_overrides.clear()


def test_tool_invocation_is_audited(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant, ["planner"])
        client.post("/agents/run", json={"question": "inventory and risk summary"})
    finally:
        app.dependency_overrides.clear()

    with tenant_session(str(seeded_tenant)) as session:
        count = session.scalar(
            select(func.count())
            .select_from(AgentEvent)
            .where(AgentEvent.action == "agent.tool_invoke")
        )
    assert (count or 0) >= 1


def test_fails_closed_on_ungrounded_composer(seeded_tenant: uuid.UUID) -> None:
    class LyingComposer:
        def compose(self, question: str, facts: list[Fact]) -> str:
            return "There are exactly 999999 critical spares and $7,777,777 exposure."

    def lying_analyst() -> Analyst:
        return Analyst(planner=KeywordPlanner(), composer=LyingComposer(), model="stub-model")

    app.dependency_overrides[get_analyst] = lying_analyst
    try:
        client = _client(seeded_tenant, ["planner"])
        body = client.post("/agents/run", json={"question": "risk summary"}).json()
        assert body["grounded"] is False
        assert "999999" not in body["answer"]  # fabricated numbers never reach the user
    finally:
        app.dependency_overrides.clear()


def test_unconfigured_analyst_returns_503(seeded_tenant: uuid.UUID) -> None:
    # No override: the real dependency 503s when OPENAI_API_KEY is unset.
    if get_settings().openai_api_key:
        pytest.skip("a real API key is configured; the 503 path is not exercised")
    client = _client(seeded_tenant, ["planner"])
    resp = client.post("/agents/run", json={"question": "anything"})
    assert resp.status_code == 503


def test_stream_emits_trace_then_answer(seeded_tenant: uuid.UUID) -> None:
    app.dependency_overrides[get_analyst] = _stub_analyst
    try:
        client = _client(seeded_tenant, ["planner"])
        resp = client.post("/agents/stream", json={"question": "inventory and risk summary"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.text
        # Trace events precede the terminal answer.
        assert "event: planning" in body
        assert "event: tool_call" in body
        assert "event: answer" in body
        assert body.index("event: planning") < body.index("event: answer")

        # The terminal answer carries the grounded envelope + conversation id.
        answer_line = next(
            line for line in body.splitlines() if line.startswith("data: {") and "grounded" in line
        )
        payload = json.loads(answer_line[len("data: ") :])
        assert payload["grounded"] is True
        assert "conversation_id" in payload
    finally:
        app.dependency_overrides.clear()


def test_requires_auth() -> None:
    assert TestClient(app).post("/agents/run", json={"question": "x"}).status_code == 401
    assert TestClient(app).post("/agents/stream", json={"question": "x"}).status_code == 401
