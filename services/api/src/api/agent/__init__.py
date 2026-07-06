"""Governed conversational analyst (CV5).

The agent package is the boundary between the LLM and SmartInv's data: a
versioned tool catalog (:mod:`api.agent.catalog`), a deterministic grounding
validator (:mod:`api.agent.grounding`), and a linear orchestrator
(:mod:`api.agent.orchestrator`). The LLM never touches the database — it only
selects catalog tools and composes an answer that the validator checks.
"""
