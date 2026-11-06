# Long Omni 1.2 Flash videos with extend — Google Flow API (Node.js & Python)

Full walkthrough: [How to Generate Audio-Native AI Video with Gemini Omni Flash via the Google Flow API › Extend a video with Omni 1.2](https://useapi.net/docs/articles/omni-flash-bash?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api#extend-a-video-with-omni-12) — June 15, 2026 (November 6, 2026)

Release post with the same story, its requests and the finished 30-second video: [Google Flow: Omni 1.2 Flash, 15-Second Videos, and Extend with Voices](https://useapi.net/blog/261106?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)

Make one video longer than a single generation allows, through the [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api): the first clip comes from Omni 1.2 Flash (3 to 15 seconds), then every extension adds 3 to 10 seconds with its own prompt, voices, reference images or characters, and Google returns the whole video each time.

| Script | What it does |
|---|---|
| `omni-extend.mjs` / `omni-extend.py` | Generates the first clip with [`POST /videos`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) (`model: "omni-flash-1.2"`), then runs [`POST /videos/extend`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-extend?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) once per entry in `extensions`, each on the previous result. Every step runs as an async job (`async: true`), polls [`GET /jobs/{jobid}`](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs-jobid?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) every 10 seconds, and saves `step-N.json` and `step-N.mp4`. The last MP4 is the whole video |

The Node.js and Python versions are equivalent. `story.json` holds the story from the release post: a street magician in a rainy Tokyo alley (10 seconds), then two 10-second extensions with the voices `Charon` and `Aoede`.

## Prerequisites

- [Node.js](https://nodejs.org) v21 or newer (no dependencies to install — uses built-in `fetch`), or [Python](https://www.python.org) 3.x (standard library only — no dependencies to install)
- A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- A connected [Google Flow account](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) on a paid Google AI plan (Plus, Pro or Ultra): extending with Omni 1.2 is paid only (a free account can extend with a Veo `model`, which this example does not use). Google is giving Omni 1.2 to accounts over several days from November 5, 2026, and an account that does not have it yet answers `400`

## Usage

```bash
node ./omni-extend.mjs <API_TOKEN> <EMAIL> [STORY_FILE]
python3 ./omni-extend.py <API_TOKEN> <EMAIL> [STORY_FILE]
```

`STORY_FILE` defaults to `story.json`.

## The story file

The top level is the first clip, sent to `POST /videos` as it is (plus your `email`): `prompt` is required, and `model`, `duration` (3 to 15), `aspectRatio`, `resolution` (`720p` or `360p`), reference images and voices work as on that endpoint. `extensions` is a list of steps, each sent to `POST /videos/extend`:

- `prompt` (required): what happens next
- `duration`: seconds to add, 3 to 10 (default 8)
- `resolution`: `720p` or `360p` (default: the source's)
- `referenceAudio_1`..`referenceAudio_3`: a built-in voice name (such as `Charon`, `Aoede`) or a custom voice id from [`POST /voices`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-voices?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)
- `referenceImage_1`..`referenceImage_3`: local image files (uploaded for you) or `mediaGenerationId`s
- `character_1`..`character_3`: character ids from [`POST /characters`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-characters?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api)

Name a reference in the prompt with an inline mention such as `@referenceAudio_1` or `@character_1` to say exactly where it belongs. Each character's images count toward the same limit of 3 images. `count` and `seed` are passed through too, and with `count` above 1 the next step continues from the first result.

Local files are uploaded for the extensions' `referenceImage_N` only. For the first clip, pass `mediaGenerationId`s from [`POST /assets/{email}`](https://useapi.net/docs/api-google-flow-v1/post-google-flow-assets-email?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api), or use [`omni-flash/`](../omni-flash), which uploads them for you.

## Limits and cost

- Google extends videos shorter than 30 seconds, so the last extension can start from at most 29 seconds, and the whole video ends below 40 seconds
- Credits are per second and the same on every plan: at 720p 3 a second up to 10 seconds and 6 a second above, at 360p 1 and 2. A 10-second extension at 720p is 30 credits, so `story.json` uses 90 credits in total (30 + 30 + 30)
- Try a story at `360p` first: it costs a third, and its extensions stay 360p

## About useapi.net

[useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=referral&utm_campaign=google-flow-api) is a third-party API service, not affiliated with Google. One subscription covers every useapi.net API, and your Google Flow account runs the videos on its own Google AI plan.
