#!/bin/bash
# run-widget-ja.sh — Deterministic JA widget reelclaw orchestrator (no LLM).
# Reads reelclaw-widget-hooks-ja.json (lines[] schema, status=active).
# Bootstrap render = workspace/reelclaw-widget-ja-* の reel-final.mp4 / reel-text.mp4。
#
# Usage: bash run-widget-ja.sh --tt <int> [--ig <int>] [--yt <int>]

set -uo pipefail
SKILL_DIR="$HOME/.openclaw/workspace/skills/reelclaw"
HOOK_FILE="$HOME/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json"
# M2 2026-06-08 random pick from reelclaw-assets/videos/widget-ja/v*.mp4 (HARD RULE 0.34)
ASSETS_DIR="$HOME/.openclaw/workspace/reelclaw-assets/videos/widget-ja"
VARIANTS=("$ASSETS_DIR"/v*.mp4)
PICKED="${VARIANTS[RANDOM % ${#VARIANTS[@]}]}"
DEFAULT_FINAL="$PICKED"
DEFAULT_TEXT="$PICKED"
echo "[widget-ja] random variant: $(basename $PICKED) of ${#VARIANTS[@]}"
TT_INT=""; IG_INT=""; YT_INT=""
SRC_FINAL="$DEFAULT_FINAL"; SRC_TEXT="$DEFAULT_TEXT"

while [[ $# -gt 0 ]]; do
  case $1 in
    --tt) TT_INT="$2"; shift 2 ;;
    --ig) IG_INT="$2"; shift 2 ;;
    --yt) YT_INT="$2"; shift 2 ;;
    --src-final) SRC_FINAL="$2"; shift 2 ;;
    --src-text) SRC_TEXT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -f "$SRC_FINAL" ]] || { echo "FATAL: src-final not found: $SRC_FINAL"; exit 2; }
[[ -f "$SRC_TEXT"  ]] || { echo "FATAL: src-text not found: $SRC_TEXT"; exit 2; }

set -a; source "$HOME/.openclaw/.env" 2>/dev/null; set +a
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not set}"

# Step 1: pick LRU active widget hook
HOOK_JSON=$(python3 - <<'PY'
import json, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json")
d=json.load(open(p))
active=[h for h in d["hooks"] if h.get("status")=="active"]
if not active: raise SystemExit("no active widget hooks")
active.sort(key=lambda h: h.get("lastUsed") or "1970-01-01")
h=active[0]
text = "\n".join(h.get("lines",[]))
print(json.dumps({"id":h["id"],"text":text}, ensure_ascii=False))
PY
)
HOOK_ID=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
HOOK_TEXT=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])")
echo "HOOK_ID=$HOOK_ID"
echo "HOOK_TEXT=$HOOK_TEXT"

# Step 2: output dir + bootstrap
RUN_TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/.openclaw/workspace/runs/reelclaw-widget-ja-${RUN_TS}-${HOOK_ID}"
mkdir -p "$OUT"
cp "$SRC_FINAL" "$OUT/reel-final.mp4"
cp "$SRC_TEXT"  "$OUT/reel-text.mp4"

# Step 2b: TT 用無音動画に BGM mux(autoAddMusic 依存をやめ ja無音着地を消す)
BGM="$HOME/.openclaw/workspace/tiktok-marketing/music/bgm-cta.mp3"
TT_VIDEO="$OUT/reel-text.mp4"
if [[ -f "$BGM" ]] && ! ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$OUT/reel-text.mp4" | grep -q .; then
  if ffmpeg -y -hide_banner -loglevel error -i "$OUT/reel-text.mp4" -stream_loop -1 -i "$BGM" \
       -filter_complex "[1:a]volume=0.5[bgm]" -map 0:v -map "[bgm]" \
       -c:v copy -c:a aac -b:a 128k -shortest -movflags +faststart "$OUT/reel-text-bgm.mp4"; then
    TT_VIDEO="$OUT/reel-text-bgm.mp4"
  else
    echo "⚠️ BGM mux failed — TT will be silent" >&2
  fi
