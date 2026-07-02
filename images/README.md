# Nano Banana / Imagen 4 images — Google Flow API batch generation (Node.js & Python)

Batch-generate images with **Nano Banana 2** (`nano-banana-2`, Gemini 3.1 Flash Image), **Nano Banana Pro** (`nano-banana-pro`, Gemini 3 Pro Image), and **Imagen 4** (`imagen-4`) through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net).

📖 Full walkthrough: **[Generate AI images via curl and the Google Flow API](https://useapi.net/docs/articles/google-flow-images-bash)**

`google-flow-images.mjs` (Node.js) and `google-flow-images.py` (Python) are equivalent implementations — each reads prompts from `prompts.json`, uploads any reference images, and calls [`POST /images`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images). Because that endpoint is **synchronous**, the script writes each result image as soon as the call returns.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies to install)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) email (image generation works with free Google AI accounts)

## Usage

```bash
node ./google-flow-images.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
python3 ./google-flow-images.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`PROMPTS_FILE` defaults to `prompts.json`. The script looks the account up by email and checks its `health` field before submitting.

## Prompts

`prompts.json` is an array of prompt objects — `prompt` is the only required field; everything else falls back to the API defaults (model `imagen-4`, four variations, 16:9). Supported models include `imagen-4`, `nano-banana-2`, and `nano-banana-pro`.

- **Image-to-image:** pass a **local file path** as `reference_1` (uploaded automatically). `nano-banana-2` and `nano-banana-pro` accept up to 10 references (`reference_1`…`reference_10`).

Every parameter is documented on [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images). Local reference paths in `prompts.json` (e.g. `./reference_image.jpeg`) are inputs **you** supply — they are not included in this repo.

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
