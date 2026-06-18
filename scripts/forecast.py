"""Recompute demand forecasts for the dev tenant (CV3.E1).

uv run python scripts/forecast.py [--tenant smartinv-dev]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

from api.db.models.core import Tenant
from api.db.session import plain_session, tenant_session
from api.forecast.service import run_forecast
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute demand forecasts.")
    parser.add_argument("--tenant", default="smartinv-dev", help="Tenant slug.")
    args = parser.parse_args()

    with plain_session() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.slug == args.tenant))
    if tenant is None:
        print(f"unknown tenant '{args.tenant}' — run `make seed` first")
        return 1

    with tenant_session(str(tenant.id)) as session:
        summary = run_forecast(session, tenant.id)

    for key, value in summary.items():
        print(f"{key:20} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
