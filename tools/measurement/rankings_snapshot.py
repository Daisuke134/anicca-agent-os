#!/usr/bin/env python3
"""Build rankings-latest.json from the measurement ledger's newest rows.

This file is the defined input for the /open dashboard build: the dashboard
loop copies this object into data.json as the `rankings` section. Numbers
and dates only; null where a surface has never been measured. The ledger
(measurement-ledger.jsonl) stays the single primary input — this snapshot
is derived from it on every run, never edited by hand.
"""
import json, os, datetime

LEDGER = os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl")
OUT = os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/rankings-latest.json")

def main():
    rows = []
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    def latest_batch(rtype, keyfn):
        sel = [r for r in rows if r.get("type") == rtype and "error" not in r]
        if not sel:
            return None, {}
        ts = max(r["ts"] for r in sel)
        return ts, {keyfn(r): r for r in sel if r["ts"] == ts}

    snap = {"updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    ts, batch = latest_batch("aso", lambda r: (r["country"], r["keyword"]))
    aso = {}
    for (country, kw), r in batch.items():
        aso.setdefault(country, {})[kw] = {"anicca": r.get("pos_anicca"),
                                          "iam": r.get("pos_iam"),
                                          "top1": r.get("top1")}
    snap["aso"] = {"measured_at": ts, "markets": aso} if ts else None

    ts, batch = latest_batch("seo_bing", lambda r: r.get("keyword") or r.get("query"))
    snap["seo_bing"] = {"measured_at": ts,
                        "positions": {kw: r.get("positions") for kw, r in batch.items()}} if ts else None

    # Google: merge the every-run core set (seo_google, 7 queries) with the
    # daily expanded sweep (seo_google_daily, 100 queries from
    # google-queries-expanded.json). Per keyword, the freshest row wins.
    g_rows = [r for r in rows if r.get("type") in ("seo_google", "seo_google_daily") and "error" not in r]
    if g_rows:
        merged = {}
        for r in g_rows:
            kw = r.get("keyword") or r.get("query")
            if kw and (kw not in merged or r["ts"] > merged[kw]["ts"]):
                merged[kw] = r
        snap["seo_google"] = {"measured_at": max(r["ts"] for r in merged.values()),
                              "queries_tracked": len(merged),
                              "positions": {kw: r.get("positions") for kw, r in merged.items()}}
    else:
        snap["seo_google"] = None

    # GEO (fixed 2026-11-15, denominator fix): the old logic took only the
    # single newest ts batch. baseline8 runs every 15 minutes while the
    # expanded sets (expanded100 + core16) run in chunks from a dedicated
    # loop, each chunk with its own ts — so the snapshot denominator was
    # structurally pinned at 8 no matter how much expanded data existed.
    # Now: per set, take the latest row per prompt_id and aggregate.
    # Denominator definitions follow anicca-ops
    # files/geo-scale-10000-spec-2026-11-14.md, amended 2026-11-19 by
    # files/geo-intents24-2026-11-19.md: total set = baseline8 (8) +
    # expanded100 (100) + core16 (16) + intents24 (24) = 148 prompts;
    # the suffering core frame is 59 = 19 ask-form prompts of
    # expanded100 (anxiety / low-self-esteem / negative-thoughts /
    # life-struggle categories) + the 16 core16 prompts + the 24
    # intents24 prompts (the principal's 6 intents x en/ja x ask/app;
    # before 2026-11-19 the frame was 35 and the total 124). Engine is
    # the Pollinations proxy (engine_kind=keyless-llm-api) — a proxy
    # sample, NOT ChatGPT / Perplexity answers (Gate GV-1).
    geo_rows = [r for r in rows if r.get("type") == "geo" and "error" not in r]
    if geo_rows:
        CORE19 = {"x021", "x022", "x023", "x024", "x025",
                  "x047", "x048", "x049", "x050", "x051",
                  "x060", "x061", "x062", "x063", "x064",
                  "x094", "x095", "x096", "x097"}
        SET_LABEL = {"core_suffering": "core16"}
        latest = {}
        for r in geo_rows:
            label = SET_LABEL.get(r.get("set"), r.get("set") or "baseline8")
            key = (label, r.get("prompt_id"))
            if key not in latest or r["ts"] > latest[key]["ts"]:
                latest[key] = r
        per_set = {}
        for (label, _pid), r in latest.items():
            st = per_set.setdefault(label, {"prompts": 0, "anicca_mentioned": 0,
                                            "anicca_cited": 0, "measured_at": r["ts"]})
            st["prompts"] += 1
            st["anicca_mentioned"] += 1 if r.get("anicca_mentioned") else 0
            st["anicca_cited"] += 1 if r.get("anicca_cited") else 0
            st["measured_at"] = max(st["measured_at"], r["ts"])
        all_latest = list(latest.values())
        core_frame = [r for (_label, pid), r in
                      ((k, v) for k, v in latest.items())
                      if pid in CORE19 or _label in ("core16", "intents24")]
        snap["geo"] = {"measured_at": max(r["ts"] for r in all_latest),
                       "engine": all_latest[0].get("engine"),
                       "engine_kind": all_latest[0].get("engine_kind"),
                       "model": all_latest[0].get("model"),
                       "prompts": len(all_latest),
                       "denominator_target": 148,
                       "anicca_mentioned": sum(1 for r in all_latest if r.get("anicca_mentioned")),
                       "anicca_cited": sum(1 for r in all_latest if r.get("anicca_cited")),
                       "per_set": per_set,
                       # Core frame renamed 35 -> 59 on 2026-11-19
                       # (intents24 added). "core_frame35" is kept as an
                       # alias of the same object so existing dashboard
                       # consumers that read the old key keep working.
                       "core_frame59": {"prompts": len(core_frame),
                                        "anicca_mentioned": sum(1 for r in core_frame if r.get("anicca_mentioned")),
                                        "anicca_cited": sum(1 for r in core_frame if r.get("anicca_cited"))},
                       "core_frame35": {"prompts": len(core_frame),
                                        "anicca_mentioned": sum(1 for r in core_frame if r.get("anicca_mentioned")),
                                        "anicca_cited": sum(1 for r in core_frame if r.get("anicca_cited"))},
                       "per_prompt": {r["prompt_id"]: {"mentioned": r.get("anicca_mentioned"),
                                                       "rank": r.get("anicca_rank"),
                                                       "cited": r.get("anicca_cited"),
                                                       "set": SET_LABEL.get(r.get("set"), r.get("set"))}
                                      for r in all_latest}}
    else:
        snap["geo"] = None

    with open(OUT, "w") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)
    print(f"rankings snapshot written: {OUT}")
    print(json.dumps({k: (v if k == 'updated_at' else ('set' if v else None))
                      for k, v in snap.items()}, ensure_ascii=False))

if __name__ == "__main__":
    main()
