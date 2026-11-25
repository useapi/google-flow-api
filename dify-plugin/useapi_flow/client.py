"""HTTP client for the useapi.net Google Flow API.

API requests go to https://api.useapi.net/v1/google-flow with the user's
useapi.net API token as a Bearer token. Finished images and videos are
downloaded from Google's signed links on https://flow-content.google, without
the token. Nothing else is contacted.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import quote, urlsplit

import requests

BASE_URL = "https://api.useapi.net/v1/google-flow"
USER_AGENT = "dify-plugin-google-flow-useapi/0.1.0"
MEDIA_HOST = "flow-content.google"

SETUP_TOKEN_URL = "https://useapi.net/docs/start-here/setup-useapi"
SETUP_ACCOUNT_URL = "https://useapi.net/docs/start-here/setup-google-flow"
CAPTCHA_URL = "https://useapi.net/docs/start-here/setup-google-flow#configure-captcha-providers"
SUBSCRIPTION_URL = "https://useapi.net/docs/subscription"

# Seconds. A generation request waits for its captcha before it answers, which can take minutes.
DEFAULT_TIMEOUT = 60
SUBMIT_TIMEOUT = 240
SYNC_TIMEOUT = 300
AGENT_TIMEOUT = 150
UPLOAD_TIMEOUT = 300
DOWNLOAD_TIMEOUT = 300


class UseapiError(Exception):
    """A readable error for the Dify user or agent."""

    def __init__(self, message: str, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


class FileTooLarge(Exception):
    def __init__(self, size: int):
        super().__init__(size)
        self.size = size


def enc(value: str) -> str:
    """URL-encode an id or email for use in a path. Ids contain ':' and '@'."""
    return quote(str(value), safe="")


def _server_message(body: Any) -> str:
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            code = err.get("status") or err.get("code")
            msg = err.get("message") or ""
            return f"{code}: {msg}" if code else msg
        if err:
            return str(err)
    if isinstance(body, str):
        return body.strip()[:500]
    return ""


def _retry_after(body: Any, headers: Any) -> str:
    seconds = None
    if headers is not None:
        try:
            seconds = headers.get("Retry-After")
        except AttributeError:
            seconds = None
    if seconds:
        return f" Retry after {seconds} seconds."
    if isinstance(body, dict) and body.get("retryAfter"):
        return f" Retry after {body['retryAfter']}."
    return ""


def describe_error(status: int, body: Any, headers: Any = None) -> str:
    """Turn an HTTP error from the API into one or two readable sentences.

    Meanings follow the published API catalog (https://api.useapi.net/v1/google-flow/models, `errors`).
    """
    server = _server_message(body)
    detail = f" Details: {server}" if server else ""
    later = _retry_after(body, headers)

    if status in (403, 429) and server.startswith("captcha_quality:"):  # the catalog matches it under both
        return (
            f"Google refused the captcha on every try ({status}), so nothing was generated and no Google Flow credits were used. "
            f"If it keeps happening, use another Google account, or leave the email empty to let useapi.net pick one.{detail}"
        )
    if status == 401:
        return f"useapi.net rejected the API token (401 Unauthorized). Check the token in the plugin's credentials. How to get one: {SETUP_TOKEN_URL}"
    if status == 402:
        return f"Your useapi.net subscription is not active (402 Payment Required). See {SUBSCRIPTION_URL}.{detail}"
    if status == 400:
        if server.startswith("No captcha provider API keys configured"):
            return (
                "The 300 free captcha credits are used up (400). Add your own captcha provider key to keep generating: "
                f"{CAPTCHA_URL}{detail}"
            )
        if "need a Google AI Ultra plan" in server:
            return f"This length needs a Google AI Ultra plan (400). Use 8 seconds, or an account on Google AI Ultra.{detail}"
        if any(
            s in server for s in ("paid Google Flow plan", "needs a paid Google AI plan", "upscaling is not available", ", which is on ")
        ):
            return f"The Google account's plan does not include this (400). Use another account or a different option.{detail}"
        if server.startswith("Google has not given"):
            return f"Omni 1.2 Flash has not reached this Google account yet (400). Use another account or Veo 3.1 Lite.{detail}"
        if server.startswith("Google no longer offers veo-3.1-lite-low-priority"):
            return f"This account does not have Veo 3.1 Lite Lower Priority (400). It is on the Google AI Ultra $199 plan owner's account only.{detail}"
        return f"The request was refused (400). Change what the details say and try again.{detail}"
    if status == 403:
        if "PUBLIC_ERROR_MODEL_ACCESS_DENIED" in server:
            return f"Google refused this model on this account (403): its plan does not include it. Use another account or model.{detail}"
        if "PUBLIC_ERROR_USER_MINOR" in server:
            return (
                f"Google treats this Google account as under 18 (403), so Google Flow is not available to it. Use another account.{detail}"
            )
        return f"Refused (403): the id belongs to another useapi.net user, or Google refused this request for the account.{detail}"
    if status == 404:
        hint = ""
        if "account" in server.lower() and "not found" in server.lower():
            hint = f" Connect the Google account first: {SETUP_ACCOUNT_URL}"
        return f"Not found (404).{detail}{hint}"
    if status == 408:
        return f"Still running when the wait ended (408). Check 'Get job status' or 'List jobs' before sending it again.{detail}"
    if status == 409:
        return f"Busy with an earlier request (409), for example an agent turn is running or waits for an approval. Wait for it to end and retry.{detail}"
    if status == 410:
        return "The job has expired (410). Jobs are kept for 7 days."
    if status == 429:
        if server == "no_eligible_account":
            return (
                "Every connected Google account is set aside for this model right now (429)."
                f"{later} Connect more Google accounts, or try another model.{detail}"
            )
        return (
            f"Google limits this account for now (429).{later} Use another account, or leave the email empty so useapi.net "
            f"picks a free one.{detail}"
        )
    if status == 502:
        return f"Google answered with an error or no readable reply (502). The request may have run: check before sending it again.{detail}"
    if status == 503:
        if server.startswith("Captcha service failed:"):
            return f"Your captcha provider failed (503): check its API key and balance. {CAPTCHA_URL}{detail}"
        return (
            f"Google Flow is briefly unavailable or the item is not ready yet (503).{later or ' Wait 5 to 10 seconds and retry.'}{detail}"
        )
    if status == 504:
        return f"Google did not answer in time (504). The request may still run: check before sending it again.{detail}"
    if status == 596:
        return (
            "Google rejected this account's session (596). useapi.net re-verifies it on its own: retry in about a minute. "
            f"If it keeps answering 596, add the account again: {SETUP_ACCOUNT_URL}{detail}"
        )
    if status >= 500:
        return f"Something failed on the useapi.net side ({status}). Retry in a minute.{detail}"
    return f"Request failed ({status}).{detail}"


def _parse_body(resp: requests.Response) -> Any:
    text = resp.text
    if not text:
        return None
    try:
        return resp.json()
    except ValueError:
        return text


def is_media_url(url: str) -> bool:
    """Only Google's signed media links on flow-content.google are downloaded."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    return parts.scheme == "https" and parts.hostname == MEDIA_HOST and not parts.username and parts.port in (None, 443)


class Client:
    def __init__(self, token: str, session: requests.Session | None = None, base_url: str = BASE_URL):
        token = (token or "").strip()
        if not token:
            raise UseapiError(f"The useapi.net API token is missing. How to get one: {SETUP_TOKEN_URL}")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.http = session or requests.Session()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if extra:
            headers.update(extra)
        return headers

    def url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        data: bytes | None = None,
        content_type: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> Any:
        """Send one request and return the parsed JSON body, or raise UseapiError."""
        extra: dict[str, str] = {}
        payload: bytes | None = None
        if body is not None:
            extra["Content-Type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")
        elif data is not None:
            extra["Content-Type"] = content_type or "application/octet-stream"
            payload = data
        clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        try:
            resp = self.http.request(
                method,
                self.url(path),
                params=clean_params or None,
                data=payload,
                headers=self._headers(extra),
                timeout=timeout,
            )
        except requests.Timeout as e:
            raise UseapiError(
                f"No answer from api.useapi.net within {int(timeout)} seconds. "
                "The request may still complete: check 'List jobs' before retrying anything that generates."
            ) from e
        except requests.RequestException as e:
            raise UseapiError(f"Could not reach api.useapi.net: {e.__class__.__name__}") from e

        parsed = _parse_body(resp)
        if resp.status_code < 400:
            return parsed if parsed is not None else {}
        raise UseapiError(describe_error(resp.status_code, parsed, resp.headers), resp.status_code, parsed)

    def download_media(
        self, url: str, timeout: float = DOWNLOAD_TIMEOUT, max_bytes: int | None = None, budget: float | None = None
    ) -> tuple[bytes, str]:
        """Download a signed Google Flow media link. Returns (bytes, content type).

        The link needs no authentication, so the API token is never sent with it.
        """
        if not is_media_url(url):
            raise UseapiError(f"Refusing to download a file from outside https://{MEDIA_HOST}.")
        end = None if budget is None else time.monotonic() + budget  # total-time limit; the read timeout is per read
        if budget is not None:
            timeout = max(1.0, min(timeout, budget))
        try:
            resp = self.http.get(
                url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, timeout=timeout, stream=True, allow_redirects=False
            )
        except requests.Timeout as e:
            raise UseapiError(f"The file download did not finish within {int(timeout)} seconds.") from e
        except requests.RequestException as e:
            raise UseapiError(f"Could not reach {MEDIA_HOST}: {e.__class__.__name__}") from e
        if resp.status_code >= 300:
            resp.close()
            raise UseapiError(
                f"The media link answered {resp.status_code}. Links expire after about 6 hours: use 'Get media' for a fresh one.",
                resp.status_code,
            )
        length = resp.headers.get("Content-Length")
        if max_bytes and length and length.isdigit() and int(length) > max_bytes:
            resp.close()
            raise FileTooLarge(int(length))
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=1 << 16):
            if end is not None and time.monotonic() > end:
                resp.close()
                raise UseapiError("The file download ran out of time.")
            total += len(chunk)
            if max_bytes and total > max_bytes:
                resp.close()
                raise FileTooLarge(total)
            chunks.append(chunk)
        content_type = resp.headers.get("Content-Type", "application/octet-stream").split(";")[0].strip()
        return b"".join(chunks), content_type
