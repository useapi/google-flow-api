# Plugin Submission

## Plugin information

- **Author**: useapi
- **Plugin name**: google_flow_useapi
- **Version**: 0.1.0
- **Source repository**: https://github.com/useapi/google-flow-api/tree/main/dify-plugin
- **Contact**: support@useapi.net

## Submission type

- [x] New plugin
- [ ] Version update

## What changed

New tool plugin for Google Flow, Google's video and image studio, through the useapi.net Google Flow API. 20 tools:

- Generate video with Veo 3.1 Lite, Omni 1.2 Flash or Veo 3.1 Lite Lower Priority: text to video, start and end frames, reference images, characters, a narration voice, and video edits.
- Extend video, Upscale video (720p, 1080p, 4K), Generate image (Nano Banana 2 Lite, Nano Banana 2.1, Nano Banana Pro), Upscale image, Video to GIF, Join videos.
- The Google Flow agent: start or continue a chat, read it, answer its approval requests, list chats.
- Accounts, jobs, uploads, media, characters and voices.

Results come back as text, JSON, workflow variables and Dify files. The interface is in English, Simplified Chinese, Japanese and Brazilian Portuguese.

useapi.net is not affiliated with Google; this is stated in the plugin description, README and PRIVACY.md. The plugin itself is free. It requires external paid services, disclosed in the description and README: a useapi.net subscription ($15/month), the user's own Google AI plan (the free plan works for Veo 3.1 Lite, Omni 1.2 Flash and Nano Banana), and captcha solving (300 free credits with the first account, then the user's own captcha provider). The README opens with a short table of the Google AI plans (Free to Google AI Ultra $199): price, Google Flow credits, models and extras, with sources and dates.

## Risk level

- [ ] Low risk
- [x] Medium risk
- [ ] High risk

