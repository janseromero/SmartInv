[< Roadmap](../index.md)

# CV10 — Executive Narratives

**Status:** 🔵 Future
**Goal:** C-level sponsors consume SmartInv as a *story*, not as a screen — monthly briefs, plant comparisons, working-capital narratives, and risk summaries grounded only in governed metrics.

---

## What This Is

CV10 widens the user base into Executive Sponsors and Boards. It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that) — full multi-agent orchestration (which includes a Narrative Agent) is deferred.

The promise once activated:

> *"At the start of each month, your CFO, COO, and VP Maintenance receive a brief written by SmartInv: working capital trajectory, risk delta, opportunity sized, decisions requested. Every paragraph traces back to validated metrics. Nothing is invented."*

CV10 is the cleanest first multi-agent use case — narratives are pull-from-governed-metrics generation, not free-form composition.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV10.E1 | Narrative Agent | Constrained-generation LLM that composes paragraphs from a pre-computed metric set with refusal on missing inputs | 🔵 Future |
| CV10.E2 | Template Registry | Versioned templates: executive brief, plant review, planner worklist, procurement review | 🔵 Future |
| CV10.E3 | Reports UI & Preview | Template gallery, preview screen, schedule controls | 🔵 Future |
| CV10.E4 | PDF / PowerPoint Export | Board-ready PDF and PPTX via Playwright / `python-pptx` | 🔵 Future |
| CV10.E5 | Scheduled Deliveries | Cron-driven generation + email / webhook delivery | 🔵 Future |

---

## Done Condition

When CV10 activates:

- The Narrative Agent has an eval suite with golden briefs and assertions on "no invented numbers".
- Templates are versioned and queryable by template ID.
- Scheduled deliveries land on the first business day of each month.
- Every brief carries a footer with the governed-metric IDs and the model version used.

---

## Out of Scope

- Free-form conversational narratives — **CV5 (pull)** vs CV10 (push) is the boundary.
- Real-time event-driven narratives — **CV13 (Event Backbone)**.
- Localization of generated text — Future.

---

**See also:** [Roadmap](../index.md) · [CV5 Governed Conversational Analyst](../cv5-conversational-analyst/index.md) · [CV11 Multi-Agent Orchestration](../cv11-multi-agent-orchestration/index.md)
