#!/usr/bin/env node
/*
Make one long Omni 1.2 Flash video with the Google Flow API by useapi.net: generate the first clip, then extend it step by step.

1. POST /videos with the story's first prompt (model omni-flash-1.2, 3 to 15 seconds).
2. POST /videos/extend for every entry in `extensions`: each adds 3 to 10 seconds to the clip before it, with its own prompt
   and optional voices (referenceAudio_1..3), reference images (referenceImage_1..3, local files uploaded for you) and
   characters (character_1..3). Each answer is ONE clip, the whole video so far plus the new seconds.
3. Every step's job is saved as step-N.json and its MP4 as step-N.mp4. The last one is the finished video.

Google Flow extends videos shorter than 30 seconds, so the last extension can start from at most 29 seconds.
Extend needs a paid Google AI plan (Plus, Pro or Ultra).

Usage: node omni-extend.mjs <API_TOKEN> <EMAIL> [STORY_FILE]
       STORY_FILE defaults to story.json

Docs: https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-extend
Walkthrough: https://useapi.net/blog/261106
*/

import fs from 'fs/promises';
import path from 'path';

const BASE = process.env.USEAPI_BASE ?? 'https://api.useapi.net/v1/google-flow';
const POLL_MS = 10000;
const REFERENCE_KEYS = ['referenceImage_1', 'referenceImage_2', 'referenceImage_3'];
const EXTEND_KEYS = ['duration', 'resolution', 'count', ...REFERENCE_KEYS,
    'character_1', 'character_2', 'character_3', 'referenceAudio_1', 'referenceAudio_2', 'referenceAudio_3'];

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function api(token, method, url, body, headers = {}) {
    const res = await fetch(url, {
        method,
        headers: { Authorization: `Bearer ${token}`, ...(body && !(body instanceof Buffer) && { 'Content-Type': 'application/json' }), ...headers },
        body: body instanceof Buffer ? body : body && JSON.stringify(body),
    });
    const text = await res.text();
    let json;
    try { json = JSON.parse(text); } catch { json = { error: text }; }
    return { status: res.status, json };
}

// A local image file → its mediaGenerationId on this account (POST /assets/{email}); anything else is passed as-is.
async function resolveImage(token, email, ref) {
    if (!ref || ref.startsWith('user:')) return ref;
    const ext = path.extname(ref).toLowerCase();
    const type = ext === '.png' ? 'image/png' : ext === '.webp' ? 'image/webp' : 'image/jpeg';
    const r = await api(token, 'POST', `${BASE}/assets/${encodeURIComponent(email)}`, await fs.readFile(ref), { 'Content-Type': type });
    const id = r.json?.mediaGenerationId?.mediaGenerationId;
    if (!id) throw new Error(`upload of ${ref} failed (HTTP ${r.status}): ${JSON.stringify(r.json)}`);
    console.log(`📤 uploaded ${ref}`);
    return id;
}

// Submit in async mode, then poll GET /jobs/{jobid} until the job completes or fails.
async function run(token, url, body, step) {
    const r = await api(token, 'POST', url, { ...body, async: true });
    if (r.status !== 200 && r.status !== 201) throw new Error(`step ${step}: HTTP ${r.status} ${JSON.stringify(r.json)}`);
    const jobid = r.json.jobid;
    console.log(`⏳ step ${step}: job ${jobid}`);
    for (;;) {
        await sleep(POLL_MS);
        const j = await api(token, 'GET', `${BASE}/jobs/${jobid}`);
        if (j.status === 429 || j.status >= 500) continue;
        if (j.status !== 200) throw new Error(`step ${step}: GET /jobs answered HTTP ${j.status} ${JSON.stringify(j.json)}`);
        if (j.json.status === 'completed') return j.json;
        if (j.json.status === 'failed') throw new Error(`step ${step} failed: ${JSON.stringify(j.json.error ?? j.json.response?.error ?? j.json)}`);
    }
}

async function save(job, step) {
    await fs.writeFile(`step-${step}.json`, JSON.stringify(job, null, 2));
    const media = job.response.media[0];
    const res = await fetch(media.videoUrl);
    if (!res.ok) throw new Error(`step ${step}: video download HTTP ${res.status}`);
    await fs.writeFile(`step-${step}.mp4`, Buffer.from(await res.arrayBuffer()));
    console.log(`✅ step ${step}: step-${step}.mp4, ${media.video?.dimensions?.length}, ${job.response.remainingCredits} credits left`);
    return media.mediaGenerationId;
}

async function main() {
    const [token, email, storyFile = 'story.json'] = process.argv.slice(2);
    if (!token || !email) {
        console.error('Usage: node omni-extend.mjs <API_TOKEN> <EMAIL> [STORY_FILE]');
        process.exit(1);
    }
    const { extensions = [], ...first } = JSON.parse(await fs.readFile(storyFile, 'utf8'));

    let source = await save(await run(token, `${BASE}/videos`, { ...first, email }, 1), 1);
    for (const [i, ext] of extensions.entries()) {
        const body = { prompt: ext.prompt, mediaGenerationId: source };
        for (const key of EXTEND_KEYS) if (ext[key] !== undefined) body[key] = ext[key];
        for (const key of REFERENCE_KEYS) if (body[key]) body[key] = await resolveImage(token, email, body[key]);
        source = await save(await run(token, `${BASE}/videos/extend`, body, i + 2), i + 2);
    }
    console.log(`🎬 done: step-${extensions.length + 1}.mp4 is the whole video`);
}

main().catch(e => { console.error(`🛑 ${e.message}`); process.exit(1); });
