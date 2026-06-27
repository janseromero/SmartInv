# SmartInv — MVP Software Architecture

> This is the **ship-first architecture** for the SmartInv MVP. It deliberately omits components from the full architecture that don't yet earn their operational cost.
>
> The full reference is [Full Software Architecture](full-architecture.md).
>
> The principle is **Option B**: start without a shared design system, but with the *discipline* (tokens + component contracts) that makes adopting one later cheap.

---

## 1. MVP scope

The MVP delivers **four killer capabilities** end-to-end, web-only:

1. **Inventory Health assessment** (excess, obsolete, duplicate, missing data, stockout risk)
2. **AI Min/Max and reorder recommendations** with explanation and confidence
3. **Critical Spare and risk dashboard**
4. **Conversational Inventory Analyst** ("Ask SmartInv")

Each is backed by **explainable AI, governed agents, and a human-approval workflow**.

---

## 2. MVP stack at a glance

```
┌─────────────────────────────────────────────────────────────┐
│  WEB CLIENT                                                 │
│  Next.js 14 (App Router) + Tailwind + shadcn/ui             │
│  TanStack Query + Zustand + React Hook Form + Zod           │
│  Visx for charts · SSE for chat · WebSocket for traces      │
│  Design tokens in packages/tokens + component contracts     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  BFF / API GATEWAY                                          │
│  tRPC + REST/OpenAPI (FastAPI) + SSE                        │
│  Auth: Auth0 or Keycloak (SSO, OIDC, MFA)                   │
│  AuthZ: simple RBAC + Postgres Row-Level Security           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN SERVICES (Python FastAPI, modular monolith)         │
│  inventory · forecast · optimization · risk · masterdata    │
│  workflow · narrative · audit                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT ORCHESTRATION (FastAPI service)                      │
│  LangGraph + PostgresSaver checkpointer                     │
│  LiteLLM gateway · Langfuse traces                          │
│  3 agents + 1 orchestrator                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  DATA PLATFORM (3 components)                               │
│  PostgreSQL 16 (+ pgvector + pg_trgm + RLS)                 │
│  Redis (cache + Dramatiq broker + rate limit)               │
│  SeaweedFS / S3 (reports, uploads, artifacts)               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PLATFORM & OPS                                             │
│  Docker Compose (dev) → single VM / small K8s (prod)        │
│  GitHub Actions CI · OpenTelemetry + Grafana Cloud          │
│  Sentry for errors                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Frontend (web-only, mobile-ready)

| Layer | Choice | Why for MVP |
|---|---|---|
| Framework | **Next.js 14** (App Router, RSC) | Mature, fast, great DX |
| Styling | **Tailwind CSS** + **shadcn/ui** (Radix-based) | Tokens map 1:1 to NativeWind later |
| Tokens | `packages/tokens` (TS) — source of truth | Mobile re-skin later = swap implementation, not values |
| Component contracts | `packages/ui-contracts` | Interfaces decoupled from rendering — portable to RN |
| Web primitives | `packages/ui-web` (shadcn/ui copied in) | You own the components |
| State | **TanStack Query** + **Zustand** | Identical API on RN |
| Forms | **React Hook Form** + **Zod** | Schema reuse with FastAPI/Pydantic |
| Charts | **Visx** (custom — heatmap, Pareto) + **Recharts** (simple) | Both have RN siblings |
| Realtime | SSE for streaming chat, WebSocket for agent traces and notifications | Native browser APIs |
| Icons | **lucide-react** | Has `lucide-react-native` sibling |

**Rule of MVP UI:** no raw hex codes in components — only token classes (`bg-teal`, `text-ink2`, `bg-aiSoft`).

---

## 4. BFF / API contract

| Concern | Choice |
|---|---|
| Internal calls (web ↔ BFF) | **tRPC** |
| External / partner | **REST + OpenAPI 3.1** (auto-generated from FastAPI) |
| Auth | **Auth0** (managed) or **Keycloak** (self-host) — SSO, OIDC, MFA |
| AuthZ | Simple RBAC (roles in JWT) + Postgres RLS as second line — defer OPA |
| Realtime | SSE for chat; WebSocket for agent traces and notifications |
| Rate limiting | Redis-backed counters |

---

## 5. Backend services (single Python codebase, modular monolith)

For MVP, start as **one FastAPI app with internal modules**, deployed as a few processes. Same code, different entrypoints — services can be split out later when scaling forces it.

| Module | Responsibility |
|---|---|
| `identity` | Auth, tenants, roles, RLS context |
| `inventory` | Items, balances, transactions, health scoring |
| `forecast` | Probabilistic demand forecasting |
| `optimization` | Min/max, safety stock, transfers |
| `risk` | Stockout risk, criticality, downtime exposure |
| `masterdata` | Duplicate detection, NLP normalization |
| `narrative` | LLM-grounded executive narratives |
| `workflow` | Approval state machine (Postgres-backed) |
| `audit` | Append-only audit events |
| `agent_orchestrator` | LangGraph runtime + tool catalog |

**Deployable processes:**

1. `api` — FastAPI HTTP server
2. `worker` — Dramatiq workers for async jobs
3. `agent` — orchestrator HTTP service with LangGraph
4. `connectors` — one worker per source system

---

## 6. Agent orchestration (no Temporal in MVP)

This is the core of SmartInv. See deeper detail below.

| Concern | Choice |
|---|---|
| Framework | **LangGraph** with `PostgresSaver` checkpointer |
| LLM gateway | **LiteLLM** — single entrypoint to OpenAI / Anthropic / Azure / Bedrock |
| Vector store | **pgvector** in the main Postgres |
| Tracing | **Langfuse Cloud** (free tier at MVP; self-host deferred to Phase 2 — [ADR-018](../project/decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability)) |
| Guardrails | Schema validation (Pydantic) + grounding check in code |

### Agents at MVP (3 + 1)

| Agent | Role |
|---|---|
| **Orchestrator** | Intent classification + routing |
| **Conversational Analyst** | Powers "Ask SmartInv" — supervisor that calls tools and other agents |
| **Inventory Health Agent** | Backs Inventory Health screen (excess, dead stock, duplicates) |
| **Optimization Agent** | Backs min/max recommendations |

Deferred to Phase 2: Risk Agent (starts as deterministic scoring), Procurement Agent, Master Data Agent (LLM enrichment), Narrative Agent, Action Agent (covered by Workflow service).

### Execution model

- **Sync streaming (SSE)** for chat
- **Async via Dramatiq + Redis** for long-running runs (portfolio scans, batch optimization)

Same LangGraph graph runs in both modes. PostgresSaver allows runs to resume after process restarts — recovering ~70% of Temporal's value at zero operational cost.

---

## 7. Data platform — 3 components

| Component | Role |
|---|---|
| **PostgreSQL 16** with `pgvector`, `pg_trgm`, `tsvector`, RLS | Holds 95% of state: items, balances, transactions, recommendations, agent runs, RAG memory, audit |
| **Redis** | Dramatiq broker, sessions, hot KPI cache, rate limits |
| **SeaweedFS** (or AWS S3 / R2) | Reports, uploads, model artifacts, exports, backups ([ADR-017](../project/decisions.md#adr-017--seaweedfs-supersedes-garage-as-the-mvp-object-store)) |

### Postgres schema layout

```sql
core.tenants, core.users, core.roles
inventory.items, inventory.balances, inventory.transactions
inventory.assets, inventory.locations, inventory.work_orders
inventory.purchase_orders, inventory.suppliers
sources.connectors, sources.sync_runs, sources.error_log
ml.model_registry, ml.predictions, ml.recommendations
agent.conversations, agent.runs, agent.events, agent.tool_catalog
-- agent.checkpoints owned by LangGraph PostgresSaver (CV5)
workflow.approvals, workflow.approval_events, workflow.approval_policies, workflow.source_writes
rag.documents, rag.chunks
audit.events
```

### Deferred until they earn it

| Component | Add when… |
|---|---|
| OpenSearch / Meilisearch | Item catalog >1M rows and pg_trgm slows down |
| TimescaleDB | Per-minute KPI history with high cardinality |
| Qdrant / Weaviate | pgvector becomes a bottleneck (>10M vectors per tenant) |
| Lakehouse (Delta / Iceberg) | Multi-TB history or BI/DS teams need direct access |
| Feast | ≥3 ML models share features |
| MLflow | Multiple training pipelines per week / A/B tests |
| BentoML | A model outgrows a sidecar FastAPI service |
| Temporal | Workflows span days, need timers, or compensation |
| Kafka | Event volume / multi-consumer fan-out becomes painful |

---

## 8. Workflow & approvals — Postgres state machine

No Temporal at MVP. Use a Postgres-backed state machine:

```sql
create table workflow.approvals (
  id                     uuid primary key,
  tenant_id              uuid not null,
  type                   text not null,     -- 'min_max_change', 'transfer', ...
  payload                jsonb not null,
  state                  text not null,     -- 'agent_proposed' | reviewer step | 'approved' | 'rejected'
  approval_path          jsonb not null,    -- ordered [{state, reviewer_type: role|user, reviewer}]
  current_step_index     integer not null,
  current_reviewer_type  text,              -- 'role' | 'user'
  current_reviewer       text,
  current_actor          text,
  created_at             timestamptz default now(),
  updated_at             timestamptz default now()
);

