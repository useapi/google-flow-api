# Veo 3.1 video — Google Flow API batch generation (Node.js)

Batch-generate [Veo 3.1](https://aistudio.google.com/models/veo-3) video through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net).

📖 Full walkthrough: **[Generate AI video with Veo 3.1 via curl and the Google Flow API](https://useapi.net/docs/articles/google-flow-bash)**

`google-flow.mjs` reads prompts from `prompts.json`, uploads any start/end-frame images, submits each job to [`POST /videos`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) in async mode, polls [`GET /jobs/{jobId}`](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs), and downloads every finished MP4.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) email

## Usage

```bash
node ./google-flow.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`PROMPTS_FILE` defaults to `prompts.json`. The script looks the account up by email and checks its `health` field before submitting.

## Prompts

`prompts.json` is an array of prompt objects — `prompt` is the only required field; everything else falls back to the API defaults (model `veo-3.1-fast`, landscape, 8 seconds). Supported models include `veo-3.1-fast`, `veo-3.1-quality`, `veo-3.1-lite`, `veo-3.1-lite-low-priority`, and `omni-flash`.

- **Image-to-video:** set `startImage` (and optionally `endImage`) to a **local file path** — the script uploads it for you.
- **Reference-to-video:** use `referenceImage_1`…`referenceImage_3`.

Every parameter is documented on [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos). Local image paths in `prompts.json` (e.g. `./first_image.jpeg`) are inputs **you** supply — they are not included in this repo.

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
