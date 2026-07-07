[< CV5 Governed Conversational Analyst](../index.md)

# CV5.E2 — Read-Only Q&A with Tool Invocation

**CV:** [CV5 — Governed Conversational Analyst](../index.md)
**Status:** 🟢 In Progress — non-streaming governed path delivered
**Depends on:** CV5.E1
**Design:** [ADR-032](../../../decisions.md#adr-032--cv5-conversational-analyst-litellm-sdk-in-process-linear-orchestrator-langgraphpostgressaver-deferred)

---

## What This Is

A single-orchestrator LangGraph state machine routes a user question to one or more tools and composes a grounded answer. Read-only. Streams via SSE. PostgresSaver persists checkpoints so a crashed run can resume from the right step ([ADR-006](../../../decisions.md#adr-006--agent-orchestration-with-langgraph--postgressaver)).

Per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that): MVP "Ask SmartInv" is **one governed tool**, not seven agents. Multi-agent lives in CV11.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV5.E2.S1 | Orchestrator: plan → tool calls → composer → **grounding validator** → finalizer (linear Python, not LangGraph — ADR-032) | ✅ Done |
| CV5.E2.S2 | PostgresSaver checkpointer wired to the `agent` schema | ⏸ Deferred (ADR-032) — guarantee recorded, not dropped |
| CV5.E2.S3 | `POST /agents/run` returning the answer envelope (JSON now; **SSE streaming** pending) | 🛠 Partial |
| CV5.E2.S4 | Ask SmartInv chat: `/analyst` page **+ global topbar launcher** (⌘K slide-over, usable from any screen). JSON now; live evidence via the trace stream lands with S3 | ✅ Done |
| CV5.E2.S5 | Conversation history persisted in `agent.conversations` (Postgres) | 📥 Backlog |
| CV5.E2.S6 | Suggested prompts side panel (5 starter prompts) | 📥 Backlog |

---

## Done Condition

- Planner asks a question and receives a streamed grounded answer in under 6 seconds for typical queries.
- A crashed orchestrator process can resume from checkpoint without losing the user's question.
- The answer always carries the envelope from CV3.E3 / CV5.E1.

---

## Out of Scope

- Multi-agent orchestration — **CV11**.
- Conversational dashboard / report creation — Phase 2 (deferred per AGENTS.md).
- Write actions through chat — Phase 2 (deferred per AGENTS.md).

---

**See also:** [CV5](../index.md) · [CV5.E1](../cv5-e1-llm-gateway-tool-catalog/index.md) · [CV5.E3](../cv5-e3-evidence-strip-source-links/index.md) · [CV11](../../cv11-multi-agent-orchestration/index.md)
