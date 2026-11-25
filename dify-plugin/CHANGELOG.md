# Changelog

## 0.1.0 (2026-11-24)

First release.

- 20 tools for the useapi.net Google Flow API: accounts and jobs, Generate video (Veo 3.1 Lite, Omni 1.2 Flash, Veo 3.1 Lite Lower Priority), Extend video, Upscale video (720p, 1080p, 4K), Generate image (Nano Banana 2 Lite, Nano Banana 2.1, Nano Banana Pro), Upscale image, Video to GIF, Join videos, uploads, media, characters, voices, and the Google Flow agent (chat, read a chat, answer approvals, list chats).
- Several Google accounts: with the email left empty, useapi.net spreads new jobs across the healthy accounts. A default email in the credentials pins every tool to one account.
- Image and video references take a media id or a Dify file; files are uploaded to the account the other references belong to.
- Video tools submit the job and wait up to 120 seconds by default (up to 420 in workflows), under Dify's 600-second limit; a job still running returns its `jobid` for Get job status.
- Results come back as readable text, JSON, workflow variables (`jobid`, `status`, `media_ids`, `file_urls`, `chat_id`, `reply`) and files.
- Only models Google keeps after 2026-12-05 are offered.
- Interface in English, Simplified Chinese, Japanese and Brazilian Portuguese.
