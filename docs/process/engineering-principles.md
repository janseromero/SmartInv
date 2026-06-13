# SmartInv — Engineering Principles

> The principles below describe **how we write SmartInv**: a startup-pragmatic engineering culture that is nonetheless compatible with a modern agentic, AI-heavy, enterprise-grade product.
>
> They sit between two failure modes — *over-engineering for an audience we don't have yet* and *under-engineering away the trust that is our entire moat*.

---

## 1. Product principles (the *why* under the code)

These shape every technical decision.

### P1 — Trust is the moat

Industrial buyers are not impressed by AI demos. They are impressed by AI they can audit, override, and defend in a meeting with their CFO. Every recommendation must be explainable, traceable, and reproducible.

### P2 — Agents propose, deterministic code disposes

LLM agents reason and recommend. Deterministic code commits state changes. The boundary between the two is the most important architectural line in the system, and it lives in versioned tool contracts.

### P3 — Trust the boring layers

Numbers come from deterministic tools, not from LLMs. Forecasting is a statistical function. Optimization is operations research. The LLM never invents a value that wasn’t in a tool output.

### P4 — Effectiveness before efficiency

Build the right thing before optimizing how we build it. Cycle-time charts and process discussions matter less than whether the thing we are shipping changes a user's decision.

### P5 — Defer what doesn’t hurt yet

Every architectural component must earn its operational cost. If pain is hypothetical, the solution is deferred.

---

## 2. Code principles

### C1 — Type everything that touches a boundary

Boundaries: HTTP, DB, queue, file, LLM, third-party API. Use **TypeScript strict** on the web, **Pydantic + mypy** on the backend. Boundaries without types are leaks waiting to happen.

### C2 — Schemas are the source of truth

We define data with **Zod (TS)** and **Pydantic (Python)** schemas — once. Types are derived from schemas. API contracts are generated. Tests assert against schemas.

### C3 — Tokens, not values

No hex code appears in a component. No magic number lives in business logic. Constants live in a small set of well-named modules.

### C4 — Functions are small, modules are clear

Prefer a 30-line pure function over a 200-line class. Prefer a clear module boundary over a clever abstraction.

### C5 — Pure where possible, side-effecting where necessary

State mutation belongs in identifiable places (services, workflow handlers). Calculations stay pure and testable.

### C6 — Don’t hide the work

If a workflow has 5 steps, the code shows 5 steps. Cleverness that obscures structure is rejected.

### C7 — Versioning is not optional

Models, prompts, tools, schemas, and API surfaces are versioned. A bug in a recommendation must be reproducible 6 months later with the exact same model and prompt versions.

### C8 — One language per layer (mostly)

TypeScript for client, Python for backend, SQL for data. Bash exists, but is never the right home for business logic.

---

## 3. Testing principles

Testing is **non-negotiable** — but its shape changes by the type of code.

### T1 — Three test pyramids, not one

| Code type | Test discipline |
|---|---|
| **Deterministic** (business rules, formulas, validators) | Classic **TDD-style unit tests** + property-based tests where useful |
| **Model-deterministic** (ML predictions, scoring) | Reproducibility tests + held-out evaluation sets + drift monitors |
| **Non-deterministic** (LLM agents, narratives) | **Eval-driven development**: golden datasets + scored evaluators (faithfulness, grounding, tool-use correctness) |

### T2 — Unit tests are required, always

Every PR that introduces a deterministic function adds at least one unit test for the happy path and one for an obvious failure path. CI fails otherwise.

### T3 — Integration tests for crossings

Every boundary crossing (HTTP, DB, queue, LLM call) has at least one integration test that exercises the full crossing.

### T4 — Evals are tests, not extras

Every prompt change is scored against an eval suite. A prompt is not "merged" if the eval score drops below threshold. Treat the eval suite like any other test file — it lives in `tests/evals/`, runs in CI, and grows with the system.

### T5 — Bugs become tests

