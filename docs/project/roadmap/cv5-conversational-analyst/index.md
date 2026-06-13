[< Roadmap](../index.md)

# CV5 — Governed Conversational Analyst

**Status:** ⚪ Planned
**Goal:** A planner asks SmartInv a question in natural language about their inventory, suppliers, work orders, or recommendations, and gets a grounded answer with evidence chips and source-record links — never invented numbers, never write actions.

---

## What This Is

CV5 is the fourth MVP killer capability ([AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that) item 4). It is **explicitly one governed tool, not a multi-agent system** — multi-agent orchestration is deferred to [CV11](../cv11-multi-agent-orchestration/index.md). The promise:

> *"Ask any question over governed inventory, usage, work-order, supplier, and recommendation data. Get an answer grounded in tool outputs only, with confidence, evidence chips, model version, and links back to source records. Never invented numbers. Never write actions."*

The trust contract is enforced in code, not in the prompt. A grounding validator rejects any LLM output containing numbers that did not come from a tool call. Eval-driven development is non-negotiable per [ADR-014](../../decisions.md#adr-014--eval-driven-development-for-ai-features).

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV5.E1](cv5-e1-llm-gateway-tool-catalog/index.md) | LLM Gateway & Tool Catalog | LiteLLM-backed gateway with a versioned tool catalog (Pydantic-validated input/output, per-scope ACLs) | ⚪ Planned |
| [CV5.E2](cv5-e2-qa-tool-invocation/index.md) | Read-Only Q&A with Tool Invocation | Planner asks a question; SmartInv routes to tools and composes a grounded answer over governed metrics only | ⚪ Planned |
| [CV5.E3](cv5-e3-evidence-strip-source-links/index.md) | Evidence Strip & Source Links | Every answer renders confidence, model_version, tool calls, governed-metric chips, and clickable source records | ⚪ Planned |
| [CV5.E4](cv5-e4-grounding-validator-evals/index.md) | Grounding Validator & Eval Suite | Deterministic validator rejects ungrounded numbers; golden eval set in `tests/evals/` runs in CI | ⚪ Planned |

---

## Done Condition

CV5 is done when:

- A planner can ask a free-form natural-language question against the Q&A endpoint and receive a streamed response.
- Every response carries the evidence strip with confidence, model_version, and at least one tool-call breadcrumb.
- The grounding validator blocks any response whose numeric claims do not match tool outputs; CI fails when validators are bypassed.
- The eval suite contains ≥ 30 golden questions covering inventory, forecast, risk, optimization, and procurement — with assertions on tool-use correctness and grounding.
- The LLM gateway exposes a single API; switching model vendors requires no code change ([ADR-006](../../decisions.md#adr-006--agent-orchestration-with-langgraph--postgressaver)).
- No write actions, no dashboard creation, no agent-to-agent calls. (Those activate in Phase 2 CVs.)

---

## Sequencing

```text
E1 (LLM gateway & tool catalog)
  └── E2 (read-only Q&A with tool invocation)
        ├── E3 (evidence strip & source links)
        └── E4 (grounding validator & eval suite)
```

E1 is the platform; E2 is the runtime; E3 and E4 are the trust layers that wrap it.

---

## Out of Scope (per AGENTS.md)

- Multi-agent orchestration with specialist agents — **CV11**.
- Dashboard / report creation through conversation — Phase 2.
- Write actions ("create requisition", "apply min/max change") through chat — Phase 2.
- Conversational narratives for executives — **CV10 (Executive Narratives)**.
- Voice / multimodal — Future.

---

**See also:** [Roadmap](../index.md) · [CV1 Foundations](../cv1-foundations/index.md) · [CV6 Workflow & Approval](../cv6-workflow-approval/index.md) · [CV11 Multi-Agent Orchestration](../cv11-multi-agent-orchestration/index.md) · [ADR-014 Eval-Driven Development](../../decisions.md#adr-014--eval-driven-development-for-ai-features)
