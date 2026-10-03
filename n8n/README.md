# n8n workflows for the Google Flow API

Two ready-to-import [n8n](https://n8n.io) workflows. Both use only core n8n nodes, with no community nodes.

| Workflow | What it does |
|---|---|
| [`ugc-ad-factory.json`](./ugc-ad-factory.json) | A form that walks you through a whole **UGC video ad** with **Omni 1.1 Flash**: presenter, voice, products, scene, clips, 1080p, download |
| [`google-flow-veo-nano-banana.json`](./google-flow-veo-nano-banana.json) | A form that generates **Veo 3.1** video or **Nano Banana Pro** images and returns the files |

## UGC Ad Factory

📖 Full walkthrough: [How to Make UGC Video Ads in n8n with the Google Flow API](https://useapi.net/docs/articles/google-flow-n8n-ugc-ads)

Open one form URL and build a short UGC-style video ad page by page. Every page shows the results so you can pick one or re-roll before anything costs credits:

1. **Setup.** 1 to 5 products, an optional intro and closing clip, vertical 9:16 or horizontal 16:9, and 1 to 4 takes per clip.
2. **Details.** Describe the presenter or upload photos of them, or paste a saved character ID. Describe each product or upload a photo of it, and write what is said in each clip.
3. **Presenter, second angle and voice.** Four candidates each, plus four preset voices reading your sample line. Face and voice are saved as one character.
4. **Product images.** Four four-view sheets per product, or your own photo as is.
5. **Scene.** The presenter and every product in one frame. The page shows the credit cost of the clips before you continue.
6. **Clips.** One per product plus the intro and closing, filmed in that scene with the picked voice. Pick a take per clip, or edit the action and re-roll.
7. **Your ad.** Optional free 1080p upscale, a player and an MP4 download, cut points you can adjust per clip and re-join for free, and the character ID to reuse.

Images, voices, the character, upscaling and joining are free. Each Omni take costs 7, 10, 12 or 15 Flow credits for a 4, 6, 8 or 10 second clip. Right after the details page the workflow checks the Google account (connected, on a paid plan, enough credits for the clips you chose) and stops at once if something is wrong, before anything is generated. Captcha and temporary errors are retried automatically, refusals ask you to change the action, and account problems stop with a page that says what to fix. While a step runs, the page shows what is being made, how long it usually takes and a running clock.

Setup is the same as below: import the file, create the Header Auth credential, select it on every HTTP Request node, activate the workflow and open the **Start form** URL. Tested on self-hosted n8n 2.41.

## Veo 3.1 videos and Nano Banana Pro images

📖 Published on n8n: [Generate Veo 3.1 videos and Nano Banana Pro images with Google Flow](https://n8n.io/workflows/19991)

Type a prompt into a form, pick **Image** or **Video**, and get the finished file back as binary data you can send to Google Drive, S3, Telegram or anything else n8n connects to. It uses only core n8n nodes (Form Trigger, HTTP Request, Code, Wait, Switch), with no community nodes.

- **Images:** one synchronous call to [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) with `nano-banana-pro` (or `nano-banana-2` / `nano-banana-2-lite`).
- **Video:** an async [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) job with `veo-3.1-fast` (or `veo-3.1-lite`, `veo-3.1-quality`, `omni-flash`), then a wait → [GET /jobs](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs-jobid) → loop until `completed` or `failed`.

## Setup

1. Get a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi) and connect your Google account with the [automated setup](https://useapi.net/docs/start-here/setup-google-flow).
2. In n8n, import [`google-flow-veo-nano-banana.json`](./google-flow-veo-nano-banana.json) (**Workflows → Import from File**), or open the [n8n listing](https://n8n.io/workflows/19991) and click **Use workflow**.
3. Create a **Header Auth** credential: Name `Authorization`, Value `Bearer <your API token>`, and select it on the three HTTP Request nodes.
4. Open the form URL (or click **Test workflow**) and submit a prompt.

Change the models, the number of results and the optional `email` in the **Settings** node. Images work on any Google AI plan, including a free one. Video needs a paid plan and spends its Flow credits.
