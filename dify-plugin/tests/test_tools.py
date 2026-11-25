"""Every tool against a mocked HTTP layer: method, path, query and body."""

from __future__ import annotations

import base64

import pytest

from fakes import FakeResponse, make_ctx, outs, run, vars_of
from useapi_flow import runner
from useapi_flow.client import UseapiError
from useapi_flow.handlers import HANDLERS, account_of

EMAIL = "john@gmail.com"
HEX = EMAIL.encode().hex()
IMG = f"user:12345-email:{HEX}-image:ff9aa5cc-0000-4000-8000-000000000001"
IMG2 = f"user:12345-email:{HEX}-image:ff9aa5cc-0000-4000-8000-000000000002"
VID = f"user:12345-email:{HEX}-video:a1d95d21-75d2-482d-a354-14ef8802ce66"
VID2 = f"user:12345-email:{HEX}-video:a1d95d21-75d2-482d-a354-14ef8802ce67"
CHAR = f"user:12345-email:{HEX}-character:f470f1b5-0000-4000-8000-000000000003-imgs:1"
JOB = "j1117123456789304152v-u12345-email:john@gmail.com-bot:google-flow"
CHAT = (
    "c-u12345-email:john@gmail.com-project:f166200a-ea22-461a-bc68-47ff6d3ee500-chat:2a0f1973-d554-4fbc-aa6b-0c372edf182e-bot:google-flow"
)
VIDEO_URL = "https://flow-content.google/video/a1d95d21?Expires=1&KeyName=k&Signature=s"
IMAGE_URL = "https://flow-content.google/image/ee2a8a64?Expires=1&KeyName=k&Signature=s"
NOWAIT = {"wait": False, "return_file": False}


def video_media(ref=VID, url=VIDEO_URL, ok=True):
    status = "MEDIA_GENERATION_STATUS_SUCCESSFUL" if ok else "MEDIA_GENERATION_STATUS_FAILED"
    item = {
        "mediaGenerationId": ref,
        "mediaMetadata": {"mediaStatus": {"mediaGenerationStatus": status}},
        "video": {"dimensions": {"length": "8s"}},
    }
    if url:
        item["videoUrl"] = url
    return item


def image_media(ref=IMG, url=IMAGE_URL, b64=None):
    gen = {"mediaGenerationId": ref, "fifeUrl": url}
    if b64:
        gen["encodedImage"] = b64
    return {"image": {"generatedImage": gen}}


def job(status="completed", kind="video", media=None, **extra):
    record = {"jobid": JOB, "type": kind, "status": status, "request": {"email": EMAIL}}
    if status == "completed":
        record["response"] = {"media": media if media is not None else [video_media()]}
    record.update(extra)
    return record


def chat(status="idle", media=None, approval=None, text="Here is your video."):
    return {
        "chatId": CHAT,
        "email": EMAIL,
        "status": status,
        "pendingApproval": approval,
        "lastError": None,
        "turns": [
            {
                "turn": 1,
                "message": {"text": "hi"},
                "agent": [
                    {"kind": "text", "text": text, "ui": {"big": "layout"}},
                    {"kind": "tool_call", "tool": "ask_for_permission", "args": {"text": "This will cost 10 credits.", "total_cost": 10}},
                ],
                "media": media or [],
            }
        ],
    }


class FakeFile:
    def __init__(self, blob=b"img", mime="image/png", filename="a.png", extension=".png"):
        self.blob = blob
        self.mime_type = mime
        self.filename = filename
        self.extension = extension


UPLOAD_OK = {"mediaGenerationId": {"mediaGenerationId": IMG}, "email": EMAIL}

