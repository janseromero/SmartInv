[< CV1 Foundations](../index.md)

# CV1.E7 — Core Service Contracts

**CV:** [CV1 — Foundations](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV1.E5, CV1.E6

---

## What This Is

Defines the four interfaces that protect every later CV from infrastructure choice changes: `WorkflowEngine`, `ObjectStore`, `LLMGateway`, `SearchIndex`. Each ships with exactly one MVP implementation. The interfaces live in `packages/contracts`; the implementations live in `services/api/<domain>`.

This is the structural commitment behind [ADR-003 (no Temporal)](../../../decisions.md#adr-003--no-temporal-in-mvp): we never need to write Temporal code if we never write code against Temporal — only against `WorkflowEngine`.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E7.S1 | Define `WorkflowEngine` protocol (start, signal, query, cancel) + `PostgresWorkflowEngine` implementation | 📥 Backlog |
| CV1.E7.S2 | Define `ObjectStore` protocol (put, get, url, list, delete) + `GarageObjectStore` implementation | 📥 Backlog |
| CV1.E7.S3 | Define `LLMGateway` protocol + `LiteLLMGateway` implementation pointing to LiteLLM proxy | 📥 Backlog |
| CV1.E7.S4 | Define `SearchIndex` protocol + `PostgresSearchIndex` implementation using `pg_trgm` + `tsvector` | 📥 Backlog |
| CV1.E7.S5 | Contract tests for every interface (one suite, both implementations swap-compliant) | 📥 Backlog |

---

## Done Condition

- All four interfaces compile against their MVP implementation.
- A contract test suite runs against each implementation and asserts protocol compliance.
- Domain code never imports a concrete implementation — only the protocol.
- A second implementation of any interface (mocked) can be substituted in tests without code changes.

---

## Out of Scope

- Temporal `WorkflowEngine` implementation — Phase 2.
- Qdrant / Weaviate `SearchIndex` implementation — Future.
- Cloud-native ObjectStore implementations (S3, R2, GCS) — added when needed for deployment.

---

**See also:** [CV1](../index.md) · [CV1.E5](../cv1-e5-database-foundations/index.md) · [ADR-003](../../../decisions.md#adr-003--no-temporal-in-mvp) · [Engineering Principles · AR2](../../../../process/engineering-principles.md#ar2--interfaces-over-implementations)
