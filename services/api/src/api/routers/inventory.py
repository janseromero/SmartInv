"""Inventory catalog, balances, and summary views (CV2.E2).

Tenant-scoped, role-gated read endpoints backing the Inventory Health page:
a paginated/filterable item catalog with stock aggregates, per-site KPI
summary, item detail (balances + recent transactions), and the site list.
Health score and ABC class arrive in CV2.E3.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Balance, Item, Location, Transaction

router = APIRouter(tags=["inventory"], prefix="/inventory")

READ_ROLES = ("admin", "planner", "manager", "finance")
SortKey = Literal["item_number", "value", "on_hand"]


class ItemRow(BaseModel):
    id: uuid.UUID
    item_number: str
    description: str | None = None
    uom: str | None = None
    item_type: str | None = None
    status: str | None = None
    unit_cost: float | None = None
    on_hand: float
    inventory_value: float
    locations: int


class ItemsPage(BaseModel):
    items: list[ItemRow]
    total: int
    page: int
    page_size: int


class InventorySummary(BaseModel):
    total_items: int
    inventory_value: float
    excess_value: float
    dead_stock_value: float
    completeness_pct: float


class LocationRow(BaseModel):
    id: uuid.UUID
    location_code: str
    name: str | None = None


class BalanceRow(BaseModel):
    location_code: str
    on_hand: float
    min_level: float | None = None
    max_level: float | None = None
    as_of: datetime | None = None


class TransactionRow(BaseModel):
    type: str
    quantity: float
    txn_date: datetime | None = None
    location_code: str | None = None


class ItemDetail(BaseModel):
    id: uuid.UUID
    item_number: str
    description: str | None = None
    uom: str | None = None
    item_type: str | None = None
    status: str | None = None
    unit_cost: float | None = None
    balances: list[BalanceRow]
    recent_transactions: list[TransactionRow]


@router.get("/locations", response_model=list[LocationRow], summary="List sites")
def list_locations(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[LocationRow]:
    rows = session.scalars(select(Location).order_by(Location.location_code)).all()
    return [LocationRow(id=r.id, location_code=r.location_code, name=r.name) for r in rows]


@router.get("/summary", response_model=InventorySummary, summary="Inventory KPIs")
def inventory_summary(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    location_id: uuid.UUID | None = None,
) -> InventorySummary:
    bal_filter = [Balance.location_id == location_id] if location_id else []

    total_items = session.scalar(select(func.count()).select_from(Item)) or 0

    inventory_value = (
        session.scalar(
            select(func.coalesce(func.sum(Balance.on_hand * Item.unit_cost), 0))
            .select_from(Balance)
            .join(Item, Item.id == Balance.item_id)
            .where(*bal_filter)
        )
        or 0
    )

    excess_value = (
        session.scalar(
            select(
                func.coalesce(func.sum((Balance.on_hand - Balance.max_level) * Item.unit_cost), 0)
            )
            .select_from(Balance)
            .join(Item, Item.id == Balance.item_id)
            .where(Balance.max_level.isnot(None), Balance.on_hand > Balance.max_level, *bal_filter)
        )
        or 0
    )

    # Dead stock: on-hand value of items with no transactions in the last 365 days.
    moved_items = select(distinct(Transaction.item_id)).where(
        Transaction.txn_date >= func.now() - func.make_interval(0, 0, 0, 365)
    )
    dead_stock_value = (
        session.scalar(
            select(func.coalesce(func.sum(Balance.on_hand * Item.unit_cost), 0))
            .select_from(Balance)
            .join(Item, Item.id == Balance.item_id)
            .where(Balance.on_hand > 0, Item.id.notin_(moved_items), *bal_filter)
        )
        or 0
    )

    with_desc = (
        session.scalar(select(func.count()).select_from(Item).where(Item.description.isnot(None)))
        or 0
    )
    completeness = (with_desc / total_items * 100.0) if total_items else 0.0

    return InventorySummary(
        total_items=total_items,
        inventory_value=float(inventory_value),
        excess_value=float(excess_value),
        dead_stock_value=float(dead_stock_value),
        completeness_pct=round(completeness, 1),
    )


@router.get("/items", response_model=ItemsPage, summary="List items (catalog)")
def list_items(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    search: str | None = None,
    item_type: str | None = None,
    location_id: uuid.UUID | None = None,
    missing_data: bool = False,
    sort: SortKey = "item_number",
) -> ItemsPage:
    outer = location_id is None
    join_cond = Balance.item_id == Item.id
    if location_id is not None:
        join_cond = and_(Balance.item_id == Item.id, Balance.location_id == location_id)

    conditions = []
    if search:
        like = f"%{search}%"
        conditions.append(or_(Item.item_number.ilike(like), Item.description.ilike(like)))
    if item_type:
        conditions.append(Item.item_type == item_type)
    if missing_data:
        conditions.append(Item.description.is_(None))

    on_hand = func.coalesce(func.sum(Balance.on_hand), 0)
    value = func.coalesce(func.sum(Balance.on_hand * Item.unit_cost), 0)
    locations = func.count(distinct(Balance.location_id))

    total = (
        session.scalar(
            select(func.count(distinct(Item.id)))
            .select_from(Item)
            .join(Balance, join_cond, isouter=outer)
            .where(*conditions)
        )
        or 0
    )

    order: Any
    if sort == "value":
        order = value.desc()
    elif sort == "on_hand":
        order = on_hand.desc()
    else:
        order = Item.item_number.asc()

    rows = session.execute(
        select(
            Item.id,
            Item.item_number,
            Item.description,
            Item.uom,
            Item.item_type,
            Item.status,
            Item.unit_cost,
            on_hand.label("on_hand"),
            value.label("inventory_value"),
            locations.label("locations"),
        )
        .select_from(Item)
        .join(Balance, join_cond, isouter=outer)
        .where(*conditions)
        .group_by(Item.id)
        .order_by(order, Item.item_number.asc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()

    items = [
        ItemRow(
            id=r.id,
            item_number=r.item_number,
            description=r.description,
            uom=r.uom,
            item_type=r.item_type,
            status=r.status,
            unit_cost=float(r.unit_cost) if r.unit_cost is not None else None,
            on_hand=float(r.on_hand),
            inventory_value=float(r.inventory_value),
            locations=r.locations,
        )
        for r in rows
    ]
    return ItemsPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/items/{item_id}", response_model=ItemDetail, summary="Item detail")
def item_detail(
    item_id: uuid.UUID,
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> ItemDetail:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    balance_rows = session.execute(
        select(
            Location.location_code,
            Balance.on_hand,
            Balance.min_level,
            Balance.max_level,
            Balance.as_of,
        )
        .join(Location, Location.id == Balance.location_id)
        .where(Balance.item_id == item_id)
        .order_by(Location.location_code)
    ).all()

    txn_rows = session.execute(
        select(
            Transaction.type,
            Transaction.quantity,
            Transaction.txn_date,
            Location.location_code,
        )
        .join(Location, Location.id == Transaction.location_id, isouter=True)
        .where(Transaction.item_id == item_id)
        .order_by(Transaction.txn_date.desc().nullslast())
        .limit(10)
    ).all()

    return ItemDetail(
        id=item.id,
        item_number=item.item_number,
        description=item.description,
        uom=item.uom,
        item_type=item.item_type,
        status=item.status,
        unit_cost=float(item.unit_cost) if item.unit_cost is not None else None,
        balances=[
            BalanceRow(
                location_code=b.location_code,
                on_hand=float(b.on_hand),
                min_level=float(b.min_level) if b.min_level is not None else None,
                max_level=float(b.max_level) if b.max_level is not None else None,
                as_of=b.as_of,
            )
            for b in balance_rows
        ],
        recent_transactions=[
            TransactionRow(
                type=t.type,
                quantity=float(t.quantity),
                txn_date=t.txn_date,
                location_code=t.location_code,
            )
            for t in txn_rows
        ],
    )