fi

# Step 3: captions
TT_TITLE="こんな言葉が欲しい人は、アニッチャ試してみて"
TT_CAPTION="$HOOK_TEXT"
IG_CAPTION="${HOOK_TEXT}

#ロック画面 #アファメーション #ウィジェット #メンタルヘルス #アニッチャ"
YT_TITLE="ロック画面にアファメーションを設定する方法"
YT_CAPTION="#アファメーション #ロック画面 #ウィジェット #メンタルヘルス #アニッチャ"

# Step 4-6: 3 posts
TT_POST_ID=""; IG_POST_ID=""; YT_POST_ID=""

if [[ -n "$TT_INT" ]]; then
  echo "=== POST TT ($TT_INT) ==="
  TT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-tiktok.sh" \
    --video "$TT_VIDEO" --caption "$TT_CAPTION" --title "$TT_TITLE" \
    --integration "$TT_INT" --privacy PUBLIC_TO_EVERYONE --posting-method DIRECT_POST 2>&1) || true
  TT_POST_ID=$(printf '%s' "$TT_RES" | grep -oE 'PostID: [^ ]+' | tail -1 | sed 's/PostID: //')
  echo "TT_POST_ID=${TT_POST_ID:-FAILED}"
fi

if [[ -n "$IG_INT" ]]; then
  echo "=== POST IG ($IG_INT) ==="
  IG_RES=$(bash "$SKILL_DIR/scripts/post-video-to-instagram.sh" \
    --video "$OUT/reel-final.mp4" --caption "$IG_CAPTION" --integration "$IG_INT" 2>&1) || true
  IG_POST_ID=$(printf '%s' "$IG_RES" | grep -oE 'IG_POST_ID=\S+' | head -1 | cut -d= -f2)
  echo "IG_POST_ID=${IG_POST_ID:-FAILED}"
fi

if [[ -n "$YT_INT" ]]; then
  echo "=== POST YT ($YT_INT) ==="
  YT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-youtube.sh" \
    --video "$OUT/reel-final.mp4" --title "$YT_TITLE" --caption "$YT_CAPTION" \
    --integration "$YT_INT" 2>&1) || true
  YT_POST_ID=$(printf '%s' "$YT_RES" | grep -oE 'YT_POST_ID=\S+' | head -1 | cut -d= -f2)
  echo "YT_POST_ID=${YT_POST_ID:-FAILED}"
fi

# Step 7: update hook lastUsed
if [[ -n "$TT_POST_ID$IG_POST_ID$YT_POST_ID" ]]; then
  HOOK_ID="$HOOK_ID" python3 - <<'PY'
import json, datetime, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json")
d=json.load(open(p))
hid=os.environ["HOOK_ID"]
for h in d["hooks"]:
    if h.get("id")==hid:
        ts=datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        h["lastUsed"]=ts[:-2]+":"+ts[-2:]
json.dump(d, open(p,"w"), ensure_ascii=False, indent=2)
print(f"updated widget hook {hid} lastUsed")
PY
fi

echo "=== REPORT ==="
echo "HOOK_ID=$HOOK_ID"
echo "TT_POST_ID=${TT_POST_ID:-NONE}"
echo "IG_POST_ID=${IG_POST_ID:-NONE}"
echo "YT_POST_ID=${YT_POST_ID:-NONE}"
echo "OUT=$OUT"

RC=0
[[ -n "$TT_INT" && -z "$TT_POST_ID" ]] && RC=$((RC|1))
[[ -n "$IG_INT" && -z "$IG_POST_ID" ]] && RC=$((RC|2))
[[ -n "$YT_INT" && -z "$YT_POST_ID" ]] && RC=$((RC|4))
exit $RC
