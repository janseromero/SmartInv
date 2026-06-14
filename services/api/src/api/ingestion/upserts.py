"""Per-entity idempotent upserts + foreign-key resolution (CV2.E1).

Each handler maps a canonical ``SourceRecord`` into an ``INSERT ... ON CONFLICT``
keyed by the entity's natural key, so re-running a sync never duplicates rows.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.inventory import (
    Asset,
    Balance,
    Item,
    Location,
    Supplier,
    Transaction,
)
from api.ingestion.connector import Entity, SourceRecord

_SOURCE_KEY = ("tenant_id", "source_system", "source_id")


@dataclass
class IngestContext:
    """Per-run state: tenant, source system, and a source-id -> UUID cache."""

    tenant_id: uuid.UUID
    source_system: str
    _ids: dict[tuple[Entity, str], uuid.UUID] = field(default_factory=dict)


def _resolve(
    session: Session, ctx: IngestContext, entity: Entity, source_id: str, model: Any
) -> uuid.UUID:
    key = (entity, source_id)
    cached = ctx._ids.get(key)
    if cached is not None:
        return cached
    found = session.scalar(
        select(model.id).where(
            model.tenant_id == ctx.tenant_id,
            model.source_system == ctx.source_system,
            model.source_id == source_id,
        )
    )
    if found is None:
        raise ValueError(f"unresolved {entity} reference: {source_id}")
    resolved: uuid.UUID = found
    ctx._ids[key] = resolved
    return resolved


def _upsert(
    session: Session, model: Any, conflict: tuple[str, ...], values: dict[str, Any]
) -> None:
    stmt = pg_insert(model.__table__).values(**values)
    update = {k: getattr(stmt.excluded, k) for k in values if k not in conflict}
    if "updated_at" in model.__table__.c:
        update["updated_at"] = func.now()
    session.execute(stmt.on_conflict_do_update(index_elements=list(conflict), set_=update))


def _base(ctx: IngestContext, rec: SourceRecord) -> dict[str, Any]:
    return {
        "tenant_id": ctx.tenant_id,
        "source_system": ctx.source_system,
        "source_id": rec.source_id,
    }


def upsert_location(session: Session, ctx: IngestContext, rec: SourceRecord) -> None:
    _upsert(
        session,
        Location,
        _SOURCE_KEY,
        {
            **_base(ctx, rec),
            "location_code": rec.data["location_code"],
            "name": rec.data.get("name"),
            "type": rec.data.get("type"),
        },
    )


def upsert_supplier(session: Session, ctx: IngestContext, rec: SourceRecord) -> None:
    _upsert(
        session,
        Supplier,
        _SOURCE_KEY,
        {
            **_base(ctx, rec),
            "supplier_code": rec.data["supplier_code"],
            "name": rec.data.get("name"),
            "status": rec.data.get("status"),
        },
    )


def upsert_item(session: Session, ctx: IngestContext, rec: SourceRecord) -> None:
    _upsert(
        session,
        Item,
        _SOURCE_KEY,
        {
            **_base(ctx, rec),
            "item_number": rec.data["item_number"],
            "description": rec.data.get("description"),
            "uom": rec.data.get("uom"),
            "item_type": rec.data.get("item_type"),
            "status": rec.data.get("status"),
            "unit_cost": rec.data.get("unit_cost"),
        },
    )


def upsert_asset(session: Session, ctx: IngestContext, rec: SourceRecord) -> None:
    location_id = (
        _resolve(session, ctx, Entity.LOCATION, rec.data["location_source_id"], Location)
        if rec.data.get("location_source_id")
        else None
    )
    _upsert(
        session,
        Asset,
        _SOURCE_KEY,
        {
            **_base(ctx, rec),
            "asset_number": rec.data["asset_number"],
            "description": rec.data.get("description"),
            "criticality": rec.data.get("criticality"),
            "status": rec.data.get("status"),
            "location_id": location_id,
        },
    )


def upsert_balance(session: Session, ctx: IngestContext, rec: SourceRecord) -> None:
    item_id = _resolve(session, ctx, Entity.ITEM, rec.data["item_source_id"], Item)
    location_id = _resolve(session, ctx, Entity.LOCATION, rec.data["location_source_id"], Location)
    _upsert(
        session,
        Balance,
        ("tenant_id", "item_id", "location_id"),
        {
            "tenant_id": ctx.tenant_id,
            "item_id": item_id,
            "location_id": location_id,
            "on_hand": rec.data.get("on_hand", 0),
            "available": rec.data.get("available", 0),
            "reserved": rec.data.get("reserved", 0),
            "min_level": rec.data.get("min_level"),
            "max_level": rec.data.get("max_level"),
            "as_of": rec.data.get("as_of"),
        },
    )


def upsert_transaction(session: Session, ctx: IngestContext, rec: SourceRecord) -> None:
    item_id = _resolve(session, ctx, Entity.ITEM, rec.data["item_source_id"], Item)
    location_id = _resolve(session, ctx, Entity.LOCATION, rec.data["location_source_id"], Location)
    _upsert(
        session,
        Transaction,
        _SOURCE_KEY,
        {
            **_base(ctx, rec),
            "item_id": item_id,
            "location_id": location_id,
            "type": rec.data["type"],
            "quantity": rec.data["quantity"],
            "unit_cost": rec.data.get("unit_cost"),
            "txn_date": rec.data.get("txn_date"),
        },
    )


Handler = Callable[[Session, IngestContext, SourceRecord], None]

HANDLERS: dict[Entity, Handler] = {
    Entity.LOCATION: upsert_location,
    Entity.SUPPLIER: upsert_supplier,
    Entity.ITEM: upsert_item,
    Entity.ASSET: upsert_asset,
    Entity.BALANCE: upsert_balance,
    Entity.TRANSACTION: upsert_transaction,
}
