"""

Script version 1.0, September 4, 2026

Build a UGC product video end to end with the Google Flow API v1 by useapi.net 🚀

Runs the whole six-step pipeline from the tutorial: a product sheet per item and a presenter
via POST /images and POST /characters, one still that carries them all, one Omni 1.1 Flash clip
per product from that still via POST /videos (async, polled on GET /jobs/{jobId}), a free 1080p
POST /videos/upscale per clip, and one POST /videos/concatenate to join them.

Companion tutorial:
  https://useapi.net/docs/articles/google-flow-ugc-product-video

Every step is checkpointed to ugc_state.json, so a re-run resumes where it stopped instead of
paying for the finished steps again. The clips are the only part that costs credits (15 each at
10s/720p), so an interrupted run must never redo them silently.

Installation Instructions:
==========================

You need Python 3.x installed to run this script (standard library only, no dependencies):

- Windows, macOS, Linux: https://www.python.org/

Verify with:

   python3 --version

Running the Script:
===================

Usage: python3 ugc-product-video.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

python3 ugc-product-video.py user:1234-abcdefhijklmnopqrstuv my@email.com

To redo one step, delete its key from ugc_state.json and run again — everything after it is
rebuilt from the new result, everything before it is reused.

Changelog:
==========

- September 4, 2026: Initial release.

"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

STATE_FILE = "ugc_state.json"
ERRORS_FILE = "ugc_errors.txt"
DEFAULT_PROMPTS_FILE = "prompts.json"
SLEEP_429 = 30  # seconds
SLEEP_POLL = 15  # seconds
MAX_RETRIES = 10

URL_IMAGES = "https://api.useapi.net/v1/google-flow/images"
URL_CHARACTERS = "https://api.useapi.net/v1/google-flow/characters"
URL_VIDEOS = "https://api.useapi.net/v1/google-flow/videos"
URL_UPSCALE = "https://api.useapi.net/v1/google-flow/videos/upscale"
URL_CONCATENATE = "https://api.useapi.net/v1/google-flow/videos/concatenate"
URL_JOBS = "https://api.useapi.net/v1/google-flow/jobs/"


# --- checkpoint state ------------------------------------------------------
# Keys: sheets, portraitFront, portraitThreeQuarter, character, still,
#       clips, upscaled, joined. A key is written only once its step succeeded.
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    if state:
        print(f"♻️  Resuming from {STATE_FILE}, already done: {', '.join(state)}")
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def log_error(what, detail):
    with open(ERRORS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{what}\t{detail}\n")


def fail(what, detail):
    print(f"🛑 {what} — {detail}")
    log_error(what, detail)
    sys.exit(1)


# --- HTTP ------------------------------------------------------------------
# One POST with retries. 429 (concurrency) and 503 (upstream busy) are transient
# and cost nothing, so they are retried; everything else is reported and fatal.
def post(api_token, url, payload, what):
    body = json.dumps({k: v for k, v in payload.items() if v is not None}).encode()

    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_token}",
            },
            method="POST",
        )
        try:
            # POST /images and POST /videos answer 200 when synchronous, 201 when async.
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code in (429, 503):
                reason = "all generation slots busy" if e.code == 429 else "service unavailable"
                print(f"🔄️ {what} — {reason}, retry {attempt}/{MAX_RETRIES} in {SLEEP_429}s")
                time.sleep(SLEEP_429)
                continue
            if e.code == 400:
                fail(what, f"rejected (validation or content policy): {detail}")
            if e.code == 402:
                fail(what, f"no subscription or insufficient credits: {detail}")
            fail(what, f"HTTP {e.code}: {detail}")

    fail(what, f"still failing after {MAX_RETRIES} retries")


def get_json(api_token, url, what):
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "Authorization": f"Bearer {api_token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        fail(what, f"HTTP {e.code}: {e.read().decode(errors='replace')}")


# --- images ----------------------------------------------------------------
# POST /images is synchronous. With count > 1 it returns several candidates;
# all of them are saved so you can look, and candidate `pick` (default the
# first) is the one the pipeline carries forward.
def generate_image(api_token, email, spec, label, extra=None):
    started = time.time()
    count = spec.get("count", 1)
    print(f"🖼️  {label} — generating {count} candidate(s)…")

    payload = {
        "model": spec.get("model"),
        "email": email,
        "prompt": spec["prompt"],
        "aspectRatio": spec.get("aspectRatio"),
        "count": count,
        "seed": spec.get("seed"),
    }
    payload.update(extra or {})

    result = post(api_token, URL_IMAGES, payload, f"POST /images ({label})")
    media = result.get("media") or []
    if not media:
        fail(label, "no images returned by POST /images")

    for i, item in enumerate(media):
        save_image((item.get("image") or {}).get("generatedImage"), f"{label}_{i + 1}.png")

    pick = spec.get("pick", 0)
    generated = (media[pick].get("image") or {}).get("generatedImage") or {}
    chosen = generated.get("mediaGenerationId")
    if not chosen:
        fail(label, f"candidate #{pick + 1} of {len(media)} has no mediaGenerationId")

    print(f"✅ {label} — using candidate #{pick + 1} of {len(media)} ({time.time() - started:.1f} sec)")
    return chosen


# A generated image arrives either as a signed URL or inline base64, never both.
def save_image(generated_image, filename):
    if not generated_image:
        return
    try:
        if generated_image.get("fifeUrl"):
            with urllib.request.urlopen(generated_image["fifeUrl"]) as resp, open(filename, "wb") as f:
                f.write(resp.read())
        elif generated_image.get("encodedImage"):
            with open(filename, "wb") as f:
                f.write(base64.b64decode(generated_image["encodedImage"]))
        else:
            print(f"⛔ {filename} — response carried neither fifeUrl nor encodedImage")
            return
        print(f"   💾 {filename}")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
        print(f"⛔ Error saving {filename}: {e}")


# --- videos ----------------------------------------------------------------
# First-plus-last-frame mode: the still goes in both slots. On omni-flash this
# mode accepts nothing else — no reference images, no character, no voice — so
# everything the clip needs must already be in the still.
def generate_clip(api_token, email, clip, still_id, index):
    print(f"🎬 Clip #{index + 1} ({clip['name']}) — submitting {clip['duration']}s at {clip['resolution']}…")

    result = post(
        api_token,
        URL_VIDEOS,
        {
            "model": clip.get("model"),
            "email": email,
            "prompt": clip["prompt"],
            "aspectRatio": clip.get("aspectRatio"),
            "duration": clip.get("duration"),
            "resolution": clip.get("resolution"),
            "startImage": still_id,
            "endImage": still_id,
            "async": True,
        },
        f"POST /videos ({clip['name']})",
    )

    # The 201 async payload uses lowercase "jobid"; a sync 200 uses "jobId". Accept either.
    job_id = result.get("jobid") or result.get("jobId")
    if not job_id:
        fail(clip["name"], "no jobid in POST /videos response")

    print(f"   ⏳ jobId {job_id}")
    return job_id


# Poll GET /jobs/{jobId} until the clip is done, then download it.
def await_clip(api_token, job_id, filename):
    started = time.time()

    while True:
        job = get_json(api_token, f"{URL_JOBS}{job_id}", f"GET /jobs/{job_id}")
        status = job.get("status")

        if status == "failed":
            fail(job_id, f"job failed: {job.get('error')}")

        if status == "completed":
            media = ((job.get("response") or {}).get("media") or [None])[0]
            if not media or not media.get("mediaGenerationId"):
                fail(job_id, "completed with no media")
            print(f"✅ {job_id} completed ({time.time() - started:.1f} sec)")
            download_video(media.get("videoUrl"), filename)
            return media["mediaGenerationId"]

        print(f"   ⌛ {job_id} is {status}, waiting…")
        time.sleep(SLEEP_POLL)


def download_video(url, filename):
    if not url:
        print(f"⛔ {filename} — no videoUrl to download")
        return
    try:
        with urllib.request.urlopen(url) as resp, open(filename, "wb") as f:
            f.write(resp.read())
        print(f"   💾 {filename}")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
        print(f"⛔ Error downloading {filename}: {e}")


# --- the six steps ---------------------------------------------------------
def execute(api_token, email, prompts_file):
    with open(prompts_file, encoding="utf-8") as f:
        config = json.load(f)

    model = config.get("model")
    video_model = config.get("videoModel")
    products = config["products"]
    presenter = config["presenter"]
    still = config["still"]
    clips = config["clips"]
    upscale = config["upscale"]
    join = config.get("join") or []
    output = config.get("output", "ugc-product-video.mp4")

    if len(products) != len(clips):
        print(f"⛔ {prompts_file} has {len(products)} products but {len(clips)} clips — one clip per product is expected.")
        sys.exit(1)
    if len(products) > 10:
        print(f"⛔ POST /images accepts at most 10 reference_* slots, but {len(products)} products were given.")
        sys.exit(1)

    state = load_state()

    # Step 1 — a sheet for each product. Four views of one item on one image, so
    # the model gets the whole object instead of one lucky angle.
    if "sheets" not in state:
        print(f"\n━━ Step 1/6 — a sheet for each of the {len(products)} products ━━")
        state["sheets"] = [
            generate_image(api_token, email, dict(product, model=model), f"01-sheet-{product['name']}")
            for product in products
        ]
        save_state(state)

    # Step 2 — the presenter. A front portrait, a three-quarter generated FROM it
    # so the two agree on the face, then a character built from both.
    if "portraitFront" not in state:
        print("\n━━ Step 2/6 — the presenter ━━")
        state["portraitFront"] = generate_image(
            api_token, email, dict(presenter["front"], model=model), "02-presenter-front"
        )
        save_state(state)

    if "portraitThreeQuarter" not in state:
        state["portraitThreeQuarter"] = generate_image(
            api_token,
            email,
            dict(presenter["threeQuarter"], model=model),
            "03-presenter-three-quarter",
            {"reference_1": state["portraitFront"]},
        )
        save_state(state)

    if "character" not in state:
        print(f"👤 Character \"{presenter['displayName']}\" — from both portraits…")
        result = post(
            api_token,
            URL_CHARACTERS,
            {
                "displayName": presenter["displayName"],
                "personalityNotes": presenter.get("personalityNotes"),
                "imageReference_1": state["portraitFront"],
                "imageReference_2": state["portraitThreeQuarter"],
                "voice": presenter.get("voice"),
            },
            "POST /characters",
        )
        if not result.get("character"):
            fail("characters", "no character field in response")
        state["character"] = result["character"]
        save_state(state)
        print("✅ Character created")

    # Step 3 — the still. Character in character_1, every sheet in reference_N,
    # placed by @-marker in the prompt. This one frame carries the whole scene.
    if "still" not in state:
        print("\n━━ Step 3/6 — the still ━━")
        extra = {"character_1": state["character"]}
        for i, sheet in enumerate(state["sheets"]):
            extra[f"reference_{i + 1}"] = sheet
        state["still"] = generate_image(api_token, email, dict(still, model=model), "04-still", extra)
        save_state(state)

    # Step 4 — one clip per product, every one starting and ending on the still,
    # so any clip can follow any other. This is the only step that costs credits.
    if "clips" not in state:
        print(f"\n━━ Step 4/6 — {len(clips)} clips, all from the still ━━")

        # Submit them all first, then collect — they generate in parallel.
        jobs = [
            generate_clip(api_token, email, dict(clip, model=video_model), state["still"], i)
            for i, clip in enumerate(clips)
        ]
        state["clips"] = [
            await_clip(api_token, job_id, f"05-clip-{i + 1}-{clips[i]['name']}-720p.mp4")
            for i, job_id in enumerate(jobs)
        ]
        save_state(state)

    # Step 5 — upscale to 1080p. Free on any paid plan, synchronous, and the new
    # id is just the source id with _upsampled on the end.
    if "upscaled" not in state:
        print(f"\n━━ Step 5/6 — upscale to {upscale['resolution']} ━━")
        upscaled = []
        for i, clip_id in enumerate(state["clips"]):
            started = time.time()
            print(f"⬆️  Clip #{i + 1} ({clips[i]['name']}) — upscaling…")
            result = post(
                api_token,
                URL_UPSCALE,
                {"mediaGenerationId": clip_id, "resolution": upscale["resolution"]},
                f"POST /videos/upscale ({clips[i]['name']})",
            )
            media = (result.get("media") or [None])[0]
            if not media or not media.get("mediaGenerationId"):
                fail(clips[i]["name"], "upscale returned no media")
            print(f"✅ Clip #{i + 1} upscaled ({time.time() - started:.1f} sec)")
            download_video(
                media.get("videoUrl"),
                f"06-clip-{i + 1}-{clips[i]['name']}-{upscale['resolution']}.mp4",
            )
            upscaled.append(media["mediaGenerationId"])
        state["upscaled"] = upscaled
        save_state(state)

    # Step 6 — join them. Trim to the sound, not the picture: she goes still
    # before she stops talking, so a cut at the first still frame clips a line.
    if "joined" not in state:
        print("\n━━ Step 6/6 — join ━━")
        started = time.time()
        media = [
            dict({"mediaGenerationId": media_id}, **(join[i] if i < len(join) else {}))
            for i, media_id in enumerate(state["upscaled"])
        ]

        result = post(api_token, URL_CONCATENATE, {"media": media}, "POST /videos/concatenate")
        if not result.get("encodedVideo"):
            fail("concatenate", "no encodedVideo in response")

        with open(output, "wb") as f:
            f.write(base64.b64decode(result["encodedVideo"]))
        state["joined"] = output
        save_state(state)
        print(f"✅ Joined {len(media)} clips ({time.time() - started:.1f} sec)")
        print(f"   💾 {output}")

    print(f"\n🎉 Done — {state['joined']}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ugc-product-video.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]")
        print("Example: python3 ugc-product-video.py user:1234-abcdefhijklmnopqrstuv my@email.com")
        sys.exit(1)

    api_token = sys.argv[1]
    email = sys.argv[2]
    prompts_file = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PROMPTS_FILE

    execute(api_token, email, prompts_file)


if __name__ == "__main__":
    main()
