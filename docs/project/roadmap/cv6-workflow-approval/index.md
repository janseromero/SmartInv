[< Roadmap](../index.md)

# CV6 — Workflow & Approval

**Status:** 🟢 In Progress
**Goal:** Every state change in SmartInv — every min/max edit, every transfer, every requisition, every source-system write — flows through an approval workflow whose policy depends on risk, value, and role, with append-only audit and zero direct writes from agents.

---

## What This Is

CV6 is the cross-cutting layer that makes every other CV trustworthy. It enforces the non-negotiable boundary from [AGENTS.md](../../../../AGENTS.md#architectural-non-negotiables) #2:

> *"No agent writes to source systems directly. All writes go through the Workflow & Approval Service."*

At MVP, the workflow engine is a **Postgres-backed state machine** ([ADR-003](../../decisions.md#adr-003--no-temporal-in-mvp)). Temporal is deferred. The interface is `WorkflowEngine` ([CV1.E7](../cv1-foundations/index.md)) so the day Temporal earns its cost, swapping is a configuration change, not a rewrite.

The promise to the customer:

> *"Every recommendation lives in a queue. Every approval is captured with actor, timestamp, and reason. Every action that touches your ERP/EAM is signed-off by the role your policy says it should be. Every change is auditable forever."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV6.E1](cv6-e1-postgres-workflow-engine/index.md) | Postgres Workflow Engine | `workflow.approvals` + `workflow.approval_events` tables driven by a configurable typed state machine behind the `WorkflowEngine` interface | 🟢 In Progress |
| [CV6.E2](cv6-e2-approval-queue-ui/index.md) | Approval Queue UI | Planner / manager / finance see "my queue", can approve / request changes / reject with reason, see evidence strip and approval steps | ⚪ Planned |
| [CV6.E3](cv6-e3-audit-trail/index.md) | Audit Trail | Append-only `audit.events` topic + queryable view; every recommendation, approval, override, and source-write is logged | ⚪ Planned |
| [CV6.E4](cv6-e4-source-system-write-dispatch/index.md) | Source-System Write Dispatch | Approved actions dispatched via Dramatiq workers to Maximo (and future sources) with idempotency and structured error handling | ⚪ Planned |

---

## Done Condition

CV6 is done when:

- Every recommendation produced by CV3 or CV4 lands in an approval queue scoped by tenant and role.
- Approval policies (auto / 2-step / 3-step / locked) are configurable per recommendation type and threshold.
- Approving an action triggers an idempotent dispatcher that writes to Maximo and records success/failure.
- The audit topic captures every state transition with actor, timestamp, before/after state, and recommendation envelope reference.
- No code path outside the workflow service can write to a source system. Verified by an integration test.
- The "overrides" tab on Approvals captures rejection reasons and routes them to the model-improvement backlog ([CV3.E5](../cv3-explainable-recommendations/index.md)).

---

## Sequencing

```text
E1 (Postgres workflow engine)
  ├── E2 (approval queue UI)
  ├── E3 (audit trail)
  └── E4 (source-system write dispatch)
```

E1 is the spine. E2, E3, E4 can be worked in parallel once E1 is stable.

---

## Out of Scope

- Temporal workflows — deferred ([ADR-003](../../decisions.md#adr-003--no-temporal-in-mvp)) until multi-day workflows, escalation timers, or compensation logic appear.
- Multi-agent agent-to-agent signaling — **CV11 (Multi-Agent Orchestration)**.
- Compliance certification (SOC 2 Type II) — **CV15**.
- Real-time approval push notifications — **CV12 (Mobile & Field)**.

---

**See also:** [Roadmap](../index.md) · [CV3 Explainable Recommendations](../cv3-explainable-recommendations/index.md) · [CV4 Operational Risk Intelligence](../cv4-operational-risk/index.md) · [ADR-003](../../decisions.md#adr-003--no-temporal-in-mvp) · [AGENTS.md non-negotiables](../../../../AGENTS.md#architectural-non-negotiables)
