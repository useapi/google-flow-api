#!/usr/bin/env python3
"""
Make one long Omni 1.2 Flash video with the Google Flow API by useapi.net: generate the first clip, then extend it step by step.

1. POST /videos with the story's first prompt (model omni-flash-1.2, 3 to 15 seconds).
2. POST /videos/extend for every entry in `extensions`: each adds 3 to 10 seconds to the clip before it, with its own prompt
   and optional voices (referenceAudio_1..3), reference images (referenceImage_1..3, local files uploaded for you) and
   characters (character_1..3). Each answer is ONE clip, the whole video so far plus the new seconds.
3. Every step's job is saved as step-N.json and its MP4 as step-N.mp4. The last one is the finished video.

Google Flow extends videos shorter than 30 seconds, so the last extension can start from at most 29 seconds.
Extend needs a paid Google AI plan (Plus, Pro or Ultra).

Usage: python3 omni-extend.py <API_TOKEN> <EMAIL> [STORY_FILE]
       STORY_FILE defaults to story.json

Docs: https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-extend
Walkthrough: https://useapi.net/blog/261106
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get('USEAPI_BASE', 'https://api.useapi.net/v1/google-flow')
POLL_SECONDS = 10
REFERENCE_KEYS = ['referenceImage_1', 'referenceImage_2', 'referenceImage_3']
EXTEND_KEYS = ['duration', 'resolution', 'count', 'seed', *REFERENCE_KEYS,
               'character_1', 'character_2', 'character_3', 'referenceAudio_1', 'referenceAudio_2', 'referenceAudio_3']


def api(token, method, url, body=None, content_type='application/json'):
    data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
    headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'omni-extend.py'}
    if data is not None:
        headers['Content-Type'] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            text = res.read().decode(errors='replace')
            try:
                return res.status, json.loads(text or '{}')
            except ValueError:
                return res.status, {'error': text}
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors='replace')
        try:
            return e.code, json.loads(text)
        except ValueError:
            return e.code, {'error': text}


def resolve_image(token, email, ref):
    """A local image file → its mediaGenerationId on this account (POST /assets/{email}); anything else is passed as-is."""
    if not ref or ref.startswith('user:'):
        return ref
    ext = os.path.splitext(ref)[1].lower()
    content_type = 'image/png' if ext == '.png' else 'image/webp' if ext == '.webp' else 'image/jpeg'
    with open(ref, 'rb') as f:
        status, body = api(token, 'POST', f'{BASE}/assets/{urllib.parse.quote(email)}', f.read(), content_type)
    media_id = (body.get('mediaGenerationId') or {}).get('mediaGenerationId')
    if not media_id:
        raise RuntimeError(f'upload of {ref} failed (HTTP {status}): {body}')
    print(f'📤 uploaded {ref}')
    return media_id


def run(token, url, body, step):
    """Submit in async mode, then poll GET /jobs/{jobid} until the job completes or fails."""
    status, answer = api(token, 'POST', url, {**body, 'async': True})
    if status not in (200, 201):
        raise RuntimeError(f'step {step}: HTTP {status} {answer}')
    jobid = answer['jobid']
    print(f'⏳ step {step}: job {jobid}')
    while True:
        time.sleep(POLL_SECONDS)
        status, job = api(token, 'GET', f'{BASE}/jobs/{jobid}')
        if status == 429 or status >= 500:
            continue
        if status != 200:
            raise RuntimeError(f'step {step}: GET /jobs answered HTTP {status} {job}')
        if job.get('status') == 'completed':
            return job
        if job.get('status') == 'failed':
            raise RuntimeError(f"step {step} failed: {job.get('error') or (job.get('response') or {}).get('error') or job}")


def save(job, step):
    with open(f'step-{step}.json', 'w') as f:
        json.dump(job, f, indent=2)
    media = job['response']['media'][0]
    req = urllib.request.Request(media['videoUrl'], headers={'User-Agent': 'omni-extend.py'})
    with urllib.request.urlopen(req) as res, open(f'step-{step}.mp4', 'wb') as f:
        f.write(res.read())
    length = media.get('video', {}).get('dimensions', {}).get('length')
    print(f"✅ step {step}: step-{step}.mp4, {length}, {job['response'].get('remainingCredits')} credits left")
    return media['mediaGenerationId']


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 omni-extend.py <API_TOKEN> <EMAIL> [STORY_FILE]', file=sys.stderr)
        sys.exit(1)
    token, email = sys.argv[1], sys.argv[2]
    story_file = sys.argv[3] if len(sys.argv) > 3 else 'story.json'
    with open(story_file, encoding='utf-8') as f:
        story = json.load(f)
    extensions = story.pop('extensions', [])

    source = save(run(token, f'{BASE}/videos', {**story, 'email': email}, 1), 1)
    for i, ext in enumerate(extensions):
        body = {'prompt': ext.get('prompt'), 'mediaGenerationId': source}
        body.update({k: ext[k] for k in EXTEND_KEYS if k in ext})
        for key in REFERENCE_KEYS:
            if body.get(key):
                body[key] = resolve_image(token, email, body[key])
        source = save(run(token, f'{BASE}/videos/extend', body, i + 2), i + 2)
    print(f'🎬 done: step-{len(extensions) + 1}.mp4 is the whole video')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'🛑 {e}', file=sys.stderr)
        sys.exit(1)