create table workflow.approval_events (
  id               bigserial primary key,
  tenant_id        uuid not null,
  approval_id      uuid references workflow.approvals(id),
  actor            text,
  event            text,                    -- 'submit', 'approve', 'reject', 'cancelled'
  idempotency_key  text,
  from_state       text,
  to_state         text,
  payload          jsonb,
  created_at       timestamptz default now(),
  unique (tenant_id, approval_id, idempotency_key)
);

create table workflow.approval_policies (
  id                uuid primary key,
  tenant_id         uuid not null,
  workflow_type     text not null,
  min_value         numeric(14,2),
  max_value         numeric(14,2),
  min_criticality   smallint,
  required_path     jsonb not null,          -- ordered [{state, reviewer_type: role|user, reviewer}]
  priority          integer not null,
  status            text not null
);
```

A small service exposes:

- `POST /approvals` — agent submits an envelope
- `POST /approvals/:id/transition` — moves through the state machine
- `GET  /approvals?actor=…` — drives the "My queue" list

Background dispatch (write to Maximo, send notification) runs via **Dramatiq + Redis**.

Wrap behind a `WorkflowEngine` interface so swapping in Temporal later is mechanical.

---

## 9. Integration (one source at a time)

For MVP, integrate **one** source end-to-end first — most likely **IBM Maximo** (the strongest customer wedge).

| Concern | Choice |
|---|---|
| Connector | Custom Python worker (FastAPI background process) |
| Maximo APIs | MIF REST + Object Structures + webhook for events |
| Pattern | Pull master data on schedule; subscribe to deltas via webhook; persist into `inventory.*` tables |
| Idempotency | Source-system IDs as natural keys; upsert with conflict resolution |

When a second source is needed (SAP, Oracle), add a second worker — same shape.

---

## 10. Security & governance (MVP-appropriate)

| Control | MVP implementation |
|---|---|
| AuthN | Auth0 or Keycloak — SSO, OIDC, MFA |
| AuthZ | RBAC in JWT + Postgres RLS |
| Encryption | TLS (Let's Encrypt) + DB encryption at rest |
| Secrets | `.env` + cloud secret manager (AWS Secrets Manager / Doppler) |
| Audit | Append-only `audit.events` table + nightly backup |
| Tenant isolation | RLS enforced in every query |
| LLM safety | Tool catalog with scopes + Pydantic-validated outputs + grounding check |

---

## 11. DevOps & observability

| Concern | Choice |
|---|---|
| Local dev | **Docker Compose** (Postgres, Redis, SeaweedFS) · Langfuse Cloud, not local |
| Production (MVP) | Single VM (Hetzner / DigitalOcean / Fly.io) or small K8s (DOKS / GKE Autopilot) |
| CI | **GitHub Actions** |
| CD | `docker compose pull && up` or simple `flyctl deploy` initially |
| Observability | **OpenTelemetry** SDK → **Grafana Cloud** (free tier) |
| LLM observability | **Langfuse** |
| Errors | **Sentry** |
| Backups | Nightly `pg_dump` → S3; SeaweedFS volume snapshot |

---

## 12. Monorepo layout (MVP)

```
smartinv/
├─ apps/
│  └─ web/                       # Next.js 14
├─ services/
│  └─ api/                       # FastAPI modular monolith
│     ├─ identity/
│     ├─ inventory/
│     ├─ forecast/
│     ├─ optimization/
│     ├─ risk/
│     ├─ masterdata/
│     ├─ narrative/
│     ├─ workflow/
│     ├─ audit/
│     └─ agent_orchestrator/
├─ workers/
│  ├─ async/                     # Dramatiq workers
│  └─ connectors/
│     └─ maximo/                 # first source connector
├─ packages/
│  ├─ tokens/                    # design tokens (source of truth)
│  ├─ ui-contracts/              # TS interfaces (KpiCard, EvidenceStrip, …)
│  ├─ ui-web/                    # shadcn-based web implementations
│  ├─ api-client/                # generated SDK from OpenAPI
│  ├─ types/                     # Zod schemas → TS + Pydantic
│  └─ utils/
├─ infra/
│  ├─ docker/                    # service configs (postgres init, seaweedfs s3.json)
│  └─ deploy/                    # production scripts (Fly / Hetzner / DOKS)
├─ docs/
└─ tests/
   ├─ unit/
   └─ evals/                     # AI evaluation suites
