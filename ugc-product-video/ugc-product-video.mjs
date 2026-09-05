/*

Script version 1.0, September 4, 2026

Script to build a UGC product video end to end with the Google Flow API v1 by useapi.net 🚀

Runs the whole six-step pipeline from the tutorial: a product sheet per item and a presenter
via POST /images and POST /characters, one still that carries them all, one Omni 1.1 Flash clip
per product from that still via POST /videos (async, polled on GET /jobs/{jobId}), a free 1080p
POST /videos/upscale per clip, and one POST /videos/concatenate to join them.

For more details visit https://useapi.net/docs/articles/google-flow-ugc-product-video

Every step is checkpointed to ugc_state.json, so a re-run resumes where it stopped instead of
paying for the finished steps again. The clips are the only part that costs credits (15 each at
10s/720p), so an interrupted run must never redo them silently.

Installation Instructions:
==========================

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node ugc-product-video.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

node ugc-product-video.mjs user:1234-abcdefhijklmnopqrstuv my@email.com

This command executes the script using API token user:1234-abcdefhijklmnopqrstuv with my@email.com Google Flow account email.

To redo one step, delete its key from ugc_state.json and run again — everything after it is
rebuilt from the new result, everything before it is reused.

Changelog:
==========

- September 4, 2026: Initial release.

*/

import fs from 'fs/promises';
import { writeFile } from 'node:fs/promises';
import { Readable } from 'node:stream';

// Constants
const STATE_FILE = 'ugc_state.json';
const ERRORS_FILE = 'ugc_errors.txt';
const DEFAULT_PROMPTS_FILE = 'prompts.json';
const SLEEP_429 = 30 * 1000; // in milliseconds
const SLEEP_POLL = 15 * 1000; // in milliseconds
const MAX_RETRIES = 10;

const urlImages = 'https://api.useapi.net/v1/google-flow/images';
const urlCharacters = 'https://api.useapi.net/v1/google-flow/characters';
const urlVideos = 'https://api.useapi.net/v1/google-flow/videos';
const urlUpscale = 'https://api.useapi.net/v1/google-flow/videos/upscale';
const urlConcatenate = 'https://api.useapi.net/v1/google-flow/videos/concatenate';
const urlJobs = 'https://api.useapi.net/v1/google-flow/jobs/';

// Utility to sleep for given milliseconds
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const elapsedTimeSec = (start) => ((Date.now() - start) / 1000).toFixed(1);

// --- checkpoint state ------------------------------------------------------
// Keys: sheets, portraitFront, portraitThreeQuarter, character, still,
//       clips, upscaled, joined. A key is written only once its step succeeded.
let state = {};

async function loadState() {
    try {
        state = JSON.parse(await fs.readFile(STATE_FILE, 'utf8'));
        const done = Object.keys(state);
        if (done.length)
            console.log(`♻️  Resuming from ${STATE_FILE}, already done:`, done.join(', '));
    } catch {
        state = {};
    }
}

async function saveState() {
    await fs.writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n');
}

async function logError(what, detail) {
    await fs.appendFile(ERRORS_FILE, `${new Date().toISOString()}\t${what}\t${detail}\n`);
}

