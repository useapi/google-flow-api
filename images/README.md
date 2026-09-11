# Nano Banana 2 & Nano Banana Pro images — Google Flow API batch generation (Node.js & Python)

Batch-generate images with **Nano Banana 2** (`nano-banana-2`, Gemini 3.1 Flash Image), **Nano Banana Pro** (`nano-banana-pro`, Gemini 3 Pro Image), and **Nano Banana 2 Lite** (`nano-banana-2-lite`, Gemini 3.1 Flash-Lite Image) through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net).

📖 Full walkthrough: **[How to Generate Nano Banana 2 & Nano Banana Pro Images via the Google Flow API](https://useapi.net/docs/articles/google-flow-images-bash)**

`google-flow-images.mjs` (Node.js) and `google-flow-images.py` (Python) are equivalent implementations — each reads prompts from `prompts.json`, uploads any reference images, and calls [`POST /images`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images). Because that endpoint is **synchronous**, the script writes each result image as soon as the call returns — downloaded from `fifeUrl`, or decoded from `encodedImage` on the rare response where `fifeUrl` is absent.

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

`prompts.json` is an array of prompt objects — `prompt` is the only required field; everything else falls back to the API defaults (model `nano-banana-2-lite`, four variations, 16:9). Supported models are `nano-banana-2-lite`, `nano-banana-2`, and `nano-banana-pro`. `imagen-4` is still accepted as a deprecated alias for `nano-banana-2-lite` (Google removed Imagen from Flow in July 2026).

- **Image-to-image:** pass a **local file path** as `reference_1` (uploaded automatically — PNG, JPEG or WebP). All three models accept up to 10 references (`reference_1`…`reference_10`).

Every parameter is documented on [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images). Local reference paths in `prompts.json` (e.g. `./reference_image.jpeg`) are inputs **you** supply — they are not included in this repo.

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
