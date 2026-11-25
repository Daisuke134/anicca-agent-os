#!/usr/bin/env python3
"""GEO probe via Pollinations text API (free, no API key).

Why this route: citeshine-audit (OSS, ~/.local/share/citeshine-audit/) needs
an LLM API key for every API engine, and its web engines need a live Chrome
(CDP) session. This VM has no LLM API keys. Pollinations
(https://text.pollinations.ai/openai) is a free keyless LLM endpoint that
answers from this VM today, so GEO measurement runs NOW instead of waiting
for a key. Prompts, brand and competitor sets are read from the citeshine
config (configs/anicca.json) so the prompt set stays identical across
engines; matching follows citeshine's method (case-insensitive substring
match on name + aliases + domain). Engine is recorded in every row: these
are keyless-LLM answers, NOT ChatGPT/Perplexity web answers, and must not
be reported as such.

Appends one JSONL row per prompt (type=geo) to the shared ledger and the
full raw answers to out/geo-raw.jsonl.

Cache bypass (added 2026-11-06, Todo item 40 prerequisite fix): until
2026-11-05T05:21Z every prompt's answer had been byte-identical for
124-146 consecutive runs — Pollinations was serving a cached answer for
the identical request body, so the loop could not detect any GEO change.
A probe with a random `seed` + `private=true` returned a different
answer (see hidden_files/geo-item40-inventory-2026-11-06.md §1). Every
request now carries a fresh random seed and private=true, and both
values are recorded in the ledger and raw rows so each run is auditable.
The 8 prompt texts themselves are unchanged.

Prompt-set expansion (2026-11-12, on the principal's direct point that a
denominator of 8 is too small): the original 8 citeshine prompts are all
recommendation-form and stay untouched as set=baseline8. A second set of
100 prompts (geo-prompts-expanded.json next to this script: 8 categories x
recommend/consult phrasings, en+ja) is measured as set=expanded100. Every
ledger and raw row carries its set label. --set baseline8 | expanded100 |
core16 | intents24 | both | all selects the sets (all = baseline8 +
expanded100 + core16 + intents24, 148 prompts); the DEFAULT is baseline8
so existing no-arg callers (the 15-minute measurement loop) keep the
exact original behaviour.

Denominator fix (2026-11-15): the opt-in design above is exactly why the
denominator stayed 8 for three days — the 2026-11-14 scale-up spec wired
the sets into this script but never into any schedule, and spec section 5
left the expanded sets as "manual reruns". The expanded sets now run in a
dedicated cron (anicca-geo-expanded-loop) that is separate from the
15-minute loop: at ~55s/prompt (2026-11-12 measurement) 116 expanded
prompts take ~106 minutes and can never fit the 15-minute loop's 1500s
budget (the 2026-11-12 combined run was SIGTERM-killed ~20 minutes in).
--offset/--limit slice the selected job list so the dedicated loop can
run the full expanded denominator in chunks that each fit one run, and
--sleep overrides the inter-prompt pause (default unchanged at 3s).
Per-prompt ledger appends (below) make chunked runs loss-free.

intents24 (2026-11-19, approved by Muse main; proposal in anicca-ops
files/geo-best-tool-2026-11-19.md, implementation record in
files/geo-intents24-2026-11-19.md): a fourth set of 24 prompts
(geo-prompts-intents.json next to this script) covering the principal's
6 intents (rumination / depression / OCD / hard day / hard life /
laziness) x en+ja x ask-form + app-form. OCD and laziness had zero
dedicated prompts in the older sets and hard day had no explicit form.
The total denominator is now 148 and the suffering core frame is 59
(expanded100 ask-form 19 + core16 16 + intents24 24; see
rankings_snapshot.py). The dedicated expanded loop runs intents24
alongside expanded100 + core16.

Model (2026-11-14): the requested model is "openai-fast" — measured the
same day, it is the ONLY model on the free anonymous Classic API and it is
the fast-mode model (GPT-OSS 20B). See the MODEL comment below and
anicca-ops files/geo-scale-10000-spec-2026-11-14.md for the engine/model
policy (frontier engines are the real target; this route is a proxy).

Ledger rows are appended per prompt (flushed as each answer lands) rather
than in one batch at the end: the 2026-11-12 first expanded run was killed
~20 minutes in and a batch-at-end design would have lost every row.
"""
import argparse, json, os, re, secrets, sys, time, urllib.parse, urllib.request, datetime

