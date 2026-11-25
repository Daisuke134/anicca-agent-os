#!/bin/bash
# post-video-to-tiktok.sh — Upload video to Postiz and post to TikTok
#
# Usage: ./post-video-to-tiktok.sh --video <path> --caption "text" --title "text" \
#        --integration <id> --privacy <level> --posting-method <method>
#
# Requires: POSTIZ_API_KEY env var (NO Bearer prefix)

set -euo pipefail

VIDEO=""
CAPTION=""
TITLE=""
INTEGRATION=""
PRIVACY="PUBLIC_TO_EVERYONE"
METHOD="DIRECT_POST"

while [[ $# -gt 0 ]]; do
  case $1 in
    --video) VIDEO="$2"; shift 2 ;;
    --caption) CAPTION="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --integration) INTEGRATION="$2"; shift 2 ;;
    --privacy) PRIVACY="$2"; shift 2 ;;
    --posting-method) METHOD="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO" || -z "$CAPTION" || -z "$INTEGRATION" ]]; then
  echo "Usage: $0 --video <path> --caption 'text' --integration <id> [--title 'text'] [--privacy SELF_ONLY] [--posting-method UPLOAD]"
  exit 1
fi

if [[ -z "${POSTIZ_API_KEY:-}" ]]; then
  echo "ERROR: POSTIZ_API_KEY not set"
  exit 1
fi

# Dais 2026-06-07 Spec Part L: read warmup_phase from postiz-integrations.json
# warmup → MEDIA_UPLOAD (draft) for 7d → anicca-warmup-flip-daily flips to live → DIRECT_POST
REGISTRY="$HOME/.openclaw/state/postiz-integrations.json"
if [[ -f "$REGISTRY" ]]; then
  PHASE=$(python3 -c "
import json, sys
d = json.load(open('$REGISTRY'))
hit = next((i for i in d.get('integrations',[]) if i.get('id') == '$INTEGRATION'), None)
print(hit.get('warmup_phase','live') if hit else 'live')
" 2>/dev/null || echo "live")
  if [[ "$PHASE" == "warmup" ]]; then
    METHOD="UPLOAD"
    echo "📡 integration $INTEGRATION phase=warmup → posting as DRAFT (UPLOAD)"
  else
    echo "📡 integration $INTEGRATION phase=$PHASE → posting DIRECT_POST"
  fi
fi

BASE_URL="https://api.postiz.com/public/v1"

# Step 1: Upload video to Postiz
echo "📤 Uploading video to Postiz..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload" \
  -H "Authorization: ${POSTIZ_API_KEY}" \
  -F "file=@${VIDEO};filename=$(basename ${VIDEO});type=video/mp4")

UPLOAD_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
UPLOAD_PATH=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('path',''))" 2>/dev/null || echo "")

if [[ -z "$UPLOAD_ID" || -z "$UPLOAD_PATH" ]]; then
  echo "❌ Upload failed: $UPLOAD_RESPONSE"
  exit 1
fi

echo "✅ Uploaded: id=$UPLOAD_ID"

# Step 2: Create TikTok post
echo "📱 Creating TikTok post (privacy=$PRIVACY, method=$METHOD)..."
# Build payload via env-var → python (avoids breaking when CAPTION/TITLE contain newlines/quotes)
NOW_UTC=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
PAYLOAD=$(NOW_UTC="$NOW_UTC" INTEGRATION="$INTEGRATION" CAPTION="$CAPTION" TITLE="$TITLE" \
          UPLOAD_ID="$UPLOAD_ID" UPLOAD_PATH="$UPLOAD_PATH" PRIVACY="$PRIVACY" METHOD="$METHOD" \
          python3 -c "
import json, os
data = {
    'type': 'now',
    'date': os.environ['NOW_UTC'],
    'shortLink': False,
    'tags': [],
    'posts': [{
        'integration': {'id': os.environ['INTEGRATION']},
        'value': [{
            'content': os.environ['CAPTION'],
            'image': [{'id': os.environ['UPLOAD_ID'], 'path': os.environ['UPLOAD_PATH']}]
        }],
        'settings': {
            '__type': 'tiktok',
            'title': os.environ['TITLE'],
            'privacy_level': os.environ['PRIVACY'],
            'duet': False,
            'stitch': False,
            'comment': True,
            'autoAddMusic': 'yes',
            'brand_content_toggle': False,
            'brand_organic_toggle': False,
            'video_made_with_ai': True,
            'content_posting_method': os.environ['METHOD']
        }
    }]
}
print(json.dumps(data))")
POST_RESPONSE=$(curl -s -X POST "$BASE_URL/posts" \
  -H "Authorization: ${POSTIZ_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "Response: $POST_RESPONSE"

POST_ID=$(echo "$POST_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('postId','') if isinstance(d,list) and d else d.get('id',''))" 2>/dev/null || echo "")

if [[ -n "$POST_ID" ]]; then
  echo "✅ Posted! PostID: $POST_ID"
  # Save meta
  META_DIR=$(dirname "$VIDEO")
  cat > "$META_DIR/reel-meta.json" << METAEOF
{
  "postId": "$POST_ID",
  "privacy": "$PRIVACY",
  "method": "$METHOD",
  "integration": "$INTEGRATION",
  "postedAt": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
}
METAEOF
  echo "📋 Metadata saved to $META_DIR/reel-meta.json"
else
  echo "❌ TikTok post failed. No postId returned."
  exit 1
fi
