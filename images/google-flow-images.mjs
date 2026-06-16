/*

Script version 1.0, June 15, 2026

Script to batch-generate images using prompts with the Google Flow API v1 by useapi.net 🚀
Uses the synchronous POST /images endpoint (default model: imagen-4) and downloads each fifeUrl.
For more details visit https://useapi.net/docs/api-google-flow-v1/post-google-flow-images

Installation Instructions:
==========================

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node google-flow-images.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

node google-flow-images.mjs user:1234-abcdefhijklmnopqrstuv my@email.com

This command executes the script using API token user:1234-abcdefhijklmnopqrstuv with my@email.com Google Flow account email.

Changelog:
==========

- June 15, 2026: Initial release.

*/

import fs from 'fs/promises';
import { writeFile } from 'node:fs/promises';
import { Readable } from 'node:stream';


// Constants
const ERRORS_FILE = 'google-flow-images_errors.txt';
const DEFAULT_PROMPTS_FILE = 'prompts.json';
const DEFAULT_MODEL = 'imagen-4';
const SLEEP_429 = 30 * 1000; // in milliseconds

const urlAccounts = 'https://api.useapi.net/v1/google-flow/accounts';
const urlImages = 'https://api.useapi.net/v1/google-flow/images';
const urlUploadAsset = 'https://api.useapi.net/v1/google-flow/assets/';

// Google Flow accepts png, jpeg and webp for reference images.
const supportedFileExtensions = ['png', 'jpeg', 'webp'];

// reference_1 .. reference_10 are accepted by POST /images.
const referenceParams = Array.from({ length: 10 }, (_, i) => `reference_${i + 1}`);

// { filename: mediaGenerationId }
const uploadedFiles = {};

// Utility to sleep for given milliseconds
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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

const elapsedTimeSec = (start) => (Date.now() - start) / 1000;

// Map a file extension to the Content-Type required by POST /assets
const contentTypeForExt = (ext) => ext === 'png' ? 'image/png' : ext === 'webp' ? 'image/webp' : 'image/jpeg';

async function uploadAsset(apiToken, email, filename) {

    // Check if already uploaded
    if (uploadedFiles.hasOwnProperty(filename))
        return uploadedFiles[filename];

    const startTime = Date.now();

    console.log(`⬆️  Account ${email} uploading file…`, filename);

    const body = new Blob([await fs.readFile(filename)]);

    const fileExt = filename.split('.').pop();

    const response = await fetch(`${urlUploadAsset}${encodeURIComponent(email)}`, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': contentTypeForExt(fileExt)
        },
        body
    });

    if (response.ok) {
        const json = await response.json();
        // POST /assets returns the reference id nested as mediaGenerationId.mediaGenerationId
        const mediaGenerationId = json?.mediaGenerationId?.mediaGenerationId;
        console.log(`🆗 mediaGenerationId (${elapsedTimeSec(startTime)} sec)`, mediaGenerationId);
        uploadedFiles[filename] = mediaGenerationId;
    }
    else {
        console.error(`❗ Unable to upload file HTTP ${response.status} (${elapsedTimeSec(startTime)} sec)`, await response.text());
        // Do not attempt to upload failed file again
        uploadedFiles[filename] = undefined;
    }

    return uploadedFiles[filename];
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

    console.log(`✅ Downloading ${url} to ${filename}`);
    try {
        const imageResponse = await fetch(url);
        if (!imageResponse.ok) {
            console.error(`⛔ Unable to download ${filename} (HTTP ${imageResponse.status})`, url);
            return;
        }
        const stream = Readable.fromWeb(imageResponse.body);
        await writeFile(filename, stream);
    } catch (err) {
        console.error(`⛔ Error during download: ${err}`);
    }
}

