/*

Script version 1.0, June 15, 2026

Script to batch-generate videos using prompts with the Google Flow API v1 by useapi.net 🚀
Uses the POST /videos endpoint in async mode (default model: veo-3.1-fast) and polls GET /jobs/{jobId}.
For more details visit https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos

Installation Instructions:
==========================

You need Node.js v21 or newer installed to run this script. Download and install Node.js from:

- Windows, macOS, Linux: https://nodejs.org/

After installation, verify by running the following command in a terminal:

   node -v

Running the Script:
===================

Usage: node google-flow.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

node google-flow.mjs user:1234-abcdefhijklmnopqrstuv my@email.com

This command executes the script using API token user:1234-abcdefhijklmnopqrstuv with my@email.com Google Flow account email.

Changelog:
==========

- June 15, 2026: Initial release.

*/

import readline from 'node:readline';
import fs from 'fs/promises';
import path from 'path';
import { writeFile } from 'node:fs/promises';
import { Readable } from 'node:stream';


// Constants
const RESULTS_FILE = 'google-flow_results.txt';
const ERRORS_FILE = 'google-flow_errors.txt';
const DEFAULT_PROMPTS_FILE = 'prompts.json';
const DEFAULT_MODEL = 'veo-3.1-fast';
const SLEEP_429 = 30 * 1000; // in milliseconds
const SLEEP_POLL = 15 * 1000; // in milliseconds

const urlAccounts = 'https://api.useapi.net/v1/google-flow/accounts';
const urlVideos = 'https://api.useapi.net/v1/google-flow/videos';
const urlJobs = 'https://api.useapi.net/v1/google-flow/jobs/';
const urlUploadAsset = 'https://api.useapi.net/v1/google-flow/assets/';

// To upload .webp keep its .webp extension — Google Flow accepts png, jpeg and webp.
const supportedFileExtensions = ['png', 'jpeg', 'webp'];

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

async function submit(apiToken, url, body, index, prompt) {
    const createResponse = await fetch(url, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiToken}`
        },
        body
    });

    const createBody = await createResponse.text();

    // Async POST /videos returns 201 Created with a jobid to poll.
    if (createResponse.status == 201) {
        const json = JSON.parse(createBody);
        // 201 async payload uses lowercase "jobid"; sync 200 uses "jobId". Accept either.
        const jobId = json.jobid ?? json.jobId;
        if (jobId) {
            await fs.appendFile(RESULTS_FILE, `${jobId},#${index}:${prompt}\n`);
            console.log(`✅ jobId`, jobId);
            return 201;
        } else {
            const error = `No jobid found in HTTP 201 response`;
            console.log(`❓ ${error}`, createBody);
            await fs.appendFile(ERRORS_FILE, `${error},#${index}:${prompt}\n`);
            return 500;
        }
    } else {
        switch (createResponse.status) {
            case 429:
                console.log(`🔄️ Retry on HTTP ${createResponse.status}`, createBody);
                break;
            case 503:
                console.log(`🔄️ Service unavailable, retry on HTTP ${createResponse.status}`, createBody);
                break;
            case 400:
                console.log(`🛑 Rejected request (validation or content policy)`, createBody);
                await fs.appendFile(ERRORS_FILE, `${createResponse.status},#${index}:${prompt}\n`);
                break;
            case 402:
                console.log(`🛑 No subscription / insufficient credits`, createBody);
                break;
            default:
                console.log(`❗ FAILED with HTTP ${createResponse.status}`, createBody);
                await fs.appendFile(ERRORS_FILE, `${createResponse.status},#${index}:${prompt}\n`);
        }
        return createResponse.status;
    }
}

// Submit a single prompt to POST /videos in async mode.
// startImage = start frame (I2V), endImage = end frame (I2V-FL, Veo only, requires startImage).
async function submitVideo(apiToken, email, prompt, index) {
    const { model, prompt: text, startImage, endImage, aspectRatio, duration, count, seed } = prompt;

    const useModel = model ?? DEFAULT_MODEL;

    console.log(`🚀 ${useModel} » Prompt #${index} • account ${email} …`);

    const startImageId = startImage ? await uploadAsset(apiToken, email, startImage) : undefined;
    const endImageId = endImage ? await uploadAsset(apiToken, email, endImage) : undefined;

    const body = JSON.stringify({
        model: useModel,
        email,
        prompt: text,
        aspectRatio,
        duration,
        count,
        seed,
        startImage: startImageId,
        endImage: endImageId,
        async: true
    });

    return await submit(apiToken, urlVideos, body, index, text);
}

