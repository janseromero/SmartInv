"""Deliver pending source-system writes for the dev tenant (CV6.E4).

    uv run python scripts/dispatch.py [--tenant smartinv-dev]

Processes the source-write queue through the configured ``SourceWriter`` (Echo
in the MVP). Run after approving recommendations in the Approvals screen.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

from api.db.models.core import Tenant
from api.db.session import plain_session, tenant_session
from api.dispatch.service import process_pending
from api.infra.providers import get_source_writer
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser(description="Deliver pending source-system writes.")
    parser.add_argument("--tenant", default="smartinv-dev", help="Tenant slug.")
    args = parser.parse_args()

    with plain_session() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.slug == args.tenant))
    if tenant is None:
        print(f"unknown tenant '{args.tenant}' — run `make seed` first")
        return 1

    with tenant_session(str(tenant.id)) as session:
        summary = process_pending(
            session, tenant_id=tenant.id, writer=get_source_writer(), actor="cli"
        )

    for key, value in summary.items():
        print(f"{key:14} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
