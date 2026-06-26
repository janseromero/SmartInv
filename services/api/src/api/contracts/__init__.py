"""Core service contracts (CV1.E7 / ADR-022).

The four ``typing.Protocol`` seams that keep domain code independent of
infrastructure choices (AR2). Domain code imports only these protocols and the
value objects; concrete implementations live in :mod:`api.infra` and are wired
by the providers there.
"""

from api.contracts.llm_gateway import LLMGateway, LLMMessage, LLMResponse
from api.contracts.object_store import ObjectNotFoundError, ObjectStore
from api.contracts.search_index import SearchHit, SearchIndex
from api.contracts.workflow_engine import (
    ApprovalStep,
    InvalidApprovalPathError,
    InvalidWorkflowTransitionError,
    WorkflowEngine,
    WorkflowHandle,
    WorkflowNotFoundError,
)

__all__ = [
    "LLMGateway",
    "LLMMessage",
    "LLMResponse",
    "ObjectNotFoundError",
    "ObjectStore",
    "SearchHit",
    "SearchIndex",
    "ApprovalStep",
    "InvalidApprovalPathError",
    "InvalidWorkflowTransitionError",
    "WorkflowEngine",
    "WorkflowHandle",
    "WorkflowNotFoundError",
]
