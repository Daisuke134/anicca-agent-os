#!/usr/bin/env python3
"""judge-calibration-check: deterministic gate for the LLM-JUDGE CALIBRATION
surface (using a model-based grader / LLM-as-judge for subjective eval
dimensions, calibrated against human experts). Stdlib only, offline, free.
Canonical source (read in full 2026-11-17, Anthropic Engineering,
"Demystifying evals for AI agents", published 2026-01-09,
https://www.anthropic.com/research/demystifying-evals-for-ai-agents):
- Three grader types: code-based, model-based, human. Choose deterministic
  graders where possible, LLM graders where necessary, human graders
  judiciously for validation.
- "LLM-as-judge graders should be closely calibrated with human experts to
  gain confidence that there is little divergence between the human grading
  and model grading."
- "To avoid hallucinations, give the LLM a way out, like providing an
  instruction to return 'Unknown' when it doesn't have enough information."
- "Create clear, structured rubrics to grade each dimension of a task, and
  then grade each dimension with an isolated LLM-as-judge rather than using
  one to grade all dimensions."
- "Once the system is robust, it's sufficient to use human review only
  occasionally." Descript: manual grading -> LLM graders with periodic
  human calibration.
- "Reserve systematic human studies for calibrating LLM graders or
  evaluating subjective outputs where human consensus serves as the
  reference standard."
- Step 6: read transcripts and grades; failures should seem fair; do not
  take eval scores at face value until someone reads transcripts.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("JC-0 judge calibration (calibrating every model-based grader against human experts before its scores are trusted) is not recorded as a decided surface - a judge can be introduced ad hoc and its scores treated as ground truth")
    if not dec.get("owner_recorded"): f.append("JC-0 no single judge-calibration owner is recorded (gold set, agreement measurement and re-calibration cadence are ongoing work, not a one-time setup)")
    if not dec.get("canonical_source_recorded"): f.append("JC-0 the canonical source is not recorded (Anthropic, Demystifying evals for AI agents: model-based graders must be closely calibrated with human experts, with little divergence) - every eval invents its own trust rule for judge scores")
    fou=d.get("foundation") or {}
    if not fou.get("deterministic_first_recorded"): f.append("JC-1 the grader choice rule is not recorded (deterministic/code-based where possible, LLM judge only where necessary, human judiciously) - subjective judging is used even where an exact check exists")
    if not fou.get("human_gold_set_exists"): f.append("JC-1 no human-labelled gold set exists for the subjective dimensions the judge will grade (human consensus is the reference standard) - there is nothing to calibrate against")
    if not fou.get("judge_identity_pinned"): f.append("JC-1 the judge identity is not pinned (judge model, version, prompt/rubric version recorded per run) - a silent judge change changes the metric while the score series looks continuous")
    cal=d.get("calibration") or {}
    if not cal.get("agreement_measured"): f.append("JC-2 judge-vs-human agreement is not measured on the gold set (agreement rate / divergence reported as a number) - 'calibrated' is asserted, not measured")
    if not cal.get("divergence_threshold_defined"): f.append("JC-2 no divergence threshold is defined that a judge must stay under before its scores may be published or used for a model decision - any amount of human/judge divergence passes")
    if not cal.get("calibration_before_trust"): f.append("JC-2 calibration is not required BEFORE a new judge / rubric / dimension is trusted - the first uncalibrated scores are the ones that shape the model roadmap")
    des=d.get("design") or {}
    if not des.get("unknown_escape"): f.append("JC-3 the judge has no 'Unknown' way out when it lacks enough information - forced answers turn judge hallucination into quality scores")
    if not des.get("per_dimension_isolated_judges"): f.append("JC-3 dimensions are not graded by isolated per-dimension judges - one judge grading all dimensions at once blurs which dimension failed and couples the scores")
    if not des.get("structured_rubric_per_dimension"): f.append("JC-3 there is no clear, structured rubric per dimension - an unstructured 'is this good?' prompt is not a grader, it is an opinion sampled from a model")
    mea=d.get("measurement") or {}
    if not mea.get("disagreements_reviewed"): f.append("JC-4 judge/human disagreement cases are not sampled and read (transcripts + grades) - the cases that would show the judge is wrong are exactly the ones never opened")
    if not mea.get("recalibration_cadence_recorded"): f.append("JC-4 no periodic re-calibration cadence is recorded (human review at intervals, and on every judge model or rubric change) - calibration decays silently as models and tasks drift")
    if not mea.get("score_reports_carry_calibration_state"): f.append("JC-4 eval score reports do not carry the calibration state (gold size, agreement, date, judge identity) next to the score - a reader cannot tell a calibrated score from an uncalibrated one")
    ver=d.get("verification") or {}
    if not ver.get("failing_calibration_blocks_scores"): f.append("JC-5 a failing calibration does not block score publication / model decisions - the gate is advisory, so the busiest week is when uncalibrated scores ship")
    if not ver.get("gold_set_held_out"): f.append("JC-5 the calibration gold set is not held out from training / capability tuning - a judge calibrated on cases the model was tuned on reports agreement that does not generalise")
    if not ver.get("calibration_fixture_tested"): f.append("JC-5 the calibration procedure itself is not fixture-tested (a judge known to diverge is caught, a judge that always returns Unknown is caught) - the measurement of the measurer is unmeasured")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