# name, params, method, path, expected query subset, expected body subset
CASES = [
    ("list_accounts", {}, "GET", "accounts", {}, None),
    ("get_account", {"email": EMAIL}, "GET", f"accounts/{EMAIL}", {}, None),
    ("list_jobs", {"options": "executing"}, "GET", "jobs", {"options": "executing"}, None),
    ("get_job", {"jobid": JOB, **NOWAIT}, "GET", f"jobs/{JOB}", {}, None),
    (
        "generate_video",
        {"prompt": "A boat", "aspect_ratio": "portrait", "duration": 8, "count": 2, **NOWAIT},
        "POST",
        "videos",
        {},
        {"prompt": "A boat", "model": "veo-3.1-lite", "aspectRatio": "portrait", "duration": 8, "count": 2, "async": True},
    ),
    (
        "extend_video",
        {"prompt": "It sails away", "video": VID, "duration": 5, "resolution": "360p", **NOWAIT},
        "POST",
        "videos/extend",
        {},
        {
            "prompt": "It sails away",
            "mediaGenerationId": VID,
            "model": "omni-flash-1.2",
            "duration": 5,
            "resolution": "360p",
            "count": 1,
            "async": True,
        },
    ),
    (
        "upscale_video",
        {"video": VID, "resolution": "4K", **NOWAIT},
        "POST",
        "videos/upscale",
        {},
        {"mediaGenerationId": VID, "resolution": "4K", "async": True},
    ),
    (
        "generate_image",
        {"prompt": "A cat", "model": "nano-banana-2", "thinking_level": "low", "aspect_ratio": "1:1", "seed": 7, "return_file": False},
        "POST",
        "images",
        {},
        {"prompt": "A cat", "model": "nano-banana-2", "thinkingLevel": "low", "aspectRatio": "1:1", "seed": 7, "count": 1},
    ),
    ("upscale_image", {"image": IMG, "resolution": "4k"}, "POST", "images/upscale", {}, {"mediaGenerationId": IMG, "resolution": "4k"}),
    ("video_to_gif", {"video": VID}, "POST", "videos/gif", {}, {"mediaGenerationId": VID}),
    (
        "concatenate_videos",
        {"videos": f"{VID}\n{VID2}"},
        "POST",
        "videos/concatenate",
        {},
        {"media": [{"mediaGenerationId": VID}, {"mediaGenerationId": VID2}]},
    ),
    ("upload_image", {"file": FakeFile()}, "POST", "assets", {}, None),
    ("list_media", {"email": EMAIL, "project_id": "p1"}, "GET", f"assets/media/{EMAIL}", {"projectId": "p1"}, None),
    ("get_media", {"media_id": VID, "return_file": False}, "GET", f"assets/{VID}", {}, None),
    ("list_characters", {"email": EMAIL}, "GET", "characters", {"email": EMAIL}, None),
    ("list_voices", {"email": EMAIL, "source": "system"}, "GET", "voices", {"email": EMAIL, "source": "system"}, None),
    ("agent_chat", {"message": "Make a video", "wait": False}, "POST", "agent/chats", {}, {"message": "Make a video"}),
    ("agent_get_chat", {"chat_id": CHAT}, "GET", f"agent/chats/{CHAT}", {}, None),
    (
        "agent_answer_approval",
        {"chat_id": CHAT, "decision": "approve", "wait": False},
        "POST",
        f"agent/chats/{CHAT}/approval",
        {},
        {"decision": "approve"},
    ),
    ("agent_list_chats", {"email": EMAIL}, "GET", "agent/chats", {"email": EMAIL}, None),
]

ROUTES = [
    ("POST", "assets", UPLOAD_OK),
    ("POST", "videos/gif", {"encodedGif": base64.b64encode(b"GIF89a").decode()}),
    ("POST", "videos/concatenate", {"encodedVideo": base64.b64encode(b"mp4").decode()}),
    ("POST", "images/upscale", {"encodedImage": base64.b64encode(b"jpg").decode()}),
    ("POST", "images", {"jobId": JOB, "media": [image_media()]}),
    ("POST", "videos", job(status="created")),
    ("POST", "agent/chats", {"chatId": CHAT, "status": "running"}),
    ("GET", "agent/chats/", chat()),
    ("GET", "jobs/", job()),
]


