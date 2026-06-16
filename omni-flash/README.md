# Gemini Omni Flash video — Google Flow API batch generation (Node.js)

Batch-generate **Gemini Omni Flash** audio-native video through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net) — synced dialogue, reference images, and video-to-video edits from a list of prompts.

📖 Full walkthrough: **[Generate audio-native AI video with Gemini Omni Flash](https://useapi.net/docs/articles/omni-flash-bash)**

`omni-flash.mjs` reads prompts from `prompts.json`, uploads any reference images or source videos, submits each job to [`POST /videos`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) in async mode with `model: "omni-flash"`, polls [`GET /jobs/{jobId}`](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs), and downloads every finished MP4.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) email (Omni Flash runs on Plus, Pro, and Ultra plans)

## Usage

```bash
node ./omni-flash.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`PROMPTS_FILE` defaults to `prompts.json`. The script looks the account up by email and checks its `health` field before submitting.

## Prompts

`prompts.json` is an array of prompt objects — `prompt` is the only required field; everything else falls back to the API defaults (model `omni-flash`, landscape, 8 seconds; durations 4 / 6 / 8 / 10 s).

- **Spoken dialogue:** set `referenceAudio_1` to a preset voice name (e.g. `Charon`, `Kore`) or a [`POST /voices`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-voices) user-voice id.
- **Reference-to-video:** use `referenceImage_1`…`referenceImage_7` (local file paths, uploaded for you).
- **Video-to-video edit:** set `referenceVideo_1` to a local MP4 plus `startFrameIndex_1` / `endFrameIndex_1` for the trim window (output max 10 s).

Every parameter is documented on [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos). Local image/video paths in `prompts.json` (e.g. `./subject.jpeg`, `./source.mp4`) are inputs **you** supply — they are not included in this repo.

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
