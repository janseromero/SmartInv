# SmartInv — Recommended Software Architecture (Full Reference)

> This is the **full target architecture** for SmartInv at production scale. It describes the end-state we are designing toward, not what we ship in the MVP.
>
> For the MVP scope, see **[MVP Software Architecture](mvp-architecture.md)**.

---

## 1. Architectural style

**Modular monolith → microservices**, organized around clear business domains: Inventory Health, Forecast, Optimization, Risk, Procurement, Master Data, Narrative, Workflow, Agents, Governance.

Three structural choices drive everything else:

1. **Monorepo** (Turborepo or Nx) — one workspace for web + mobile + services + shared packages.
2. **Cross-platform UI system** built on **Tamagui** — 100% of design tokens and 80%+ of components are shared between React (web) and React Native (mobile).
3. **Agent-aware backbone** — every agent runs as a workflow on **Temporal**, communicates over **Kafka**, and writes only via the **Workflow & Approval Service**.

---

## 2. End-to-end stack overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                         CLIENTS (shared design system)                │
│  Web (Next.js 14 + React)         Mobile (Expo + React Native)        │
│  Tamagui  +  Tailwind tokens      Tamagui  +  Reanimated              │
│  TanStack Query  +  Zustand       Offline cache (WatermelonDB)        │
└───────────────────────────────────────────────────────────────────────┘
                 │                                  │
                 ▼                                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         BFF / API GATEWAY                             │
│   tRPC (internal) + REST/OpenAPI (external) + GraphQL (BI/exports)    │
│   Auth0 / Keycloak (SSO, SAML, OIDC, MFA)  +  OPA (ABAC/RBAC)         │
│   Streaming: SSE + WebSockets for chat, alerts, agent traces          │
└───────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         DOMAIN SERVICES (Python FastAPI)              │
│  Inventory │ Forecast │ Optimization │ Risk │ Procurement │ Master    │
│  Data │ Narrative │ Workflow & Approval │ Notification │ Audit        │
└───────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         AGENT ORCHESTRATION                           │
│   LangGraph / OpenAI Agents SDK    Temporal workflows (durable)       │
│   LiteLLM gateway → OpenAI / Anthropic / Azure / vLLM                 │
│   Langfuse for prompt + agent observability                           │
└───────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         DATA & ML PLATFORM                            │
│  PostgreSQL (RLS) │ pgvector │ Redis │ OpenSearch │ S3/MinIO/Garage   │
│  Lakehouse: Databricks + Delta (or Iceberg + DuckDB)                  │
│  Feature Store: Feast       ML Registry: MLflow      Serving: BentoML │
└───────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         EVENT BACKBONE & INTEGRATION                  │
│   Kafka / Redpanda + Schema Registry (Avro/Protobuf)                  │
│   Debezium CDC │ Connectors: Maximo, SAP S/4, Oracle, Infor, Lakehouse│
│   dbt + Dagster for batch ELT                                         │
└───────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         PLATFORM & OPS                                │
│   Kubernetes (EKS/AKS/GKE) │ Helm │ Terraform │ Vault / KMS │ Sentry  │
│   OpenTelemetry → Prometheus + Grafana + Loki + Tempo                 │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Frontend (shared web + mobile)

| Layer | Choice | Why |
|---|---|---|
| Web framework | **Next.js 14** (App Router, RSC) | Streaming UI, SSR for executive briefs, edge runtime |
| Mobile framework | **Expo + React Native** | Shared TS code, OTA updates, push notifications |
| Cross-platform UI | **Tamagui** | One component library compiles to web and native with shared tokens |
| Styling tokens | Tailwind tokens (HTML mock already defines them) | Move CSS variables → Tamagui theme config |
| State | **TanStack Query** + **Zustand** | Server cache + lightweight UI state |
| Forms | **React Hook Form** + **Zod** | Schema reuse with backend |
| Charts | **Visx** (web) + **Victory Native** (mobile) — or ECharts via wrapper | Heatmaps, Pareto, forecast bands |
| Chat / streaming | **Vercel AI SDK** + SSE | Powers "Ask SmartInv" |
| Realtime | WebSockets (`socket.io` or native) | Agent traces, notifications |
| Mobile-specific | Expo Notifications, Expo Camera/BarCode, WatermelonDB offline, biometrics | Field use: scan, approve, lookup offline |

### Reuse target

- **100%** of types, validators, design tokens, business rules
- **~80%** of components (lists, KPI cards, evidence strip, approval cards)
- **~50%** of screens (overview, approvals, alerts on mobile; agent console + report designer web-only)

---

## 4. BFF / API contract

| Concern | Choice |
|---|---|
| Internal contract | **tRPC** for typed end-to-end calls in the monorepo |
| External / partner | **REST + OpenAPI 3.1** auto-generated from FastAPI/Pydantic |
| BI exports | **GraphQL** for the governed semantic layer |
| AuthN | **Keycloak** (self-host) or **Auth0** (managed) — SAML, OIDC, MFA |
| AuthZ | **Open Policy Agent (OPA)** for ABAC; Postgres RLS as second line |
| Rate limit / gateway | **Kong** or **Envoy** |
| Realtime | SSE for narrative streaming; WebSocket for agent traces and alerts |

