#!/bin/bash
# run-honne-ja.sh — Deterministic JA Honne reelclaw orchestrator (no LLM).
# Honne = relationship/感情翻訳 niche (別アプリ "Honne AI").
# Reads honne-hooks-ja.json + honne-mapping.json. Posts TT only (no IG/YT).
# Bootstrap: existing honne-ai/reel-final.mp4。

set -euo pipefail
SKILL_DIR="$HOME/.openclaw/workspace/skills/reelclaw"
HONNE_DIR="$HOME/.openclaw/workspace/honne-ai"
# M2 2026-06-08 random pick from reelclaw-assets/videos/honne-ja/v*.mp4 (HARD RULE 0.34)
ASSETS_DIR="$HOME/.openclaw/workspace/reelclaw-assets/videos/honne-ja"
VARIANTS=("$ASSETS_DIR"/v*.mp4)
PICKED="${VARIANTS[RANDOM % ${#VARIANTS[@]}]}"
DEFAULT_FINAL="$PICKED"
DEFAULT_TEXT="$PICKED"
echo "[honne-ja] random variant: $(basename $PICKED) of ${#VARIANTS[@]}"   # honne TT = silent autoMusic ok
TT_INT=""
SRC_FINAL="$DEFAULT_FINAL"; SRC_TEXT="$DEFAULT_TEXT"

while [[ $# -gt 0 ]]; do
  case $1 in
    --tt) TT_INT="$2"; shift 2 ;;
    --src-final) SRC_FINAL="$2"; shift 2 ;;
    --src-text) SRC_TEXT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -f "$SRC_FINAL" ]] || { echo "FATAL: src-final not found: $SRC_FINAL"; exit 2; }
set -a; source "$HOME/.openclaw/.env" 2>/dev/null; set +a
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not set}"

# pick LRU active honne hook (hooksByVideo structure: dict of video→[hooks])
HOOK_JSON=$(python3 - <<'PY'
import json, os
p=os.path.expanduser("~/.openclaw/workspace/honne-ai/honne-hooks-ja.json")
d=json.load(open(p))
hbv=d.get("hooksByVideo") or {}
all_hooks=[]
for vid, hooks in hbv.items():
    for h in hooks:
        if h.get("status") in (None,"active","preferred"):
            h["_video"]=vid
            all_hooks.append(h)
# fallback flat shape (en)
if not all_hooks:
    hooks=d.get("hooks", d if isinstance(d,list) else [])
    for h in hooks:
        if h.get("status") in (None,"active","preferred"): all_hooks.append(h)
if not all_hooks: raise SystemExit("no honne active hooks")
all_hooks.sort(key=lambda h: h.get("lastUsed") or "1970-01-01")
h=all_hooks[0]
text = h.get("text") or "\n".join(h.get("lines",[]))
print(json.dumps({"id":h.get("id","H?"),"text":text,"video":h.get("_video","")}, ensure_ascii=False))
PY
)
HOOK_ID=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
HOOK_TEXT=$(printf '%s' "$HOOK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])")
if [[ -z "${HOOK_ID:-}" || -z "${HOOK_TEXT:-}" ]]; then
  echo "FATAL: refusing to post with an empty hook id or text" >&2
  exit 3
fi
echo "HOOK_ID=$HOOK_ID"
echo "HOOK_TEXT=$HOOK_TEXT"

RUN_TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/.openclaw/workspace/runs/honne-ja-${RUN_TS}-${HOOK_ID}"
mkdir -p "$OUT"
cp "$SRC_FINAL" "$OUT/reel-final.mp4"
cp "$SRC_TEXT" "$OUT/reel-text.mp4"

TT_TITLE="Honne — 言いたいこと、翻訳します"
TT_CAPTION="$HOOK_TEXT"

TT_POST_ID=""
if [[ -n "$TT_INT" ]]; then
  echo "=== POST TT ($TT_INT) ==="
  TT_RES=$(bash "$SKILL_DIR/scripts/post-video-to-tiktok.sh" \
    --video "$OUT/reel-text.mp4" --caption "$TT_CAPTION" --title "$TT_TITLE" \
    --integration "$TT_INT" --privacy PUBLIC_TO_EVERYONE --posting-method DIRECT_POST 2>&1) || true
  TT_POST_ID=$(printf '%s' "$TT_RES" | grep -oE 'PostID: [^ ]+' | tail -1 | sed 's/PostID: //')
  echo "TT_POST_ID=${TT_POST_ID:-FAILED}"
fi

if [[ -n "$TT_POST_ID" ]]; then
  HOOK_ID="$HOOK_ID" python3 - <<'PY'
import json, datetime, os
p=os.path.expanduser("~/.openclaw/workspace/honne-ai/honne-hooks-ja.json")
d=json.load(open(p))
hid=os.environ["HOOK_ID"]
ts=datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
stamp=ts[:-2]+":"+ts[-2:]
# hooksByVideo structure
for vid, hooks in (d.get("hooksByVideo") or {}).items():
    for h in hooks:
        if h.get("id")==hid: h["lastUsed"]=stamp
# fallback flat hooks
for h in (d.get("hooks", d if isinstance(d,list) else [])):
    if h.get("id")==hid: h["lastUsed"]=stamp
json.dump(d, open(p,"w"), ensure_ascii=False, indent=2)
print(f"updated honne hook {hid} lastUsed")
PY
fi

echo "=== REPORT ==="
echo "HOOK_ID=$HOOK_ID"
echo "TT_POST_ID=${TT_POST_ID:-NONE}"
echo "IG_POST_ID=NONE"
echo "YT_POST_ID=NONE"
echo "OUT=$OUT"

[[ -n "$TT_INT" && -z "$TT_POST_ID" ]] && exit 1
exit 0
