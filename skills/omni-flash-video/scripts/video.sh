#!/usr/bin/env bash
# Everything in one command: upload local files, generate, wait, download. Prints the saved .mp4 paths.
# Usage: video.sh "<prompt>" [key=value ...]
#   Any value that is an existing local file (for referenceImage_N, startImage, endImage or
#   referenceVideo_1) is uploaded first and replaced by its asset id. Other options as in generate.sh.
# Example: video.sh "The woman in @referenceImage_1 holds up the mug and says: 'Best coffee I've had.'" \
#            referenceImage_1=./presenter.jpg referenceAudio_1=Kore aspectRatio=portrait duration=6
# OUT_DIR sets the folder (default: the current one). If the run is interrupted after the job id was
# logged, resume with: wait-job.sh <jobid> > job.json && download.sh job.json
DIR="$(dirname "$0")"
source "$DIR/_common.sh"
PROMPT="${1:?Usage: video.sh \"<prompt>\" [key=value ...]}"
shift

ARGS=()
for KV in "$@"; do
  K="${KV%%=*}"
  V="${KV#*=}"
  if [ "$K" != "$KV" ] && [ -f "$V" ]; then
    ID=$("$DIR/upload.sh" "$V")
    # Keep every upload on the same Google account as the first one, or the generation is rejected
    if [ -z "${USEAPI_EMAIL:-}" ]; then
      USEAPI_EMAIL=$(asset_email "$ID")
      export USEAPI_EMAIL
    fi
    KV="$K=$ID"
  fi
  ARGS+=("$KV")
done

JOBID=$("$DIR/generate.sh" "$PROMPT" ${ARGS[@]+"${ARGS[@]}"})
JOB=$("$DIR/wait-job.sh" "$JOBID")
"$DIR/download.sh" - "${OUT_DIR:-.}" <<< "$JOB"
