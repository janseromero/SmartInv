[< CV5 Governed Conversational Analyst](../index.md)

# CV5.E3 — Evidence Strip & Source Links

**CV:** [CV5 — Governed Conversational Analyst](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV5.E2

---

## What This Is

The user-visible commitment to trust. Every answer renders an evidence strip with confidence, model version, governed-metric chips, tool-call breadcrumbs, and clickable source-record links that resolve to concrete rows in Maximo / Postgres.

The strip is what separates SmartInv from a "GPT wrapper" in the customer's eyes.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV5.E3.S1 | `EvidenceStrip` component consuming the envelope from CV3.E3 | 📥 Backlog |
| CV5.E3.S2 | Tool-call breadcrumb chips with hover-to-expand details | 📥 Backlog |
| CV5.E3.S3 | Source-record link rendering: resolves to source-system ID + drill view | 📥 Backlog |
| CV5.E3.S4 | "Challenge answer" action capturing structured user feedback | 📥 Backlog |
| CV5.E3.S5 | Confidence visualization (meter + numeric value) | 📥 Backlog |
| CV5.E3.S6 | Violet accent reserved for AI-produced content ([AGENTS.md non-negotiable #8](../../../../AGENTS.md#architectural-non-negotiables)) | 📥 Backlog |

---

## Done Condition

- Every answer renders the strip with at least confidence + model_version + one tool chip.
- Source links resolve to real records.
- "Challenge answer" routes into the override feedback loop (CV3.E5 pattern).
- The violet AI marker is consistent across every AI-produced surface.

---

## Out of Scope

- Voice / multimodal evidence — Future.
- Cross-conversation evidence linking — Future.

---

**See also:** [CV5](../index.md) · [CV1.E8](../../cv1-foundations/cv1-e8-component-contracts-storybook/index.md) · [CV3.E5](../../cv3-explainable-recommendations/cv3-e5-override-feedback-loop/index.md)
