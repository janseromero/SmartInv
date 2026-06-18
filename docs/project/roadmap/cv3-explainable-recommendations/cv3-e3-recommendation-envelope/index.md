[< CV3 Explainable Recommendations](../index.md)

# CV3.E3 — Recommendation Envelope

**CV:** [CV3 — Explainable Inventory Recommendations](../index.md)
**Status:** ✅ Done (reuses `ml.recommendations`; append-only)
**Depends on:** CV3.E2
**Design:** [ADR-028](../../../decisions.md#adr-028--explainable-recommendations-deterministic-crostontsb-forecast--closed-form-optimization-versioned-lightgbmpyomo-deferred)

> Every recommendation persists the full envelope (claim, evidence, confidence, assumptions, model_version, approval_path) in `ml.recommendations`. Envelopes are **append-only** — a re-run replaces only still-`proposed` rows; accepted/overridden ones are immutable history. SSE serialization (S4) lands with CV5.

---

## What This Is

Every recommendation in SmartInv ships as an envelope: claim, evidence, confidence, assumptions, model_version, approval_path. This epic establishes the schema, the persistence, the API surface, and the immutability rules.

The envelope is the structural backbone of [AGENTS.md non-negotiable #4](../../../../AGENTS.md#architectural-non-negotiables): *"Every recommendation carries its envelope."*

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV3.E3.S1 | Define envelope schema (Pydantic + Zod) shared by API and UI | 📥 Backlog |
| CV3.E3.S2 | Persist envelopes in `ml.recommendations` (immutable; new versions append) | 📥 Backlog |
| CV3.E3.S3 | `GET /api/recommendations?status=pending` + filters | 📥 Backlog |
| CV3.E3.S4 | Envelope serializer for SSE streaming (used by CV5 conversational analyst) | 📥 Backlog |
| CV3.E3.S5 | Reproducibility hook: given an envelope ID, reproduce inputs + model versions | 📥 Backlog |

---

## Done Condition

- Every recommendation persisted carries a complete envelope.
- No code path mutates a stored envelope in place.
- The envelope schema is the contract consumed by the UI evidence strip.
- A regression test asserts reproducibility from envelope ID.

---

## Out of Scope

- UI rendering of envelopes — **CV3.E4** + **CV1.E8 (EvidenceStrip)**.
- Workflow / approval execution — **CV6**.

---

**See also:** [CV3](../index.md) · [CV3.E4](../cv3-e4-recommendations-ui/index.md) · [CV6](../../cv6-workflow-approval/index.md)
