#!/usr/bin/env python3
"""feedback-loop-check: deterministic gate for the PRODUCTION FEEDBACK LOOP
surface (capture, triage, dataset, gating, calibration/closure). Stdlib only, offline, free.
Canonical source (read in full 2026-11-18, Langfuse, "Turn user feedback on AI
responses into evaluation datasets",
https://langfuse.com/resources/engineering/user-feedback-to-evaluation-datasets):
- User feedback is the cheapest quality signal an LLM app produces, and most teams
  waste it: a thumbs-down lands in a dashboard and the conversation behind it is
  never seen again. Treat every negative rating as a candidate test case, attach
  the answer the user should have received, and run every future prompt or model
  change against that growing set.
- Capture: every signal becomes a score (name, value, data type, optional comment)
  attached to the trace that produced the output. Evaluators, human annotators and
  user feedback write to the same score table, so a negative rating is filterable
  and comparable with a judge verdict. Explicit ratings come from the frontend
  (public key only, backend returns the trace ID, stable score id so re-rating
  updates instead of duplicating); implicit signals (edited draft, closed ticket)
  are scored from the server, with the comment carrying the edit diff or complaint;
  signals that exist only in conversation text are scored by an LLM-as-a-judge
  evaluator on production observations.
- Triage: read a sample before adding anything to a dataset. Thumbs feedback skews
  toward unhappy users, and some negative ratings are about latency or tone rather
  than correctness. A boolean/categorical score is a filter, so the failure list is
  one query away (score name + value, plus time window, trace name or user ID).
  Twenty minutes of reading usually yields two or three failure clusters, which
  decide how many datasets you create.
- Dataset items: an input, an optional expected output, optional metadata, and a
  link to the source trace/observation. Keep the input in the shape the task
  expects, record the failure cluster in metadata, protect the collection with
  JSON Schema validation and versioning (pin a version so an experiment stays
  reproducible). Fill routes by volume: one-by-one on a trace, batch from the
  observations table, or SDK/API for recurring pipelines. The expected output is
  the answer a domain expert would have given, stored as a Corrected Output
  (dataType CORRECTION) - never the disliked output itself; if no reference
  exists, leave it empty and use reference-free checks. Reviewers produce
  corrections naturally inside an annotation queue.
- Gating: run experiments against the dataset (UI for prompt-only changes, SDK so
  the real task function runs for logic/retrieval/tool changes); each run is one
  trace per item. In CI, pin dataset_version, fail the job on regression, keep the
  gated dataset small enough to run on every pull request (tens to low hundreds)
  and move the long tail to a second dataset that runs on a schedule.
- Calibration and closure: give the judge an output that mirrors the feedback
  signal and compare the two (Cohen's Kappa, F1, overall agreement, confusion
  matrix on traces carrying both scores). The feedback dataset doubles as the
  judge calibration set. Route the disagreements (thumbs-down the judge rated
  helpful, judge failure the user rated positively) to an annotation queue where
  a domain expert scores them and adds a corrected output; each resolved
  disagreement improves the judge rubric, the dataset, or the understanding of
  what users mean by a thumbs-down.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("FB-0 the feedback-loop surface is not recorded as a decided surface - user feedback lands in a dashboard and the conversation behind it is never seen again")
    if not dec.get("owner_recorded"): f.append("FB-0 no feedback-loop owner is recorded - nobody is named to read failures, grow the dataset and keep the loop closing")
    if not dec.get("canonical_source_recorded"): f.append("FB-0 the canonical source is not recorded (Langfuse: feedback to evaluation datasets - capture as scores on traces, triage, correct, gate in CI, calibrate the judge) - every surface invents its own way of wasting feedback")
    cap=d.get("capture") or {}
    if not cap.get("explicit_implicit_judge_signals_defined"): f.append("FB-1 the signals are not defined across all three kinds (explicit ratings, implicit backend events such as edits or closed tickets, and judge-scored signals that exist only in conversation text) - the cheapest quality signal the product produces is not even collected")
    if not cap.get("score_attached_to_producing_trace_shared_namespace"): f.append("FB-1 feedback is not stored as a score (name, value, data type, comment) attached to the trace that produced the output, in the same namespace as evaluator and annotator scores - a negative rating cannot be filtered or compared with a judge verdict without manual joining")
    if not cap.get("stable_id_idempotent_no_secret_in_frontend"): f.append("FB-1 capture is not idempotent and safe (stable score id so re-rating updates instead of duplicating, public key only in the frontend, backend returns the trace ID) - changed minds double-count and secret keys leak into client code")
    tri=d.get("triage") or {}
    if not tri.get("sample_read_bias_and_cause_checked"): f.append("FB-2 no sample is read before dataset conversion, and the skew of thumbs feedback (toward unhappy users; some negatives are latency or tone, not correctness) is not checked - the dataset fills with unexamined complaints")
    if not tri.get("failures_filterable_and_clustered"): f.append("FB-2 failures are not one query away (filter by score name and value, plus window, trace name or user) and reading does not yield named failure clusters that decide how many datasets exist - triage is anecdote, not a list")
    if not tri.get("item_shape_source_link_schema_versioning"): f.append("FB-2 dataset items do not preserve reproducibility (input in the shape the task expects, failure cluster in metadata, source trace link, JSON Schema validation, dataset versioning) - a future experiment cannot reproduce the failure or pin the set it ran against")
    dat=d.get("dataset") or {}
    if not dat.get("routes_by_volume_defined"): f.append("FB-3 the fill routes by volume are not defined (one-by-one on a trace for a few failures, batch from filtered observations for tens to hundreds, SDK/API for recurring pipelines) - conversion depends on whoever happens to notice a failure")
    if not dat.get("expected_output_is_expert_correction_never_disliked_output"): f.append("FB-3 the expected output is not fixed as the answer a domain expert would have given - the disliked output itself gets mapped in, or references are invented; where no reference exists the item is not left empty with reference-free checks")
    if not dat.get("corrections_stored_and_produced_in_annotation_queue"): f.append("FB-3 corrections are not stored as first-class records (CORRECTION scores fetchable via API) and reviewers do not produce them inside an annotation queue - the work of writing the right answer has no home and is redone from scratch each time")
    gat=d.get("gating") or {}
    if not gat.get("experiments_run_on_dataset_ui_and_sdk"): f.append("FB-4 changes are not run as experiments against the feedback dataset (UI for prompt-only changes, SDK with the real task function for logic, retrieval or tool changes) - a fix is believed, not measured against the failures that motivated it")
    if not gat.get("ci_gate_pinned_version_small_set_long_tail_scheduled"): f.append("FB-4 the dataset is not a CI gate (pinned dataset version, job fails on regression, gated set kept small enough for every pull request, long tail in a second dataset on a schedule) - a change can silently reintroduce a known failure the users already reported")
    if not gat.get("per_item_run_traceability"): f.append("FB-4 experiment runs are not traceable per item (one trace per dataset item, a failing item one click from the output that failed) - aggregate scores hide which known failure came back")
    cal=d.get("calibration_closure") or {}
    if not cal.get("judge_mirrors_signal_agreement_measured"): f.append("FB-5 the production judge is not calibrated against user feedback (judge output mirrors the feedback signal, agreement measured with Kappa, F1 and a confusion matrix on traces carrying both scores, the feedback dataset doubling as the calibration set) - automated scoring flags failures nobody trusts")
    if not cal.get("disagreements_routed_to_annotation_and_resolved"): f.append("FB-5 judge-user disagreements are not routed to an annotation queue and resolved into a better rubric, dataset or understanding (expert scores against fixed criteria and adds a corrected output) - the most informative traces in the system are never read")
    if not cal.get("loop_owned_on_cadence_dataset_grows"): f.append("FB-5 the loop has no cadence (feedback reviewed on a rhythm, new failures keep entering the dataset, the gated set is refreshed as traffic changes) - the loop was a one-off cleanup, not a flywheel, and it stalls the week nobody looks")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