Every bug fix includes a regression test. Tests are how we *remember* the system.

### T6 — End-to-end tests for critical flows only

We don't try to test everything end-to-end. We test the 5–10 flows that, if broken, would destroy customer trust: approve a min/max change, run a forecast, ask a question and get a grounded answer, export a board pack.

### T7 — Coverage is a smell, not a target

Coverage numbers are useful as a smell — sudden drops mean something. They are not a target. A test that asserts nothing is worse than no test.

### T8 — Tests describe behavior, not implementation

Test names read as sentences (`it_recommends_min_max_increase_when_stockout_probability_is_high`). When the implementation changes but the behavior is the same, the tests don't move.

---

## 4. AI / agentic principles

### A1 — One tool per capability, versioned

Every capability an agent can invoke (`forecast.predict`, `inventory.query_items`, `optimization.run`) is a versioned tool with a Pydantic input/output schema, an allowed scope, and an owner.

### A2 — Agents never see raw data

Agents call tools. Tools touch the database. The LLM context window never contains rows pulled directly from a table.

### A3 — Envelope or it didn't happen

Every agent output is an envelope: claim, evidence, confidence, assumptions, recommended action, approval path, model version. If it doesn't fit the envelope, it doesn't ship.

### A4 — Grounding is enforced by code

A separate deterministic validator confirms that every number in the narrative exists in a tool output. The LLM cannot invent numbers; the validator catches it if it tries.

### A5 — Human approval for state changes

Agents propose. State changes go through the Workflow & Approval Service. No exceptions.

### A6 — Observability is a feature

Every agent run is traced. Every tool call is logged. Every recommendation links back to its trace. The Agent Console is a *product*, not an afterthought.

### A7 — Cost is a property of correctness

Token cost and latency are tracked per run. A correct answer that costs $0.50 is worse than a correct answer that costs $0.005. We treat cost like any other test metric.

### A8 — Eval suites are part of the product

The eval suite is owned by the team. It grows when a customer complains. It grows when a bug is fixed. It is the single most important asset protecting our trust moat.

---

## 5. Architecture principles

### AR1 — Modular monolith first

We start as a modular monolith with clearly named modules. We split into services only when independent scaling, deployment, or team boundaries force it.

### AR2 — Interfaces over implementations

`WorkflowEngine`, `ObjectStore`, `SearchIndex`, `LLMGateway` are interfaces. Implementations are swappable. This is how we go from "Postgres state machine" to "Temporal" without a rewrite.

### AR3 — Tenant ID is a first-class citizen

Tenant ID lives in the JWT, in every query, in every event, in every log line. RLS is the safety net, not the primary defense.

### AR4 — One source of truth per fact

If two tables can disagree about a fact, the design is wrong. Source-system records are immutable. Derived state is recomputable.

### AR5 — Side effects through services, not from components

UI components don't write to the DB. Services do. UI calls services through typed clients.

### AR6 — Events are append-only

Audit, workflow events, and agent events are append-only. Truth is the sequence of events; tables are projections.

### AR7 — The simplest infra that works

Until pain proves otherwise: 1 Postgres, 1 Redis, 1 object store, 1 FastAPI app, 1 web app, GitHub Actions, Sentry, Grafana Cloud. Adding a component is a decision with a trigger, not a default.

---

## 6. Process principles (how we ship)

### PR1 — Kanban with 5 statuses

`Backlog · Doing · Blocked · Review · Done`. WIP-limited. Triaged weekly. Demoed weekly. Details in [roadmap.md](../project/roadmap.md).

### PR2 — Vertical task slicing

Tasks slice end-to-end through layers (UI + API + DB + tests). Horizontal slices ("build the data layer this month, the API next month") are rejected.

### PR3 — One task at a time per person

WIP limit is one in `Doing` per person. If you can't move forward, the task goes to `Blocked` with a reason, and you pull a new one.

### PR4 — Demo every Friday

Internal or to a friendly customer. Anything not demo-able by Friday is the team's most important signal.

