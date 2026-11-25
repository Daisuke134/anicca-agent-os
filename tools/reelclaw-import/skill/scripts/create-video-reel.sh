#!/bin/bash
# create-video-reel.sh — Create a 15-second video reel from template images + text overlay
# Uses Larry's add-text-overlay.js (node-canvas) for text, then ffmpeg zoompan for video
#
# Usage: ./create-video-reel.sh --output-dir <dir> --texts <texts.json> --template-dir <dir>
#
# texts.json format: ["slide 1 text", "slide 2 text", ..., "slide 6 text"]
# Each text entry can have \n for line breaks
#
# Output: <output-dir>/reel-final.mp4 (1080x1920, 15s, H.264)

set -euo pipefail

OUTPUT_DIR=""
TEXTS_FILE=""
TEMPLATE_DIR=""
LARRY_SCRIPTS="$HOME/.openclaw/workspace/skills/larry/scripts"

while [[ $# -gt 0 ]]; do
  case $1 in
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --texts) TEXTS_FILE="$2"; shift 2 ;;
    --template-dir) TEMPLATE_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$OUTPUT_DIR" || -z "$TEXTS_FILE" || -z "$TEMPLATE_DIR" ]]; then
  echo "Usage: $0 --output-dir <dir> --texts <texts.json> --template-dir <dir>"
  exit 1
fi

mkdir -p "$OUTPUT_DIR/clips"

# Step 1: Copy template images as slide1.png through slide6.png
echo "📋 Copying template images..."
TEMPLATES=($(ls "$TEMPLATE_DIR"/*.png 2>/dev/null | sort))
if [[ ${#TEMPLATES[@]} -lt 6 ]]; then
  echo "ERROR: Need at least 6 template images, found ${#TEMPLATES[@]}"
  exit 1
fi

for i in $(seq 0 5); do
  cp "${TEMPLATES[$i]}" "$OUTPUT_DIR/slide$((i+1)).png"
done
echo "  ✅ 6 slides copied"

# Step 2: Add text overlays using Larry's add-text-overlay.js (node-canvas)
echo "🎨 Adding text overlays..."
node "$LARRY_SCRIPTS/add-text-overlay.js" --input "$OUTPUT_DIR" --texts "$TEXTS_FILE"
echo "  ✅ Text overlays complete"

# Step 3: Find the output files (add-text-overlay.js creates slide1_final.png etc or overwrites)
# Check which naming convention was used
if [[ -f "$OUTPUT_DIR/slide1_final.png" ]]; then
  SLIDE_PATTERN="slide%d_final.png"
  echo "  Using _final.png files"
elif [[ -f "$OUTPUT_DIR/slide1.png" ]]; then
  SLIDE_PATTERN="slide%d.png"
  echo "  Using slide.png files (in-place)"
else
  echo "ERROR: No output slides found after text overlay"
  exit 1
fi

# Step 4: Create video clips from each image with zoompan (Ken Burns effect)
echo "🎬 Creating video clips..."
CONCAT_LIST="$OUTPUT_DIR/clips/concat.txt"
> "$CONCAT_LIST"

SLIDE_DURATION="2.5"
for i in $(seq 1 6); do
  SLIDE_FILE=$(printf "$OUTPUT_DIR/$SLIDE_PATTERN" $i)
  CLIP="$OUTPUT_DIR/clips/slide${i}.mp4"
  
  if [[ ! -f "$SLIDE_FILE" ]]; then
    echo "  ⚠️ Missing: $SLIDE_FILE"
    continue
  fi
  
  echo "  Slide $i → clip..."
  # Pad to 1080x1920 + zoompan for subtle movement
  ffmpeg -y -hide_banner -loglevel error \
    -loop 1 -i "$SLIDE_FILE" \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z='min(zoom+0.0012,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=75:s=1080x1920:fps=30" \
    -t "$SLIDE_DURATION" \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
    "$CLIP"
  
  echo "file 'slide${i}.mp4'" >> "$CONCAT_LIST"
done

# Step 5: Concatenate all clips
echo "🔗 Concatenating clips..."
ffmpeg -y -hide_banner -loglevel error \
  -f concat -safe 0 -i "$CONCAT_LIST" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart \
  "$OUTPUT_DIR/reel-final.mp4"

# Step 6: Validate duration
DURATION=$(ffprobe -v quiet -print_format json -show_entries format=duration "$OUTPUT_DIR/reel-final.mp4" | python3 -c "import sys,json; print(float(json.load(sys.stdin)['format']['duration']))")
echo ""
echo "✅ Reel created: $OUTPUT_DIR/reel-final.mp4"
echo "  Duration: ${DURATION}s"
echo "  Resolution: 1080x1920"
echo "  Codec: H.264"

if (( $(echo "$DURATION > 15.5" | bc -l) )); then
  echo "⚠️ WARNING: Duration ${DURATION}s exceeds 15s limit!"
  exit 1
fi

echo "✅ Duration OK (<= 15s)"
