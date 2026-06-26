[< CV6 Workflow & Approval](../index.md)

# CV6.E1 — Postgres Workflow Engine

**CV:** [CV6 — Workflow & Approval](../index.md)
**Status:** ✅ Done
**Prerequisite for:** CV6.E2, CV6.E3, CV6.E4

---

## What This Is

The workflow spine. Implements the `WorkflowEngine` interface ([CV1.E7](../../cv1-foundations/cv1-e7-core-service-contracts/index.md)) against Postgres tables (`workflow.approvals`, `workflow.approval_events`) using a typed state machine. Temporal is deferred ([ADR-003](../../../decisions.md#adr-003--no-temporal-in-mvp)); the interface is the migration insurance.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV6.E1.S1 | Implement `PostgresWorkflowEngine` behind the `WorkflowEngine` interface | ✅ Done |
| CV6.E1.S2 | `workflow.approvals` table + configurable state machine: agent_proposed → ordered reviewer path → approved/rejected | ✅ Done |
| CV6.E1.S3 | `workflow.approval_events` append-only event log | ✅ Done |
| CV6.E1.S4 | Policy table: workflow type × value × criticality → required approvers | ✅ Done |
| CV6.E1.S5 | Idempotency keys on every state transition | ✅ Done |
| CV6.E1.S6 | Engine contract tests assert protocol compliance | ✅ Done |

---

## Done Condition

- Every recommendation can be submitted, transitioned, and finalized through the engine API.
- State transitions are atomic and idempotent.
- Policy rules drive the approval graph; changing policy does not require code changes.
- The engine passes the `WorkflowEngine` contract suite.

---

## Out of Scope

- Temporal implementation — deferred.
- Escalation timers / SLA deadlines — Future.
- Mobile push notifications — **CV12**.

---

**See also:** [CV6](../index.md) · [CV1.E7](../../cv1-foundations/cv1-e7-core-service-contracts/index.md) · [ADR-003](../../../decisions.md#adr-003--no-temporal-in-mvp)
