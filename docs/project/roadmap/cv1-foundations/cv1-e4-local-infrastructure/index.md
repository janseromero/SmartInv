[< CV1 Foundations](../index.md)

# CV1.E4 — Local Infrastructure

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done

---

## What This Is

`docker compose up` brings the local data platform online: Postgres (with `pgvector`, `pg_trgm`, `tsvector`), Redis, and a SeaweedFS S3-compatible object store. `make dev-up` boots the stack and bootstraps the object-store bucket; `make check-infra` smoke-tests connectivity. This is the contract that lets any new contributor be productive in under an hour.

LLM observability uses **Langfuse Cloud (free tier)** — no local Langfuse service. CV1.E4 ships only the `LANGFUSE_*` configuration scaffolding; the SDK is wired into the LLM gateway in [CV5.E1](../../cv5-conversational-analyst/cv5-e1-llm-gateway-tool-catalog/index.md), where the first traces are produced.

Stack choice anchored in [ADR-004 (data platform)](../../../decisions.md#adr-004--data-platform--postgres--redis--s3-compatible), [ADR-017 (SeaweedFS)](../../../decisions.md#adr-017--seaweedfs-supersedes-garage-as-the-mvp-object-store), and [ADR-018 (Langfuse Cloud)](../../../decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E4.S1 | `docker-compose.yml` (root) with Postgres 16 + pgvector + pg_trgm | ✅ Done |
| CV1.E4.S2 | Add Redis 7 service | ✅ Done |
| CV1.E4.S3 | Add **SeaweedFS** object store with bucket bootstrap script | ✅ Done |
| CV1.E4.S4 | ~~Langfuse self-hosted~~ → **Langfuse Cloud free tier**; env scaffolding only (SDK wiring deferred to [CV5.E1](../../cv5-conversational-analyst/cv5-e1-llm-gateway-tool-catalog/index.md), [ADR-018](../../../decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability)) | ✅ Done |
| CV1.E4.S5 | Document local-dev workflow in `README.md` and add `make dev-up` / `make dev-down` shortcuts | ✅ Done |
| CV1.E4.S6 | Add `.env.example` with non-secret defaults for every service | ✅ Done |

---

## Done Condition

- `docker compose up` (via `make dev-up`) boots the three services in under 30 seconds on a mid-range laptop.
- `make check-infra` confirms `services/api` can reach Postgres (with `vector` + `pg_trgm` extensions), Redis, and the object store at the documented URLs.
- Langfuse Cloud credentials are carried in config (`LANGFUSE_*`); the SDK itself is wired in CV5.E1 — no local Langfuse service ([ADR-018](../../../decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability)).
- The README local-dev section is accurate and end-to-end reproducible.

---

## Out of Scope

- Cloud / production deployment manifests — **CV8.E5 (Deployment runbook)**.
- Multi-tenant orchestration — **CV15 (Compliance & Multi-Tenant Operations)**.
- Real source-system mocks — Future.
- DB schemas / tables / Alembic — **CV1.E5 (Database Foundations)**. E4 stands up an empty Postgres with extensions only.
- Langfuse SDK integration — **CV5.E1 (LLM Gateway & Tool Catalog)**.
- Self-hosted Langfuse — Phase 2 ([ADR-018](../../../decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability)).

---

**See also:** [CV1](../index.md) · [CV1.E5](../cv1-e5-database-foundations/index.md) · [ADR-017](../../../decisions.md#adr-017--seaweedfs-supersedes-garage-as-the-mvp-object-store) · [ADR-018](../../../decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability)
