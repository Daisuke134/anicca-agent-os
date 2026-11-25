#!/bin/bash
# create-ugc-reel.sh — Full ReelClaw pipeline using mcporter + DanSUGC
#
# Usage: ./create-ugc-reel.sh --output-dir <dir> --hook-text <text> --emotion <emotion> --lang <en|ja>
#
# Pipeline:
#   1. mcporter call dansugc.search_videos → find UGC reaction clip
#   2. mcporter call dansugc.purchase_videos → buy + get download URL
#   3. curl download → trim to 5s hook clip (ffmpeg)
#   4. Generate demo segment from template images (2s each × 5 = 10s)
#   5. Concatenate hook(5s) + demo(10s) = 15s
#   6. Add text overlay via node-canvas (Larry's add-text-overlay.js on frames)
#   7. Output: reel-final.mp4 (1080x1920, ≤15s, H.264)
#
# Requires: mcporter, ffmpeg, node, POSTIZ_API_KEY env

set -euo pipefail

OUTPUT_DIR=""
HOOK_TEXT=""
EMOTION="sad"
LANG="ja"
TEMPLATE_DIR="$HOME/.openclaw/workspace/tiktok-marketing/assets/templates"
UGC_LIBRARY="$HOME/.openclaw/workspace/tiktok-marketing/ugc-library"
DEMO_VIDEO=""
DEMO_MODE="TRIM"

while [[ $# -gt 0 ]]; do
  case $1 in
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --hook-text) HOOK_TEXT="$2"; shift 2 ;;
    --emotion) EMOTION="$2"; shift 2 ;;
    --lang) LANG="$2"; shift 2 ;;
    --template-dir) TEMPLATE_DIR="$2"; shift 2 ;;
    --demo-video) DEMO_VIDEO="$2"; shift 2 ;;
    --demo-mode) DEMO_MODE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$OUTPUT_DIR" || -z "$HOOK_TEXT" ]]; then
  echo "Usage: $0 --output-dir <dir> --hook-text <text> [--emotion sad] [--lang ja] [--demo-video <path>] [--demo-mode NO_TRIM|TRIM]"
  exit 1
fi

mkdir -p "$OUTPUT_DIR/clips" "$UGC_LIBRARY"

FONT="$HOME/Library/Fonts/TikTokSansDisplayBold.ttf"

echo "🎬 ReelClaw Pipeline Start"
echo "  Emotion: $EMOTION"
echo "  Lang: $LANG"
echo "  Hook: ${HOOK_TEXT:0:50}..."

# ═══════════════════════════════════════════════════
# Step 1: Search UGC reaction clip via mcporter
# ═══════════════════════════════════════════════════
echo ""
echo "🔍 Step 1: Searching DanSUGC for $EMOTION reaction..."

SEARCH_RESULT=$(mcporter call dansugc.search_videos \
  semantic_search="$EMOTION reaction looking at phone" \
  emotion="$EMOTION" \
  min_virality=50 \
  limit=5 \
  --output json 2>&1)

