[< CV6 Workflow & Approval](../index.md)

# CV6.E2 — Approval Queue UI

**CV:** [CV6 — Workflow & Approval](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV6.E1

---

## What This Is

The Approvals screen from the mock. "My queue" per role, approval cards with evidence strip and approval steps, Approve / Request Changes / Reject actions with structured reasons, and the Automation Policy table for transparency.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV6.E2.S1 | "My queue" page filtered by current actor | 📥 Backlog |
| CV6.E2.S2 | Approval card with evidence strip + before/after impact summary | 📥 Backlog |
| CV6.E2.S3 | `ApprovalStep` visualization showing path progress | 📥 Backlog |
| CV6.E2.S4 | Approve / Request Changes / Reject actions with structured reasons | 📥 Backlog |
| CV6.E2.S5 | Tabs: My queue · Semi-automated · Completed · Overrides | 📥 Backlog |
| CV6.E2.S6 | Automation policy table view (read-only at MVP) | 📥 Backlog |

---

## Done Condition

- Planner, manager, and finance roles see their respective queues.
- Approving a critical-spare action requires a manager step; approving > $25K requires finance.
- Every action persists an event with actor, timestamp, and reason.

---

## Out of Scope

- Editing automation policy in-app — Future.
- Mobile push notifications — **CV12**.

---

**See also:** [CV6](../index.md) · [CV6.E1](../cv6-e1-postgres-workflow-engine/index.md) · [CV1.E8 (ApprovalStep)](../../cv1-foundations/cv1-e8-component-contracts-storybook/index.md)
