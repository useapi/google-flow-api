"""Error mapping and transport behaviour of the HTTP client."""

import pytest
import requests

from fakes import FakeResponse, FakeSession
from useapi_flow.client import Client, UseapiError, describe_error, is_media_url


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (400, {"error": "No captcha provider API keys configured", "code": 400}, "300 free captcha credits are used up"),
        (400, {"error": "4-second 'veo-3.1-lite' videos need a Google AI Ultra plan; x", "code": 400}, "Use 8 seconds"),
        (
            400,
            {"error": "Model 'omni-flash-1.2' extends videos on paid Google Flow plans only (Plus, Pro or Ultra).", "code": 400},
            "plan does not include",
        ),
        (400, {"error": "Google has not given Omni 1.2 Flash to x", "code": 400}, "has not reached this Google account"),
        (400, {"error": "Google no longer offers veo-3.1-lite-low-priority on this account", "code": 400}, "Ultra $199"),
        (400, {"error": "Cannot use referenceVideo_1 with start/end frames", "code": 400}, "Details: Cannot use referenceVideo_1"),
        (401, {"error": "useapi.net ⁝ Unauthorized", "code": 401}, "rejected the API token"),
        (402, {"error": "no subscription", "code": 402}, "subscription is not active"),
        (
            403,
            {"error": "captcha_quality: PUBLIC_ERROR_UNUSUAL_ACTIVITY after 5 attempts", "code": 403},
            "no Google Flow credits were used",
        ),
        (429, {"error": "captcha_quality: PUBLIC_ERROR_UNUSUAL_ACTIVITY after 5 attempts", "code": 429}, "no Google Flow credits were used"),
        (403, {"error": "PUBLIC_ERROR_MODEL_ACCESS_DENIED", "code": 403}, "its plan does not include it"),
        (403, {"error": "Google refused ... (PUBLIC_ERROR_USER_MINOR)", "code": 403}, "under 18"),
        (403, {"error": "Unauthorized access to user:99999 detected in mediaGenerationId", "code": 403}, "another useapi.net user"),
        (404, {"error": "Google Flow account john@gmail.com not found", "code": 404}, "Connect the Google account first"),
        (404, {"error": "Job not found", "code": 404}, "Not found (404). Details: Job not found"),
        (408, {"error": "Video generation polling timeout", "code": 408}, "Still running"),
        (409, {"error": "A turn is running", "code": 409}, "agent turn is running"),
        (410, {"error": "Job has expired", "code": 410}, "kept for 7 days"),
        (429, {"error": "no_eligible_account", "code": 429, "retryAfter": "2026-11-24T10:00:00Z"}, "Connect more Google accounts"),
        (429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "x"}}, "leave the email empty"),
        (502, {"error": "Google answered without a readable reply", "code": 502}, "may have run"),
        (503, {"error": "Captcha service failed: ERROR_ZERO_BALANCE", "code": 503}, "captcha provider failed"),
        (503, {"error": {"code": 503, "message": "Service temporarily unavailable.", "status": "UNAVAILABLE"}}, "Wait 5 to 10 seconds"),
        (504, {"error": "Google has not confirmed the turn yet", "code": 504}, "may still run"),
        (596, {"error": "Google rejected this account session (HTTP 401)", "code": 596}, "add the account again"),
        (500, None, "useapi.net side"),
    ],
)
def test_describe_error(status, body, expected):
    assert expected in describe_error(status, body)


def test_retry_after_header_wins():
    assert "Retry after 30 seconds" in describe_error(429, {"error": "x", "retryAfter": "2026"}, {"Retry-After": "30"})
    assert "Retry after 2026" in describe_error(429, {"error": "x", "retryAfter": "2026"}, {})


def test_error_raised_with_status():
    session = FakeSession([("GET", "accounts", FakeResponse(401, {"error": "useapi.net ⁝ Unauthorized", "code": 401}))])
    with pytest.raises(UseapiError) as e:
        Client("bad", session=session).request("GET", "accounts")
    assert e.value.status == 401


def test_missing_token():
    with pytest.raises(UseapiError, match="token is missing"):
        Client("  ")


class Boom:
    def __init__(self, exc):
        self.exc = exc

    def request(self, *a, **k):
        raise self.exc


def test_timeout_and_network_errors():
    with pytest.raises(UseapiError, match="within 60 seconds"):
        Client("t", session=Boom(requests.Timeout())).request("GET", "accounts")
    with pytest.raises(UseapiError, match="Could not reach api.useapi.net"):
        Client("t", session=Boom(requests.ConnectionError())).request("GET", "accounts")


def test_empty_params_are_dropped():
    session = FakeSession()
    Client("t", session=session).request("GET", "voices", params={"email": None, "source": ""})
    assert session.calls[0].query == {}


@pytest.mark.parametrize(
    "url,ok",
    [
        ("https://flow-content.google/video/x?Expires=1", True),
        ("https://flow-content.google:443/image/x", True),
        ("http://flow-content.google/video/x", False),
        ("https://flow-content.google.evil.com/video/x", False),
        ("https://user@flow-content.google/video/x", False),
        ("https://api.useapi.net/v1/google-flow/assets/x?raw=true", False),
        ("file:///etc/passwd", False),
    ],
)
def test_media_hosts(url, ok):
    assert is_media_url(url) is ok


def test_download_refuses_redirects_and_large_files():
    session = FakeSession([("GET", "/video/", FakeResponse(302, content=b"", headers={"Location": "https://elsewhere.example/x"}))])
    with pytest.raises(UseapiError, match="answered 302"):
        Client("t", session=session).download_media("https://flow-content.google/video/x")
    from useapi_flow.client import FileTooLarge

    session = FakeSession([("GET", "/video/", FakeResponse(200, content=b"x" * 100, headers={"Content-Type": "video/mp4"}))])
    with pytest.raises(FileTooLarge):
        Client("t", session=session).download_media("https://flow-content.google/video/x", max_bytes=10)


def test_download_stops_when_the_total_time_budget_is_spent():
    session = FakeSession([("GET", "/video/", FakeResponse(200, content=b"x" * 100, headers={"Content-Type": "video/mp4"}))])
    with pytest.raises(UseapiError, match="ran out of time"):
        Client("t", session=session).download_media("https://flow-content.google/video/x", budget=-1)