// Submit a single prompt to the synchronous POST /images endpoint and download the results.
async function submitImage(apiToken, email, prompt, index) {
    const { model, prompt: text } = prompt;

    const useModel = model ?? DEFAULT_MODEL;

    console.log(`🚀 ${useModel} » Prompt #${index} • account ${email} …`);

    // Build the request body, uploading any local reference_* file to a mediaGenerationId first.
    const body = { model: useModel, email, prompt: text };

    for (const key of ['aspectRatio', 'count', 'seed'])
        if (prompt[key] !== undefined) body[key] = prompt[key];

    for (const refKey of referenceParams) {
        const value = prompt[refKey];
        if (value)
            body[refKey] = await uploadAsset(apiToken, email, value);
    }

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
            const json = JSON.parse(responseText);
            const media = json?.media ?? [];

            if (media.length == 0)
                console.error(`🛑 200 OK but no media for prompt #${index}:\n${text}\n`);

            // count > 1 returns multiple images in the media array.
            for (let i = 0; i < media.length; i++) {
                const img = media[i]?.image?.generatedImage;
                const filename = `google-flow_${index}_${i + 1}.jpg`;
                await downloadImage(img?.fifeUrl, filename);
            }
            return 200;
        }

        switch (response.status) {
            case 429:
                console.log(`🔄️ Retry on HTTP ${response.status}`, responseText);
                await sleep(SLEEP_429);
                break;
            case 503:
                console.log(`🔄️ Service unavailable, retry on HTTP ${response.status}`, responseText);
                await sleep(SLEEP_429);
                break;
            case 402:
                console.log(`🛑 No subscription / insufficient credits`, responseText);
                await fs.appendFile(ERRORS_FILE, `${response.status},#${index}:${text}\n`);
                process.exit(1);
            case 400:
            case 500:
                console.log(`🛑 Rejected (validation or content moderation)`, responseText);
                await fs.appendFile(ERRORS_FILE, `${response.status},#${index}:${text}\n`);
                return response.status;
            default:
                console.log(`❗ FAILED with HTTP ${response.status}`, responseText);
                await fs.appendFile(ERRORS_FILE, `${response.status},#${index}:${text}\n`);
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
        console.error('Usage: node google-flow-images.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]');
        process.exit(1);
    }

    console.info('Script v1.0');
    console.info('Node version is: ' + process.version);

    const start = new Date();
    try {
        console.info('START EXECUTION', start);
        await execute(apiToken, email, promptFile);
    } catch (error) {
        console.error('⛔ Error during execution:', error.stack || error);
    } finally {
        console.info('COMPLETED', new Date());
        console.info('EXECUTION ELAPSED', diffInMinutesAndSeconds(start, new Date()));
    }
}

async function execute(apiToken, email, promptFile) {
    const accounts = await fetchAccounts(apiToken);

    console.info(`Configured Google Flow API accounts (${Object.keys(accounts).length}):`, Object.keys(accounts).join(', '));

    if (Object.keys(accounts).length <= 0) {
        console.error(`⛔ No configured Google Flow accounts found. Please refer to https://useapi.net/docs/start-here/setup-google-flow`);
        process.exit(1);
    }

    if (!accounts[email]) {
        console.error(`⛔ Account ${email} not found. Please refer to https://useapi.net/docs/start-here/setup-google-flow`);
        process.exit(1);
    }

    if (accounts[email].health && accounts[email].health !== 'OK') {
        console.error(`⛔ Account ${email} health is '${accounts[email].health}'. Please resolve and update the account, see https://useapi.net/docs/start-here/setup-google-flow`);
        process.exit(1);
    }

    const promptData = await fs.readFile(promptFile, 'utf8');
    const prompts = JSON.parse(promptData);
    console.log(`Total number of prompts to process`, prompts.length);

    let warnings = [];

    // Parameters accepted by this script for the POST /images endpoint.
    // See https://useapi.net/docs/api-google-flow-v1/post-google-flow-images for every model's full parameter set.
    const supportedParams = ['model', 'prompt', 'aspectRatio', 'count', 'seed', ...referenceParams];

    const invalidKeys = (prompt) => Object.keys(prompt).filter(key => !key.startsWith('__') && !supportedParams.includes(key))

    for (let i = 1; i <= prompts.length; i++) {
        const prompt = prompts[i - 1];
        const { prompt: text } = prompt;

        const validateImage = async (file) => {
            if (file) {
                try {
                    await fs.access(file);
                } catch {
                    warnings.push(`⚠️  Image '${file}' does not exist. Prompt ${i}`);
                }

                const ext = file.split('.').pop();

                if (!supportedFileExtensions.includes(ext))
                    warnings.push(`⚠️  Image ${file} extension ${ext} not supported. Prompt ${i}`);
            }
        };

        const notSupported = invalidKeys(prompt);
        if (notSupported.length)
            warnings.push(`⚠️  Following params not supported: ${notSupported.join(',')}. Prompt ${i}`);

        if (!text)
            warnings.push(`⚠️  prompt is required. Prompt ${i}`);

        await Promise.all(referenceParams.map(refKey => validateImage(prompt[refKey])));
    }

    if (warnings.length > 0) {
        warnings.forEach(warning => console.warn(warning));
        console.error(`⛔ Execution stopped due to warnings.`);
        process.exit(1);
    }

    for (let i = 0; i < prompts.length; i++)
        await submitImage(apiToken, email, prompts[i], i + 1);
}

function diffInMinutesAndSeconds(date1, date2) {
    const diffInSeconds = Math.floor((date2 - date1) / 1000);
    return `${Math.floor(diffInSeconds / 60)} minutes ${diffInSeconds % 60} seconds`;
};

main();
