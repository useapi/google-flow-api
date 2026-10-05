# Google Flow API examples (useapi.net)

Runnable Node.js and Python examples for the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) — generate **Veo 3.1** video, **Gemini Omni Flash** audio-native video, and **Nano Banana 2 Lite** / **Nano Banana 2** / **Nano Banana Pro** images through a simple REST API that drives your own [Google Flow](https://flow.google.com) subscription (no Google Cloud project, API key, or per-call metering).

Each example ships JavaScript and Python implementations (`.mjs` and `.py`) driven by a `prompts.json` you edit. Most are batch runners: they submit every prompt in the file and download every result, so you can queue a batch and come back to the winners. [`ugc-product-video/`](./ugc-product-video) is a pipeline instead — it chains six endpoints into one finished video, checkpointing as it goes.

| Example | What it does | Tutorial | Tutorial date |
|---|---|---|---|
| [`veo-video/`](./veo-video) | Batch-generate **Veo 3.1** video — text-to-video, first/last-frame image-to-video | [Generate Veo 3.1 video via curl](https://useapi.net/docs/articles/google-flow-bash) | June 15, 2026 (September 11, 2026) |
| [`images/`](./images) | Batch-generate images with **Nano Banana 2 Lite** (default), **Nano Banana 2**, **Nano Banana Pro** | [Generate images via curl](https://useapi.net/docs/articles/google-flow-images-bash) | June 15, 2026 (September 11, 2026) |
| [`nano-banana-compare/`](./nano-banana-compare) | Run one prompt through all three **Nano Banana** models (**2 Lite**, **2**, **Pro**) and compare | [Nano Banana 2 Lite vs 2 vs Pro compared](https://useapi.net/docs/articles/google-flow-nano-banana-compare) | July 2, 2026 (September 11, 2026) |
| [`omni-flash/`](./omni-flash) | Batch-generate **Gemini Omni Flash** audio-native video — text-to-video, first/last-frame image-to-video, reference-to-video, video-to-video edit | [Generate Omni Flash video via curl](https://useapi.net/docs/articles/omni-flash-bash) | June 15, 2026 (September 11, 2026) |
| [`ugc-product-video/`](./ugc-product-video) | Build a whole **UGC product video** — product sheets, a presenter, one still, an **Omni 1.1 Flash** clip per product, upscaled and joined | [Make a UGC product video](https://useapi.net/docs/articles/google-flow-ugc-product-video) | September 4, 2026 |
| [`n8n/`](./n8n) | Ready-to-import **n8n** workflow: a form that generates **Veo 3.1** video or **Nano Banana Pro** images and returns the files | [n8n template #19991](https://n8n.io/workflows/19991) | September 28, 2026 |
| [`n8n/ugc-ad-factory.json`](./n8n/ugc-ad-factory.json) | Ready-to-import **n8n** form workflow that builds a whole **UGC video ad** with **Omni 1.1 Flash**: pick or re-roll at every step, upload your own product photos, 1–5 products, 1080p | [Make UGC video ads in n8n](https://useapi.net/docs/articles/google-flow-n8n-ugc-ads) | October 3, 2026 |

## Quick start

You need [Node.js](https://nodejs.org) v21 or newer **or** [Python](https://www.python.org) 3.x (neither has any dependencies to install), a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), and a connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) (one [$15/month subscription](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) covers every useapi.net API):

```bash
git clone https://github.com/useapi/google-flow-api.git
cd google-flow-api/veo-video
node ./google-flow.mjs <API_TOKEN> <EMAIL>
# or, equivalently, with Python:
python3 ./google-flow.py <API_TOKEN> <EMAIL>
```

Edit `prompts.json` in each folder to queue your own prompts. Every supported parameter is documented on the [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) and [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) endpoint pages.

## Common questions

- **Does Google Flow have an official API or API key?** No. Flow is a web app only, and Google doesn't issue a Google Flow API key. Veo 3.1, Omni 1.1 Flash and Nano Banana are sold separately on the metered Gemini API (Omni since June 30, 2026, about $0.10 per second of 720p video). This API drives your own Flow account instead.
- **So what do I use as the API key?** A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api). Then connect your own Google account once through the [Google Flow setup](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github&utm_medium=referral&utm_campaign=google-flow-api): sign in with Google, with no cookies to copy and no Google Cloud project or Gemini API key. The only other key is a captcha provider's, which you add once the 300 free solves on your first account run out.
- **What does the Google Flow API cost?** A flat [$15/month](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) to useapi.net, which covers 3 Google Flow accounts and every other useapi.net API, plus the Google AI plan you already have. Images work even on a free Google account, and video spends your plan's Flow credits. For an 8-second clip, the official Gemini API charges $0.80 for Veo 3.1 Fast, $3.20 for Veo 3.1 Quality, $0.40 for Veo 3.1 Lite and about $0.81 for Omni 1.1 Flash at 720p. Through Flow, the same clips cost about $0.40, $2.00, $0.20 and $0.24 in credits on the Pro plan, or $0.10, $1.00, $0.05 and $0.12 on Ultra. A Nano Banana Pro image is $0.134 on the Gemini API and included in Flow. Captcha solves cost about $0.80–$3.00 per 1,000 through your own provider. See the [pricing comparison](https://useapi.net/docs/api-google-flow-v1?utm_source=github&utm_medium=referral&utm_campaign=google-flow-api#pricing).
- More answers: [Google Flow API questions](https://useapi.net/docs/api-google-flow-v1#questions).

## 中文说明

这是 [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) 托管的 Google Flow API 示例代码（Node.js 与 Python）。通过 REST API 调用 **Veo 3.1** 视频、**Omni Flash** 带音频视频，以及 **Nano Banana 2 Lite / Nano Banana 2 / Nano Banana Pro** 图片生成。

- 使用你自己的 Google 账号和 Google AI 订阅，已支持新域名 `flow.google.com`。
- 无需 Google Cloud 项目或 Gemini API Key，无需自己部署服务或维护浏览器。
- 账号通过自动化浏览器流程绑定，登录 Google 即可，无需手动复制 Cookie。
- reCAPTCHA 由服务端自动处理（首个账号赠送 300 次免费打码，之后接入你自己的打码服务）。
- 价格：useapi.net 每月 15 美元（含 3 个 Google Flow 账号及所有其他 API），加上你已有的 Google AI 订阅。图片生成在免费 Google 账号上也可使用。

中文教程（Veo 3.1、Omni 1.1 Flash、Nano Banana Pro，含价格对比与示例）：[如何通过 Google Flow API 调用 Veo 3.1、Omni 1.1 Flash 和 Nano Banana Pro](https://useapi.net/docs/articles/google-flow-api-zh)。快速开始见上方 [Quick start](#quick-start)，完整文档：[Google Flow API](https://useapi.net/docs/api-google-flow-v1)。

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) is an experimental REST API for AI services. The Google Flow API drives your own Google Flow / Google AI subscription, so you spend your plan's credits at consumer rates instead of metered developer-API pricing. See the [model matrix](https://useapi.net/model-matrix?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) and the pricing comparison on the [API overview](https://useapi.net/docs/api-google-flow-v1).

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@useapi-net).

## License

The example code in this repository is released under the [MIT License](./LICENSE). It covers the example scripts only, not the useapi.net service or API.
