"""Governed conversational analyst endpoint — "Ask SmartInv" (CV5.E2, slice 1).

``POST /agents/run`` answers a natural-language question over the governed tool
catalog and returns the answer envelope (answer, grounded flag, confidence,
tool calls, evidence). Read-only; streaming (SSE) and chat history arrive in the
next slice.

The analyst (planner + composer) is an injected dependency: production uses the
LiteLLM gateway (503 until an API key is configured); tests override it with the
deterministic stub so the governed path is exercised without a model vendor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.agent.catalog import READ_ROLES, ToolScopeError
from api.agent.orchestrator import (
    AgentAnswer,
    Composer,
    LLMComposer,
    LLMPlanner,
    Planner,
    run_agent,
)
from api.audit.service import record_audit_event
from api.auth.dependencies import get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.config import get_settings
from api.infra.llm_gateway import LiteLLMGateway

router = APIRouter(tags=["agents"], prefix="/agents")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


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


@router.post("/run", response_model=AgentAnswer, summary="Ask SmartInv (governed)")
def ask(
    body: AskRequest,
    user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    analyst: Annotated[Analyst, Depends(get_analyst)],
) -> AgentAnswer:
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

    # Audit the query itself (who asked what, and whether it grounded) in
    # addition to the per-tool audit records emitted inside the catalog.
    record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor=user.sub,
        action="agent.ask",
        resource_type="conversation",
        payload={
            "question": body.question,
            "grounded": answer.grounded,
            "model": answer.model,
            "tools": [call.name for call in answer.tool_calls],
        },
    )
    return answer
