#!/usr/bin/env bash
# Download every video of a finished job and print the saved paths.
# Usage: download.sh <job.json|-> [OUT_DIR]
# The video links are signed Google URLs that stay valid for about 6 hours.
source "$(dirname "$0")/_common.sh"
JOB=$(cat "${1:--}")
OUT="${2:-.}"
mkdir -p "$OUT"

SHORT=$(jq -r '(.jobid // "") | (capture("^j(?<id>[0-9]+)").id // "")' <<< "$JOB")
NAME="omni-flash${SHORT:+_$SHORT}"
N=0
for URL in $(jq -r '.response.media[]?.videoUrl // empty' <<< "$JOB"); do
  N=$((N + 1))
  FILE="$OUT/${NAME}_$N.mp4"
  curl -sS --fail --max-time 600 -o "$FILE" "$URL"
  echo "$FILE"
done
[ "$N" -gt 0 ] || { echo "The job has no video URLs: $(jq -c '{status, error}' <<< "$JOB")" >&2; exit 1; }
