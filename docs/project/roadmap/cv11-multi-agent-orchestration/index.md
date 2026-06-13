[< Roadmap](../index.md)

# CV11 — Multi-Agent Orchestration

**Status:** 🔵 Future
**Goal:** Replace the single governed Q&A tool ([CV5](../cv5-conversational-analyst/index.md)) with a graph of specialist agents — Inventory Health, Risk, Optimization, Procurement, Master Data, Narrative — collaborating under an orchestrator with full audit and governed tool access.

---

## What This Is

CV11 is the architectural shift from *one governed tool* to *orchestrated agents*. It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that): in the MVP, "Ask SmartInv is ONE governed tool, not 7 agents."

The promise once activated:

> *"One user question may activate several agents in parallel. The orchestrator routes intent, agents call governed tools, conflicts resolve through declared precedence, and the user sees an orchestration trace they can challenge. No agent writes to source systems; every action still flows through the Workflow & Approval Service."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV11.E1 | Agent Orchestrator | LangGraph state machine with PostgresSaver checkpointing, intent routing, conflict resolution | 🔵 Future |
| CV11.E2 | Specialist Agents | Inventory Health Agent, Risk Agent, Optimization Agent (then Procurement, Master Data, Narrative) as subgraphs | 🔵 Future |
| CV11.E3 | Orchestration Trace UI | Live trace of agent steps, tool calls, evidence, and confidence — surfaced on the Agent Console | 🔵 Future |
| CV11.E4 | Agent Eval Framework | Per-agent eval suites for tool-use correctness, faithfulness, and grounding ([ADR-014](../../decisions.md#adr-014--eval-driven-development-for-ai-features)) | 🔵 Future |

---

## Done Condition

When CV11 activates:

- The orchestrator can route a question to 1–N agents, collect structured envelopes, resolve conflicts, and present one governed recommendation.
- Each agent has scope, input/output contracts, permission model, and audit log.
- The Agent Console surfaces live orchestration traces and per-agent KPIs.
- All agent decisions still route through CV6 ([Workflow & Approval](../cv6-workflow-approval/index.md)) for any side effect.
- Eval suites cover ≥ 80% of the question types observed in production over the previous 30 days.

---

## Out of Scope

- Autonomous agents acting without explicit user trigger — Future / Radar.
- Multi-agent debate / self-critique loops — Future.
- Long-term per-agent memory / "learning" — Future. The feedback loop remains accept/reject capture into a table.

---

**See also:** [Roadmap](../index.md) · [CV5 Governed Conversational Analyst](../cv5-conversational-analyst/index.md) · [CV6 Workflow & Approval](../cv6-workflow-approval/index.md) · [ADR-006 LangGraph + PostgresSaver](../../decisions.md#adr-006--agent-orchestration-with-langgraph--postgressaver)
