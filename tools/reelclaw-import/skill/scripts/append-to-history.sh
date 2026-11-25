#!/usr/bin/env bash
# append-to-history.sh — orchestrators call this AFTER a successful post.
# Updates ~/.openclaw/state/content-library/account-history.jsonl so the
# next propose-from-library run enforces 14d anti-repeat per account.
#
# Usage: append-to-history.sh --account <handle> --platform <TT|IG|YT> \
#                             --post-id <postId> --source-id <pattern source_id> \
#                             --hook <text> --emotion <e> [--posted-at <iso>]

set -uo pipefail
HISTORY="$HOME/.openclaw/state/content-library/account-history.jsonl"
ACCOUNT=""; PLATFORM=""; POST_ID=""; SOURCE_ID=""; HOOK=""; EMOTION=""; POSTED_AT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --account) ACCOUNT="$2"; shift 2 ;;
    --platform) PLATFORM="$2"; shift 2 ;;
    --post-id) POST_ID="$2"; shift 2 ;;
    --source-id) SOURCE_ID="$2"; shift 2 ;;
    --hook) HOOK="$2"; shift 2 ;;
    --emotion) EMOTION="$2"; shift 2 ;;
    --posted-at) POSTED_AT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done
[[ -n "$ACCOUNT" && -n "$PLATFORM" && -n "$POST_ID" && -n "$SOURCE_ID" ]] || {
  echo "FATAL: required --account --platform --post-id --source-id" >&2; exit 2; }
[[ -z "$POSTED_AT" ]] && POSTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)

ACCOUNT="$ACCOUNT" PLATFORM="$PLATFORM" POST_ID="$POST_ID" SOURCE_ID="$SOURCE_ID" \
HOOK="$HOOK" EMOTION="$EMOTION" POSTED_AT="$POSTED_AT" \
python3 - <<'PY' >> "$HISTORY"
import json, os
print(json.dumps({
    "account":   os.environ["ACCOUNT"],
    "platform":  os.environ["PLATFORM"],
    "post_id":   os.environ["POST_ID"],
    "source_id": os.environ["SOURCE_ID"],
    "hook":      os.environ["HOOK"],
    "emotion":   os.environ["EMOTION"],
    "posted_at": os.environ["POSTED_AT"],
    "views_6h":  None, "views_24h": None, "views_48h": None,
    "killed_at": None,
}, ensure_ascii=False))
PY
echo "appended to account-history.jsonl: $ACCOUNT/$PLATFORM/$POST_ID source=$SOURCE_ID"
