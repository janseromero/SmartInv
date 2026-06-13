[< CV7 Data Quality & Trust](../index.md)

# CV7.E3 — LLM-Powered Cleansing

**CV:** [CV7 — Data Quality & Trust](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV7.E1, CV5.E1

---

## What This Is

Constrained-generation LLM extraction for missing manufacturer part numbers, description normalization, and UoM harmonization. The "wave" job runs in batches with a high-confidence auto-apply threshold and a human-review queue for everything below.

Always grounded ([Engineering Principles · A4](../../../../process/engineering-principles.md#a4--grounding-is-enforced-by-code)) — the LLM operates on the item's own description and never invents free-form values.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV7.E3.S1 | Tool: extract MPN from description (NER + LLM fallback) | 📥 Backlog |
| CV7.E3.S2 | Tool: normalize description to noun-modifier template | 📥 Backlog |
| CV7.E3.S3 | Tool: harmonize UoM with provided UoM dictionary | 📥 Backlog |
| CV7.E3.S4 | Cleansing wave Dramatiq job — batches with confidence threshold | 📥 Backlog |
| CV7.E3.S5 | Auto-apply ≥ 0.9; queue 0.6–0.9 for review; reject < 0.6 | 📥 Backlog |
| CV7.E3.S6 | Eval suite per cleansing tool ([ADR-014](../../../decisions.md#adr-014--eval-driven-development-for-ai-features)) | 📥 Backlog |

---

## Done Condition

- The three cleansing tools have working prompts and eval suites passing thresholds.
- A wave can be run on a tenant; the impact (items improved) is queryable.
- Cleansing actions route through CV6 for applied changes that touch source systems.

---

## Out of Scope

- Write-back to source ERP/EAM master data — Future (per-customer governance).
- Cross-language description normalization — Future.

---

**See also:** [CV7](../index.md) · [CV5.E1](../../cv5-conversational-analyst/cv5-e1-llm-gateway-tool-catalog/index.md) · [CV7.E4](../cv7-e4-dq-confidence-linkage/index.md)
