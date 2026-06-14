"""SmartInv persistence layer (CV1.E5).

Exposes the SQLAlchemy declarative base, common mixins, and the engine/session
factory. Domain models live under :mod:`api.db.models`.
"""

from api.db.base import Base, TenantMixin, TimestampMixin
from api.db.session import get_engine, get_sessionmaker

__all__ = [
    "Base",
    "TenantMixin",
    "TimestampMixin",
    "get_engine",
    "get_sessionmaker",
]
