[< CV5 Governed Conversational Analyst](../index.md)

# CV5.E1 — LLM Gateway & Tool Catalog

**CV:** [CV5 — Governed Conversational Analyst](../index.md)
**Status:** 🟢 In Progress — gateway + first tools delivered
**Prerequisite for:** CV5.E2
**Design:** [ADR-032](../../../decisions.md#adr-032--cv5-conversational-analyst-litellm-sdk-in-process-linear-orchestrator-langgraphpostgressaver-deferred)

---

## What This Is

The platform layer for any LLM-driven feature. A LiteLLM proxy abstracts model vendor choice. A versioned tool catalog defines, in code, exactly what the LLM is allowed to call. Each tool ships with Pydantic input/output schemas, per-tenant + per-role scopes, and an owner.

The catalog *is* the boundary between the LLM and SmartInv's data ([AGENTS.md non-negotiables #2 and #3](../../../../AGENTS.md#architectural-non-negotiables)).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV5.E1.S1 | ~~LiteLLM proxy service~~ → **LiteLLM Python SDK in-process** (ADR-032) | ✅ Done |
| CV5.E1.S2 | `LLMGateway` implementation pointing to LiteLLM, with cost + latency tracking | 🛠 Partial — `LiteLLMGateway` done; token usage captured, per-run cost pending |
| CV5.E1.S3 | Pydantic tool I/O schemas (`ToolSpec`/`ToolOutput`) — in `api.agent.catalog` for MVP, extract to a package later | ✅ Done (in-app) |
| CV5.E1.S4 | Tool registry with version, scope, owner, evaluator pointer | ✅ Done (evaluator pointer pending) |
| CV5.E1.S5 | Scope enforcement at call time (tenant + role) with audit | ✅ Done |
| CV5.E1.S6 | Initial tools: `inventory.summary`, `risk.summary` (forecast/optimization tools pending) | 🛠 Partial |
| CV5.E1.S7 | Langfuse SDK wired into the gateway via LiteLLM's success/failure callbacks (registered once when `LANGFUSE_*` keys are present; no-op otherwise). Traces prompt/response/tokens/cost/latency for every analyst LLM call ([ADR-018](../../../decisions.md#adr-018--langfuse-cloud-free-tier-for-mvp-llm-observability)) | ✅ Done |

---

## Done Condition

- LiteLLM proxies all model traffic; switching vendor is a config change.
- The tool catalog refuses calls outside the caller's scope.
- Tool inputs and outputs are validated by Pydantic at every call.
- Langfuse traces every tool call with prompt, response, cost.

---

## Out of Scope

- Multi-agent orchestration — **CV11**.
- Tool versions older than the current active version — Future.
- Tool marketplace / third-party tools — Radar.

---

**See also:** [CV5](../index.md) · [CV5.E2](../cv5-e2-qa-tool-invocation/index.md) · [ADR-006](../../../decisions.md#adr-006--agent-orchestration-with-langgraph--postgressaver)
