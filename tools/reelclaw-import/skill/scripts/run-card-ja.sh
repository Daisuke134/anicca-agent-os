#!/bin/bash
# run-card-ja.sh — Deterministic JA-card reelclaw orchestrator (no LLM).
# - Pick least-recently-used preferred hook from hooks-ja.json
# - Use an existing rendered card video as the source (bootstrap; real render integration later)
# - Post to TT + IG (optional) + YT via the 3 post shells
# - Update hook lastUsed state in hooks-ja.json
# - Exit !=0 on any failure; print POST IDs + URLs to stdout
#
# Usage: bash run-card-ja.sh --tt <integration> [--ig <integration>] [--yt <integration>]
#                            [--src-final /path] [--src-text /path]
#
# Required env: POSTIZ_API_KEY (sourced from ~/.openclaw/.env)

set -uo pipefail
SKILL_DIR="$HOME/.openclaw/workspace/skills/reelclaw"
HOOK_FILE="$HOME/.openclaw/workspace/tiktok-marketing/hooks-ja.json"
# M2 2026-06-08 random pick from reelclaw-assets/videos/card-ja/v*.mp4 (HARD RULE 0.34)
ASSETS_DIR="$HOME/.openclaw/workspace/reelclaw-assets/videos/card-ja"
VARIANTS=("$ASSETS_DIR"/v*.mp4)
PICKED="${VARIANTS[RANDOM % ${#VARIANTS[@]}]}"
DEFAULT_FINAL="$PICKED"
DEFAULT_TEXT="$PICKED"
echo "[card-ja] random variant: $(basename $PICKED) of ${#VARIANTS[@]}"
TT_INT=""; IG_INT=""; YT_INT=""
SRC_FINAL="$DEFAULT_FINAL"
SRC_TEXT="$DEFAULT_TEXT"
USE_PATTERN_JSONL=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --tt) TT_INT="$2"; shift 2 ;;
    --ig) IG_INT="$2"; shift 2 ;;
    --yt) YT_INT="$2"; shift 2 ;;
    --src-final) SRC_FINAL="$2"; shift 2 ;;
    --src-text) SRC_TEXT="$2"; shift 2 ;;
    --use-pattern-jsonl) USE_PATTERN_JSONL=1; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -f "$SRC_FINAL" ]] || { echo "FATAL: src-final not found: $SRC_FINAL"; exit 2; }
[[ -f "$SRC_TEXT"  ]] || { echo "FATAL: src-text not found: $SRC_TEXT"; exit 2; }

set -a; source "$HOME/.openclaw/.env" 2>/dev/null; set +a
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not in ~/.openclaw/.env}"

# WS3b3 #152 Task6b: --use-pattern-jsonl flag — propose-and-rewrite で structural_principle pick
SKIP_LEGACY_HOOK=0
if [[ "$USE_PATTERN_JSONL" == "1" ]]; then
  PRR_OUT="$(bash "$HOME/.openclaw/skills/_shared/propose-and-rewrite.sh" \
    --channel card-ja --platform TikTok --account anicca-jp --lang ja 2>/dev/null)" || PRR_OUT=""
  if [[ -n "$PRR_OUT" ]]; then
    PRR_HOOK="$(printf '%s' "$PRR_OUT" | jq -r '.structural_principle // empty' 2>/dev/null)"
    if [[ -n "$PRR_HOOK" ]]; then
      HOOK_TEXT="$PRR_HOOK"
      HOOK_ID="pjsonl-$(date +%s)"
      SOURCE_ID=""
      EMOTION=""
      echo "[card-ja] using pattern-jsonl source HOOK_ID=$HOOK_ID"
      echo "HOOK_ID=$HOOK_ID"
      echo "HOOK_TEXT=$HOOK_TEXT"
      SKIP_LEGACY_HOOK=1
    fi
  fi
  [[ "$SKIP_LEGACY_HOOK" == "0" ]] && echo "[card-ja] pattern-jsonl unavailable, falling back to legacy hooks-ja.json"
fi

