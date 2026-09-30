# n8n workflow: Veo 3.1 videos and Nano Banana Pro images with Google Flow

📖 Published on n8n: [Generate Veo 3.1 videos and Nano Banana Pro images with Google Flow](https://n8n.io/workflows/19991)

A ready-to-import [n8n](https://n8n.io) workflow. Type a prompt into a form, pick **Image** or **Video**, and get the finished file back as binary data you can send to Google Drive, S3, Telegram or anything else n8n connects to. It uses only core n8n nodes (Form Trigger, HTTP Request, Code, Wait, Switch), with no community nodes.

- **Images:** one synchronous call to [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) with `nano-banana-pro` (or `nano-banana-2` / `nano-banana-2-lite`).
- **Video:** an async [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) job with `veo-3.1-fast` (or `veo-3.1-lite`, `veo-3.1-quality`, `omni-flash`), then a wait → [GET /jobs](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs-jobid) → loop until `completed` or `failed`.

## Setup

1. Get a useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi) and connect your Google account with the [automated setup](https://useapi.net/docs/start-here/setup-google-flow).
2. In n8n, import [`google-flow-veo-nano-banana.json`](./google-flow-veo-nano-banana.json) (**Workflows → Import from File**), or open the [n8n listing](https://n8n.io/workflows/19991) and click **Use workflow**.
3. Create a **Header Auth** credential: Name `Authorization`, Value `Bearer <your API token>`, and select it on the three HTTP Request nodes.
4. Open the form URL (or click **Test workflow**) and submit a prompt.

Change the models, the number of results and the optional `email` in the **Settings** node. Images work on any Google AI plan, including a free one. Video needs a paid plan and spends its Flow credits.