def test_every_tool_has_a_case():
    assert {c[0] for c in CASES} == set(HANDLERS)


@pytest.mark.parametrize("name,params,method,path,query,body", CASES, ids=[c[0] for c in CASES])
def test_request(name, params, method, path, query, body):
    ctx, session, _ = make_ctx(ROUTES)
    items = list(runner.outputs(ctx, name, params))
    assert items and items[0].kind == "text" and items[0].value.strip()
    call = next(c for c in session.calls if c.method == method and c.path == path)
    for key, value in query.items():
        assert call.query.get(key) == value, (call, key)
    if body is not None:
        for key, value in body.items():
            assert call.body.get(key) == value, (call.body, key)
    assert call.headers["User-Agent"] == "dify-plugin-google-flow-useapi/0.1.0"
    assert call.headers["Authorization"] == "Bearer user:12345-test"


# --------------------------------------------------------------- multiple Google accounts: rotation and pinning


@pytest.mark.parametrize(
    "name,params,path",
    [
        ("generate_video", {"prompt": "x", **NOWAIT}, "videos"),
        ("generate_image", {"prompt": "x", "return_file": False}, "images"),
        ("agent_chat", {"message": "x", "wait": False}, "agent/chats"),
    ],
)
def test_empty_email_is_left_out_so_useapi_rotates(name, params, path):
    ctx, session, _ = make_ctx(ROUTES)
    run(HANDLERS[name], ctx, params)
    call = next(c for c in session.calls if c.method == "POST" and c.path == path)
    assert "email" not in call.body


@pytest.mark.parametrize(
    "name,params,path",
    [
        ("generate_video", {"prompt": "x", **NOWAIT}, "videos"),
        ("generate_image", {"prompt": "x", "return_file": False}, "images"),
        ("agent_chat", {"message": "x", "wait": False}, "agent/chats"),
    ],
)
def test_given_or_default_email_is_sent(name, params, path):
    ctx, session, _ = make_ctx(ROUTES)
    run(HANDLERS[name], ctx, {**params, "email": "jane@gmail.com"})
    assert next(c for c in session.calls if c.path == path).body["email"] == "jane@gmail.com"
    ctx, session, _ = make_ctx(ROUTES, email="default@gmail.com")
    run(HANDLERS[name], ctx, params)
    assert next(c for c in session.calls if c.path == path).body["email"] == "default@gmail.com"


def test_upload_without_email_lets_useapi_pick_then_pins_the_rest():
    second = {"mediaGenerationId": {"mediaGenerationId": IMG2}, "email": EMAIL}
    ctx, session, _ = make_ctx([("POST", "assets", [UPLOAD_OK, second]), ("POST", "videos", job(status="created"))])
    run(HANDLERS["generate_video"], ctx, {"prompt": "x", "reference_image_files": [FakeFile(), FakeFile()], **NOWAIT})
    uploads = [c for c in session.calls if c.path.startswith("assets")]
    assert [c.path for c in uploads] == ["assets", f"assets/{EMAIL}"]
    assert uploads[0].data == b"img" and uploads[0].headers["Content-Type"] == "image/png"
    body = next(c for c in session.calls if c.path == "videos").body
    assert body["referenceImage_1"] == IMG and body["referenceImage_2"] == IMG2 and body["email"] == EMAIL


def test_reference_ids_pin_uploads_to_their_account_over_the_default():
    ctx, session, _ = make_ctx([("POST", "assets", UPLOAD_OK), ("POST", "videos", job(status="created"))], email="default@gmail.com")
    run(HANDLERS["generate_video"], ctx, {"prompt": "x", "start_image": IMG, "end_image_file": FakeFile(), **NOWAIT})
    upload = next(c for c in session.calls if c.path.startswith("assets"))
    assert upload.path == f"assets/{EMAIL}"
    body = next(c for c in session.calls if c.path == "videos").body
    assert body["startImage"] == IMG and body["endImage"] == IMG and body["email"] == EMAIL


