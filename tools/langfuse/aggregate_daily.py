#!/usr/bin/env python3
"""Read-only daily aggregation over Langfuse Cloud (project: distribution).

Read-only: only GETs against the public API. Never sends traces/scores and
never converts Grok Bot / Cursor official usage into own token counts or cost.
Only usage/cost actually recorded in Langfuse observations is summed; anything
else is reported as unmeasured, never as zero.

Live read path (per Langfuse deprecation notice, v3 traces API removed
2026-11-16): GET /api/public/v2/observations
  ?fields=core,basic,usage,metadata,io&fromStartTime=<from>&toStartTime=<to>
with cursor pagination; group rows by traceId; sum totalCost per trace.
Scores: GET /api/public/v3/scores (cursor pagination), joined by
timestamp == trace startTime (v3 list rows carry no traceId; a trace
score's timestamp equals its trace startTime -- verified 2026-11-06).
If two traces share a startTime the join is marked ambiguous, never guessed.

Classification per trace (same task/output floor = same sessionId + run_id):
  - accepted: score artifact_delivered == 1
  - failed: artifact_delivered == 0 (an ERROR span alone is not failure:
    a trace can carry ERROR spans and still deliver its artifact)
  - accepted_output_null: artifact_count == 0
  - cost_unmeasured: totalCost is null on every observation (no generation
    with model + usage was ever sent) -- reported as null, not 0
  - cache vs new tokens: usageDetails keys other than input/output/total
    (e.g. cache keys) are summed separately and never folded into input.

Keys are read like langfuse_emit.py (env, then ~/.langfuse/keys.env).
Secret values are never printed.

Usage:
  python3 aggregate_daily.py [--from 2026-11-05T15:00:00Z --to 2026-11-06T15:00:00Z]
  Defaults: the current JST day (15:00Z previous day .. 15:00Z today).
  Output: one JSON object on stdout (summary + per-trace rows).
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

KEYS_FILE = Path.home() / ".langfuse" / "keys.env"
DEFAULT_HOST = "https://cloud.langfuse.com"


def load_config():
    cfg = {
        "host": os.environ.get("LANGFUSE_HOST", ""),
        "public": os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
        "secret": os.environ.get("LANGFUSE_SECRET_KEY", ""),
    }
    if not (cfg["public"] and cfg["secret"]) and KEYS_FILE.exists():
        for line in KEYS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k.strip() == "LANGFUSE_HOST" and not cfg["host"]:
                cfg["host"] = v
            elif k.strip() == "LANGFUSE_PUBLIC_KEY" and not cfg["public"]:
                cfg["public"] = v
            elif k.strip() == "LANGFUSE_SECRET_KEY" and not cfg["secret"]:
                cfg["secret"] = v
    cfg["host"] = (cfg["host"] or DEFAULT_HOST).rstrip("/")
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_ts", default=None)
    ap.add_argument("--to", dest="to_ts", default=None)
    args = ap.parse_args()
    now_utc = datetime.now(timezone.utc)
    jst_today = (now_utc + timedelta(hours=9)).date()
    to_dt = datetime(jst_today.year, jst_today.month, jst_today.day, 15, 0, tzinfo=timezone.utc)
    from_dt = to_dt - timedelta(days=1)
    from_ts = args.from_ts or from_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_ts = args.to_ts or to_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    cfg = load_config()
    if not (cfg["public"] and cfg["secret"]):
        print("no Langfuse keys configured (env or ~/.langfuse/keys.env)", file=sys.stderr)
        return 2
    os.environ.pop("NO_PROXY", None)
    os.environ.pop("no_proxy", None)
    tok = base64.b64encode(f"{cfg['public']}:{cfg['secret']}".encode()).decode()

    def get(path):
        req = urllib.request.Request(
            cfg["host"] + path, headers={"Authorization": f"Basic {tok}"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())

    # --- observations (cursor pagination) ---
    traces = {}
    obs_total = 0
    cursor = None
    while True:
        q = {
            "limit": 100,
            "fields": "core,basic,usage,metadata,io",
            "fromStartTime": from_ts,
            "toStartTime": to_ts,
        }
        if cursor:
            q["cursor"] = cursor
        page = get("/api/public/v2/observations?" + urllib.parse.urlencode(q))
        for o in page.get("data", []):
            obs_total += 1
            t = traces.setdefault(
                o["traceId"],
                {
                    "traceId": o["traceId"],
                    "startTime": o.get("startTime"),
                    "sessionId": o.get("sessionId"),
                    "run_id": None,
                    "agent_id": None,
                    "task_id": None,
                    "accepted_outcome_id": None,
                    "obs_by_type": Counter(),
                    "models": Counter(),
                    "has_error": False,
                    "input_usage": 0,
                    "output_usage": 0,
                    "total_usage": 0,
                    "other_usage_details": Counter(),
                    "total_cost": None,
                    "cost_measured": False,
                },
            )
            if o.get("startTime") and (t["startTime"] is None or o["startTime"] < t["startTime"]):
                t["startTime"] = o["startTime"]
            t["obs_by_type"][o.get("type")] += 1
            if o.get("level") == "ERROR":
                t["has_error"] = True
            if o.get("type") == "GENERATION" and o.get("modelId"):
                t["models"][o["modelId"]] += 1
            t["input_usage"] += o.get("inputUsage") or 0
            t["output_usage"] += o.get("outputUsage") or 0
            t["total_usage"] += o.get("totalUsage") or 0
            for k, v in (o.get("usageDetails") or {}).items():
                if k not in ("input", "output", "total") and isinstance(v, (int, float)):
                    t["other_usage_details"][k] += v
            if o.get("totalCost") is not None:
                t["cost_measured"] = True
                t["total_cost"] = (t["total_cost"] or 0.0) + o["totalCost"]
            if o.get("isRootObservation"):
                md = o.get("metadata") or {}
                for f in ("run_id", "agent_id", "task_id", "accepted_outcome_id"):
                    if md.get(f):
                        t[f] = md[f]
        cursor = (page.get("meta") or {}).get("cursor")
        if not cursor:
            break

    # --- scores: v3 list rows carry no traceId, so fetch one descending
    # list and join on timestamp == trace startTime (a trace score's
    # timestamp equals its trace startTime; verified 2026-11-06 on
    # 867dd7a5fea644a337290e34ee448007 and 407e7de7d22b5f76c62848e392d2e2ca).
    # One list fetch keeps request volume low: per-trace fetching hit
    # HTTP 429 on 2026-11-06. Stop paging once rows are older than the
    # window (list is newest-first). If two traces share a startTime the
    # join is ambiguous and reported as such, never guessed.
    scores_by_ts = defaultdict(dict)
    cursor = None
    pages = 0
    done = False
    while not done and pages < 20:
        q = {"limit": 100}
        if cursor:
            q["cursor"] = cursor
        page = get("/api/public/v3/scores?" + urllib.parse.urlencode(q))
        pages += 1
        rows_page = page.get("data", [])
        if not rows_page:
            break
        for s in rows_page:
            ts = s.get("timestamp")
            if ts and ts >= from_ts:
                scores_by_ts[ts][s.get("name")] = s.get("value")
        if all((s.get("timestamp") or "") < from_ts for s in rows_page):
            done = True
        cursor = (page.get("meta") or {}).get("cursor")
        if not cursor:
            break
    scores = {}
    for tid, t in traces.items():
        st = t["startTime"]
        n_same_ts = sum(1 for u in traces.values() if u["startTime"] == st)
        if n_same_ts > 1:
            scores[tid] = {"_ambiguous_timestamp_join": True}
        else:
            scores[tid] = scores_by_ts.get(st, {})

    rows = []
    for tid, t in sorted(traces.items(), key=lambda kv: kv[1]["startTime"] or ""):
        sc = scores.get(tid, {})
        ambiguous = bool(sc.pop("_ambiguous_timestamp_join", False))
        ad = sc.get("artifact_delivered")
        row = {
            "traceId": tid,
            "startTime": t["startTime"],
            "sessionId": t["sessionId"],
            "run_id": t["run_id"],
            "agent_id": t["agent_id"],
            "task_id": t["task_id"],
            "accepted_outcome_id": t["accepted_outcome_id"],
            "obs_by_type": dict(t["obs_by_type"]),
            "models": dict(t["models"]),
            "has_error": t["has_error"],
            "input_usage": t["input_usage"],
            "output_usage": t["output_usage"],
            "total_usage": t["total_usage"],
            "other_usage_details": dict(t["other_usage_details"]),
            "total_cost_usd": t["total_cost"],
            "cost_measured": t["cost_measured"],
            "scores": sc,
            "scores_join_ambiguous": ambiguous,
            "accepted": (ad == 1) if not ambiguous else None,
            # failed = no accepted output. An ERROR span alone is NOT a
            # failed run: a trace can carry ERROR spans (e.g. a wedged
            # renderer that was recovered) and still deliver its artifact.
            # has_error stays its own signal above.
            "failed": (ad == 0) if (not ambiguous and sc) else None,
            "accepted_output_null": (
                (sc.get("artifact_count") == 0) if (not ambiguous and sc) else None
            ),
            "scores_missing": (not sc) if not ambiguous else None,
        }
        rows.append(row)

    summary = {
        "window": {"from": from_ts, "to": to_ts},
        "observations": obs_total,
        "traces": len(rows),
        "generations": sum(r["obs_by_type"].get("GENERATION", 0) for r in rows),
        "traces_with_generation": sum(1 for r in rows if r["obs_by_type"].get("GENERATION")),
        "traces_with_cost_measured": sum(1 for r in rows if r["cost_measured"]),
        "total_input_usage": sum(r["input_usage"] for r in rows),
        "total_output_usage": sum(r["output_usage"] for r in rows),
        "total_usage": sum(r["total_usage"] for r in rows),
        "total_cost_usd": (
            sum(r["total_cost_usd"] for r in rows if r["total_cost_usd"] is not None)
            if any(r["cost_measured"] for r in rows)
            else None
        ),
        "accepted_traces": sum(1 for r in rows if r["accepted"]),
        "failed_traces": sum(1 for r in rows if r["failed"]),
        "accepted_output_null_traces": sum(
            1 for r in rows if r["accepted_output_null"]
        ),
        "error_span_traces": sum(1 for r in rows if r["has_error"]),
        "scores_missing_traces": sum(1 for r in rows if r["scores_missing"]),
        "traces_with_run_id": sum(1 for r in rows if r["run_id"]),
        "traces_with_agent_id": sum(1 for r in rows if r["agent_id"]),
        "traces_with_task_id": sum(1 for r in rows if r["task_id"]),
        "traces_with_accepted_outcome_id": sum(
            1 for r in rows if r["accepted_outcome_id"]
        ),
        "not_countable": [
            "Grok Bot / Cursor official usage (never converted to own tokens or cost)",
            "Any worker that never emits to Langfuse (no generation observation exists)",
            "Traces with total_cost null (cost unmeasured, not zero)",
        ],
    }
    print(json.dumps({"summary": summary, "traces": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
