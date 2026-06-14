"""Token minting and verification — the IdP seam (ADR-021).

MVP: symmetric HS256 dev tokens signed with ``SMARTINV_JWT_SECRET``. The claim
names (``sub``, ``tenant_id``, ``roles``, ``email``, ``iss``, ``aud``, ``exp``)
mirror a real OIDC token, so production only changes the verification method
(to RS256 + JWKS) inside :func:`verify_token`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from api.auth.models import CurrentUser
from api.config import Settings, get_settings


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or untrusted."""


def mint_dev_token(
    *,
    sub: str,
    tenant_id: uuid.UUID | str,
    roles: list[str],
    email: str | None = None,
    settings: Settings | None = None,
) -> str:
    """Sign an HS256 development token. Never use in production (ADR-021)."""
    cfg = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "tenant_id": str(tenant_id),
        "roles": roles,
        "email": email,
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=cfg.jwt_expiry_minutes)).timestamp()),
    }
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def verify_token(raw: str, settings: Settings | None = None) -> CurrentUser:
    """Verify a bearer token and return the authenticated principal.

    This is the single swap point for a real IdP: replace HS256 + shared secret
    with RS256 + JWKS lookup, keeping the return type identical.
    """
    cfg = settings or get_settings()
    try:
        claims = jwt.decode(
            raw,
            cfg.jwt_secret,
            algorithms=[cfg.jwt_algorithm],
            audience=cfg.jwt_audience,
            issuer=cfg.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc

    try:
        return CurrentUser(
            sub=claims["sub"],
            tenant_id=uuid.UUID(claims["tenant_id"]),
            roles=list(claims.get("roles", [])),
            email=claims.get("email"),
        )
    except (KeyError, ValueError) as exc:
        raise TokenError(f"invalid claims: {exc}") from exc
