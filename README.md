# Google Flow API examples (useapi.net)

English · [中文](#中文说明) · [日本語](#日本語の説明) · [Português](#sobre-este-repositório) · [Tiếng Việt](#về-repo-này) · [Bahasa Indonesia](#tentang-repo-ini) · [ไทย](#เกี่ยวกับ-repo-นี้)

Runnable Node.js and Python examples for the [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) — generate Veo 3.1 Fast, Quality and Lite video, Omni 1.2 and 1.1 Flash audio-native video, and Nano Banana Pro, 2.1 and 2 Lite images through a REST API that runs on your [Google AI subscription](https://gemini.google/subscriptions/) for [Google Flow](https://flow.google.com): Free, Plus $4.99, Pro $19.99, Ultra $99.99 or Ultra $199.99 a month (as of November 2026). No Google Cloud project, no Gemini API key, no per-call metering.

Each example ships JavaScript and Python implementations (`.mjs` and `.py`) driven by a `prompts.json` (or, for [`omni-extend/`](./omni-extend), a `story.json`) you edit. Most are batch runners: they submit every prompt in the file and download every result, so you can queue a batch and come back to the winners. [`ugc-product-video/`](./ugc-product-video) is a pipeline instead — it chains six endpoints into one finished video, checkpointing as it goes.

| Example | What it does | Tutorial | Tutorial date |
|---|---|---|---|
| [`demo/`](./demo) | **Live agent chat app**: a browser chat with Google Flow's creative agent through the API, with answers streamed live, the agent's images and videos inline (full-size view, download, reuse), uploads, characters and voices attached along the way, spending approvals, a Library and the agent's settings. Open the [live demo](https://useapi.net/demos/google-flow/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) or open `demo/index.html` locally. Vanilla JS, no build | [Agent overview](https://useapi.net/docs/api-google-flow-v1/agent?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), [Chat with Google Flow Agent](https://useapi.net/docs/articles/google-flow-agent-chat?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | October 16, 2026 |
| [`veo-video/`](./veo-video) | Batch-generate **Veo 3.1** video — text-to-video, first/last-frame image-to-video | [Generate Veo 3.1 video via curl](https://useapi.net/docs/articles/google-flow-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · [中文](https://useapi.net/docs/articles/google-flow-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | June 15, 2026 (October 20, 2026) |
| [`images/`](./images) | Batch-generate images with **Nano Banana 2 Lite** (default), **Nano Banana 2.1**, **Nano Banana Pro** | [Generate images via curl](https://useapi.net/docs/articles/google-flow-images-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | June 15, 2026 (October 20, 2026) |
| [`nano-banana-compare/`](./nano-banana-compare) | Run one prompt through all three **Nano Banana** models (**2 Lite**, **2.1**, **Pro**) and compare | [Nano Banana 2 Lite vs 2.1 vs Pro compared](https://useapi.net/docs/articles/google-flow-nano-banana-compare?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | July 2, 2026 (October 20, 2026) |
| [`omni-flash/`](./omni-flash) | Batch-generate **Omni 1.1 Flash** (or **Omni 1.2 Flash** with `"model": "omni-flash-1.2"`) audio-native video — text-to-video, first/last-frame image-to-video, reference-to-video, video-to-video edit | [Generate Omni 1.1 Flash video via curl](https://useapi.net/docs/articles/omni-flash-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | June 15, 2026 (November 6, 2026) |
| [`omni-extend/`](./omni-extend) | Make one long **Omni 1.2 Flash** video: a first clip of 3 to 15 seconds, then extensions of up to 10 seconds each with their own voices, images or characters (the release post's 30-second scene is the default story) | [Extend a video with Omni 1.2](https://useapi.net/docs/articles/omni-flash-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#extend-a-video-with-omni-12) | June 15, 2026 (November 6, 2026) |
| [`ugc-product-video/`](./ugc-product-video) | Build a whole **UGC product video** — product sheets, a presenter, one still, an **Omni 1.1 Flash** clip per product, upscaled and joined | [Make a UGC product video](https://useapi.net/docs/articles/google-flow-ugc-product-video?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | September 4, 2026 (October 20, 2026) |
| [`n8n/`](./n8n) | Ready-to-import **n8n** workflows: a **Google Sheet** batch of **Veo 3.1** videos and **Nano Banana Pro** images saved to Google Drive, and a one-prompt form | [n8n workflows](./n8n/README.md) | September 28, 2026 (October 28, 2026) |
| [`n8n/ugc-ad-factory.json`](./n8n/ugc-ad-factory.json) | Ready-to-import **n8n** form workflow that builds a whole **UGC video ad** with **Omni 1.1 Flash**: pick or re-roll at every step, upload your own product photos, 1–5 products, 1080p | [Make UGC video ads in n8n](https://useapi.net/docs/articles/google-flow-n8n-ugc-ads?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) | October 3, 2026 (October 20, 2026) |
| [`skills/omni-flash-video/`](./skills/omni-flash-video) | **Agent skill** for Claude Code, Codex and Cursor: ask for a clip and the agent makes it with **Omni 1.2 Flash**, **Omni 1.1 Flash** or **Veo 3.1** (dialogue, voices, reference images, first/last frames) and downloads the `.mp4`. Install: `npx skills add useapi/google-flow-api --skill omni-flash-video` | [SKILL.md](./skills/omni-flash-video/SKILL.md) |

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

- **Does Google Flow have an API or an API key?** Through useapi.net, yes. Google offers [Flow](https://flow.google.com) only as a website, with no public API and no Flow API key (as of November 2026). The useapi.net Google Flow API runs Veo 3.1, Omni 1.1 Flash and Nano Banana Pro, 2.1 and 2 Lite over REST on your Google AI subscription, with a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) as the key, and also chats with [Google Flow Agent](https://useapi.net/docs/api-google-flow-v1/agent?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), which Google offers only inside the Flow website.
- **How do I connect my Google account?** Through the useapi.net [automated browser setup](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api): sign in with Google once, with no cookies to copy and no Google Cloud project or Gemini API key, and it's done in about a minute. Captchas are solved for you: your first account gets 300 free, then your own captcha provider costs about $0.80 to $3.00 per 1,000. To connect by hand, the [Google Account Setup](https://github.com/useapi/google-account-setup) scripts (Windows, macOS, Linux) open a clean, single-use browser profile, so the cookies you copy keep working.
- **How much does the Google Flow API cost?** Through useapi.net, Google Flow video costs a fraction of Google's own APIs. On Google AI Ultra $199.99, Omni 1.2 Flash is about $0.024 a second at 720p ($0.19 for 8 seconds), against $0.07 a second on [Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/gemini-omni-1-2-flash-generally-available), and an 8-second Veo 3.1 Fast video is $0.08, against $0.80 on Google's [Agent Platform](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing). Nano Banana Pro images use no credits, against $0.134 each (as of November 2026). The [price table](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#pricing) shows every model on every subscription.
- **Is there a free Google Flow API?** Through useapi.net, yes: a free Google account makes Nano Banana images, Veo 3.1 Fast and Lite videos and Omni 1.2 Flash videos of up to 10 seconds on its [50 daily Flow credits](https://support.google.com/flow/answer/16526234), enough for 2 Fast or 5 Lite videos, while Google's own APIs charges for every image and every second of video (as of November 2026). Upscaling an image to 2K is free on every account too. Omni 1.1 Flash, Omni 1.2 Flash longer than 10 seconds, extending with Omni 1.2 and video upscaling need a paid Google AI subscription.
- **Is there a second Omni allowance?** Through useapi.net, yes: the [Google Vids API](https://useapi.net/docs/api-google-vids-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) makes Omni 1.1 Flash video on the same Google AI subscription from Vids' own monthly allowance, separate from Flow credits and with no captcha. On Ultra $199.99 the two allowances together come to about 2,666 ten-second Omni clips a month on one Google account. Examples: [useapi/google-vids-api](https://github.com/useapi/google-vids-api).
- More answers: [Google Flow API questions](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#questions).

## More articles

- [Can You Use Your Google AI Subscription Through an API? What Plus, Pro and Ultra Get You](https://useapi.net/docs/articles/google-ai-subscription-api?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · Also in [中文](https://useapi.net/docs/articles/google-ai-subscription-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · [日本語](https://useapi.net/docs/articles/google-ai-subscription-api-ja?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · [Português](https://useapi.net/docs/articles/google-ai-subscription-api-pt?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · [Tiếng Việt](https://useapi.net/docs/articles/google-ai-subscription-api-vi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · [Bahasa Indonesia](https://useapi.net/docs/articles/google-ai-subscription-api-id?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · [ไทย](https://useapi.net/docs/articles/google-ai-subscription-api-th?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [How to Use the Gemini Omni 1.2 Flash API: 15-Second Videos in Google Flow and Google Vids](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) · Also in [中文](https://useapi.net/docs/articles/gemini-omni-1-2-flash-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [Veo 3.1 API Pricing: Official Google Veo API vs Google Flow API](https://useapi.net/docs/articles/veo-3-1-api-pricing?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [Google Flow Errors Explained: Upscaling Failed, PUBLIC_ERROR_UNUSUAL_ACTIVITY and Unsafe Generation](https://useapi.net/docs/articles/google-flow-errors?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- [Sora 2 API Alternatives Compared, With Code: Seedance 2.5, Omni Flash, MiniMax H3, Kling v3](https://useapi.net/docs/articles/sora-2-api-alternatives?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- All articles: [useapi.net articles](https://useapi.net/docs/articles?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)

## 中文说明

这是 [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) 托管的第三方 Google Flow API 示例代码（Node.js 与 Python）。通过 REST API 调用 Veo 3.1 Fast、Quality、Lite 视频，Omni 1.1 Flash 带音频视频，以及 Nano Banana Pro、2.1 和 2 Lite 图片生成。

- 使用你的 Google AI 订阅（免费版、Plus $4.99、Pro $19.99、Ultra $99.99 或 Ultra $199.99 每月，2026 年 11 月价格），已支持新域名 `flow.google.com`。
- 无需 Google Cloud 项目或 Gemini API Key，无需自己部署服务或维护浏览器。
- 账号通过自动化浏览器流程绑定，登录 Google 即可，无需手动复制 Cookie。
- reCAPTCHA 由服务端自动处理（首个账号赠送 300 次免费打码，之后接入你自己的打码服务）。
- useapi.net 每月 15 美元，含所有 API，每个订阅可连接 3 个 Google 账号。
- 成本：在 Google AI Ultra $199.99 上，一条 8 秒 Veo 3.1 Fast 视频约 $0.08 的 Flow 积分，Google 官方 API 为 $0.80（2026 年 11 月）。图片生成不消耗积分，免费 Google 账号也可使用。

中文教程（Veo 3.1、Omni Flash 1.2 和 1.1、Nano Banana Pro，含价格对比与示例）：[如何通过 Google Flow API 调用 Veo 3.1、Omni Flash（1.2 和 1.1）和 Nano Banana Pro](https://useapi.net/docs/articles/google-flow-api-zh?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)。快速开始见上方 [Quick start](#quick-start)，完整文档：[Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)。

## 日本語の説明

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) がホストするサードパーティの Google Flow API の、Node.js と Python のサンプルです。REST API で、Veo 3.1 Fast、Quality、Lite の動画、音声付きの Omni 1.2 Flash と 1.1 Flash の動画、Nano Banana Pro、2.1、2 Lite の画像を生成します。

- お使いの Google AI のプランで動きます：無料、Plus $4.99、Pro $19.99、Ultra $99.99、Ultra $199.99（月額、2026年11月時点）。新しいドメイン `flow.google.com` にも対応しています。
- Google Cloud プロジェクトも Gemini API キーも不要で、サーバーやブラウザーを自分で管理する必要もありません。
- Google アカウントは、自動化されたブラウザーの手順で接続します。Google に一度ログインするだけで、Cookie をコピーする必要はありません。
- reCAPTCHA はサーバー側で解決します。最初のアカウントには300回の無料解決が付き、その後はご自身の CAPTCHA プロバイダーを使います。
- コスト：Google AI Ultra $199.99 では、8秒の Veo 3.1 Fast の動画1本が Flow クレジットで約 $0.08 で、Google の公式 API では $0.80 です（2026年11月時点）。画像はクレジットを使わず、無料の Google アカウントでも作れます。useapi.net は月 $15 で、すべての API と、サブスクリプションごとに3つの Google アカウントが含まれます。
- サンプルでは、`prompts.json` から動画と画像を一括生成し、Omni 1.2 の延長で長いシーンを組み立て、UGC の商品動画を最初から最後まで作ります。

日本語の記事：[Veo 3.1 API の使い方：Google Flow API と curl で動画を生成する](https://useapi.net/docs/articles/google-flow-bash-ja?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)、[Google AI のサブスクは API で使える？Plus・Pro・Ultra で毎月できること](https://useapi.net/docs/articles/google-ai-subscription-api-ja?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)。ドキュメント全体：[Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)。

## Sobre este repositório

Exemplos em Node.js e Python da Google Flow API, uma API de terceiros hospedada pela [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), para gerar por REST vídeos Veo 3.1 Fast, Quality e Lite, vídeos Omni 1.2 e 1.1 Flash com áudio, e imagens Nano Banana Pro, 2.1 e 2 Lite.

- Roda na sua assinatura do Google AI: gratuita, Plus $4,99, Pro $19,99, Ultra $99,99 ou Ultra $199,99 por mês (preços de novembro de 2026), já no novo domínio `flow.google.com`.
- Sem projeto no Google Cloud e sem chave da Gemini API, sem servidor nem navegador para manter.
- A conta Google é conectada por um fluxo automatizado no navegador: você entra no Google uma vez, sem copiar cookies.
- O reCAPTCHA é resolvido pelo servidor: a primeira conta ganha 300 resoluções grátis, depois você usa o seu próprio provedor de captcha.
- Custo: no Google AI Ultra $199,99, um vídeo Veo 3.1 Fast de 8 segundos gasta cerca de $0,08 em créditos do Flow, contra $0,80 na API oficial do Google (novembro de 2026). Imagens não gastam créditos e funcionam em contas Google gratuitas. A useapi.net custa $15 por mês, com todas as APIs e 3 contas Google por assinatura.
- Os exemplos geram vídeos e imagens em lote a partir de um `prompts.json`, montam uma cena longa com extensões do Omni 1.2 e criam um vídeo UGC de produto do início ao fim.

Artigos em português: [Como usar a API do Veo 3.1 com curl pela Google Flow API](https://useapi.net/docs/articles/google-flow-bash-pt?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) e [Dá para usar a assinatura do Google AI por API?](https://useapi.net/docs/articles/google-ai-subscription-api-pt?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api). Documentação completa: [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api).

## Về repo này

Ví dụ Node.js và Python cho Google Flow API, một API của bên thứ ba do [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) host, để tạo qua REST video Veo 3.1 Fast, Quality và Lite, video Omni 1.2 và 1.1 Flash có âm thanh, và ảnh Nano Banana Pro, 2.1 và 2 Lite.

- Chạy trên gói Google AI của bạn: Ultra $199,99, Ultra $99,99, Pro $19,99, Plus $4,99 mỗi tháng hoặc gói miễn phí (giá tháng 11/2026), đã hỗ trợ tên miền mới `flow.google.com`.
- Không cần dự án Google Cloud hay Gemini API key, không phải tự triển khai server hay duy trì trình duyệt.
- Tài khoản Google được kết nối bằng quy trình trình duyệt tự động: đăng nhập Google một lần, không cần chép cookie.
- reCAPTCHA được server tự giải: tài khoản đầu tiên được 300 lần miễn phí, sau đó bạn dùng dịch vụ giải captcha của riêng mình.
- Chi phí: trên Google AI Ultra $199,99, một video Veo 3.1 Fast dài 8 giây tốn khoảng $0,08 credit Flow, so với $0,80 trên API chính thức của Google (tháng 11/2026). Ảnh không tốn credit và dùng được trên tài khoản Google miễn phí. useapi.net giá $15 mỗi tháng, gồm mọi API và 3 tài khoản Google mỗi gói đăng ký.
- Các ví dụ tạo hàng loạt video và ảnh từ một file `prompts.json`, dựng một cảnh dài bằng các lần kéo dài Omni 1.2, và làm trọn một video UGC giới thiệu sản phẩm.

Bài viết tiếng Việt: [Cách dùng Veo 3.1 API: tạo video bằng curl qua Google Flow API](https://useapi.net/docs/articles/google-flow-bash-vi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) và [Dùng gói Google AI qua API được không?](https://useapi.net/docs/articles/google-ai-subscription-api-vi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api). Tài liệu đầy đủ: [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api).

## Tentang repo ini

Ini adalah contoh kode Node.js dan Python untuk Google Flow API dari [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), API pihak ketiga untuk membuat video Veo 3.1 Fast, Quality dan Lite, video Omni 1.2 dan 1.1 Flash dengan audio, serta gambar Nano Banana Pro, 2.1 dan 2 Lite lewat REST API.

- Berjalan di paket Google AI Anda sendiri (Gratis, Plus $4,99, Pro $19,99, Ultra $99,99 atau Ultra $199,99 per bulan, harga per November 2026), dan sudah mendukung domain baru `flow.google.com`.
- Tanpa project Google Cloud atau Gemini API key, tanpa server atau browser yang harus Anda kelola sendiri.
- Akun dihubungkan lewat [setup browser otomatis](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api): cukup login ke Google, tanpa menyalin cookie. Captcha diselesaikan di server (300 gratis untuk akun pertama, setelah itu lewat penyedia captcha Anda sendiri).
- Harga: di Google AI Ultra $199,99, satu video Veo 3.1 Fast 8 detik memakai kredit Flow senilai sekitar $0,08, dibanding $0,80 di API resmi Google (per November 2026). Gambar tidak memakai kredit, dan akun Google gratis pun bisa. Langganan useapi.net $15 per bulan untuk semua API, dengan 3 akun Google per langganan.
- Contoh di repo: `veo-video/` dan `images/` membuat video dan gambar secara batch dari `prompts.json`, `omni-extend/` membuat video Omni 1.2 Flash panjang lewat perpanjangan dengan suara, `ugc-product-video/` membuat video produk UGC utuh, ditambah workflow n8n dan agent skill untuk Claude Code, Codex dan Cursor.

Artikel bahasa Indonesia: [Cara Memakai Veo 3.1 API: Membuat Video dengan curl lewat Google Flow API](https://useapi.net/docs/articles/google-flow-bash-id?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) dan [Bisakah Langganan Google AI Dipakai Lewat API? Isi Paket Plus, Pro dan Ultra](https://useapi.net/docs/articles/google-ai-subscription-api-id?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api). Dokumentasi lengkap: [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api).

## เกี่ยวกับ repo นี้

นี่คือตัวอย่างโค้ด Node.js และ Python สำหรับ Google Flow API ของ [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) ซึ่งเป็น API ของบุคคลที่สาม ใช้สร้างวิดีโอ Veo 3.1 Fast, Quality และ Lite วิดีโอ Omni 1.2 และ 1.1 Flash พร้อมเสียง และภาพ Nano Banana Pro, 2.1 และ 2 Lite ผ่าน REST API

- ใช้แพ็กเกจ Google AI ของคุณเอง (ฟรี, Plus $4.99, Pro $19.99, Ultra $99.99 หรือ Ultra $199.99 ต่อเดือน ราคา ณ พฤศจิกายน 2026) และรองรับโดเมนใหม่ `flow.google.com` แล้ว
- ไม่ต้องมีโปรเจกต์ Google Cloud หรือ Gemini API key ไม่ต้องตั้งเซิร์ฟเวอร์หรือดูแลเบราว์เซอร์เอง
- เชื่อมบัญชีผ่าน[ขั้นตอนตั้งค่าแบบเบราว์เซอร์อัตโนมัติ](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) แค่ล็อกอิน Google ไม่ต้องคัดลอก cookie ส่วน captcha ระบบแก้ให้ (บัญชีแรกฟรี 300 ครั้ง หลังจากนั้นใช้ผู้ให้บริการ captcha ของคุณเอง)
- ราคา: บน Google AI Ultra $199.99 วิดีโอ Veo 3.1 Fast ยาว 8 วินาทีใช้เครดิต Flow ราว $0.08 เทียบกับ $0.80 บน API ทางการของ Google (ข้อมูล ณ พฤศจิกายน 2026) การสร้างภาพไม่ใช้เครดิต และใช้บัญชี Google ฟรีได้ ค่าบริการ useapi.net คือ $15 ต่อเดือน รวมทุก API และเชื่อมบัญชี Google ได้ 3 บัญชีต่อการสมัคร
- ตัวอย่างใน repo: `veo-video/` และ `images/` สร้างวิดีโอและภาพทีละหลายรายการจาก `prompts.json` `omni-extend/` สร้างวิดีโอ Omni 1.2 Flash ยาวด้วยการต่อความยาวพร้อมเสียงพูด `ugc-product-video/` สร้างวิดีโอรีวิวสินค้าแบบ UGC ทั้งคลิป และยังมี workflow ของ n8n กับ agent skill สำหรับ Claude Code, Codex และ Cursor

บทความภาษาไทย: [วิธีใช้ Veo 3.1 API: สร้างวิดีโอด้วย curl ผ่าน Google Flow API](https://useapi.net/docs/articles/google-flow-bash-th?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) และ [ใช้แพ็กเกจ Google AI ผ่าน API ได้ไหม? Plus, Pro และ Ultra ได้อะไรบ้าง](https://useapi.net/docs/articles/google-ai-subscription-api-th?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) เอกสารฉบับเต็ม: [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) is a third-party REST API for AI services, not affiliated with Google. The [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) runs on your Google AI subscription, so you spend its Flow credits instead of paying metered developer-API prices. See the [models](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#models) and the [pricing comparison](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#pricing).

Visit our [Discord Server](https://discord.gg/w28uK3cnmF) or [Telegram Channel](https://t.me/use_api) for any support questions and concerns.

We regularly post guides and tutorials on the [YouTube Channel](https://www.youtube.com/@useapi-net).

## License

The example code in this repository is released under the [MIT License](./LICENSE). It covers the example scripts only, not the useapi.net service or API.