// --- HTTP ------------------------------------------------------------------
// One POST with retries. 429 (concurrency) and 503 (upstream busy) are transient
// and cost nothing, so they are retried; everything else is reported and fatal.
async function post(apiToken, url, payload, what) {
    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        const startTime = Date.now();

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiToken}`
            },
            body: JSON.stringify(payload)
        });

        const body = await response.text();

        // POST /images and POST /videos answer 200 when synchronous, 201 when async.
        if (response.status == 200 || response.status == 201)
            return JSON.parse(body);

        switch (response.status) {
            case 429:
                console.log(`🔄️ ${what} — all generation slots busy, retry ${attempt}/${MAX_RETRIES} in ${SLEEP_429 / 1000}s`);
                await sleep(SLEEP_429);
                break;
            case 503:
                console.log(`🔄️ ${what} — service unavailable, retry ${attempt}/${MAX_RETRIES} in ${SLEEP_429 / 1000}s`);
                await sleep(SLEEP_429);
                break;
            case 400:
                console.error(`🛑 ${what} — rejected (validation or content policy):`, body);
                await logError(what, body);
                process.exit(1);
            case 402:
                console.error(`🛑 ${what} — no subscription or insufficient credits:`, body);
                await logError(what, body);
                process.exit(1);
            default:
                console.error(`❗ ${what} — HTTP ${response.status} (${elapsedTimeSec(startTime)} sec):`, body);
                await logError(what, `HTTP ${response.status} ${body}`);
                process.exit(1);
        }
    }

    console.error(`⛔ ${what} — still failing after ${MAX_RETRIES} retries, giving up.`);
    await logError(what, `gave up after ${MAX_RETRIES} retries`);
    process.exit(1);
}

// --- images ----------------------------------------------------------------
// POST /images is synchronous. With count > 1 it returns several candidates;
// all of them are saved so you can look, and candidate `pick` (default the
// first) is the one the pipeline carries forward.
async function generateImage(apiToken, email, spec, label, extra = {}) {
    const startTime = Date.now();
    console.log(`🖼️  ${label} — generating ${spec.count ?? 1} candidate(s)…`);

    const json = await post(apiToken, urlImages, {
        model: spec.model,
        email,
        prompt: spec.prompt,
        aspectRatio: spec.aspectRatio,
        count: spec.count,
        seed: spec.seed,
        ...extra
    }, `POST /images (${label})`);

    const media = json?.media ?? [];
    if (media.length == 0) {
        console.error(`🛑 ${label} — no images returned:`, JSON.stringify(json).slice(0, 400));
        await logError(label, 'no media in POST /images response');
        process.exit(1);
    }

    for (let i = 0; i < media.length; i++)
        await saveImage(media[i]?.image?.generatedImage, `${label}_${i + 1}.png`);

    const pick = spec.pick ?? 0;
    const chosen = media[pick]?.image?.generatedImage?.mediaGenerationId;
    if (!chosen) {
        console.error(`🛑 ${label} — no mediaGenerationId on candidate #${pick + 1} of ${media.length}.`);
        await logError(label, `candidate ${pick} missing mediaGenerationId`);
        process.exit(1);
    }

    console.log(`✅ ${label} — using candidate #${pick + 1} of ${media.length} (${elapsedTimeSec(startTime)} sec)`);
    return chosen;
}

// A generated image arrives either as a signed URL or inline base64, never both.
async function saveImage(generatedImage, filename) {
    if (!generatedImage) return;

    try {
        if (generatedImage.fifeUrl) {
            const response = await fetch(generatedImage.fifeUrl);
            if (!response.ok) {
                console.error(`⛔ Unable to download ${filename} (HTTP ${response.status})`);
                return;
            }
            await writeFile(filename, Readable.fromWeb(response.body));
        } else if (generatedImage.encodedImage) {
            await writeFile(filename, Buffer.from(generatedImage.encodedImage, 'base64'));
        } else {
            console.error(`⛔ ${filename} — response carried neither fifeUrl nor encodedImage`);
            return;
        }
        console.log(`   💾 ${filename}`);
    } catch (error) {
        console.error(`⛔ Error saving ${filename}:`, error.stack || error);
    }
}

// --- videos ----------------------------------------------------------------
// First-plus-last-frame mode: the still goes in both slots. On omni-flash this
// mode accepts nothing else — no reference images, no character, no voice — so
// everything the clip needs must already be in the still.
async function generateClip(apiToken, email, clip, stillId, index) {
    console.log(`🎬 Clip #${index + 1} (${clip.name}) — submitting ${clip.duration}s at ${clip.resolution}…`);

    const json = await post(apiToken, urlVideos, {
        model: clip.model,
        email,
        prompt: clip.prompt,
        aspectRatio: clip.aspectRatio,
        duration: clip.duration,
        resolution: clip.resolution,
        startImage: stillId,
        endImage: stillId,
        async: true
    }, `POST /videos (${clip.name})`);

    // The 201 async payload uses lowercase "jobid"; a sync 200 uses "jobId". Accept either.
    const jobId = json.jobid ?? json.jobId;
    if (!jobId) {
        console.error(`🛑 Clip ${clip.name} — no jobid in response:`, JSON.stringify(json).slice(0, 400));
        await logError(clip.name, 'no jobid in POST /videos response');
        process.exit(1);
    }

    console.log(`   ⏳ jobId ${jobId}`);
    return jobId;
}

