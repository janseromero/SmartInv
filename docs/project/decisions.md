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

> **Adding a new ADR?** Number sequentially, follow the same format, include the trade-off honestly. ADRs are immutable — supersede with a new ADR rather than editing an old one.
