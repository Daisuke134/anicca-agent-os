#!/bin/bash
# post-video-to-youtube.sh — Upload BGM video to Postiz and post to YouTube Short
#
# Usage: ./post-video-to-youtube.sh --video <path> --title "FIXED CTA" --caption "hashtags only" \
#        --integration <id> [--upload-id <id> --upload-path <path>]
#
# Requires: POSTIZ_API_KEY env var (NO Bearer prefix)
#
# Prints (stdout):
#   YT_UPLOAD_ID=cm...
#   YT_POST_ID=cm...
#   YT_STATE=PUBLISHED|ERROR|QUEUE
#   YT_URL=https://www.youtube.com/watch?v=...
# Exit !=0 on failure.

set -uo pipefail

VIDEO=""; TITLE=""; CAPTION=""; INTEGRATION=""; UPLOAD_ID=""; UPLOAD_PATH=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --video) VIDEO="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --caption) CAPTION="$2"; shift 2 ;;
    --integration) INTEGRATION="$2"; shift 2 ;;
    --upload-id) UPLOAD_ID="$2"; shift 2 ;;
    --upload-path) UPLOAD_PATH="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done
if [[ -z "$TITLE" || -z "$INTEGRATION" ]]; then
  echo "Usage: $0 --video <path> --title 'FIXED CTA' --caption 'hashtags' --integration <id>"; exit 1
fi
if [[ -z "$UPLOAD_ID" && -z "$VIDEO" ]]; then
  echo "Need --video or --upload-id/--upload-path"; exit 1
fi
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not set}"
BASE_URL="https://api.postiz.com/public/v1"

# Step 1: upload if needed
if [[ -z "$UPLOAD_ID" ]]; then
  [[ -f "$VIDEO" ]] || { echo "FATAL: video not found: $VIDEO"; exit 2; }
  echo "📤 YT: Uploading $(basename "$VIDEO")..." >&2
  UR=$(curl -sS --connect-timeout 20 --max-time 180 -X POST "$BASE_URL/upload" \
    -H "Authorization: ${POSTIZ_API_KEY}" \
    -F "file=@${VIDEO};filename=$(basename "${VIDEO}");type=video/mp4")
  UPLOAD_ID=$(printf '%s' "$UR" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
  UPLOAD_PATH=$(printf '%s' "$UR" | python3 -c "import sys,json; print(json.load(sys.stdin).get('path',''))" 2>/dev/null || echo "")
  [[ -n "$UPLOAD_ID" ]] || { echo "FATAL: YT upload failed. Response: $UR"; exit 3; }
fi
echo "YT_UPLOAD_ID=$UPLOAD_ID"

# Step 2: POST to Postiz (youtube settings with selfDeclaredMadeForKids=no)
NOW_UTC=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
PAYLOAD=$(NOW_UTC="$NOW_UTC" INTEGRATION="$INTEGRATION" CAPTION="$CAPTION" TITLE="$TITLE" UPLOAD_ID="$UPLOAD_ID" UPLOAD_PATH="$UPLOAD_PATH" python3 -c "
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
    'settings':{'__type':'youtube','title':os.environ['TITLE'],'selfDeclaredMadeForKids':'no','type':'public'}
  }]
}
print(json.dumps(data))")
echo "📤 YT: POST to integration $INTEGRATION ..." >&2
RESP=$(curl -sS --connect-timeout 15 --max-time 30 -X POST "$BASE_URL/posts" \
  -H "Authorization: ${POSTIZ_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")
POST_ID=$(printf '%s' "$RESP" | python3 -c "import sys,json
d=json.load(sys.stdin)
if isinstance(d,list) and d: print(d[0].get('postId') or d[0].get('id') or '')
else: print(d.get('id','') if isinstance(d,dict) else '')" 2>/dev/null || echo "")
if [[ -z "$POST_ID" ]]; then
  echo "FATAL: YT POST failed. Response: $RESP" >&2
  exit 4
fi
echo "YT_POST_ID=$POST_ID"

# Step 3: poll state (YT Postiz processing typically takes 120-240s; allow up to 360s)
S=$(date -u -v-1d +%Y-%m-%dT00:00:00); E=$(date -u -v+1d +%Y-%m-%dT00:00:00)
STATE="QUEUE"; URL=""
for i in $(seq 1 18); do
  sleep 10
  CHK=$(POST_ID="$POST_ID" curl -sS --connect-timeout 10 --max-time 20 "$BASE_URL/posts?startDate=$S&endDate=$E&display=all" -H "Authorization: $POSTIZ_API_KEY" \
        | python3 -c "
import sys,json,os
d=json.load(sys.stdin); arr=d if isinstance(d,list) else d.get('posts',[])
pid=os.environ['POST_ID']
for p in arr:
  if p.get('id')==pid:
    print((p.get('state') or '') + '|' + (p.get('releaseURL') or ''))
    break" 2>/dev/null)
  STATE=$(printf '%s' "$CHK" | cut -d'|' -f1)
  URL=$(printf '%s' "$CHK" | cut -d'|' -f2-)
  [[ "$STATE" == "PUBLISHED" || "$STATE" == "ERROR" ]] && break
done
echo "YT_STATE=${STATE:-UNKNOWN}"
echo "YT_URL=${URL:-}"
[[ "$STATE" == "ERROR" ]] && exit 5 || exit 0  # QUEUE=submitted=success (YT transcode is async)
