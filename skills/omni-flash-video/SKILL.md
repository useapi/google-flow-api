---
name: omni-flash-video
description: Generate AI video with Google's Omni 1.1 Flash (Gemini Omni Flash, audio-native video with spoken dialogue and voices) or Veo 3.1 through the useapi.net Google Flow API, on the user's own Google AI plan. Supports text-to-video, reference images of people or products, start and end frames, preset voices and video-to-video edits, and downloads the .mp4. Use when the user asks to make a video, clip, ad, talking-head, UGC or product video with Omni Flash, Gemini Omni, Veo 3.1 or Google Flow, or to automate Google Flow video from the command line. Needs curl, jq and a USEAPI_TOKEN environment variable.
license: MIT
compatibility: Needs bash, curl, jq and network access to api.useapi.net. Requires a useapi.net API token (USEAPI_TOKEN) and a Google account with a Google AI Plus, Pro or Ultra plan connected to useapi.net.
metadata:
  author: useapi.net
  homepage: https://github.com/useapi/google-flow-api
---

# Omni 1.1 Flash and Veo 3.1 video with the useapi.net Google Flow API

These scripts call the [useapi.net Google Flow API](https://useapi.net/docs/api-google-flow-v1), a third-party REST API that drives the user's own Google Flow account. Each clip spends Flow credits from the user's Google AI plan. Every script is in `scripts/` next to this file. Run them with bash.

## Before you start

1. `USEAPI_TOKEN` must be set. If it is missing, ask the user for their useapi.net API token (setup: https://useapi.net/docs/start-here/setup-useapi). Their Google account must already be connected (https://useapi.net/docs/start-here/setup-google-flow). Never print the token or write it to a file.
2. `USEAPI_EMAIL` is optional: the connected Google account to use. Leave it unset and the API picks the healthiest account.
3. `curl` and `jq` must be installed.

## Fastest path: one command

```bash
scripts/video.sh "<prompt>" [key=value ...]
```

Values that are existing local files (for `referenceImage_N`, `startImage`, `endImage`, `referenceVideo_1`) are uploaded first. It prints progress on stderr and the saved `.mp4` paths on stdout (`OUT_DIR` sets the folder, default the current one). A clip usually takes 1 to 3 minutes; run it in the background (in Claude Code, `run_in_background`) or with a timeout of at least 10 minutes, and do not start a second copy while it runs.

Examples:

```bash
# Text to video, 8 s landscape at 720p (the defaults)
scripts/video.sh "A lighthouse keeper climbs the spiral stairs at dusk, lantern swinging. Slow handheld follow shot."

# A presenter from a photo, speaking with a preset voice, portrait for Shorts/Reels
scripts/video.sh "The woman in @referenceImage_1 holds up the mug, smiles and says: 'Honestly the best coffee I've had all year.' Handheld phone camera." \
  referenceImage_1=./presenter.jpg referenceAudio_1=Kore aspectRatio=portrait duration=6

# Animate from a first frame to a last frame
scripts/video.sh "The paper boat drifts down the gutter stream and into the drain." startImage=./first.png endImage=./last.png

# A cheap draft: 360p costs about half; upscale the keeper later
scripts/video.sh "..." resolution=360p duration=4
```

## Costs and limits (Omni 1.1 Flash)

| Duration | Credits at 720p | At 360p |
|---|---|---|
| 4 s | 7 | 4 |
| 6 s | 10 | 5 |
| 8 s (default) | 12 | 6 |
| 10 s | 15 | 7 |
| Video-to-video edit | 20 | 10 |

- `aspectRatio`: `landscape` (default) or `portrait`. Ask the user which one; for phone video it is `portrait`, and forgetting it is the most common wasted generation.
- Omni tops out at 720p. `count` (1 to 4) multiplies the cost.
- Veo 3.1 (`model=veo-3.1-fast`, `veo-3.1-quality`, `veo-3.1-lite`) has no 360p, takes up to 3 reference images and one voice (neither on `veo-3.1-quality`), and also accepts 1:1, 4:3 and 3:4.
- Tell the user the credit cost before generating more than one clip or anything over 8 s.

## Writing prompts that work

- **Put the physical action first.** Models drop trailing clauses. "He blinks twice, then looks into the lens and says…" works; "…and then at the end he blinks" often does not happen.
- **Spoken lines go in quotes** after "says:". One or two short sentences per 8 s clip. A delivery note helps: "says, flat:", "whispers:".
- **A voice needs a face.** `referenceAudio_N` (a preset name like `Kore`, `Charon`, `Puck`, `Aoede`, or a voice id) only works together with a `referenceImage_N`, a `character_N` or a video edit. A voice on its own is rejected. Omni takes up to 5 voices for several speakers, Veo one.
- **Point at references in the prompt** with `@referenceImage_1`, `@character_1`, `@referenceAudio_1`. Each marker needs its matching parameter.
- **Name the camera**: "handheld phone camera", "static tripod shot", "slow push-in". UGC-style ads read as real with "handheld phone camera, natural light".
- **Omni takes up to 7 references** (`referenceImage_*` and `character_*` together; Veo 3). More references are slower and fail more often; 1 to 3 is the sweet spot.
- `startImage`/`endImage` mode takes no other references and no voice.

## Step by step (for more control)

1. Upload local files (each prints an asset id). Without `USEAPI_EMAIL`, set it to the first upload's account before the next upload, or the generation is rejected for mixing accounts; `video.sh` does this for you.
   ```bash
   IMG=$(scripts/upload.sh ./presenter.jpg)
   ```
2. Start the generation. It prints the job id (and logs it on stderr):
   ```bash
   JOB=$(scripts/generate.sh "The woman in @referenceImage_1 waves and says: 'Hi!'" referenceImage_1="$IMG" referenceAudio_1=Kore)
   ```
3. Wait for it (polls every 10 s) and save the final record:
   ```bash
   scripts/wait-job.sh "$JOB" > job.json
   ```
4. Download the video(s). Prints the saved paths:
   ```bash
   scripts/download.sh job.json ./out
   ```

All options of `generate.sh` are listed in its header and at https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos

## Timeouts and resuming

If a run is interrupted after `job j...` was logged, do not run it again: that spends the credits twice. Resume with the job id:

```bash
scripts/wait-job.sh "<jobid>" > job.json && scripts/download.sh job.json
```

The scripts never retry a generation request on their own, for the same reason.

## Errors

Every failed request prints the API's error and a one-line hint. The common ones:

- `HTTP 400`: a parameter was rejected (the message names it), or Google refused the content. For a content refusal, rephrase the prompt or change the image. Video-to-video moderation is not deterministic, so one plain resubmit can also clear it.
- `HTTP 401`: the token is wrong. `HTTP 404`: `USEAPI_EMAIL` is not a connected account.
- `HTTP 402`: the account has no Plus, Pro or Ultra plan, or no Flow credits left.
- `HTTP 403`: Google rejected the captcha on every try (wait a minute, try once more), or `MODEL_ACCESS_DENIED` (the plan does not include the model).
- `HTTP 429`: the account is busy or out of quota. `retryAfter` says when to try again; or unset `USEAPI_EMAIL` so the API uses another account. Do not loop on it.
- `HTTP 503`: Google is temporarily overloaded. Try again in a minute or two, with fewer references or a lower `count`.
- `HTTP 596`: the Google account needs reconnecting: https://useapi.net/docs/start-here/setup-google-flow

## After it finishes

Tell the user the file path(s), the duration and the credits it used. The video links in `job.json` stay valid for about 6 hours. The clip is also in the user's Google Flow project.
