"""Linear governed orchestrator for "Ask SmartInv" (CV5.E2, slice 1).

Flow: plan (select tools) -> execute tools (deterministic, scoped, audited) ->
compose (answer from tool facts) -> validate (grounding) -> finalize (envelope).

Deliberately a straight Python pipeline, not LangGraph: with no branching and no
durable checkpointing at MVP (ADR-032), a graph engine would be ceremony. The
planner/composer are injected so the real LLM path and a deterministic stub
share one code path — the stub is what keeps CI green without an API key.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.agent.catalog import ToolSpec, list_tools, run_tool
from api.agent.grounding import check_grounded, expand_allowed
from api.auth.models import CurrentUser
from api.contracts.llm_gateway import LLMGateway, LLMMessage

# Answer returned when composition cannot be grounded — we never ship numbers we
# cannot trace, so we say so instead (fail closed).
UNGROUNDED_FALLBACK = (
    "I can't answer that reliably from the governed data right now — the drafted "
    "answer referenced figures I couldn't trace to a tool result."
)


@dataclass(frozen=True)
class Fact:
    """One grounded metric surfaced to the composer and the evidence strip."""

    key: str
    label: str
    value: float
    source: str


class Planner(Protocol):
    """Selects which catalog tools to run for a question."""

    def plan(self, question: str, tools: list[ToolSpec]) -> list[str]: ...


class Composer(Protocol):
    """Writes a natural-language answer grounded in the given facts."""

    def compose(self, question: str, facts: list[Fact]) -> str: ...


class EvidenceChip(BaseModel):
    metric: str
    label: str
    value: float
    source: str


class ToolCallRef(BaseModel):
    name: str
    version: str
    source: str


class AgentAnswer(BaseModel):
    """The governed answer envelope (mirrors the CV3 recommendation envelope)."""

    answer: str
    grounded: bool
    confidence: float
    model: str
    tool_calls: list[ToolCallRef]
    evidence: list[EvidenceChip]


def run_agent(
    session: Session,
    user: CurrentUser,
    tenant_id: uuid.UUID,
    question: str,
    planner: Planner,
    composer: Composer,
    model: str,
) -> AgentAnswer:
    """Answer ``question`` over governed tools, failing closed if ungrounded."""
    tools = list_tools()
    selected = planner.plan(question, tools)
    if not selected:  # safe default: a portfolio question can touch every tool
        selected = [spec.name for spec in tools]

    facts: list[Fact] = []
    tool_calls: list[ToolCallRef] = []
    for name in selected:
        output = run_tool(session, user, name, tenant_id)
        tool_calls.append(
            ToolCallRef(name=output.tool, version=output.version, source=output.source)
        )
        for key, value in output.facts.items():
            facts.append(
                Fact(key=key, label=output.labels.get(key, key), value=value, source=output.source)
            )

    allowed = expand_allowed([f.value for f in facts])
    answer = composer.compose(question, facts)
    result = check_grounded(answer, allowed)
    if not result.grounded:
        # Retry once, then fail closed rather than ship untraceable numbers.
        answer = composer.compose(question, facts)
        result = check_grounded(answer, allowed)
        if not result.grounded:
            return AgentAnswer(
                answer=UNGROUNDED_FALLBACK,
                grounded=False,
                confidence=0.0,
                model=model,
                tool_calls=tool_calls,
                evidence=[
                    EvidenceChip(metric=f.key, label=f.label, value=f.value, source=f.source)
                    for f in facts
                ],
            )

    return AgentAnswer(
        answer=answer,
        grounded=True,
        confidence=0.9 if facts else 0.3,
        model=model,
        tool_calls=tool_calls,
        evidence=[
            EvidenceChip(metric=f.key, label=f.label, value=f.value, source=f.source) for f in facts
        ],
    )


# --- deterministic stubs (tests + no-key dev) --------------------------------


class KeywordPlanner:
    """Selects tools whose name/description overlaps the question keywords."""

    def plan(self, question: str, tools: list[ToolSpec]) -> list[str]:
        q = question.lower()
        selected = [spec.name for spec in tools if any(token in q for token in _keywords(spec))]
        return selected


def _keywords(spec: ToolSpec) -> set[str]:
    domain = spec.name.split(".", 1)[0]
    extra = {"risk": {"risk", "downtime", "critical", "spare"}}.get(domain, set())
    inventory = {"inventory": {"inventory", "stock", "excess", "obsolete", "health", "item"}}.get(
        domain, set()
    )
    return {domain} | extra | inventory


class TemplateComposer:
    """Grounded-by-construction answer: restates the tool facts verbatim."""

    def compose(self, question: str, facts: list[Fact]) -> str:
        if not facts:
            return "No governed data was available to answer that."
        lines = [f"{f.label}: {_fmt(f.value)}" for f in facts]
        return "Here is what the governed data shows. " + "; ".join(lines) + "."


def _fmt(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.2f}"


# --- LLM-backed planner / composer -------------------------------------------

_PLAN_SYSTEM = (
    "You route a user question to data tools. Reply with ONLY a JSON array of "
    "tool names to call, chosen from the provided list. No prose."
)

_COMPOSE_SYSTEM = (
    "You are SmartInv's governed analyst. Answer the user's question using ONLY "
    "the FACTS provided. Never invent or estimate numbers. Every number in your "
    "answer must be copied exactly from a FACT value. Be concise."
)


class LLMPlanner:
    """Tool selection via the LLM; falls back to all tools on parse failure."""

    def __init__(self, gateway: LLMGateway, model: str) -> None:
        self._gateway = gateway
        self._model = model

    def plan(self, question: str, tools: list[ToolSpec]) -> list[str]:
        catalog = "\n".join(f"- {spec.name}: {spec.description}" for spec in tools)
        messages = [
            LLMMessage(role="system", content=_PLAN_SYSTEM),
            LLMMessage(role="user", content=f"Tools:\n{catalog}\n\nQuestion: {question}"),
        ]
        raw = self._gateway.complete(messages=messages, model=self._model).content
        valid = {spec.name for spec in tools}
        try:
            names = json.loads(raw)
            return [n for n in names if n in valid]
        except (json.JSONDecodeError, TypeError):
            return [spec.name for spec in tools]


class LLMComposer:
    """Grounded answer composition via the LLM."""

    def __init__(self, gateway: LLMGateway, model: str, temperature: float = 0.0) -> None:
        self._gateway = gateway
        self._model = model
        self._temperature = temperature

    def compose(self, question: str, facts: list[Fact]) -> str:
        fact_lines = "\n".join(f"- {f.label} = {_fmt(f.value)}" for f in facts)
        messages = [
            LLMMessage(role="system", content=_COMPOSE_SYSTEM),
            LLMMessage(role="user", content=f"FACTS:\n{fact_lines}\n\nQuestion: {question}"),
        ]
        return self._gateway.complete(
            messages=messages, model=self._model, temperature=self._temperature
        ).content