Medium: the plugin sends user content (prompts, agent messages and uploaded images and videos) to an external service, performs write actions there (generations that spend the user's Google Flow credits, uploads), and downloads the generated files. Requests go to one fixed HTTPS API, `api.useapi.net`; files are downloaded only from Google's media host `flow-content.google`. Both are declared in `manifest.yaml` `network.domains`.

## Required checks

- [x] I have read and followed the [Marketplace submission requirements](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-submission-requirements.md).
- [x] I have read and comply with the Plugin Developer Agreement.
- [x] I tested this plugin on Dify Community Edition and Dify Cloud, or documented any limitation below.
- [x] The package contains only files needed at runtime.
- [x] The package does not contain secrets, local credentials, `.env` files, `.git` directories, virtual environments, caches, logs, or IDE files.
- [x] The package does not contain executables or bundled binaries, or I explained why they are required below.
- [x] The plugin README includes setup steps, usage instructions, required APIs or credentials, connection requirements, and the source repository link.
- [x] The plugin includes `PRIVACY.md` or a hosted privacy policy, and `manifest.yaml` references it.
- [x] All user-facing text is primarily in English, with any localized README files following the [i18n guidance](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/multilingual-readme).

## Security and privacy notes

- Network: API calls go only to `https://api.useapi.net/v1/google-flow`. Finished images and videos are downloaded only from `https://flow-content.google` (Google's signed, time-limited links that the API returns); the plugin checks the scheme and host before every download, does not follow redirects, and never sends the API token there. Both domains are in `manifest.yaml` `network.domains`. The `useapi.net` hits in the static scan are documentation links inside error messages, not requests.
- File upload: image and video parameters accept a Dify file the user selected. It is sent to the API as the request body of the upload endpoint (PNG, JPEG, WebP up to 20 MB, MP4 up to 100 MB). No filesystem access.
- Credentials: the useapi.net token is a `secret-input` and is sent only in the `Authorization` header to `api.useapi.net`. Error messages never include it (the "token" in error strings is the word, plus a link to the setup page). Account cookies that the account endpoint returns (masked by the API) are removed before any output reaches Dify.
- The "payment" and "charged" matches in the financial check are the 402 Payment Required error message, the subscription price disclosure, and text telling the user that the Google Flow agent spends the user's own Google Flow credits. The plugin performs no payments or transfers.
- Every request has a timeout (60 s; 150 s for agent messages; 240 to 300 s for generations, uploads and downloads, since a generation request waits for its captcha). Waits are capped at 420 s, under Dify's 600 s plugin limit: long jobs return a job id and the user checks it with "Get job status".
- The plugin stores nothing; see PRIVACY.md.

## Local validation

```
python -m pytest                                    # 218 passed: every tool with a mocked HTTP layer, SDK loading of all YAML and tool classes, i18n completeness, agent safety
ruff check .                                        # All checks passed
python dev/routing_check.py                         # 10/10 read-only endpoints answer 401 to a fake token (routes exist)
dify plugin package ./dify-plugin                   # plugin packaged successfully
python3 validator/validate-difypkg.py <pkg>         # dify-marketplace-toolkit: 0 blocking failures (review warnings explained in Security and privacy notes)
python3 validator/test-plugin-install.py -d <dir>   # Plugin test result: success
```

## Reviewer notes

This is a tool plugin, not a model provider or a plain gateway. It does not resell a model API:

- It runs on the user's own Google AI plan. Videos spend the Google Flow credits that come with that plan (the free plan included); images use none. Google's per-call Gemini API is not involved and is not billed.
- It covers what only Google Flow offers: the Google Flow agent (Google's own creative agent, with its approval step), saved characters and voices, video extend, upscale to 4K, GIF export and clip joining.
- Users can connect several Google accounts. With the email left empty, useapi.net sends each new job to a healthy account and sets aside accounts that Google throttled or that reached their quota, so users get more parallel jobs, more credits in total, and work that keeps going when one account is limited. A plugin built on a single Gemini API key cannot do this.

Price comparison, plan cost only (the useapi.net subscription, $15/month, is separate):

| Per generation | Google's paid API | Google AI Ultra $199.99 (25,000 credits) | Google AI Pro $19.99 (1,000 credits) | Free plan |
|---|---|---|---|---|
| Veo 3.1 Lite video, 8 s, 720p | $0.40 | $0.04 (5 credits) | $0.20 (10 credits) | 10 credits of the 50 a day |
| Nano Banana Pro image | $0.134 | $0 (no credits) | $0 | $0 |
| Nano Banana 2.1 image | $0.034 | $0 | $0 | $0 |

On Google AI Ultra a Veo 3.1 Lite clip costs one tenth of Google's API price, and images use no credits on any plan. Sources: Google Cloud Vertex AI pricing (Veo 3.1 Lite $0.05 a second at 720p) and the Gemini API pricing page, read 2026-11-06; plan prices and credits from gemini.google/subscriptions, read 2026-10-20; credits per video from the Google Flow credits page (support.google.com/flow/answer/16526234).

Brand: "Google Flow" is a Google product name. The label names the provider ("Google Flow by useapi.net"), the description says "Third-party API by useapi.net, not affiliated with Google", and the icon is our own paper-boat logo, not Google's. We already publish `useapi/notebooklm_useapi` (merged in #3410) with the same approach.

Testing: 0.1.0 was tested on Dify Cloud on 2026-11-25 in an agent app (gpt-5): local package install, credential validation (Save checks the token with GET /accounts), "List Google accounts" (one healthy account, rotation path with the email left empty), and "Generate image" with Nano Banana 2 Lite, which returned the media id, the temporary link and the .jpg as a Dify file (shown in the conversation log). Limitation: on Dify Cloud the Legacy Agent "Debug & Preview" chat crashed in the browser while drawing the returned file ("Cannot use 'in' operator to search for 'transferMethod'" in Dify's front end); the same message and file show correctly in the app's Logs. Video generation was not run on Dify (it spends Google Flow credits); it is covered by the mocked tests. Not tested on a self-hosted Community Edition instance.
