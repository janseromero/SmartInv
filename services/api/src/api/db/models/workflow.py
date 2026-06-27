"""``workflow`` schema — Postgres-backed approval state machine (ADR-003).

``approvals`` holds current state; ``approval_events`` is the append-only
transition log. An approval may reference the ``ml.recommendation`` it acts on.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
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
    current_step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    current_reviewer_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    current_reviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_path: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml.recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )


class ApprovalPolicy(Base, TenantMixin, TimestampMixin):
    """Configurable rule that resolves a workflow's required approval path.

    Rules are tenant-scoped because approval policy is customer-specific. The
    selected ``required_path`` is copied onto each approval at start time so
    in-flight workflows remain reproducible if policy changes later.
    """

    __tablename__ = "approval_policies"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = uuid_pk()
    workflow_type: Mapped[str] = mapped_column(String(32), nullable=False)
    min_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    min_criticality: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    required_path: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class SourceWrite(Base, TenantMixin, TimestampMixin):
    """A queued write to a source system (CV6.E4).

    Created when an approval reaches ``approved``. A dispatcher delivers it to
    the source system behind the ``SourceWriter`` seam with idempotency, retries,
    and dead-letter handling. ``receipt`` holds the delivery receipt; a permanent
    failure lands in ``dead_letter`` with ``last_error`` (the structured incident).
    """

    __tablename__ = "source_writes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_source_writes_idempotency"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml.recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )
    approval_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow.approvals.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_system: Mapped[str] = mapped_column(String(32), nullable=False, default="maximo")
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    receipt: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class ApprovalEvent(Base, TenantMixin):
    """Append-only approval transition log."""

    __tablename__ = "approval_events"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "approval_id", "idempotency_key", name="uq_approval_events_idempotency"
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow.approvals.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    from_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
