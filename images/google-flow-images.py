"""

Script version 1.0, June 15, 2026

Script to batch-generate images using prompts with the Google Flow API v1 by useapi.net 🚀
Uses the synchronous POST /images endpoint (default model: imagen-4) and downloads each fifeUrl.
For more details visit https://useapi.net/docs/api-google-flow-v1/post-google-flow-images

Installation Instructions:
==========================

You need Python 3.x installed to run this script. Download and install Python from:

- Windows, macOS, Linux: https://www.python.org/

After installation, verify by running the following command in a terminal:

   python3 --version

Running the Script:
===================

Usage: python3 google-flow-images.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]

Replace API_TOKEN with your actual useapi.net API token, see https://useapi.net/docs/start-here/setup-useapi
Replace EMAIL with configured Google Flow email account, see https://useapi.net/docs/start-here/setup-google-flow
If optional PROMPTS_FILE not provided prompts.json will be used.

Example:
--------

python3 google-flow-images.py user:1234-abcdefhijklmnopqrstuv my@email.com

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
ERRORS_FILE = 'google-flow-images_errors.txt'
DEFAULT_PROMPTS_FILE = 'prompts.json'
DEFAULT_MODEL = 'imagen-4'
SLEEP_429 = 30  # in seconds

urlAccounts = 'https://api.useapi.net/v1/google-flow/accounts'
urlImages = 'https://api.useapi.net/v1/google-flow/images'
urlUploadAsset = 'https://api.useapi.net/v1/google-flow/assets/'

# Google Flow accepts png, jpeg and webp for reference images.
supportedFileExtensions = ['png', 'jpeg', 'webp']

# reference_1 .. reference_10 are accepted by POST /images.
referenceParams = [f'reference_{i + 1}' for i in range(10)]

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
    return 'image/png' if ext == 'png' else 'image/webp' if ext == 'webp' else 'image/jpeg'


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


# Download a single image from its signed fifeUrl.
def downloadImage(url, filename):
    if os.path.exists(filename):
        print(f'⚠️ {filename} already exists. Skipping download.')
        return

    if not url:
        print(f'🛑 No fifeUrl for {filename}', file=sys.stderr)
        return

    print(f'✅ Downloading {url} to {filename}')
    try:
        status, data = http_download(url)
        if not (200 <= status < 300):
            print(f'⛔ Unable to download {filename} (HTTP {status})', url, file=sys.stderr)
            return
        with open(filename, 'wb') as f:
            f.write(data)
    except Exception as err:
        print(f'⛔ Error during download: {err}', file=sys.stderr)


# Submit a single prompt to the synchronous POST /images endpoint and download the results.
def submitImage(apiToken, email, prompt, index):
    model = prompt.get('model')
    text = prompt.get('prompt')

    useModel = model if model is not None else DEFAULT_MODEL

    print(f'🚀 {useModel} » Prompt #{index} • account {email} …')

    # Build the request body, uploading any local reference_* file to a mediaGenerationId first.
    body = {'model': useModel, 'email': email, 'prompt': text}

    for key in ['aspectRatio', 'count', 'seed']:
        if prompt.get(key) is not None:
            body[key] = prompt[key]

    for refKey in referenceParams:
        value = prompt.get(refKey)
        if value:
            body[refKey] = uploadAsset(apiToken, email, value)

    while True:
        status, responseText = http_request(urlImages, method='POST', headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {apiToken}'
        }, data=json.dumps(body).encode('utf-8'))

        if status == 200:
            jsonBody = json.loads(responseText)
            media = (jsonBody or {}).get('media') or []

            if len(media) == 0:
                print(f'🛑 200 OK but no media for prompt #{index}:\n{text}\n', file=sys.stderr)

            # count > 1 returns multiple images in the media array.
            for i in range(len(media)):
                img = ((media[i] or {}).get('image') or {}).get('generatedImage')
                filename = f'google-flow_{index}_{i + 1}.jpg'
                downloadImage((img or {}).get('fifeUrl'), filename)
            return 200

        if status == 429:
            print(f'🔄️ Retry on HTTP {status}', responseText)
            sleep(SLEEP_429)
        elif status == 503:
            print(f'🔄️ Service unavailable, retry on HTTP {status}', responseText)
            sleep(SLEEP_429)
        elif status == 402:
            print('🛑 No subscription / insufficient credits', responseText)
            appendFile(ERRORS_FILE, f'{status},#{index}:{text}\n')
            sys.exit(1)
        elif status == 400 or status == 500:
            print('🛑 Rejected (validation or content moderation)', responseText)
            appendFile(ERRORS_FILE, f'{status},#{index}:{text}\n')
            return status
        else:
            print(f'❗ FAILED with HTTP {status}', responseText)
            appendFile(ERRORS_FILE, f'{status},#{index}:{text}\n')
            return status


# Main function
def main():
    apiToken = sys.argv[2] if len(sys.argv) > 2 else None
    email = sys.argv[3] if len(sys.argv) > 3 else None
    promptFile = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_PROMPTS_FILE

    if not apiToken or not email:
        print('Usage: python3 google-flow-images.py <API_TOKEN> <EMAIL> [PROMPTS_FILE]', file=sys.stderr)
        sys.exit(1)

    print('Script v1.0')
    print('Python version is: ' + sys.version)

    start = datetime.now()
    try:
        print('START EXECUTION', start)
        execute(apiToken, email, promptFile)
    except SystemExit:
        raise
    except Exception as error:
        print('⛔ Error during execution:', error, file=sys.stderr)
    finally:
        print('COMPLETED', datetime.now())
        print('EXECUTION ELAPSED', diffInMinutesAndSeconds(start, datetime.now()))


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

    # Parameters accepted by this script for the POST /images endpoint.
    # See https://useapi.net/docs/api-google-flow-v1/post-google-flow-images for every model's full parameter set.
    supportedParams = ['model', 'prompt', 'aspectRatio', 'count', 'seed'] + referenceParams

    def invalidKeys(prompt):
        return [key for key in prompt.keys() if not key.startswith('__') and key not in supportedParams]

    for i in range(1, len(prompts) + 1):
        prompt = prompts[i - 1]
        text = prompt.get('prompt')

        def validateImage(file):
            if file:
                if not os.path.exists(file):
                    warnings.append(f"⚠️  Image '{file}' does not exist. Prompt {i}")

                ext = file.split('.').pop()

                if ext not in supportedFileExtensions:
                    warnings.append(f'⚠️  Image {file} extension {ext} not supported. Prompt {i}')

        notSupported = invalidKeys(prompt)
        if len(notSupported):
            warnings.append(f"⚠️  Following params not supported: {','.join(notSupported)}. Prompt {i}")

        if not text:
            warnings.append(f'⚠️  prompt is required. Prompt {i}')

        for refKey in referenceParams:
            validateImage(prompt.get(refKey))

    if len(warnings) > 0:
        for warning in warnings:
            print(warning, file=sys.stderr)
        print('⛔ Execution stopped due to warnings.', file=sys.stderr)
        sys.exit(1)

    for i in range(len(prompts)):
        submitImage(apiToken, email, prompts[i], i + 1)


def diffInMinutesAndSeconds(date1, date2):
    diffInSeconds = int((date2 - date1).total_seconds())
    return f'{diffInSeconds // 60} minutes {diffInSeconds % 60} seconds'


main()