if [[ "${SKIP_LEGACY_HOOK:-0}" != "1" ]]; then
# Step 1: pick hook (LRU preferred from curated hooks-ja.json bank — safe for now).
# T1-#82/#83 follow-up: propose-from-library is wired and tested (T1 lib commit), BUT
# returns VERBATIM viral hook text from public TikTok — using as-is = plagiarism.
# Production wire-up requires LLM clone-don't-template rewrite step (take propose's
# structure+emotion+niche, generate fresh Anicca-voice hook in JA). Until that step
# exists, stay on the curated bank (Dais-approved hooks).
HOOK_JSON=$(python3 - <<'PY'
import json, datetime, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/hooks-ja.json")
d=json.load(open(p))
preferred=[h for h in d["hooks"] if h.get("family")=="reelclaw-card" and h.get("status")=="preferred"]
if not preferred:
    raise SystemExit("no preferred reelclaw-card hooks in hooks-ja.json")
preferred.sort(key=lambda h: h.get("lastUsed") or "1970-01-01")
h=preferred[0]
print(json.dumps({"id":h["id"],"text":h.get("text","")}, ensure_ascii=False))
PY
)
HOOK_ID=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
HOOK_TEXT=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])")
SOURCE_ID=""  # legacy bank, no library source
EMOTION=""
echo "HOOK_ID=$HOOK_ID"
echo "HOOK_TEXT=$HOOK_TEXT"
fi
# Account derivation kept for future account-history when we re-enable propose
case "$TT_INT" in
  cmnhlk3ju*) ACCOUNT="anicca.jp8" ;;
  cmlrv8jq*)  ACCOUNT="anicca.jpx" ;;
  cmlt171eq*) ACCOUNT="aniccaen2" ;;
  cmp9sdev5*) ACCOUNT="anicca.jp" ;;
  *)          ACCOUNT="${TT_INT:0:12}" ;;
esac

# Step 2: prepare output dir + copy source videos (bootstrap render — to be replaced with per-run render)
RUN_TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/.openclaw/workspace/runs/reelclaw-card-ja-${RUN_TS}-${HOOK_ID}"
mkdir -p "$OUT"
cp "$SRC_FINAL" "$OUT/reel-final.mp4"
cp "$SRC_TEXT" "$OUT/reel-text.mp4"

# Step2b: TT 用無音動画に BGM mux(autoAddMusic 依存をやめ ja無音着地を消す)
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

# Step 3: build captions
TT_TITLE="こんな言葉が欲しい人は、アニッチャ試してみて"
TT_CAPTION="$HOOK_TEXT"
IG_CAPTION="${HOOK_TEXT}

#メンタルヘルス #自己肯定感 #マインドフルネス #アニッチャ"
YT_TITLE="こんな言葉が欲しい人は、アニッチャ試してみて"
YT_CAPTION="#メンタルヘルス #自己肯定感 #マインドフルネス #アニッチャ"

# Step 4: POST TikTok (silent video → autoAddMusic via Postiz)
TT_POST_ID=""; TT_URL=""
if [[ -n "$TT_INT" ]]; then
  echo "=== POST TT ($TT_INT) ==="
  TT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-tiktok.sh" \
    --video "$TT_VIDEO" \
    --caption "$TT_CAPTION" \
    --title "$TT_TITLE" \
    --integration "$TT_INT" \
    --privacy PUBLIC_TO_EVERYONE \
    --posting-method DIRECT_POST 2>&1) || true
  TT_POST_ID=$(printf '%s' "$TT_RES" | grep -oE 'PostID: [^ ]+' | tail -1 | sed 's/PostID: //')
  echo "TT_POST_ID=${TT_POST_ID:-FAILED}"
  printf '%s\n' "$TT_RES" | tail -3
fi

