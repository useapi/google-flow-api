#!/usr/bin/env bash
# Upload a local image (PNG, JPEG, WebP) or video (MP4) and print its asset id (mediaGenerationId).
# Usage: upload.sh <file>
# The asset belongs to one Google account: USEAPI_EMAIL if set, otherwise the one the API picks.
# Use the id as referenceImage_N, startImage, endImage or referenceVideo_1 in generate.sh.
source "$(dirname "$0")/_common.sh"
FILE="${1:?Usage: upload.sh <file>}"
[ -f "$FILE" ] || { echo "No such file: $FILE" >&2; exit 1; }

EXT=$(tr '[:upper:]' '[:lower:]' <<< "${FILE##*.}")
case "$EXT" in
  png) TYPE=image/png ;;
  jpg|jpeg) TYPE=image/jpeg ;;
  webp) TYPE=image/webp ;;
  mp4) TYPE=video/mp4 ;;
  *) echo "Unsupported file type .$EXT (use png, jpg, jpeg, webp or mp4)" >&2; exit 1 ;;
esac

P="assets"
if [ -n "${USEAPI_EMAIL:-}" ]; then P="assets/$(enc "$USEAPI_EMAIL")"; fi
OUT=$(mktemp)
CODE=$(acurl -sS --max-time 320 -o "$OUT" -w '%{http_code}' -X POST -H "Content-Type: $TYPE" --data-binary "@$FILE" "$API/$P") || true
CODE="${CODE:-000}"
BODY=$(_finish POST "$P")
ID=$(jq -r '.mediaGenerationId.mediaGenerationId // empty' <<< "$BODY")
[ -n "$ID" ] || { echo "Upload answered without an asset id: $BODY" >&2; exit 1; }
log "uploaded $FILE"
echo "$ID"
