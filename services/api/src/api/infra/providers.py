"""Composition root: build concrete implementations of the service contracts.

These are the only functions that name a concrete implementation. Everything
else depends on the protocols in :mod:`api.contracts`. Swapping an implementation
(e.g. EchoLLMGateway -> LiteLLMGateway in CV5) changes only this module.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from api.contracts.llm_gateway import LLMGateway
from api.contracts.object_store import ObjectStore
from api.contracts.search_index import SearchIndex
from api.contracts.workflow_engine import WorkflowEngine
from api.infra.llm_gateway import EchoLLMGateway
from api.infra.object_store import S3ObjectStore
from api.infra.search_index import InMemorySearchIndex
from api.infra.workflow_engine import PostgresWorkflowEngine


def get_object_store() -> ObjectStore:
    return S3ObjectStore.from_settings()


def get_llm_gateway() -> LLMGateway:
    # Echo gateway until CV5.E1 wires LiteLLM.
    return EchoLLMGateway()


def get_search_index() -> SearchIndex:
    # In-memory until CV2 wires the pg_trgm-backed index.
    return InMemorySearchIndex()


def get_workflow_engine(session: Session) -> WorkflowEngine:
    return PostgresWorkflowEngine(session)
