[< CV6 Workflow & Approval](../index.md)

# CV6.E3 — Audit Trail

**CV:** [CV6 — Workflow & Approval](../index.md)
**Status:** ✅ Done
**Depends on:** CV6.E1

---

## What This Is

Append-only audit. Every state-changing operation (recommendation creation, approval transition, source-system write, configuration change, override) lands in `audit.events`. The audit is the floor for [Engineering Principles · S3](../../../../process/engineering-principles.md#s3--audit-is-the-floor-not-the-ceiling).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV6.E3.S1 | `audit.events` append-only table with indexes on actor, tenant_id, kind, time | ✅ Done |
| CV6.E3.S2 | Audit service emits an event on state-changing workflow/recommendation/review/admin endpoints | ✅ Done |
| CV6.E3.S3 | Audit query view with role-gated access | ✅ Done |
| CV6.E3.S4 | CSV export for compliance teams | ✅ Done |
| CV6.E3.S5 | Regression test asserting no state-changing endpoint can skip audit | 📥 Backlog |

---

## Done Condition

- Every state-changing operation produces an audit event.
- Audit events are queryable by actor, tenant, kind, and time window.
- A failing regression test blocks any state-changing endpoint that bypasses audit.

---

## Out of Scope

- SOC 2 audit packaging — **CV15.E1**.
- Real-time audit streaming for SIEM — **CV13**.

---

**See also:** [CV6](../index.md) · [CV15.E1](../../cv15-compliance-operations/cv15-e1-soc2-readiness/index.md)
