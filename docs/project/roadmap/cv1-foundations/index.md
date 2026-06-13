[< Roadmap](../index.md)

# CV1 — Foundations

**Status:** 🟢 In Progress · 1 of 8 epics done
**Goal:** Make every later CV cheap to start. A runnable monorepo, a token-based design system, infra you can boot with `docker compose up`, governed schemas, auth with tenant context, swappable interfaces, and a UI shell that matches the design language of the mock.

---

## What This Is

CV1 is the floor. Nothing else ships without it. Every choice here is biased toward **letting later CVs slice vertically through the system without rebuilding the platform**.

Three principles guide every decision in CV1:

1. **Defer what doesn't hurt yet.** No Temporal, no Kafka, no lakehouse, no Tamagui until they earn their cost. ([ADR-003](../../decisions.md#adr-003--no-temporal-in-mvp), [ADR-004](../../decisions.md#adr-004--data-platform--postgres--redis--s3-compatible))
2. **Interfaces over implementations.** `WorkflowEngine`, `ObjectStore`, `LLMGateway`, `SearchIndex` are interfaces with one MVP implementation each — so we can swap them later without rewriting domain code. ([Engineering Principles · AR2](../../../process/engineering-principles.md#ar2--interfaces-over-implementations))
3. **Tokens + contracts before components.** Web-only today, but every UI primitive is consumed via a contract from `@smartinv/ui-contracts`, styled only via `@smartinv/tokens`. The day mobile activates, only the renderer changes. ([ADR-002](../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b))

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV1.E1](cv1-e1-monorepo-tooling/index.md) | Monorepo & Tooling | A runnable `pnpm + uv + turbo` workspace with FastAPI `/health` and a Next.js shell, validated by CI | ✅ Done |
| [CV1.E2](cv1-e2-design-tokens-tailwind/index.md) | Design Tokens & Tailwind Wiring | Tailwind reads from `@smartinv/tokens`; raw hex codes banned in lint | ⚪ Planned |
| [CV1.E3](cv1-e3-ui-shell/index.md) | UI Shell | Sidebar + topbar + screen routing matching the high-fidelity UI mock | ⚪ Planned |
| [CV1.E4](cv1-e4-local-infrastructure/index.md) | Local Infrastructure | Docker Compose for Postgres + Redis + object store + Langfuse | ⚪ Planned |
| [CV1.E5](cv1-e5-database-foundations/index.md) | Database Foundations | Alembic + initial schemas: `core`, `inventory`, `agent`, `workflow`, `audit`, `rag`, `ml`, `sources` | ⚪ Planned |
| [CV1.E6](cv1-e6-auth-tenancy/index.md) | Auth & Tenancy | SSO / OIDC sign-in, JWT with tenant_id, Postgres Row-Level Security | ⚪ Planned |
| [CV1.E7](cv1-e7-core-service-contracts/index.md) | Core Service Contracts | `WorkflowEngine`, `ObjectStore`, `LLMGateway`, `SearchIndex` interfaces with MVP implementations | ⚪ Planned |
| [CV1.E8](cv1-e8-component-contracts-storybook/index.md) | Component Contracts & Web Implementations | `KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter` contracts + web implementations + Storybook | ⚪ Planned |

---

## CV1.E1 — Stories (closed)

| # | Story | Status |
|---|---|---|
| CV1.E1.S1 | Initialize monorepo (Turborepo + pnpm + uv) with `apps/web`, `services/api`, `packages/*` | ✅ Done |
| CV1.E1.S2 | Set up CI on GitHub Actions: lint + typecheck + tests + build | ✅ Done |
| CV1.E1.S3 | Stand up `services/api` (FastAPI) with `/health`, OpenAPI export, Pydantic models | ✅ Done |

Delivered in commits `a84e370`, `b7a1586`, `bdce4d8`, `2854d9a`, `237ddca`, `87572b8`.

---

## Done Condition

CV1 is done when:

- `pnpm install && uv sync --all-packages` brings the whole monorepo to a runnable state.
- `docker compose up` boots Postgres, Redis, the object store, and Langfuse locally.
- `pnpm --filter=@smartinv/web dev` boots the Next.js shell with the sidebar + topbar from the UI mock.
- A signed-in planner lands on a placeholder Inventory Health page with their `tenant_id` enforced via RLS.
- All four core service interfaces have an MVP implementation behind them.
- `KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, and `ConfidenceMeter` are usable from `apps/web` via `@smartinv/ui-web`.
- CI is green and runs all of the above on every push.

---

## Sequencing

```text
E1 (monorepo & tooling)
  ├── E2 (design tokens) ── E3 (UI shell) ── E8 (component contracts)
  └── E4 (local infra) ── E5 (DB schemas) ── E6 (auth & tenancy)
                          └── E7 (core service contracts)
```

The web track (E2 → E3 → E8) and the backend track (E4 → E5 → E6) can be
worked in parallel. E7 (contracts) lands once schemas and tenancy exist —
otherwise we'd be designing interfaces blind to their first real consumer.

---

## Out of Scope

- Agent orchestration runtime — that lives in **CV5 (Governed Conversational Analyst)**.
- Forecasting and optimization engines — **CV3**.
- Risk scoring — **CV4**.
- Source-system connectors — **CV2.E1 (Maximo)**.
- Cross-platform UI system (Tamagui) — **CV12 (Mobile & Field)**.
- Temporal, Kafka, Lakehouse, Feast, MLflow, BentoML — explicitly deferred ([ADR-003](../../decisions.md#adr-003--no-temporal-in-mvp), [ADR-004](../../decisions.md#adr-004--data-platform--postgres--redis--s3-compatible)).

---

**See also:** [Roadmap](../index.md) · [MVP Architecture](../../../architecture/mvp-architecture.md) · [Decisions](../../decisions.md) · [Engineering Principles](../../../process/engineering-principles.md)
