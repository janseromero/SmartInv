"""Ingest the fixture inventory dataset for the dev tenant (CV2.E1).

Idempotent — re-running upserts the same rows. Requires `make seed` first.

    uv run python scripts/sync_fixtures.py [--tenant smartinv-dev]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

from api.db.models.core import Tenant
from api.db.session import plain_session, tenant_session
from api.ingestion.fixture_sync import run_fixture_sync
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync the fixture inventory dataset.")
    parser.add_argument("--tenant", default="smartinv-dev", help="Tenant slug.")
    args = parser.parse_args()

    with plain_session() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.slug == args.tenant))
    if tenant is None:
        print(f"unknown tenant '{args.tenant}' — run `make seed` first")
        return 1

    with tenant_session(str(tenant.id)) as session:
        summary = run_fixture_sync(session, tenant.id)

    for entity, counts in summary.items():
        print(
            f"{entity:12} read={counts['read']:5} "
            f"upserted={counts['upserted']:5} failed={counts['failed']:5}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
