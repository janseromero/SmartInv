# SmartInv — Roadmap (Kanban)

> Simple Kanban board with **5 statuses**: `Backlog · Doing · Blocked · Review · Done`.
> Tasks are sliced **vertically** by user journey, per [ADR-010](decisions.md#adr-010--vertical-task-slicing).
> Definition of Done varies by task type — see [engineering-principles.md PR5](../process/engineering-principles.md#pr5--definition-of-done-is-type-specific).

---

## Method recap

| Rule | Detail |
|---|---|
| WIP limits | Max 1 task in **Doing** per person · Max 3 total in **Review** · Max 3 total in **Blocked** |
| Weekly triage | Mondays 09:00 (15 min) — order Backlog, break large tasks |
| Daily sync | 5 min — what I'm pulling |
| Weekly demo | Fridays 15:00 (30 min) — show what entered Review/Done |
| Cycle time | Track Doing → Done trend, not story points |

> Status icons used below:
> `📥 Backlog` · `🛠 Doing` · `⛔ Blocked` · `👀 Review` · `✅ Done`

---

## Board

### 🛠 Doing

_— empty —_

### ⛔ Blocked

_— empty —_

### 👀 Review

_— empty —_

### ✅ Done

_— empty —_

### 📥 Backlog (ordered)

The Backlog is grouped by **Epic** (a meaningful slice of customer value) and ordered roughly in the sequence we plan to pull tasks. Anything at the top of an Epic is the next one in.

---

## Epic E1 — Foundations (week 1–2)

> Goal: a runnable web app, the basic backend, design tokens, auth scaffold, and the contracts that protect future portability.

- [x] **E1.1** Initialize monorepo (Turborepo + pnpm + uv) with `apps/web`, `services/api`, `packages/{tokens,ui-contracts,ui-web,types,utils}` — ✅ done
- [ ] **E1.2** Define design tokens in `packages/tokens` from the HTML mock (colors, spacing, typography, radii, shadows)
- [ ] **E1.3** Wire Tailwind to read tokens from `packages/tokens`; ban raw hex in lint
- [ ] **E1.4** Bootstrap `apps/web` with Next.js 14, layout, sidebar + topbar shell matching the UI mock
- [x] **E1.5** Set up CI on GitHub Actions: lint + type-check + tests + build — ✅ done
- [x] **E1.6** Stand up `services/api` (FastAPI) with health check, OpenAPI export, Pydantic models — ✅ done
- [ ] **E1.7** Docker Compose for local dev: Postgres + Redis + Garage + Langfuse
- [ ] **E1.8** Postgres migration tool (Alembic) + initial schemas (`core`, `inventory`, `agent`, `workflow`, `audit`, `rag`, `ml`, `sources`)
- [ ] **E1.9** Auth scaffold: integrate Auth0 (or Keycloak), JWT on the BFF, current user endpoint
- [ ] **E1.10** Tenant context propagation: tenant_id in JWT → SQLAlchemy session → RLS
- [ ] **E1.11** Define `WorkflowEngine`, `ObjectStore`, `LLMGateway`, `SearchIndex` interfaces in `packages/contracts` with one implementation each
- [ ] **E1.12** Define `KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter` contracts in `packages/ui-contracts`; implement them in `packages/ui-web`
- [ ] **E1.13** Storybook (or Ladle) for `packages/ui-web` with all components

---

## Epic E2 — Executive Overview (vertical slice on mock data)

> First demo-able slice. Real layout, mock data, real auth flow.

- [ ] **E2.1** Planner can log in via Auth0 and land on `/overview`
- [ ] **E2.2** Planner can see 4 KPI cards (Total inventory, Safely reducible, Critical stockout, Service level) with mock data
- [ ] **E2.3** Planner can see the Working Capital trend chart (Visx area chart) with mock data
- [ ] **E2.4** Planner can see the Plant Comparison table with mock data
- [ ] **E2.5** Planner can see the Priority Alerts list with mock data
- [ ] **E2.6** Planner can see the AI-generated monthly narrative card with evidence chips, all mock
- [ ] **E2.7** Replace mock KPI values with values served from `services/api` (still synthetic in DB)

---

## Epic E3 — Inventory Health (real data path)

> First real data flow end-to-end through DB → API → UI.

- [ ] **E3.1** Define `inventory.items` schema (Pydantic + Postgres migration); seed 50 sample items
- [ ] **E3.2** API endpoint `GET /api/inventory/items?site=X&health=low` returns paginated items
- [ ] **E3.3** Planner can see Inventory Health page with the items table from real DB
- [ ] **E3.4** Add filter bar (Site, Criticality, ABC class, Health) wired to query params
- [ ] **E3.5** Implement deterministic Health Score function with unit tests; expose as derived column
- [ ] **E3.6** Planner can see the Health Score donut summary aggregated by site
- [ ] **E3.7** Planner can see KPI cards (Excess value, Dead stock 24m+, Item master completeness) from real aggregates
- [ ] **E3.8** Add Excess / Slow-moving / Obsolete / Stockout-risk badges based on Health Score thresholds
- [ ] **E3.9** Anomaly detection (Isolation Forest) on consumption; surface "Anomalies — last 7 days" panel
- [ ] **E3.10** Save-view feature: planner can save the current filter set as a personal view

---

## Epic E4 — Maximo source connector (end-to-end ingestion)

> Replace synthetic data with a real Maximo source.

- [ ] **E4.1** Define `sources.connectors` and `sources.sync_runs` schemas
- [ ] **E4.2** Implement Maximo REST/MIF client (auth, paging, retries)
- [ ] **E4.3** Pull Maximo `MXITEM` master into `inventory.items` (initial sync), idempotent by item ID
- [ ] **E4.4** Pull Maximo balances into `inventory.balances`
- [ ] **E4.5** Pull Maximo transactions into `inventory.transactions` (last 24 months)
- [ ] **E4.6** Connector status surfaced on `/admin/connectors` page with sync timestamps and errors
- [ ] **E4.7** Scheduled nightly sync via Dramatiq cron task

---

## Epic E5 — Demand Forecasting (model-deterministic)

> First ML feature with full versioning and reproducibility.

- [ ] **E5.1** Define `ml.model_registry` and `ml.predictions` schemas
- [ ] **E5.2** Implement intermittent-demand baseline (Croston / TSB) per item
- [ ] **E5.3** Implement gradient-boosted forecast (LightGBM) with item + seasonality features
- [ ] **E5.4** Compute P50/P80/P95 forecasts; store in `ml.predictions` with `model_version`
- [ ] **E5.5** API endpoint `GET /api/forecast/:item?horizon=12`
- [ ] **E5.6** Planner can see Demand Forecasting page with forecast chart + P50 line + P80–P95 band
- [ ] **E5.7** Planner can see Demand Drivers panel (Driver weights computed from features)
- [ ] **E5.8** Planner can see Forecast Quality card (MASE, bias, P80 coverage)
- [ ] **E5.9** Planner can see Model Comparison table (baseline vs ML vs override vs actual)
- [ ] **E5.10** Planner can submit an override; override is logged with reason and routed to model improvement backlog

---

## Epic E6 — Optimization recommendations (deterministic + envelope)

> First "AI recommendation" with envelope, evidence, and explicit approval path.

- [ ] **E6.1** Implement Min/Max recommendation engine (Pyomo or Monte Carlo)
- [ ] **E6.2** Generate recommendation envelope (claim, evidence, confidence, assumptions, model_version, approval_path)
- [ ] **E6.3** Persist envelope in `ml.recommendations`
- [ ] **E6.4** API endpoint `GET /api/optimization/recommendations?status=pending`
- [ ] **E6.5** Planner can see Optimization Recommendations page with cards (raise min/max, transfer, excess reduction)
- [ ] **E6.6** Each card shows the evidence strip (confidence, Monte Carlo info, lead-time stats, model version)
- [ ] **E6.7** Planner can click "Accept" — recommendation moves to approval queue
- [ ] **E6.8** Pareto frontier visualization on the right pane (mocked then real)
- [ ] **E6.9** "Portfolio impact if accepted" card aggregates selected recommendations

---

## Epic E7 — Approvals & Workflow (Postgres state machine)

> First end-to-end approval flow, from agent envelope to source-system write.

- [ ] **E7.1** Define `workflow.approvals` and `workflow.approval_events` schemas
- [ ] **E7.2** Implement `PostgresWorkflowEngine` behind the `WorkflowEngine` interface
- [ ] **E7.3** Define approval policies (auto, 2-step, 3-step) by recommendation type and value
- [ ] **E7.4** Planner can see "My queue" of pending approvals with evidence strips
- [ ] **E7.5** Manager can approve or reject critical-spare min/max changes
- [ ] **E7.6** Finance can approve working-capital-impact actions above threshold
- [ ] **E7.7** Approved action dispatched via Dramatiq worker to Maximo (idempotent)
- [ ] **E7.8** Audit event written for every state transition
- [ ] **E7.9** "Overrides" tab captures reasons and feeds the model-improvement backlog

---

## Epic E8 — Risk & Criticality (deterministic scoring first)

> Risk view backed by deterministic scoring, with placeholder for future graph model.

- [ ] **E8.1** Define risk scoring function combining item + asset criticality + lead-time variance + single-source flag
- [ ] **E8.2** API endpoint `GET /api/risk/items` and `/api/risk/heatmap`
- [ ] **E8.3** Planner can see Risk & Criticality page with KPI cards (Downtime exposure, Critical spare coverage, Single-source items, Obsolescence candidates)
- [ ] **E8.4** Planner can see Plant × Risk dimension heatmap
- [ ] **E8.5** Planner can see Top Critical-Spare Exposures table
- [ ] **E8.6** Planner can click "Mitigate" — triggers Optimization Agent to draft a mitigation
- [ ] **E8.7** AI-generated risk narrative card (using Narrative Agent — see E10)

---

## Epic E9 — Ask SmartInv (Conversational Analyst)

> First fully agentic capability. Conversational analyst calls tools and returns grounded answers.

- [ ] **E9.1** Stand up `services/agent_orchestrator` with FastAPI + LangGraph
- [ ] **E9.2** Implement LiteLLM gateway with one model (Claude / GPT-4o)
- [ ] **E9.3** Wire Langfuse for tracing
- [ ] **E9.4** Define the tool catalog (`packages/tool-contracts`): `inventory.query_items`, `forecast.predict`, `risk.score`, `optimization.run`
- [ ] **E9.5** Implement Orchestrator graph (intent router → planner → tool calls → composer → validator → finalizer)
- [ ] **E9.6** Grounding validator: every number in the LLM output must come from a tool output
- [ ] **E9.7** SSE endpoint `POST /agents/run` streaming tokens + tool calls + evidence + envelope
- [ ] **E9.8** Planner can use the Ask SmartInv chat page; receives a streamed answer with the evidence strip
- [ ] **E9.9** Planner can click "Pin to dashboard" — creates a saved view
- [ ] **E9.10** Eval suite in `tests/evals/ask_smartinv/` with 20 golden questions and expected behaviors
- [ ] **E9.11** Suggested prompts side panel (5 starter prompts from the UI mock)
- [ ] **E9.12** Session quality KPIs (prompt success rate, avg time to insight)

---

## Epic E10 — Agent Console & Inventory Health Agent

> Visible agentic layer with the first true autonomous-ish run (still proposes, never commits).

- [ ] **E10.1** Implement Inventory Health Agent as a LangGraph subgraph
- [ ] **E10.2** Implement Optimization Agent as a LangGraph subgraph
- [ ] **E10.3** `services/agent_orchestrator` exposes async run via Dramatiq for portfolio scans
- [ ] **E10.4** Planner can see the Agent Console with the 3 agents and their KPIs
- [ ] **E10.5** Each agent card shows status (busy / healthy / idle), tasks 24h, success rate, tool count
- [ ] **E10.6** Orchestration trace view streams events for the most recent run
- [ ] **E10.7** Guardrails panel (toggles for tool-based access, writes via workflow, role-scoped memory) — read-only at MVP
- [ ] **E10.8** Eval suite for Inventory Health Agent recommendations

---

## Epic E11 — Data Quality (item master health)

> The screen the spec considers a differentiator. Backs trust by exposing limits.

- [ ] **E11.1** Implement DQ scoring per item (missing MPN, weak description, inconsistent UoM, missing commodity, missing asset link)
- [ ] **E11.2** API endpoint `GET /api/quality/items` and `/api/quality/issues`
- [ ] **E11.3** Planner can see the Data Quality page with the DQ donut and KPIs
- [ ] **E11.4** Issue backlog table by category with suggested fixes
- [ ] **E11.5** Implement LLM extraction for missing MPN from description (background job)
- [ ] **E11.6** "Start cleansing wave" button enqueues a Dramatiq batch
- [ ] **E11.7** DQ → confidence chart proving that DQ affects recommendation confidence
- [ ] **E11.8** Recommendations include a DQ warning chip when DQ < 60 for the relevant item

---

## Epic E12 — Reports & Stories (Narrative Agent)

> Executive storytelling — the C-level value layer.

- [ ] **E12.1** Implement Narrative Agent (constrained generation from governed metrics only)
- [ ] **E12.2** Template registry (executive brief, plant review, planner worklist, procurement review)
- [ ] **E12.3** Executive can see the Reports page with the four template thumbnails
- [ ] **E12.4** Executive can preview the monthly executive brief generated from governed metrics
- [ ] **E12.5** Export to PDF (via Playwright or `weasyprint`)
- [ ] **E12.6** Export to PowerPoint (via `python-pptx`)
- [ ] **E12.7** "Generate monthly narrative" button on the Executive Overview triggers the agent
- [ ] **E12.8** Scheduled deliveries setting (monthly brief on first business day)
- [ ] **E12.9** Eval suite for Narrative Agent (no invented numbers, exact metric references)

---

## Epic E13 — Procurement & Suppliers (Phase 2)

> Procurement intelligence — strong differentiator, second-tier MVP.

- [ ] **E13.1** Late-PO probability classifier (gradient boosting) with calibrated probabilities
- [ ] **E13.2** Procurement screen KPIs (Open POs, Late risk POs, Lead-time reliability, Off-contract spend)
- [ ] **E13.3** Open POs table with late delivery risk meter and "Expedite" action
- [ ] **E13.4** Supplier scorecards table (lead-time adherence, price trend, late deliveries, emergency buys)
- [ ] **E13.5** AI RFQ draft generation panel (constrained LLM)
- [ ] **E13.6** "Create requisition" workflow (Workflow & Approval Service)

---

## Epic E14 — Admin & Governance

> The operational floor: connectors, model registry, security posture.

- [ ] **E14.1** Connectors list page with sync status badges
- [ ] **E14.2** Model registry table reading from `ml.model_registry`
- [ ] **E14.3** Model rollback action (admin only) — replaces deployed_version pointer
- [ ] **E14.4** Drift watch: cron job that compares recent prediction accuracy to baseline; flags items
- [ ] **E14.5** Security posture page (SSO, RBAC, encryption, audit, SOC 2 readiness — currently informational)
- [ ] **E14.6** Audit log export to CSV (filtered by tenant + time window)

---

## Epic E15 — Polish, Onboarding & Pilot Readiness

> What gets us to the first paying pilot, not just running code.

- [ ] **E15.1** Onboarding wizard: tenant creation, first connector, first user roles
- [ ] **E15.2** Empty-state designs for every page
- [ ] **E15.3** Loading skeletons and error states for every async surface
- [ ] **E15.4** Keyboard navigation pass on every page
- [ ] **E15.5** Accessibility audit (WCAG 2.1 AA) on the four MVP screens
- [ ] **E15.6** Performance budget enforced on dashboard pages (< 2s TTI on a mid-range laptop)
- [ ] **E15.7** Pilot deployment runbook
- [ ] **E15.8** Customer support handover (one-pager per common question)

---

## Backlog parking lot (good ideas, not now)

- Mobile app via Expo + Tamagui (post-MVP)
- Risk graph model (GNN) — currently scored deterministically
- Master Data Agent duplicate review queue UI
- Action Agent as a distinct agent card
- Voice / multimodal in Ask SmartInv
- Multi-region deployment
- Marketplace / partner connectors

---

## How tasks become "Done"

Per [ADR-011](decisions.md#adr-011--definition-of-done-is-type-specific):

| Task type | Done when |
|---|---|
| Deterministic feature | Unit tests + integration test + merged + no regression |
| ML model change | Reproducible + metrics on held-out set + `model_version` registered |
| Agent / prompt change | Eval suite passes threshold + structured envelope validated |
| UI feature | Token-only styling + keyboard accessible + demo in 60 seconds |
| Integration | Idempotent + retry + structured logs + 1 error case handled |

---

## Task card template (use this when adding a task)

```markdown
- [ ] **EX.Y** Short, specific title in user-facing terms

  - **Why:** one line — what user problem or risk this addresses
  - **Scope in:** ...
  - **Scope out:** ...
  - **Done when:**
    - [ ] criterion 1
    - [ ] criterion 2
    - [ ] (if AI) eval threshold ≥ X
  - **Notes:** links to ADRs, PRs, related tasks
```

---

> When in doubt, ship the smallest thing that crosses every layer for one user, one item, one site. Then generalize.
