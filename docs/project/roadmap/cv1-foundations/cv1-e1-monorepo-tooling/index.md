[< CV1 Foundations](../index.md)

# CV1.E1 — Monorepo & Tooling

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done

---

## What This Is

The first epic of CV1. Establishes the runnable shape of the repository: a pnpm + Turborepo monorepo with `apps/web` (Next.js 14), `services/api` (FastAPI), `packages/*` (tokens, contracts, types, utils), a uv-managed Python workspace, and GitHub Actions CI green on every push.

Delivered in commits `a84e370`, `b7a1586`, `bdce4d8`, `2854d9a`, `237ddca`, `87572b8`.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E1.S1 | Initialize monorepo (Turborepo + pnpm + uv) with `apps/web`, `services/api`, `packages/{tokens,ui-contracts,ui-web,types,utils}` | ✅ Done |
| CV1.E1.S2 | Set up CI on GitHub Actions: lint + typecheck + tests + build | ✅ Done |
| CV1.E1.S3 | Stand up `services/api` (FastAPI) with `/health`, OpenAPI export, Pydantic models | ✅ Done |

---

## Done Condition

All criteria met:

- ✅ `pnpm install && uv sync --all-packages` brings the workspace to a runnable state.
- ✅ `pnpm typecheck` passes (8 tasks via turbo).
- ✅ `pnpm build` builds web + 5 packages.
- ✅ `pnpm test` runs vitest across the workspace.
- ✅ `uv run pytest` passes 3 tests against `/health` + OpenAPI.
- ✅ `uv run ruff check`, `ruff format --check`, `mypy services` are all clean.
- ✅ GitHub Actions runs the JS and Python pipelines on every push.

---

## Out of Scope

- Design tokens content — **CV1.E2**.
- Tailwind ↔ tokens wiring — **CV1.E2**.
- UI shell components — **CV1.E3**.

---

**See also:** [CV1](../index.md) · [CV1.E2](../cv1-e2-design-tokens-tailwind/index.md)
