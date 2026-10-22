# Google Flow API examples (useapi.net)

Runnable Node.js and Python examples for the [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) — generate Veo 3.1 Fast, Quality and Lite video, Omni 1.1 Flash audio-native video, and Nano Banana Pro, 2.1 and 2 Lite images through a REST API that runs on your [Google AI subscription](https://gemini.google/subscriptions/) for [Google Flow](https://flow.google.com): Free, Plus $4.99, Pro $19.99, Ultra $99.99 or Ultra $199.99 a month (as of October 2026). No Google Cloud project, no Gemini API key, no per-call metering.

Each example ships JavaScript and Python implementations (`.mjs` and `.py`) driven by a `prompts.json` you edit. Most are batch runners: they submit every prompt in the file and download every result, so you can queue a batch and come back to the winners. [`ugc-product-video/`](./ugc-product-video) is a pipeline instead — it chains six endpoints into one finished video, checkpointing as it goes.

| Example | What it does | Tutorial | Tutorial date |
|---|---|---|---|
| [`demo/`](./demo) | **Live agent chat app**: a browser chat with Google Flow's creative agent through the API, with answers streamed live, the agent's images and videos inline (full-size view, download, reuse), uploads, characters and voices attached along the way, spending approvals, a Library and the agent's settings. Open the [live demo](https://useapi.net/demos/google-flow/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) or open `demo/index.html` locally. Vanilla JS, no build | [Agent overview](https://useapi.net/docs/api-google-flow-v1/agent?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), [Chat with Google Flow Agent](https://useapi.net/docs/articles/google-flow-agent-chat?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | October 16, 2026 |
| [`veo-video/`](./veo-video) | Batch-generate **Veo 3.1** video — text-to-video, first/last-frame image-to-video | [Generate Veo 3.1 video via curl](https://useapi.net/docs/articles/google-flow-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | June 15, 2026 (October 20, 2026) |
| [`images/`](./images) | Batch-generate images with **Nano Banana 2 Lite** (default), **Nano Banana 2.1**, **Nano Banana Pro** | [Generate images via curl](https://useapi.net/docs/articles/google-flow-images-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | June 15, 2026 (October 20, 2026) |
| [`nano-banana-compare/`](./nano-banana-compare) | Run one prompt through all three **Nano Banana** models (**2 Lite**, **2.1**, **Pro**) and compare | [Nano Banana 2 Lite vs 2.1 vs Pro compared](https://useapi.net/docs/articles/google-flow-nano-banana-compare?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | July 2, 2026 (October 20, 2026) |
| [`omni-flash/`](./omni-flash) | Batch-generate **Omni 1.1 Flash** audio-native video — text-to-video, first/last-frame image-to-video, reference-to-video, video-to-video edit | [Generate Omni 1.1 Flash video via curl](https://useapi.net/docs/articles/omni-flash-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | June 15, 2026 (October 20, 2026) |
| [`ugc-product-video/`](./ugc-product-video) | Build a whole **UGC product video** — product sheets, a presenter, one still, an **Omni 1.1 Flash** clip per product, upscaled and joined | [Make a UGC product video](https://useapi.net/docs/articles/google-flow-ugc-product-video?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | September 4, 2026 (October 20, 2026) |
| [`n8n/`](./n8n) | Ready-to-import **n8n** workflow: a form that generates **Veo 3.1** video or **Nano Banana Pro** images and returns the files | [n8n template #19991](https://n8n.io/workflows/19991-generate-veo-31-videos-and-nano-banana-pro-images-with-google-flow/) | September 28, 2026 |
| [`n8n/ugc-ad-factory.json`](./n8n/ugc-ad-factory.json) | Ready-to-import **n8n** form workflow that builds a whole **UGC video ad** with **Omni 1.1 Flash**: pick or re-roll at every step, upload your own product photos, 1–5 products, 1080p | [Make UGC video ads in n8n](https://useapi.net/docs/articles/google-flow-n8n-ugc-ads?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | October 3, 2026 (October 20, 2026) |
| [`skills/omni-flash-video/`](./skills/omni-flash-video) | **Agent skill** for Claude Code, Codex and Cursor: ask for a clip and the agent makes it with **Omni 1.1 Flash** or **Veo 3.1** (dialogue, voices, reference images, first/last frames) and downloads the `.mp4`. Install: `npx skills add useapi/google-flow-api --skill omni-flash-video` | [SKILL.md](./skills/omni-flash-video/SKILL.md) |

## Quick start

You need [Node.js](https://nodejs.org) v21 or newer or [Python](https://www.python.org) 3.x (neither has any dependencies to install), a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), and a connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) (one [$15/month subscription](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) covers every useapi.net API and 3 Google accounts):

```bash
git clone https://github.com/useapi/google-flow-api.git
cd google-flow-api/veo-video
node ./google-flow.mjs <API_TOKEN> <EMAIL>
# or, equivalently, with Python:
python3 ./google-flow.py <API_TOKEN> <EMAIL>
```

Edit `prompts.json` in each folder to queue your own prompts. Every supported parameter is documented on the [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) and [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) endpoint pages.

## MCP server

useapi.net also runs a hosted [Model Context Protocol](https://modelcontextprotocol.io) server for Google Flow, so an AI assistant such as Claude Code, Cursor or VS Code Copilot can use it on your Google Flow account. It has 12 tools: chat with Google Flow Agent, attach images, a video, voices and characters, answer its requests to spend credits, manage chats, set the project's approval mode, instructions and default models, list the account's characters, voices, images and videos, and upload images. Nothing to install or run locally.

- Endpoint: `https://api.useapi.net/v1/google-flow/mcp`
- Transport: Streamable HTTP
- Authorization: your useapi.net API token in the `Authorization: Bearer …` header, and an account connected with the [Google Flow setup](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- Listed in the official MCP Registry as `net.useapi/google-flow`

Claude Code:

```bash
claude mcp add --transport http useapi-google-flow https://api.useapi.net/v1/google-flow/mcp --header "Authorization: Bearer YOUR_API_TOKEN"
```

Cursor, VS Code, Windsurf and the full tool list: [Google Flow MCP server docs](https://useapi.net/docs/api-google-flow-v1/mcp?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api). useapi.net is a third-party API, not affiliated with Google.

## Use with Claude Code

This repo is also a Claude Code plugin marketplace. The plugin adds the hosted Google Flow MCP server and the `omni-flash-video` agent skill, and reads your token from the `USEAPI_TOKEN` environment variable, so set it before you start Claude Code:

```bash
export USEAPI_TOKEN=user:12345-...      # your useapi.net API token
```

Then, inside Claude Code:

```
/plugin marketplace add useapi/google-flow-api
/plugin install google-flow@useapi-google-flow
```

On Claude Code 2.1.275 or later, `/plugin install google-flow --marketplace useapi/google-flow-api` does both in one step. Run `/mcp` to check that `useapi-google-flow` is connected.

## Use with Gemini CLI

This repo is also a Gemini CLI extension with the same MCP server and the `omni-flash-video` agent skill:

```bash
gemini extensions install https://github.com/useapi/google-flow-api
```

The install asks for your useapi.net API token and keeps it in the system keychain. Change it later with `gemini extensions config useapi-google-flow`, and check the connection with `gemini mcp list`. The `omni-flash-video` skill's scripts read `USEAPI_TOKEN` from your shell, so export it as well if you use the skill.

## Common questions

<!-- Figures verified 2026-10-20, the same as the useapi.net Google Flow API overview (docs/api-google-flow-v1/index.md and _includes/google-flow/price-table.md). Official: Veo on https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing (Veo 3.1 Fast $0.10/s = $0.80 per 8 s), Omni 1.1 Flash and Nano Banana on https://ai.google.dev/gemini-api/docs/pricing ($17.50 per 1M output tokens at 5,792 tokens per 720p second = ~$0.81 per 8 s, Nano Banana Pro $0.134 per image). Flow: Pro $19.99 / 1,000 credits, Ultra $199.99 / 25,000 credits, Veo 3.1 Fast 20 credits (10 on Ultra), Omni 8 s 12 credits, images 0 credits. The useapi.net subscription is not part of the per-video math. -->

- **Does Google Flow have an API or an API key?** Through useapi.net, yes. Google offers [Flow](https://flow.google.com) only as a website, with no public API and no Flow API key (as of October 2026). The useapi.net Google Flow API runs Veo 3.1, Omni 1.1 Flash and Nano Banana Pro, 2.1 and 2 Lite over REST on your Google AI subscription, with a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) as the key, and also chats with [Google Flow Agent](https://useapi.net/docs/api-google-flow-v1/agent?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), which Google offers only inside the Flow website.
- **How do I connect my Google account?** Through the useapi.net [automated browser setup](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api): sign in with Google once, with no cookies to copy and no Google Cloud project or Gemini API key, and it's done in about a minute. Captchas are solved for you: your first account gets 300 free, then your own captcha provider costs about $0.80 to $3.00 per 1,000. To connect by hand, the [Google Account Setup](https://github.com/useapi/google-account-setup) scripts (Windows, macOS, Linux) open a clean, single-use browser profile, so the cookies you copy keep working.
- **How much does the Google Flow API cost?** Through useapi.net, an 8-second Veo 3.1 Fast video costs $0.08 in Flow credits on Google AI Ultra $199.99 and $0.40 on Pro $19.99, against $0.80 on Google's [Agent Platform](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing). An 8-second Omni 1.1 Flash video costs $0.10 on Ultra $199.99, against $0.81 on the [Gemini API](https://ai.google.dev/gemini-api/docs/pricing), and Nano Banana Pro images use no credits, against $0.134 each (as of October 2026). The [price table](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#pricing) shows every model on every subscription.
- **Is there a free Google Flow API?** Through useapi.net, yes: a free Google account makes Nano Banana images and Veo 3.1 Fast and Lite videos on its 50 daily Flow credits, enough for 2 Fast or 5 Lite videos, while Google's Gemini API charges for every image and every second of video (as of October 2026). Upscaling an image to 2K is free on every account too. Omni 1.1 Flash and video upscaling need a paid Google AI subscription.
- **Is there a second Omni allowance?** Through useapi.net, yes: the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) makes Omni 1.1 Flash video on the same Google AI subscription from Vids' own monthly allowance, separate from Flow credits and with no captcha. On Ultra $199.99 the two allowances together come to about 2,666 ten-second Omni clips a month on one Google account. Examples: [useapi/google-vids-api](https://github.com/useapi/google-vids-api).
- More answers: [Google Flow API questions](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#questions).

## More articles

- [Veo 3.1 API Pricing: Official Google Veo API vs Google Flow API](https://useapi.net/docs/articles/veo-3-1-api-pricing?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [Google Flow Errors Explained: Upscaling Failed, PUBLIC_ERROR_UNUSUAL_ACTIVITY and Unsafe Generation](https://useapi.net/docs/articles/google-flow-errors?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [Sora 2 API Alternatives Compared, With Code: Seedance 2.5, Omni Flash, MiniMax H3, Kling v3](https://useapi.net/docs/articles/sora-2-api-alternatives?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [Chinese-language tutorial (中文教程): Veo 3.1, Omni 1.1 Flash and Nano Banana Pro](https://useapi.net/docs/articles/google-flow-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- All articles: [useapi.net articles](https://useapi.net/docs/articles?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)

## 中文说明

这是 [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) 托管的第三方 Google Flow API 示例代码（Node.js 与 Python）。通过 REST API 调用 Veo 3.1 Fast、Quality、Lite 视频，Omni 1.1 Flash 带音频视频，以及 Nano Banana Pro、2.1 和 2 Lite 图片生成。

- 使用你的 Google AI 订阅（免费版、Plus $4.99、Pro $19.99、Ultra $99.99 或 Ultra $199.99 每月，2026 年 10 月价格），已支持新域名 `flow.google.com`。
- 无需 Google Cloud 项目或 Gemini API Key，无需自己部署服务或维护浏览器。
- 账号通过自动化浏览器流程绑定，登录 Google 即可，无需手动复制 Cookie。
- reCAPTCHA 由服务端自动处理（首个账号赠送 300 次免费打码，之后接入你自己的打码服务）。
- useapi.net 每月 15 美元，含所有 API，每个订阅可连接 3 个 Google 账号。
- 成本：在 Google AI Ultra $199.99 上，一条 8 秒 Veo 3.1 Fast 视频约 $0.08 的 Flow 积分，Google 官方 API 为 $0.80（2026 年 10 月）。图片生成不消耗积分，免费 Google 账号也可使用。

中文教程（Veo 3.1、Omni 1.1 Flash、Nano Banana Pro，含价格对比与示例）：[如何通过 Google Flow API 调用 Veo 3.1、Omni 1.1 Flash 和 Nano Banana Pro](https://useapi.net/docs/articles/google-flow-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)。快速开始见上方 [Quick start](#quick-start)，完整文档：[Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)。

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) is a third-party REST API for AI services, not affiliated with Google. The [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) runs on your Google AI subscription, so you spend its Flow credits instead of paying metered developer-API prices. See the [models](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#models) and the [pricing comparison](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#pricing).

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@useapi-net).

## License

The example code in this repository is released under the [MIT License](./LICENSE). It covers the example scripts only, not the useapi.net service or API.
