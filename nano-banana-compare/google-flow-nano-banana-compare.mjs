/*

Script version 1.0, July 2, 2026

Batch-compare Google Flow's Nano Banana image models (2 Lite, 2, Pro) with the useapi.net API 🚀
Reads prompts.json (one entry per model), submits each to the synchronous POST /images endpoint,
and downloads every returned image with a model-labeled filename.
For more details visit https://useapi.net/docs/api-google-flow-v1/post-google-flow-images

Companion tutorial:
  https://useapi.net/docs/articles/google-flow-nano-banana-compare

Installation Instructions:
==========================

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node google-flow-nano-banana-compare.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

node google-flow-nano-banana-compare.mjs user:1234-abcdefhijklmnopqrstuv my@email.com

Changelog:
==========

- July 2, 2026: Initial release.

*/

import fs from 'fs/promises';
import { writeFile } from 'node:fs/promises';
import { Readable } from 'node:stream';

// Constants
const DEFAULT_PROMPTS_FILE = 'prompts.json';
const DEFAULT_MODEL = 'nano-banana-2-lite';
const SLEEP_RETRY = 30 * 1000; // in milliseconds

const urlAccounts = 'https://api.useapi.net/v1/google-flow/accounts';
const urlImages = 'https://api.useapi.net/v1/google-flow/images';

// Utility to sleep for given milliseconds
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const elapsedTimeSec = (start) => (Date.now() - start) / 1000;

// Function to fetch configured Google Flow API accounts
async function fetchAccounts(apiToken) {
    const response = await fetch(urlAccounts, {
        headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${apiToken}`
        }
    });

    if (!response.ok) {
        console.error(`⛔ Error fetching accounts (HTTP ${response.status}): ${response.statusText}`);
        process.exit(1);
    }

    return response.json();
}

// Download a single image from its signed fifeUrl.
async function downloadImage(url, filename) {
    try {
        await fs.access(filename);
        console.log(`⚠️ ${filename} already exists. Skipping download.`);
        return;
    } catch {
        // File does not exist, proceed with downloading
    }

    if (!url) {
        console.error(`🛑 No fifeUrl for ${filename}`);
        return;
    }

    console.log(`✅ Downloading ${filename}`);
    try {
        const imageResponse = await fetch(url);
        if (!imageResponse.ok) {
            console.error(`⛔ Unable to download ${filename} (HTTP ${imageResponse.status})`);
            return;
        }
        await writeFile(filename, Readable.fromWeb(imageResponse.body));
    } catch (err) {
        console.error(`⛔ Error during download: ${err}`);
    }
}

// Submit a single prompt to the synchronous POST /images endpoint and download the results.
async function submitImage(apiToken, email, prompt, index) {
    const model = prompt.model ?? DEFAULT_MODEL;

    // Build the request body.
    const body = { model, email, prompt: prompt.prompt };
    for (const key of ['aspectRatio', 'count', 'seed'])
        if (prompt[key] !== undefined) body[key] = prompt[key];

    console.log(`🚀 ${model} » Prompt #${index} • account ${email} …`);
    const startTime = Date.now();

    while (true) {
        const response = await fetch(urlImages, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiToken}`
            },
            body: JSON.stringify(body)
        });

        const responseText = await response.text();

        if (response.status == 200) {
            const media = JSON.parse(responseText)?.media ?? [];

            if (media.length == 0)
                console.error(`🛑 200 OK but no media (moderated?) for ${model}`);

            // count > 1 returns multiple images in the media array.
            for (let i = 0; i < media.length; i++) {
                const img = media[i]?.image?.generatedImage;
                await downloadImage(img?.fifeUrl, `${model}_${i + 1}.jpg`);
            }
            console.log(`🆗 ${model} done (${elapsedTimeSec(startTime)} sec)`);
            return 200;
        }

        switch (response.status) {
            case 429:
            case 503:
                console.log(`🔄️ Retry on HTTP ${response.status}`, responseText);
                await sleep(SLEEP_RETRY);
                break;
            default:
                console.error(`🛑 ${model} failed with HTTP ${response.status}`, responseText);
                return response.status;
        }
    }
}

// Main function
async function main() {
    const apiToken = process.argv[2];
    const email = process.argv[3];
    const promptFile = process.argv[4] || DEFAULT_PROMPTS_FILE;

    if (!apiToken || !email) {
        console.error('Usage: node google-flow-nano-banana-compare.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]');
        process.exit(1);
    }

    console.info('Script v1.0 • Node version ' + process.version);

    const accounts = await fetchAccounts(apiToken);

    if (!accounts[email]) {
        console.error(`⛔ Account ${email} not found. Please refer to https://useapi.net/docs/start-here/setup-google-flow`);
        process.exit(1);
    }

    if (accounts[email].health && accounts[email].health !== 'OK') {
        console.error(`⛔ Account ${email} health is '${accounts[email].health}'. Please resolve and update the account, see https://useapi.net/docs/start-here/setup-google-flow`);
        process.exit(1);
    }

    const prompts = JSON.parse(await fs.readFile(promptFile, 'utf8'));
    console.log(`Comparing ${prompts.length} model runs …`);

    const start = new Date();
    for (let i = 0; i < prompts.length; i++)
        await submitImage(apiToken, email, prompts[i], i + 1);

    console.info('COMPLETED', new Date(), '• elapsed', elapsedTimeSec(start), 'sec');
}

main();
