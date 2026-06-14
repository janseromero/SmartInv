"""Engine and session factory (psycopg 3, sync).

The MVP uses synchronous SQLAlchemy with psycopg 3. The single driver also
backs Alembic migrations and dev scripts. Tenant context (``app.current_tenant_id``
GUC) is wired into the session in CV1.E6; here we only build the connectable.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from api.config import get_settings

TENANT_GUC = "app.current_tenant_id"


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


@contextmanager
def tenant_session(tenant_id: str) -> Iterator[Session]:
    """Yield a session inside a transaction with the tenant RLS GUC set.

    ``set_config(..., is_local => true)`` scopes the GUC to the transaction, so
    it never leaks across pooled connections. RLS then filters every query to
    the given tenant. Used by the request-scoped FastAPI dependency.
    """
    with get_sessionmaker()() as session, session.begin():
        session.execute(text(f"SELECT set_config('{TENANT_GUC}', :tid, true)"), {"tid": tenant_id})
        yield session


@contextmanager
def plain_session() -> Iterator[Session]:
    """Yield a session with no tenant context (for non-tenant-scoped reads)."""
    with get_sessionmaker()() as session, session.begin():
        yield session
