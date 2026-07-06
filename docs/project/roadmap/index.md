[< Project](../decisions.md) · [Engineering Principles](../../process/engineering-principles.md) · [AGENTS](../../../AGENTS.md)

# SmartInv — Roadmap

The roadmap is organized as **CV → Epic → Story**. Each level has its own
home. Epics get their own folder (with `plan.md` and `test-guide.md`) when
work on them actually begins.

| Level | Definition | Granularity |
|---|---|---|
| **CV** (Capability Value) | A major delivery stage with clear user-visible impact | Months |
| **Epic** | A cohesive block of work within a CV, with a done condition | Weeks |
| **Story** | An atomic, user-centric delivery that can be verified end-to-end | Hours to days |

### Status icons

| CV / Epic level | Story level (Kanban) |
|---|---|
| ✅ Done | ✅ Done |
| 🟢 In Progress | 👀 Review |
| 🟡 Planning | 🛠 Doing |
| ⚪ Planned | ⛔ Blocked |
| 🔵 Future | 📥 Backlog |

CV / Epic statuses are strategic; Story statuses use the 5-column Kanban
discipline ([Engineering Principles · PR1](../../process/engineering-principles.md#pr1--kanban-with-5-statuses)).

---

## Capability Values

### MVP (must ship to first paying pilot)

| Code | Capability Value | Status |
|------|-----------------|--------|
| [CV0](cv0-pilot-dq-assessment/index.md) | Pilot Data-Quality Assessment | ⚪ Planned |
| [CV1](cv1-foundations/index.md) | Foundations | ✅ Done · 8 of 8 epics |
| [CV2](cv2-inventory-health/index.md) | Inventory Health & Visibility | 🟢 In Progress |
| [CV3](cv3-explainable-recommendations/index.md) | Explainable Inventory Recommendations | 🟢 In Progress · 5 of 5 epics (deterministic) |
| [CV4](cv4-operational-risk/index.md) | Operational Risk Intelligence | 🟢 In Progress · 4 of 4 epics (deterministic) |
| [CV5](cv5-conversational-analyst/index.md) | Governed Conversational Analyst | 🟢 In Progress · slice 1 (governed path) |
| [CV6](cv6-workflow-approval/index.md) | Workflow & Approval | 🟢 In Progress |
| [CV7](cv7-data-quality-trust/index.md) | Data Quality & Trust | ⚪ Planned |
| [CV8](cv8-customer-readiness/index.md) | Customer Readiness | ⚪ Planned |

### Phase 2 (deferred per [AGENTS.md](../../../AGENTS.md#mvp-scope--build-this-defer-that))

| Code | Capability Value | Status |
|------|-----------------|--------|
| [CV9](cv9-procurement-supplier/index.md) | Procurement & Supplier Intelligence | 🔵 Future |
| [CV10](cv10-executive-narratives/index.md) | Executive Narratives | 🔵 Future |
| [CV11](cv11-multi-agent-orchestration/index.md) | Multi-Agent Orchestration | 🔵 Future |
| [CV12](cv12-mobile-field/index.md) | Mobile & Field | 🔵 Future |
| [CV13](cv13-event-backbone/index.md) | Event Backbone | 🔵 Future |
| [CV14](cv14-advanced-ml/index.md) | Advanced ML | 🔵 Future |
| [CV15](cv15-compliance-operations/index.md) | Compliance & Multi-Tenant Operations | 🔵 Future |

---

## MVP narrative

The MVP path through the CVs:

```text
CV0 (pilot DQ assessment)
   │  decides if a customer is viable for a pilot
   ▼
CV1 (foundations)
   │  monorepo, design system, infra, schemas, auth, UI shell
   ▼
   ├── CV2 (inventory health & visibility)
   ├── CV3 (explainable recommendations)
   ├── CV4 (operational risk intelligence)
   └── CV5 (governed conversational analyst)
        │
        ▼
   ┌─────────────────────────────────────────────┐
   │ CV6 (workflow & approval) is cross-cutting  │
   │ CV7 (data quality & trust)  is cross-cutting│
   └─────────────────────────────────────────────┘
        │
        ▼
   CV8 (customer readiness)
        │  pilot deployment
        ▼
   First paying pilot
```

CV6 and CV7 are cross-cutting — they accrete value as CV2–CV5 land,
and CV8 finishes whatever pilot-readiness gaps remain.

---

## MVP killer capabilities (per AGENTS.md)

The MVP delivers four end-to-end capabilities plus the cross-cutting layers
that make them trustworthy:

1. **Inventory Health & Visibility** → CV2
2. **Explainable Min/Max & Reorder Recommendations** → CV3
3. **Critical Spare & Risk** → CV4
4. **Governed Conversational Analyst (one tool, not multi-agent)** → CV5

All four are wrapped by CV6 (Workflow & Approval) and CV7 (Data Quality & Trust),
delivered by CV1 (Foundations), and made customer-ready by CV8.

---

## Phase 2 narrative

Phase 2 begins after a paying pilot validates that the MVP delivers measurable
inventory cost reduction without raising operational risk. Each Phase 2 CV
expands a specific dimension of value:

- **CV9** widens the user base into Procurement.
- **CV10** widens the user base into C-level via narratives.
- **CV11** evolves the AI architecture from a single governed tool to
  orchestrated specialist agents.
- **CV12** extends SmartInv to mobile and field use.
- **CV13** moves the architecture from batch to event-driven.
- **CV14** deepens the ML stack (TFT, GNN, RL exploration).
- **CV15** lifts the platform to enterprise compliance and multi-tenant ops.

Phase 2 CV indices are scaffolded but kept light — their bodies fill in when
the CV activates.

---

## How to add a new CV

1. Decide it passes the three tests: user-visible promise, months of work,
   independent of the others.
2. Create a folder `cv{N}-kebab-name/` and add an `index.md` matching the
   structure of an existing one.
3. Update this top-level index (table + narrative paragraph).
4. Open an ADR in [`decisions.md`](../decisions.md) for any architectural
   choice the new CV implies.

## How to add a new Epic

1. Pick or create the parent CV.
2. Add a row to the CV's `Epics` table.
3. When work on the Epic *starts*, create a folder
   `cv{N}-foundations/cv{N}-e{M}-kebab-name/` with `index.md`, and when the
   epic is non-trivial, `plan.md` and `test-guide.md`. This mirrors the
   Mirror Mind discipline of not over-scaffolding ahead of work.

## How to add a new Story

1. Stories live as rows in the relevant Epic table (or in a Stories table
   inside the CV's `index.md` when the epic is small).
2. Status uses the 5-column Kanban (📥 🛠 ⛔ 👀 ✅).
3. Stories are sliced **vertically** by user journey ([ADR-010](../decisions.md#adr-010--vertical-task-slicing)).
4. Definition of Done is type-specific ([ADR-011](../decisions.md#adr-011--definition-of-done-is-type-specific)).

---

## Radar

Forward-looking improvements not committed to a CV. Surfaced for visibility,
not planned for a specific cycle. Items graduate from Radar to CV/Epic when
they fit a larger arc.

### Lakehouse & data products marketplace

**Surfaced:** 2026-06-13

When MRO inventory data needs to be combined with finance, SAP master data,
or third-party reliability data, a lakehouse layer (Delta or Iceberg) plus a
governed data-product publishing surface becomes valuable. Today this is
outside MVP and CV13 (Event Backbone).

### Marketplace / partner connector ecosystem

**Surfaced:** 2026-06-13

Allowing third parties to publish connectors (Maximo flavors, SAP add-ons,
historian integrations) would shorten time-to-value per pilot. Requires a
connector contract version and a publishing process — neither exists yet.

### White-label SaaS multi-tenancy

**Surfaced:** 2026-06-13

Beyond per-tenant isolation, full white-label SaaS implies brand theming,
custom domains, billing primitives, and partner-managed support. Currently
out of scope; would graduate when a partner channel materializes.

### On-prem / air-gapped deployment

**Surfaced:** 2026-06-13

Some industrial customers cannot run hosted SaaS. An on-prem distribution
story (signed installer, offline model registry, offline LLM gateway) would
unlock that segment. Today every dependency choice ([ADR-005 Garage](../decisions.md#adr-005--garage-as-the-mvp-s3-compatible-store))
already considers self-host paths, so the foundation is friendly to this
graduation.

---

**See also:** [Decisions](../decisions.md) · [Engineering Principles](../../process/engineering-principles.md) · [MVP Architecture](../../architecture/mvp-architecture.md) · [AGENTS](../../../AGENTS.md)
