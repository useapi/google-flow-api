"""A fake requests.Session: records every request and answers from a route table."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from useapi_flow.client import BASE_URL, Client
from useapi_flow.handlers import Ctx


class FakeResponse:
    def __init__(self, status: int = 200, body: Any = None, content: bytes | None = None, headers: dict[str, str] | None = None):
        self.status_code = status
        self._body = body
        self.content = content if content is not None else (b"" if body is None else json.dumps(body).encode())
        self.headers = headers or {"Content-Type": "application/json"}

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", "replace")

    def json(self) -> Any:
        return json.loads(self.text)

    def iter_content(self, chunk_size: int = 65536):
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i : i + chunk_size]

    def close(self) -> None:
        pass


class Call:
    def __init__(self, method: str, url: str, params: dict | None, data: bytes | None, headers: dict):
        self.method = method
        parts = urlsplit(url)
        base = urlsplit(BASE_URL).path
        self.host = parts.hostname
        self.path = unquote(parts.path[len(base) + 1 :]) if parts.path.startswith(base) else parts.path
        self.raw_path = parts.path
        self.query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        self.query.update({k: str(v) for k, v in (params or {}).items()})
        self.headers = headers
        self.data = data
        self.body = None
        if data is not None and headers.get("Content-Type") == "application/json":
            self.body = json.loads(data)

    def __repr__(self) -> str:
        return f"{self.method} {self.path} {self.query} {self.body}"


class FakeSession:
    """routes: list of (method, path prefix, response or list of responses)."""

    def __init__(self, routes: list[tuple[str, str, Any]] | None = None):
        self.routes = routes or []
        self.calls: list[Call] = []

    def _answer(self, call: Call) -> FakeResponse:
        for _i, (method, prefix, answer) in enumerate(self.routes):
            if method == call.method and call.path.startswith(prefix):
                resp = (answer.pop(0) if len(answer) > 1 else answer[0]) if isinstance(answer, list) else answer
                return resp if isinstance(resp, FakeResponse) else FakeResponse(200, resp)
        return FakeResponse(200, {})

    def request(self, method, url, params=None, data=None, headers=None, timeout=None, allow_redirects=True):
        call = Call(method, url, params, data, headers or {})
        call.timeout = timeout
        self.calls.append(call)
        return self._answer(call)

    def get(self, url, headers=None, timeout=None, stream=False, allow_redirects=True):
        return self.request("GET", url, headers=headers, timeout=timeout, allow_redirects=allow_redirects)


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds


def make_ctx(routes=None, email: str | None = None) -> tuple[Ctx, FakeSession, FakeClock]:
    session = FakeSession(routes)
    clock = FakeClock()
    ctx = Ctx(client=Client("user:12345-test", session=session), default_email=email, sleep=clock.sleep, clock=clock.now)
    return ctx, session, clock


def run(handler, ctx, params):
    return list(handler(ctx, params))


def outs(items, kind):
    return [o for o in items if o.kind == kind]


def vars_of(items):
    return {o.name: o.value for o in items if o.kind == "var"}
