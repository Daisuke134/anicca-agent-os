#!/bin/bash
# post-video-to-instagram.sh — Upload BGM video to Postiz and post to Instagram (instagram-standalone)
#
# Usage: ./post-video-to-instagram.sh --video <path> --caption "text" --integration <id>
#        [--upload-id <existing-id> --upload-path <existing-path>] (reuse already-uploaded video)
#
# Requires: POSTIZ_API_KEY env var (NO Bearer prefix)
#
# Prints to stdout (one line per kv) so caller can capture:
#   IG_UPLOAD_ID=cm...
#   IG_POST_ID=cm...
#   IG_STATE=PUBLISHED|ERROR|QUEUE
#   IG_URL=https://www.instagram.com/...
# Exit !=0 if any step fails.

set -uo pipefail

VIDEO=""
CAPTION=""
INTEGRATION=""
UPLOAD_ID=""
UPLOAD_PATH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --video) VIDEO="$2"; shift 2 ;;
    --caption) CAPTION="$2"; shift 2 ;;
    --integration) INTEGRATION="$2"; shift 2 ;;
    --upload-id) UPLOAD_ID="$2"; shift 2 ;;
    --upload-path) UPLOAD_PATH="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$CAPTION" || -z "$INTEGRATION" ]]; then
  echo "Usage: $0 --video <path> --caption 'text' --integration <id>"; exit 1
fi
if [[ -z "$UPLOAD_ID" && -z "$VIDEO" ]]; then
  echo "Need either --video or --upload-id/--upload-path"; exit 1
fi
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not set}"

BASE_URL="https://api.postiz.com/public/v1"

# Step 1: Upload video to Postiz (skip if --upload-id passed)
if [[ -z "$UPLOAD_ID" ]]; then
  [[ -f "$VIDEO" ]] || { echo "FATAL: video not found: $VIDEO"; exit 2; }
  echo "📤 IG: Uploading $(basename "$VIDEO")..." >&2
  UPLOAD_RESPONSE=$(curl -sS -X POST "$BASE_URL/upload" \
    -H "Authorization: ${POSTIZ_API_KEY}" \
    -F "file=@${VIDEO};filename=$(basename "${VIDEO}");type=video/mp4")
  UPLOAD_ID=$(printf '%s' "$UPLOAD_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
  UPLOAD_PATH=$(printf '%s' "$UPLOAD_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('path',''))" 2>/dev/null || echo "")
  if [[ -z "$UPLOAD_ID" ]]; then
    echo "FATAL: IG upload failed. Response: $UPLOAD_RESPONSE"; exit 3
  fi
fi
echo "IG_UPLOAD_ID=$UPLOAD_ID"

# Step 2: POST to Postiz (instagram-standalone, post_type "post" — IG auto-treats vertical as Reel)
NOW_UTC=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
PAYLOAD=$(python3 -c "
import json,os
data={
  'type':'now',
  'date':os.environ['NOW_UTC'],
  'shortLink':False,
  'tags':[],
  'posts':[{
    'integration':{'id':os.environ['INTEGRATION']},
    'value':[{
      'content':os.environ['CAPTION'],
      'image':[{'id':os.environ['UPLOAD_ID'],'path':os.environ['UPLOAD_PATH']}]
    }],
    'settings':{'__type':'instagram-standalone','post_type':'post'}
  }]
}
print(json.dumps(data))
" 2>/dev/null) \
  NOW_UTC="$NOW_UTC" INTEGRATION="$INTEGRATION" CAPTION="$CAPTION" UPLOAD_ID="$UPLOAD_ID" UPLOAD_PATH="$UPLOAD_PATH"
PAYLOAD=$(NOW_UTC="$NOW_UTC" INTEGRATION="$INTEGRATION" CAPTION="$CAPTION" UPLOAD_ID="$UPLOAD_ID" UPLOAD_PATH="$UPLOAD_PATH" python3 -c "
import json,os
data={
  'type':'now',
  'date':os.environ['NOW_UTC'],
  'shortLink':False,
  'tags':[],
  'posts':[{
    'integration':{'id':os.environ['INTEGRATION']},
    'value':[{
      'content':os.environ['CAPTION'],
      'image':[{'id':os.environ['UPLOAD_ID'],'path':os.environ['UPLOAD_PATH']}]
    }],
    'settings':{'__type':'instagram-standalone','post_type':'post'}
  }]
}
print(json.dumps(data))")
echo "📤 IG: POST to integration $INTEGRATION ..." >&2
RESP=$(curl -sS -X POST "$BASE_URL/posts" \
  -H "Authorization: ${POSTIZ_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")
POST_ID=$(printf '%s' "$RESP" | python3 -c "import sys,json
d=json.load(sys.stdin)
if isinstance(d,list) and d: print(d[0].get('postId') or d[0].get('id') or '')
else: print(d.get('id','') if isinstance(d,dict) else '')" 2>/dev/null || echo "")
if [[ -z "$POST_ID" ]]; then
  echo "FATAL: IG POST failed. Response: $RESP" >&2
  exit 4
fi
echo "IG_POST_ID=$POST_ID"

# Step 3: poll state up to ~90s
S=$(date -u -v-1d +%Y-%m-%dT00:00:00); E=$(date -u -v+1d +%Y-%m-%dT00:00:00)
STATE="QUEUE"; URL=""
for i in 1 2 3 4 5 6 7 8 9; do
  sleep 10
  CHK=$(curl -sS "$BASE_URL/posts?startDate=$S&endDate=$E&display=all" -H "Authorization: $POSTIZ_API_KEY" \
        | python3 -c "
import sys,json,os
d=json.load(sys.stdin); arr=d if isinstance(d,list) else d.get('posts',[])
pid=os.environ['POST_ID']
for p in arr:
  if p.get('id')==pid:
    print((p.get('state') or '') + '|' + (p.get('releaseURL') or ''))
    break" POST_ID="$POST_ID" 2>/dev/null)
  STATE=$(printf '%s' "$CHK" | cut -d'|' -f1)
  URL=$(printf '%s' "$CHK" | cut -d'|' -f2-)
  [[ "$STATE" == "PUBLISHED" || "$STATE" == "ERROR" ]] && break
done
echo "IG_STATE=${STATE:-UNKNOWN}"
echo "IG_URL=${URL:-}"
[[ "$STATE" == "PUBLISHED" ]] || exit 5
