[< CV6 Workflow & Approval](../index.md)

# CV6.E4 — Source-System Write Dispatch

**CV:** [CV6 — Workflow & Approval](../index.md)
**Status:** 🟢 In Progress · dispatch spine delivered behind the `SourceWriter` seam; the live Maximo write client (S2) is deferred until CV2.E1.S10
**Depends on:** CV6.E1, CV2.E1

---

## What This Is

The single gate through which any SmartInv-originated change lands in the customer's ERP/EAM. Dramatiq workers consume approved actions and dispatch them with idempotency, retries, and dead-letter handling. Every write produces an audit event (CV6.E3) and a delivery receipt.

This is the operational manifestation of [AGENTS.md non-negotiable #2](../../../../AGENTS.md#architectural-non-negotiables).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV6.E4.S1 | Source-write queue + dispatcher (Dramatiq-ready, runs sync today) | ✅ Done |
| CV6.E4.S2 | Idempotent **Maximo** write client (min/max change, transfer, requisition) | 📥 Backlog (blocked on CV2.E1.S10) |
| CV6.E4.S3 | Retry / backoff policy with dead-letter queue for permanent failures | ✅ Done |
| CV6.E4.S4 | Delivery receipt persisted on the originating recommendation | ✅ Done |
| CV6.E4.S5 | Failed writes generate a structured incident with surfaced reason | ✅ Done |

---

## Done Condition

- An approved min/max change reaches Maximo within a defined SLO with audit and delivery receipt.
- Replaying a write does not duplicate or corrupt the source record (idempotency).
- A failure surfaces as a structured incident, never silently swallowed.

---

## Implementation Notes (MVP)

The dispatch spine ships behind a `SourceWriter` seam ([ADR-030 path mirrors
ADR-024](../../decisions.md)): an `EchoSourceWriter` delivers deterministically
with no external call, so the queue, idempotency, retry/backoff, dead-letter, and
delivery-receipt machinery are real and tested today. The **live Maximo write
client (S2)** is the only deferred piece and is gated on the real
`MaximoConnector` ([CV2.E1.S10](../../cv2-inventory-health/cv2-e1-maximo-connector/index.md)).
Swapping `EchoSourceWriter` for `MaximoSourceWriter` changes only
`api/infra/providers.py`. The dispatcher is synchronous and idempotent so a
Dramatiq worker later simply calls `process_pending` (run today via
`make dispatch` / `POST /admin/dispatch`).

## Out of Scope

- SAP / Oracle / Infor write clients — Phase 2.
- Source-system back-pressure / quotas — Future.

---

**See also:** [CV6](../index.md) · [CV2.E1](../../cv2-inventory-health/cv2-e1-maximo-connector/index.md) · [CV6.E3](../cv6-e3-audit-trail/index.md)