```

---

## 13. Non-negotiable MVP rules

1. **Agents propose, deterministic code disposes.** Same rule as full architecture.
2. **No agent writes to source systems.** Always via Workflow & Approval Service.
3. **No raw DB access from LLMs.** Tools only, with Pydantic validation.
4. **Every recommendation carries its envelope.** Claim, evidence, confidence, assumptions, model_version, approval_path.
5. **Tokens-only styling.** No hex codes in components.
6. **WorkflowEngine, ObjectStore, SearchIndex** are interfaces, never direct calls.
7. **Tenant ID is in the JWT and in every query** — RLS is the safety net, not the primary defense.
8. **Every AI feature ships with an eval suite.** No prompt change without scored results.

---

## 14. From MVP to full architecture

The MVP architecture is designed so the path to the full architecture is **additive**, not destructive:

| MVP component | Full architecture upgrade | Trigger |
|---|---|---|
| Postgres-backed approval state machine | Temporal workflows | Multi-day workflows, escalations, compensations |
| Postgres `audit.events` | Kafka `audit.*` topic → Iceberg | Compliance volume + multi-consumer needs |
| `ml.model_registry` table | MLflow + BentoML | Multiple models / training pipelines per week |
| pgvector | Qdrant / Weaviate | Vector volume + hybrid search |
| Postgres full-text + pg_trgm | OpenSearch | Catalog crosses ~1M items |
| Monolithic FastAPI app | Split services | Independent scaling needs |
| Single VM / small K8s | Full K8s cluster + Helm + ArgoCD | Multi-tenant scale |
| Web-only UI | Tamagui-based shared system + RN mobile | Mobile becomes roadmap item |

Each transition is one component, one decision, one PR.

---

See also: [Full Software Architecture](full-architecture.md) for the production target.
