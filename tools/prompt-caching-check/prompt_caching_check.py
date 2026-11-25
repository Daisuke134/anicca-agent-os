#!/usr/bin/env python3
"""prompt-caching-check: deterministic gate for the PROMPT CACHING surface
(structuring reusable prompt prefixes so provider caches are actually read:
stable content first, dynamic content after the breakpoint, TTL matched to
reuse interval, break-even checked, cache usage fields measured).
Stdlib only, offline.
Canonical source (read in full 2026-11-18 via the docs mirror at
https://docs.aihubmix.com/en/api/Claude-Cache , 371 lines, reproducing
Anthropic's Claude Platform prompt caching docs; corroborated by
coremesh.online checked against the official docs 2026-10-24):
- A cache hit requires the breakpoint and everything before it, in
  tools -> system -> messages order, to be byte-for-byte identical; one
  changed character invalidates and rewrites the whole prefix.
- The most common failure is writing the cache but never reading it:
  cache_creation_input_tokens large while cache_read_input_tokens stays 0,
  caused by changing content placed before the breakpoint.
- Place static content (tool definitions, system instructions, context,
  examples) at the beginning; put the per-turn question after the
  breakpoint; in multi-turn conversations only append, never edit earlier
  messages; thinking blocks from earlier turns must be passed back verbatim.
- Up to 4 cache breakpoints per request; each caches a different reusable
  section separately; the longest matching prefix is used. Automatic
  caching (top-level cache_control) places the breakpoint on the last
  cacheable block and moves it forward as the conversation grows.
- Minimum cacheable length varies by model (512 to 4,096 tokens); shorter
  prefixes are processed without caching even when marked.
- Lifetimes: 5 minutes by default, refreshed free on each use; 1-hour via
  ttl="1h". Pricing: 5m writes 1.25x base input, 1h writes 2x, reads 0.1x.
  Anthropic pricing guidance: the 5-minute cache pays off after one read,
  the 1-hour cache after two reads. Use 1h for batch processing, long
  sessions, large-document analysis and codebase Q&A with gaps over 5 min.
- Track performance with usage.cache_creation_input_tokens,
  usage.cache_read_input_tokens and usage.input_tokens; regularly analyze
  hit rates and adjust strategy.
- Troubleshooting: identical cached sections and breakpoint locations
  across calls, calls within the cache lifetime, consistent tool_choice
  and image usage, at least the minimum tokens.
- A cache entry becomes available only after the first response begins;
  for parallel requests needing hits, wait for the first response first.
- Caches are isolated between organizations (and per workspace on the
  Claude API); exact matching only; caching does not change outputs.
- OpenAI caching is automatic for prefixes of 1,024+ tokens (no explicit
  breakpoints on older models); DeepSeek and Gemini have their own native
  / implicit forms - provider differences must be handled explicitly.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PC-0 the prompt-caching surface is not recorded as a decided surface - whether reusable prefixes are cached at all is left to each call site / harness default")
    if not dec.get("owner_recorded"): f.append("PC-0 no owner is recorded for caching economics (write premiums paid vs reads gained) - cache waste has no accountable reader")
    if not dec.get("call_surface_inventory_classified"): f.append("PC-0 there is no inventory classifying each LLM call surface by prefix stability and reuse interval - cacheable and uncacheable surfaces are indistinguishable")
    pre=d.get("prefix_design") or {}
    if not pre.get("stable_content_first"): f.append("PC-1 prompts are not ordered stable-first (tool definitions, system instructions, background, examples before anything that changes) - the cacheable prefix is not the longest reusable prefix")
    if not pre.get("dynamic_content_after_breakpoint"): f.append("PC-1 dynamic content (timestamps, request IDs, per-turn questions, fresh retrieval) is not kept after the breakpoint / at the end - one changed character before the breakpoint invalidates and rewrites the whole prefix every call")
    if not pre.get("breakpoints_strategic_max4"): f.append("PC-1 cache breakpoints are not placed strategically (up to 4, separating sections with different change rates; or automatic caching deliberately chosen for rolling multi-turn conversations) - differently-lived sections share one invalidation fate")
    eco=d.get("economics") or {}
    if not eco.get("minimum_threshold_verified"): f.append("PC-2 the minimum cacheable length for the model in use (512-4,096 tokens by model) is not verified per surface - short prefixes are marked, never cached, and the miss is silent")
    if not eco.get("ttl_matched_to_reuse_interval"): f.append("PC-2 TTL is not matched to the measured reuse interval (5-minute default refreshed free on use; 1-hour for gaps between 5 minutes and an hour, batch work and long sessions) - entries expire between reuses or the 2x write premium is paid for traffic the 5-minute cache would have held")
    if not eco.get("breakeven_checked_before_caching"): f.append("PC-2 break-even is not checked before caching a prefix (5-minute writes at 1.25x pay off after one read; 1-hour writes at 2x after two reads) - prefixes written once and rarely read cost more than no caching")
    mea=d.get("measurement") or {}
    if not mea.get("usage_fields_tracked"): f.append("PC-3 cache usage fields (cache_creation_input_tokens, cache_read_input_tokens, input_tokens) are not tracked per call surface - caching is asserted, not measured")
    if not mea.get("hit_rate_computed_and_reviewed"): f.append("PC-3 the cache hit rate (cache reads over total input) is not computed and reviewed regularly with strategy adjusted from it - a silently zero hit rate can run indefinitely")
    if not mea.get("write_without_read_alerted"): f.append("PC-3 the write-but-never-read failure (large cache_creation with cache_read at 0) is not alerted on - the single most common caching failure has no detector")
    inv=d.get("invalidation_control") or {}
    if not inv.get("prefix_change_control"): f.append("PC-4 changes to cached prefix content (system prompt, tool definitions, skill lists and their order, examples) are not treated as cache-invalidating changes and versioned as such - a prompt edit silently resets every hit rate downstream")
    if not inv.get("consistency_of_tool_choice_and_images"): f.append("PC-4 tool_choice, image usage and breakpoint locations are not held consistent across calls sharing a prefix - troubleshooting's basic consistency checks have no owner")
    if not inv.get("concurrency_warmup_handled"): f.append("PC-4 parallel fan-out does not account for a cache entry becoming available only after the first response begins - parallel workers each pay a full write for the same prefix")
    mai=d.get("maintenance") or {}
    if not mai.get("strategy_per_use_case"): f.append("PC-5 there is no per-use-case caching strategy (conversational agents, coding/codebase Q&A, large-document processing, detailed instruction sets with many examples, agentic tool use) - one accidental shape serves every workload")
    if not mai.get("hit_rate_tuning_iterated"): f.append("PC-5 hit rates are not used to iterate the strategy (breakpoint placement, TTL choice, prefix ordering re-checked after prompt or model changes) - the caching shape is frozen at first build")
    if not mai.get("provider_differences_handled"): f.append("PC-5 provider differences are not handled explicitly (Anthropic explicit breakpoints vs OpenAI automatic caching vs other providers' native/implicit forms; organization/workspace isolation; exact-match only) - a strategy tuned for one provider is silently assumed on another")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