def test_account_of_decodes_documented_ids():
    assert account_of(IMG) == EMAIL and account_of(CHAR) == EMAIL
    assert account_of("Kore") is None and account_of("user:1-email:zz-image:x") is None


def test_need_email_uses_the_only_account_and_lists_several():
    ctx, session, _ = make_ctx([("GET", "accounts", {EMAIL: {"health": "OK"}}), ("GET", "characters", {"characters": []})])
    run(HANDLERS["list_characters"], ctx, {})
    assert session.calls[-1].query["email"] == EMAIL
    ctx, _, _ = make_ctx([("GET", "accounts", {EMAIL: {}, "jane@gmail.com": {}})])
    with pytest.raises(UseapiError, match="Connected: john@gmail.com, jane@gmail.com"):
        run(HANDLERS["list_voices"], ctx, {})


def test_list_accounts_counts_healthy_accounts():
    accounts = {EMAIL: {"health": "OK"}, "jane@gmail.com": {"health": "OK"}, "old@gmail.com": {"health": "Signed out"}}
    ctx, _, _ = make_ctx([("GET", "accounts", accounts)])
    items = run(HANDLERS["list_accounts"], ctx, {})
    message = outs(items, "text")[0].value
    assert "3 Google account(s)" in message and "2 healthy" in message and "spreads new jobs" in message
    assert vars_of(items)["healthy_emails"] == [EMAIL, "jane@gmail.com"]


def test_get_account_reports_plan_and_hides_cookies():
    data = {
        "health": "OK",
        "accountCookies": [{"name": "HSID", "value": "secret"}],
        "flowCookies": [{"name": "OSID", "value": "secret"}],
        "credits": {"credits": 1250, "userPaygateTier": "PAYGATE_TIER_TWO"},
        "models": {"videoModels": [{"displayName": "Veo 3.1 - Lite"}, {"displayName": "Veo 3.1 - Lite"}]},
    }
    ctx, _, _ = make_ctx([("GET", "accounts/", data)])
    items = run(HANDLERS["get_account"], ctx, {"email": EMAIL})
    message = outs(items, "text")[0].value
    assert "Google AI Ultra $199" in message and "1250" in message
    assert "secret" not in str(outs(items, "json")[0].value)
    assert vars_of(items)["video_models"] == ["Veo 3.1 - Lite"]


# --------------------------------------------------------------- generation


def test_generation_polls_and_attaches_the_file_without_the_token():
    ctx, session, clock = make_ctx(
        [
            ("POST", "videos", job(status="created")),
            ("GET", "jobs/", [job(status="started"), job()]),
            ("GET", "/video/", FakeResponse(200, content=b"mp4data", headers={"Content-Type": "video/mp4"})),
        ]
    )
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert clock.sleeps == [10, 10]
    blob = outs(items, "blob")[0]
    assert blob.value == b"mp4data" and blob.meta == {"mime_type": "video/mp4", "filename": "google-flow-video.mp4"}
    download = next(c for c in session.calls if c.host == "flow-content.google")
    assert "Authorization" not in download.headers
    v = vars_of(items)
    assert v["media_ids"] == [VID] and v["file_urls"] == [VIDEO_URL] and v["jobid"] == JOB


def test_media_downloads_only_from_flow_content():
    bad = job(media=[video_media(url="https://evil.example.com/v.mp4")])
    ctx, session, _ = make_ctx([("POST", "videos", bad)])
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert not outs(items, "blob")
    assert any("could not be attached" in o.value for o in outs(items, "text"))
    assert all(c.host != "evil.example.com" for c in session.calls)


def test_expired_link_falls_back_to_the_url():
    ctx, _, _ = make_ctx([("POST", "videos", job()), ("GET", "/video/", FakeResponse(403, content=b"denied"))])
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert not outs(items, "blob") and any("Get media" in o.value for o in outs(items, "text"))


