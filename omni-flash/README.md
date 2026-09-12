# Gemini Omni Flash video — Google Flow API batch generation (Node.js & Python)

Batch-generate **Gemini Omni Flash** audio-native video through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) — synced dialogue, reference images and characters, start/end frames, and video-to-video edits from a list of prompts.

📖 Full walkthrough: **[How to Generate Audio-Native AI Video with Gemini Omni Flash via the Google Flow API](https://useapi.net/docs/articles/omni-flash-bash)** — June 15, 2026 (September 11, 2026)

`omni-flash.mjs` (Node.js) and `omni-flash.py` (Python) are equivalent implementations — each reads prompts from `prompts.json`, uploads any reference images, start/end frames or source videos, submits each job to [`POST /videos`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) in async mode with `model: "omni-flash"`, polls [`GET /jobs/{jobId}`](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs), and downloads every finished MP4.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies to install)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) email (Omni Flash runs on Plus, Pro, and Ultra plans)

## Usage

```bash
node ./omni-flash.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
python3 ./omni-flash.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`PROMPTS_FILE` defaults to `prompts.json`. The script looks the account up by email and checks its `health` field before submitting.

## Prompts

`prompts.json` is an array of prompt objects — `prompt` is the only required field; everything else falls back to the API defaults (model `omni-flash`, landscape, 8 seconds at 720p; durations 4 / 6 / 8 / 10 s).

- **Spoken dialogue:** set `referenceAudio_1` to a preset voice name (e.g. `Charon`, `Kore`) or a [`POST /voices`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-voices) user-voice id. The voice needs a `referenceImage_*` or `character_*` in the same prompt (or a video-to-video edit via `referenceVideo_1`) — a voice on its own is rejected.
- **Reference-to-video:** use `referenceImage_1`…`referenceImage_7` (local file paths, uploaded for you).
- **Characters:** set `character_1`…`character_7` to character ids from [`POST /characters`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-characters) (sent as-is). They drive reference-to-video like `referenceImage_*`, and each character's images count toward the same 7-reference budget.
- **Image-to-video:** set `startImage` to a local file path for the first frame, and optionally `endImage` for the last frame (uploaded for you). `endImage` requires `startImage`, and the frames are the only input in this mode — no `referenceImage_*`, `character_*`, `referenceAudio_*` or `referenceVideo_1` alongside them.
- **Video-to-video edit:** set `referenceVideo_1` to a local MP4 plus `startFrameIndex_1` / `endFrameIndex_1` for the trim window (output max 10 s).
- **Resolution:** `resolution` is `720p` (default) or `360p`, which costs about half the credits and can be promoted to 720p later with [`POST /videos/upscale`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-upscale).

Every parameter is documented on [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos). Local image/video paths in `prompts.json` (e.g. `./subject.jpeg`, `./first_image.jpeg`, `./source.mp4`) are inputs **you** supply — they are not included in this repo.

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
