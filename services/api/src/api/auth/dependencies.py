"""FastAPI dependencies for authentication, RBAC, and tenant-scoped sessions."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api.auth.models import CurrentUser
from api.auth.tokens import TokenError, verify_token
from api.db.session import tenant_session


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Resolve the authenticated principal from the ``Authorization`` header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_role(*roles: str) -> Callable[[CurrentUser], CurrentUser]:
    """Dependency factory gating an endpoint on having any of ``roles``."""

    def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not user.has_any_role(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return checker


def get_tenant_session(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Iterator[Session]:
    """Yield a DB session bound to the current tenant (RLS enforced)."""
    with tenant_session(str(user.tenant_id)) as session:
        yield session
