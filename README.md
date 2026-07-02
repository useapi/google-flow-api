# Google Flow API examples (useapi.net)

Runnable Node.js and Python examples for the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net) — generate **Veo 3.1** video, **Gemini Omni Flash** audio-native video, and **Nano Banana 2 Lite** / **Nano Banana 2** / **Nano Banana Pro** images through a simple REST API that drives your own [Google Flow](https://labs.google/flow) subscription (no Google Cloud project, API key, or per-call metering).

Each example ships JavaScript and Python implementations (`.mjs` and `.py`) that read a list of prompts from `prompts.json`, submit them through the useapi.net Google Flow API, and download every result — so you can queue a batch and come back to the winners.

| Example | What it does | Tutorial |
|---|---|---|
| [`veo-video/`](./veo-video) | Batch-generate **Veo 3.1** video — text-to-video, first/last-frame image-to-video, reference-to-video | [Generate Veo 3.1 video via curl](https://useapi.net/docs/articles/google-flow-bash) |
| [`images/`](./images) | Batch-generate images with **Nano Banana 2**, **Nano Banana Pro** | [Generate images via curl](https://useapi.net/docs/articles/google-flow-images-bash) |
| [`nano-banana-compare/`](./nano-banana-compare) | Run one prompt through all three **Nano Banana** models (**2 Lite**, **2**, **Pro**) and compare | [Nano Banana 2 Lite vs 2 vs Pro compared](https://useapi.net/docs/articles/google-flow-nano-banana-compare) |
| [`omni-flash/`](./omni-flash) | Batch-generate **Gemini Omni Flash** audio-native video — text-to-video, reference-to-video, video-to-video edit | [Generate Omni Flash video via curl](https://useapi.net/docs/articles/omni-flash-bash) |

## Quick start

You need [Node.js](https://nodejs.org) v21 or newer **or** [Python](https://www.python.org) 3.x (neither has any dependencies to install), a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi), and a connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) (one [$15/month subscription](https://useapi.net/docs/subscription) covers every useapi.net API):

```bash
git clone https://github.com/useapi/google-flow-api.git
cd google-flow-api/veo-video
node ./google-flow.mjs <API_TOKEN> <EMAIL>
# or, equivalently, with Python:
python3 ./google-flow.py <API_TOKEN> <EMAIL>
```

Edit `prompts.json` in each folder to queue your own prompts. Every supported parameter is documented on the [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) and [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) endpoint pages.

## About useapi.net

[useapi.net](https://useapi.net) is an experimental REST API for AI services. The Google Flow API drives your own Google Flow / Google AI subscription, so you spend your plan's credits at consumer rates instead of metered developer-API pricing. See the [model matrix](https://useapi.net/model-matrix) and the pricing comparison on the [API overview](https://useapi.net/docs/api-google-flow-v1).

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@midjourneyapi).
