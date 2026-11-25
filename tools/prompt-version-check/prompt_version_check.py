#!/usr/bin/env python3
"""prompt-version-check: deterministic gate for the PROMPT VERSIONING /
PROMPT MANAGEMENT surface (prompts treated as production code: versioned
as a whole bundle, reviewed, evaluated before promotion, rollback-ready).
Stdlib only, offline, free.
Canonical source (read in full 2026-11-18, Monte Carlo, "Prompt
Versioning: Why Your AI Prompts Need The Same Rigor As Your Code",
https://montecarlo.ai/blog-prompt-versioning-why-your-ai-prompts-need-the-same-rigor-as-your-code):
- A prompt is production code: versioned, reviewed, and evaluated before
  it ships. Versioning tracks every change with who / when / why, a
  snapshot of the exact text (system instructions, examples, formatting),
  and metadata linking the version to the model, parameters and eval
  results it was tested against.
- Use semantic versioning (major = breaking: new model / output schema,
  minor = new capability, patch = wording tweak). Control who can edit
  and deploy a live prompt.
- Version the WHOLE configuration, not just the text: wording + model
  version + sampling settings (temperature, top_p) + tool schemas move
  together as one versioned unit. Separate fixed template from variable
  runtime inputs.
- Treat prompts as code: store in the same repo, PR review, commit hash;
  keep prompt logic in separate files, not embedded strings; tag versions
  with intent labels (e.g. v4-reduced-verbosity).
- Run evaluations before promoting: same fixed set, baseline from the
  current version, compare quality / format / cost / latency, review
  failures. Keep production and experimental versions separate (staging).
- Rollback must restore the exact prior bundle in minutes. When the model
  changes, re-evaluate: a prompt tuned for one model behaves differently
  on another, and prompt+model pairing is what makes behaviour debuggable.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PV-0 the prompt-versioning surface is not recorded as a decided surface - prompts are edited ad hoc and prompt drift (small edits until nobody can match which prompt produced which output) is the default")
    if not dec.get("owner_recorded"): f.append("PV-0 no single owner / edit-and-deploy permission is recorded for live prompts - anyone can change production behaviour with a one-line edit and nobody owns the change")
    if not dec.get("canonical_source_recorded"): f.append("PV-0 the canonical source is not recorded (Monte Carlo: a prompt is production code, versioned, reviewed and evaluated before it ships) - every prompt invents its own change rule")
    bun=d.get("bundle") or {}
    if not bun.get("unique_version_id_per_prompt"): f.append("PV-1 prompts have no unique version identifier (semantic versioning: major for breaking model/schema change, minor for capability, patch for wording) - two different behaviours share one name and cannot be compared or cited")
    if not bun.get("whole_config_versioned"): f.append("PV-1 the whole configuration is not versioned as one bundle (wording + model version + sampling parameters + tool schemas) - changing the model or temperature shifts behaviour as much as editing the text, but only the text is tracked")
    if not bun.get("fixed_template_separated_from_variables"): f.append("PV-1 the fixed template is not separated from variable runtime inputs - version history is cluttered with per-request noise, or dynamic inputs are frozen into the prompt text")
    sto=d.get("storage_review") or {}
    if not sto.get("prompts_in_version_control_as_code"): f.append("PV-2 prompts are not stored in version control as code (same repo, commit history) - the prior prompt exists only in memory, docs or screenshots and cannot be restored exactly")
    if not sto.get("changes_reviewed_like_code"): f.append("PV-2 prompt changes do not go through code-style review (pull request, another reviewer, commit hash) - a behaviour change ships with less scrutiny than a typo fix in code")
    if not sto.get("changelog_with_reason_and_intent"): f.append("PV-2 there is no changelog entry with what changed, why, and an intent label per version - future readers cannot tell why a version exists without archaeology")
    ev=d.get("evaluation") or {}
    if not ev.get("baseline_from_current_version"): f.append("PV-3 no baseline is recorded by running the current production prompt on the same cases first - a new version is judged in isolation and improvement is asserted, not measured")
    if not ev.get("eval_before_promotion_on_fixed_set"): f.append("PV-3 a new version is not evaluated on a fixed, representative test set before it replaces the production version - regressions are found by users, not by the test set")
    if not ev.get("comparison_includes_quality_format_cost_latency"): f.append("PV-3 version comparison does not include quality, format compliance, cost and latency together - a slightly better prompt that costs multiples more or breaks format passes on vibes")
    pro=d.get("promotion") or {}
    if not pro.get("production_and_experiment_separate"): f.append("PV-4 production and experimental prompt versions are not kept separate (staging / tested status) - experiments run on live users by default")
    if not pro.get("gated_promotion_not_direct_edit"): f.append("PV-4 promotion is not gated (a prompt can be edited directly in production) - the fastest path to production is also the least reviewed one")
    if not pro.get("exact_rollback_to_prior_bundle"): f.append("PV-4 there is no exact rollback to the prior bundle (text + model + parameters) in minutes - a bad prompt change becomes a multi-day reconstruction from memory")
    tra=d.get("traceability") or {}
    if not tra.get("outputs_linked_to_prompt_and_model_version"): f.append("PV-5 production outputs / traces are not linked to the prompt version and model version that produced them - when behaviour changes, nobody can isolate whether the prompt or the model moved")
    if not tra.get("model_change_triggers_reevaluation"): f.append("PV-5 a model change (version update or provider switch) does not trigger re-evaluation of the paired prompt - a finely tuned prompt silently degrades on the new model")
    if not tra.get("eval_results_linked_to_version"): f.append("PV-5 evaluation results are not linked to the version they were run against - a version's test evidence cannot be audited after the fact and stale results certify new text")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
