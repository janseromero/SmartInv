"""Authentication and tenant-context primitives (CV1.E6).

The IdP lives behind a single seam: ``verify_token`` turns a raw bearer token
into a :class:`CurrentUser`. The MVP verifies HS256 dev tokens; a real IdP
(Auth0/Keycloak) swaps in by changing only ``verify_token`` (ADR-021).
"""

from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.auth.tokens import TokenError, mint_dev_token, verify_token

__all__ = [
    "CurrentUser",
    "TokenError",
    "get_current_user",
    "get_tenant_session",
    "mint_dev_token",
    "require_role",
    "verify_token",
]
