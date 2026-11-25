"""Live routing check: call every read-only tool against api.useapi.net with a
fake token. Each call must answer 401 (the route exists and checks the token),
never 404 (a wrong path) or 400 (a malformed id or parameter).

It never sends a real token and never calls an endpoint that generates,
uploads or spends Google Flow credits or captcha credits.

Run from the plugin folder:  python dev/routing_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dev"))

from endpoints import ENDPOINTS  # noqa: E402
from useapi_flow.client import Client, UseapiError  # noqa: E402
from useapi_flow.handlers import HANDLERS, Ctx  # noqa: E402

FAKE_TOKEN = "user:12345-glamahealthcheck"
EMAIL = "john@gmail.com"
JOB = "j1117123456789304152v-u12345-email:john@gmail.com-bot:google-flow"
MEDIA = "user:12345-email:6a6f686e40676d61696c2e636f6d-video:a1d95d21-75d2-482d-a354-14ef8802ce66"
CHAT = (
    "c-u12345-email:john@gmail.com-project:f166200a-ea22-461a-bc68-47ff6d3ee500-chat:2a0f1973-d554-4fbc-aa6b-0c372edf182e-bot:google-flow"
)

READ_ONLY = {
    "list_accounts": {},
    "get_account": {"email": EMAIL},
    "list_jobs": {},
    "get_job": {"jobid": JOB, "wait": False},
    "list_media": {"email": EMAIL},
    "get_media": {"media_id": MEDIA, "return_file": False},
    "list_characters": {"email": EMAIL},
    "list_voices": {"email": EMAIL},
    "agent_get_chat": {"chat_id": CHAT},
    "agent_list_chats": {"email": EMAIL},
}


def main() -> int:
    ctx = Ctx(client=Client(FAKE_TOKEN))
    failures = 0
    for name, params in READ_ONLY.items():
        try:
            list(HANDLERS[name](ctx, params))
            status = 200
        except UseapiError as e:
            status = e.status
        ok = status == 401
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {status} {name:20} {ENDPOINTS[name][0]}")
    print(f"{len(READ_ONLY) - failures}/{len(READ_ONLY)} routes answered 401")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
