[< CV1 Foundations](../index.md)

# CV1.E7 — Core Service Contracts

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done
**Depends on:** CV1.E5, CV1.E6

---

## What This Is

Defines the four `typing.Protocol` interfaces that protect every later CV from infrastructure choice changes: `WorkflowEngine`, `ObjectStore`, `LLMGateway`, `SearchIndex`. The protocols live in **`api/contracts/`**; implementations in **`api/infra/`**, wired by `api/infra/providers.py` (the composition root). Domain code imports only the protocols ([ADR-022](../../../decisions.md#adr-022--core-service-contracts-typingprotocol-seams--contract-test-against-fakes)).

This is the structural commitment behind [ADR-003 (no Temporal)](../../../decisions.md#adr-003--no-temporal-in-mvp): we never need to write Temporal code if we never write code against Temporal — only against `WorkflowEngine`.

**What ships real vs faked (ADR-022):** `ObjectStore` (S3/SeaweedFS) and `WorkflowEngine` (Postgres state machine) have real MVP impls now; `LLMGateway` (echo) and `SearchIndex` (in-memory) ship fakes, with their real impls deferred to their first consumers (CV5, CV2). Every protocol is exercised by a contract suite against its impl(s) + an in-memory fake.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E7.S1 | `WorkflowEngine` protocol (start/signal/query/cancel) + `PostgresWorkflowEngine` impl | ✅ Done |
| CV1.E7.S2 | `ObjectStore` protocol (put/get/url/list/delete/exists) + `S3ObjectStore` (SeaweedFS) impl | ✅ Done |
| CV1.E7.S3 | `LLMGateway` protocol + `EchoLLMGateway` fake (real `LiteLLMGateway` → CV5.E1) | ✅ Done (fake) |
| CV1.E7.S4 | `SearchIndex` protocol + `InMemorySearchIndex` fake (real `PostgresSearchIndex` pg_trgm → CV2) | ✅ Done (fake) |
| CV1.E7.S5 | Contract tests per protocol against real impl + in-memory fake (swap-compliant) | ✅ Done |

---

## Done Condition

- ✅ All four protocols compile against an MVP implementation (2 real, 2 fake).
- ✅ A contract suite asserts protocol compliance against each implementation; `ObjectStore` and `WorkflowEngine` run against both a real impl and an in-memory fake.
- ✅ Domain code imports only `api.contracts`; concrete impls are named only in `api/infra/providers.py`.
- ✅ A second (in-memory) implementation substitutes in the contract tests without code changes.

## Deferred to owning CVs (ADR-022)

- Real `LiteLLMGateway` → **CV5.E1** (its first consumer).
- Real `PostgresSearchIndex` (`pg_trgm`) → **CV2** (item search).
- Temporal `WorkflowEngine` → Phase 2.

---

## Out of Scope

- Temporal `WorkflowEngine` implementation — Phase 2.
- Qdrant / Weaviate `SearchIndex` implementation — Future.
- Cloud-native ObjectStore implementations (S3, R2, GCS) — added when needed for deployment.

---

**See also:** [CV1](../index.md) · [CV1.E5](../cv1-e5-database-foundations/index.md) · [ADR-003](../../../decisions.md#adr-003--no-temporal-in-mvp) · [Engineering Principles · AR2](../../../../process/engineering-principles.md#ar2--interfaces-over-implementations)
