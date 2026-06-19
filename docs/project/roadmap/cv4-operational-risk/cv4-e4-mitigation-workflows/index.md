[< CV4 Operational Risk Intelligence](../index.md)

# CV4.E4 — Mitigation Workflows

**CV:** [CV4 — Operational Risk Intelligence](../index.md)
**Status:** ✅ Done (routes to the approval seam; CV6 executes once built)
**Depends on:** CV4.E3, CV3.E2, CV6.E1
**Design:** [ADR-029](../../../decisions.md#adr-029--operational-risk-deterministic-likelihoodxconsequence-score--rule-based-critical-spare-versioned-gnngbm-deferred)

> "Mitigate" reuses the item's CV3 reorder policy to stage a `risk_mitigation` recommendation envelope (`approval_path='cv6_workflow'`, status `proposed`) — never a direct write (#2), identical to CV3 accept / CV2.E4 merge. CV6 performs the actual execution and outcome-tracking once it exists; the risk-narrative card is grounded templated text.

---

## What This Is

Closes the loop from risk to action. The "Mitigate" button on a high-risk item generates a candidate mitigation envelope via the optimization engine (CV3.E2), routes it to the approval queue (CV6.E2), and tracks outcome (success / rejection).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV4.E4.S1 | "Mitigate" action button on high-risk items | 📥 Backlog |
| CV4.E4.S2 | Mitigation candidate generation via CV3.E2 optimization engine | 📥 Backlog |
| CV4.E4.S3 | Mitigation envelope routed to CV6 approval queue with correct precedence | 📥 Backlog |
| CV4.E4.S4 | Mitigation outcome (approved / rejected / superseded) tracked back to the originating risk item | 📥 Backlog |
| CV4.E4.S5 | Risk-narrative card on the dashboard summarizes top mitigations (grounded text only) | 📥 Backlog |

---

## Done Condition

- A maintenance manager can move from a heatmap cell to an approved mitigation in three clicks.
- Mitigation outcomes update the risk score on the affected item.
- The risk narrative card never invents numbers.

---

## Out of Scope

- Automated mitigation execution without approval — forbidden ([AGENTS.md non-negotiable #2](../../../../AGENTS.md#architectural-non-negotiables)).
- Cross-tenant mitigation patterns — Future.

---

**See also:** [CV4](../index.md) · [CV3.E2](../../cv3-explainable-recommendations/cv3-e2-optimization-engine/index.md) · [CV6.E2](../../cv6-workflow-approval/cv6-e2-approval-queue-ui/index.md)
