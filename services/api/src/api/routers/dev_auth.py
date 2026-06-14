"""Development-only token issuer (ADR-021).

Mints HS256 tokens for a tenant chosen by slug, so the web app and tests can
authenticate without a real IdP. Returns 404 outside dev/test environments —
this endpoint must never exist in production.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.models.core import Tenant
from api.db.session import plain_session

router = APIRouter(tags=["auth"], prefix="/auth")


class DevLoginRequest(BaseModel):
    tenant_slug: str = "smartinv-dev"
    roles: list[str] = Field(default_factory=lambda: ["admin"])
    sub: str | None = None
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 — OAuth token type, not a secret


@router.post("/dev-login", response_model=TokenResponse, summary="Mint a dev token")
def dev_login(body: DevLoginRequest) -> TokenResponse:
    settings = get_settings()
    if settings.environment not in ("dev", "test"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not available.")

    with plain_session() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.slug == body.tenant_slug))
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown tenant '{body.tenant_slug}'. Run `make seed` first.",
        )

    token = mint_dev_token(
        sub=body.sub or f"dev|{body.tenant_slug}",
        tenant_id=tenant.id,
        roles=body.roles,
        email=body.email,
    )
    return TokenResponse(access_token=token)
