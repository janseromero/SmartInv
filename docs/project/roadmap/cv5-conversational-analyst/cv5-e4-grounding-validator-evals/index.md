[< CV5 Governed Conversational Analyst](../index.md)

# CV5.E4 — Grounding Validator & Eval Suite

**CV:** [CV5 — Governed Conversational Analyst](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV5.E2

---

## What This Is

The trust contract enforced in code, not in the prompt. A deterministic validator inspects every LLM output and rejects any numeric claim that did not come from a tool call. The golden eval suite lives in `tests/evals/` and runs in CI; prompt changes that drop the score below threshold cannot merge ([ADR-014](../../../decisions.md#adr-014--eval-driven-development-for-ai-features)).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV5.E4.S1 | Validator extracts numeric claims from LLM output (NER + regex) | 📥 Backlog |
| CV5.E4.S2 | Validator cross-references claims against tool outputs; rejects on mismatch | 📥 Backlog |
| CV5.E4.S3 | Golden eval set (≥ 30 questions) in `tests/evals/ask_smartinv/` | 📥 Backlog |
| CV5.E4.S4 | Langfuse evaluator integration for grounding, faithfulness, tool-use correctness | 📥 Backlog |
| CV5.E4.S5 | CI job runs eval suite on every prompt change | 📥 Backlog |
| CV5.E4.S6 | Eval threshold gates merge; failures show the diff in the PR | 📥 Backlog |

---

## Done Condition

- No answer with ungrounded numbers reaches the UI in test or in production.
- Eval suite covers inventory, forecast, risk, optimization, and procurement (placeholder) questions.
- A regression test asserts the validator catches a deliberately ungrounded LLM output.
- The CI eval job blocks merges below threshold.

---

## Out of Scope

- LLM-based evaluators that are themselves ungrounded — Future.
- Cross-model eval comparison — Future.

---

**See also:** [CV5](../index.md) · [ADR-014](../../../decisions.md#adr-014--eval-driven-development-for-ai-features) · [Engineering Principles · A4](../../../../process/engineering-principles.md#a4--grounding-is-enforced-by-code)