def test_still_running_after_max_wait():
    ctx, _, clock = make_ctx([("POST", "videos", job(status="created")), ("GET", "jobs/", job(status="started"))])
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert sum(clock.sleeps) == 120
    assert "get_job" in items[0].value and JOB in items[0].value and "Do not start" in items[0].value
    assert vars_of(items)["status"] == "started"


def test_max_wait_is_capped_at_420():
    ctx, _, clock = make_ctx([("POST", "videos", job(status="created")), ("GET", "jobs/", job(status="started"))])
    run(HANDLERS["generate_video"], ctx, {"prompt": "x", "max_wait_seconds": 9999})
    assert sum(clock.sleeps) == 420


def test_failed_job_raises_readable_error():
    failed = job(status="failed", error="All operations failed", response={"failureReasons": ["PUBLIC_ERROR_AUDIO_FILTERED"]})
    ctx, _, _ = make_ctx([("POST", "videos", job(status="created")), ("GET", "jobs/", failed)])
    with pytest.raises(UseapiError, match="audio filter") as e:
        run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert JOB in str(e.value)


def test_partly_failed_media_is_reported():
    ctx, _, _ = make_ctx([("POST", "videos", job(media=[video_media(), video_media(ref=VID2, url=None, ok=False)]))])
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x", "return_file": False})
    assert "made 1 video" in items[0].value and "failed" in items[0].value
    assert vars_of(items)["media_ids"] == [VID]


def test_retired_models_are_refused_before_any_call():
    ctx, session, _ = make_ctx()
    for model in ("veo-3.1-fast", "veo-3.1-quality", "omni-flash"):
        with pytest.raises(UseapiError, match="not offered"):
            run(HANDLERS["generate_video"], ctx, {"prompt": "x", "model": model})
    assert not session.calls


def test_end_image_needs_start_image():
    ctx, _, _ = make_ctx()
    with pytest.raises(UseapiError, match="start image"):
        run(HANDLERS["generate_video"], ctx, {"prompt": "x", "end_image": IMG})


def test_video_edit_sends_frames_and_no_duration():
    ctx, session, _ = make_ctx([("POST", "videos", job(status="created"))])
    params = {
        "prompt": "x",
        "model": "omni-flash-1.2",
        "reference_video": VID,
        "duration": 8,
        "start_frame": 24,
        "end_frame": 120,
        **NOWAIT,
    }
    run(HANDLERS["generate_video"], ctx, params)
    body = session.calls[-1].body
    assert body["referenceVideo_1"] == VID and body["startFrameIndex_1"] == 24 and body["endFrameIndex_1"] == 120
    assert "duration" not in body


def test_references_characters_and_voice():
    ctx, session, _ = make_ctx([("POST", "videos", job(status="created"))])
    params = {"prompt": "x", "reference_images": f"{IMG}, {IMG2}", "characters": CHAR, "voice": "Kore", **NOWAIT}
    run(HANDLERS["generate_video"], ctx, params)
    body = session.calls[-1].body
    assert body["referenceImage_1"] == IMG and body["referenceImage_2"] == IMG2
    assert body["character_1"] == CHAR and body["referenceAudio_1"] == "Kore"


def test_too_many_references():
    ctx, _, _ = make_ctx()
    with pytest.raises(UseapiError, match="at most 3"):
        run(HANDLERS["extend_video"], ctx, {"prompt": "x", "video": VID, "reference_images": "a b c d"})


def test_extend_with_veo_sends_no_omni_fields():
    ctx, session, _ = make_ctx([("POST", "videos/extend", job(status="created"))])
    run(
        HANDLERS["extend_video"],
        ctx,
        {"prompt": "x", "video": VID, "model": "veo-3.1-lite", "duration": 5, "reference_images": IMG, **NOWAIT},
    )
    body = session.calls[-1].body
    assert body["model"] == "veo-3.1-lite" and "duration" not in body and "referenceImage_1" not in body