# Step 5: POST IG (BGM video) — only if --ig supplied
IG_POST_ID=""; IG_URL=""
if [[ -n "$IG_INT" ]]; then
  echo "=== POST IG ($IG_INT) ==="
  IG_RES=$(bash "$SKILL_DIR/scripts/post-video-to-instagram.sh" \
    --video "$OUT/reel-final.mp4" \
    --caption "$IG_CAPTION" \
    --integration "$IG_INT" 2>&1) || true
  IG_POST_ID=$(printf '%s' "$IG_RES" | grep -oE 'IG_POST_ID=\S+' | head -1 | cut -d= -f2)
  IG_URL=$(printf '%s' "$IG_RES" | grep -oE 'IG_URL=\S+' | head -1 | cut -d= -f2)
  echo "IG_POST_ID=${IG_POST_ID:-FAILED}"
fi

# Step 6: POST YT (BGM video)
YT_POST_ID=""; YT_URL=""
if [[ -n "$YT_INT" ]]; then
  echo "=== POST YT ($YT_INT) ==="
  YT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-youtube.sh" \
    --video "$OUT/reel-final.mp4" \
    --title "$YT_TITLE" \
    --caption "$YT_CAPTION" \
    --integration "$YT_INT" 2>&1) || true
  YT_POST_ID=$(printf '%s' "$YT_RES" | grep -oE 'YT_POST_ID=\S+' | head -1 | cut -d= -f2)
  YT_URL=$(printf '%s' "$YT_RES" | grep -oE 'YT_URL=\S+' | head -1 | cut -d= -f2)
  echo "YT_POST_ID=${YT_POST_ID:-FAILED}"
fi

# Step 7: append posts to account-history (per-account 14d anti-repeat — Bible HARD RULE #15).
# Also keep legacy hooks-ja.json lastUsed for fallback compat (when propose unavailable).
if [[ -n "$TT_POST_ID$IG_POST_ID$YT_POST_ID" && -n "$SOURCE_ID" ]]; then
  # append each platform that successfully posted to account-history.jsonl
  for plat_pid in "TT:$TT_POST_ID:$ACCOUNT" "IG:$IG_POST_ID:${ACCOUNT%.*}.video" "YT:$YT_POST_ID:anicca-jp"; do
    PLAT="${plat_pid%%:*}"; rest="${plat_pid#*:}"
    PID="${rest%%:*}"; ACC="${rest#*:}"
    [[ -z "$PID" || "$PID" == "FAILED" || "$PID" == "NONE" ]] && continue
    bash "$SKILL_DIR/scripts/append-to-history.sh" \
      --account "$ACC" --platform "$PLAT" --post-id "$PID" \
      --source-id "$SOURCE_ID" \
      --hook "$HOOK_TEXT" --emotion "$EMOTION" >/dev/null 2>&1 || true
  done
fi
# legacy hooks-ja.json lastUsed (fallback compat — harmless when propose is used)
if [[ -n "$TT_POST_ID$IG_POST_ID$YT_POST_ID" && -z "$SOURCE_ID" && -n "$HOOK_ID" ]]; then
  HOOK_ID="$HOOK_ID" python3 - <<'PY'
import json, datetime, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/hooks-ja.json")
d=json.load(open(p))
hid=os.environ["HOOK_ID"]
for h in d["hooks"]:
    if h.get("id")==hid:
        ts=datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        h["lastUsed"]=ts[:-2]+":"+ts[-2:]
json.dump(d, open(p,"w"), ensure_ascii=False, indent=2)
print(f"updated legacy hook {hid} lastUsed")
PY
fi

# Step 8: report (single block — easy to grep from cron summary)
echo "=== REPORT ==="
echo "HOOK_ID=$HOOK_ID"
echo "TT_POST_ID=${TT_POST_ID:-NONE}"
echo "IG_POST_ID=${IG_POST_ID:-NONE}"
echo "YT_POST_ID=${YT_POST_ID:-NONE}"
echo "OUT=$OUT"

# Step 9: exit code — fail if ANY requested platform missed
RC=0
[[ -n "$TT_INT" && -z "$TT_POST_ID" ]] && RC=$((RC|1))
[[ -n "$IG_INT" && -z "$IG_POST_ID" ]] && RC=$((RC|2))
[[ -n "$YT_INT" && -z "$YT_POST_ID" ]] && RC=$((RC|4))
exit $RC
