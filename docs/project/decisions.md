# SmartInv — Architecture Decision Records

> Every significant directional choice is recorded here. New ADRs are appended at the end.
> Format: **Context · Decision · Consequences · Alternatives considered**.

---

## ADR-001 — Monorepo with Turborepo + pnpm

**Context.** SmartInv will share substantial code between web, future mobile, and Python services (types, contracts, design tokens).

**Decision.** Use a single monorepo managed by **Turborepo** with **pnpm** for JS/TS and **uv** for Python.

**Consequences.**
- One PR can touch web + types + API client coherently.
- Local dev needs Node + Python + Docker.
- Versioning is per-package via changesets.

**Alternatives considered.** Polyrepo (rejected — too much coordination overhead at our size); Nx (viable, slightly heavier than Turborepo).

---

## ADR-002 — Web-only MVP, but shared-system-ready (Option B)

**Context.** Mobile is on the long-term roadmap but not on the MVP. We must not pay the cost of a cross-platform UI system now, nor pay the cost of a rewrite later.

**Decision.** Start web-only with **Next.js 14 + Tailwind + shadcn/ui**, but enforce **design tokens** and **component contracts** from day one — so the path to a shared system (Tamagui or equivalent) is a re-skin, not a rewrite.

**Consequences.**
- `packages/tokens` is the single source of truth for colors, spacing, typography, radii.
- `packages/ui-contracts` defines TS interfaces consumed by screens.
- `packages/ui-web` implements the contracts; future `packages/ui-native` will reimplement them.
- ESLint rule bans direct imports of `@radix-ui/*` outside `ui-web`.
- Stylelint rule bans raw hex codes in `apps/web`.