### PR5 — Definition of Done is type-specific

| Task type | Done means |
|---|---|
| Deterministic feature | Unit tests + integration test + merged + no regression |
| ML model change | Reproducible + metrics on held-out set + registered in `ml.model_registry` |
| Agent / prompt change | Eval suite passes threshold + structured envelope validated |
| UI feature | Token-only styling + keyboard accessible + demo in 60s |
| Integration | Idempotent + retry logic + structured logs + 1 error case handled |

### PR6 — ADRs for directional choices

Every architectural decision is recorded in [decisions.md](../project/decisions.md). Future contributors must be able to learn *why*, not just *what*.

### PR7 — Commits tell the why

Commit messages explain *why*, not just *what*. Small commits with clear review boundaries.

### PR8 — Pull requests are small

Default size: < 300 lines changed. If a PR is large, it should have been multiple PRs.

### PR9 — Review is mandatory, blocking

No self-merges. Reviews are technical and respectful. Style is automated (Biome / Ruff). Reviews are about correctness, design, and clarity.

### PR10 — Bugs are paid back in tests

Every fix adds a regression test. The system gets harder to break, not easier.

---

## 7. Security principles

### S1 — Least privilege everywhere

Users see only their tenant. Services have minimal DB roles. Agents only see tools in their scope.

### S2 — Secrets never in git

Use `.env.local` + cloud secret manager. Pre-commit hooks block accidental commits.

### S3 — Audit is the floor, not the ceiling

Every meaningful action is logged. We design for compliance from day one even if we are not certified yet.

### S4 — Encrypt by default

TLS in transit, KMS at rest, field-level for sensitive PII.

### S5 — Tenant isolation has two layers

Application-level (JWT + service code) and database-level (RLS). Either is enough; both is what we ship.

---

## 8. Data principles

### D1 — Source-system data is sacred

Maximo says what Maximo says. We never overwrite source-of-truth records. Derived data lives in its own tables.

### D2 — Versioned model outputs

Every prediction in `ml.predictions` includes `model_version`, input fingerprint, and timestamp. Reproducibility is non-negotiable.

### D3 — Schemas live in migrations

Every DB change is a migration file in git. No manual `ALTER TABLE` in production.

### D4 — Tests run against a real database

Unit tests can mock; integration tests use a real Postgres. SQL bugs hide where mocks live.

---

## 9. Documentation principles

### DOC1 — Docs are part of the product

Documentation lives in `docs/` and is updated in the same PR as the code change.

### DOC2 — README is the entry point

A new contributor can productively start from `README.md` alone. Everything else is reachable from there.

### DOC3 — ADRs explain decisions

Significant choices are recorded with context, options, decision, and trade-offs.

### DOC4 — Architecture docs are kept honest

If the code disagrees with the architecture doc, one of them is wrong — and we fix it before moving on.

---

## 10. Hard constraints (project-level)

These apply to every contributor and every AI assistant working in this repository.

1. **Truth.** Do not invent numbers, library APIs, model versions, or behaviors. If uncertain, say so.
2. **Service, not subservience.** Engineering is an intellectual partnership, not task execution.
3. **English everywhere.** Code, comments, commits, docs, and tests in English regardless of the language conversations happen in.
4. **Effectiveness before efficiency.** Working on the right thing comes before optimizing how we do it.
5. **No raw secrets, no raw data, no raw mutations.** Through interfaces, through services, through workflows.

---

## 11. What we explicitly are *not*

So the culture stays sharp:

- ❌ We are not a research lab. We ship.
- ❌ We are not a consultancy. Process exists to serve the product.
- ❌ We are not a hyperscaler. Operational complexity must earn its place.
- ❌ We are not an "AI startup that wraps GPT." We are an industrial intelligence platform whose moat is trust.

---

## 12. Living document

These principles will evolve. Changes go through a PR like any other change, and the PR explains *why*. When a principle changes, the ADR explaining the new direction is mandatory.