---

## 5. Backend services (Python FastAPI)

A single language (Python) keeps ML/data and business code on one runtime, avoiding two SDKs and two CI pipelines.

| Service | Responsibility | Key Libraries |
|---|---|---|
| Identity & Tenancy | SSO, RBAC/ABAC enforcement, tenant scoping | `fastapi`, `authlib`, `opa-python` |
| Inventory | Catalog, balances, transactions, health scoring | `sqlalchemy`, `pydantic` |
| Forecast | Probabilistic demand forecasting | `darts`, `nixtla`, `lightgbm`, `xgboost` |
| Optimization | Min/max, safety stock, transfers, Pareto | `pyomo`, `ortools`, `numpy`, Monte Carlo |
| Risk | Scoring, criticality, graph analytics | `networkx`, `pyg` (GNN), `pyod` (anomaly) |
| Procurement | Suppliers, POs, RFQs, scorecards | `scikit-learn` (late-PO classifier) |
| Master Data | Duplicate detection, NLP normalization | `sentence-transformers`, `splink`, `spacy` |
| Narrative | Grounded LLM storytelling | `langchain` / `litellm`, template engine |
| Workflow & Approval | Durable approval flows, source-system writes | **Temporal Python SDK** |
| Notification | Alerts, channels, prioritization | `apprise`, FCM, APNs, email |
| Audit & Governance | Append-only audit, model lineage | Kafka → Iceberg cold storage |

---

## 6. Agentic layer

The UI shows 7 agents and an orchestration trace. Build it like this:

| Concern | Choice |
|---|---|
| Agent framework | **LangGraph** or **OpenAI Agents SDK** |
| Long-running execution | **Temporal** workflows (retries, timeouts, audit) |
| LLM gateway | **LiteLLM** — unified API for OpenAI, Anthropic, Azure, Bedrock, vLLM |
| Vector store | **pgvector** (start) → **Qdrant** for scale |
| RAG / governed access | Tools call governed APIs (not raw DB). Tool catalog versioned. |
| Observability | **Langfuse** for prompt / agent traces, cost, evals |
| Guardrails | **NeMo Guardrails** or **Guardrails AI** + output validation in code |
| Eval | Custom benchmarks + Langfuse evaluators on a frozen test set per release |

Every agent emits a structured envelope (claim, evidence, confidence, assumptions, recommended action, approval path, model version). The UI evidence strip consumes this envelope directly.

---

## 7. Data platform

| Layer | Choice | Notes |
|---|---|---|
| OLTP | **PostgreSQL 16** with Row-Level Security per tenant | Single source of truth for transactional state |
| Vector | **pgvector** (start), **Qdrant** (scale) | Duplicate detection, semantic search |
| Search | **OpenSearch** or **Meilisearch** | Free-text + filters across items, suppliers, assets |
| Cache | **Redis** | Sessions, hot KPIs, rate limits |
| Object storage | **S3** (cloud) / **Garage** / **MinIO** (self-host) | Reports, attachments, embeddings backups |
| Time series | **TimescaleDB** | Metrics + KPI trend curves |
| Lakehouse | **Databricks + Delta** or **Apache Iceberg + DuckDB** | Bronze/Silver/Gold from ERP/EAM CDC |
| Feature Store | **Feast** | Online (Redis) + offline (Delta) parity |
| ML Registry | **MLflow** | Model versioning, drift watch |
| ML Serving | **BentoML** or **KServe** on K8s | Forecast, risk, duplicate, late-PO models |

Multi-tenancy = schema-per-tenant on Postgres for premium tenants; shared schema + RLS for SaaS tier.

---

## 8. Event & integration layer

| Concern | Choice |
|---|---|
| Broker | **Kafka** (Confluent / MSK) or **Redpanda** |
| Schema | **Avro** + Confluent Schema Registry |
| CDC | **Debezium** for SAP / Oracle DB; Maximo MIF webhooks for events |
| Connectors | Custom Python workers per source (Maximo, SAP S/4 OData/CDS, Oracle Procurement REST, Infor ION, lakehouse Delta Share) |
| Batch ELT | **dbt-core** + **Dagster** |
| iPaaS alternative | **Airbyte** for low-touch SaaS sources |

Events drive agent triggers, notifications, and audit.

---

## 9. Workflows & approvals

The UI relies heavily on multi-step approvals and durable agent runs. Use **Temporal.io**:

- Approval workflows with timers, escalation, cancellation
- Agent runs (planner → risk → optimization → narrative) survive restarts
- Single audit log of every signal
- Strong fit with the “source-system writes only via Workflow & Approval Service” rule

Each approval path = a Temporal workflow definition (e.g. `criticalSpareMinMaxChange`).

---

## 10. Security, privacy, governance