**Alternatives considered.** Tamagui from day one (rejected — slower initial velocity for an MVP that isn't yet mobile); pure Tailwind without contracts (rejected — guarantees rewrite later).

---

## ADR-003 — No Temporal in MVP

**Context.** Temporal is excellent for durable workflows, retries, timers, and audit. It also adds operational complexity, a learning curve, and determinism constraints.

**Decision.** Defer Temporal. Implement the MVP approval workflow as a **Postgres-backed state machine** (`workflow.approvals` + `workflow.approval_events`) behind a `WorkflowEngine` interface.

**Consequences.**
- One less service to operate.
- All approval state is in Postgres — easy to debug with `psql`.
- Migration to Temporal later is a drop-in replacement of the interface.

**Triggers to revisit.** Workflows spanning days/weeks; complex compensation/saga logic; thousands of concurrent workflows per tenant; replay-for-compliance needs.

**Alternatives considered.** Temporal from day one (rejected — overkill for MVP); Celery chains (rejected — weaker state model); custom thread/loop (rejected — reinvention).

---

## ADR-004 — Data platform = Postgres + Redis + S3-compatible

**Context.** A full data platform (Kafka, Lakehouse, MLflow, Feast, OpenSearch, Qdrant) is overkill at MVP scale and operational cost.

**Decision.** MVP data platform is **three components**:
1. **PostgreSQL 16** with `pgvector`, `pg_trgm`, `tsvector`, and Row-Level Security.
2. **Redis** for cache, Dramatiq broker, sessions, rate limits.
3. **S3-compatible object store** for reports, uploads, model artifacts.

**Consequences.**
- All transactional state, vector search, and full-text search live in Postgres.
- Three containers in dev (Postgres, Redis, object store) — laptop-friendly.
- Schemas inside Postgres act as future service boundaries.

**Triggers for additional components.** Catalog >1M items → OpenSearch. >10M vectors per tenant → Qdrant. ≥3 ML models sharing features → Feast. Multi-TB history → Lakehouse.

**Alternatives considered.** Multiple specialized stores from day one (rejected — premature); single SQLite (rejected — insufficient for multi-tenant prod).

---

## ADR-005 — Garage as the MVP S3-compatible store

**Context.** We need an S3-compatible object store for reports, uploads, and artifacts. Choices include AWS S3 (cloud), MinIO (self-host), and Garage (self-host).

**Decision.** Use **Garage** as the default self-hosted S3-compatible store for dev and on-prem deployments. AWS S3 / Cloudflare R2 are acceptable cloud alternatives behind the same `ObjectStore` interface.

**Consequences.**
- Single Rust binary, ~50 MB RAM idle, easy to deploy.
- Strong fit for future multi-region / on-prem industrial deployments.
- All code talks to it via `boto3` — same code in dev and cloud.

**Alternatives considered.** MinIO (viable, larger community); SeaweedFS (less S3-faithful).

---

## ADR-006 — Agent orchestration with LangGraph + PostgresSaver

**Context.** SmartInv depends on agentic orchestration (Conversational Analyst, Inventory Health, Optimization). We need durable runs without adding Temporal at MVP.

**Decision.** Use **LangGraph** with the **PostgresSaver** checkpointer for agent state. LLM calls go through a **LiteLLM** gateway. Tracing via **Langfuse**.

**Consequences.**
- ~70% of Temporal's durability benefits for agent runs at zero extra infra cost.
- Graph topology is explicit, testable, and observable.
- LiteLLM gives us a single switch to change model vendor without touching agent code.

**Alternatives considered.** OpenAI Agents SDK (viable, more vendor-coupled); CrewAI (rejected for production use — less mature governance); raw chain code (rejected — reinvents orchestration).

---

## ADR-007 — Python FastAPI as the backend stack

**Context.** SmartInv combines transactional services, ML, and agents. Mixing Python and Node would double our SDK surface and CI cost.

**Decision.** Use **Python 3.12 + FastAPI** for all backend services. Start as a **modular monolith**; split when independent scaling forces it.

**Consequences.**
- One language for services, ML pipelines, agents, and connectors.
- Pydantic schemas double as request/response models and feed OpenAPI clients.
- Type hints + mypy + Ruff enforced in CI.

**Alternatives considered.** Node/NestJS for transactional services + Python for ML (rejected — overhead for our team size); Go (rejected — slower ML/agent ecosystem).

---

## ADR-008 — Kanban with 5 statuses for project management

**Context.** Team is small. Process must be light but not absent.

**Decision.** Use **Kanban with 5 columns: Backlog · Doing · Blocked · Review · Done**, with WIP limits, weekly triage, weekly Friday demo, and type-specific Definition of Done.

**Consequences.**
- Tooling: GitHub Projects (or Linear) — board lives in the same place as the code.
- One hour per week of process; rest is work.
- Tasks are sliced **vertically by user journey**, never horizontally by layer.

**Alternatives considered.** Scrum (rejected — too rigid for our size and shape of work); Shape Up cycles (viable later if predictability is demanded by customers).

---

## ADR-009 — MVP scope = four killer capabilities

**Context.** The full feature specification lists eight functional domains and ten non-functional domains. Shipping all of them at MVP is impossible and wrong.

**Decision.** MVP delivers four end-to-end capabilities:
1. **Inventory Health assessment**
2. **AI Min/Max recommendations** with explanation and confidence
3. **Critical Spare and risk dashboard**
4. **Conversational Inventory Analyst** ("Ask SmartInv")

**Consequences.**
- Procurement, Master Data enrichment, full Risk graph analytics, and Narrative Agent are Phase 2.
- One source system integrated end-to-end first (probably IBM Maximo).
- Web-only; mobile deferred.

**Alternatives considered.** Broader MVP (rejected — guaranteed scope creep).

---

## ADR-010 — Vertical task slicing

**Context.** Small teams that slice work horizontally produce nothing demo-able for months and absorb integration costs late.

**Decision.** Every task in the roadmap slices the system **vertically**: a thin path through UI → API → service → DB → tests for a specific user journey on a specific item/plant.

**Consequences.**
- Integration problems surface early, when they are cheap to fix.
- Every Friday demo can show real progress.
- Tasks are smaller, more numerous, and easier to estimate.

**Alternatives considered.** Layer-by-layer construction (rejected — well-known anti-pattern for small teams).

---

## ADR-011 — Definition of Done is type-specific

**Context.** A single Definition of Done across deterministic code, ML models, agents, and UI features lets AI features pass as "done" when they are not.

**Decision.** Each task type has a specific Definition of Done. See [engineering-principles.md §6 PR5](../process/engineering-principles.md#pr5--definition-of-done-is-type-specific).

**Consequences.**
- AI features only ship when their eval suite passes thresholds.
- Models only ship with `model_version` registered and reproducible.
- UI features only ship token-styled and keyboard-accessible.

---

## ADR-012 — Auth0 or Keycloak for identity at MVP

**Context.** SSO, MFA, and SAML are required by industrial buyers.

**Decision.** Use **Auth0** (managed) for hosted-customer deployments and **Keycloak** (self-hosted) for on-prem. The application code only knows OIDC.

**Consequences.**
- Same JWT shape across deployments.
- RBAC via roles claim in JWT; ABAC (OPA) deferred until needed.

**Alternatives considered.** Build our own (rejected — security boundary, not differentiation); Clerk (viable for managed only).

---

## ADR-013 — One source system integrated end-to-end first

**Context.** Trying to integrate Maximo + SAP + Oracle in parallel for the MVP destroys focus and produces shallow integrations.

**Decision.** Integrate **IBM Maximo** end-to-end first. Add SAP and Oracle in subsequent phases, reusing the connector pattern.

**Consequences.**
- Connector contract is real (not hypothetical) by the time the second source lands.
- Maximo is also where most early prospects live, given the team's wedge.

---

## ADR-014 — Eval-driven development for AI features

**Context.** LLM features silently degrade. Without a guardrail, "looks good in the demo" becomes "fine in production" — until it isn't.

**Decision.** Every prompt, agent, or narrative feature ships with an **eval suite** in `tests/evals/`. CI runs the suite. A prompt change that drops the score below threshold cannot merge.

**Consequences.**
- Slower initial prompt iteration.
- A growing, owned asset that protects the trust moat.
- Bug reports become eval cases.

---

## ADR-015 — Tokens-only styling, no hex codes in components

**Context.** Hex codes in components make rebranding, theming, and future cross-platform sharing painful.

**Decision.** All colors, spacing, typography, radii live in `packages/tokens` and are consumed via Tailwind theme. ESLint/Stylelint rule blocks `/^#[0-9a-f]{3,8}$/i` in `apps/web` and `packages/ui-web/src/**`.

**Consequences.**
- One rebrand or dark-mode change is a token update.
- Migration to a shared mobile system reuses tokens directly.

---

## ADR-016 — English is the project language

**Context.** The team and product operate across languages. Code, docs, and tests must remain unambiguously interpretable.

**Decision.** All code, comments, commit messages, ADRs, tests, and documentation are written in **English**, regardless of the language conversations happen in. Exceptions: user-facing content explicitly authored for a localized market.

**Consequences.**
- Onboarding new contributors is friction-free.
- Search and tooling work consistently.

---

> **Adding a new ADR?** Number sequentially, follow the same format, include the trade-off honestly. ADRs are immutable — supersede with a new ADR rather than editing an old one.
