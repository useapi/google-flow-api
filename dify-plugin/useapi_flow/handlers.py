"""One handler per Dify tool. Each handler yields Out items that runner.py turns
into Dify messages, so the handlers can be unit-tested without Dify.

API reference: https://useapi.net/docs/api-google-flow-v1
API catalog (models, inputs, errors): https://api.useapi.net/v1/google-flow/models
"""

from __future__ import annotations

import base64
import binascii
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from . import params as P
from .client import (
    AGENT_TIMEOUT,
    SETUP_ACCOUNT_URL,
    SUBMIT_TIMEOUT,
    SYNC_TIMEOUT,
    UPLOAD_TIMEOUT,
    Client,
    FileTooLarge,
    UseapiError,
    enc,
)

POLL_SECONDS = 10
DEFAULT_WAIT = 120  # agent friendly: a Dify agent turn stays short
MAX_WAIT = 420  # leaves room for file downloads under Dify's default 600 s plugin execution limit
DOWNLOAD_DEADLINE = 570  # seconds from the tool's start: no file download begins or runs past this
MAX_FILE_BYTES = 150 * 1024 * 1024
RUNNING = ("created", "started")  # job states before completed / failed

# Active models only (catalog lifecycle.status == "active"). Retiring models are not offered.
VIDEO_MODELS = ("veo-3.1-lite", "omni-flash-1.2", "veo-3.1-lite-low-priority")
EXTEND_MODELS = ("omni-flash-1.2", "veo-3.1-lite", "veo-3.1-lite-low-priority")
IMAGE_MODELS = ("nano-banana-2-lite", "nano-banana-2", "nano-banana-pro")
DEFAULT_VIDEO_MODEL = "veo-3.1-lite"
DEFAULT_EXTEND_MODEL = "omni-flash-1.2"
DEFAULT_IMAGE_MODEL = "nano-banana-2-lite"

UPLOAD_TYPES = {"image/png": 20, "image/jpeg": 20, "image/webp": 20, "video/mp4": 100}  # MB, per the catalog
EXT_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "mp4": "video/mp4"}

PLAN_NAMES = {
    "PAYGATE_TIER_NOT_PAID": "Free",
    "PAYGATE_TIER_ZERO": "Google AI Plus",
    "PAYGATE_TIER_ONE": "Google AI Pro",
    "PAYGATE_TIER_TIER1P5": "Google AI Ultra $99",
    "PAYGATE_TIER_TWO": "Google AI Ultra $199",
}

SECRET_KEYS = ("accountCookies", "flowCookies", "sessionData", "cookies")
BULKY_KEYS = ("encodedImage", "encodedVideo", "encodedGif", "ui")


@dataclass
class Out:
    kind: str  # text | json | var | blob | link
    value: Any
    name: str | None = None
    meta: dict[str, Any] | None = None


def text(value: str) -> Out:
    return Out("text", value)


def js(value: Any) -> Out:
    return Out("json", value if isinstance(value, (dict, list)) else {"result": value})


def var(name: str, value: Any) -> Out:
    return Out("var", value, name=name)


@dataclass
class Ctx:
    client: Client
    default_email: str | None = None
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    log: list[str] = field(default_factory=list)
    t0: float = field(init=False, default=0.0)  # the tool's start, for the overall download deadline

    def __post_init__(self) -> None:
        self.t0 = self.clock()

    def download_budget(self) -> float:
        """Seconds left before files must stop being attached."""
        return self.t0 + DOWNLOAD_DEADLINE - self.clock()

    def email(self, p: dict[str, Any]) -> str | None:
        """The tool's email, else the credentials' default, else None (useapi.net then picks an account)."""
        return P.text(p, "email") or self.default_email

    def get(self, path: str, **kw: Any) -> Any:
        return self.client.request("GET", path, **kw)

    def post(self, path: str, body: dict[str, Any], **kw: Any) -> Any:
        return self.client.request("POST", path, body=body, **kw)


Handler = Callable[[Ctx, dict[str, Any]], Iterator[Out]]
HANDLERS: dict[str, Handler] = {}


def tool(name: str) -> Callable[[Handler], Handler]:
    def register(fn: Handler) -> Handler:
        HANDLERS[name] = fn
        return fn

    return register


def done(message: str, data: Any) -> Iterator[Out]:
    yield text(message)
    yield js(data)


