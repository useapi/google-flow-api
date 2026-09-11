"""

Script version 1.1, September 11, 2026

Batch-compare Google Flow's Nano Banana image models (2 Lite, 2, Pro) with the useapi.net API.
Reads prompts.json (one entry per model), submits each to the synchronous POST /images endpoint,
and downloads every returned image with a model-labeled filename.
For more details visit https://useapi.net/docs/api-google-flow-v1/post-google-flow-images

Companion tutorial:
  https://useapi.net/docs/articles/google-flow-nano-banana-compare

Installation Instructions:
==========================

You need Python 3.x installed to run this script (standard library only, no dependencies):

- Windows, macOS, Linux: https://www.python.org/

Verify with:

   python3 --version

Running the Script:
===================

Usage: python3 google-flow-nano-banana-compare.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

python3 google-flow-nano-banana-compare.py user:1234-abcdefhijklmnopqrstuv my@email.com

Changelog:
==========

- July 2, 2026: Initial release.
- September 11, 2026: Sends a named User-Agent on API calls (api.useapi.net rejects urllib's default one with HTTP 403), saves encodedImage when fifeUrl is absent, and a failed image download no longer stops the run or leaves a partial file for the next run to skip as "already exists".

"""

import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

DEFAULT_PROMPTS_FILE = "prompts.json"
DEFAULT_MODEL = "nano-banana-2-lite"
SLEEP_RETRY = 30  # seconds

URL_ACCOUNTS = "https://api.useapi.net/v1/google-flow/accounts"
URL_IMAGES = "https://api.useapi.net/v1/google-flow/images"

# api.useapi.net's Cloudflare edge rejects urllib's default User-Agent (error 1010, HTTP 403).
USER_AGENT = "google-flow-nano-banana-compare.py"


def fetch_accounts(api_token):
    req = urllib.request.Request(
        URL_ACCOUNTS,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_token}",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"⛔ Error fetching accounts (HTTP {e.code})")
        sys.exit(1)


# Save one generated image. fifeUrl is normally present; when it is absent the image
# arrived inline as base64 in encodedImage. A failure is reported and skipped so the
# remaining images are still saved.
def download_image(image, filename):
    if os.path.exists(filename):
        print(f"⚠️ {filename} already exists. Skipping download.")
        return
    url = image.get("fifeUrl")
    if not url and image.get("encodedImage"):
        print(f"✅ Saving {filename} from encodedImage")
        try:
            data = base64.b64decode(image["encodedImage"])
            with open(filename, "wb") as f:
                f.write(data)
        except Exception as e:
            print(f"⛔ Unable to save {filename}: {e}")
        return
    if not url:
        print(f"🛑 No fifeUrl or encodedImage for {filename}")
        return
    print(f"✅ Downloading {filename}")
    try:
        # Read the whole body before creating the file, so a failed download leaves no
        # partial file behind for the next run to skip as "already exists".
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        with open(filename, "wb") as f:
            f.write(data)
    except urllib.error.HTTPError as e:
        print(f"⛔ Unable to download {filename} (HTTP {e.code})")
    except Exception as e:
        print(f"⛔ Error during download of {filename}: {e}")


def submit_image(api_token, email, prompt, index):
    model = prompt.get("model", DEFAULT_MODEL)
    body = {"model": model, "email": email, "prompt": prompt["prompt"]}
    for key in ("aspectRatio", "count", "seed"):
        if key in prompt:
            body[key] = prompt[key]

    print(f"🚀 {model} » Prompt #{index} • account {email} …")
    start = time.time()

    while True:
        req = urllib.request.Request(
            URL_IMAGES,
            method="POST",
            data=json.dumps(body).encode(),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_token}",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                media = data.get("media") or []
                if not media:
                    print(f"🛑 200 OK but no media (moderated?) for {model}")
                for i, m in enumerate(media):
                    gen = (m.get("image") or {}).get("generatedImage") or {}
                    download_image(gen, f"{model}_{i + 1}.jpg")
                print(f"🆗 {model} done ({time.time() - start:.0f} sec)")
                return 200
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                print(f"🔄️ Retry on HTTP {e.code}, waiting {SLEEP_RETRY}s")
                time.sleep(SLEEP_RETRY)
                continue
            print(f"🛑 {model} failed with HTTP {e.code}: {e.read().decode()[:200]}")
            return e.code


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 google-flow-nano-banana-compare.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]")
        sys.exit(1)

    api_token, email = sys.argv[1], sys.argv[2]
    prompt_file = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PROMPTS_FILE

    accounts = fetch_accounts(api_token)
    if email not in accounts:
        print(f"⛔ Account {email} not found. See https://useapi.net/docs/start-here/setup-google-flow")
        sys.exit(1)
    health = accounts[email].get("health")
    if health and health != "OK":
        print(f"⛔ Account {email} health is '{health}'.")
        sys.exit(1)

    with open(prompt_file, encoding="utf-8") as f:
        prompts = json.load(f)
    print(f"Comparing {len(prompts)} model runs …")

    start = time.time()
    for i, prompt in enumerate(prompts, 1):
        submit_image(api_token, email, prompt, i)
    print(f"COMPLETED • elapsed {time.time() - start:.0f} sec")


if __name__ == "__main__":
    main()
