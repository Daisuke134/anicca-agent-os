#!/usr/bin/env python3
"""effort-check: deterministic gate for the EFFORT ALLOCATION surface
(how much work / token spend each LLM workload is assigned via the
effort parameter, how that assignment is measured, and how its
interactions with thinking, tool use and prompt caching are handled).
Stdlib only, offline.
Canonical source (read in full 2026-11-18):
- Anthropic Claude Platform Docs "Effort"
  https://platform.claude.com/docs/en/build-with-claude/effort
  (153 lines read in full): output_config.effort controls how many
  tokens Claude spends responding; one model trades thoroughness
  against token efficiency. Most models default to high; Opus 5.5
  and Haiku 5.5 default to medium. Levels: max (absolute maximum, no
  token constraint), xhigh (extended capability for long-horizon
  agentic/coding work over 30 minutes, budgets in the millions),
  high (default; complex reasoning, difficult coding, agentic),
  medium (balanced; agentic tasks balancing speed/cost/performance),
  low (most efficient, significant savings, some capability loss;
  simpler speed-sensitive tasks such as subagents). Not every model
  supporting max supports xhigh. Effort affects ALL output tokens -
  text, tool calls and arguments, and thinking when active - so it
  works with or without thinking; lower effort also means fewer,
  terser tool calls, combining operations, proceeding directly to
  action and terse confirmations, while higher effort explains plans,
  calls more tools and summarises in detail. thinking controls
  whether thinking blocks exist; effort controls how much work goes
  into the whole response and, in adaptive mode, how often/deeply it
  thinks - never pass "adaptive" as an effort value. At lower levels
  Claude can skip thinking for simpler problems; follow-up requests
  that only process tool results can skip thinking at any level.
  Effort is changed mid-conversation per-message (keeps the prompt
  cache) or top-level on the next request (can invalidate all or
  part of the cache because top-level effort shapes the rendered
  prompt); if a model lacks per-message effort and the session
  relies on caching, pick a level at the start and keep it constant.
  Best practices: set effort explicitly; use low for latency- or
  simplicity-bound work; test the impact on your own use cases
  before deploying because impact varies by task type; consider
  dynamic effort by task complexity, varied across workloads rather
  than within a cached conversation.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("EF-0 the effort-allocation surface is not recorded as a decided surface - how hard each workload thinks is left to API defaults and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("EF-0 no owner is recorded for effort economics and correctness (what each level costs, where quality dropped) - silent overspend and silent under-thinking have no accountable reader")
    if not dec.get("workload_inventory_classified_by_complexity"): f.append("EF-0 there is no inventory classifying each LLM workload by complexity and latency sensitivity - effort cannot be assigned per workload if workloads are indistinguishable")
    asg=d.get("assignment") or {}
    if not asg.get("effort_set_explicitly_per_workload"): f.append("EF-1 effort is not set explicitly per workload (output_config.effort) - the docs' first best practice is explicit setting, and the silent default is high on most models (medium only on Opus 5.5 / Haiku 5.5)")
    if not asg.get("low_assigned_to_simple_speed_sensitive"): f.append("EF-1 low effort is not assigned to the simple, speed-sensitive workloads it exists for (lookups, classification, routine subagent work) - those workloads pay high-effort token spend for no measured gain")
    if not asg.get("highest_levels_not_used_as_default"): f.append("EF-1 the highest levels (max / xhigh - unconstrained spend, or budgets in the millions for 30-minute-plus horizons) are not fenced off from default use - an unconstrained level as a routine default burns prepaid credit with no quality contract")
    cor=d.get("correctness") or {}
    if not cor.get("effort_treated_as_soft_signal_not_hard_budget"): f.append("EF-2 effort is treated as a hard token budget - it is a behavioural signal over all output tokens: even at low, a hard problem can still think, and the hard cap remains max_tokens; designs that rely on effort as a cap misprice and misjudge runs")
    if not cor.get("model_support_and_defaults_verified_per_model"): f.append("EF-2 supported levels and defaults are not verified per model (not every max model supports xhigh; defaults differ - high generally, medium on Opus 5.5 / Haiku 5.5) - a level copied across models can error or silently change spend")
    if not cor.get("thinking_and_effort_not_conflated"): f.append("EF-2 thinking and effort are conflated (adaptive passed as an effort value, or effort expected to switch thinking off) - adaptive is a thinking mode, not an effort level, and effort works with or without thinking")
    mea=d.get("measurement") or {}
    if not mea.get("effort_levels_evaluated_on_own_use_cases"): f.append("EF-3 effort levels are not evaluated on the team's own use cases before deployment - the docs warn impact varies by task type, so a level chosen from the table alone is unmeasured")
    if not mea.get("quality_cost_latency_measured_per_level"): f.append("EF-3 quality, cost and latency are not measured per effort level (thinking tokens are billed as output tokens, and effort moves all three) - there is no cost-per-successful-task by level to assign from")
    if not mea.get("dynamic_effort_by_complexity_considered"): f.append("EF-3 dynamic effort by task complexity is not implemented or explicitly ruled out (simple queries low, complex reasoning / agentic coding high) - one fixed level for every complexity is the unexamined middle the docs argue against")
    inter=d.get("interactions") or {}
    if not inter.get("effort_held_constant_in_cached_conversations"): f.append("EF-4 effort is varied top-level inside conversations that rely on prompt caching - changing the top-level value shapes the rendered prompt and can invalidate all or part of the cache; the cache-preserving route is a per-message change, or a level picked at the start and held constant")
    if not inter.get("tool_use_effect_accounted"): f.append("EF-4 the tool-use effect of effort is not accounted for (lower effort makes fewer, terser, combined tool calls and skips preamble; higher effort calls more tools and explains more) - lowering effort can silently drop tool steps a workflow depends on")
    if not inter.get("mid_conversation_change_method_chosen"): f.append("EF-4 no method is chosen for mid-conversation effort changes (per-message where supported, which keeps the cache, versus top-level on the next request, which may not) - changes are improvised per incident")
    ops=d.get("operations") or {}
    if not ops.get("effort_events_logged_with_tokens_and_latency"): f.append("EF-5 effort is not logged per workload with realised output / thinking tokens and latency - nobody can tell which level each run used, what it spent, or whether a quality drop followed a level change")
    if not ops.get("defaults_rechecked_on_model_change"): f.append("EF-5 effort defaults and supported levels are not rechecked when a model changes - a model swap silently changes the default (high vs medium) and the available levels under an unchanged configuration")
    if not ops.get("escalation_path_for_quality_failure_at_low_effort"): f.append("EF-5 there is no escalation path when a low-effort run under-thinks or drops quality (raise the level for that workload and record it) - failures at low effort are retried at the same level or blamed on the model")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
