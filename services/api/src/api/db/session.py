"""Engine and session factory (psycopg 3, sync).

The MVP uses synchronous SQLAlchemy with psycopg 3. The single driver also
backs Alembic migrations and dev scripts. Tenant context (``app.current_tenant_id``
GUC) is wired into the session in CV1.E6; here we only build the connectable.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import get_settings


def _to_psycopg_url(url: str) -> str:
    """Normalize a plain ``postgresql://`` URL to the psycopg 3 driver."""
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@lru_cache
def get_engine() -> Engine:
    """Return a process-wide SQLAlchemy engine bound to the configured DB."""
    settings = get_settings()
    return create_engine(
        _to_psycopg_url(settings.database_url),
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    """Return a process-wide session factory bound to the engine."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
