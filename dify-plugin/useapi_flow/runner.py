"""Glue between a Dify Tool and the handlers: credentials in, Dify messages out."""

from __future__ import annotations

from collections.abc import Generator, Mapping
from typing import Any

from .client import Client
from .handlers import HANDLERS, Ctx, Out


def make_context(credentials: Mapping[str, Any]) -> Ctx:
    token = str(credentials.get("useapi_token") or "")
    email = str(credentials.get("email") or "").strip() or None
    return Ctx(client=Client(token), default_email=email)


def to_message(tool: Any, out: Out) -> Any:
    if out.kind == "text":
        return tool.create_text_message(out.value)
    if out.kind == "json":
        return tool.create_json_message(out.value)
    if out.kind == "var":
        return tool.create_variable_message(out.name, out.value)
    if out.kind == "blob":
        return tool.create_blob_message(out.value, meta=out.meta)
    if out.kind == "link":
        return tool.create_link_message(out.value)
    raise ValueError(f"unknown output kind {out.kind}")


def is_empty(value: Any) -> bool:
    """Dify's agent runtime rejects a variable or text message with an empty value as a tool invoke error."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set, bytes)):
        return len(value) == 0
    return False


def outputs(ctx: Ctx, name: str, tool_parameters: dict[str, Any]) -> Generator[Out, None, None]:
    """The handler's outputs, made safe for Dify agents.

    - Empty variables, texts and links are dropped (False and 0 are kept: they are values).
    - An empty JSON value is wrapped, so the JSON message is never empty.
    - A readable text always comes first: outputs before the handler's first text wait for it.
    """
    pending: list[Out] = []
    said = False
    for out in HANDLERS[name](ctx, dict(tool_parameters or {})):
        if out.kind in ("var", "text", "link") and is_empty(out.value):
            continue
        if out.kind == "json" and is_empty(out.value):
            out = Out("json", {"result": out.value if out.value is not None else "ok"})
        if said:
            yield out
        elif out.kind == "text":
            said = True
            yield out
            yield from pending
            pending = []
        else:
            pending.append(out)
    if pending:
        yield Out("text", "Done.")
        yield from pending


def invoke(tool: Any, name: str, tool_parameters: dict[str, Any]) -> Generator[Any, None, None]:
    ctx = make_context(tool.runtime.credentials)
    for out in outputs(ctx, name, tool_parameters):
        yield to_message(tool, out)