def test_upscale_needs_a_video():
    ctx, _, _ = make_ctx()
    with pytest.raises(UseapiError, match="video_file"):
        run(HANDLERS["upscale_video"], ctx, {"resolution": "1080p"})


def test_upscale_uploads_a_video_file():
    ctx, session, _ = make_ctx(
        [
            ("POST", "assets", {"mediaGenerationId": {"mediaGenerationId": VID}, "email": EMAIL}),
            ("POST", "videos/upscale", job(status="created")),
        ]
    )
    run(HANDLERS["upscale_video"], ctx, {"video_file": FakeFile(b"mp4", "video/mp4", "a.mp4", ".mp4"), **NOWAIT})
    assert session.calls[0].headers["Content-Type"] == "video/mp4"
    assert session.calls[-1].body["mediaGenerationId"] == VID


def test_unsupported_upload_type_is_refused():
    ctx, session, _ = make_ctx()
    with pytest.raises(UseapiError, match="PNG, JPEG and WebP"):
        run(HANDLERS["upload_image"], ctx, {"file": FakeFile(b"x", "application/pdf", "a.pdf", ".pdf")})
    assert not session.calls


def test_upload_reads_the_type_from_the_extension():
    ctx, session, _ = make_ctx([("POST", "assets", UPLOAD_OK)])
    items = run(HANDLERS["upload_image"], ctx, {"file": FakeFile(b"x", None, "a.webp", ".webp"), "email": EMAIL})
    assert session.calls[0].path == f"assets/{EMAIL}" and session.calls[0].headers["Content-Type"] == "image/webp"
    assert vars_of(items)["media_id"] == IMG


def test_image_sync_answer_with_link_and_base64():
    b64 = base64.b64encode(b"jpegbytes").decode()
    ctx, session, _ = make_ctx(
        [
            ("POST", "images", {"jobId": JOB, "media": [image_media(), image_media(ref=IMG2, url=None, b64=b64)]}),
            ("GET", "/image/", FakeResponse(200, content=b"img1", headers={"Content-Type": "image/jpeg"})),
        ]
    )
    items = run(HANDLERS["generate_image"], ctx, {"prompt": "x", "count": 2})
    blobs = outs(items, "blob")
    assert [b.value for b in blobs] == [b"img1", b"jpegbytes"]
    assert "made 2 image" in items[0].value
    assert "(omitted)" in str(outs(items, "json")[0].value) and b64 not in str(outs(items, "json")[0].value)
    assert session.calls[0].timeout == 300 and "async" not in session.calls[0].body


def test_thinking_level_only_for_nano_banana_2():
    ctx, session, _ = make_ctx(ROUTES)
    run(HANDLERS["generate_image"], ctx, {"prompt": "x", "thinking_level": "low", "return_file": False})
    assert "thinkingLevel" not in session.calls[-1].body and session.calls[-1].body["model"] == "nano-banana-2-lite"


@pytest.mark.parametrize(
    "name,params,mime",
    [
        ("upscale_image", {"image": IMG}, "image/jpeg"),
        ("video_to_gif", {"video": VID}, "image/gif"),
        ("concatenate_videos", {"videos": f"{VID} {VID2}"}, "video/mp4"),
    ],
)
def test_base64_results_become_files(name, params, mime):
    ctx, _, _ = make_ctx(ROUTES)
    items = run(HANDLERS[name], ctx, params)
    assert outs(items, "blob")[0].meta["mime_type"] == mime


def test_concatenate_needs_two_and_takes_trims():
    ctx, session, _ = make_ctx(ROUTES)
    with pytest.raises(UseapiError, match="2 to 10"):
        run(HANDLERS["concatenate_videos"], ctx, {"videos": VID})
    media = [{"mediaGenerationId": VID, "trimEnd": 0.375}, {"mediaGenerationId": VID2, "trimStart": 0.458}]
    run(HANDLERS["concatenate_videos"], ctx, {"media_json": media})
    assert session.calls[-1].body == {"media": media}


