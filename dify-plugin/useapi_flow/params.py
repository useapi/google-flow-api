"""Read Dify tool parameters defensively.

Workflow variables can arrive as strings, numbers, lists or JSON text, so
every reader accepts the common shapes and normalises them.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .client import UseapiError

_SPLIT_RE = re.compile(r"[\s,]+")


def text(p: dict[str, Any], name: str) -> str | None:
    value = p.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def required(p: dict[str, Any], name: str, label: str | None = None) -> str:
    value = text(p, name)
    if not value:
        raise UseapiError(f"Parameter '{label or name}' is required.")
    return value


def flag(p: dict[str, Any], name: str, default: bool | None = None) -> bool | None:
    value = p.get(name)
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in ("true", "1", "yes", "y", "on"):
        return True
    if lowered in ("false", "0", "no", "n", "off"):
        return False
    return default


def number(p: dict[str, Any], name: str, default: int | None, lo: int, hi: int) -> int | None:
    value = p.get(name)
    if value is None or value == "":
        return default
    try:
        result = int(float(value))
    except (TypeError, ValueError) as e:
        raise UseapiError(f"Parameter '{name}' must be a number.") from e
    return max(lo, min(hi, result))


def items(p: dict[str, Any], name: str, split_spaces: bool = True) -> list[str]:
    """A list from a list, a JSON array string, or text separated by new lines (and commas/spaces)."""
    value = p.get(name)
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    raw = str(value).strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except ValueError:
            pass
    parts = _SPLIT_RE.split(raw) if split_spaces else re.split(r"[\r\n]+", raw)
    return [part.strip() for part in parts if part.strip()]


def json_list(p: dict[str, Any], name: str) -> list[Any] | None:
    value = p.get(name)
    if value is None or value == "":
        return None
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(str(value))
    except ValueError as e:
        raise UseapiError(f"Parameter '{name}' must be a JSON array.") from e
    if not isinstance(parsed, list):
        raise UseapiError(f"Parameter '{name}' must be a JSON array.")
    return parsed


def put(body: dict[str, Any], key: str, value: Any) -> None:
    """Add a value to a request body only when it is set."""
    if value is None or value == "" or value == []:
        return
    body[key] = value


def files(p: dict[str, Any], name: str) -> list[Any]:
    """Dify file objects from a `file` or `files` parameter (one object or a list)."""
    value = p.get(name)
    if value is None or value == "" or value == []:
        return []
    if isinstance(value, (list, tuple)):
        return [v for v in value if v is not None]
    return [value]
