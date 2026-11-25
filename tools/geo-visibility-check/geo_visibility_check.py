#!/usr/bin/env python3
"""geo-visibility-check: deterministic gate for AI-search (GEO) visibility measurement.
Stdlib only, offline, free. Sources (full read 2026-11-14):
- CourtAvenue, Generative Engine Optimization: Enterprise GEO Guide
  https://www.courtavenue.com/news-and-insights/geo-for-enterprise-how-to-get-your-brand-cited-in-chatgpt-perplexity-and-google-ai-overviews
  Prompt set 50-150 real buyer questions; run across ChatGPT / Perplexity /
  Google AI Overviews / Gemini; repeat each prompt many times and track
  MENTION FREQUENCY, not a single 'AI rank' (SparkToro/Gumshoe Jan 2026: same
  question asked 100 times returns the same brand list <1 time in 100).
  Record mention frequency, cited-with-link, which URL, which competitors and
  third-party sources appear instead. KDD 2024 (Aggarwal et al.): quotations,
  statistics, cited sources each raised visibility ~30-41%. AI crawlers
  (GPTBot/ClaudeBot/PerplexityBot) do not execute JavaScript -> facts must be
  server-rendered. Google Search Central: llms.txt / AI markup NOT required;
  Ahrefs Jun 2026: 97% of llms.txt files got zero requests; schema showed no
  meaningful citation uplift -> neither counts as a GEO tactic here.
  Report alongside pipeline, not as a standalone mention count; change one
  variable at a time and re-measure.
- Okara, We Asked ChatGPT, Claude, Gemini and Perplexity 230 Buying Questions
  https://okara.ai/blog/ai-search-citation-study-2026
  Cross-engine cited-domain overlap only ~6% -> track each engine separately.
  ChatGPT cites vendor pages 52%; Claude/Gemini/Perplexity cite third-party
  roundups/comparisons 52-64% -> third-party presence is a separate surface.
  Same question twice: brands shared 62%, sources 41% -> single screenshots
  are not measurement. Fixed set 30-70+, rerun monthly.
In-house goal (user, 2026-11-12): the core frame is suffering consultations
('I feel depressed', 'I can't stop ruminating'), not app-shopping queries;
that frame is reported separately. Crisis-level queries are excluded from
the target frame (safety lines first is correct by design).
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    # GV-0 prompt set
    n = d.get("prompt_count") or 0
    if not d.get("prompt_set_recorded"):
        fails.append("GV-0 no fixed prompt set recorded (a wandering set cannot be re-measured)")
    if n < 50:
        fails.append(f"GV-0 prompt set has {n} prompts, below the 50 floor (CourtAvenue 50-150; Okara fixed set 30-70 is the absolute minimum band)")
    if d.get("prompts_brand_hinted"):
        fails.append("GV-0 prompts hint the brand name (measurement must be unprompted: the user does not name us to the AI)")
    if not d.get("suffering_core_split"):
        fails.append("GV-0 suffering-consultation core frame is not split and reported separately from app-shopping queries (house goal: the core is the suffering consultation itself)")
    if d.get("crisis_queries_targeted"):
        fails.append("GV-0 crisis-level queries are in the target frame (by house rule they are excluded: crisis lines surfacing first is correct safety design)")
    # GV-1 engines
    engines = d.get("engines_measured") or []
    if d.get("proxy_only"):
        fails.append("GV-1 measurement runs only through a proxy/free-relay model, not the real engines (a proxy result is a labelled sample, never the engines' answer)")
    if len(engines) < 3:
        fails.append(f"GV-1 only {len(engines)} engine(s) measured (cross-engine cited-domain overlap is ~6%: one engine says nothing about the others; minimum 3, target ChatGPT/Perplexity/Gemini/Claude or Grok)")
    if not d.get("per_engine_results_separate"):
        fails.append("GV-1 results are pooled across engines instead of reported per engine")
    # GV-2 repeats / frequency
    r = d.get("repeats_per_prompt") or 0
    if r < 3:
        fails.append(f"GV-2 repeats per prompt = {r} (single answers are snapshots: same question twice shares only 62% of brands / 41% of sources; the metric is mention frequency over >=3 repeats)")
    if d.get("metric") != "mention_frequency":
        fails.append(f"GV-2 metric is {d.get('metric')!r}, not mention_frequency (a single 'AI rank' or one screenshot measures noise)")
    # GV-3 per-answer record
    rec = d.get("per_answer_record") or {}
    for k, label in [("mentioned","brand mentioned"), ("cited_with_link","cited with link"), ("cited_url","which URL was cited"), ("competitors_named","which competitors were named instead"), ("third_party_sources","which third-party sources were cited")]:
        if rec.get(k) is not True:
            fails.append(f"GV-3 per-answer record is missing: {label}")
    # GV-4 site readiness for retrieval
    site = d.get("site") or {}
    if site.get("facts_server_rendered") is not True:
        fails.append("GV-4 key facts (what it is / who for / price) are not confirmed server-rendered (GPTBot, ClaudeBot and PerplexityBot do not execute JavaScript)")
    if site.get("claims_attributed") is not True:
        fails.append("GV-4 priority pages lack attributed statistics / quotations / cited sources (KDD 2024: each raised visibility ~30-41%)")
    if site.get("pages_dated") is not True:
        fails.append("GV-4 priority pages carry no visible publish/update dates (recency and topic match decide citation; undated pages lose)")
    if site.get("comparison_content") is not True:
        fails.append("GV-4 no honest comparison / 'best for' content (absent comparisons lost citations in SIGIR 2026 trials)")
    if site.get("llms_or_schema_counted_as_tactic"):
        fails.append("GV-4 llms.txt / schema is counted as a GEO tactic (Google: not required; Ahrefs: 97% of llms.txt got zero requests, schema showed no uplift — keep them as hygiene, never as the plan)")
    # GV-5 third-party surface
    tp = d.get("third_party") or {}
    if tp.get("cited_roundups_inventoried") is not True:
        fails.append("GV-5 the roundups/comparisons the engines actually cite are not inventoried (Claude/Gemini/Perplexity cite third-party lists 52-64% of the time)")
    if tp.get("presence_in_cited_roundups") is None:
        fails.append("GV-5 our presence in those cited roundups is not measured (named / not named, per source)")
    # GV-6 cadence & interpretation
    if not d.get("rerun_cadence"):
        fails.append("GV-6 no rerun cadence recorded for the full set (fixed set, rerun at least monthly; sources shift month to month)")
    elif d.get("rerun_cadence") not in ("weekly", "monthly"):
        warns.append(f"GV-6 rerun cadence is {d.get('rerun_cadence')!r}, slower than monthly")
    if d.get("reported_with_pipeline") is not True:
        fails.append("GV-6 results are reported as a standalone mention count, not alongside the funnel / pipeline (mentions that never reach the store are not yet value)")
    if d.get("one_variable_changes") is not True:
        fails.append("GV-6 fixes are not run one variable at a time with re-measurement (bundled changes cannot be attributed)")
    return fails, warns

def main():
    with open(sys.argv[1]) as fh:
        d = json.load(fh)
    fails, warns = check(d)
    for w in warns: print(f"WARN {w}")
    for f in fails: print(f"FAIL {f}")
    print(f"{'PASS' if not fails else 'FAIL'} {d.get('app','?')}: {len(fails)} fail(s), {len(warns)} warning(s)")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
