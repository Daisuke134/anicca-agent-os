#!/usr/bin/env python3
"""error-analysis-check: deterministic gate for the ERROR ANALYSIS PROCESS
surface (how real traces are read, coded and turned into fixes/evals).
Stdlib only, offline, free.
Canonical source (read in full 2026-11-17, Hamel Husain & Shreya Shankar,
"AI Evals FAQ / Your AI Product Needs Evals",
https://hamel.dev/blog/posts/evals-faq/):
- Error analysis is the most important activity in evals: it decides what
  evals to write. Steps: gather representative traces -> open coding
  (free-text notes, first failure, domain expert / benevolent dictator,
  annotate at least 30 yourself before agent suggestions) -> axial coding
  (failure taxonomy with counts per category) -> iterate to theoretical
  saturation (working pool of roughly 100 diverse traces).
- Do NOT write the rubric before reviewing examples (criteria drift);
  build the rubric from the analysis and revisit it periodically.
- Record problems that are not the model's fault; defer root-cause
  analysis until after prioritisation.
- Surface traces beyond user feedback: random sampling, eval screening,
  outlier / stratified sampling.
- Convert the taxonomy into action: cheapest detector per failure mode
  (code-based where a rule works, judge where judgment is needed);
  non-eval engineering/design fixes are tracked as fixes, not forced
  into evaluators.
- Re-run on a cadence: full pass every 2-4 weeks / on significant
  changes and incidents, 10-20 outlier traces weekly; refresh stale
  gold data from fresh error analysis.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("EA-0 error analysis is not recorded as a decided, recurring surface - failures are handled ad hoc and nobody can say how failure modes are discovered")
    if not dec.get("owner_recorded"): f.append("EA-0 no single domain-expert owner (benevolent dictator) is recorded - open coding by committee or by agent alone drifts from user judgment")
    if not dec.get("canonical_source_recorded"): f.append("EA-0 the canonical source is not recorded (Hamel/Shankar: traces -> open coding -> axial taxonomy -> saturation) - every team invents its own failure-discovery method")
    sam=d.get("sample") or {}
    if not sam.get("real_representative_traces"): f.append("EA-1 traces are not real, representative user interactions (synthetic-only is a bootstrap, not the pool) - the taxonomy describes invented behaviour, not the product")
    if not sam.get("diverse_pool_about_100"): f.append("EA-1 the working pool is not roughly 100 diverse traces (or its size is unrecorded) - a handful of traces cannot reveal the failure distribution")
    if not sam.get("sampling_beyond_feedback"): f.append("EA-1 traces are surfaced only from user feedback - silent failures never reported by users are never reviewed (use random, eval-screened, outlier or stratified sampling too)")
    ope=d.get("open_coding") or {}
    if not ope.get("free_text_first_failure"): f.append("EA-2 open coding is not free-text notes on the first failure per trace - a pre-made checklist/rubric blinds reviewers to unanticipated failures (criteria drift is lost)")
    if not ope.get("expert_first30_before_agent"): f.append("EA-2 the domain expert did not annotate at least 30 traces before agent suggestions - early agent guesses bias the human criteria the whole taxonomy rests on")
    if not ope.get("rubric_built_after_review"): f.append("EA-2 a rubric was fixed before examples were reviewed, or was never rebuilt from the analysis - the rubric freezes yesterday's definition of good")
    axi=d.get("axial_coding") or {}
    if not axi.get("taxonomy_with_counts"): f.append("EA-3 open notes were never axial-coded into a failure taxonomy with a count per category - without counts there is no prioritisation, only anecdotes")
    if not axi.get("non_model_problems_included"): f.append("EA-3 problems that are not the model's fault (missing features, broken UX, missing data) are excluded - the review only finds model-shaped failures")
    if not axi.get("root_cause_deferred"): f.append("EA-3 root-cause analysis is done during annotation instead of after prioritisation - annotators slow down, see less data, and code shallower notes")
    con=d.get("conversion") or {}
    if not con.get("top_categories_acted_on"): f.append("EA-4 the largest taxonomy categories have no recorded fix or evaluator - error analysis that changes nothing is journaling, not improvement")
    if not con.get("cheapest_detector_chosen"): f.append("EA-4 the detector per failure mode is not chosen by cost (code-based rule where a rule works, judge only where judgment is needed) - expensive judges get built for failures a regex would catch")
    if not con.get("non_eval_fixes_tracked"): f.append("EA-4 failures needing engineering/design fixes (not evaluators) are not tracked separately - they are either forced into evals or dropped")
    mai=d.get("maintenance") or {}
    if not mai.get("saturation_checked"): f.append("EA-5 theoretical saturation was never checked (review continues until new traces stop revealing or changing failure modes) - stopping early is a guess, not a finding")
    if not mai.get("rerun_cadence_recorded"): f.append("EA-5 no re-run cadence is recorded (full pass every 2-4 weeks / on significant change or incident, plus 10-20 outlier traces weekly) - the taxonomy goes stale while the product moves")
    if not mai.get("taxonomy_revisited_on_change"): f.append("EA-5 the taxonomy and rubric are not revisited after model/prompt/feature changes or gold-data staleness - yesterday's failure map is applied to today's system")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
