# Nano Banana 2 Lite vs 2 vs Pro — Google Flow image model comparison (Node.js & Python)

Run the **same prompt** through all three Google Flow Nano Banana image models — **Nano Banana 2 Lite** (`nano-banana-2-lite`, Gemini 3.1 Flash-Lite Image, the default), **Nano Banana 2** (`nano-banana-2`, Gemini 3.1 Flash Image), and **Nano Banana Pro** (`nano-banana-pro`, Gemini 3 Pro Image) — through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net), and download every result labeled by model.

📖 Full walkthrough: **[Nano Banana 2 Lite vs 2 vs Pro: Google Flow Image Models Compared](https://useapi.net/docs/articles/google-flow-nano-banana-compare)**

`google-flow-nano-banana-compare.mjs` (Node.js) and `google-flow-nano-banana-compare.py` (Python) are equivalent implementations — each reads `prompts.json` (one entry per model) and calls [`POST /images`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images). Because that endpoint is **synchronous**, the script writes each result image as soon as the call returns.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) email (image generation works with free Google AI accounts)

## Usage

```bash
node ./google-flow-nano-banana-compare.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
python3 ./google-flow-nano-banana-compare.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`PROMPTS_FILE` defaults to `prompts.json`. The script looks the account up by email and checks its `health` field before submitting, and sends no `captchaToken` — the useapi.net worker solves the reCAPTCHA automatically. Output images are named `<model>_<n>.jpg`.

## Prompts

`prompts.json` is an array of prompt objects — one per model, all with the same `prompt` so you can compare interpretations. `prompt` is the only required field; `model`, `aspectRatio`, `count`, and `seed` fall back to the API defaults (model `nano-banana-2-lite`, four variations, 16:9). All three models accept up to 10 reference images (`reference_1`…`reference_10`), the `auto` aspect ratio in image-to-image mode, and [2K/4K upscaling](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images-upscale).

Every parameter is documented on [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images).

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
