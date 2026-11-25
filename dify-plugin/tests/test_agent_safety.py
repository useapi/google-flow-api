"""Dify's agent runtime treats a variable (or text) message with an empty value as a
tool invoke error, so no tool may emit one in any path."""

from __future__ import annotations

import pytest
from test_tools import CASES, CHAT, JOB, VID, chat, job, video_media

from fakes import make_ctx
from useapi_flow import runner
from useapi_flow.client import UseapiError

JOB_TOOLS = {
    "generate_video": {"prompt": "x"},
    "extend_video": {"prompt": "x", "video": VID},
    "upscale_video": {"video": VID},
    "get_job": {"jobid": JOB},
}

STATES = {
    "completed": job(),
    "completed_no_media": job(media=[]),
    "completed_no_url": job(media=[video_media(url=None)]),
    "created": job(status="created"),
    "started": job(status="started"),
}


def assert_clean(items):
    for out in items:
        if out.kind in ("var", "text", "link"):
            assert not runner.is_empty(out.value), out
        if out.kind == "json":
            assert out.value not in ({}, [], None), out
    texts = [o for o in items if o.kind == "text"]
    assert texts and texts[0].value.strip(), "a non-empty text comes first for agents"
    assert items[0].kind == "text"


@pytest.mark.parametrize("state", list(STATES))
@pytest.mark.parametrize("name", list(JOB_TOOLS))
def test_job_tools_never_emit_empty(name, state):
    record = STATES[state]
    ctx, _, _ = make_ctx([("POST", "", record), ("GET", "jobs/", record)])
    items = list(runner.outputs(ctx, name, {**JOB_TOOLS[name], "max_wait_seconds": 30, "return_file": False}))
    assert_clean(items)
    if record["status"] in ("created", "started"):
        assert JOB in items[0].value and "get_job" in items[0].value
        assert any(o.kind == "var" and o.name == "jobid" and o.value == JOB for o in items)


@pytest.mark.parametrize("name", list(JOB_TOOLS))
def test_failed_job_raises_not_empty(name):
    record = job(status="failed", error="API error: 500")
    ctx, _, _ = make_ctx([("POST", "", record), ("GET", "jobs/", record)])
    with pytest.raises(UseapiError, match="API error: 500"):
        list(runner.outputs(ctx, name, JOB_TOOLS[name]))


@pytest.mark.parametrize("state", ["idle", "running", "waiting_approval", "failed"])
@pytest.mark.parametrize("name", ["agent_chat", "agent_get_chat", "agent_answer_approval"])
def test_agent_tools_never_emit_empty(name, state):
    record = chat(state, text="")
    params = {"message": "x", "chat_id": CHAT, "decision": "approve", "max_wait_seconds": 20}
    ctx, _, _ = make_ctx([("POST", "", {"chatId": CHAT, "status": "running"}), ("GET", "agent/chats/", record)])
    assert_clean(list(runner.outputs(ctx, name, params)))


@pytest.mark.parametrize("name,params", [(c[0], c[1]) for c in CASES], ids=[c[0] for c in CASES])
def test_every_tool_with_empty_api_answers(name, params):
    """Even when the API answers {} everywhere, nothing empty reaches Dify."""
    ctx, _, _ = make_ctx([("GET", "accounts", {"john@gmail.com": {"health": "OK"}})])
    try:
        items = list(runner.outputs(ctx, name, params))
    except UseapiError as e:  # a readable error is fine; an empty message is not
        assert str(e).strip()
        return
    assert_clean(items)
