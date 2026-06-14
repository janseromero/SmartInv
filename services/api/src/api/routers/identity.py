"""``/me`` — current principal, with just-in-time user provisioning."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user, get_tenant_session
from api.auth.models import CurrentUser
from api.db.models.core import User

router = APIRouter(tags=["identity"])


class MeResponse(BaseModel):
    sub: str
    tenant_id: uuid.UUID
    email: str | None = None
    roles: list[str] = Field(default_factory=list)


@router.get("/me", response_model=MeResponse, summary="Current principal")
def me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> MeResponse:
    """Return the authenticated principal, provisioning the user row on first sight."""
    existing = session.scalar(select(User).where(User.external_subject == user.sub))
    if existing is None:
        session.add(
            User(
                tenant_id=user.tenant_id,
                external_subject=user.sub,
                email=user.email or f"{user.sub}@dev.local",
                display_name=user.email,
            )
        )
    return MeResponse(sub=user.sub, tenant_id=user.tenant_id, email=user.email, roles=user.roles)
