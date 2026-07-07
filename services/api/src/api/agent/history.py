"""Conversation persistence for Ask SmartInv (CV5.E2.S5).

Each governed Q&A turn is recorded so a planner can revisit and continue a
conversation. Storage maps onto the existing ``agent`` schema:

- ``agent.conversations`` — one row per chat session (owned by a user)
- ``agent.runs``          — one row per question→answer turn
- ``agent.events``        — the append-only ``user_message`` / ``assistant_message``
  pair carrying the question and the full answer envelope

Tenant isolation is RLS; per-user ownership is enforced by filtering on the
resolved ``user_id``. Durable LangGraph checkpointing stays deferred (ADR-032).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.agent.orchestrator import AgentAnswer
from api.auth.models import CurrentUser
from api.db.models.agent import Conversation, Event, Run
from api.db.models.core import User

_TITLE_MAX = 60


def get_or_create_user(session: Session, user: CurrentUser) -> User:
    """Resolve the principal to a ``core.users`` row, provisioning on first sight.

    Mirrors the just-in-time provisioning in ``/me`` so a conversation can be
    owned by a real user id even before a full IdP exists.
    """
    existing = session.scalar(select(User).where(User.external_subject == user.sub))
    if existing is not None:
        return existing
    row = User(
        tenant_id=user.tenant_id,
        external_subject=user.sub,
        email=user.email or f"{user.sub}@dev.local",
        display_name=user.email,
    )
    session.add(row)
    session.flush()
    return row


def _title_from(question: str) -> str:
    q = question.strip()
    return f"{q[:_TITLE_MAX]}…" if len(q) > _TITLE_MAX else q


def record_turn(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    user: User,
    conversation_id: uuid.UUID | None,
    question: str,
    answer: AgentAnswer,
    latency_ms: int | None = None,
) -> Conversation:
    """Persist one Q&A turn; create the conversation when none is supplied.

    Raises :class:`LookupError` when ``conversation_id`` is given but not owned
    by ``user`` (mapped to 404 by the router).
    """
    now = datetime.now(UTC)
    if conversation_id is not None:
        conversation = session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user.id
            )
        )
        if conversation is None:
            raise LookupError("conversation not found")
        conversation.updated_at = now  # bump activity for ordering
    else:
        conversation = Conversation(
            tenant_id=tenant_id, user_id=user.id, title=_title_from(question)
        )
        session.add(conversation)
        session.flush()

    run = Run(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        status="completed",
        model=answer.model,
        latency_ms=latency_ms,
        finished_at=now,
    )
    session.add(run)
    session.flush()

    session.add(
        Event(tenant_id=tenant_id, run_id=run.id, type="user_message", payload={"text": question})
    )
    session.add(
        Event(
            tenant_id=tenant_id,
            run_id=run.id,
            type="assistant_message",
            payload={
                "text": answer.answer,
                "grounded": answer.grounded,
                "confidence": answer.confidence,
                "model": answer.model,
                "evidence": [chip.model_dump() for chip in answer.evidence],
                "tool_calls": [call.model_dump() for call in answer.tool_calls],
            },
        )
    )
    return conversation


def list_conversations(session: Session, user_id: uuid.UUID) -> list[dict[str, Any]]:
    """Recent conversations for a user, newest activity first, with turn counts."""
    turns = (
        select(Run.conversation_id, func.count().label("turns"))
        .group_by(Run.conversation_id)
        .subquery()
    )
    rows = session.execute(
        select(
            Conversation.id,
            Conversation.title,
            Conversation.updated_at,
            func.coalesce(turns.c.turns, 0),
        )
        .join(turns, turns.c.conversation_id == Conversation.id, isouter=True)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    ).all()
    return [
        {
            "id": r[0],
            "title": r[1] or "Untitled",
            "updated_at": r[2].isoformat() if r[2] else None,
            "turns": int(r[3]),
        }
        for r in rows
    ]


def load_conversation(
    session: Session, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> dict[str, Any] | None:
    """Full turn history for a conversation the user owns, oldest first."""
    conversation = session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )
    if conversation is None:
        return None

    runs = session.scalars(
        select(Run).where(Run.conversation_id == conversation_id).order_by(Run.started_at)
    ).all()

    turns: list[dict[str, Any]] = []
    for run in runs:
        events = session.scalars(
            select(Event).where(Event.run_id == run.id).order_by(Event.id)
        ).all()
        question = next((e.payload.get("text") for e in events if e.type == "user_message"), None)
        answer = next((e.payload for e in events if e.type == "assistant_message"), None)
        if question is not None and answer is not None:
            turns.append({"question": question, "answer": answer})

    return {"id": conversation.id, "title": conversation.title, "turns": turns}
