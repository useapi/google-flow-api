"""

Script version 1.0, June 15, 2026

Script to batch-generate audio-native videos with Gemini Omni Flash using the Google Flow API v1 by useapi.net 🚀
Uses the POST /videos endpoint in async mode (model: omni-flash) and polls GET /jobs/{jobId}.
For more details visit https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos

Installation Instructions:
==========================

You need Python 3.x installed to run this script. Download and install Python from:

- Windows, macOS, Linux: https://www.python.org/

After installation, verify by running the following command in a terminal:

   python3 --version

Running the Script:
===================

Usage: python3 omni-flash.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

python3 omni-flash.py user:1234-abcdefhijklmnopqrstuv my@email.com

This command executes the script using API token user:1234-abcdefhijklmnopqrstuv with my@email.com Google Flow account email.

Changelog:
==========

- June 15, 2026: Initial release.

"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime


# Constants
RESULTS_FILE = 'omni-flash_results.txt'
ERRORS_FILE = 'omni-flash_errors.txt'
DEFAULT_PROMPTS_FILE = 'prompts.json'
MODEL = 'omni-flash'
SLEEP_429 = 30  # in seconds
SLEEP_POLL = 15  # in seconds

urlAccounts = 'https://api.useapi.net/v1/google-flow/accounts'
urlVideos = 'https://api.useapi.net/v1/google-flow/videos'
urlJobs = 'https://api.useapi.net/v1/google-flow/jobs/'
urlUploadAsset = 'https://api.useapi.net/v1/google-flow/assets/'

# Google Flow accepts png, jpeg and webp images, and mp4 video (for omni-flash V2V edit).
supportedImageExtensions = ['png', 'jpeg', 'webp']
supportedVideoExtensions = ['mp4']

# { filename: mediaGenerationId }
uploadedFiles = {}


# Utility to sleep for given seconds
def sleep(seconds):
    time.sleep(seconds)


def now_ms():
    return time.time() * 1000


# Perform an HTTP request and return (status, body_text). Network/HTTP errors
# are surfaced as their HTTP status (mirroring fetch which does not throw on 4xx/5xx).
def http_request(url, method='GET', headers=None, data=None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return e.code, body


# Download binary content from a (signed) URL; returns (status, bytes).
def http_download(url):
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, b''


def appendFile(path, text):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(text)


# Function to fetch configured Google Flow API accounts
def fetchAccounts(apiToken):
    status, body = http_request(urlAccounts, method='GET', headers={
        'Accept': 'application/json',
        'Authorization': f'Bearer {apiToken}'
    })

    if not (200 <= status < 300):
        print(f'⛔ Error fetching accounts (HTTP {status}): {body}', file=sys.stderr)
        sys.exit(1)

    return json.loads(body)


def elapsedTimeSec(start):
    return (now_ms() - start) / 1000


# Map a file extension to the Content-Type required by POST /assets
def contentTypeForExt(ext):
    if ext == 'png':
        return 'image/png'
    if ext == 'webp':
        return 'image/webp'
    if ext == 'mp4':
        return 'video/mp4'
    return 'image/jpeg'


def uploadAsset(apiToken, email, filename):

    # Check if already uploaded
    if filename in uploadedFiles:
        return uploadedFiles[filename]

    startTime = now_ms()

    print(f'⬆️  Account {email} uploading file…', filename)

    with open(filename, 'rb') as f:
        body = f.read()

    fileExt = filename.split('.').pop()

    status, responseText = http_request(
        f'{urlUploadAsset}{urllib.parse.quote(email, safe="")}',
        method='POST',
        headers={
            'Accept': 'application/json',
            'Authorization': f'Bearer {apiToken}',
            'Content-Type': contentTypeForExt(fileExt)
        },
        data=body
    )

    if 200 <= status < 300:
        jsonBody = json.loads(responseText)
        # POST /assets returns the reference id nested as mediaGenerationId.mediaGenerationId
        mediaGenerationId = (jsonBody or {}).get('mediaGenerationId', {})
        mediaGenerationId = mediaGenerationId.get('mediaGenerationId') if isinstance(mediaGenerationId, dict) else None
        print(f'🆗 mediaGenerationId ({elapsedTimeSec(startTime)} sec)', mediaGenerationId)
        uploadedFiles[filename] = mediaGenerationId
    else:
        print(f'❗ Unable to upload file HTTP {status} ({elapsedTimeSec(startTime)} sec)', responseText, file=sys.stderr)
        # Do not attempt to upload failed file again
        uploadedFiles[filename] = None

    return uploadedFiles[filename]


def submit(apiToken, url, body, index, prompt):
    createStatus, createBody = http_request(url, method='POST', headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {apiToken}'
    }, data=body.encode('utf-8'))

    # Async POST /videos returns 201 Created with a jobid to poll.
    if createStatus == 201:
        jsonBody = json.loads(createBody)
        # 201 async payload uses lowercase "jobid"; sync 200 uses "jobId". Accept either.
        jobId = jsonBody.get('jobid') if jsonBody.get('jobid') is not None else jsonBody.get('jobId')
        if jobId:
            appendFile(RESULTS_FILE, f'{jobId},#{index}:{prompt}\n')
            print('✅ jobId', jobId)
            return 201
        else:
            error = 'No jobid found in HTTP 201 response'
            print(f'❓ {error}', createBody)
            appendFile(ERRORS_FILE, f'{error},#{index}:{prompt}\n')
            return 500
    else:
        if createStatus == 429:
            print(f'🔄️ Retry on HTTP {createStatus}', createBody)
        elif createStatus == 503:
            print(f'🔄️ Service unavailable, retry on HTTP {createStatus}', createBody)
        elif createStatus == 400:
            print('🛑 Rejected request (validation or content policy)', createBody)
            appendFile(ERRORS_FILE, f'{createStatus},#{index}:{prompt}\n')
        elif createStatus == 402:
            print('🛑 No subscription / insufficient credits', createBody)
        else:
            print(f'❗ FAILED with HTTP {createStatus}', createBody)
            appendFile(ERRORS_FILE, f'{createStatus},#{index}:{prompt}\n')
        return createStatus


# Build a JSON body that omits keys whose value is None, mirroring JSON.stringify
# which drops keys set to undefined.
def jsonStringify(obj):
    return json.dumps({k: v for k, v in obj.items() if v is not None})


# Submit a single prompt to POST /videos with model omni-flash in async mode.
# referenceImage_1..7 = R2V image refs; referenceVideo_1 = V2V edit (no duration);
# referenceAudio_1..5 = system voice name or POST /voices user-voice id.
def submitVideo(apiToken, email, prompt, index):
    text = prompt.get('prompt')
    aspectRatio = prompt.get('aspectRatio')
    duration = prompt.get('duration')
    count = prompt.get('count')
    seed = prompt.get('seed')
    referenceImage_1 = prompt.get('referenceImage_1')
    referenceImage_2 = prompt.get('referenceImage_2')
    referenceImage_3 = prompt.get('referenceImage_3')
    referenceImage_4 = prompt.get('referenceImage_4')
    referenceImage_5 = prompt.get('referenceImage_5')
    referenceImage_6 = prompt.get('referenceImage_6')
    referenceImage_7 = prompt.get('referenceImage_7')
    referenceVideo_1 = prompt.get('referenceVideo_1')
    startFrameIndex_1 = prompt.get('startFrameIndex_1')
    endFrameIndex_1 = prompt.get('endFrameIndex_1')
    referenceAudio_1 = prompt.get('referenceAudio_1')
    referenceAudio_2 = prompt.get('referenceAudio_2')
    referenceAudio_3 = prompt.get('referenceAudio_3')
    referenceAudio_4 = prompt.get('referenceAudio_4')
    referenceAudio_5 = prompt.get('referenceAudio_5')

    print(f'🚀 {MODEL} » Prompt #{index} • account {email} …')

    # Upload any local image/video files and swap the paths for their mediaGenerationId.
    def resolveRef(ref):
        if ref and (ref.startswith('./') or ('.' in ref)) \
                and (ref.split('.').pop() in supportedImageExtensions or ref.split('.').pop() in supportedVideoExtensions):
            return uploadAsset(apiToken, email, ref)
        return ref

    refImage_1 = resolveRef(referenceImage_1)
    refImage_2 = resolveRef(referenceImage_2)
    refImage_3 = resolveRef(referenceImage_3)
    refImage_4 = resolveRef(referenceImage_4)
    refImage_5 = resolveRef(referenceImage_5)
    refImage_6 = resolveRef(referenceImage_6)
    refImage_7 = resolveRef(referenceImage_7)
    refVideo_1 = resolveRef(referenceVideo_1)

    # V2V edit does not accept duration — output matches the trim window.
    isV2V = bool(refVideo_1)

    body = jsonStringify({
        'model': MODEL,
        'email': email,
        'prompt': text,
        'aspectRatio': aspectRatio,
        'duration': None if isV2V else duration,
        'count': count,
        'seed': seed,
        'referenceImage_1': refImage_1,
        'referenceImage_2': refImage_2,
        'referenceImage_3': refImage_3,
        'referenceImage_4': refImage_4,
        'referenceImage_5': refImage_5,
        'referenceImage_6': refImage_6,
        'referenceImage_7': refImage_7,
        'referenceVideo_1': refVideo_1,
        'startFrameIndex_1': startFrameIndex_1,
        'endFrameIndex_1': endFrameIndex_1,
        'referenceAudio_1': referenceAudio_1,
        'referenceAudio_2': referenceAudio_2,
        'referenceAudio_3': referenceAudio_3,
        'referenceAudio_4': referenceAudio_4,
        'referenceAudio_5': referenceAudio_5,
        'async': True
    })

    return submit(apiToken, urlVideos, body, index, text)


# Function to download videos
def download(apiToken):
    if not fileExists(RESULTS_FILE):
        return

    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            resultsContent = f.read()
        lines = resultsContent.strip().split('\n')

        for line in lines:
            parts = line.split(',')
            jobId = parts[0]
            prompt = parts[1] if len(parts) > 1 else None

            print(f'👉 {jobId}')

            while True:
                status, responseText = http_request(f'{urlJobs}{jobId}', method='GET', headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {apiToken}'
                })

                if not (200 <= status < 300):
                    print(f'🛑 Poll failed {jobId} (HTTP {status}):\n{prompt}\n', responseText)
                    break

                jobBody = json.loads(responseText)
                jobStatus = jobBody.get('status')
                error = jobBody.get('error')
                jobResponse = jobBody.get('response')

                if jobStatus == 'failed':
                    print(f'🛑 FAILED {jobId} ({error}):\n{prompt}\n', file=sys.stderr)
                    break

                if jobStatus == 'completed':
                    media = (jobResponse or {}).get('media') or []

                    if len(media) == 0:
                        print(f'🛑 Completed but no media for {jobId}:\n{prompt}\n', file=sys.stderr)

                    # A single prompt with count > 1 returns multiple videos.
                    for i in range(len(media)):
                        url = (media[i] or {}).get('videoUrl')
                        videoFilename = f"{jobId.replace(':', '_').replace('*', '_')}_{i + 1}.mp4"

                        if os.path.exists(videoFilename):
                            print(f'⚠️ {videoFilename} already exists. Skipping download.')
                            continue

                        if url:
                            print(f'✅ Downloading {url} to {videoFilename}')
                            try:
                                videoStatus, videoData = http_download(url)
                                if not (200 <= videoStatus < 300):
                                    print(f'⛔ Unable to download {jobId} (HTTP {videoStatus}):\n{prompt}\n', url, file=sys.stderr)
                                    continue
                                with open(videoFilename, 'wb') as vf:
                                    vf.write(videoData)
                            except Exception as err:
                                print(f'⛔ Error during download: {err}', file=sys.stderr)
                        else:
                            print(f'🛑 No videoUrl for {jobId} media #{i + 1}:\n{prompt}\n', file=sys.stderr)

                    break

                print(f'⌛ {jobId} status ({jobStatus}) and is still in progress, waiting…')
                sleep(SLEEP_POLL)
    except Exception as error:
        print('⛔ Error during download:', error)


# Main function
def main():
    apiToken = sys.argv[2] if len(sys.argv) > 2 else None
    email = sys.argv[3] if len(sys.argv) > 3 else None
    promptFile = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_PROMPTS_FILE

    if not apiToken or not email:
        print('Usage: python3 omni-flash.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]', file=sys.stderr)
        sys.exit(1)

    print('Script v1.0')

    print('Python version is: ' + sys.version)

    try:
        if fileExists(RESULTS_FILE):
            user_input = None
            while user_input not in ['y', 'n']:
                answer = promptUser(f'❔ {RESULTS_FILE} file detected. Do you want to download the results now? (y/n): ')
                user_input = answer.lower() if answer else None
                if user_input == 'y':
                    download(apiToken)
                    os.unlink(RESULTS_FILE)

        start = datetime.now()
        try:
            print('START EXECUTION', start)
            execute(apiToken, email, promptFile)  # Pass the promptFile to execute function
        finally:
            print('COMPLETED', datetime.now())
            print('EXECUTION ELAPSED', diffInMinutesAndSeconds(start, datetime.now()))

        try:
            print('START DOWNLOAD', start)
            download(apiToken)
        finally:
            print('TOTAL ELAPSED', diffInMinutesAndSeconds(start, datetime.now()))
    except Exception as error:
        print('⛔ Error during execution:', error, file=sys.stderr)


# Modify the execute function to accept promptFile as a parameter
def execute(apiToken, email, promptFile):
    accounts = fetchAccounts(apiToken)

    print(f'Configured Google Flow API accounts ({len(accounts.keys())}):', ', '.join(accounts.keys()))

    if len(accounts.keys()) <= 0:
        print('⛔ No configured Google Flow accounts found. Please refer to https://useapi.net/docs/start-here/setup-google-flow', file=sys.stderr)
        sys.exit(1)

    if not accounts.get(email):
        print(f'⛔ Account {email} not found. Please refer to https://useapi.net/docs/start-here/setup-google-flow', file=sys.stderr)
        sys.exit(1)

    if accounts[email].get('health') and accounts[email].get('health') != 'OK':
        print(f"⛔ Account {email} health is '{accounts[email].get('health')}'. Please resolve and update the account, see https://useapi.net/docs/start-here/setup-google-flow", file=sys.stderr)
        sys.exit(1)

    with open(promptFile, 'r', encoding='utf-8') as f:
        promptData = f.read()
    prompts = json.loads(promptData)
    print('Total number of prompts to process', len(prompts))

    warnings = []

    # Parameters accepted by this script for the omni-flash POST /videos endpoint.
    # See https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos for the full parameter set.
    supportedParams = [
        'prompt', 'aspectRatio', 'duration', 'count', 'seed',
        'referenceImage_1', 'referenceImage_2', 'referenceImage_3', 'referenceImage_4',
        'referenceImage_5', 'referenceImage_6', 'referenceImage_7',
        'referenceVideo_1', 'startFrameIndex_1', 'endFrameIndex_1',
        'referenceAudio_1', 'referenceAudio_2', 'referenceAudio_3', 'referenceAudio_4', 'referenceAudio_5'
    ]

    imageRefKeys = ['referenceImage_1', 'referenceImage_2', 'referenceImage_3', 'referenceImage_4', 'referenceImage_5', 'referenceImage_6', 'referenceImage_7']

    def invalidKeys(prompt):
        return [key for key in prompt.keys() if not key.startswith('__') and key not in supportedParams]

    # Validate a local file path reference (skip already-uploaded mediaGenerationId strings).
    def looksLikePath(ref):
        return ref and (ref.startswith('./') or ('.' in ref and not ref.startswith('user:')))

    for i in range(1, len(prompts) + 1):
        prompt = prompts[i - 1]
        text = prompt.get('prompt')
        referenceVideo_1 = prompt.get('referenceVideo_1')
        duration = prompt.get('duration')

        def validateFile(file, allowedExts):
            if looksLikePath(file):
                if not os.path.exists(file):
                    warnings.append(f"⚠️  File '{file}' does not exist. Prompt {i}")

                ext = file.split('.').pop()

                if ext not in allowedExts:
                    warnings.append(f'⚠️  File {file} extension {ext} not supported. Prompt {i}')

        notSupported = invalidKeys(prompt)
        if len(notSupported):
            warnings.append(f"⚠️  Following params not supported: {','.join(notSupported)}. Prompt {i}")

        if not text:
            warnings.append(f'⚠️  prompt is required. Prompt {i}')

        # V2V edit (referenceVideo_1) does not accept duration — output matches the trim window.
        if referenceVideo_1 and duration:
            warnings.append(f'⚠️  duration is not accepted with referenceVideo_1 (V2V edit). Prompt {i}')

        validateFile(referenceVideo_1, supportedVideoExtensions)
        for k in imageRefKeys:
            validateFile(prompt.get(k), supportedImageExtensions)

    if len(warnings) > 0:
        for warning in warnings:
            print(warning, file=sys.stderr)
        print('⛔ Execution stopped due to warnings.', file=sys.stderr)
        sys.exit(1)

    for i in range(len(prompts)):
        prompt = prompts[i]
        while True:
            responseCode = submitVideo(apiToken, email, prompt, i + 1)
            if responseCode == 429 or responseCode == 503:
                sleep(SLEEP_429)
            else:
                if responseCode == 402:
                    sys.exit(1)
                else:
                    break


# Utility function to check if a file exists
def fileExists(path):
    return os.path.exists(path)


# Function to prompt user input
def promptUser(query):
    try:
        return input(query)
    except EOFError:
        return None


def diffInMinutesAndSeconds(date1, date2):
    diffInSeconds = int((date2 - date1).total_seconds())
    return f'{diffInSeconds // 60} minutes {diffInSeconds % 60} seconds'


main()