def slim(value: Any) -> Any:
    """A copy for the JSON output without base64 payloads, raw layouts or account cookies."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in SECRET_KEYS:
                continue
            if k in BULKY_KEYS:
                if v:
                    out[k] = "(omitted)"
                continue
            out[k] = slim(v)
        return out
    if isinstance(value, list):
        return [slim(v) for v in value]
    return value


def deadline_for(ctx: Ctx, p: dict[str, Any], started: float) -> float:
    return started + (P.number(p, "max_wait_seconds", DEFAULT_WAIT, 10, MAX_WAIT) or DEFAULT_WAIT)


# --------------------------------------------------------------------------- accounts and references


def account_of(ref: str | None) -> str | None:
    """The Google account an image, video, character or voice id belongs to.

    Ids look like user:12345-email:<hex of the email>-image:<id> (documented on POST /assets/{email}).
    """
    if not ref:
        return None
    match = re.search(r"-email:([0-9a-fA-F]+)-", str(ref))
    if not match or len(match.group(1)) % 2:
        return None
    try:
        email = bytes.fromhex(match.group(1)).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    return email if "@" in email else None


def need_email(ctx: Ctx, p: dict[str, Any]) -> str:
    """Tools that read one account's data need an email. With one connected account, use it."""
    email = ctx.email(p)
    if email:
        return email
    accounts = ctx.get("accounts")
    emails = list(accounts) if isinstance(accounts, dict) else []
    if len(emails) == 1:
        return emails[0]
    if not emails:
        raise UseapiError(f"No Google account is connected to Google Flow yet. Connect one first: {SETUP_ACCOUNT_URL}")
    raise UseapiError(
        "Parameter 'email' is required here: say which Google account to read. "
        f"Connected: {', '.join(emails)}. You can also set a default email in the plugin's credentials."
    )


def _file_payload(file: Any) -> tuple[bytes, str, str | None]:
    blob = getattr(file, "blob", None)
    if blob is None:
        raise UseapiError("Could not read the uploaded file.")
    name = getattr(file, "filename", None)
    mime = (getattr(file, "mime_type", None) or "").lower().strip()
    if mime == "image/jpg":
        mime = "image/jpeg"
    if mime not in UPLOAD_TYPES:
        ext = (getattr(file, "extension", None) or (name or "").rsplit(".", 1)[-1] or "").lower().lstrip(".")
        mime = EXT_TYPES.get(ext, mime)
    if mime not in UPLOAD_TYPES:
        raise UseapiError("Google Flow accepts PNG, JPEG and WebP images up to 20 MB and MP4 videos up to 100 MB.")
    limit = UPLOAD_TYPES[mime]
    if len(blob) > limit * 1024 * 1024:
        raise UseapiError(f"The file is {len(blob) // (1024 * 1024)} MB. Google Flow accepts {mime} files up to {limit} MB.")
    return blob, mime, name


class Refs:
    """Collects media references for one request and uploads Dify files to the right account.

    Every referenced item must belong to one Google account (catalog constraint `depends_on_account`),
    so uploads go to the account of the ids given, else to the account of the first upload.
    """

    def __init__(self, ctx: Ctx, p: dict[str, Any]):
        self.ctx = ctx
        self.explicit = P.text(p, "email")
        self.email: str | None = self.explicit
        self.uploaded: list[str] = []

    def pin(self, ref: str | None) -> None:
        if ref and not self.email:
            self.email = account_of(ref)

    def finish_pinning(self) -> None:
        """No id pinned an account: fall back to the credentials' default email (or let useapi.net pick)."""
        if not self.email:
            self.email = self.ctx.default_email

    def upload(self, file: Any) -> str:
        blob, mime, _name = _file_payload(file)
        path = f"assets/{enc(self.email)}" if self.email else "assets"
        data = self.ctx.client.request("POST", path, data=blob, content_type=mime, timeout=UPLOAD_TIMEOUT)
        holder = data.get("mediaGenerationId") if isinstance(data, dict) else None
        ref = holder.get("mediaGenerationId") if isinstance(holder, dict) else holder
        if not ref:
            raise UseapiError("Google Flow did not return an id for the uploaded file. Try again.")
        if not self.email:
            self.email = data.get("email") or account_of(ref)
        self.uploaded.append(ref)
        return ref


def gather(refs: Refs, p: dict[str, Any], slots: list[tuple[str, str, str | None, int]]) -> dict[str, Any]:
    """Resolve reference slots into API fields.

    slots: (API name or prefix ending in '_', id parameter, file parameter or None, max items).
    Ids are pinned first, so uploads land on the account the ids belong to.
    """
    ids: dict[str, list[str]] = {}
    for api, id_param, _file_param, limit in slots:
        values = P.items(p, id_param)
        if len(values) > limit:
            raise UseapiError(f"Parameter '{id_param}' takes at most {limit} item(s).")
        ids[api] = values
        for value in values:
            refs.pin(value)
    refs.finish_pinning()
    fields: dict[str, Any] = {}
    for api, id_param, file_param, limit in slots:
        values = list(ids[api])
        if file_param:
            for file in P.files(p, file_param):
                values.append(refs.upload(file))
        if len(values) > limit:
            raise UseapiError(f"'{id_param}' and its files take at most {limit} item(s) together.")
        if not values:
            continue
        if api.endswith("_"):
            for n, value in enumerate(values, 1):
                fields[f"{api}{n}"] = value
        else:
            fields[api] = values[0]
    return fields


# --------------------------------------------------------------------------- media outputs


