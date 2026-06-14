"""Mint a development JWT for a tenant (CV1.E6 / ADR-021).

Resolves a tenant by slug and prints a signed HS256 token. Dev only.

    uv run python scripts/dev_token.py --tenant smartinv-dev --roles admin,planner
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

from api.auth.tokens import mint_dev_token
from api.db.models.core import Tenant
from api.db.session import plain_session
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser(description="Mint a SmartInv dev token.")
    parser.add_argument("--tenant", default="smartinv-dev", help="Tenant slug.")
    parser.add_argument("--roles", default="admin", help="Comma-separated roles.")
    parser.add_argument("--sub", default=None, help="Subject id (defaults to dev|<tenant>).")
    parser.add_argument("--email", default=None, help="Email claim.")
    args = parser.parse_args()

    with plain_session() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.slug == args.tenant))
    if tenant is None:
        print(f"unknown tenant '{args.tenant}' — run `make seed` first")
        return 1

    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    token = mint_dev_token(
        sub=args.sub or f"dev|{args.tenant}",
        tenant_id=tenant.id,
        roles=roles,
        email=args.email,
    )
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
