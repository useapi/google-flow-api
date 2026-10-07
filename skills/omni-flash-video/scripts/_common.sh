# Shared helpers for the omni-flash-video skill scripts. Sourced, not run.
# Needs: curl, jq. Env: USEAPI_TOKEN (required), USEAPI_EMAIL (optional, which connected Google Flow account to use).
# Written for bash 3.2 and later (the macOS default), so no bash 4 features.
set -euo pipefail

API="${USEAPI_API:-https://api.useapi.net/v1/google-flow}"
: "${USEAPI_TOKEN:?Set USEAPI_TOKEN to your useapi.net API token (https://useapi.net/docs/start-here/setup-useapi)}"
command -v jq > /dev/null || { echo "jq is required (https://jqlang.org/download/)" >&2; exit 1; }

enc() { jq -rn --arg v "$1" '$v|@uri'; }
log() { echo "$(date +%H:%M:%S) $*" >&2; }

# acurl [curl args ...] -> curl with the Authorization header read from stdin (-H @-),
# so the token does not show up in the process list
acurl() { curl "$@" -H @- <<< "Authorization: Bearer $USEAPI_TOKEN"; }

# _call METHOD PATH [JSON_BODY] -> sets CODE (the HTTP status, 000 on a network error) and OUT (a temp file with the body)
_call() {
  local method="$1" path="$2" body="${3:-}"
  OUT=$(mktemp)
  if [ -n "$body" ]; then
    CODE=$(acurl -sS --max-time 320 -o "$OUT" -w '%{http_code}' -H "Content-Type: application/json" -X "$method" "$API/$path" -d "$body") || true
  else
    CODE=$(acurl -sS --max-time 320 -o "$OUT" -w '%{http_code}' -X "$method" "$API/$path") || true
  fi
  CODE="${CODE:-000}"
}

# hint CODE BODY_FILE -> one line on what to do about a failed request (stderr)
hint() {
  local code="$1" body
  body=$(cat "$2" 2>/dev/null || true)
  case "$code" in
    400)
      if grep -q 'SAFETY\|safety\|policy' <<< "$body"; then
        echo "Hint: Google refused the content. Rephrase the prompt or change the reference images. Video-to-video moderation is not deterministic, so one plain resubmit can also clear it." >&2
      else
        echo "Hint: a parameter was rejected. The error names it; see https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos" >&2
      fi ;;
    401) echo "Hint: the API token is wrong or missing. Check USEAPI_TOKEN." >&2 ;;
    402) echo "Hint: the Google account has no active Google AI plan or is out of Flow credits. Omni Flash needs Plus, Pro or Ultra." >&2 ;;
    403)
      if grep -q 'MODEL_ACCESS_DENIED' <<< "$body"; then
        echo "Hint: Google refused this model on this account. Check that the account's plan includes it." >&2
      else
        echo "Hint: Google rejected the captcha on every try. Wait a minute and try once more; if it keeps happening, see https://useapi.net/docs/api-google-flow-v1/get-google-flow-accounts-captcha-stats" >&2
      fi ;;
    404) echo "Hint: that Google Flow account is not connected. Check USEAPI_EMAIL, or see https://useapi.net/docs/start-here/setup-google-flow" >&2 ;;
    429) echo "Hint: the account is busy or out of quota. retryAfter in the error says when to try again; or leave USEAPI_EMAIL unset so the API picks another account. Do not loop on it." >&2 ;;
    503) echo "Hint: Google is temporarily unavailable or overloaded. Try again in a minute or two (fewer reference images or a lower count also help)." >&2 ;;
    596) echo "Hint: the Google account needs to be reconnected: https://useapi.net/docs/start-here/setup-google-flow" >&2 ;;
  esac
}

# _finish METHOD PATH -> prints the body of a 2xx answer; anything else prints the error, a hint, and exits 1
_finish() {
  if [ "${CODE:0:1}" != "2" ]; then
    echo "$1 /$2 -> HTTP $CODE: $(cat "$OUT")" >&2
    hint "$CODE" "$OUT"
    rm -f "$OUT"
    exit 1
  fi
  cat "$OUT"
  rm -f "$OUT"
}

# api METHOD PATH [JSON_BODY] -> response body on stdout; a non-2xx answer prints the error and exits 1
api() {
  _call "$@"
  _finish "$1" "$2"
}

# api_poll METHOD PATH -> like api, for the polling loop: a network error or an HTTP 5xx is retried
# up to 3 times, 10 s apart (except 596, which means the Google account needs reconnecting)
api_poll() {
  local try=1
  while true; do
    _call "$@"
    case "$CODE" in
      000|5??)
        if [ "$CODE" != 596 ] && [ "$try" -le 3 ]; then
          log "$1 /$2 -> HTTP $CODE, retry $try of 3 in 10 s"
          rm -f "$OUT"
          try=$((try + 1))
          sleep 10
          continue
        fi ;;
    esac
    break
  done
  _finish "$1" "$2"
}

# asset_email MEDIA_GENERATION_ID -> the Google account an uploaded asset belongs to
# (the id embeds it hex-encoded: user:123-email:<hex>-image:...)
asset_email() {
  local hex
  hex=$(sed -n 's/.*-email:\([0-9a-fA-F]*\)-.*/\1/p' <<< "$1")
  [ -n "$hex" ] || return 0
  printf "$(sed 's/../\\x&/g' <<< "$hex")"
}