def _get(obj: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def media_items(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise the media of a job record or a sync answer: id, url, kind, ok, error, base64."""
    media = record.get("media")
    if media is None:
        media = _get(record, "response", "media")
    items: list[dict[str, Any]] = []
    for m in media if isinstance(media, list) else []:
        if not isinstance(m, dict):
            continue
        image = _get(m, "image", "generatedImage")
        if isinstance(image, dict):
            items.append(
                {
                    "kind": "image",
                    "id": image.get("mediaGenerationId") or m.get("mediaGenerationId"),
                    "url": image.get("fifeUrl"),
                    "b64": image.get("encodedImage"),
                    "ok": True,
                    "error": None,
                }
            )
            continue
        status = _get(m, "mediaMetadata", "mediaStatus", "mediaGenerationStatus")
        error = _get(m, "mediaMetadata", "mediaStatus", "error", "message")
        items.append(
            {
                "kind": "video",
                "id": m.get("mediaGenerationId"),
                "url": m.get("videoUrl"),
                "b64": None,
                "ok": status in (None, "MEDIA_GENERATION_STATUS_SUCCESSFUL"),
                "error": error,
                "length": _get(m, "video", "dimensions", "length"),
            }
        )
    return items


def _decode(b64: str) -> bytes | None:
    try:
        return base64.b64decode(b64, validate=False)
    except (binascii.Error, ValueError):
        return None


def files_out(ctx: Ctx, items: list[dict[str, Any]], stem: str) -> Iterator[Out]:
    """Attach finished media as Dify files: base64 when the answer carries it, else Google's signed link."""
    for n, item in enumerate(items, 1):
        if not item.get("ok"):
            continue
        budget = ctx.download_budget()
        if budget <= 0 and not item.get("b64"):
            yield text("The remaining files were not attached because of time (Dify stops a tool call at 600 seconds). Download them from file_urls.")
            return
        ext = "mp4" if item["kind"] == "video" else "jpg"
        name = f"{stem}-{n}.{ext}" if len(items) > 1 else f"{stem}.{ext}"
        if item.get("b64"):
            blob = _decode(item["b64"])
            if blob:
                yield Out("blob", blob, meta={"mime_type": "image/jpeg", "filename": name})
                continue
        url = item.get("url")
        if not url:
            continue
        try:
            blob, mime = ctx.client.download_media(url, max_bytes=MAX_FILE_BYTES, budget=budget)
        except FileTooLarge as e:
            yield text(
                f"File {n} is {e.size // (1024 * 1024)} MB, too large to attach. Download it from its link in file_urls within 6 hours."
            )
            continue
        except UseapiError as e:
            yield text(f"File {n} could not be attached: {e} Its link is in file_urls.")
            continue
        default = "video/mp4" if item["kind"] == "video" else "image/jpeg"
        yield Out("blob", blob, meta={"mime_type": mime if mime.startswith(("video/", "image/")) else default, "filename": name})


def b64_file(data: Any, key: str, mime: str, filename: str) -> Out:
    value = data.get(key) if isinstance(data, dict) else None
    blob = _decode(value) if isinstance(value, str) and value else None
    if not blob:
        raise UseapiError("Google Flow returned no file. Try again in a minute.")
    return Out("blob", blob, meta={"mime_type": mime, "filename": filename})


# --------------------------------------------------------------------------- jobs (shared)


def _failure_text(job: dict[str, Any]) -> str:
    reasons = _get(job, "response", "failureReasons") or []
    error = job.get("error")
    if isinstance(error, dict):
        error = error.get("message")
    line = f"The {job.get('type') or 'generation'} job failed: {error or 'no reason given'}."
    if reasons:
        line += " Google's reasons: " + ", ".join(str(r) for r in reasons) + "."
    joined = " ".join(str(r) for r in reasons) + " " + str(error or "")
    if "AUDIO_FILTERED" in joined:
        line += " Google's audio filter rejected the sound made with the video. Send it again (each try makes new sound), or use Omni 1.2 Flash."
    elif "IP_PROHIBITED" in joined or "IP_INPUT_IMAGE" in joined:
        line += " Google flagged an input image as protected content. Replace the image; a retry with the same one fails again."
    elif "SPEECH_EDIT" in joined:
        line += (
            " Google refused the edit because of the speech in the clip. Try a prompt that keeps the dialogue, or a clip without speech."
        )
    elif reasons or "PUBLIC_ERROR" in joined:
        line += " Moderation varies between tries: retry, change the prompt or the reference images, or switch models."
    return line + f" jobid: {job.get('jobid') or job.get('jobId')}"


def _poll(ctx: Ctx, job: dict[str, Any], deadline: float) -> dict[str, Any]:
    while job.get("status") in RUNNING and job.get("jobid"):
        remaining = deadline - ctx.clock()
        if remaining <= 0:
            break
        ctx.sleep(min(POLL_SECONDS, remaining))
        try:
            job = ctx.get(f"jobs/{enc(job['jobid'])}")
        except UseapiError as e:
            if e.status in (404, 410):
                raise
            # A hiccup (5xx, 408, network) must not end the tool: the job keeps running. Keep the last known state.
    return job


def _as_record(answer: Any) -> dict[str, Any]:
    """A sync answer ({jobId, media}) becomes a completed job record; a job record stays as it is."""
    if not isinstance(answer, dict):
        return {}
    if "status" not in answer and answer.get("media") is not None:
        return {**answer, "jobid": answer.get("jobId"), "status": "completed"}
    if "jobid" not in answer and answer.get("jobId"):
        return {**answer, "jobid": answer.get("jobId")}
    return answer


def finish_job(ctx: Ctx, answer: Any, p: dict[str, Any], started: float, stem: str = "google-flow") -> Iterator[Out]:
    job = _as_record(answer)
    if P.flag(p, "wait", True):
        job = _poll(ctx, job, deadline_for(ctx, p, started))
    status = job.get("status")
    jobid = job.get("jobid")
    if status == "failed":
        raise UseapiError(_failure_text(job), body=job)
    if status in RUNNING:
        yield text(
            f"Google Flow is still generating (job {jobid}, status {status}). "
            "Call 'Get job status' (get_job) with this jobid and wait=true to get the result and the files. "
            "Do not start the generation again."
        )
        yield js(slim(job))
        yield var("jobid", jobid)
        yield var("status", status)
        return
    items = media_items(job)
    good = [i for i in items if i["ok"]]
    kind = "image" if items and items[0]["kind"] == "image" else "video"
    lines = [f"Google Flow made {len(good)} {kind}(s). jobid: {jobid}"]
    for n, item in enumerate(items, 1):
        if item["ok"]:
            length = f" ({item['length']})" if item.get("length") else ""
            lines.append(
                f"{n}. media id: {item['id']}{length}"
                + (f"\n   url: {item['url']}" if item.get("url") else " (link not ready yet: use 'Get media' in a minute)")
            )
        else:
            lines.append(f"{n}. failed: {item.get('error') or 'no reason given'}")
    if good:
        lines.append(
            "Links expire about 6 hours after they are made; 'Get media' gives a fresh one. Pass a media id to the other tools to extend, upscale or edit."
        )
    elif not items:
        lines.append("The job finished without media. Check it with 'Get job status' in a minute.")
    yield text("\n".join(lines))
    yield js(slim(job))
    yield var("jobid", jobid)
    yield var("status", status)
    yield var("media_ids", [i["id"] for i in good if i.get("id")])
    yield var("file_urls", [i["url"] for i in good if i.get("url")])
    if P.flag(p, "return_file", True):
        yield from files_out(ctx, good, stem)


def submit_async(ctx: Ctx, path: str, body: dict[str, Any], p: dict[str, Any]) -> Any:
    """Generations run in async mode (the API's sync mode can hold for 600 s, Dify's whole limit) and are polled."""
    P.put(body, "replyUrl", P.text(p, "reply_url"))
    return ctx.post(path, {**body, "async": True}, timeout=SUBMIT_TIMEOUT)


def _model(p: dict[str, Any], allowed: tuple[str, ...], default: str) -> str:
    model = P.text(p, "model") or default
    if model not in allowed:
        raise UseapiError(f"Model '{model}' is not offered by this plugin. Use one of: {', '.join(allowed)}.")
    return model


def _media_id(refs: Refs, p: dict[str, Any], id_param: str, file_param: str, label: str) -> str:
    fields = gather(refs, p, [("mediaGenerationId", id_param, file_param, 1)])
    if not fields.get("mediaGenerationId"):
        raise UseapiError(f"Give the {label}: a media id in '{id_param}', or a file in '{file_param}'.")
    return fields["mediaGenerationId"]


# --------------------------------------------------------------------------- accounts and jobs tools


@tool("list_accounts")
def list_accounts(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    data = ctx.get("accounts")
    accounts = data if isinstance(data, dict) else {}
    healthy = [e for e, i in accounts.items() if isinstance(i, dict) and i.get("health") == "OK"]
    lines = [f"{len(accounts)} Google account(s) connected to Google Flow, {len(healthy)} healthy."]
    for email, info in accounts.items():
        info = info if isinstance(info, dict) else {}
        health = str(info.get("health", "?"))
        lines.append(f"- {email}: {'OK' if health == 'OK' else 'not working: ' + health[:300]}")
    if len(healthy) > 1:
        lines.append("With the email left empty, useapi.net spreads new jobs across the healthy accounts.")
    yield var("emails", list(accounts.keys()))
    yield var("healthy_emails", healthy)
    yield from done("\n".join(lines), slim(data))


@tool("get_account")
def get_account(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    email = need_email(ctx, p)
    data = ctx.get(f"accounts/{enc(email)}")
    data = data if isinstance(data, dict) else {}
    credits = data.get("credits") if isinstance(data.get("credits"), dict) else {}
    plan = PLAN_NAMES.get(credits.get("userPaygateTier"), credits.get("userPaygateTier"))
    models: list[str] = []
    for m in _get(data, "models", "videoModels") or []:
        name = m.get("displayName") if isinstance(m, dict) else None
        if name and name not in models:
            models.append(name)
    lines = [f"Account {email}: health {data.get('health', '?')}."]
    if plan:
        lines.append(f"Plan: {plan}.")
    if credits.get("credits") is not None:
        lines.append(f"Google Flow credits left: {credits.get('credits')}.")
    if models:
        lines.append("Video models on this account: " + ", ".join(models) + ".")
    for tip in data.get("recommendations") or []:
        lines.append(f"Tip: {tip}")
    yield var("plan", plan)
    yield var("credits", credits.get("credits"))
    yield var("video_models", models)
    yield from done("\n".join(lines), slim(data))


@tool("list_jobs")
def list_jobs(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    data = ctx.get("jobs", params={"options": P.text(p, "options")})
    data = data if isinstance(data, dict) else {}
    lines: list[str] = []
    for section in ("videos", "images"):
        summary = _get(data, section, "summary") or {}
        for email, s in summary.items():
            if isinstance(s, dict):
                lines.append(
                    f"- {section} on {email}: {s.get('executing', 0)} running, {s.get('completed', 0)} done, "
                    f"{s.get('failed', 0)} failed, {s.get('rateLimited', 0)} rate-limited in the last 15 minutes"
                )
    header = f"Healthy accounts: {', '.join(data.get('emails') or []) or 'none'}."
    yield from done("\n".join([header, *lines]), slim(data))


@tool("get_job")
def get_job(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    job = ctx.get(f"jobs/{enc(P.required(p, 'jobid'))}")
    yield from finish_job(ctx, job, p, started)


# --------------------------------------------------------------------------- generation tools


@tool("generate_video")
def generate_video(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    body: dict[str, Any] = {"prompt": P.required(p, "prompt"), "model": _model(p, VIDEO_MODELS, DEFAULT_VIDEO_MODEL)}
    P.put(body, "aspectRatio", P.text(p, "aspect_ratio"))
    P.put(body, "duration", P.number(p, "duration", None, 3, 15))
    P.put(body, "resolution", P.text(p, "resolution"))
    body["count"] = P.number(p, "count", 1, 1, 4)
    refs = Refs(ctx, p)
    body.update(
        gather(
            refs,
            p,
            [
                ("startImage", "start_image", "start_image_file", 1),
                ("endImage", "end_image", "end_image_file", 1),
                ("referenceImage_", "reference_images", "reference_image_files", 10),
                ("character_", "characters", None, 10),
                ("referenceAudio_1", "voice", None, 1),
                ("referenceVideo_1", "reference_video", "reference_video_file", 1),
            ],
        )
    )
    if "endImage" in body and "startImage" not in body:
        raise UseapiError("An end image needs a start image too (end-frame-only is not supported).")
    if "referenceVideo_1" in body:
        body.pop("duration", None)  # an edit is as long as the slice of the source video
        P.put(body, "startFrameIndex_1", P.number(p, "start_frame", None, 0, 359))
        P.put(body, "endFrameIndex_1", P.number(p, "end_frame", None, 1, 360))
    P.put(body, "email", refs.email)
    answer = submit_async(ctx, "videos", body, p)
    yield from finish_job(ctx, answer, p, started, "google-flow-video")


@tool("extend_video")
def extend_video(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    model = _model(p, EXTEND_MODELS, DEFAULT_EXTEND_MODEL)
    refs = Refs(ctx, p)
    body: dict[str, Any] = {"prompt": P.required(p, "prompt"), "model": model}
    body["mediaGenerationId"] = _media_id(refs, p, "video", "video_file", "video to extend")
    if model == "omni-flash-1.2":
        P.put(body, "duration", P.number(p, "duration", None, 3, 10))
        P.put(body, "resolution", P.text(p, "resolution"))
        body.update(
            gather(
                refs,
                p,
                [
                    ("referenceImage_", "reference_images", "reference_image_files", 3),
                    ("character_", "characters", None, 3),
                    ("referenceAudio_1", "voice", None, 1),
                ],
            )
        )
    body["count"] = P.number(p, "count", 1, 1, 4)
    answer = submit_async(ctx, "videos/extend", body, p)
    yield from finish_job(ctx, answer, p, started, "google-flow-extended")


@tool("upscale_video")
def upscale_video(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    refs = Refs(ctx, p)
    body: dict[str, Any] = {"mediaGenerationId": _media_id(refs, p, "video", "video_file", "video to upscale")}
    P.put(body, "resolution", P.text(p, "resolution"))
    answer = submit_async(ctx, "videos/upscale", body, p)
    yield from finish_job(ctx, answer, p, started, "google-flow-upscaled")


@tool("generate_image")
def generate_image(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    model = _model(p, IMAGE_MODELS, DEFAULT_IMAGE_MODEL)
    body: dict[str, Any] = {"prompt": P.required(p, "prompt"), "model": model}
    P.put(body, "aspectRatio", P.text(p, "aspect_ratio"))
    body["count"] = P.number(p, "count", 1, 1, 4)
    P.put(body, "seed", P.number(p, "seed", None, 0, 2**31 - 1))
    if model == "nano-banana-2":
        P.put(body, "thinkingLevel", P.text(p, "thinking_level"))
    refs = Refs(ctx, p)
    body.update(
        gather(
            refs,
            p,
            [("reference_", "reference_images", "reference_image_files", 10), ("character_", "characters", None, 7)],
        )
    )
    P.put(body, "email", refs.email)
    P.put(body, "replyUrl", P.text(p, "reply_url"))
    answer = ctx.post("images", body, timeout=SYNC_TIMEOUT)  # images answer in sync mode only (about 100 s at most)
    yield from finish_job(ctx, answer, {**p, "wait": False}, started, "google-flow-image")


@tool("upscale_image")
def upscale_image(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    refs = Refs(ctx, p)
    body: dict[str, Any] = {"mediaGenerationId": _media_id(refs, p, "image", "image_file", "image to upscale")}
    P.put(body, "resolution", P.text(p, "resolution"))
    data = ctx.post("images/upscale", body, timeout=SYNC_TIMEOUT)
    blob = b64_file(data, "encodedImage", "image/jpeg", f"google-flow-upscaled-{body.get('resolution') or '2k'}.jpg")
    yield text(f"Image upscaled to {body.get('resolution') or '2k'} ({len(blob.value) // 1024} KB). The file is attached.")
    yield js(slim(data))
    yield blob


@tool("video_to_gif")
def video_to_gif(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    refs = Refs(ctx, p)
    body = {"mediaGenerationId": _media_id(refs, p, "video", "video_file", "video")}
    data = ctx.post("videos/gif", body, timeout=SYNC_TIMEOUT)
    blob = b64_file(data, "encodedGif", "image/gif", "google-flow.gif")
    yield text(f"Animated GIF ready ({len(blob.value) // 1024} KB). The file is attached.")
    yield js(slim(data))
    yield blob


@tool("concatenate_videos")
def concatenate_videos(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    advanced = P.json_list(p, "media_json")
    if advanced:
        media = advanced
    else:
        refs = Refs(ctx, p)
        ids = P.items(p, "videos")
        for ref in ids:
            refs.pin(ref)
        refs.finish_pinning()
        ids += [refs.upload(f) for f in P.files(p, "video_files")]
        media = [{"mediaGenerationId": ref} for ref in ids]
    if not 2 <= len(media) <= 10:
        raise UseapiError("Give 2 to 10 videos, in order, all landscape or all portrait.")
    data = ctx.post("videos/concatenate", {"media": media}, timeout=SYNC_TIMEOUT)
    blob = b64_file(data, "encodedVideo", "video/mp4", "google-flow-joined.mp4")
    yield text(f"Joined {len(media)} videos into one MP4 ({len(blob.value) // (1024 * 1024)} MB). The file is attached.")
    yield js(slim(data))
    yield blob


# --------------------------------------------------------------------------- media tools


@tool("upload_image")
def upload_image(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    file = p.get("file")
    if file is None:
        raise UseapiError("Parameter 'file' is required.")
    refs = Refs(ctx, p)
    refs.finish_pinning()
    ref = refs.upload(file)
    yield var("media_id", ref)
    yield var("email", refs.email)
    yield text(
        f"Uploaded to Google Flow on {refs.email or 'the account useapi.net picked'}. media id: {ref}\n"
        "Pass it as a start image, reference image or video to the generation tools. It works only with media of the same Google account."
    )
    yield js({"mediaGenerationId": ref, "email": refs.email})


@tool("list_media")
def list_media(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    email = need_email(ctx, p)
    data = ctx.get(f"assets/media/{enc(email)}", params={"projectId": P.text(p, "project_id")})
    media = data.get("media") if isinstance(data, dict) else []
    media = media if isinstance(media, list) else []
    lines = [f"{data.get('count', len(media))} item(s) in the Google Flow project of {email}, newest first."]
    for m in media[:50]:
        upload = ", upload" if m.get("likelyUpload") else ""
        lines.append(f"- {str(m.get('mediaType', '')).lower()}{upload}, {m.get('createTime', '')}: {m.get('mediaGenerationId')}")
    if len(media) > 50:
        lines.append(f"(first 50 of {len(media)} shown; all are in the JSON output)")
    yield var("media_ids", [m.get("mediaGenerationId") for m in media if m.get("mediaGenerationId")])
    yield from done("\n".join(lines), data)


@tool("get_media")
def get_media(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    ref = P.required(p, "media_id")
    data = ctx.get(f"assets/{enc(ref)}")
    url = data.get("url") if isinstance(data, dict) else None
    kind = "video" if "-video:" in ref else "image"
    yield text(
        f"Fresh link for this {kind}, valid about 6 hours:\n{url}" if url else "Google Flow returned no link yet. Try again in a minute."
    )
    yield js(data)
    yield var("file_url", url)
    if url:
        yield Out("link", url)
        if P.flag(p, "return_file", True):
            yield from files_out(ctx, [{"kind": kind, "url": url, "ok": True}], f"google-flow-{kind}")


@tool("list_characters")
def list_characters(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    email = need_email(ctx, p)
    data = ctx.get("characters", params={"email": email})
    chars = data.get("characters") if isinstance(data, dict) else []
    chars = chars if isinstance(chars, list) else []
    lines = [f"{len(chars)} character(s) on {email}."]
    for c in chars:
        voice = _get(c, "voice", "displayName")
        lines.append(f"- {c.get('displayName')}" + (f" (voice {voice})" if voice else "") + f": {c.get('character')}")
    if chars:
        lines.append("Pass a character id in 'characters' of Generate video, Generate image or Google Flow agent chat.")
    yield var("character_ids", [c.get("character") for c in chars if c.get("character")])
    yield from done("\n".join(lines), data)


@tool("list_voices")
def list_voices(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    email = need_email(ctx, p)
    data = ctx.get("voices", params={"email": email, "source": P.text(p, "source")})
    voices = data.get("voices") if isinstance(data, dict) else []
    voices = voices if isinstance(voices, list) else []
    system = [v.get("voice") for v in voices if v.get("source") == "system"]
    own = [v for v in voices if v.get("source") == "user"]
    lines = [f"{len(voices)} voice(s) on {email}."]
    if system:
        lines.append("Built-in voices (pass the name): " + ", ".join(str(v) for v in system))
    for v in own:
        lines.append(f"- {v.get('displayName')} (own voice): {v.get('voice')}")
    yield var("voices", [v.get("voice") for v in voices if v.get("voice")])
    yield from done("\n".join(lines), data)


# --------------------------------------------------------------------------- Google Flow agent


def _chat_path(chat_id: str) -> str:
    return f"agent/chats/{enc(chat_id)}"


def _latest_turn(chat: dict[str, Any]) -> dict[str, Any]:
    turns = chat.get("turns") if isinstance(chat.get("turns"), list) else []
    return turns[-1] if turns and isinstance(turns[-1], dict) else {}


def _pending(m: Any) -> bool:
    """Media is still being made unless it is completed, failed or error ("queued" and "running" are both pending)."""
    return isinstance(m, dict) and m.get("status") not in ("completed", "failed", "error")


def _queued(chat: dict[str, Any]) -> bool:
    return any(_pending(m) for m in _latest_turn(chat).get("media") or [])


def _last_error(value: Any) -> str:
    if isinstance(value, dict):
        code, message = value.get("code"), value.get("message")
        return " ".join(str(x) for x in (code, message) if x) or "no reason given"
    return str(value) if value else "no reason given"


def _follow(ctx: Ctx, chat_id: str, deadline: float, wait_videos: bool) -> dict[str, Any]:
    """Read the chat until its turn ends (and, if asked, its videos finish) or the wait runs out."""
    while True:
        chat = ctx.get(_chat_path(chat_id), params={"media": "false"})
        chat = chat if isinstance(chat, dict) else {}
        busy = chat.get("status") == "running" or (wait_videos and _queued(chat))
        remaining = deadline - ctx.clock()
        if not busy or remaining <= 0:
            break
        ctx.sleep(min(POLL_SECONDS, remaining))
    full = ctx.get(_chat_path(chat_id))  # one read with fresh media links
    return full if isinstance(full, dict) else chat


def chat_out(ctx: Ctx, chat: dict[str, Any], chat_id: str, p: dict[str, Any]) -> Iterator[Out]:
    status = chat.get("status") or "unknown"
    turn = _latest_turn(chat)
    texts = [str(i.get("text")) for i in turn.get("agent") or [] if isinstance(i, dict) and i.get("kind") == "text" and i.get("text")]
    media = [m for m in turn.get("media") or [] if isinstance(m, dict)]
    lines = ["\n\n".join(texts) or "(the agent has not replied yet)"]
    for m in media:
        state = m.get("status")
        url = f"\n   url: {m['url']}" if m.get("url") else ""
        lines.append(f"- {m.get('type')} [{state}] {m.get('displayName') or ''}: {m.get('referenceId')}{url}")
    approval = chat.get("pendingApproval")
    if status == "waiting_approval" and isinstance(approval, dict):
        ask = next(
            (
                i.get("args", {}).get("text")
                for i in turn.get("agent") or []
                if isinstance(i, dict) and i.get("tool") == "ask_for_permission"
            ),
            None,
        )
        lines.append(
            f"The agent asks before it spends Google Flow credits: {ask or ''} (cost {approval.get('cost')} credits). "
            "Ask the user, then call 'Answer the agent's approval request' (agent_answer_approval) with this chat_id and "
            "approve, always or reject, within about 4 minutes."
        )
    elif status == "running":
        lines.append(
            "The turn is still running. Call 'Get Google Flow agent chat' (agent_get_chat) with this chat_id and wait=true. Do not send the message again."
        )
    elif status == "failed":
        lines.append(f"The turn failed: {_last_error(chat.get('lastError'))}. Send the next message when ready.")
    if any(_pending(m) for m in media):
        lines.append("Videos finish a minute or two after the turn: call agent_get_chat with wait=true to get their links.")
    lines.append(f"chat_id: {chat_id} (status {status})")
    yield text("\n".join(lines))
    yield js(slim(chat))
    done_media = [m for m in media if m.get("status") == "completed"]
    yield var("chat_id", chat_id)
    yield var("status", status)
    yield var("reply", "\n\n".join(texts))
    yield var("media_ids", [m.get("referenceId") for m in done_media if m.get("referenceId")])
    yield var("file_urls", [m.get("url") for m in done_media if m.get("url")])
    if P.flag(p, "return_file", False):
        items = [{"kind": "video" if m.get("type") == "video" else "image", "url": m.get("url"), "ok": True} for m in done_media]
        yield from files_out(ctx, items, "google-flow-agent")


def _after_send(ctx: Ctx, answer: Any, p: dict[str, Any], started: float, chat_id: str | None = None) -> Iterator[Out]:
    chat_id = (answer.get("chatId") if isinstance(answer, dict) else None) or chat_id
    if not chat_id:
        raise UseapiError("Google Flow did not return a chat id. Check 'List Google Flow agent chats' before sending again.")
    if not P.flag(p, "wait", True):
        yield text(f"Message sent. The agent is working (chat_id: {chat_id}). Read the answer with agent_get_chat and wait=true.")
        yield js(answer)
        yield var("chat_id", chat_id)
        yield var("status", answer.get("status") if isinstance(answer, dict) else None)
        return
    chat = _follow(ctx, chat_id, deadline_for(ctx, p, started), wait_videos=False)
    yield from chat_out(ctx, chat, chat_id, p)


@tool("agent_chat")
def agent_chat(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    chat_id = P.text(p, "chat_id")
    body: dict[str, Any] = {"message": P.required(p, "message")}
    refs = Refs(ctx, p)
    if chat_id and not refs.email:
        refs.email = _chat_account(chat_id)  # references must belong to the chat's account
    body.update(
        gather(
            refs,
            p,
            [
                ("referenceImage_", "reference_images", "reference_image_files", 7),
                ("referenceVideo_1", "reference_video", "reference_video_file", 1),
                ("referenceAudio_", "voices", None, 5),
                ("character_", "characters", None, 7),
            ],
        )
    )
    P.put(body, "replyUrl", P.text(p, "reply_url"))
    if chat_id:
        answer = ctx.post(f"{_chat_path(chat_id)}/messages", body, timeout=AGENT_TIMEOUT)
    else:
        P.put(body, "email", refs.email)
        P.put(body, "projectId", P.text(p, "project_id"))
        answer = ctx.post("agent/chats", body, timeout=AGENT_TIMEOUT)
    yield from _after_send(ctx, answer, p, started, chat_id)


def _chat_account(chat_id: str) -> str | None:
    """Chat ids carry the account in plain text: c-u12345-email:john@gmail.com-project:..."""
    match = re.search(r"-email:([^\s]+?@[^\s]+?)-project:", chat_id)
    return match.group(1) if match else None


@tool("agent_get_chat")
def agent_get_chat(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    chat_id = P.required(p, "chat_id")
    if P.flag(p, "wait", False):
        chat = _follow(ctx, chat_id, deadline_for(ctx, p, started), wait_videos=True)
    else:
        chat = ctx.get(_chat_path(chat_id))
        chat = chat if isinstance(chat, dict) else {}
    yield from chat_out(ctx, chat, chat_id, p)


@tool("agent_answer_approval")
def agent_answer_approval(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    started = ctx.clock()
    chat_id = P.required(p, "chat_id")
    decision = P.required(p, "decision")
    if decision not in ("approve", "always", "reject"):
        raise UseapiError("Parameter 'decision' must be approve, always or reject.")
    answer = ctx.post(f"{_chat_path(chat_id)}/approval", {"decision": decision}, timeout=AGENT_TIMEOUT)
    yield from _after_send(ctx, answer, p, started, chat_id)


@tool("agent_list_chats")
def agent_list_chats(ctx: Ctx, p: dict[str, Any]) -> Iterator[Out]:
    email = need_email(ctx, p)
    data = ctx.get("agent/chats", params={"email": email, "projectId": P.text(p, "project_id")})
    chats = data.get("chats") if isinstance(data, dict) else []
    chats = chats if isinstance(chats, list) else []
    lines = [f"{len(chats)} Google Flow agent chat(s) on {email}."]
    for c in chats:
        running = " (running)" if c.get("running") else ""
        lines.append(f"- {c.get('title') or '(untitled)'}{running}, updated {c.get('updated')}: {c.get('chatId')}")
    yield var("chat_ids", [c.get("chatId") for c in chats if c.get("chatId")])
    yield from done("\n".join(lines), data)