| Control | Implementation |
|---|---|
| SSO | Keycloak / Auth0 (SAML, OIDC) |
| MFA | TOTP + WebAuthn / passkeys |
| RBAC/ABAC | OPA policies, decision logs |
| Encryption | TLS 1.3 in transit; KMS at rest; field-level for PII |
| Secrets | HashiCorp Vault or cloud KMS |
| Audit | Append-only Kafka topic → Iceberg cold storage; queryable Postgres view |
| Tenant isolation | RLS + per-tenant Vault namespaces + signed JWTs |
| LLM safety | NeMo Guardrails + tool allowlist + no raw DB access |
| Compliance | SOC 2 Type II + ISO 27001 + GDPR/LGPD playbook |

---

## 11. DevEx, CI/CD, observability

| Concern | Choice |
|---|---|
| Monorepo | **Turborepo** (or Nx) |
| Package manager | **pnpm** (web), **uv** / **Poetry** (Python) |
| CI | **GitHub Actions** + Docker Buildx + cache |
| CD | **ArgoCD** or **Flux** for K8s |
| IaC | **Terraform** + **Helm** |
| Container orch | **Kubernetes** + Karpenter autoscaling |
| Observability | **OpenTelemetry** + **Prometheus** + **Grafana** + **Loki** + **Tempo** |
| LLM/Agent observability | **Langfuse** |
| Errors | **Sentry** |
| Feature flags | **OpenFeature** + Unleash / LaunchDarkly |

---

## 12. Monorepo layout (target)

```
smartinv/
├─ apps/
│  ├─ web/                  # Next.js 14
│  ├─ mobile/               # Expo (iOS + Android)
│  ├─ admin/                # internal back-office (optional)
│  └─ api-gateway/          # tRPC + REST/OpenAPI BFF
├─ services/
│  ├─ inventory/            # FastAPI
│  ├─ forecast/
│  ├─ optimization/
│  ├─ risk/
│  ├─ procurement/
│  ├─ masterdata/
│  ├─ narrative/
│  ├─ workflow/             # Temporal worker
│  ├─ notification/
│  └─ audit/
├─ agents/
│  ├─ orchestrator/         # LangGraph
│  ├─ inventory_health/
│  ├─ risk/
│  ├─ optimization/
│  ├─ procurement/
│  ├─ masterdata/
│  ├─ narrative/
│  └─ action/
├─ packages/
│  ├─ ui/                   # Tamagui design system
│  ├─ types/                # Zod schemas → TS types
│  ├─ api-client/           # Generated SDK
│  ├─ icons/
│  └─ utils/
├─ infra/
│  ├─ terraform/
│  ├─ helm/
│  └─ docker/
└─ data/
   ├─ dbt/
   └─ dagster/
```

---

## 13. Mapping UI requirements → architecture

| UI requirement | What in the stack solves it |
|---|---|
| Evidence strip on every AI widget | Agent envelope contract + Langfuse trace IDs surfaced via API |
| Confidence + model version chips | MLflow registry IDs propagated through services |
| Heatmap + Pareto + forecast bands | Visx (web) + Victory Native (mobile) sharing data shapes |
| Approval steps | Temporal workflow definitions per approval path |
| Source-system writes guard | Workflow & Approval Service is the only writer of POs/min-max changes |
| Conversational analyst | Vercel AI SDK + SSE + LangGraph + tool-restricted RAG over governed views |
| Notification dot + priority alerts | Kafka topics + Notification Service + WebSocket fan-out |
| Connectors panel | Independent Python workers, status emitted to Kafka, surfaced via Audit Service |
| Model registry with rollback / drift | MLflow + Langfuse + scheduled drift jobs in Dagster |
| Mobile field use (barcode, approve) | Expo Camera + WatermelonDB offline cache + Expo Notifications |

---

## 14. Non-negotiable architectural rules

1. **Agents propose, deterministic code disposes.** Agents reason and recommend; only deterministic workflows commit state changes.
2. **No agent writes to source systems directly.** All writes go through the Workflow & Approval Service.
3. **No raw DB access from LLMs.** Agents call versioned tools with Pydantic-validated inputs and outputs.
4. **Every recommendation carries its envelope.** Claim, evidence, confidence, assumptions, model_version, approval_path.
5. **All tenant data is isolated by JWT + RLS + tool scope.** No cross-tenant reads, ever.
6. **Models are pinned.** Every prediction includes its `model_version` (registered in MLflow).
7. **All side effects are auditable.** Append-only audit topic + queryable view.
8. **The UI never contains a hex color.** Tokens only.

---

## 15. Glossary (architecture-relevant)

- **Agentic envelope** — structured output of an agent: claim, evidence, confidence, assumptions, recommended action, approval path, model version.
- **Tool catalog** — versioned list of functions agents are allowed to call. Each tool has Pydantic input/output schemas and scopes.
- **Workflow & Approval Service** — the only service authorized to write to source systems. Every write goes through an approved workflow definition.
- **Evidence strip** — UI element rendering the envelope as compact chips next to AI output.
- **Model-deterministic** — output is reproducible given the same input and pinned model version.

---

See also: [MVP Software Architecture](mvp-architecture.md) for the simplified ship-first version.
