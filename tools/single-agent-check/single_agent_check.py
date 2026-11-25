#!/usr/bin/env python3
"""single-agent-check: deterministic gate for the SINGLE-AGENT LOOP /
FOLD-SUBAGENTS surface (when a specialist subagent should be folded back
into one main agent loop as skills + tools, and when it should be kept).
Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic / Claude,
"Building agents: When to fold subagents into your main agent loop",
Diane Sarkis, Applied AI team, published 2026-10-22,
https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop,
250 lines read via browser.open):
- Finding: across several enterprise deployments, a single agent with
  skills frequently outperformed both the one-prompt-for-everything
  design and the subagent design on quality, and often at lower cost
  and latency per task; one customer saw roughly 2x faster runtime with
  a single loop; Claude Code's system prompt for advanced models was
  cut by over 80%, partly via progressive disclosure of skills/tools.
- Keep a subagent only when: (1) measurable performance degradation
  from context bloat, (2) parallel work in fresh context windows that
  can be discarded, or (3) the single agent struggles to select tools
  or instructions conflict. Divide by context, not by problem type or
  org chart (Conway's law / subagent sprawl / Frankenprompt).
- Target shape: one model, one context window, open-ended tool loop,
  harness limits (turn/cost budgets, write gates); the model writes
  its plan in context and revises it; procedure moves into skills,
  hard limits and mid-conversation needs move into tools; shared
  context stays in the main window instead of lossy handoffs.
- Progressive disclosure: short descriptions first, skills loaded via
  skills and tools via tool search only when needed; tools grouped by
  user intent (tool choice degrades past ~30-50 definitions in the
  prompt); knowledge bases behind search/lookup, not code-pasted.
- Migration: build a small end-to-end eval first (even ~10 golden
  examples; one shared E2E set owned by a small central team, smaller
  evals shipped with each skill); merge specialists that chain on each
  other's output / share data / are called together; call kept
  subagents as tools before any full handoff; fold one subagent at a
  time (prompt -> skill, API calls -> tools), compare with and without,
  inspect which tasks flipped (not just the final score), run each
  task more than once, and keep a subagent only if the folded version
  scores worse.
- Contribution: teams shift ownership from agents to skills/tools;
  one small central team owns the system prompt and end-to-end quality
  and vets new skills/tools/evals; DRI per skill; prune the library
  (skill-doctor: cost/usage, delete dead weight); prompt-audit removes
  instructions written for older models; hillclimb / cost-optimize
  change one thing at a time. Principle: measure, change one thing at
  a time, keep what holds up.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("SA-0 the single-agent-loop surface is not recorded as a decided surface - when to fold a subagent into the main loop versus keep it is left to per-team habit")
    if not dec.get("central_owner_recorded"): f.append("SA-0 no small central owner is recorded for the system prompt and end-to-end quality - every team adds sentences and evals, producing the Frankenprompt and unvetted localized evals")
    if not dec.get("subagent_inventory_with_verdicts"): f.append("SA-0 there is no inventory of subagents with a verdict per subagent (fold / merge / call as a tool / keep) - sprawl is invisible and no migration order exists")
    keep=d.get("keep_conditions") or {}
    if not keep.get("keep_only_on_measurable_evidence"): f.append("SA-1 subagents are not kept only on measurable evidence (context-bloat degradation, parallel fresh-context need, or tool-selection struggle / conflicting instructions) - a subagent exists because a team or problem type wanted one")
    if not keep.get("divide_by_context_not_problem_type"): f.append("SA-1 work is divided by problem type / org chart instead of by context (each subagent gets work needing little from the rest of the system and hands back a compact result) - split-by-problem agents play telephone and fidelity degrades at every handoff")
    if not keep.get("parallel_fresh_context_used"): f.append("SA-1 the legitimate parallel case is not actually used where it fits (independent paths run in parallel in fresh, discardable context windows) - the one measured benefit of subagents is left unused while their costs are paid elsewhere")
    dis=d.get("disclosure") or {}
    if not dis.get("progressive_disclosure_skills_tools"): f.append("SA-2 context and tools are not progressively disclosed (short descriptions first; skills and tool search load full content only when needed) - everything sits in one long system prompt, which is the bloat that forced splitting in the first place")
    if not dis.get("tools_grouped_by_intent_under_limit"): f.append("SA-2 tools are not grouped by user intent with the in-prompt definition count kept under the ~30-50 range where tool choice degrades - one tool per API, all preloaded")
    if not dis.get("knowledge_behind_search_not_pasted"): f.append("SA-2 reference material is code-retrieved and pasted into prompts instead of sitting behind a search/lookup tool or as reference files inside a skill - stale copies ride every prompt")
    loop=d.get("loop_shape") or {}
    if not loop.get("one_model_one_context_open_loop"): f.append("SA-3 the target shape is not one model and one context window running an open-ended tool loop - the model that writes the plan is not the one carrying it out, so plans cannot be revised mid-turn")
    if not loop.get("harness_limits_write_gates"): f.append("SA-3 harness limits are not set (turn and cost budgets, write / approval gates in the harness, not in prompt prose) - a single loop without firm limits is unbounded")
    if not loop.get("plan_in_context_revised_shared_context_kept"): f.append("SA-3 the model does not write and revise its plan in context while earlier results stay in the main window - folded work still returns as lossy summaries and the shared-context advantage is lost")
    mig=d.get("migration_eval") or {}
    if not mig.get("small_e2e_eval_before_folding"): f.append("SA-4 no small end-to-end eval exists before folding (even ~10 golden examples; one shared E2E set owned centrally plus smaller evals shipped with each skill) - fold/keep decisions are made on vibes")
    if not mig.get("fold_one_at_a_time_compare"): f.append("SA-4 subagents are not folded one at a time (prompt becomes a skill, API calls become tools) with a with/without eval comparison per fold - big-bang rewrites cannot attribute a regression to a fold")
    if not mig.get("flipped_tasks_inspected_and_tasks_run_multiple_times"): f.append("SA-4 comparisons read only the final score and run each task once - the source's own case (a fold that lowered latency but broke a passing process, visible in one run out of two) is exactly what this misses; flipped tasks and must-not-break rules are not inspected")
    mnt=d.get("maintenance") or {}
    if not mnt.get("teams_own_skills_tools_vetted"): f.append("SA-5 teams still own agents instead of skills and tools, with no central vetting before a new skill/tool/eval ships - ownership stays Conway-shaped and quality has no gate")
    if not mnt.get("skill_dri_and_pruning_by_cost_usage"): f.append("SA-5 skills have no DRI per team and the library is not pruned by cost and actual usage (skill-doctor style: delete dead weight, deduplicate) - skill sprawl replaces subagent sprawl")
    if not mnt.get("prompt_audit_and_one_change_at_a_time"): f.append("SA-5 prompts are not audited for instructions written for older models, and improvements are not made one change at a time against the eval (measure, change one thing, keep what holds up) - rigid harness rules written for weaker models keep taxing stronger ones")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