CONFIG = os.path.expanduser("~/.local/share/citeshine-audit/configs/anicca.json")
LEDGER = os.path.expanduser("~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl")
RAW = os.path.expanduser("~/workspace/tools/measurement/out/geo-raw.jsonl")
EXPANDED = os.path.expanduser("~/workspace/tools/measurement/geo-prompts-expanded.json")
ENDPOINT = "https://text.pollinations.ai/openai"
CORE = os.path.expanduser("~/workspace/tools/measurement/geo-prompts-core.json")
INTENTS = os.path.expanduser("~/workspace/tools/measurement/geo-prompts-intents.json")
# Model choice (2026-11-14, on the principal's instruction to always ask the
# best model in fast mode): measured the same day, GET
# https://text.pollinations.ai/models on the anonymous Classic API returns
# exactly ONE model: "openai-fast" (GPT-OSS 20B Reasoning LLM, OVH; aliases
# include "openai"). Every other model name returns 404 "isn't on the
# Classic API ... Every model we offer is on https://enter.pollinations.ai"
# (the account/credit platform). So on this free keyless route the best --
# and only -- model IS the fast one, and it is named explicitly here instead
# of via its "openai" alias. It remains a small open-weight proxy sample,
# NOT a frontier engine (ChatGPT/Perplexity/Claude/Grok); ledger rows keep
# engine_kind=keyless-llm-api and record both the requested model and the
# model name the endpoint reports back.
MODEL = "openai-fast"

