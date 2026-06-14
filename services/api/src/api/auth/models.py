"""Identity value objects shared across the auth layer."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    """The authenticated principal for a request.

    This shape is intentionally what a real OIDC token provides (``sub``,
    ``tenant_id``, ``roles``, ``email``) so swapping the dev issuer for a real
    IdP changes only token verification, not anything downstream (ADR-021).
    """

    sub: str = Field(..., description="Stable subject identifier from the IdP.")
    tenant_id: uuid.UUID = Field(..., description="Tenant the principal belongs to.")
    roles: list[str] = Field(default_factory=list, description="Authorization roles.")
    email: str | None = Field(default=None, description="Principal email, if present.")

    def has_any_role(self, roles: tuple[str, ...]) -> bool:
        return bool(set(roles) & set(self.roles))