# Extract first video ID from result
VIDEO_ID=$(echo "$SEARCH_RESULT" | python3 -c "
import sys, re
raw = sys.stdin.read()
ids = re.findall(r'\(([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\)', raw)
print(ids[0] if ids else '')
" 2>/dev/null)

if [[ -z "$VIDEO_ID" ]]; then
  echo "  ⚠️ No clips found for emotion=$EMOTION, trying broader search..."
  SEARCH_RESULT=$(mcporter call dansugc.search_videos \
    semantic_search="emotional reaction" \
    limit=5 \
    --output json 2>&1)
  VIDEO_ID=$(echo "$SEARCH_RESULT" | python3 -c "
import sys, re
raw = sys.stdin.read()
ids = re.findall(r'\(([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\)', raw)
print(ids[0] if ids else '')
" 2>/dev/null)
fi

if [[ -z "$VIDEO_ID" ]]; then
  echo "  ❌ No UGC clips found at all"
  exit 1
fi

echo "  ✅ Found: $VIDEO_ID"

# ═══════════════════════════════════════════════════
# Step 2: Check if already purchased, if not purchase
# ═══════════════════════════════════════════════════
UGC_FILE="$UGC_LIBRARY/${EMOTION}-${VIDEO_ID:0:8}.mp4"

if [[ -f "$UGC_FILE" ]]; then
  echo "  📁 Already downloaded: $UGC_FILE"
else
  echo ""
  echo "💰 Step 2: Purchasing clip..."
  PURCHASE_RESULT=$(mcporter call dansugc.purchase_videos \
    --args "{\"video_ids\":[\"$VIDEO_ID\"]}" \
    --output json 2>&1)

  # Extract download URL
  DOWNLOAD_URL=$(echo "$PURCHASE_RESULT" | python3 -c "
import sys, re
raw = sys.stdin.read()
urls = re.findall(r'Download: (https://[^\s\\\\\"]+)', raw)
url = urls[0].rstrip(\"'\").rstrip('\"') if urls else ''
print(url)
" 2>/dev/null)

  if [[ -z "$DOWNLOAD_URL" ]]; then
    # Might be already purchased - check purchases
    echo "  ⚠️ Purchase may have failed or already owned. Checking purchases..."
    PURCHASES=$(mcporter call dansugc.list_purchases limit=10 --output json 2>&1)
    DOWNLOAD_URL=$(echo "$PURCHASES" | python3 -c "
import sys, re
raw = sys.stdin.read()
urls = re.findall(r'Download: (https://[^\s\\\\\"]+)', raw)
url = urls[0].rstrip(\"'\").rstrip('\"') if urls else ''
print(url)
" 2>/dev/null)
  fi

  if [[ -z "$DOWNLOAD_URL" ]]; then
    echo "  ❌ Could not get download URL"
    exit 1
  fi

  echo "  📥 Downloading: $DOWNLOAD_URL"
  curl -L -s -o "$UGC_FILE" "$DOWNLOAD_URL"
  echo "  ✅ Downloaded: $(du -h "$UGC_FILE" | cut -f1)"
fi

# ═══════════════════════════════════════════════════
# Step 3: Trim UGC clip to 5s hook + center-crop to 1080x1920
# ═══════════════════════════════════════════════════
echo ""
echo "✂️ Step 3: Trimming hook clip to 5s..."

# Detect orientation
HOOK_W=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=width -of csv=p=0 "$UGC_FILE")
HOOK_H=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=height -of csv=p=0 "$UGC_FILE")

if [[ $HOOK_W -gt $HOOK_H ]]; then
  # Landscape → center crop to portrait
  VF="scale=-1:1920,crop=1080:1920,setsar=1,fps=30"
else
  # Portrait → scale + pad
  VF="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30"
fi

ffmpeg -y -hide_banner -loglevel error \
  -i "$UGC_FILE" -ss 1 -t 5 \
  -vf "$VF" -an \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
  "$OUTPUT_DIR/clips/hook.mp4"

echo "  ✅ Hook clip: 5s, 1080x1920"

# ═══════════════════════════════════════════════════
# Step 4: Create demo segment
# ═══════════════════════════════════════════════════
echo ""
if [[ "$DEMO_MODE" == "NO_TRIM" && -n "$DEMO_VIDEO" && -f "$DEMO_VIDEO" ]]; then
  echo "🖼️ Step 4: Using provided demo video AS-IS..."
  ffmpeg -y -hide_banner -loglevel error \
    -i "$DEMO_VIDEO" \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30" \
    -an \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
    "$OUTPUT_DIR/clips/demo.mp4"
  echo "  ✅ Demo segment: full source video kept untrimmed"
  echo "  ✅ NO_TRIM mode: preserve demo AS-IS, but allow normal skill hook trimming"
else
  echo "🖼️ Step 4: Creating demo segment from templates..."
  TEMPLATES=($(ls "$TEMPLATE_DIR"/*.png 2>/dev/null | sort))
  DEMO_CONCAT="$OUTPUT_DIR/clips/demo_concat.txt"
  > "$DEMO_CONCAT"

  for i in $(seq 0 4); do
    IMG="${TEMPLATES[$((i % ${#TEMPLATES[@]}))]}"
    DEMO_CLIP="$OUTPUT_DIR/clips/demo_${i}.mp4"
    
    ffmpeg -y -hide_banner -loglevel error \
      -loop 1 -i "$IMG" \
      -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z='min(zoom+0.001,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=60:s=1080x1920:fps=30" \
      -t 2 \
      -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
      "$DEMO_CLIP"
    
    echo "file 'demo_${i}.mp4'" >> "$DEMO_CONCAT"
  done

  ffmpeg -y -hide_banner -loglevel error \
    -f concat -safe 0 -i "$DEMO_CONCAT" \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
    "$OUTPUT_DIR/clips/demo.mp4"

  echo "  ✅ Demo segment: template fallback"
fi

# ═══════════════════════════════════════════════════
# Step 5: Concatenate hook + demo
# ═══════════════════════════════════════════════════
echo ""
echo "🔗 Step 5: Concatenating hook + demo..."

cat > "$OUTPUT_DIR/clips/final_concat.txt" << EOF
file 'hook.mp4'
file 'demo.mp4'
EOF

ffmpeg -y -hide_banner -loglevel error \
  -f concat -safe 0 -i "$OUTPUT_DIR/clips/final_concat.txt" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
  "$OUTPUT_DIR/reel-notext.mp4"

# ═══════════════════════════════════════════════════
# Step 6: Add BGM and finalize
# ═══════════════════════════════════════════════════
echo ""
echo "🎵 Step 6: Mixing BGM and finalizing..."

BGM="$HOME/.openclaw/workspace/tiktok-marketing/music/bgm-cta.mp3"
ffmpeg -y -hide_banner -loglevel error \
  -i "$OUTPUT_DIR/reel-notext.mp4" \
  -stream_loop -1 -i "$BGM" \
  -filter_complex "[1:a]volume=0.15[bgm]" \
  -map 0:v -map "[bgm]" \
  -c:v copy \
  -c:a aac -b:a 128k -shortest -movflags +faststart \
  "$OUTPUT_DIR/reel-final.mp4"

# ═══════════════════════════════════════════════════
# Step 7: Validate
# ═══════════════════════════════════════════════════
DURATION=$(ffprobe -v quiet -print_format json -show_entries format=duration "$OUTPUT_DIR/reel-final.mp4" | python3 -c "import sys,json; print(float(json.load(sys.stdin)['format']['duration']))")

echo ""
echo "═══════════════════════════════"
echo "✅ REEL COMPLETE"
echo "  File: $OUTPUT_DIR/reel-final.mp4"
echo "  Duration: ${DURATION}s"
echo "  Format: 1080x1920 H.264"
echo "  Hook: UGC $EMOTION reaction (5s)"
if [[ "$DEMO_MODE" == "NO_TRIM" ]]; then
  echo "  Demo: Full source video AS-IS"
else
  echo "  Demo: Template slideshow (10s)"
fi
echo "  CTA: script does not append CTA itself"
echo "  BGM: included"
echo "  UGC ID: $VIDEO_ID"
echo "═══════════════════════════════"

if [[ "$DEMO_MODE" == "NO_TRIM" ]]; then
  echo "✅ NO_TRIM mode active: skipping 15s enforcement"
elif (( $(echo "$DURATION > 15.5" | bc -l) )); then
  echo "⚠️ OVER 15s! Trimming..."
  ffmpeg -y -hide_banner -loglevel error \
    -i "$OUTPUT_DIR/reel-final.mp4" -t 15 \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
    "$OUTPUT_DIR/reel-trimmed.mp4"
  mv "$OUTPUT_DIR/reel-trimmed.mp4" "$OUTPUT_DIR/reel-final.mp4"
  echo "  ✅ Trimmed to 15s"
fi

# Save metadata
HOOK_TEXT_JSON=$(HOOK_TEXT="$HOOK_TEXT" python3 - <<'PY'
import json, os
print(json.dumps(os.environ["HOOK_TEXT"]))
PY
)

cat > "$OUTPUT_DIR/reel-meta.json" << METAEOF
{
  "ugcVideoId": "$VIDEO_ID",
  "ugcEmotion": "$EMOTION",
  "hookText": $HOOK_TEXT_JSON,
  "lang": "$LANG",
  "duration": $DURATION,
  "createdAt": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
}
METAEOF

echo "📋 Metadata saved"