def test_get_media_fresh_link_and_file():
    ctx, _, _ = make_ctx(
        [
            ("GET", "assets/", {"url": IMAGE_URL, "mediaGenerationId": IMG}),
            ("GET", "/image/", FakeResponse(200, content=b"i", headers={"Content-Type": "image/png"})),
        ]
    )
    items = run(HANDLERS["get_media"], ctx, {"media_id": IMG})
    assert outs(items, "link")[0].value == IMAGE_URL and outs(items, "blob")[0].meta["mime_type"] == "image/png"


def test_get_media_not_ready_is_readable():
    ctx, _, _ = make_ctx(
        [("GET", "assets/", FakeResponse(503, {"error": "Media is still processing", "code": 503}, headers={"Retry-After": "10"}))]
    )
    with pytest.raises(UseapiError, match="Retry after 10 seconds"):
        run(HANDLERS["get_media"], ctx, {"media_id": VID})


# --------------------------------------------------------------- Google Flow agent


def test_agent_chat_new_chat_follows_the_turn():
    ctx, session, clock = make_ctx(
        [
            ("POST", "agent/chats", {"chatId": CHAT, "status": "running"}),
            ("GET", "agent/chats/", [chat("running"), chat("running"), chat("idle")]),
        ]
    )
    items = run(HANDLERS["agent_chat"], ctx, {"message": "Make a video", "email": EMAIL})
    assert session.calls[0].timeout == 150 and session.calls[0].body["email"] == EMAIL
    polls = [c for c in session.calls if c.method == "GET"]
    assert polls[0].query.get("media") == "false" and "media" not in polls[-1].query
    assert clock.sleeps == [10, 10]
    v = vars_of(items)
    assert v["chat_id"] == CHAT and v["status"] == "idle" and v["reply"] == "Here is your video."
    assert '"big"' not in str(outs(items, "json")[0].value)


def test_agent_chat_continues_a_chat_on_its_account():
    ctx, session, _ = make_ctx([("POST", "agent/chats/", {"chatId": CHAT, "status": "running"}), ("POST", "assets", UPLOAD_OK)])
    run(
        HANDLERS["agent_chat"],
        ctx,
        {"message": "again", "chat_id": CHAT, "reference_image_files": [FakeFile()], "voices": "Kore\nPuck", "wait": False},
    )
    assert session.calls[0].path == f"assets/{EMAIL}"
    post = session.calls[-1]
    assert post.path == f"agent/chats/{CHAT}/messages"
    assert post.body["referenceImage_1"] == IMG and post.body["referenceAudio_2"] == "Puck" and "email" not in post.body


def test_agent_waiting_approval_tells_the_agent_what_to_do():
    ctx, _, _ = make_ctx(
        [
            ("POST", "agent/chats", {"chatId": CHAT, "status": "running"}),
            ("GET", "agent/chats/", chat("waiting_approval", approval={"cost": 10})),
        ]
    )
    items = run(HANDLERS["agent_chat"], ctx, {"message": "Make a video"})
    assert "agent_answer_approval" in items[0].value and "10 credits" in items[0].value


def test_agent_get_chat_waits_for_queued_videos():
    queued = chat(media=[{"referenceId": VID, "type": "video", "status": "queued"}])
    ready = chat(media=[{"referenceId": VID, "type": "video", "status": "completed", "url": VIDEO_URL}])
    ctx, _, clock = make_ctx(
        [
            ("GET", "agent/chats/", [queued, queued, ready, ready]),
            ("GET", "/video/", FakeResponse(200, content=b"v", headers={"Content-Type": "video/mp4"})),
        ]
    )
    items = run(HANDLERS["agent_get_chat"], ctx, {"chat_id": CHAT, "wait": True, "return_file": True})
    assert clock.sleeps == [10, 10]
    assert vars_of(items)["file_urls"] == [VIDEO_URL] and outs(items, "blob")


