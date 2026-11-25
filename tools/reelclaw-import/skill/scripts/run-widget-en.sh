#!/bin/bash
# run-widget-en.sh — Deterministic EN widget reelclaw orchestrator (no LLM).
# 5/17 override: en widget typically passes no --yt.

set -uo pipefail
SKILL_DIR="$HOME/.openclaw/workspace/skills/reelclaw"
HOOK_FILE="$HOME/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json"
# M2 2026-06-08 random pick from reelclaw-assets/videos/widget-en/v*.mp4 (HARD RULE 0.34)
ASSETS_DIR="$HOME/.openclaw/workspace/reelclaw-assets/videos/widget-en"
VARIANTS=("$ASSETS_DIR"/v*.mp4)
PICKED="${VARIANTS[RANDOM % ${#VARIANTS[@]}]}"
DEFAULT_FINAL="$PICKED"
DEFAULT_TEXT="$PICKED"
echo "[widget-en] random variant: $(basename $PICKED) of ${#VARIANTS[@]}"
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

HOOK_JSON=$(python3 - <<'PY'
import json, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json")
d=json.load(open(p))
active=[h for h in d["hooks"] if h.get("status")=="active"]
if not active: raise SystemExit("no active widget hooks en")
active.sort(key=lambda h: h.get("lastUsed") or "1970-01-01")
h=active[0]
text = "\n".join(h.get("lines",[]))
print(json.dumps({"id":h["id"],"text":text}))
PY
)
HOOK_ID=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
HOOK_TEXT=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])")
echo "HOOK_ID=$HOOK_ID"
echo "HOOK_TEXT=$HOOK_TEXT"

RUN_TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/.openclaw/workspace/runs/reelclaw-widget-en-${RUN_TS}-${HOOK_ID}"
mkdir -p "$OUT"
cp "$SRC_FINAL" "$OUT/reel-final.mp4"
cp "$SRC_TEXT"  "$OUT/reel-text.mp4"

TT_TITLE="try Anicca — words like these, every day"
TT_CAPTION="$HOOK_TEXT"
IG_CAPTION="${HOOK_TEXT}

#affirmations #lockscreen #widget #mentalhealth #anicca"
YT_TITLE="how to put affirmations on your lockscreen"
YT_CAPTION="#affirmations #lockscreen #widget #mentalhealth #anicca"

TT_POST_ID=""; IG_POST_ID=""; YT_POST_ID=""

if [[ -n "$TT_INT" ]]; then
  echo "=== POST TT ($TT_INT) ==="
  TT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-tiktok.sh" \
    --video "$OUT/reel-text.mp4" --caption "$TT_CAPTION" --title "$TT_TITLE" \
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

if [[ -n "$TT_POST_ID$IG_POST_ID$YT_POST_ID" ]]; then
  HOOK_ID="$HOOK_ID" python3 - <<'PY'
import json, datetime, os
p=os.path.expanduser("~/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json")
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
