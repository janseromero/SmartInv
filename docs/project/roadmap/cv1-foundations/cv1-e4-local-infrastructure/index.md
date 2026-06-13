[< CV1 Foundations](../index.md)

# CV1.E4 — Local Infrastructure

**CV:** [CV1 — Foundations](../index.md)
**Status:** ⚪ Planned

---

## What This Is

`docker compose up` brings the entire local development stack online: Postgres (with `pgvector`, `pg_trgm`, `tsvector`), Redis, an S3-compatible object store, and Langfuse for agent observability. This is the contract that lets any new contributor be productive in under an hour.

Stack choice anchored in [ADR-004 (data platform)](../../../decisions.md#adr-004--data-platform--postgres--redis--s3-compatible) and [ADR-005 (Garage)](../../../decisions.md#adr-005--garage-as-the-mvp-s3-compatible-store).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E4.S1 | `docker-compose.yml` with Postgres 16 + pgvector + pg_trgm | 📥 Backlog |
| CV1.E4.S2 | Add Redis 7 service | 📥 Backlog |
| CV1.E4.S3 | Add object store (Garage or MinIO) with bucket bootstrap script | 📥 Backlog |
| CV1.E4.S4 | Add Langfuse self-hosted service for agent observability | 📥 Backlog |
| CV1.E4.S5 | Document local-dev workflow in `README.md` and add `make dev-up` / `make dev-down` shortcuts | 📥 Backlog |
| CV1.E4.S6 | Add `.env.example` with non-secret defaults for every service | 📥 Backlog |

---

## Done Condition

- `docker compose up` boots all four services in under 30 seconds on a mid-range laptop.
- A connection from `services/api` succeeds to Postgres, Redis, and the object store at the documented URLs.
- Langfuse is reachable on `http://localhost:3300` with a default project.
- The README local-dev section is accurate and end-to-end reproducible.

---

## Out of Scope

- Cloud / production deployment manifests — **CV8.E5 (Deployment runbook)**.
- Multi-tenant orchestration — **CV15 (Compliance & Multi-Tenant Operations)**.
- Real source-system mocks — Future.

---

**See also:** [CV1](../index.md) · [CV1.E5](../cv1-e5-database-foundations/index.md) · [ADR-005](../../../decisions.md#adr-005--garage-as-the-mvp-s3-compatible-store)
