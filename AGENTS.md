# SmartInv — Project Operating Instructions

> Read by every AI assistant (Pi, Codex, Gemini CLI, Claude Code) and by every new contributor before touching this repository.

---

## What this project is

SmartInv is an **AI-powered MRO inventory intelligence platform** for industrial customers (manufacturing, oil & gas, logistics, utilities). It sits *above* existing ERP/EAM systems and turns inventory data into explainable recommendations, governed agentic workflows, and executive narratives.

For full context, see [README.md](README.md).

---

## Operating mode

- Default mode: **Builder Mode** (Mirror Mind), persona: `engineer`.
- Activate via `/mm-build smartinv` (Pi / Gemini CLI), `$mm-build smartinv` (Codex), or `/mm:build smartinv` (Claude Code).

---

## Language

- All code, comments, commits, ADRs, docs, and tests are written in **English**, regardless of the language conversations happen in.
- User-facing strings can be localized later — they are not the project's primary language.

---

## Stack at a glance (MVP)

| Layer | Choice |
|---|---|
| Monorepo | Turborepo + pnpm + uv |
| Web | Next.js 14 + Tailwind + shadcn/ui |
| Mobile | Deferred — but contracts pattern keeps the door open |
| Services | Python 3.12 + FastAPI (modular monolith) |
| Data | PostgreSQL 16 (+ pgvector, pg_trgm, RLS) · Redis · Garage/MinIO/S3 |
| Agents | LangGraph + LiteLLM + Langfuse |
| Workflow | Postgres-backed state machine (Temporal deferred) |
| Background jobs | Dramatiq + Redis |
| CI | GitHub Actions |
| Observability | OpenTelemetry → Grafana Cloud + Sentry |

For full architecture: [docs/architecture/mvp-architecture.md](docs/architecture/mvp-architecture.md).
For the target end-state: [docs/architecture/full-architecture.md](docs/architecture/full-architecture.md).

---

## Conventions

- **Python:** `uv` for dependency management; `ruff` + `mypy`; tests via `pytest`.
- **JS/TS:** `pnpm`; TypeScript strict; `biome` (or `eslint` + `prettier`); tests via `vitest`.
- **SQL:** all schema changes via Alembic migrations — no manual `ALTER TABLE` in production.
- **Styling:** tokens only; no raw hex codes in components.
- **Naming:** features grouped under `apps/web/features/<domain>` and `services/api/<domain>`.
- **Commits:** descriptive English commit messages explaining *why*, not just *what*.
- **PRs:** small (< 300 lines preferred). Self-merges not allowed.

---

## Architectural non-negotiables

1. **Agents propose, deterministic code disposes.** LLMs reason and recommend; only deterministic workflows commit state changes.
2. **No agent writes to source systems directly.** All writes go through the Workflow & Approval Service.
3. **No raw DB access from LLMs.** Agents call versioned tools with Pydantic-validated inputs and outputs.
4. **Every recommendation carries its envelope.** Claim, evidence, confidence, assumptions, model_version, approval_path.
5. **Tenant ID lives in the JWT, in every query, in every log line.** RLS is the safety net, not the primary defense.
6. **Models, prompts, tools are versioned.** Reproducibility is non-negotiable.
7. **No raw hex colors in components.** Tokens only.

---

## Testing discipline

| Code type | Discipline |
|---|---|
| Deterministic (business rules, formulas, validators) | Classic unit tests (TDD) |
| Model-deterministic (ML models, scoring) | Reproducibility + held-out eval set + drift monitor |
| Non-deterministic (LLM agents, narratives) | Eval-driven development — golden datasets in `tests/evals/` |

Unit tests are **required** in every PR introducing or changing deterministic code.

---

## Decision-making

- Significant architectural choices are recorded as **ADRs** in [`docs/project/decisions.md`](docs/project/decisions.md).
- New ADRs are appended (never edit old ones — supersede instead).
- An architectural change without an ADR is rejected.

---

## What to read first (priority order)

1. [`README.md`](README.md)
2. [`docs/architecture/mvp-architecture.md`](docs/architecture/mvp-architecture.md)
3. [`docs/process/engineering-principles.md`](docs/process/engineering-principles.md)
4. [`docs/project/decisions.md`](docs/project/decisions.md)
5. [`docs/project/roadmap.md`](docs/project/roadmap.md)

---

## Hard constraints

- **Truth.** Do not invent numbers, library APIs, model versions, or behaviors. If uncertain, say so.
- **Service, not subservience.** Engineering is an intellectual partnership, not task execution.
- **Effectiveness before efficiency.** Working on the right thing comes before optimizing how we do it.

---

## When you make a change

1. Find or create the task in [`docs/project/roadmap.md`](docs/project/roadmap.md).
2. Slice the work **vertically** through the layers it touches.
3. Write tests (or evals) first.
4. Apply the type-specific Definition of Done.
5. Update docs in the same PR if the change is architectural.
6. Open a small PR with a clear "why" in the description.

That is the contract.
