#!/usr/bin/env python3
"""compaction-check: deterministic gate for the CONTEXT SHRINKING surface
(how a long-running agent reduces its own context inside a session:
tool-result clearing first, then summary compaction, with preserve lists,
recall-first tuning, measured loss, and cache cost accounted).
Stdlib only, offline.
Canonical sources (read in full 2026-11-18):
- Anthropic "Effective context engineering for AI agents"
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  (2025-09-29, updated 2026-10-18, 228 lines read in full):
  context rot and the finite attention budget; compaction = summarize a
  window nearing the limit and reinitiate from the summary, preserving
  architectural decisions, unresolved bugs and implementation details
  while discarding redundant tool outputs, continuing with the summary
  plus the five most recently accessed files; tune the compaction prompt
  on complex traces maximizing recall first, then precision; tool-result
  clearing is the safest, lightest-touch form of compaction.
- Anthropic Claude Platform context management docs, as corroborated by
  full-text secondary reads of the docs (ssdnodes / nodeflare / voxlang
  research, 2026): clearing (clear_tool_uses_20250919, beta header
  context-management-2025-06-27) deletes old tool results in place with
  no LLM call - trigger defaults to 100,000 input tokens, keep defaults
  to the last 3 tool uses, clear_tool_inputs defaults to false (results
  only, calls stay visible), clear_at_least aborts the edit when too
  little is reclaimable, exclusions keep named tools' results; clearing
  invalidates the cached prefix from the clearing point onward.
  Compaction (compact_20260112, beta header compact-2026-01-12) is one
  LLM call that replaces the transcript with a summary returned as a
  compaction content block which must be preserved and passed back;
  trigger minimum 50K, widely cited default 150K; on-demand compaction
  (compact-2026-09-04) lets the application decide when, returns the
  summary block alone, and the block must be sent back exactly as
  returned, signature included, with the beta header kept on every
  request carrying it. Measured caveat from independent runs of the
  same primitives: compaction preserved high-level facts but lost
  obscure specifics (identifiers among lookalikes survived 0/3 runs
  with the default prompt, 3/3 when instructions named them); a too-low
  clearing trigger (30K, 18 clears) cost more than doing nothing
  because every clear breaks the cache.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CP-0 the context-shrinking surface is not recorded as a decided surface - whether long sessions clear or compact at all is left to harness defaults nobody chose")
    if not dec.get("owner_recorded"): f.append("CP-0 no owner is recorded for shrinking quality (what survives a summary, what a clear may delete) - silent context loss has no accountable reader")
    if not dec.get("long_surface_inventory_classified"): f.append("CP-0 there is no inventory classifying each long-running surface by expected length and its shrink strategy - surfaces that will hit the window are indistinguishable from short ones")
    mec=d.get("mechanism_choice") or {}
    if not mec.get("clearing_before_compaction"): f.append("CP-1 the lightest lever is not first: old tool results are not cleared before a full summary compaction is considered - the safest, cheapest shrink is skipped for the lossiest one")
    if not mec.get("mechanisms_distinguished_by_task"): f.append("CP-1 clearing, compaction, structured note-taking and sub-agent isolation are not distinguished by task type (flow / milestones / parallel exploration) - the four levers are treated as interchangeable")
    if not mec.get("preserve_list_defined"): f.append("CP-1 no preserve list is defined per surface (decisions, unresolved issues, identifiers, implementation details that a summary must keep) - what survives shrinking is decided by a default prompt nobody tuned")
    clr=d.get("clearing") or {}
    if not clr.get("trigger_and_keep_set_from_traces"): f.append("CP-2 the clearing trigger and keep count are not set from measured traces (defaults are 100K input tokens / keep last 3 tool uses) - an untested trigger either never fires or fires constantly")
    if not clr.get("clear_at_least_set"): f.append("CP-2 clear_at_least is not set - clears that reclaim too little still pay the full cache-invalidation cost, and a too-low trigger can cost more than doing nothing")
    if not clr.get("exclusions_and_inputs_choice_deliberate"): f.append("CP-2 exclusions (results that must never be cleared) and the inputs-vs-results choice (clear_tool_inputs, default results only) are not decided deliberately - a later turn can lose a result it still needs, or keep inputs nobody re-reads")
    cmp_=d.get("compaction") or {}
    if not cmp_.get("trigger_set_not_only_hard_limit"): f.append("CP-3 the compaction trigger is not set (threshold, minimum 50K, or an explicit on-demand decision point) - shrinking happens only as an emergency at the hard window limit, mid-task")
    if not cmp_.get("summary_instructions_name_preserve_items"): f.append("CP-3 the summary instructions do not name the items to preserve (including identifiers and unresolved state) - measured runs lose obscure specifics under the default prompt that named instructions keep")
    if not cmp_.get("compaction_block_carried_correctly"): f.append("CP-3 the compaction block is not preserved and passed back exactly as returned (signature included, beta header kept on carrying requests, recent files carried alongside) - the handoff rule that quietly breaks agents has no owner")
    tun=d.get("tuning_and_loss") or {}
    if not tun.get("recall_first_tuning_on_real_traces"): f.append("CP-4 the compaction prompt is not tuned on real complex traces recall-first, then precision - the one tuning order the primary source prescribes is untested on the surfaces that actually shrink")
    if not tun.get("post_shrink_loss_measured"): f.append("CP-4 post-shrink loss is not measured (fact and identifier survival checks after clearing / compaction on real traces) - context loss is asserted away, not measured")
    if not tun.get("cache_cost_of_shrinking_accounted"): f.append("CP-4 the cache cost of shrinking is not accounted (every clear invalidates the cached prefix from that point; compaction rewrites the window) - shrink frequency is tuned blind to the write premiums it triggers")
    ops=d.get("operations") or {}
    if not ops.get("fresh_start_for_unrelated_tasks"): f.append("CP-5 unrelated tasks do not start fresh - compacting an unrelated history carries stale material into new work instead of starting from an empty window")
    if not ops.get("shrink_events_logged_with_token_counts"): f.append("CP-5 shrink events are not logged per surface with before/after token counts - nobody can tell how often shrinking fires, what it reclaims, or what it costs")
    if not ops.get("combined_with_notes_and_subagents"): f.append("CP-5 shrinking is not composed with outside-window notes and sub-agent isolation for long tasks - a single lever is expected to carry every long-horizon shape")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
