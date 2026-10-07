#!/usr/bin/env bash
# Start one video generation and print its job id. It does not wait; use wait-job.sh.
# Usage: generate.sh "<prompt>" [key=value ...]
#   model=omni-flash (default) | veo-3.1-fast | veo-3.1-quality | veo-3.1-lite
#   aspectRatio=landscape (default) | portrait     duration=4|6|8|10 (default 8)
#   resolution=720p (default) | 360p (omni-flash only, about half the credits)
#   count=1..4  seed=<int>  referenceImage_1..7=<asset id>  startImage=<asset id>  endImage=<asset id>
#   character_1..7=<character id>  referenceAudio_1..5=<voice name or voice id>
#   referenceVideo_1=<asset id> startFrameIndex_1=<0-239> endFrameIndex_1=<1-240>
# Every option: https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos
# This spends Flow credits. It never retries by itself: a retry after an unclear failure could pay twice.
source "$(dirname "$0")/_common.sh"
PROMPT="${1:?Usage: generate.sh \"<prompt>\" [key=value ...]}"
shift

BODY=$(jq -n --arg p "$PROMPT" '{prompt: $p, model: "omni-flash", async: true}')
if [ -n "${USEAPI_EMAIL:-}" ]; then BODY=$(jq --arg e "$USEAPI_EMAIL" '.email = $e' <<< "$BODY"); fi
for KV in "$@"; do
  case "$KV" in *=*) ;; *) echo "Expected key=value, got: $KV" >&2; exit 1 ;; esac
  K="${KV%%=*}"
  V="${KV#*=}"
  case "$K" in
    duration|count|seed|startFrameIndex_1|endFrameIndex_1) BODY=$(jq --arg k "$K" --argjson v "$V" '.[$k] = $v' <<< "$BODY") ;;
    *) BODY=$(jq --arg k "$K" --arg v "$V" '.[$k] = $v' <<< "$BODY") ;;
  esac
done

JOB=$(api POST videos "$BODY")
ID=$(jq -r '.jobid // empty' <<< "$JOB")
[ -n "$ID" ] || { echo "No job id in the answer: $JOB" >&2; exit 1; }
log "job $ID"
echo "$ID"
