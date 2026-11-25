# Google Flow by useapi.net

**Author:** [useapi](https://useapi.net/?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) · **Version:** 0.1.0 · **Type:** tool · **Source:** https://github.com/useapi/google-flow-api/tree/main/dify-plugin · **Contact:** support@useapi.net

Use Google Flow from Dify [workflows, chatflows](https://docs.dify.ai/en/cloud/use-dify/build/workflow-chatflow) and [agents](https://docs.dify.ai/en/cloud/use-dify/build/new-agent/overview). Make videos with sound with Veo 3.1 Lite and Omni 1.2 Flash, make images with Nano Banana, extend and edit videos, upscale them up to 4K, turn them into GIFs, join clips, and chat with the Google Flow agent, Google's own creative agent that plans, writes storyboards and generates for you. Images and videos come back as Dify files.

**Connect several Google accounts and let useapi.net share the work.** Leave the email empty and useapi.net sends each new job to a healthy account. You get more jobs running in parallel, the Google Flow credits of every account in one place, and work keeps going when Google throttles one account or it reaches its quota. A plugin built on a single Gemini API key cannot do this: that key is billed per call and does not use your Google AI plan. See [Several Google accounts](#several-google-accounts).

> This plugin calls the [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) by useapi.net, a third-party API. It is not made by, affiliated with or endorsed by Google. You need a useapi.net subscription ($15/month, covers every useapi.net API), a Google account with a Google AI plan (the free plan works for Veo 3.1 Lite, Omni 1.2 Flash and Nano Banana), and captcha solving: 300 free captcha credits come with your first Google Flow account, then you add your own captcha provider key.

## Google AI plans and Google Flow

Videos spend the Google Flow credits of the Google account that makes them. Images use no credits on any plan.

| Plan | Price a month | Google Flow credits | Video models | Extras | Veo 3.1 Lite videos (8 s, 720p) |
|---|---|---|---|---|---|
| Free | $0 | 50 a day | Veo 3.1 Lite (8 s), Omni 1.2 Flash (up to 10 s) | Nano Banana 2.1 at thinking level high only; image upscale to 2K | about 5 a day |
| Google AI Plus | $4.99 | 200 a month | Veo 3.1 Lite (8 s), Omni 1.2 Flash (3 to 15 s) | Omni 1.2 Flash extend; video upscale to 720p and 1080p | about 20 a month |
| Google AI Pro | $19.99 | 1,000 a month | as Google AI Plus | as Google AI Plus | about 100 a month |
| Google AI Ultra $99 | $99.99 | 10,000 a month | as Google AI Plus, plus 4 and 6 s Veo 3.1 Lite videos | 4K video and image upscale | about 2,000 a month |
| Google AI Ultra $199 | $199.99 | 25,000 a month | as Google AI Ultra $99, plus Veo 3.1 Lite Lower Priority at 0 credits (the plan manager's account only) | 4K video and image upscale | about 5,000 a month |

Every plan makes images with Nano Banana 2 Lite, Nano Banana 2.1 and Nano Banana Pro. Prices are Google's US prices as of 2026-10-20, from the useapi.net API catalog (`https://api.useapi.net/v1/google-flow/models`, `plans`). Credits per plan come from Google's [plans page](https://gemini.google/subscriptions/) and [Google Flow credits page](https://support.google.com/flow/answer/16526234), as listed in the useapi.net [Google Flow docs](https://useapi.net/docs/api-google-flow-v1?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) in November 2026. The video counts divide those credits by the Veo 3.1 Lite price in the catalog (10 credits for 8 seconds, 5 on Google AI Ultra). The table shows the Google plan's cost only. The useapi.net subscription ($15/month) is separate.

Why it matters: you use the credits already in your Google AI plan instead of paying Google per clip, and you can combine several accounts ([Several Google accounts](#several-google-accounts)).

## Quick start

1. **Get a useapi.net API token.** Subscribe and copy your token: [Setup useapi.net](https://useapi.net/docs/start-here/setup-useapi?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin).
2. **Connect a Google account.** Follow [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) (the automated setup takes about 5 minutes). Your first account comes with 300 free captcha credits, so you can generate right away. When they run out, add a captcha provider key as the same page shows under [Configure Captcha Providers](https://useapi.net/docs/start-here/setup-google-flow#configure-captcha-providers). Captcha solving costs about $0.80 to $3.00 per 1,000 generations, paid to the provider.
3. **Install and authorize the plugin, then make a video.** Install it from the [Dify Marketplace](https://marketplace.dify.ai/plugins/useapi/google_flow_useapi), or upload the `.difypkg` from the [GitHub releases](https://github.com/useapi/google-flow-api/releases) under Plugins > Install plugin > Local package file. In Tools, open "Google Flow by useapi.net", click Authorize, paste the token and save. Then add **Generate video** to a workflow with the prompt "A paper boat floating on a calm pond at sunrise" and run it. The `.mp4` comes back as a file.

### Credentials

| Credential | Required | What it is |
|---|:-:|---|
| `useapi.net API token` | Yes | Your token from step 1. Stored by Dify as a secret. |
| `Default Google account email` | No | Leave empty to rotate across all connected accounts. Set it only to pin every tool to one Google account. |

Saving the credentials makes one check, `GET /accounts`, which confirms the token works and that at least one Google account is connected. It does not call Google.

### Connection requirements

The plugin connects to `https://api.useapi.net/v1/google-flow` with the token in an `Authorization: Bearer` header, and downloads finished images and videos from Google's signed links on `https://flow-content.google` (no token is sent there). A self-hosted Dify needs outbound HTTPS to both hosts. No proxy, webhook or inbound connection is required.

## Several Google accounts

Add each Google account the same way as the first one, with [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin). **List Google accounts** then shows each account and whether its health is OK, **List jobs per account** shows what runs on each one, and **Get account plan and credits** shows one account's plan, credits left and video models.

**How rotation works.** When the email is empty, Generate video, Generate image, Upload image or video and a new agent chat leave the choice to useapi.net. Its [load balancer](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs#load-balancing-algorithm) first sets aside any account that Google has recently throttled or that reached its quota, until the cooldown ends. Among the rest it picks the account with the fewest running and recent jobs, and recent failures and rate limits count against an account. If every account is set aside for the model, you get a `429` with the time to retry. With a single account nothing is set aside: your request always goes to it.

**What you gain.** More jobs in parallel, because each job goes to the least busy account. More credits, because every account brings its own Google AI plan. Fewer stops, because a throttled or exhausted account is skipped while the others keep working.

**When to set an email.**
- Leave both emails empty to rotate. This is the best default.
- Set the **default email in the credentials** to pin every tool to one account. An explicit email skips the load balancer, so requests go to that account even while it is set aside.
- Set the **email on one tool** to send just that call to one account, for example to spend the credits of a Google AI Ultra account on a 4K upscale.

**References pin the account.** An image, video, character or voice you made or uploaded lives on one Google account, and every item in one request must belong to the same account. So a request that uses a media id runs on that media's account, whatever the rotation would pick. Extend, upscale, GIF and join run on the account of their source video. Files you attach to a tool are uploaded to the account of the other ids in that request. An agent chat stays on the account it started on, so continue it with its `chat_id` and use references from that account. Each account runs at most 3 agent turns at a time.

## Tools

20 tools, one per task. Media ids look like `user:12345-email:...-video:<id>`; pass them between nodes as variables. Endpoints are relative to `https://api.useapi.net/v1/google-flow`.

| Tool | Label | Endpoint |
|---|---|---|
| `list_accounts` | List Google accounts | `GET /accounts` |
| `get_account` | Get account plan and credits | `GET /accounts/{email}` |
| `list_jobs` | List jobs per account | `GET /jobs` |
| `get_job` | Get job status | `GET /jobs/{jobid}` |
| `generate_video` | Generate video | `POST /videos` |
| `extend_video` | Extend video | `POST /videos/extend` |
| `upscale_video` | Upscale video | `POST /videos/upscale` |
| `generate_image` | Generate image | `POST /images` |
| `upscale_image` | Upscale image | `POST /images/upscale` |
| `video_to_gif` | Video to GIF | `POST /videos/gif` |
| `concatenate_videos` | Join videos | `POST /videos/concatenate` |
| `upload_image` | Upload image or video | `POST /assets/{email}` |
| `list_media` | List media | `GET /assets/media/{email}` |
| `get_media` | Get media | `GET /assets/{mediaGenerationId}` |
| `list_characters` | List characters | `GET /characters` |
| `list_voices` | List voices | `GET /voices` |
| `agent_chat` | Google Flow agent chat | `POST /agent/chats`, `POST /agent/chats/{chatId}/messages` |
| `agent_get_chat` | Get Google Flow agent chat | `GET /agent/chats/{chatId}` |
| `agent_answer_approval` | Answer the agent's approval request | `POST /agent/chats/{chatId}/approval` |
| `agent_list_chats` | List Google Flow agent chats | `GET /agent/chats` |

### Models and options

| Tool | Models | Main options |
|---|---|---|
| Generate video | `veo-3.1-lite` (default), `omni-flash-1.2`, `veo-3.1-lite-low-priority` (Google AI Ultra $199 only) | landscape or portrait; 4, 6 or 8 s on Veo (4 and 6 on Google AI Ultra), 3 to 15 s on Omni 1.2 Flash (above 10 s on paid plans); 720p, or 360p on Omni 1.2 Flash; 1 to 4 videos; start and end image; up to 10 reference images and characters (3 on Veo); a voice; video edit with Omni 1.2 Flash |
| Extend video | `omni-flash-1.2` (default, paid plans), `veo-3.1-lite`, `veo-3.1-lite-low-priority` | 3 to 10 seconds added (Omni 1.2 Flash); reference images, characters and a voice |
| Upscale video | | 720p or 1080p (paid plans), 4K (Google AI Ultra); videos up to 15 s |
| Generate image | `nano-banana-2-lite` (default), `nano-banana-2` (Nano Banana 2.1), `nano-banana-pro` | 16:9, 4:3, 1:1, 3:4, 9:16 or auto; 1 to 4 images; seed; thinking level for Nano Banana 2.1; up to 10 reference images and 7 characters |
| Upscale image | | 2K, or 4K on Google AI Ultra |

Image and video references take either a media id or a Dify file. A file is uploaded first (PNG, JPEG or WebP up to 20 MB, MP4 up to 100 MB). Veo 3.1 Fast, Veo 3.1 Quality and Omni 1.1 Flash are not offered: Google retires them on 2026-12-05.

### Outputs

- **text**: a readable summary with the media ids and links, the agent's reply, or what to do next. This is what an agent reads.
- **json**: the API response, without base64 data or account cookies.
- **files**: the finished `.mp4`, `.jpg` or `.gif`. Turn off "Attach the files" to skip them. Files over 150 MB are not attached.
- **variables**: `jobid`, `status`, `media_ids` and `file_urls` from the generation tools; `chat_id`, `status`, `reply`, `media_ids` and `file_urls` from the agent tools; `media_id` from Upload; `emails` and `healthy_emails` from List Google accounts.

Links to Google's files expire about 6 hours after they are made. **Get media** gives a fresh one.

## Usage examples

### Workflow: image to video in two nodes

```
[Start: idea (text)]
        |
[Google Flow > Generate image]       prompt = {{Start.idea}}, aspect ratio = 16:9, count = 1
        |
[Google Flow > Generate video]       prompt = "Slow camera push-in, soft wind"
                                     model = Omni 1.2 Flash, duration = 8
                                     start_image = {{Generate image.media_ids}}
                                     Maximum wait = 420
        |
[End: video = {{Generate video.files}}, id = {{Generate video.media_ids}}]
```

The image uses no credits. An id field also takes a one-item list, so `media_ids` can be passed as it is. The start image pins the video to the same Google account. If the video is still running after the wait, add a **Get job status** node with `jobid = {{Generate video.jobid}}`.

### Agent: a video assistant with the Google Flow agent

Create an Agent app and add Google Flow agent chat, Get Google Flow agent chat, Answer the agent's approval request, Generate video, Get job status and List Google accounts. Use instructions like:

```
You help the user make short videos with Google Flow.
- For a quick single clip, use Generate video. For a story with several shots, use the Google Flow agent chat.
- When the agent asks for approval, tell the user what it wants to make and its cost in Google Flow credits,
  and answer only after the user agrees.
- If a tool says a job or turn is still running, never start it again: call Get job status or
  Get Google Flow agent chat with wait=true.
- Leave the email empty unless the user names an account.
```

Then ask, for example: "Make a 3-shot storyboard of a paper boat's journey and turn the first shot into a video."

## Waiting and limits

- **Dify's 600-second limit.** A Dify plugin call ends after 600 seconds (`PLUGIN_MAX_EXECUTION_TIMEOUT`). So the video tools submit the job, poll it every 10 seconds and return after 120 seconds by default. If the video is not ready, they return its `jobid`: call **Get job status** with it (it waits up to 120 seconds per call). In a workflow you can raise "Maximum wait" up to 420 seconds. The job keeps running after the call returns, and jobs are kept for 7 days.
- **Timing.** A video usually takes 60 to 180 seconds. An image answers in one call. An agent turn usually takes about a minute, and its videos finish a minute or two after the turn.
- **Agent approvals.** In ask mode the agent asks before it spends credits. Answer within about 4 minutes, or Google closes the request and the message has to be sent again.
- **Captcha.** Every image and video request, and every agent turn, uses one captcha solve: from the 300 free credits, then from your own provider.

## Troubleshooting

| Code | What it means | What to do |
|---|---|---|
| 400 | The request was refused. The message says why: a model or option the plan lacks, a wrong combination, or the free captcha credits are used up. | Change what the message says. For captcha, add your provider key: [Configure Captcha Providers](https://useapi.net/docs/start-here/setup-google-flow#configure-captcha-providers). |
| 401 | The useapi.net token is wrong. | Check the token in the plugin's credentials. |
| 402 | The useapi.net subscription is not active. | Renew it: [subscription](https://useapi.net/docs/subscription). |
| 403 | Google refused the captcha on every try (nothing was generated or charged), the plan lacks the model, the account is treated as under 18, or the id belongs to another useapi.net user. | Use another account, or leave the email empty so useapi.net picks one. |
| 404 | The account is not connected, or the job, media or chat does not exist. | Connect the account with [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow). |
| 408 | The job was still running when the wait ended. | Check **Get job status** before sending it again. |
| 409 | An agent turn is running in this chat, or an approval waits. | Answer the approval, or wait for the turn to end. |
| 410 | The job has expired. | Jobs are kept for 7 days. |
| 429 | Google limits this account for now, every account is set aside for this model, or the account already runs 3 agent turns. | Wait for the retry time, connect more accounts, or leave the email empty. |
| 502, 504 | Google did not answer clearly or in time. The request may have run. | Check **List jobs per account** or **Get Google Flow agent chat** before sending it again. |
| 503 | Google is briefly unavailable, the media is not ready, or your captcha provider failed. | Retry in a few seconds. For the captcha provider, check its key and balance. |
| 596 | Google rejected the account's session. useapi.net re-verifies it on its own. | Retry in about a minute. If it continues, add the account again. |

A failed video names Google's reason. For example, `PUBLIC_ERROR_AUDIO_FILTERED` means Google's audio filter rejected the sound made with the video: send it again, or use Omni 1.2 Flash.

## What it costs

- The plugin is free.
- useapi.net: $15/month, for every useapi.net API.
- Google: your own Google AI plan, the free one included. Videos spend its Google Flow credits; images use none.
- Captcha: 300 free credits with your first Google Flow account, then your own provider at about $0.80 to $3.00 per 1,000 generations.

## Privacy

The plugin sends requests only to `api.useapi.net`, downloads files only from `flow-content.google`, and stores nothing. See [PRIVACY.md](./PRIVACY.md) and the useapi.net [Terms and Privacy Policy](https://useapi.net/docs/legal?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin).

## Support

- API reference: https://useapi.net/docs/api-google-flow-v1
- Examples (Node.js, Python, n8n, an agent skill and this plugin's source): https://github.com/useapi/google-flow-api
- Email support@useapi.net, or ask on [Discord](https://discord.gg/w28uK3cnmF) or [Telegram](https://t.me/use_api).

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).

## Development

The tool YAML and Python stubs are generated from `dev/specs.py`, the single source of the parameters and their four UI languages (English, Simplified Chinese, Japanese, Brazilian Portuguese). Parameter names, models and limits follow the published API catalog, `https://api.useapi.net/v1/google-flow/models`.

```bash
python dev/gen_tools.py                 # writes tools/*.yaml, tools/*.py and the provider YAML
python -m pytest                        # every tool against a mocked HTTP layer
python dev/routing_check.py             # live 401 check of every read-only endpoint with a fake token
dify plugin package . -o google_flow_useapi-0.1.0.difypkg
```

`dev/` and `tests/` are left out of the package by `.difyignore`.