// Function to download videos
async function download(apiToken) {
    if (! await fileExists(RESULTS_FILE)) return;

    try {
        const resultsContent = await fs.readFile(RESULTS_FILE, 'utf8');
        const lines = resultsContent.trim().split('\n');

        for (const line of lines) {
            const [jobId, prompt] = line.split(',');

            console.log(`👉 ${jobId}`);

            while (true) {
                const response = await fetch(`${urlJobs}${jobId}`, {
                    headers: {
                        'Accept': 'application/json',
                        'Authorization': `Bearer ${apiToken}`
                    }
                });

                if (!response.ok) {
                    console.log(`🛑 Poll failed ${jobId} (HTTP ${response.status}):\n${prompt}\n`, await response.text());
                    break;
                }

                const jobBody = await response.json();
                const { status, error, response: jobResponse } = jobBody;

                if (status == 'failed') {
                    console.error(`🛑 FAILED ${jobId} (${error}):\n${prompt}\n`);
                    break;
                }

                if (status == 'completed') {
                    const media = jobResponse?.media ?? [];

                    if (media.length == 0)
                        console.error(`🛑 Completed but no media for ${jobId}:\n${prompt}\n`);

                    // A single prompt with count > 1 returns multiple videos.
                    for (let i = 0; i < media.length; i++) {
                        const url = media[i]?.videoUrl;
                        const videoFilename = `${jobId.replace(/[:*]/g, '_')}_${i + 1}.mp4`;

                        try {
                            await fs.access(videoFilename);
                            console.log(`⚠️ ${videoFilename} already exists. Skipping download.`);
                            continue;
                        } catch {
                            // File does not exist, proceed with downloading
                        }

                        if (url) {
                            console.log(`✅ Downloading ${url} to ${videoFilename}`);
                            try {
                                const videoResponse = await fetch(url);
                                if (!videoResponse.ok) {
                                    console.error(`⛔ Unable to download ${jobId} (HTTP ${videoResponse.status}):\n${prompt}\n`, url);
                                    continue;
                                }
                                const stream = Readable.fromWeb(videoResponse.body);
                                await writeFile(videoFilename, stream);
                            } catch (err) {
                                console.error(`⛔ Error during download: ${err}`);
                            }
                        } else
                            console.error(`🛑 No videoUrl for ${jobId} media #${i + 1}:\n${prompt}\n`);
                    }

                    break;
                }

                console.log(`⌛ ${jobId} status (${status}) and is still in progress, waiting…`);
                await sleep(SLEEP_POLL);
            }
        }
    } catch (error) {
        console.log(`⛔ Error during download:`, error.stack || error);
    }
}

// Main function
async function main() {
    const apiToken = process.argv[2];
    const email = process.argv[3];
    const promptFile = process.argv[4] || DEFAULT_PROMPTS_FILE;

    if (!apiToken || !email) {
        console.error('Usage: node google-flow.mjs <API_TOKEN> <EMAIL> [PROMPTS_FILE]');
        process.exit(1);
    }

    console.info('Script v1.0');

    console.info('Node version is: ' + process.version);

    try {
        if (await fileExists(RESULTS_FILE)) {
            let user_input;
            while (!['y', 'n'].includes(user_input)) {
                user_input = (await promptUser(`❔ ${RESULTS_FILE} file detected. Do you want to download the results now? (y/n): `))?.toLowerCase();
                if (user_input == 'y') {
                    await download(apiToken);
                    await fs.unlink(RESULTS_FILE);
                }
            }
        }

        const start = new Date();
        try {
            console.info('START EXECUTION', start);
            await execute(apiToken, email, promptFile); // Pass the promptFile to execute function
        }
        finally {
            console.info('COMPLETED', new Date());
            console.info('EXECUTION ELAPSED', diffInMinutesAndSeconds(start, new Date()));
        }

        try {
            console.info('START DOWNLOAD', start);
            await download(apiToken);
        }
        finally {
            console.info('TOTAL ELAPSED', diffInMinutesAndSeconds(start, new Date()));
        }
    } catch (error) {
        console.error('⛔ Error during execution:', error.stack || error);
    }
}

// Modify the execute function to accept promptFile as a parameter
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

    // Parameters accepted by this script for the POST /videos endpoint.
    // See https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos for every model's full parameter set.
    const supportedParams = ['model', 'prompt', 'startImage', 'endImage', 'aspectRatio', 'duration', 'count', 'seed'];

    const invalidKeys = (prompt) => Object.keys(prompt).filter(key => !key.startsWith('__') && !supportedParams.includes(key))

    for (let i = 1; i <= prompts.length; i++) {
        const prompt = prompts[i - 1];
        const { prompt: text, startImage, endImage } = prompt;

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

        if (endImage && !startImage)
            warnings.push(`⚠️  endImage requires startImage (end-frame-only is not supported). Prompt ${i}`);

        await Promise.all([validateImage(startImage), validateImage(endImage)]);
    }

    if (warnings.length > 0) {
        warnings.forEach(warning => console.warn(warning));
        console.error(`⛔ Execution stopped due to warnings.`);
        process.exit(1);
    }

    for (let i = 0; i < prompts.length; i++) {
        const prompt = prompts[i];
        while (true) {
            const responseCode = await submitVideo(apiToken, email, prompt, i + 1);
            if (responseCode == 429 || responseCode == 503)
                await sleep(SLEEP_429);
            else
                if (responseCode == 402) {
                    process.exit(1);
                } else
                    break;
        }
    }
}

// Utility function to check if a file exists
async function fileExists(path) {
    try {
        await fs.access(path);
        return true;
    } catch {
        return false;
    }
}

// Function to prompt user input
async function promptUser(query) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    return new Promise((resolve) => rl.question(query, answer => {
        rl.close();
        resolve(answer);
    }));
}

function diffInMinutesAndSeconds(date1, date2) {
    const diffInSeconds = Math.floor((date2 - date1) / 1000);
    return `${Math.floor(diffInSeconds / 60)} minutes ${diffInSeconds % 60} seconds`;
};

main();
