# n8n workflows for the Google Flow API

Three ready-to-import [n8n](https://n8n.io) workflows for the [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) by useapi.net. Import the JSON file in n8n with **Workflows → Import from File**. The Sheet batch uses the core Google Sheets and Google Drive nodes, the forms only core n8n nodes, and none needs a community node.

| Workflow | What it does |
|---|---|
| [`google-flow-sheet-batch.json`](./google-flow-sheet-batch.json) | Batch-generates **Veo 3.1** videos and **Nano Banana Pro** images from the rows of a **Google Sheet**, saves them to Google Drive and writes the status and links back to each row |
| [`ugc-ad-factory.json`](./ugc-ad-factory.json) | A form that walks you through a whole **UGC video ad** with **Omni 1.1 Flash**: presenter, voice, products, scene, clips, 1080p, download |
| [`google-flow-veo-nano-banana.json`](./google-flow-veo-nano-banana.json) | A form that generates **Veo 3.1** video or **Nano Banana Pro** images and returns the files |

## Google Sheet batch: Veo 3.1 videos and Nano Banana Pro images

Import [`google-flow-sheet-batch.json`](./google-flow-sheet-batch.json).

Also on n8n.io: [Batch-generate Veo 3.1 videos and Nano Banana Pro images from Google Sheets with Google Flow](https://n8n.io/workflows/19991)

Each row of the sheet is one job: a prompt, a `type` (`image`, `video` or `image+video`) and optional models, aspect ratio and upscale. Run it by hand or publish it for an hourly run. Rows with an empty `status` are marked `running` at once, so overlapping runs never take a row twice, and then run one by one:

- **Images:** [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) with Nano Banana Pro, usually 10 to 20 seconds each.
- **Video:** an async [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) job with Veo 3.1, polled with [GET /jobs](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api). An `image+video` row can use its image as the first frame, and `upscale` makes a free 1080p copy on paid Google AI plans.
- **Results:** files go to your Google Drive folder, and the row gets `done` or `failed: <reason>` with the links. Busy answers (`429`) wait and retry, and one failed row never stops the batch. Result links expire after about 6 hours, so keep `drive_link`.

Setup: a Header Auth credential (Name `Authorization`, Value `Bearer <your API token>`) on the four useapi.net HTTP nodes, Google Sheets and Drive OAuth2 credentials, and your `sheetId` in **Settings**. Row 1 of the tab holds these columns: `prompt`, `video_prompt`, `type`, `image_model`, `video_model`, `aspect_ratio`, `use_image_as_first_frame`, `upscale`, `email`, `status`, `image_url`, `video_url`, `drive_link`, `error`. **Settings** also holds the defaults, batch size, retries and Drive folder, and clearing a row's `status` runs it again.

## UGC Ad Factory

Import [`ugc-ad-factory.json`](./ugc-ad-factory.json). Full walkthrough: [How to Make UGC Video Ads in n8n with the Google Flow API](https://useapi.net/docs/articles/google-flow-n8n-ugc-ads?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)

Also on n8n.io: [Create UGC video ads with Google Flow Omni 1.1 Flash via useapi.net](https://n8n.io/workflows/20392)

An ad made with this workflow, on YouTube: [How to Make UGC Video Ads in n8n with the Google Flow API](https://youtube.com/shorts/1vPpoNdWHJw)

Open one form URL and build a short UGC-style video ad page by page. Every page shows the results so you can pick one or re-roll before anything costs credits:

1. **Setup.** 1 to 5 products, an optional intro and closing clip, vertical 9:16 or horizontal 16:9, and 1 to 4 takes per clip.
2. **Details.** Describe the presenter or upload photos of them, or paste a saved character ID. Describe each product or upload a photo of it, and write what is said in each clip.
3. **Presenter, second angle and voice.** Four candidates each, plus four preset voices reading your sample line. Face and voice are saved as one character.
4. **Product images.** Four four-view sheets per product, or your own photo as is.
5. **Scene.** The presenter and every product in one frame. The page shows the credit cost of the clips before you continue.
6. **Clips.** One per product plus the intro and closing, filmed in that scene with the picked voice. Pick a take per clip, or edit the action and re-roll.
7. **Your ad.** Optional free 1080p upscale, a player and an MP4 download, cut points you can adjust per clip and re-join for free, and the character ID to reuse.

Images, voices, the character, upscaling and joining are free. Each Omni take costs 7, 10, 12 or 15 Flow credits for a 4, 6, 8 or 10 second clip. Right after the details page the workflow checks the Google account (connected, on a paid Google AI subscription, enough credits for the clips you chose) and stops at once if something is wrong, before anything is generated. Captcha and temporary errors are retried automatically, refusals ask you to change the action, and account problems stop with a page that says what to fix. While a step runs, the page shows what is being made, how long it usually takes and a running clock. The run lives on your n8n server, not in the browser: the pages before the long steps show a resume link, so you can close the tab while the clips render and come back to your picks and finished takes. If the page does not load yet, the step is still running, so try again in a few minutes.

Setup is the same as below: import the file, create the Header Auth credential, select it on every HTTP Request node, create a **Basic Auth** credential (any username and password) and select it on **Start form** so only you can open the form and spend your allowance, then activate the workflow and open the **Start form** URL. Tested on self-hosted n8n 2.41.

## Veo 3.1 videos and Nano Banana Pro images from a form

Import [`google-flow-veo-nano-banana.json`](./google-flow-veo-nano-banana.json). This is the simple one-prompt version. Its n8n.io listing now carries the Google Sheet batch above.

Type a prompt into a form, pick **Image** or **Video**, and get the finished file back as binary data you can send to Google Drive, S3, Telegram or anything else n8n connects to. It uses only core n8n nodes (Form Trigger, HTTP Request, Code, Wait, Switch), with no community nodes.

- **Images:** one synchronous call to [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) with `nano-banana-pro` (or `nano-banana-2` / `nano-banana-2-lite`).
- **Video:** an async [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) job with `veo-3.1-fast` (or `veo-3.1-lite`, `veo-3.1-quality`, `omni-flash`), then a wait → [GET /jobs](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) → loop until `completed` or `failed`.

## Setup

1. Get a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) and connect your Google account with the [automated setup](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api).
2. In n8n, import [`google-flow-veo-nano-banana.json`](./google-flow-veo-nano-banana.json) (**Workflows → Import from File**).
3. Create a **Header Auth** credential: Name `Authorization`, Value `Bearer <your API token>`, and select it on the three HTTP Request nodes.
4. Create a **Basic Auth** credential (any username and password) and select it on **Prompt form**, so only you can open the form and spend your allowance.
5. Open the form URL (or click **Test workflow**) and submit a prompt.

Change the models, the number of results and the optional `email` in the **Settings** node. Images work on every Google AI subscription, a free account included, and use no Flow credits. Video spends Flow credits: a free account gets 50 a day, enough for 2 Veo 3.1 Fast or 5 Lite videos, and Omni 1.1 Flash needs a paid subscription.
