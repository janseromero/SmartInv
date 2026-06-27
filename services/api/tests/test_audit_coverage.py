"""Regression coverage for CV6.E3 audit instrumentation.

This is intentionally a static guardrail: every mutating router endpoint must
call the audit service directly or through a small local helper. It prevents new
state-changing API routes from landing silently without an audit event.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROUTERS_DIR = Path("services/api/src/api/routers")
MUTATING_METHODS = {"post", "put", "patch", "delete"}
# Dev login mints a local token and is intentionally outside product audit.
EXEMPT_MODULES = {"dev_auth.py"}
AUDIT_CALLS = {"record_audit_event", "_audit_admin_job"}


def _is_mutating_route(decorator: ast.expr) -> bool:
    call = decorator if isinstance(decorator, ast.Call) else None
    if call is None or not isinstance(call.func, ast.Attribute):
        return False
    return (
        isinstance(call.func.value, ast.Name)
        and call.func.value.id == "router"
        and call.func.attr in MUTATING_METHODS
    )


def _calls_audit(function: ast.FunctionDef) -> bool:
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in AUDIT_CALLS
        ):
            return True
    return False


def test_every_state_changing_router_endpoint_records_audit_event() -> None:
    missing: list[str] = []
    for path in sorted(ROUTERS_DIR.glob("*.py")):
        if path.name in EXEMPT_MODULES or path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if any(_is_mutating_route(decorator) for decorator in node.decorator_list):
                if not _calls_audit(node):
                    missing.append(f"{path.name}:{node.name}")

    assert missing == [], "Mutating endpoints without audit coverage: " + ", ".join(missing)
