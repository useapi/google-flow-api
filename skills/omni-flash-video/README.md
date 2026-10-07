# Omni 1.1 Flash video: an agent skill

An [Agent Skill](https://agentskills.io) that lets Claude Code, Codex and other coding agents make AI video with Google's **Omni 1.1 Flash** (Gemini Omni Flash, audio-native: spoken dialogue, preset voices, reference images of people and products, video-to-video edits) or **Veo 3.1**, and download the `.mp4`. Ask your agent "make a 6-second portrait clip of the woman in presenter.jpg holding up our mug and saying it's the best coffee she's had" and it runs the scripts in this folder.

It calls the [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=github.com&utm_medium=skill&utm_campaign=omni-flash-skill) by [useapi.net](https://useapi.net/?utm_source=github.com&utm_medium=skill&utm_campaign=omni-flash-skill), a third-party REST API that runs on your own Google Flow account. Each clip spends Flow credits from your Google AI plan.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills) (asks which agents to install for):

```bash
npx skills add useapi/google-flow-api --skill omni-flash-video
# add -g to install for your user instead of the current project
```

Or copy the folder yourself:

```bash
git clone https://github.com/useapi/google-flow-api.git
cp -r google-flow-api/skills/omni-flash-video ~/.claude/skills/     # Claude Code, every project
cp -r google-flow-api/skills/omni-flash-video .claude/skills/       # Claude Code, this project only
cp -r google-flow-api/skills/omni-flash-video ~/.codex/skills/      # Codex
```

Then give the agent your token in the environment it runs in:

```bash
export USEAPI_TOKEN=user:12345-...      # your useapi.net API token
export USEAPI_EMAIL=you@gmail.com       # optional: which connected Google account to use
```

You need:

1. A useapi.net [API token](https://useapi.net/docs/start-here/setup-useapi?utm_source=github.com&utm_medium=skill&utm_campaign=omni-flash-skill). One [$15/month subscription](https://useapi.net/docs/subscription?utm_source=github.com&utm_medium=skill&utm_campaign=omni-flash-skill) covers every useapi.net API.
2. A Google account with a Google AI Plus, Pro or Ultra plan, connected with the [Google Flow setup](https://useapi.net/docs/start-here/setup-google-flow?utm_source=github.com&utm_medium=skill&utm_campaign=omni-flash-skill). An 8-second 720p Omni clip costs 12 Flow credits, a 360p draft about half.
3. `bash`, `curl` and [`jq`](https://jqlang.org/download/).

## Use it without an agent

The scripts work on their own too:

```bash
./scripts/video.sh "The woman in @referenceImage_1 holds up the mug and says: 'Best coffee I've had all year.'" \
  referenceImage_1=./presenter.jpg referenceAudio_1=Kore aspectRatio=portrait duration=6
```

| Script | What it does |
|---|---|
| `scripts/video.sh` | Everything below in one command: prompt and local files in, `.mp4` out |
| `scripts/upload.sh` | Upload an image (PNG, JPEG, WebP) or video (MP4), print its asset id |
| `scripts/generate.sh` | Start a generation, print the job id |
| `scripts/wait-job.sh` | Poll the job until it is done, print the final record |
| `scripts/download.sh` | Download the finished `.mp4` file(s) |

[`SKILL.md`](./SKILL.md) is what the agent reads: the options, credit costs, prompting rules that work with Omni, and what to do on each error. The full API reference is at [useapi.net/docs/api-google-flow-v1](https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos?utm_source=github.com&utm_medium=skill&utm_campaign=omni-flash-skill).
