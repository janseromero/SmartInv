"""Seed local-dev fixture data (CV1.E5.S11). Idempotent.

Creates one synthetic tenant, the role catalog, and one admin user bound to
that tenant. Safe to run repeatedly. Intended for local development only.
"""

from __future__ import annotations

import pathlib
import sys

# Make the api package importable without requiring an editable install.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

from api.db.models.core import Role, RoleBinding, Tenant, User
from api.db.session import get_sessionmaker
from sqlalchemy import select, text
from sqlalchemy.orm import Session

TENANT_SLUG = "smartinv-dev"
ADMIN_EMAIL = "admin@smartinv.local"
ROLE_CATALOG = (
    ("admin", "Administrator"),
    ("planner", "Inventory Planner"),
    ("manager", "Maintenance Manager"),
    ("finance", "Finance / CFO Office"),
    ("reliability", "Reliability Engineer"),
)


def _ensure_roles(session: Session) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for key, name in ROLE_CATALOG:
        role = session.scalar(select(Role).where(Role.key == key))
        if role is None:
            role = Role(key=key, name=name)
            session.add(role)
            session.flush()
        roles[key] = role
    return roles


def main() -> int:
    session_factory = get_sessionmaker()
    with session_factory() as session:
        roles = _ensure_roles(session)

        tenant = session.scalar(select(Tenant).where(Tenant.slug == TENANT_SLUG))
        if tenant is None:
            tenant = Tenant(slug=TENANT_SLUG, name="SmartInv Dev", status="active")
            session.add(tenant)
            session.flush()

        # Tenant-scoped writes set the RLS GUC so this works under a
        # least-privilege role too (superuser bypasses it harmlessly).
        session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant.id)},
        )

        user = session.scalar(
            select(User).where(User.tenant_id == tenant.id, User.email == ADMIN_EMAIL)
        )
        if user is None:
            user = User(
                tenant_id=tenant.id,
                email=ADMIN_EMAIL,
                display_name="Dev Admin",
                status="active",
            )
            session.add(user)
            session.flush()

        binding = session.scalar(
            select(RoleBinding).where(
                RoleBinding.tenant_id == tenant.id,
                RoleBinding.user_id == user.id,
                RoleBinding.role_id == roles["admin"].id,
            )
        )
        if binding is None:
            session.add(
                RoleBinding(tenant_id=tenant.id, user_id=user.id, role_id=roles["admin"].id)
            )

        session.commit()
        print(f"seeded tenant '{TENANT_SLUG}' with admin user '{ADMIN_EMAIL}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