def ask(prompt):
    # Repaired 2026-11-06 (fix-now): the old 3-attempt version kept producing
    # error rows (IncompleteRead / Remote end closed) across 2026-11-05/06 and
    # each round was deferred as "Pollinations instability". Now: 6 attempts
    # with exponential backoff on the OpenAI endpoint, then a fallback to the
    # plain-text GET endpoint on the same service (recorded honestly in the
    # model field as "openai(get-fallback)"). An error row is the last resort.
    seed = secrets.randbelow(2_147_483_647)
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "private": True}).encode()
    last = None
    for attempt in range(6):
        try:
            req = urllib.request.Request(ENDPOINT, data=body, headers={
                "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            d = json.loads(raw.decode("utf-8"))
            return d["choices"][0]["message"]["content"], d.get("model", MODEL), seed
        except Exception as e:
            last = e
            time.sleep(min(60, 5 * (2 ** attempt)))
    try:
        q = urllib.parse.quote(prompt, safe="")
        req = urllib.request.Request(
            f"https://text.pollinations.ai/{q}?model=openai-fast&seed={seed}&private=true",
            headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            text = r.read().decode("utf-8", "replace")
        if text.strip():
            return text, "openai(get-fallback)", seed
    except Exception as e:
        last = e
    raise last

def first_pos(text_low, terms):
    best = None
    for t in terms:
        i = text_low.find(t.lower())
        if i >= 0 and (best is None or i < best):
            best = i
    return best

def main(args):
    cfg = json.load(open(CONFIG))
    brand = cfg["brand"]
    tracked = [(brand["name"], [brand["name"]] + brand.get("aliases", []) + [brand["domain"]])]
    for c in cfg["competitors"]:
        tracked.append((c["name"], [c["name"]] + c.get("aliases", [])))
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    jobs = []
    if args.set in ("baseline8", "both", "all"):
        jobs += [(p, "baseline8") for p in cfg["prompts"]]
    if args.set in ("expanded100", "both", "all"):
        exp = json.load(open(EXPANDED))
        jobs += [(p, "expanded100") for p in exp["prompts"]]
    if args.set in ("core16", "all"):
        core = json.load(open(CORE))
        jobs += [(p, core.get("set", "core_suffering")) for p in core["prompts"]]
    if args.set in ("intents24", "all"):
        intents = json.load(open(INTENTS))
        jobs += [(p, intents.get("set", "intents24")) for p in intents["prompts"]]
    if args.offset:
        jobs = jobs[args.offset:]
    if args.limit is not None:
        jobs = jobs[:args.limit]
    rows, mentioned, cited = [], 0, 0
    per_set = {}
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    for p, set_label in jobs:
        try:
            answer, model, seed = ask(p["text"])
        except Exception as e:
            rows.append({"type": "geo", "ts": ts, "engine": "pollinations",
                         "engine_kind": "keyless-llm-api", "model_requested": MODEL,
                         "prompt_id": p["id"], "set": set_label,
                         **({"core_type": p["core_type"]} if "core_type" in p else {}),
                         "lang": p["lang"], "prompt": p["text"], "error": str(e)})
            with open(LEDGER, "a") as f:
                f.write(json.dumps(rows[-1], ensure_ascii=False) + "\n")
            continue
        low = answer.lower()
        hits = []
        for name, terms in tracked:
            pos = first_pos(low, terms)
            if pos is not None:
                hits.append((pos, name))
        hits.sort()
        order = [n for _, n in hits]
        urls = re.findall(r"https?://([^/\s)\]]+)", answer)
        anicca_cited = any("aniccaai.com" in u for u in urls)
        is_mentioned = brand["name"] in order
        st = per_set.setdefault(set_label, [0, 0, 0])
        st[0] += 1
        if is_mentioned:
            mentioned += 1
            st[1] += 1
        if anicca_cited:
            cited += 1
            st[2] += 1
        rows.append({"type": "geo", "ts": ts, "engine": "pollinations",
                     "engine_kind": "keyless-llm-api", "model": model,
                     "model_requested": MODEL, "mode": "fast",
                     "cache_bypass": "seed+private", "seed": seed, "private": True,
                     "prompt_id": p["id"], "set": set_label,
                     **({"core_type": p["core_type"]} if "core_type" in p else {}),
                     "lang": p["lang"], "prompt": p["text"],
                     "anicca_mentioned": is_mentioned,
                     "anicca_rank": (order.index(brand["name"]) + 1) if is_mentioned else None,
                     "anicca_cited": anicca_cited,
                     "brands_in_order": order,
                     "cited_domains": sorted(set(urls))[:20],
                     "answer_chars": len(answer)})
        with open(LEDGER, "a") as f:
            f.write(json.dumps(rows[-1], ensure_ascii=False) + "\n")
        with open(RAW, "a") as f:
            f.write(json.dumps({"ts": ts, "engine": "pollinations", "model": model,
                                "cache_bypass": "seed+private", "seed": seed, "private": True,
                                "prompt_id": p["id"], "set": set_label, "prompt": p["text"],
                                "answer": answer}, ensure_ascii=False) + "\n")
        time.sleep(args.sleep)
    ok = [r for r in rows if "error" not in r]
    for label, (ans, men, cit) in per_set.items():
        print(f"geo pollinations [{label}]: {ans} prompts answered; "
              f"Anicca mentioned {men}/{ans}, cited {cit}/{ans}")
    print(f"geo pollinations [all]: {len(ok)}/{len(rows)} prompts answered; "
          f"Anicca mentioned {mentioned}/{len(ok)}, cited {cited}/{len(ok)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["baseline8", "expanded100", "core16", "intents24", "both", "all"], default="baseline8")
    ap.add_argument("--offset", type=int, default=0,
                    help="skip the first N jobs of the selected set (chunked runs)")
    ap.add_argument("--limit", type=int, default=None,
                    help="run at most N jobs after --offset (chunked runs)")
    ap.add_argument("--sleep", type=float, default=3.0,
                    help="seconds to pause between prompts (default 3)")
    main(ap.parse_args())
