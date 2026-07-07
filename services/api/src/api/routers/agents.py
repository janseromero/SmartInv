"""Governed conversational analyst endpoint — "Ask SmartInv" (CV5.E2).

``POST /agents/run`` answers a natural-language question over the governed tool
catalog and returns the answer envelope (answer, grounded flag, confidence,
tool calls, evidence). Read-only; streaming (SSE, CV5.E2.S3) and chat history
(CV5.E2.S5) arrive later.

The analyst (planner + composer) is an injected dependency: production uses the
LiteLLM gateway (503 until an API key is configured); tests override it with the
deterministic stub so the governed path is exercised without a model vendor.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.agent.catalog import READ_ROLES, ToolScopeError
from api.agent.history import (
    get_or_create_user,
    list_conversations,
    load_conversation,
    record_turn,
)
from api.agent.orchestrator import (
    AgentAnswer,
    Composer,
    LLMComposer,
    LLMPlanner,
    Planner,
    run_agent,
    stream_agent,
)
from api.audit.service import record_audit_event
from api.auth.dependencies import get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.config import get_settings
from api.infra.llm_gateway import LiteLLMGateway

router = APIRouter(tags=["agents"], prefix="/agents")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: uuid.UUID | None = None


class AskResponse(AgentAnswer):
    """The governed answer plus the conversation it was recorded in."""

    conversation_id: uuid.UUID


class ConversationRow(BaseModel):
    id: uuid.UUID
    title: str
    updated_at: str | None = None
    turns: int


class ConversationTurn(BaseModel):
    question: str
    answer: dict[str, Any]


class ConversationDetail(BaseModel):
    id: uuid.UUID
    title: str
    turns: list[ConversationTurn]


@dataclass(frozen=True)
class Analyst:
    """Injected planner + composer + model id used by the endpoint."""

    planner: Planner
    composer: Composer
    model: str


def get_analyst() -> Analyst:
    """Default analyst: the LiteLLM gateway, or 503 when no key is configured."""
    settings = get_settings()
    gateway = LiteLLMGateway(settings)
    if not gateway.configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversational analyst is not configured (missing OPENAI_API_KEY).",
        )
    return Analyst(
        planner=LLMPlanner(gateway, settings.llm_model),
        composer=LLMComposer(gateway, settings.llm_model, settings.llm_temperature),
        model=settings.llm_model,
    )


@router.post("/run", response_model=AskResponse, summary="Ask SmartInv (governed)")
def ask(
    body: AskRequest,
    user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    analyst: Annotated[Analyst, Depends(get_analyst)],
) -> AskResponse:
    started = time.monotonic()
    try:
        answer = run_agent(
            session,
            user,
            user.tenant_id,
            body.question,
            analyst.planner,
            analyst.composer,
            analyst.model,
        )
    except ToolScopeError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    latency_ms = int((time.monotonic() - started) * 1000)

    # Persist the turn (CV5.E2.S5) — creates the conversation on the first turn.
    user_row = get_or_create_user(session, user)
    try:
        conversation = record_turn(
            session,
            tenant_id=user.tenant_id,
            user=user_row,
            conversation_id=body.conversation_id,
            question=body.question,
            answer=answer,
            latency_ms=latency_ms,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found."
        ) from exc

    # Audit the query itself (who asked what, and whether it grounded) in
    # addition to the per-tool audit records emitted inside the catalog.
    record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor=user.sub,
        action="agent.ask",
        resource_type="conversation",
        resource_id=conversation.id,
        payload={
            "question": body.question,
            "grounded": answer.grounded,
            "model": answer.model,
            "tools": [call.name for call in answer.tool_calls],
        },
    )
    return AskResponse(**answer.model_dump(), conversation_id=conversation.id)


def _sse(event_type: str, data: dict[str, Any]) -> str:
    """Format one Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/stream", summary="Ask SmartInv (governed, streamed trace)")
def ask_stream(
    body: AskRequest,
    user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    analyst: Annotated[Analyst, Depends(get_analyst)],
) -> StreamingResponse:
    """Stream the governed run *trace* (planning, tool calls, validating), then a
    terminal ``answer`` event with the validated envelope + conversation id.

    Never streams raw answer tokens — fail-closed grounding runs on the complete
    answer, which is delivered whole (ADR-032).
    """

    def event_stream() -> Iterator[str]:
        started = time.monotonic()
        try:
            for event in stream_agent(
                session,
                user,
                user.tenant_id,
                body.question,
                analyst.planner,
                analyst.composer,
                analyst.model,
            ):
                if event.type != "answer":
                    yield _sse(event.type, event.data)
                    continue

                answer = event.data["answer"]
                assert isinstance(answer, AgentAnswer)  # noqa: S101 — internal invariant
                latency_ms = int((time.monotonic() - started) * 1000)
                user_row = get_or_create_user(session, user)
                conversation = record_turn(
                    session,
                    tenant_id=user.tenant_id,
                    user=user_row,
                    conversation_id=body.conversation_id,
                    question=body.question,
                    answer=answer,
                    latency_ms=latency_ms,
                )
                record_audit_event(
                    session,
                    tenant_id=user.tenant_id,
                    actor=user.sub,
                    action="agent.ask",
                    resource_type="conversation",
                    resource_id=conversation.id,
                    payload={
                        "question": body.question,
                        "grounded": answer.grounded,
                        "model": answer.model,
                        "tools": [call.name for call in answer.tool_calls],
                        "streamed": True,
                    },
                )
                payload = AskResponse(
                    **answer.model_dump(), conversation_id=conversation.id
                ).model_dump(mode="json")
                yield _sse("answer", payload)
        except ToolScopeError as exc:
            yield _sse("error", {"detail": str(exc), "status": 403})
        except LookupError:
            yield _sse("error", {"detail": "Conversation not found.", "status": 404})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/conversations", response_model=list[ConversationRow], summary="List conversations")
def conversations(
    user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[ConversationRow]:
    user_row = get_or_create_user(session, user)
    return [ConversationRow(**row) for row in list_conversations(session, user_row.id)]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Load a conversation",
)
def conversation_detail(
    conversation_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> ConversationDetail:
    user_row = get_or_create_user(session, user)
    detail = load_conversation(session, user_row.id, conversation_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return ConversationDetail(**detail)