// Poll GET /jobs/{jobId} until the clip is done, then download it.
async function awaitClip(apiToken, jobId, filename) {
    const startTime = Date.now();

    while (true) {
        const response = await fetch(`${urlJobs}${jobId}`, {
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${apiToken}`
            }
        });

        if (!response.ok) {
            console.error(`🛑 Poll failed ${jobId} (HTTP ${response.status}):`, await response.text());
            await logError(jobId, `poll HTTP ${response.status}`);
            process.exit(1);
        }

        const { status, error, response: jobResponse } = await response.json();

        if (status == 'failed') {
            console.error(`🛑 FAILED ${jobId}: ${error}`);
            await logError(jobId, `job failed: ${error}`);
            process.exit(1);
        }

        if (status == 'completed') {
            const media = jobResponse?.media?.[0];
            if (!media?.mediaGenerationId) {
                console.error(`🛑 Completed but no media for ${jobId}`);
                await logError(jobId, 'completed with no media');
                process.exit(1);
            }
            console.log(`✅ ${jobId} completed (${elapsedTimeSec(startTime)} sec)`);
            await downloadVideo(media.videoUrl, filename);
            return media.mediaGenerationId;
        }

        console.log(`   ⌛ ${jobId} is ${status}, waiting…`);
        await sleep(SLEEP_POLL);
    }
}

async function downloadVideo(url, filename) {
    if (!url) {
        console.error(`⛔ ${filename} — no videoUrl to download`);
        return;
    }
    try {
        const response = await fetch(url);
        if (!response.ok) {
            console.error(`⛔ Unable to download ${filename} (HTTP ${response.status})`);
            return;
        }
        await writeFile(filename, Readable.fromWeb(response.body));
        console.log(`   💾 ${filename}`);
    } catch (error) {
        console.error(`⛔ Error downloading ${filename}:`, error.stack || error);
    }
}

// --- the six steps ---------------------------------------------------------
async function execute(apiToken, email, promptsFile) {
    const config = JSON.parse(await fs.readFile(promptsFile, 'utf8'));
    const { model, videoModel, products, presenter, still, clips, upscale, join, output } = config;

    if (products.length != clips.length) {
        console.error(`⛔ ${promptsFile} has ${products.length} products but ${clips.length} clips — one clip per product is expected.`);
        process.exit(1);
    }
    if (products.length > 10) {
        console.error(`⛔ POST /images accepts at most 10 reference_* slots, but ${products.length} products were given.`);
        process.exit(1);
    }

    await loadState();

    // Step 1 — a sheet for each product. Four views of one item on one image, so
    // the model gets the whole object instead of one lucky angle.
    if (!state.sheets) {
        console.log(`\n━━ Step 1/6 — a sheet for each of the ${products.length} products ━━`);
        const sheets = [];
        for (const product of products)
            sheets.push(await generateImage(apiToken, email, { model, ...product }, `01-sheet-${product.name}`));
        state.sheets = sheets;
        await saveState();
    }

    // Step 2 — the presenter. A front portrait, a three-quarter generated FROM it
    // so the two agree on the face, then a character built from both.
    if (!state.portraitFront) {
        console.log(`\n━━ Step 2/6 — the presenter ━━`);
        state.portraitFront = await generateImage(apiToken, email, { model, ...presenter.front }, '02-presenter-front');
        await saveState();
    }
    if (!state.portraitThreeQuarter) {
        state.portraitThreeQuarter = await generateImage(
            apiToken, email, { model, ...presenter.threeQuarter }, '03-presenter-three-quarter',
            { reference_1: state.portraitFront });
        await saveState();
    }
    if (!state.character) {
        console.log(`👤 Character "${presenter.displayName}" — from both portraits…`);
        const json = await post(apiToken, urlCharacters, {
            displayName: presenter.displayName,
            personalityNotes: presenter.personalityNotes,
            imageReference_1: state.portraitFront,
            imageReference_2: state.portraitThreeQuarter,
            voice: presenter.voice
        }, 'POST /characters');

        if (!json?.character) {
            console.error(`🛑 No character in response:`, JSON.stringify(json).slice(0, 400));
            await logError('characters', 'no character field in response');
            process.exit(1);
        }
        state.character = json.character;
        await saveState();
        console.log(`✅ Character created`);
    }

    // Step 3 — the still. Character in character_1, every sheet in reference_N,
    // placed by @-marker in the prompt. This one frame carries the whole scene.
    if (!state.still) {
        console.log(`\n━━ Step 3/6 — the still ━━`);
        const references = {};
        state.sheets.forEach((id, i) => { references[`reference_${i + 1}`] = id; });
        state.still = await generateImage(apiToken, email, { model, ...still }, '04-still', {
            character_1: state.character,
            ...references
        });
        await saveState();
    }

    // Step 4 — one clip per product, every one starting and ending on the still,
    // so any clip can follow any other. This is the only step that costs credits.
    if (!state.clips) {
        console.log(`\n━━ Step 4/6 — ${clips.length} clips, all from the still ━━`);

        // Submit them all first, then collect — they generate in parallel.
        const jobs = [];
        for (let i = 0; i < clips.length; i++)
            jobs.push(await generateClip(apiToken, email, { model: videoModel, ...clips[i] }, state.still, i));

        const generated = [];
        for (let i = 0; i < jobs.length; i++)
            generated.push(await awaitClip(apiToken, jobs[i], `05-clip-${i + 1}-${clips[i].name}-720p.mp4`));

        state.clips = generated;
        await saveState();
    }

    // Step 5 — upscale to 1080p. Free on any paid plan, synchronous, and the new
    // id is just the source id with _upsampled on the end.
    if (!state.upscaled) {
        console.log(`\n━━ Step 5/6 — upscale to ${upscale.resolution} ━━`);
        const upscaled = [];
        for (let i = 0; i < state.clips.length; i++) {
            const startTime = Date.now();
            console.log(`⬆️  Clip #${i + 1} (${clips[i].name}) — upscaling…`);
            const json = await post(apiToken, urlUpscale, {
                mediaGenerationId: state.clips[i],
                resolution: upscale.resolution
            }, `POST /videos/upscale (${clips[i].name})`);

            const media = json?.media?.[0];
            if (!media?.mediaGenerationId) {
                console.error(`🛑 Upscale returned no media for clip #${i + 1}:`, JSON.stringify(json).slice(0, 400));
                await logError(clips[i].name, 'upscale returned no media');
                process.exit(1);
            }
            console.log(`✅ Clip #${i + 1} upscaled (${elapsedTimeSec(startTime)} sec)`);
            await downloadVideo(media.videoUrl, `06-clip-${i + 1}-${clips[i].name}-${upscale.resolution}.mp4`);
            upscaled.push(media.mediaGenerationId);
        }
        state.upscaled = upscaled;
        await saveState();
    }

    // Step 6 — join them. Trim to the sound, not the picture: she goes still
    // before she stops talking, so a cut at the first still frame clips a line.
    if (!state.joined) {
        console.log(`\n━━ Step 6/6 — join ━━`);
        const startTime = Date.now();
        const media = state.upscaled.map((mediaGenerationId, i) => ({ mediaGenerationId, ...(join?.[i] ?? {}) }));

        const json = await post(apiToken, urlConcatenate, { media }, 'POST /videos/concatenate');

        if (!json?.encodedVideo) {
            console.error(`🛑 No encodedVideo in response:`, JSON.stringify(json).slice(0, 400));
            await logError('concatenate', 'no encodedVideo in response');
            process.exit(1);
        }

        await writeFile(output, Buffer.from(json.encodedVideo, 'base64'));
        state.joined = output;
        await saveState();
        console.log(`✅ Joined ${media.length} clips (${elapsedTimeSec(startTime)} sec)`);
        console.log(`   💾 ${output}`);
    }

    console.log(`\n🎉 Done — ${state.joined}`);
}

async function main() {
    const apiToken = process.argv[2];
    const email = process.argv[3];
    const promptsFile = process.argv[4] || DEFAULT_PROMPTS_FILE;

    if (!apiToken || !email) {
        console.error('Usage: node ugc-product-video.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]');
        console.error('Example: node ugc-product-video.mjs user:1234-abcdefhijklmnopqrstuv my@email.com');
        process.exit(1);
    }

    try {
        await execute(apiToken, email, promptsFile);
    } catch (error) {
        console.error('⛔ Unexpected error:', error.stack || error);
        process.exit(1);
    }
}

main();
