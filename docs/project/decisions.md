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

> **Superseded by [ADR-017](#adr-017--seaweedfs-supersedes-garage-as-the-mvp-object-store).** Retained for history; the active object store is SeaweedFS.

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

## ADR-008 — CV / Epic / Story hierarchy with Kanban at Story level

**Context.** Team is small. We need a strategic structure that scales with the product *and* a light operational discipline for day-to-day work.

**Decision.** Use the **Mirror Mind CV / Epic / Story** hierarchy ([`docs/project/roadmap/index.md`](roadmap/index.md)):
- **CV** (Capability Value) — major delivery stage, user-visible promise, months of work.
- **Epic** — cohesive block of work inside a CV, weeks.
- **Story** — atomic, user-centric delivery, hours to days.

Story-level work uses a **5-column Kanban**: Backlog · Doing · Blocked · Review · Done, with WIP limits, weekly triage, weekly Friday demo, and type-specific Definition of Done.

**Consequences.**
- Strategic doc: `docs/project/roadmap/index.md` + `docs/project/roadmap/cvN-*/index.md`.
- Operational tooling: GitHub Projects (or Linear) — board lives in the same place as the code.
- Epic folders (`cvN-*/cvN-eM-*/`) are created only when work on the epic starts (Mirror's discipline of not over-scaffolding ahead of work).
- One hour per week of process; rest is work.
- Stories are sliced **vertically by user journey**, never horizontally by layer.

**Alternatives considered.** Flat Kanban with no strategic hierarchy (rejected — scales poorly past ~50 stories); Scrum (rejected — too rigid); Shape Up cycles (viable later if predictability is demanded by customers).

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

## ADR-017 — SeaweedFS supersedes Garage as the MVP object store

> **Supersedes [ADR-005](#adr-005--garage-as-the-mvp-s3-compatible-store).**

**Context.** [ADR-005](#adr-005--garage-as-the-mvp-s3-compatible-store) selected Garage as the default S3-compatible store and flagged SeaweedFS as "less S3-faithful." On revisiting the choice for CV1.E4, SeaweedFS was preferred for its single-binary `server` mode (master + volume + filer + S3 in one process), its scale-out volume model, and operational familiarity. The object store is consumed exclusively through a future `ObjectStore` interface backed by `boto3` (path-style addressing), so the application only depends on the S3 API surface, not the engine.

**Decision.** Use **SeaweedFS** as the default self-hosted S3-compatible store for dev and on-prem deployments. AWS S3 / Cloudflare R2 remain acceptable cloud alternatives behind the same `ObjectStore` interface.

**Consequences.**
- Local dev runs SeaweedFS via `docker compose` (`server -s3`), S3 API on `:8333`, credentials in `infra/docker/seaweedfs/s3.json`.
- All code talks to it via `boto3` with **path-style addressing** — the same code targets AWS S3 in cloud.
- **Trade-off (honest):** SeaweedFS's S3 gateway is historically less complete than MinIO's. We mitigate by (a) using only core operations (put/get/list/delete/multipart/presign) and (b) keeping access behind the `ObjectStore` interface so swapping engines is a config change. If an S3 feature gap blocks us, switching to MinIO or AWS S3 is mechanical.

**Triggers to revisit.** A required S3 feature is missing or buggy in SeaweedFS; multi-region replication needs outgrow the single-binary mode; a managed cloud store becomes cheaper to operate than self-hosting.

**Alternatives considered.** Garage ([ADR-005](#adr-005--garage-as-the-mvp-s3-compatible-store), now superseded); MinIO (viable, larger community, AGPL considerations); AWS S3 (cloud-only, not self-host friendly for on-prem industrial customers).

---

## ADR-018 — Langfuse Cloud (free tier) for MVP LLM observability

**Context.** SmartInv's agentic features (CV5) need LLM/agent observability — prompt, tool-call, token-cost, and latency tracing ([Engineering Principles A6/A7](../process/engineering-principles.md#a6--observability-is-a-feature)). Self-hosted Langfuse v3 pulls in its own Postgres + ClickHouse + worker, which is heavy for a laptop and adds operational cost. Critically, **no LLM call exists in the codebase until CV5** — the agent runtime is explicitly out of scope for CV1 ([CV1 Foundations](roadmap/cv1-foundations/index.md)).

**Decision.** Use **Langfuse Cloud (free tier)** for the MVP. There is **no local Langfuse service** in `docker-compose.yml`. CV1.E4 ships only the configuration scaffolding (`LANGFUSE_*` env vars in `config.py` and `.env.example`); the actual SDK wiring lands in **[CV5.E1](roadmap/cv5-conversational-analyst/cv5-e1-llm-gateway-tool-catalog/index.md)** alongside the LLM gateway that produces traces. Self-hosting Langfuse is a Phase 2 concern.

**Consequences.**
- The local stack stays light — three services (Postgres, Redis, SeaweedFS), preserving the "boots in under 30 seconds" target.
- Langfuse keys are read from the SDK's conventional unprefixed `LANGFUSE_*` env vars; real keys live only in the gitignored `.env`, never in `.env.example`.
- Deferring carries **no retrofit cost**: Langfuse is edge observability (a callback in the LLM gateway), so adding it in CV5 is additive, not a rewrite. It is validated against real traces when it arrives — not stood up empty.
- **Trade-off:** trace data lives in Langfuse's cloud during the MVP. Acceptable for pre-pilot development; revisited for customers with data-residency constraints.

**Triggers to revisit.** Data-residency or on-prem requirements from a pilot customer; free-tier limits exceeded; need to retain traces beyond the cloud retention window.

**Alternatives considered.** Self-host Langfuse now (rejected — heavy stack, zero consumers until CV5); OpenTelemetry-only for LLM spans (rejected — loses prompt/cost-native LLM views); defer all observability config to CV5 (rejected — cheap to scaffold the env contract now).

---

## ADR-019 — Persistence stack: SQLAlchemy 2.0 + Alembic + psycopg 3, RLS default-deny

**Context.** CV1.E5 lays the database foundation: eight schemas, ~28 tables, migrations, and tenant isolation. We needed to commit to an ORM, a migration tool, a driver, and a concrete Row-Level Security pattern — consistent with ADR-007 (Python everywhere) and AR3 (tenant_id is first-class).

**Decision.**
- **ORM:** SQLAlchemy 2.0 declarative with `Mapped[...]` typing. (Rejected SQLModel — couples ORM to Pydantic in ways that bite later.)
- **Migrations:** Alembic, autogenerate against the declarative metadata. Schemas and extensions are created in the baseline migration (autogenerate does not manage them). Every up-migration has a down-migration.
- **Driver:** **psycopg 3** as the single driver for the app, Alembic, and dev scripts (sync for the MVP). One driver, less surface.
- **IDs / conventions:** UUID PKs via `gen_random_uuid()` (PG16 core); `tenant_id uuid` on every tenant-scoped table; `timestamptz` created/updated; `bigserial` for append-only event tables; deterministic constraint/index naming for stable autogenerate.
- **RLS:** every tenant-scoped table gets `ENABLE` + `FORCE ROW LEVEL SECURITY` and a `tenant_isolation` policy `USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)` with the same `WITH CHECK`. When the GUC is unset, `current_setting` returns NULL and the predicate denies — **default-deny**.
- **Migrations split:** one baseline migration (schemas + extensions + tables) and a separate RLS migration, so the security-sensitive diff is reviewed in isolation (AGENTS.md slow lane).

**Consequences.**
- `alembic upgrade head` builds the full schema on an empty DB; `downgrade base` removes it cleanly — both verified in CI against a real Postgres (with pgvector).
- **RLS only bites for a non-superuser role.** Postgres superusers (and `BYPASSRLS` roles) ignore RLS even with FORCE. The dev `smartinv` role is a superuser, so it is used for migrations/admin only. The **least-privilege runtime login role** that the API connects with — and the per-request GUC wiring — are delivered in **CV1.E6 (Auth & Tenancy)**. E5 proves the policy semantics by testing against a dedicated non-superuser role.
- The `ml.model_registry` and `agent.tool_catalog` catalogs and `core.tenants`/`core.roles` are platform-level (no `tenant_id`, no RLS).
- LangGraph's checkpoint tables are intentionally not modeled here — the PostgresSaver owns them in CV5.
- Embedding dimension `vector(1536)` is provisional; revisited when CV5 picks the embedding model.

**Alternatives considered.** Raw SQL migrations (rejected — lose autogenerate + model parity); asyncpg + separate sync driver for Alembic (rejected — two drivers); application-only tenancy without RLS (rejected — violates S5 "two layers").

---

## ADR-020 — Tenant-context enforcement: least-privilege role + per-request GUC

**Context.** CV1.E5 added RLS policies, but a critical fact surfaced: **Postgres superusers (and `BYPASSRLS` roles) ignore RLS even with FORCE.** The dev `smartinv` role is a superuser, so RLS never filtered for it. For isolation to be real, the application must connect as a least-privilege role and set the tenant context per request.

**Decision.**
- **Two roles, two URLs.** Migrations/admin use the superuser role (`SMARTINV_ADMIN_DATABASE_URL`); the application runtime connects as **`smartinv_app`** (`NOSUPERUSER NOBYPASSRLS`, `SMARTINV_DATABASE_URL`). The app role is created and granted in a migration; future tables are covered via `ALTER DEFAULT PRIVILEGES`.
- **Per-request GUC.** A request-scoped SQLAlchemy session opens a transaction and runs `SELECT set_config('app.current_tenant_id', :tid, true)` from the authenticated `CurrentUser`. `is_local => true` scopes it to the transaction, so it never leaks across pooled connections; RLS then filters every query.
- **Enforcement, not filtering.** Endpoints do **not** add `WHERE tenant_id = …`; the database enforces isolation. The capstone test proves a tenant cannot see another's rows through a real endpoint that never filters.

**Consequences.**
- Tenant isolation holds even when application code forgets to filter — the moat is structural.
- Dev/CI app-role password is a fixed default; **production manages it out of band** (secret manager + `ALTER ROLE ... PASSWORD`).
- Migrations require the admin URL; the app requires the app URL — both are documented in `.env.example`.

**Alternatives considered.** Single superuser role (rejected — RLS never applies); application-only `WHERE tenant_id` filtering (rejected — one forgotten clause leaks data, violates S5 "two layers"); `SET ROLE` per request instead of a dedicated login role (rejected — more moving parts than a least-privilege connection).

---

## ADR-021 — MVP identity: dev token-issuer behind an OIDC-shaped seam

> Adjusts the wording of [ADR-012](#adr-012--auth0-or-keycloak-for-identity-at-mvp): the real IdP is deferred, but the app still only knows OIDC.

**Context.** Full Auth0/Keycloak integration needs an external account or a heavy self-hosted service, and its login/callback flow is hard to test hermetically in CI. The agent runtime that needs *real* SSO is not the MVP's first blocker; the **tenant-isolation loop** (ADR-020) is. We want to build and prove that loop now without standing up an IdP.

**Decision.**
- Build to **generic OIDC-shaped JWTs**. The IdP lives behind one function, `verify_token(raw) -> CurrentUser`.
- **MVP:** a local **HS256 dev token-issuer** (`mint_dev_token`, `POST /auth/dev-login`, `make token`) signed with `SMARTINV_JWT_SECRET`. Claims mirror a real token: `sub`, `tenant_id`, `roles`, `email`, `iss`, `aud`, `exp`.
- **Roles travel in the JWT `roles` claim** (keeps ADR-012). The `core.roles`/`role_bindings` tables remain the future management surface, not wired now.
- **Web:** a minimal dev sign-in page + token storage + `Authorization` header; protected routes via a client guard. Full Auth.js + TanStack Query deferred.
- **Production swap:** replace HS256+secret with RS256+JWKS inside `verify_token`, and the dev login page with an Auth.js OIDC flow. Nothing downstream changes.

**Consequences.**
- Hermetic, CI-friendly auth; the full tenant-isolation chain (JWT → GUC → RLS → least-privilege role) is provable today.
- **The dev issuer is insecure by design** — anyone with the secret can mint any tenant's token. `dev-login` returns 404 outside `dev`/`test`. **A real IdP must be wired before any customer data lands.**
- Deferred to a follow-up story (CV8 Customer Readiness or an E6 follow-up): real Auth0/Keycloak OIDC, full web Auth.js, optional RBAC-from-DB.

**Alternatives considered.** Auth0 now (rejected — external dependency, CI can't run the flow); Keycloak self-host now (rejected — heavy service for zero current SSO need); no auth until the real IdP (rejected — leaves the RLS loop unproven and every endpoint unguarded).

---

## ADR-022 — Core service contracts: `typing.Protocol` seams + contract-test-against-fakes

**Context.** CV1.E7 defines the four interfaces that keep domain code independent of infrastructure (AR2, ADR-003): `WorkflowEngine`, `ObjectStore`, `LLMGateway`, `SearchIndex`. Two of the four have no live consumer yet (LLMGateway's is CV5, SearchIndex's is CV2), so building full real implementations of those now would be speculative.

**Decision.**
- **Protocols as `typing.Protocol`** (structural, `@runtime_checkable`) in **`api/contracts/`** — a module in the modular monolith, not a separate `packages/` member (AR1; `packages/*` stays TS-only). Value objects are frozen dataclasses.
- **Implementations in `api/infra/`**, wired by a single composition root (`api/infra/providers.py`). Domain code imports only `api.contracts`.
- **Ship real impls where there is an immediate consumer or it is trivially real:** `S3ObjectStore` (boto3/SeaweedFS, ADR-017) and `PostgresWorkflowEngine` (over the E5 `workflow.*` tables).
- **Ship in-memory fakes now, real impls deferred to the owning CV:** `EchoLLMGateway` (real LiteLLM → CV5.E1), `InMemorySearchIndex` (real `pg_trgm` → CV2).
- **Contract tests run each protocol against its implementation(s)** — the real impl *and* an in-memory fake. This pattern *is* the Done Condition's "a second implementation substitutes without code changes."
- **`WorkflowEngine` uses Temporal-shaped verbs** (`start`/`signal`/`query`/`cancel`) so the future Temporal swap stays mechanical (ADR-003). **Sync** for the MVP (matches the psycopg stack); CV5 may give `LLMGateway` an async variant.

**Consequences.**
- All four seams exist today; later CVs depend on abstractions from day one.
- No speculative code: LLMGateway/SearchIndex ship the smallest real-enough thing (a fake) until a caller exists.
- Swapping an implementation (Echo → LiteLLM, in-memory → pg_trgm, Postgres → Temporal) changes only `api/infra` + `providers.py`.
- `boto3` is promoted to an api runtime dependency.

**Alternatives considered.** A separate `packages/contracts` Python package (rejected — premature split for a modular monolith); `abc.ABC` base classes (rejected — inheritance coupling vs structural typing); building all four real impls now (rejected — speculative for LLMGateway/SearchIndex); approval-domain verbs for `WorkflowEngine` (rejected — would make the Temporal swap leak into domain code).

---

## ADR-023 — Component primitives: plain token-styled React (no Radix until needed)

**Context.** CV1.E8 fills `@smartinv/ui-contracts` + `@smartinv/ui-web` with the five shared primitives (`KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter`) and a component explorer. The original plan said "shadcn/ui primitives" and a `@radix-ui` import-ban lint rule — but all five primitives are **presentational**; none need Radix's accessibility machinery (dialogs, menus, selects).

**Decision.**
- **Contracts in `@smartinv/ui-contracts`** (pure TS interfaces); **implementations in `@smartinv/ui-web`** as **plain token-styled React** — no Radix/shadcn. Radix is adopted *inside `ui-web`* only when an interactive, accessibility-critical widget needs it.
- **Explorer: Ladle** (Vite-based, light) rather than Storybook (heavy). Builds to a static site for design review.
- **Snapshot tests with Vitest + @testing-library/react + jsdom**, run in CI via `pnpm test`.
- **Defer the `@radix-ui` import-ban Biome rule** until Radix is actually introduced (it guards code that doesn't exist yet).
- Components use **tokens only** (no raw hex — `pnpm lint:hex`); the consuming app and Ladle both map `@smartinv/tokens` into their Tailwind theme and scan `packages/ui-web/src`.

**Consequences.**
- The five primitives ship with stories + snapshot regression tests; the cross-platform port stays a re-skin (ADR-002).
- No Radix/shadcn weight is paid before a component needs it.
- pnpm 11's build-script approval (`allowBuilds`) and pre-run check (`verifyDepsBeforeRun: false`) are configured in `pnpm-workspace.yaml` so the new dev tooling (Ladle/Vitest/swc) doesn't break CI.

**Alternatives considered.** shadcn/Radix now (rejected — weight without a consumer for presentational primitives); Storybook (rejected — heavier than Ladle for the MVP); skipping the explorer entirely (rejected — the Done Condition wants isolated design review, and Ladle is cheap).

---

## ADR-024 — Source ingestion: connector seam, fixtures-first, secret-manager credentials

**Context.** CV2 needs real inventory data from IBM Maximo (ADR-013), but a real Maximo integration is a hard external dependency (access, auth, OSLC quirks, volume) that would gate every other CV2 epic if built first. We also must decide where source credentials live.

**Decision.**
- **Ingestion is a source-agnostic pipeline behind a `SourceConnector` seam** (`api/ingestion`): a connector yields canonical records per entity in dependency order; an `IngestionService` upserts them idempotently (INSERT … ON CONFLICT on the natural key) with **per-record failure isolation** via SAVEPOINTs (a bad row lands in `sources.error_log`; the rest commit) and per-entity `sources.sync_runs` tracking.
- **Data-first with fixtures (Option B).** Ship a deliberately-messy `FixtureConnector` (missing/duplicate descriptions, null costs, odd UOMs, excess/stockout balances, obsolete items) now, so the catalog, scoring, and dedup epics are built and tested against realistic mess. The real `MaximoConnector` implements the **same seam** later — it is the only remaining piece, bounded to a REST client (auth/paging/retry) + field mapping; everything around it (idempotency, tracking, errors, status, scheduling) is already built.
- **Credentials via secret manager (Pattern A), not a DB form.** `sources.connectors.config` holds **non-secret** config only (endpoint, object structures, schedule). Maximo API keys live in the secret manager / env, never in a plaintext column or a web form. The `/admin/connectors` surface is **read-only status** (connectors + recent runs); self-serve encrypted credential entry (Pattern B) is deferred to multi-tenant onboarding (CV8/CV15).

**Consequences.**
- Visible value (catalog, health, dedup) ships without waiting on Maximo access; integration risk is isolated to one epic.
- The fixture loader is permanent value: test fixtures, demo data, and the scoring eval baseline.
- The natural-key seam from [ADR-019](#adr-019--persistence-stack-sqlalchemy-20--alembic--psycopg-3-rls-default-deny) (`source_system`+`source_id`) makes the live-connector swap mechanical.
- The real Maximo connector and the scheduled (Dramatiq) sync remain to be built before CV2 is fully done.

**Alternatives considered.** Connector-first (rejected — gates all of CV2 on the hardest, most uncertain task); credentials in a DB config form (rejected — plaintext secrets in DB/backups/logs, violates S2/S4); per-record commits instead of savepoints (rejected — weaker atomicity, more round-trips).

---

## ADR-025 — Health scoring: deterministic weighted-penalty engine, versioned

**Context.** CV2.E3 needs a 0–100 inventory health score per item combining excess, slow-moving, obsolete (dead stock), stockout risk, and data-quality flags. It must be **deterministic and reproducible** (no LLM — AGENTS non-negotiable #3; T1 model-deterministic) and it owns the "disposal candidate" definition the UI surfaces.

**Decision.**
- **Pure function** `score_item(ScoreInput) -> ScoreResult` (`api/scoring/engine.py`): no I/O, no clock, no randomness — `days_since_movement` is passed in. Fully unit-tested.
- **Score = `100 − min(1, Σ weightᵢ·severityᵢ) × 100`**, clamped [0,100]. Five dimensions with severities in [0,1] and weights: obsolete 0.6, stockout 0.4, excess 0.3, slow-moving 0.2, dq 0.15.
- **Obsolete (= dead stock / disposal candidate)** = `on_hand > 0` AND no usage in **24 months** (or a retired status). This replaces the provisional 12-month dead-stock proxy from CV2.E2.
- **Versioned** (`SCORE_VERSION = "health-v1"`); registered in `ml.model_registry` (name+version+weights) on every run for reproducibility.
- **Persisted** on `inventory.items` (`health_score`, `health_class`, `score_version`, `score_dimensions` jsonb, `scored_at`). Recompute is **on-demand** (`make score` / `POST /admin/score`); a nightly Dramatiq schedule is deferred (no worker yet).
- Classification (for the portfolio donut): `obsolete_risk` → `excess_slow` → `dq_risk` → `healthy`.

**Consequences.**
- The same inputs + version always yield the same score; a recommendation can be reproduced months later.
- The catalog now exposes `health_score`, badges, a Health filter, a portfolio donut, and the Dead-stock KPI (value + disposal-candidate count) — all from one rule, no competing "obsolete" definitions.
- Weights/thresholds are explicit constants, easy to tune; a tuning change is a new `score_version`.
- Full risk score (operational impact, CV4) and the full DQ score (CV7) are separate — E3 carries only a lightweight DQ *flag* dimension.

**Alternatives considered.** LLM-assisted scoring (forbidden — non-negotiable #3); computing on read instead of persisting (rejected — not reproducible, slow for filters/donut); a single hard-coded threshold per dimension without weights (rejected — no graceful severity blending).

---

## ADR-026 — Duplicate detection: deterministic blocked-similarity engine, versioned (embeddings/classifier deferred)

**Context.** CV2.E4 needs an item-master duplicate-detection queue with confidence-scored pairs that a planner can review and merge. The epic's original sketch (`cv2-e4` index) prescribed sentence-transformer embeddings in `rag.chunks` plus a gradient-boosting pair classifier. Two facts argue against building that now: (1) the `rag.chunks` embedding dimension is explicitly *provisional until CV5 picks the embedding model* (`api/db/models/rag.py`), so building dedup on embeddings hard-commits that choice prematurely; (2) MPN/description NLP enrichment is **CV7's** scope (CV2 out-of-scope list), so manufacturer part numbers are not yet available in the item master. A heavy ML dependency is also an architecture choice requiring review (AGENTS "slow lane"). The Done Condition only requires ≥ 0.85 average confidence for "probable" pairs, reviewable, with the producing model versioned — all achievable deterministically.

**Decision.**
- **Pure functions** in `api/dedup/engine.py`: `normalize` (lowercase, strip punctuation, drop stopwords, sorted token set), `blocking_key`, and `score_pair`. No I/O, no clock, no randomness — fully unit-tested (model-deterministic, T1).
- **Blocking (S2):** `(item_type, uom, block-prefix)` caps the O(n²) comparison to within-block pairs. The block-prefix prefers a manufacturer-part prefix when present but falls back to the first 4 chars of the alphabetically-first description token — *never* the item number, since true duplicates carry different item numbers. Blocks larger than 400 are skipped (too-coarse key).
- **Pair confidence** = weighted mean of five similarity features: description token-set (Jaccard) 0.70, manufacturer-part match 0.10 (bonus; 0 until CV7 extracts MPNs), UoM 0.08, item-type 0.07, unit-cost proximity 0.05. The description dominates because it is the only signal reliably present in raw item masters.
- **Bands:** `confidence ≥ 0.85` → `probable`; `[0.60, 0.85)` → `possible`; below → dropped. Because blocking already forces equal item-type + UoM, a perfect description match reaches exactly the 0.85 "probable" bar.
- **Versioned** (`DEDUP_VERSION = "dedup-v1"`); registered in `ml.model_registry` (name+version+weights) on every run.
- **Persisted** in a new tenant-scoped, RLS-protected `ml.duplicate_candidates` table (canonical ordering `item_a_id < item_b_id`, `confidence`, `band`, `features` jsonb, `model_version`, `status`). Recompute is **on-demand** (`make dedup` / `POST /admin/dedup`); a nightly Dramatiq schedule is deferred (mirrors ADR-025). Re-runs preserve a planner's decision (only still-`open` pairs are refreshed).
- **Merge is a proposal, never a mutation (S6).** A "merge" verdict records the candidate status and emits an `ml.recommendations` envelope (`type='item_merge'`, `status='proposed'`, `approval_path='cv6_workflow'`) carrying claim, evidence, confidence, and model_version. The actual merge is performed by the deterministic CV6 workflow once it exists (non-negotiable #2 — engines propose, workflow disposes).

**Consequences.**
- The whole queue (engine → schema → service → API → UI) ships with no ML dependency and no premature embedding-model commitment; the embedding + classifier variant becomes a drop-in `dedup-v2` behind the same model-registry seam once CV5 fixes the embedding model.
- Synthetic CV2.E1 fixtures draw from a fixed 10-description pool, so detected pairs cluster at the extremes (identical description → ~0.85–0.90, unrelated → dropped) and the `possible` band is sparsely populated. This is a fixture-data characteristic, not an engine limit; realistic near-duplicates (typos, word order, abbreviations) arrive with the live Maximo connector or a future fixture enrichment.
- AI-produced content is violet-marked in the queue (non-negotiable #8): the model badge, confidence figure, and feature-contribution bars use the `ai` accent; status bands keep ok/warn/crit.

**Alternatives considered.** Sentence-transformer embeddings + gradient-boosting classifier now (deferred — premature embedding commitment, dependency weight, MPN not yet available); blocking on item-number prefix (rejected — duplicates have different item numbers, so pairs would never co-locate); direct DB merge on planner action (forbidden — non-negotiable #2); computing pairs on read (rejected — O(n²), not reviewable/auditable).

---

## ADR-027 — Anomaly detection: deterministic robust-z / SPC detectors, versioned (Isolation Forest deferred)

**Context.** CV2.E5 surfaces unusual events for planner review: consumption spikes, unit-price jumps, and negative available balances, flagged within 24h with a likely-cause annotation and drill-down to the source record. The epic sketch named Isolation Forest for volume anomalies. As in ADR-025/026, an ML model is the wrong default here: Isolation Forest adds an sklearn dependency and is not cleanly reproducible (random sampling/seeds), while the Done Condition needs none of it. Two data realities also shaped the design: (1) the synthetic CV2.E1 fixtures originally carried no anomalies (transaction `unit_cost` was always null, balances never went negative, consumption was uniform noise spread over two years), so the feature was undemonstrable and untestable; (2) a naive robust-z over-flags very tight series — a 7% price wiggle or a 1.5x usage is genuinely 3.5σ when the baseline dispersion is tiny.

**Decision.**
- **Pure detectors** in `api/anomaly/engine.py`, no I/O / clock / randomness, fully unit-tested (model-deterministic, T1):
  - **Consumption spike (S1):** per-item **robust z-score** on issue quantities — `z = (qty − median) / (1.4826 · MAD)`, with a std-dev fallback when MAD collapses. Requires ≥ 5 history; only upward.
  - **Price jump (S2):** the same robust z on the per-item unit-price series (SPC control limits), flagging deviations in either direction.
  - **Negative balance (S3):** a pure rule — `available < 0` or `reserved > on_hand`.
- **Practical-significance floor.** A flag must be statistically unusual **and** materially large: consumption ≥ 3x median; price outside [0.5x, 2x] median. This is what separates a real spike from quiet-series noise and mirrors how production SPC alerting works. (Tuning these dropped the synthetic dataset from 249 noisy flags to 139 that map exactly to the injected cohorts.)
- **Versioned** (`ANOMALY_VERSION = "anomaly-v1"`), registered in `ml.model_registry` (name+version+params).
- **Persisted** in a new tenant-scoped, RLS-protected `ml.anomalies` table (`type`, `target_type`/`target_id`, `source_record_id` for drill-down, `score`, `severity`, `detected_for`, `evidence` jsonb with the likely-cause, `model_version`, `status`). Natural key `(tenant, type, target_id)` keeps re-runs idempotent; re-runs preserve a planner's `acknowledged`/`dismissed` decision. An anomaly is an **observation**, not a recommendation — it deliberately does *not* use the `ml.recommendations` envelope.
- **On-demand** recompute (`make anomalies` / `POST /admin/anomalies`); the "within 24 hours" SLA is met by a **nightly Dramatiq run**, which stays **deferred** (no worker yet, mirrors ADR-025/026). The "last 7 days" panel filters on `detected_for`.
- **Fixtures enriched (accepted scope).** CV2.E1 fixtures now give each item a characteristic usage rate and price (so normal variation is tight and a real spike stands out) and inject seeded, recent anomalies of all three kinds. The change is additive (more transactions, edited balance values) and preserves the count-pinned ingestion tests.

**Consequences.**
- The whole panel (engine → schema → service → API → UI) ships with no ML dependency; an Isolation Forest / forecast-residual detector can later slot in as `anomaly-v2` behind the same registry seam if precision/recall demands it.
- The detectors are honest about MRO reality: price history’s real source is procurement (CV9); E5 runs against fixture-injected transaction prices as the MVP source.
- AI-produced content is violet-marked in the panel (non-negotiable #8): the model badge and score use the `ai` accent; warn/crit severities keep status colors.

**Alternatives considered.** Isolation Forest now (deferred — dependency weight, non-reproducible, unnecessary for the Done Condition); z-score without a practical-significance floor (rejected — floods the queue on tight series); raising the z-threshold instead of a ratio floor (rejected — real injected anomalies are z≫10, so a higher threshold only trims the false-positive band arbitrarily); storing anomalies as recommendations (rejected — an anomaly is an observation, not a proposed action); leaving fixtures empty and shipping detectors against no data (rejected — untestable, undemonstrable).

---

## ADR-028 — Explainable recommendations: deterministic Croston/TSB forecast + closed-form optimization, versioned (LightGBM/Pyomo deferred)

**Context.** CV3 is the second killer capability — explainable min/max & reorder recommendations, each carrying its full envelope (claim, evidence, confidence, assumptions, model_version, approval_path). The roadmap sketched a heavy ML/OR stack: LightGBM forecasting, Pyomo/OR-Tools optimization, a cross-site transfer LP. Two of the architecture's own non-negotiables already constrain this: **#1 agents propose, deterministic code disposes** and **#3 no LLM-generated numbers**. As with CV2 (ADR-025/026/027), the heavy libraries add weight and reproducibility risk without being required to satisfy the Done Conditions — and forecasting/optimization for MRO is well-served by classical, fully explainable methods.

**Decision (one ADR for the whole CV3 chain E1–E5).**
- **E1 Forecasting** — deterministic **Croston / TSB** intermittent-demand baselines (`forecast-croston-v1`) in `api/forecast/`. Demand is bucketed into ~monthly periods; TSB is chosen when trailing zeros signal obsolescence, Croston for dense-intermittent, a naive mean otherwise. P50/P80/P95 bands come from the historical coefficient of variation. Persisted in `ml.predictions` with `model_version` + an input fingerprint (reproducibility, D2). **LightGBM deferred** to `forecast-v2`; deep forecasting is CV14.
- **E2 Optimization** — **closed-form inventory theory** (`optimize-eoq-v1`) in `api/optimize/`: safety stock = z·σ_LT, reorder point = lead-time demand + safety stock, EOQ for the order quantity, min/max from those. Stockout probability is estimated by a **seeded Monte-Carlo** (reproducible from `MONTE_CARLO_SEED`) and cross-checked against the analytical service level; the cost↔risk **Pareto frontier** is computed analytically across service levels. **Pyomo/OR-Tools and the cross-site transfer LP deferred** (CV14 / a later slice).
- **E3 Envelope** — reuses the existing `ml.recommendations` table; every recommendation persists the full envelope and is **append-only** (a re-run replaces only still-`proposed` rows; accepted/overridden envelopes are immutable history). `approval_path='cv6_workflow'`; accepting never writes to a source system (#2).
- **E4 UI** — the Optimization Recommendations screen: cards with the shared `EvidenceStrip` (min/max, stockout, lead time, confidence, model version), Accept / Override, a Pareto scatter, and a portfolio capital-impact summary. Accept routes to approval; AI content is violet-marked (#8).
- **E5 Override & feedback** — `ml.recommendation_feedback` captures accept/adjust/override with a typed reason taxonomy; repeated overrides on the same item axis accumulate into an `ml.regime_signals` row (regime-change candidate); an acceptance-rate-per-model endpoint feeds the quality dashboard. Not an autonomous learning loop.
- **New domain column** `inventory.items.lead_time_days` (CV3 owns replenishment lead time; fixtures seed it). Forecasting/optimization run **on-demand** (`make forecast` / `make optimize`, `POST /admin/forecast` / `/admin/optimize`); nightly schedule deferred (mirrors CV2).

**Consequences.**
- The whole CV3 capability ships with **no ML/OR dependency** and is fully reproducible — same inputs + same versions reproduce every forecast and recommendation; both model families are registered in `ml.model_registry`. LightGBM (`forecast-v2`) and Pyomo (`optimize-v2`) slot in behind the same seams when accuracy demands it.
- Every recommendation is explainable end-to-end: the claim cites the stockout delta, the evidence carries the Monte-Carlo result and Pareto frontier, the assumptions pin the service level / seed / model versions. No recommendation can exist without its envelope (#4).
- The optimizer runs on **forecast output**, not raw history — E1 → E2 → E3 → E4 → E5 is a strict pipeline; the optimizer skips items with no demand signal.

**Alternatives considered.** LightGBM / Pyomo / OR-Tools now (deferred — dependency weight, reproducibility risk, unnecessary for the Done Condition); LLM-generated or LLM-edited numbers (forbidden — #1/#3); a separate recommendations table (rejected — the envelope table already exists and is the #4 backbone); mutating envelopes in place on accept/override (rejected — envelopes are immutable history; status transitions + a feedback row capture the decision); deriving regime signals on read only (rejected — the Done Condition asks for a regime-change *record*).

---

## ADR-029 — Operational risk: deterministic likelihood×consequence score + rule-based critical-spare, versioned (GNN/GBM deferred)

**Context.** CV4 surfaces *operational risk* — where missing parts hurt, in dollars — and triggers mitigations. The roadmap already calls for deterministic risk at MVP (GNN deferred to CV14); E2.S2 additionally sketched a gradient-boosted critical-spare classifier. As in ADR-025–028, ML is the wrong default here, and there is a sharper reason than usual: the genuinely ML-worthy task (learning *unlabeled* criticals) **needs labels we do not have** — synthetic fixtures can't supply them, so a classifier now would be theatre. The harder problem is that the risk inputs themselves (item criticality, supplier reliability, lead-time volatility) did not exist in the schema.

**Decision.**
- **Deterministic score** (`risk-v1`) in `api/risk/`: **risk = likelihood × consequence**. Likelihood is a weighted supply-side severity (stockout cover 0.55, lead time 0.20, supplier unreliability 0.25); consequence is a criticality ramp with a floor (`0.3 + 0.7·(crit−1)/4`). The result is **risk-weighted exposure on a 0–100 scale** — a well-stocked portfolio clusters low *by construction*, so the class bands (critical ≥ 45, high ≥ 25, moderate ≥ 12) are absolute exposure cutoffs, not a uniform split. Pure, fully unit-tested.
- **Dollar exposure** = downtime-cost/day (escalating by criticality, a documented assumption) × lead time × stockout severity — the figure the dashboard leads with.
- **Critical-spare flag is rule-based (E2.S1):** criticality ≥ 4, or a single-source mid-criticality item at stockout risk, each with a human-readable reason. **The GBM classifier (E2.S2) is deferred** to `critical-v2` and explicitly gated on a *labeled pilot dataset*; the asset-graph rollup (E1.S3) is deferred to the CV14 graph work.
- **Schema/fixtures enriched (accepted scope, like CV2.E5):** `inventory.items.criticality` + `primary_supplier_id`, `inventory.suppliers.on_time_rate`, plus the risk columns on items (`risk_score`, `risk_class`, `risk_version`, `risk_breakdown`, `is_critical_spare`, `critical_reason`). Fixtures seed criticality (skewed low), a primary supplier, and per-supplier reliability. The change is additive and preserves the count-pinned ingestion tests.
- **Risk consumes CV3 (E1 Done Condition):** the score reads the CV3 forecast (`demand_rate`) and reorder point, so risk is grounded in the same governed numbers; the `/risk` list ranks by score.
- **Mitigation routes to the approval seam (E4):** "Mitigate" reuses the item's CV3 reorder policy to stage a `risk_mitigation` recommendation envelope (`approval_path='cv6_workflow'`, status `proposed`) — never a direct write (#2), identical to CV3 accept / CV2.E4 merge.
- **Narratives are templated, grounded text (E3.S5/E4.S5):** no LLM, no invented numbers; the CV5 grounding pattern replaces them later.

**Consequences.**
- CV4 ships with no ML/graph dependency, reproducible and versioned in `ml.model_registry`. The GNN (`risk-v2`, CV14) and the GBM critical-spare classifier (`critical-v2`) slot in behind the same seam — the classifier only once a pilot provides labeled criticality.
- Every figure is explainable: the breakdown shows the stockout/lead-time/supplier severities, the exposure cites the downtime-cost assumption, the narrative restates them verbatim.
- The bands are honest about a well-stocked portfolio — "critical" means genuinely exposed (high criticality + actual stockout risk), not merely high-criticality.

**Alternatives considered.** GNN / gradient-boosted classifier now (deferred — no labels, dependency weight, reproducibility); additive weighted sum instead of likelihood×consequence (rejected — it lets a well-stocked critical item score high, which is operationally wrong); uniform 0–100 bands (rejected — the score is risk-weighted exposure and is low by construction for a healthy portfolio); LLM risk narratives (deferred to CV5 — #3); executing mitigation directly (forbidden — #2).

---

## ADR-030 — Configurable approval paths with role-or-user reviewers

**Context.** CV6 turns recommendation envelopes from CV3/CV4 into governed approvals. A hard-coded path (`planner → manager → finance`) would satisfy the first demo but would fail real industrial workflows, where some actions need only planner approval, critical-spare actions need manager review, high-value actions need finance, and some customers assign approvals to named users rather than roles. The engine also needs reproducibility: an approval already in flight must not change shape if policy changes later.

**Decision.** Store a concrete, ordered `approval_path` on each `workflow.approvals` row at workflow start. Each step has `state`, `reviewer_type`, and `reviewer`. `reviewer_type` supports **Option B**: `role` or `user`. The workflow starts at `agent_proposed`; `submit` moves to the first configured reviewer step; `approve` advances through the stored path and then to `approved`; `reject` / `cancelled` moves to `rejected`. Every transition writes an append-only `workflow.approval_events` row with `from_state`, `to_state`, actor, payload, and an idempotency key.

**Consequences.**
- The engine is no longer coupled to one approval chain; the UI can later offer reviewer selection without redesigning the workflow table.
- In-flight approvals are reproducible because the chosen path is persisted, not re-resolved on every action.
- Idempotency keys make retries safe and prevent duplicate transition events.
- Policy resolution (`workflow type × value × criticality → required approvers`) is implemented as tenant-scoped `workflow.approval_policies`; it produces the path that the engine persists and executes.

**Alternatives considered.** Hard-coded planner/manager/finance path (rejected — too rigid for real customers); role-only reviewers (rejected — faster, but forces redesign when named approvers are needed); resolving policy on every transition (rejected — policy edits could rewrite an in-flight approval's required path).

## ADR-031 — Source-system write dispatch behind a `SourceWriter` seam (Echo first)

**Context.** CV6.E4 is the single gate through which an approved SmartInv action reaches a customer's ERP/EAM (AGENTS non-negotiable #2). The roadmap sketched a Dramatiq worker pool delivering to a real Maximo write client. But the live Maximo write client depends on the real `MaximoConnector` (CV2.E1.S10), which is still backlog — and writes to source systems are irreversible at the customer (AGENTS slow lane). Building the whole epic against a hard external dependency would block the durable parts (queue, idempotency, retries, dead-letter, receipts) on the least-certain part.

**Decision.** Implement the dispatch spine behind a `SourceWriter` seam, mirroring the fixtures-first connector pattern ([ADR-024](#adr-024--source-ingestion-connector-seam-fixtures-first-secret-manager-credentials)):
- A tenant-scoped, RLS-protected `workflow.source_writes` queue row is staged when an approval reaches `approved` (idempotency key `recwrite:{recommendation_id}` — a repeated approval cannot duplicate a write).
- `process_pending` delivers each write through the `SourceWriter`, bounded by `max_attempts`; a retryable failure stays `pending`, a permanent/exhausted failure becomes `dead_letter` and emits a `dispatch.incident` audit event (CV6.E3).
- A successful write persists a delivery receipt on the row and marks the originating recommendation `delivered`.
- The MVP `SourceWriter` is `EchoSourceWriter` — deterministic external id, no external call — so idempotency and the failure path are provable today. The dispatcher is synchronous and idempotent, so a Dramatiq worker later simply calls `process_pending`; today it runs via `make dispatch` / `POST /admin/dispatch`.

**Consequences.**
- The whole CV6.E4 mechanism (queue, idempotency, retry/backoff, dead-letter, receipts, incidents) ships and is tested without a live source system; the only deferred piece is `MaximoSourceWriter` (CV6.E4.S2), gated on CV2.E1.S10. Swapping it changes only `api/infra/providers.py`.
- No agent or endpoint writes to a source system directly — every write flows through the dispatch service after approval.
- **Trade-off:** the MVP “delivers” to an echo sink, so end-to-end delivery to Maximo is not yet exercised against a real system; that validation arrives with the live client.

**Alternatives considered.** Build the real Maximo write client now (rejected — blocked on CV2.E1.S10, irreversible at the customer); stand up Dramatiq broker wiring now (deferred — the sync dispatcher is idempotent and the worker is a thin wrapper, so the broker earns its cost only when async delivery is needed); write directly from the approval endpoint (forbidden — non-negotiable #2).

---

## ADR-032 — CV5 conversational analyst: LiteLLM SDK in-process, linear orchestrator, LangGraph/PostgresSaver deferred

**Context.** CV5 ships the governed conversational analyst ("Ask SmartInv"). [ADR-006](#adr-006--agent-orchestration-with-langgraph--postgressaver) chose LangGraph + PostgresSaver + a LiteLLM gateway; the CV5.E1 plan additionally speced LiteLLM as a **proxy container**. Building slice 1 (one thin governed path end to end) surfaced that two of those choices buy nothing yet while adding real cost.

**Decision.**
- **LiteLLM Python SDK in-process** behind the existing `LLMGateway` contract — not a proxy container. A proxy earns its keep for multi-service/multi-team key management, which the modular monolith does not have. Vendor choice stays a config swap (`llm_model`); default `gpt-4o-mini`, `claude-3-5-haiku` as an alternate target.
- **In-process `/agents` router** in the monolith rather than a separate `agent` service (same split-later posture as every other module).
- **Linear Python orchestrator** (plan → execute tools → compose → validate → finalize) instead of LangGraph. With no branching and no durable checkpointing at MVP, a graph engine is ceremony.
- **PostgresSaver checkpointing deferred**, not removed. Conversations/runs/events are still persisted for history and audit; durable crash-resume activates when a query becomes long-running/multi-step. This consciously defers the CV5.E2 done-condition guarantee ("a crashed orchestrator resumes from checkpoint") — recorded here rather than dropped silently.
- **The grounding validator is the hard MVP guarantee** ([ADR-014](#adr-014--eval-driven-development-for-ai-features)): a deterministic check that every numeric claim in an answer traces to a tool output; the orchestrator **fails closed** (never ships untraceable numbers). It is unit-tested on every PR, independent of any live model.

**Consequences.**
- Slice 1 adds only the `litellm` dependency (lazily imported), no new container or service.
- The `LLMGateway` seam is unchanged, so swapping to the proxy or to LangGraph later is localized.
- The analyst endpoint `503`s until `OPENAI_API_KEY` is configured; tests inject a deterministic stub planner/composer so the governed path runs in CI without a vendor.
- **Trade-off:** no durable resume yet (acceptable for sub-6s read-only queries); LangGraph adoption is postponed until the graph actually branches (full CV5.E2 / CV11).

**Alternatives considered.** LiteLLM proxy container now (rejected — ops weight, zero MVP benefit); LangGraph + PostgresSaver now (deferred — no branching/durability need yet); separate `agent` service (deferred — premature split); enforce grounding in the prompt only (rejected — non-negotiable trust is enforced in code, not prose).

---

> **Adding a new ADR?** Number sequentially, follow the same format, include the trade-off honestly. ADRs are immutable — supersede with a new ADR rather than editing an old one.
