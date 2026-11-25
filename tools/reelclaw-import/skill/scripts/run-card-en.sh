#!/bin/bash
# run-card-en.sh — Deterministic EN-card reelclaw orchestrator (no LLM).
# Sister of run-card-ja.sh; reads hooks-en.json + EN niche hashtags + EN CTA.
# 5/17 override: en-card crons typically pass NO --yt (YT skip).
#
# Usage: bash run-card-en.sh --tt <int> [--ig <int>] [--yt <int>]
#                            [--src-final /path] [--src-text /path]
# Required env: POSTIZ_API_KEY

set -euo pipefail
SKILL_DIR="$HOME/.openclaw/workspace/skills/reelclaw"
HOOK_FILE="$HOME/.openclaw/workspace/tiktok-marketing/hooks-en.json"
# M2 2026-06-08 random pick from reelclaw-assets/videos/card-en/v*.mp4 (HARD RULE 0.34)
ASSETS_DIR="$HOME/.openclaw/workspace/reelclaw-assets/videos/card-en"
VARIANTS=("$ASSETS_DIR"/v*.mp4)
PICKED="${VARIANTS[RANDOM % ${#VARIANTS[@]}]}"
DEFAULT_FINAL="$PICKED"
DEFAULT_TEXT="$PICKED"
echo "[card-en] random variant: $(basename $PICKED) of ${#VARIANTS[@]}"
TT_INT=""; IG_INT=""; YT_INT=""
SRC_FINAL="$DEFAULT_FINAL"; SRC_TEXT="$DEFAULT_TEXT"
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
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not set}"

# WS3b3 #152 Task6b: --use-pattern-jsonl flag — propose-and-rewrite で structural_principle pick
SKIP_LEGACY_HOOK=0
if [[ "$USE_PATTERN_JSONL" == "1" ]]; then
  PRR_OUT="$(bash "$HOME/.openclaw/skills/_shared/propose-and-rewrite.sh" \
    --channel card-en --platform TikTok --account anicca-ai --lang en 2>/dev/null)" || PRR_OUT=""
  if [[ -n "$PRR_OUT" ]]; then
    PRR_HOOK="$(printf '%s' "$PRR_OUT" | jq -r '.structural_principle // empty' 2>/dev/null)"
    if [[ -n "$PRR_HOOK" ]]; then
      HOOK_TEXT="$PRR_HOOK"
      HOOK_ID="pjsonl-$(date +%s)"
      echo "[card-en] using pattern-jsonl source HOOK_ID=$HOOK_ID"
      echo "HOOK_ID=$HOOK_ID"
      echo "HOOK_TEXT=$HOOK_TEXT"
      SKIP_LEGACY_HOOK=1
    fi
  fi
  [[ "$SKIP_LEGACY_HOOK" == "0" ]] && echo "[card-en] pattern-jsonl unavailable, falling back to legacy hooks-en.json"
fi

if [[ "${SKIP_LEGACY_HOOK:-0}" != "1" ]]; then
# Step 1: pick LRU preferred EN card hook
HOOK_JSON=$(python3 - <<'PY'
import json, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/hooks-en.json")
d=json.load(open(p))
preferred=[h for h in d["hooks"] if h.get("family")=="reelclaw-card" and h.get("status")=="preferred"]
if not preferred: raise SystemExit("no preferred reelclaw-card EN hooks")
preferred.sort(key=lambda h: h.get("lastUsed") or "1970-01-01")
h=preferred[0]
print(json.dumps({"id":h["id"],"text":h.get("text","")}, ensure_ascii=False))
PY
)
HOOK_ID=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
HOOK_TEXT=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])")
echo "HOOK_ID=$HOOK_ID"
echo "HOOK_TEXT=$HOOK_TEXT"
fi

if [[ -z "${HOOK_ID:-}" || -z "${HOOK_TEXT:-}" ]]; then
  echo "FATAL: refusing to post with an empty hook id or text" >&2
  exit 3
fi

# Step 2: output dir + bootstrap video
RUN_TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/.openclaw/workspace/runs/reelclaw-card-en-${RUN_TS}-${HOOK_ID}"
mkdir -p "$OUT"
cp "$SRC_FINAL" "$OUT/reel-final.mp4"
cp "$SRC_TEXT"  "$OUT/reel-text.mp4"

# Step 3: EN captions
TT_TITLE="try Anicca — words like these, every day"
TT_CAPTION="$HOOK_TEXT"
IG_CAPTION="${HOOK_TEXT}

#affirmations #mentalhealth #selfcare #mindfulness #anicca"
YT_TITLE="try Anicca — words like these, every day"
YT_CAPTION="#affirmations #mentalhealth #selfcare #mindfulness #anicca"

# Step 4: TT
TT_POST_ID=""
if [[ -n "$TT_INT" ]]; then
  echo "=== POST TT ($TT_INT) ==="
  TT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-tiktok.sh" \
    --video "$OUT/reel-text.mp4" --caption "$TT_CAPTION" --title "$TT_TITLE" \
    --integration "$TT_INT" --privacy PUBLIC_TO_EVERYONE --posting-method DIRECT_POST 2>&1) || true
  TT_POST_ID=$(printf '%s' "$TT_RES" | grep -oE 'PostID: [^ ]+' | tail -1 | sed 's/PostID: //')
  echo "TT_POST_ID=${TT_POST_ID:-FAILED}"
  printf '%s\n' "$TT_RES" | tail -3
fi

# Step 5: IG (optional)
IG_POST_ID=""
if [[ -n "$IG_INT" ]]; then
  echo "=== POST IG ($IG_INT) ==="
  IG_RES=$(bash "$SKILL_DIR/scripts/post-video-to-instagram.sh" \
    --video "$OUT/reel-final.mp4" --caption "$IG_CAPTION" --integration "$IG_INT" 2>&1) || true
  IG_POST_ID=$(printf '%s' "$IG_RES" | grep -oE 'IG_POST_ID=\S+' | head -1 | cut -d= -f2)
  echo "IG_POST_ID=${IG_POST_ID:-FAILED}"
fi

# Step 6: YT (optional — usually skipped for EN per 5/17 override)
YT_POST_ID=""
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
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/hooks-en.json")
d=json.load(open(p))
hid=os.environ["HOOK_ID"]
for h in d["hooks"]:
    if h.get("id")==hid:
        ts=datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        h["lastUsed"]=ts[:-2]+":"+ts[-2:]
json.dump(d, open(p,"w"), ensure_ascii=False, indent=2)
print(f"updated hook {hid} lastUsed")
PY
fi

# Step 8: REPORT
echo "=== REPORT ==="
echo "HOOK_ID=$HOOK_ID"
echo "TT_POST_ID=${TT_POST_ID:-NONE}"
echo "IG_POST_ID=${IG_POST_ID:-NONE}"
echo "YT_POST_ID=${YT_POST_ID:-NONE}"
echo "OUT=$OUT"

# Step 9: exit code
RC=0
[[ -n "$TT_INT" && -z "$TT_POST_ID" ]] && RC=$((RC|1))
[[ -n "$IG_INT" && -z "$IG_POST_ID" ]] && RC=$((RC|2))
[[ -n "$YT_INT" && -z "$YT_POST_ID" ]] && RC=$((RC|4))
exit $RC
