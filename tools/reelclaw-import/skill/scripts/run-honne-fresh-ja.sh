#!/usr/bin/env bash
# run-honne-fresh-ja.sh — Honne JA reelclaw with FRESH LLM-generated hooks (no fixed dict).
# Spec Part E1: pattern-honne-ja.jsonl pick by views + 14d anti-repeat → LLM clone structure → fresh wording → post.
# Usage: run-honne-fresh-ja.sh --tt <int> [--ig <int>] [--yt <int>]
set -euo pipefail
SKILL_DIR="${HONNE_SKILL_DIR:-$HOME/.openclaw/workspace/skills/reelclaw}"
HONNE_DIR="${HONNE_DIR:-$HOME/.openclaw/workspace/honne-ai}"
PATTERN="${HONNE_PATTERN:-$HOME/.openclaw/state/content-library/pattern-honne-ja.jsonl}"
HISTORY="${HONNE_HISTORY:-$HOME/.openclaw/state/account-history.jsonl}"
SRC_FINAL="$HONNE_DIR/reel-final.mp4"
SRC_TEXT="$HONNE_DIR/reel-text.mp4"
RUN_ROOT="${HONNE_RUN_ROOT:-$HOME/.openclaw/workspace/runs}"
MARKETING_RUNNER="${HONNE_MARKETING_RUNNER:-/Users/anicca/profitable-claude/bin/run_marketing_prompt.sh}"
HOOK_SCHEMA="${HONNE_HOOK_SCHEMA:-/Users/anicca/profitable-claude/config/openclaw/schemas/honne-fresh-hook.schema.json}"

TT_INT=""; IG_INT=""; YT_INT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tt) TT_INT="$2"; shift 2 ;;
    --ig) IG_INT="$2"; shift 2 ;;
    --yt) YT_INT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

set -a; [ ! -f "$HOME/.openclaw/.env" ] || . "$HOME/.openclaw/.env"; set +a
: "${POSTIZ_API_KEY:?POSTIZ_API_KEY not set}"
[ -x "$MARKETING_RUNNER" ] || { echo "marketing runner missing: $MARKETING_RUNNER" >&2; exit 2; }
[ -f "$HOOK_SCHEMA" ] || { echo "hook schema missing: $HOOK_SCHEMA" >&2; exit 2; }

# Pick the highest-view fresh pattern deterministically. The shared marketing runner
# owns provider/model selection and structured generation after this step.
PICK_JSON=$(python3 <<PY
import json, os, datetime
pattern_p = "$PATTERN"
hist_p = "$HISTORY"

# 14d anti-repeat: load account-history.jsonl
posted_hooks = set()
now = datetime.datetime.now(datetime.timezone.utc)
cutoff = now - datetime.timedelta(days=14)
if os.path.exists(hist_p):
    for line in open(hist_p):
        try:
            r = json.loads(line)
            ts = r.get('posted_at') or r.get('ts') or ''
            if ts:
                dt = datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))
                if dt > cutoff:
                    src = r.get('source_id') or r.get('hook_pattern_id')
                    if src: posted_hooks.add(src)
        except Exception:
            pass

# Load patterns, filter, sort by views
patterns = []
if not os.path.exists(pattern_p): raise SystemExit("pattern jsonl missing")
for line in open(pattern_p):
    try:
        p = json.loads(line)
        if p.get('source_id') in posted_hooks: continue
        if p.get('status') != 'active': continue
        patterns.append(p)
    except Exception:
        pass

if not patterns: raise SystemExit("no fresh honne patterns")
patterns.sort(key=lambda p: p.get('observed',{}).get('views',0), reverse=True)
pick = patterns[0]
print(json.dumps({
    'source_id': pick.get('source_id','?'),
    'source_hook': pick.get('hook',''),
    'char_count': pick.get('structure',{}).get('char_count', 30),
    'emotion': pick.get('emotion','calm'),
}, ensure_ascii=False))
PY
)
SOURCE_ID=$(printf '%s' "$PICK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['source_id'])")
SOURCE_HOOK=$(printf '%s' "$PICK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['source_hook'])")
CHAR_COUNT=$(printf '%s' "$PICK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['char_count'])")
EMOTION=$(printf '%s' "$PICK_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['emotion'])")

PROMPT_FILE=$(mktemp "${TMPDIR:-/tmp}/honne-fresh-hook.XXXXXX")
trap 'rm -f "$PROMPT_FILE"' EXIT
python3 - "$SOURCE_HOOK" "$CHAR_COUNT" "$EMOTION" >"$PROMPT_FILE" <<'PY'
import sys

source_hook, char_count, emotion = sys.argv[1:]
print(f'''日本の Honne/本音 TikTok の hook を1つ新しく書く。
構造 reference: "{source_hook}"
target 字数: {char_count} 前後
emotion: {emotion}
内容: 親密な人間関係について、honne（本音）を日本語1行で書く。
referenceの逐語借用は禁止。構造だけcloneして、hashtagとemojiは付けない。
hookフィールドだけを厳格JSONで返す。投稿やファイル変更は行わない。''')
PY

GENERATED_JSON=$("$MARKETING_RUNNER" \
  --label reelclaw-honne-ja-fresh-hook \
  --prompt "$PROMPT_FILE" \
  --schema "$HOOK_SCHEMA" \
  --loop honne-marketing \
  --workdir "$HOME/.openclaw")
HOOK_TEXT=$(printf '%s' "$GENERATED_JSON" | python3 -c '
import json, sys
hook = str(json.load(sys.stdin).get("hook", "")).strip()
if not hook or "\n" in hook:
    raise SystemExit("generated hook must be one non-empty line")
print(hook)
')
HOOK_ID="honne-ja-${SOURCE_ID}-$(date +%y%m%d)"
echo "HOOK_ID=$HOOK_ID"
echo "HOOK_TEXT=$HOOK_TEXT"
echo "SOURCE_ID=$SOURCE_ID"

RUN_TS=$(date +%Y%m%d-%H%M%S)
OUT="$RUN_ROOT/honne-ja-fresh-${RUN_TS}-${SOURCE_ID}"
mkdir -p "$OUT"
cp "$SRC_FINAL" "$OUT/reel-final.mp4"
# reel-text.mp4 may not exist for JA; fall back to reel-final.mp4
if [[ -f "$SRC_TEXT" ]]; then
  cp "$SRC_TEXT" "$OUT/reel-text.mp4"
else
  cp "$SRC_FINAL" "$OUT/reel-text.mp4"
fi

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

# Append to account-history (14d anti-repeat record)
if [[ -n "$TT_POST_ID" ]]; then
  HONNE_SOURCE_ID="$SOURCE_ID" HONNE_HOOK_TEXT="$HOOK_TEXT" \
    HONNE_POST_ID="$TT_POST_ID" HONNE_HISTORY="$HISTORY" python3 - <<'PY'
import json, datetime, os
hist = os.environ['HONNE_HISTORY']
os.makedirs(os.path.dirname(hist), exist_ok=True)
rec = {
    'posted_at': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
    'account': 'honne-ja-1',
    'hook_pattern_id': 'honne-ja-' + os.environ['HONNE_SOURCE_ID'] + '-' + datetime.datetime.now().strftime('%y%m%d'),
    'source_id': os.environ['HONNE_SOURCE_ID'],
    'hook_text': os.environ['HONNE_HOOK_TEXT'],
    'post_id': os.environ['HONNE_POST_ID'],
    'platform': 'tiktok'
}
with open(hist, 'a') as f: f.write(json.dumps(rec, ensure_ascii=False)+'\n')
print(f"appended account-history: {rec['post_id']}")
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
