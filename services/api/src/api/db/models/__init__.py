"""SmartInv ORM models, grouped by Postgres schema.

Importing this package registers every model on ``Base.metadata`` so Alembic
autogenerate and ``create_all`` see the full schema set.
"""

from api.db.models import (
    agent,
    audit,
    core,
    inventory,
    ml,
    rag,
    sources,
    workflow,
)

__all__ = [
    "agent",
    "audit",
    "core",
    "inventory",
    "ml",
    "rag",
    "sources",
    "workflow",
]
