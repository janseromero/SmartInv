"""``workflow`` schema — Postgres-backed approval state machine (ADR-003).

``approvals`` holds current state; ``approval_events`` is the append-only
transition log. An approval may reference the ``ml.recommendation`` it acts on.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.db.base import Base, TenantMixin, TimestampMixin, uuid_pk

SCHEMA = "workflow"


class Approval(Base, TenantMixin, TimestampMixin):
    __tablename__ = "approvals"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = uuid_pk()
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="agent_proposed")
    current_actor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml.recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )


class ApprovalEvent(Base, TenantMixin):
    """Append-only approval transition log."""

    __tablename__ = "approval_events"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow.approvals.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
