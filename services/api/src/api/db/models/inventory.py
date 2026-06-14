"""``inventory`` schema — Silver canonical model (direct-conform).

Lean by design: each table carries the natural-key seam
(``source_system`` + ``source_id``) plus essential columns. Richer domain
columns (lead times, safety-stock parameters, failure modes) are added by
their owning CV via migration.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.db.base import Base, TenantMixin, TimestampMixin, uuid_pk

SCHEMA = "inventory"
QTY = Numeric(18, 4)


def _source_unique(table: str) -> UniqueConstraint:
    return UniqueConstraint("tenant_id", "source_system", "source_id", name=f"uq_{table}_source")


class Location(Base, TenantMixin, TimestampMixin):
    __tablename__ = "locations"
    __table_args__ = (_source_unique("locations"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    location_code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.locations.id", ondelete="SET NULL"), nullable=True
    )


class Supplier(Base, TenantMixin, TimestampMixin):
    __tablename__ = "suppliers"
    __table_args__ = (_source_unique("suppliers"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    supplier_code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)


class Item(Base, TenantMixin, TimestampMixin):
    __tablename__ = "items"
    __table_args__ = (_source_unique("items"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    item_number: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uom: Mapped[str | None] = mapped_column(String(16), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unit_cost: Mapped[float | None] = mapped_column(QTY, nullable=True)
    # Health score (CV2.E3) — populated by the scoring service.
    health_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    health_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score_dimensions: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Asset(Base, TenantMixin, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (_source_unique("assets"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_number: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criticality: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.locations.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)


class WorkOrder(Base, TenantMixin, TimestampMixin):
    __tablename__ = "work_orders"
    __table_args__ = (_source_unique("work_orders"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    wo_number: Mapped[str] = mapped_column(Text, nullable=False)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.assets.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    priority: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PurchaseOrder(Base, TenantMixin, TimestampMixin):
    __tablename__ = "purchase_orders"
    __table_args__ = (_source_unique("purchase_orders"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    po_number: Mapped[str] = mapped_column(Text, nullable=False)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.suppliers.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Balance(Base, TenantMixin, TimestampMixin):
    __tablename__ = "balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "item_id", "location_id", name="uq_balances_item_location"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.items.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.locations.id", ondelete="CASCADE"), nullable=False
    )
    on_hand: Mapped[float] = mapped_column(QTY, nullable=False, default=0)
    available: Mapped[float] = mapped_column(QTY, nullable=False, default=0)
    reserved: Mapped[float] = mapped_column(QTY, nullable=False, default=0)
    min_level: Mapped[float | None] = mapped_column(QTY, nullable=True)
    max_level: Mapped[float | None] = mapped_column(QTY, nullable=True)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Transaction(Base, TenantMixin):
    __tablename__ = "transactions"
    __table_args__ = (_source_unique("transactions"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.items.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory.locations.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[float] = mapped_column(QTY, nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(QTY, nullable=True)
    txn_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory.work_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
