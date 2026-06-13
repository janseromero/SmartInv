[< CV3 Explainable Recommendations](../index.md)

# CV3.E4 — Recommendations UI

**CV:** [CV3 — Explainable Inventory Recommendations](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV3.E3

---

## What This Is

The Optimization Recommendations screen from the mock: recommendation cards with evidence strip, accept/adjust/override actions, the Pareto frontier on the side, and a "Portfolio impact if accepted" preview. The visible promise of CV3.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV3.E4.S1 | Recommendations page with card list (raise min/max, transfer, excess reduction) | 📥 Backlog |
| CV3.E4.S2 | EvidenceStrip on every card rendering confidence, model_version, source records | 📥 Backlog |
| CV3.E4.S3 | Accept / Adjust / Override actions per card | 📥 Backlog |
| CV3.E4.S4 | Bulk-select + "Accept selected" with portfolio impact preview | 📥 Backlog |
| CV3.E4.S5 | Pareto frontier scatter on the right pane | 📥 Backlog |
| CV3.E4.S6 | Tabs: Recommendations · Excess plans · Transfers · Scenarios · History | 📥 Backlog |

---

## Done Condition

- Planner can review, accept, adjust, or override recommendations from a single screen.
- "Accept" routes to the workflow approval queue (CV6); never a direct DB write.
- The evidence strip is present on every card.
- The Pareto frontier reflects the current optimization run.

---

## Out of Scope

- Real what-if scenario builder — **CV10.E3** (or unlocks here with a thin slice).
- Mobile rendering — **CV12**.

---

**See also:** [CV3](../index.md) · [CV3.E3](../cv3-e3-recommendation-envelope/index.md) · [CV6.E2](../../cv6-workflow-approval/cv6-e2-approval-queue-ui/index.md)
