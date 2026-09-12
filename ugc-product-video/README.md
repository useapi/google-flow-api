# UGC product video — the whole pipeline in one run (Node.js & Python)

Build a finished UGC product video end to end through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1) by [useapi.net](https://useapi.net/?utm_source=github&utm_medium=readme&utm_campaign=google-flow-api): one invented presenter showing your products to the camera, in six steps, with nothing processed locally. No editor, no local ffmpeg — the joined MP4 comes back from the API.

📖 Full walkthrough: **[How to Make a UGC Product Video with the Google Flow API](https://useapi.net/docs/articles/google-flow-ugc-product-video)** — September 4, 2026

`ugc-product-video.mjs` (Node.js) and `ugc-product-video.py` (Python) are equivalent implementations — each reads `prompts.json` and runs the same six steps:

| Step | Endpoint | What it makes | Credits |
|---|---|---|---|
| 1 | [`POST /images`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) | a four-view **product sheet** per item | 0 |
| 2 | [`POST /images`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) ×2 + [`POST /characters`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-characters) | two portraits and a **character** built from both | 0 |
| 3 | [`POST /images`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images) | the **still** — presenter and every product in one frame | 0 |
| 4 | [`POST /videos`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos) (async) | one **Omni 1.1 Flash clip** per product, from that still | 15 each |
| 5 | [`POST /videos/upscale`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-upscale) | each clip to **1080p** | 0 |
| 6 | [`POST /videos/concatenate`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-concatenate) | the clips **joined** into the final MP4 | 0 |

The shipped `prompts.json` reproduces the tutorial exactly — three products, three 10-second clips, 45 credits in total.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github&utm_medium=readme&utm_campaign=google-flow-api)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow) email on a **paid** [Google AI](https://one.google.com/ai) plan — images and characters work on a free account, but Omni 1.1 Flash video and upscaling do not

## Usage

```bash
node ./ugc-product-video.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]
python3 ./ugc-product-video.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]
```

`PROMPTS_FILE` defaults to `prompts.json`. A full run takes roughly 5–10 minutes, most of it waiting on the three clips, which are submitted together and generate in parallel.

Everything is written to the working directory, numbered in pipeline order: `01-sheet-*.png`, `02-presenter-front_*.png`, `03-presenter-three-quarter_*.png`, `04-still_*.png`, `05-clip-*-720p.mp4`, `06-clip-*-1080p.mp4`, and the joined `ugc-product-video.mp4`.

## Resuming — this is the part that saves credits

Each step is checkpointed to **`ugc_state.json`** as soon as it succeeds. Re-running picks up where it stopped, so an interrupted run never pays for the clips twice:

```bash
node ./ugc-product-video.mjs <API_TOKEN> <EMAIL>   # crashed at step 6? just run it again
```

To **redo one step**, delete its key from `ugc_state.json` and run again — everything after it is rebuilt from the new result, everything before it is reused. The keys are `sheets`, `portraitFront`, `portraitThreeQuarter`, `character`, `still`, `clips`, `upscaled`, `joined`. Deleting `still`, for example, re-renders the still and then re-generates all three clips from it (15 credits each), but keeps the sheets and the character. Delete the whole file to start over.

Failures are appended to `ugc_errors.txt`.

## Editing `prompts.json`

One object, mirroring the six steps:

- **`products`** — one entry per item, each with a `name` (used in filenames), a `prompt`, and `count` candidates to render. A product sheet shows the same item from four sides in a 2×2 grid, so the model gets the whole object instead of one lucky angle. Name what each panel shows; give flat objects a top-down panel. Keep hands, captions and logos out, because whatever lands on the sheet can end up in the clip.
- **`presenter`** — `front` and `threeQuarter` prompts plus `displayName`, `personalityNotes` and `voice` (one of Google's system presets). The three-quarter portrait is generated *from* the front one via `reference_1`, so the two agree on the face before they become a character.
- **`still`** — the one frame that carries the whole scene. It references the character as `@character_1` and each product sheet as `@reference_1`, `@reference_2`, … in prompt text; the script wires the slots up in `products` order. Add a product and its marker moves with it.
- **`clips`** — one per product, in the same order. Each is generated with the still as **both** `startImage` and `endImage`, so every clip opens and closes on the same frame and any clip can follow any other.
- **`join`** — per-clip `trimStart` / `trimEnd` in seconds, parallel to `clips`.
- **`pick`** — optional on any image step: which candidate to carry forward (default `0`, the first). Every candidate is saved, so look at the PNGs, set `pick`, delete that step's key from `ugc_state.json`, and re-run.

Some things worth knowing before you rewrite the prompts, all learned the hard way in the tutorial:

- **The still carries the tags.** On `omni-flash`, first-plus-last-frame mode accepts *only* the two images — `referenceImage_*`, `character_*` and `referenceAudio_*` are rejected alongside them. Do the tagging in the still and the clips inherit it.
- **Time the choreography.** A 10-second clip with a full line needs the put-down called out by the clock ("by the eight-second mark") and a still, silent hold at the end, or the model runs the line long and snaps into the end frame. About 20 words fits 10 seconds at this pace.
- **Describe the voice identically in every clip.** Nothing carries a voice between separate generations, and a character's `voice` preset cannot reach this mode.
- **Trim to the sound, not the picture.** The presenter goes still before she stops talking, so a cut placed at the first still frame takes the end of a line with it.
- **Keep the presenter invented.** Google's moderation is stricter with real, identifiable people.

Every parameter is documented on [POST /images](https://useapi.net/docs/api-google-flow-v1/post-google-flow-images), [POST /characters](https://useapi.net/docs/api-google-flow-v1/post-google-flow-characters) and [POST /videos](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos).

---

Support: [Discord](https://discord.gg/w28uK3cnmF) · [Telegram](https://t.me/use_api) · [YouTube](https://www.youtube.com/@midjourneyapi)
