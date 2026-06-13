[< CV8 Customer Readiness](../index.md)

# CV8.E4 — Performance Budget

**CV:** [CV8 — Customer Readiness](../index.md)
**Status:** ⚪ Planned

---

## What This Is

A measurable performance budget on the MVP dashboard pages, enforced in CI. < 2s TTI on a mid-range laptop. Long jobs surface progress, never freeze the UI. Async patterns (suspense, optimistic UI) wherever a request can take more than a heartbeat.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV8.E4.S1 | Define performance budget per page (TTI, FCP, INP) | 📥 Backlog |
| CV8.E4.S2 | Lighthouse CI baseline + regression check | 📥 Backlog |
| CV8.E4.S3 | Long-job progress surface (Dramatiq job → UI poll/SSE) | 📥 Backlog |
| CV8.E4.S4 | Suspense boundaries + skeleton wiring | 📥 Backlog |
| CV8.E4.S5 | Optimistic UI on common actions (accept recommendation, save view) | 📥 Backlog |

---

## Done Condition

- The four MVP pages meet the budget on a mid-range laptop.
- Lighthouse CI rejects PRs that regress the budget by more than 5%.
- No critical-path interaction freezes the UI.

---

## Out of Scope

- Mobile-network performance — **CV12**.
- Offline performance — **CV12.E3**.

---

**See also:** [CV8](../index.md)
