"""Minimal tenant-scoped inventory read endpoint.

Exists in E6 to demonstrate the isolation loop end-to-end (RLS filters results
to the caller's tenant). The full Inventory Health API is CV2.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Item

INVENTORY_READ_ROLES = ("admin", "planner", "manager")

router = APIRouter(tags=["inventory"], prefix="/inventory")


class ItemResponse(BaseModel):
    id: uuid.UUID
    item_number: str
    description: str | None = None


@router.get("/items", response_model=list[ItemResponse], summary="List items (current tenant)")
def list_items(
    _user: Annotated[CurrentUser, Depends(require_role(*INVENTORY_READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[ItemResponse]:
    """Return inventory items for the caller's tenant. RLS enforces isolation."""
    rows = session.scalars(select(Item).order_by(Item.item_number)).all()
    return [
        ItemResponse(id=row.id, item_number=row.item_number, description=row.description)
        for row in rows
    ]
