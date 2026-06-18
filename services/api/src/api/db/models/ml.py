"""``ml`` schema — Gold layer: model registry, predictions, recommendations.

``model_registry`` is a platform-level catalog (not tenant-scoped). Predictions,
recommendations, and feature snapshots are tenant-scoped. ``recommendations`` is
the governance envelope (claim, evidence, confidence, assumptions, model
version, approval path) per Engineering Principles A3.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.db.base import Base, TenantMixin, TimestampMixin, uuid_pk

SCHEMA = "ml"


class ModelRegistry(Base, TimestampMixin):
    """Platform-level registry of model versions (not tenant-scoped)."""

    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_registry_name_version"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    task: Mapped[str] = mapped_column(String(32), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Prediction(Base, TenantMixin):
    __tablename__ = "predictions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = uuid_pk()
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml.model_registry.id", ondelete="RESTRICT"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    horizon: Mapped[str | None] = mapped_column(String(32), nullable=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    input_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Recommendation(Base, TenantMixin, TimestampMixin):
    """Governance envelope — claim, evidence, confidence, approval path (A3)."""

    __tablename__ = "recommendations"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = uuid_pk()
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml.model_registry.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    assumptions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_path: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")


class DuplicateCandidate(Base, TenantMixin, TimestampMixin):
    """A probable item-master duplicate pair (CV2.E4).

    Produced by the deterministic dedup engine and reviewed by a planner.
    Canonical ordering (``item_a_id < item_b_id``) keeps each pair unique.
    ``model_version`` records which model produced the pair (Done Condition).
    A "merge" decision never mutates source rows here — it emits a
    ``ml.recommendations`` envelope routed through CV6 approval.
    """

    __tablename__ = "duplicate_candidates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "item_a_id", "item_b_id", name="uq_duplicate_candidates_pair"
        ),
        CheckConstraint("item_a_id < item_b_id", name="canonical_pair_order"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    item_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.items.id", ondelete="CASCADE"), nullable=False
    )
    item_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.items.id", ondelete="CASCADE"), nullable=False
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    band: Mapped[str] = mapped_column(String(16), nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FeatureSnapshot(Base, TenantMixin):
    __tablename__ = "feature_snapshots"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = uuid_pk()
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
