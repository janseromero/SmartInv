"""Unit tests for the SourceWriter seam (CV6.E4)."""

from __future__ import annotations

from api.dispatch.writer import EchoSourceWriter, SourceWriter, WriteReceipt


def test_echo_writer_is_deterministic_and_idempotent() -> None:
    writer = EchoSourceWriter()
    first = writer.write(operation="min_max_change", payload={"min": 1}, idempotency_key="rec-1")
    second = writer.write(operation="min_max_change", payload={"min": 1}, idempotency_key="rec-1")
    assert isinstance(first, WriteReceipt)
    assert first.external_id == second.external_id


def test_echo_writer_distinguishes_idempotency_keys() -> None:
    writer = EchoSourceWriter()
    a = writer.write(operation="transfer", payload={}, idempotency_key="rec-a")
    b = writer.write(operation="transfer", payload={}, idempotency_key="rec-b")
    assert a.external_id != b.external_id


def test_echo_writer_satisfies_protocol() -> None:
    assert isinstance(EchoSourceWriter(), SourceWriter)