def test_agent_approval_decision_is_checked():
    ctx, session, _ = make_ctx()
    with pytest.raises(UseapiError, match="approve, always or reject"):
        run(HANDLERS["agent_answer_approval"], ctx, {"chat_id": CHAT, "decision": "maybe"})
    assert not session.calls


def test_required_parameter_message():
    ctx, _, _ = make_ctx()
    with pytest.raises(UseapiError, match="Parameter 'prompt' is required"):
        run(HANDLERS["generate_video"], ctx, {})


# --------------------------------------------------------------- review fixes


def test_poll_survives_a_503_then_completes():
    ctx, _, clock = make_ctx(
        [
            ("POST", "videos", job(status="created")),
            ("GET", "jobs/", [FakeResponse(503, {"error": "down", "code": 503}), job()]),
            ("GET", "/video/", FakeResponse(200, content=b"v", headers={"Content-Type": "video/mp4"})),
        ]
    )
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert clock.sleeps == [10, 10] and outs(items, "blob")
    assert vars_of(items)["status"] == "completed"


def test_poll_with_only_errors_returns_the_jobid():
    ctx, _, clock = make_ctx([("POST", "videos", job(status="created")), ("GET", "jobs/", FakeResponse(503, {"error": "down", "code": 503}))])
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert sum(clock.sleeps) == 120
    assert JOB in items[0].value and "Do not start" in items[0].value
    assert vars_of(items)["jobid"] == JOB


def test_poll_still_raises_on_404():
    ctx, _, _ = make_ctx([("POST", "videos", job(status="created")), ("GET", "jobs/", FakeResponse(404, {"error": "Job not found", "code": 404}))])
    with pytest.raises(UseapiError, match="Not found"):
        run(HANDLERS["generate_video"], ctx, {"prompt": "x"})


def test_download_deadline_skips_files_and_keeps_urls():
    media = [video_media(), video_media()]
    ctx, session, clock = make_ctx([("POST", "videos", job(media=media)), ("GET", "/video/", FakeResponse(200, content=b"v"))])
    clock.t = 600  # past the 570 s overall deadline
    items = run(HANDLERS["generate_video"], ctx, {"prompt": "x"})
    assert not outs(items, "blob")
    assert not [c for c in session.calls if c.host == "flow-content.google"]
    assert any("not attached because of time" in o.value for o in outs(items, "text"))
    assert vars_of(items)["file_urls"] == [VIDEO_URL, VIDEO_URL]


def test_agent_running_media_is_pending():
    running = chat(media=[{"referenceId": VID, "type": "video", "status": "running"}])
    ready = chat(media=[{"referenceId": VID, "type": "video", "status": "completed", "url": VIDEO_URL}])
    ctx, _, clock = make_ctx([("GET", "agent/chats/", [running, running, ready, ready])])
    items = run(HANDLERS["agent_get_chat"], ctx, {"chat_id": CHAT, "wait": True})
    assert clock.sleeps == [10, 10] and vars_of(items)["file_urls"] == [VIDEO_URL]
    shown = run(HANDLERS["agent_get_chat"], make_ctx([("GET", "agent/chats/", running)])[0], {"chat_id": CHAT})
    assert "Videos finish" in shown[0].value


def test_agent_last_error_dict_is_formatted():
    failed = chat(status="failed")
    failed["lastError"] = {"turn": 1, "code": "RATE_LIMIT", "message": "Too many requests"}
    items = run(HANDLERS["agent_get_chat"], make_ctx([("GET", "agent/chats/", failed)])[0], {"chat_id": CHAT})
    assert "RATE_LIMIT Too many requests" in items[0].value and "'turn'" not in items[0].value
    failed["lastError"] = "plain text"
    items = run(HANDLERS["agent_get_chat"], make_ctx([("GET", "agent/chats/", failed)])[0], {"chat_id": CHAT})
    assert "failed: plain text." in items[0].value
