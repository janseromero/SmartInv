[< CV1 Foundations](../index.md)

# CV1.E5 — Database Foundations

**CV:** [CV1 — Foundations](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV1.E4

---

## What This Is

Alembic migrations + the eight initial Postgres schemas that organize SmartInv's domain: `core` (tenants, users, roles), `inventory`, `sources`, `ml`, `agent`, `workflow`, `audit`, `rag`. Row-Level Security is enabled on every tenant-scoped table so tenant isolation is enforced at the database, not only at the application layer.

Per [Engineering Principles · AR3](../../../../process/engineering-principles.md#ar3--tenant-id-is-a-first-class-citizen), tenant_id is a first-class citizen everywhere — column on every table, predicate on every query, value on every log line.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E5.S1 | Alembic configured with autogenerate against a SQLAlchemy declarative base | 📥 Backlog |
| CV1.E5.S2 | Create `core` schema: tenants, users, roles, role_bindings | 📥 Backlog |
| CV1.E5.S3 | Create `inventory` schema: items, balances, transactions, assets, locations, work_orders, purchase_orders, suppliers | 📥 Backlog |
| CV1.E5.S4 | Create `sources` schema: connectors, sync_runs, error_log | 📥 Backlog |
| CV1.E5.S5 | Create `ml` schema: model_registry, predictions, recommendations, feature_snapshots | 📥 Backlog |
| CV1.E5.S6 | Create `agent` schema: conversations, runs, checkpoints, events, tool_catalog | 📥 Backlog |
| CV1.E5.S7 | Create `workflow` schema: approvals, approval_events | 📥 Backlog |
| CV1.E5.S8 | Create `audit` schema: append-only events table with indexes | 📥 Backlog |
| CV1.E5.S9 | Create `rag` schema: documents, chunks (with `vector(1536)`) | 📥 Backlog |
| CV1.E5.S10 | Enable RLS on every tenant-scoped table; default deny when tenant context is not set | 📥 Backlog |
| CV1.E5.S11 | Seed script for local-dev fixture data (one synthetic tenant) | 📥 Backlog |

---

## Done Condition

- `alembic upgrade head` produces the full eight-schema state on an empty database.
- Every tenant-scoped table has an `RLS ENABLE` policy that rejects access when `app.current_tenant_id` is not set.
- A seed script creates one local tenant + admin user for dev.
- Down-migrations exist for every up-migration.

---

## Out of Scope

- Real customer data ingestion — **CV2.E1 (Maximo Connector)**.
- Application-layer tenancy enforcement — **CV1.E6**.
- Per-tenant schema sharding — Future.

---

**See also:** [CV1](../index.md) · [CV1.E6](../cv1-e6-auth-tenancy/index.md) · [Engineering Principles · AR3](../../../../process/engineering-principles.md#ar3--tenant-id-is-a-first-class-citizen)
