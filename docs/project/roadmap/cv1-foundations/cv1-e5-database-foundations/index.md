[< CV1 Foundations](../index.md)

# CV1.E5 — Database Foundations

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done
**Depends on:** CV1.E4

---

## What This Is

Alembic migrations + the eight initial Postgres schemas that organize SmartInv's domain: `core` (tenants, users, roles), `inventory`, `sources`, `ml`, `agent`, `workflow`, `audit`, `rag`. Row-Level Security is enabled on every tenant-scoped table so tenant isolation is enforced at the database, not only at the application layer.

Per [Engineering Principles · AR3](../../../../process/engineering-principles.md#ar3--tenant-id-is-a-first-class-citizen), tenant_id is a first-class citizen everywhere — column on every table, predicate on every query, value on every log line.

Stack and RLS pattern anchored in [ADR-019](../../../decisions.md#adr-019--persistence-stack-sqlalchemy-20--alembic--psycopg-3-rls-default-deny). Tables follow the **direct-conform** model with the natural-key seam (`source_system` + `source_id`); modeled medallion Bronze is deferred.

> **RLS enforcement note:** Postgres superusers bypass RLS even with FORCE. The dev `smartinv` role is a superuser used for migrations/admin only. The least-privilege runtime login role the API connects with — and the per-request `app.current_tenant_id` wiring — land in [CV1.E6](../cv1-e6-auth-tenancy/index.md). E5 proves the policy semantics against a dedicated non-superuser role.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E5.S1 | Alembic configured with autogenerate against a SQLAlchemy 2.0 declarative base | ✅ Done |
| CV1.E5.S2 | Create `core` schema: tenants, users, roles, role_bindings | ✅ Done |
| CV1.E5.S3 | Create `inventory` schema: items, balances, transactions, assets, locations, work_orders, purchase_orders, suppliers | ✅ Done |
| CV1.E5.S4 | Create `sources` schema: connectors, sync_runs, error_log | ✅ Done |
| CV1.E5.S5 | Create `ml` schema: model_registry, predictions, recommendations, feature_snapshots | ✅ Done |
| CV1.E5.S6 | Create `agent` schema: conversations, runs, events, tool_catalog (checkpoints owned by LangGraph in CV5) | ✅ Done |
| CV1.E5.S7 | Create `workflow` schema: approvals, approval_events | ✅ Done |
| CV1.E5.S8 | Create `audit` schema: append-only events table with indexes | ✅ Done |
| CV1.E5.S9 | Create `rag` schema: documents, chunks (with `vector(1536)`) | ✅ Done |
| CV1.E5.S10 | Enable RLS (FORCE) on every tenant-scoped table; default-deny when tenant context is not set | ✅ Done |
| CV1.E5.S11 | Seed script for local-dev fixture data (one synthetic tenant + admin) | ✅ Done |

---

## Done Condition

- ✅ `alembic upgrade head` produces the full eight-schema state (28 tables) on an empty database; `downgrade base` removes it cleanly. Verified in CI against a real Postgres + pgvector.
- ✅ Every tenant-scoped table (24 of 28) has a `tenant_isolation` RLS policy that rejects access when `app.current_tenant_id` is not set (default-deny), proven by an integration test against a non-superuser role.
- ✅ `make seed` creates one local tenant + admin user (idempotent).
- ✅ Down-migrations exist for every up-migration.

## How to use

```bash
make migrate        # alembic upgrade head
make migrate-down   # downgrade one revision
make seed           # seed dev tenant + admin
```

---

## Out of Scope

- Real customer data ingestion — **CV2.E1 (Maximo Connector)**.
- Application-layer tenancy enforcement — **CV1.E6**.
- Per-tenant schema sharding — Future.

---

**See also:** [CV1](../index.md) · [CV1.E6](../cv1-e6-auth-tenancy/index.md) · [Engineering Principles · AR3](../../../../process/engineering-principles.md#ar3--tenant-id-is-a-first-class-citizen)
