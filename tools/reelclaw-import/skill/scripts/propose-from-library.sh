#!/usr/bin/env bash
# propose-from-library.sh — generic propose-from-library for any family.
# Bible HARD RULE #15: NO rotation. Every post fresh from library.
# Adrià Martinez + StudyTok Hermes pattern.
#
# Usage:
#   bash propose-from-library.sh --family <card-ja|card-en|widget-ja|widget-en|...>
#                                --account <handle>
# Output (stdout, JSON one-line):
#   {"source_id":"...", "hook":"...", "structure_type":"slideshow|video|long-caption",
#    "emotion":"...", "observed_views":NNN, "music_id":"...", "source_url":"..."}
# Exit 0 = picked; exit 1 = no eligible entry.
#
# Algorithm (per Bible):
#   1. Load pattern-<family>.jsonl (sorted by views desc)
#   2. Load account-history.jsonl, build "recent source_ids for this account in last 14d"
#   3. Filter pattern entries:
#      - status != killed
#      - source_id NOT in recent (14d anti-repeat per account)
#      - emotion / structure diversity (niche-rotation: prefer emotion untouched 30d+
#        by this account; soft bonus, not hard filter)
#   4. From top-50 by views, pick least-recently-used by lastUsed (NULL = never used)
#   5. Update lastUsed in pattern-<family>.jsonl

set -uo pipefail
FAMILY=""
ACCOUNT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --family) FAMILY="$2"; shift 2 ;;
    --account) ACCOUNT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done
[[ -n "$FAMILY" ]] || { echo "FATAL: --family required" >&2; exit 2; }
[[ -n "$ACCOUNT" ]] || { echo "FATAL: --account required" >&2; exit 2; }

LIB="$HOME/.openclaw/state/content-library"
PATTERN="$LIB/pattern-${FAMILY}.jsonl"
HISTORY="$LIB/account-history.jsonl"
[[ -f "$PATTERN" ]] || { echo "FATAL: pattern file missing: $PATTERN" >&2; exit 3; }
[[ -f "$HISTORY" ]] || { echo "FATAL: history file missing (run T1-77 init)" >&2; exit 4; }

FAMILY="$FAMILY" ACCOUNT="$ACCOUNT" PATTERN="$PATTERN" HISTORY="$HISTORY" python3 - <<'PY'
import json, os, sys, datetime, time, random
family  = os.environ["FAMILY"]
account = os.environ["ACCOUNT"]
pattern = os.environ["PATTERN"]
history = os.environ["HISTORY"]

# load pattern
entries = []
for line in open(pattern):
    line = line.strip()
    if not line: continue
    try: entries.append(json.loads(line))
    except: pass
if not entries:
    print("FATAL: empty pattern file", file=sys.stderr); sys.exit(3)

# load history (skip schema header line)
recent_source_ids = set()
recent_emotions   = {}
cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
cutoff_30 = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
for line in open(history):
    line=line.strip()
    if not line: continue
    try: h=json.loads(line)
    except: continue
    if h.get("schema"): continue
    if h.get("account") != account: continue
    posted = h.get("posted_at","")
    if posted < cutoff: continue       # outside 14d window
    sid = h.get("source_id")
    if sid: recent_source_ids.add(sid)
    emo = h.get("emotion")
    if emo and posted >= cutoff_30:
        recent_emotions[emo] = recent_emotions.get(emo,0) + 1

# filter
eligible = [e for e in entries
            if e.get("status","active") != "killed"
            and e.get("source_id") not in recent_source_ids]

if not eligible:
    print(f"FATAL: no eligible entries for {family}/{account} (14d anti-repeat exhausted: {len(recent_source_ids)} recent)", file=sys.stderr)
    sys.exit(5)

# top-50 by views
top50 = sorted(eligible, key=lambda e: -e["observed"]["views"])[:50]

# niche-rotation soft bonus: prefer emotion not used in last 30d
def score(e):
    base = e["observed"]["views"]
    emo_used = recent_emotions.get(e.get("emotion"),0)
    # penalize already-used emotions
    if emo_used >= 3: base = base // 2
    elif emo_used >= 1: base = base * 3 // 4
    # boost never-used (lastUsed is null)
    if not e.get("lastUsed"):
        base = int(base * 1.2)
    return base

top50.sort(key=score, reverse=True)

# pick top 1 (eventually plug recursive-improver here for 5-candidate scoring)
winner = top50[0]

# mark lastUsed in pattern file (rewrite atomic)
now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
tmp = pattern + ".tmp"
with open(tmp,"w") as out:
    for e in entries:
        if e.get("source_id") == winner.get("source_id"):
            e["lastUsed"] = now
        out.write(json.dumps(e, ensure_ascii=False) + "\n")
os.replace(tmp, pattern)

# emit pick
print(json.dumps({
    "source_id":      winner.get("source_id",""),
    "source_url":     winner.get("source_url",""),
    "hook":           winner.get("hook",""),
    "structure_type": winner.get("structure",{}).get("type",""),
    "emotion":        winner.get("emotion",""),
    "observed_views": winner["observed"]["views"],
    "music_id":       winner.get("music_id",""),
    "author":         winner.get("author",""),
}, ensure_ascii=False))
PY
