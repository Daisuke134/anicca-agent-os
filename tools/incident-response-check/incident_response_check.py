#!/usr/bin/env python3
"""incident-response-check: deterministic gate for the LLM INCIDENT RESPONSE
surface (classify, grade, detect, contain, recover, learn). Stdlib only, offline, free.
Canonical source (read in full 2026-11-18, Sandeep Belgavi, "LLM Incident Response,
in depth", https://www.aicassindra.com/blogs/llm_security/llm_sec_incident_response.html):
- An incident is any event where the system did, or could have done, something its
  owners would not authorise. Classes that need different first moves: prompt injection
  (direct/indirect), sensitive data disclosure, system prompt / secret leakage,
  excessive agency, harmful or wrong output at scale, abuse of the service.
- Severity is decided in minutes on four questions, taking the HIGHEST grade any
  answer gives (data left its boundary? system acted in the world? how many users/
  records? is it still happening?). "Unknown" counts as the higher grade; an incident
  is downgraded only when evidence supports it. Nondeterminism: a leak reproduced
  1 time in 20 is still happening at a 5% rate - never downgrade because the first
  three reproduction attempts failed.
- Detection signals that pay: canary tokens in prompts/documents/fake credentials;
  tool-call anomalies and novel destinations (a tool writing somewhere new);
  classifier rate shifts vs the same hour last week; cost/token anomalies (runaway
  loops show up first as spend); refusal-rate changes after a deploy. All depend on
  a complete record of prompts, retrieved context, outputs and tool calls joined by
  a request ID.
- Containment is a ladder built in advance, each rung existing, tested and operable
  without a deploy: block the pattern, disable one tool, revoke the credential,
  roll back prompt/model/index version, read-only mode, kill switch last (its cost
  is the whole feature). Freeze evidence before or in parallel with containment,
  never after - a rollback or key rotation can destroy the state you need.
- First hour: declare (anyone can open one; name a commander, provisional class and
  severity, one channel, one timeline doc); freeze evidence (audit window from at
  least 1h before first signal + exact versions); contain with the narrowest rung
  and verify it worked by watching the same signal; scope (query logs for every
  session matching the indicator); assign a comms lead and a fix owner; update at
  a fixed interval even if nothing changed.
- Recovery gate: every captured attack payload becomes a regression case plus
  variations (languages, encodings, instruction split across documents); replay
  incident sessions against the fixed system and confirm no harmful action in any
  of at least 20 samples per case; re-enable in stages (internal first, then a
  small share) with the firing detection rule kept on a tighter threshold for a
  week; keep the narrow containment (e.g. recipient restriction) permanently.
  A hard boundary first, a model-side mitigation second - fixing only the prompt
  reduces the rate but leaves the sensitive action reachable.
- Communication and learning: notification depends on class (confirmed personal
  data disclosure in GDPR scope: supervisory authority without undue delay, where
  feasible within 72h of becoming aware - the moment of awareness belongs in the
  timeline; contracts carry their own windows, counsel confirms, comms lead does
  not improvise). Never say "the AI did it" - the cause is nearly always a
  permission or design decision. Postmortem blameless and within a week: timeline
  with detection/containment/resolution times, class and final severity, affected
  users/data, which rung stopped the harm and how long it took to find it,
  contributing factors split into model behaviour / permissions / missing detection,
  actions with owners. Track two numbers across incidents: first harmful event to
  detection, and detection to verified containment. Feed each new class back into
  the severity table and the containment file, test each switch quarterly in
  staging (confirm behaviour change within one minute), and run a tabletop exercise.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("IR-0 the incident-response surface is not recorded as a decided surface - when an LLM event happens the team argues about whether it is even an incident")
    if not dec.get("owner_recorded"): f.append("IR-0 no incident commander role is recorded - nobody is named to declare, coordinate and decide severity in minutes")
    if not dec.get("canonical_source_recorded"): f.append("IR-0 the canonical source is not recorded (Belgavi: LLM Incident Response - classify, grade, contain, recover, postmortem) - every incident invents its own response")
    cls=d.get("classification_severity") or {}
    if not cls.get("classes_with_first_lever"): f.append("IR-1 the incident classes and their different first levers are not written down (prompt injection, data disclosure, prompt/secret leakage, excessive agency, harmful output at scale, abuse) - classification is paperwork instead of deciding the first move")
    if not cls.get("severity_four_questions_highest_grade"): f.append("IR-1 severity is not graded on the four quick questions taking the highest grade (data left its boundary? acted in the world? how many? still happening?) - a slow, argued grade lets harm spread while the grade is debated")
    if not cls.get("unknown_upgraded_no_downgrade_on_failed_repro"): f.append("IR-1 'unknown' is not treated as the higher grade and failed reproductions are not barred from downgrading - a leak that fires 1 time in 20 is read as not happening after three clean attempts")
    det=d.get("detection") or {}
    if not det.get("canary_and_tool_anomaly_signals"): f.append("IR-2 canary tokens and tool-call anomaly / novel-destination signals are not wired - an agent suddenly writing to somewhere new is found by a user or researcher, not by monitoring")
    if not det.get("classifier_cost_refusal_shape_alerts"): f.append("IR-2 classifier rate shifts (vs the same hour last week), cost/token anomalies and refusal-rate changes after a deploy are not alerted on shape changes - a silent quality regression or a runaway loop is only noticed when the bill or complaints arrive")
    if not det.get("complete_record_joined_by_request_id"): f.append("IR-2 there is no complete record of prompts, retrieved context, outputs and tool calls joined by a request ID - without the retrieved document the injection source cannot be found")
    con=d.get("containment_first_hour") or {}
    if not con.get("containment_ladder_built_tested_no_deploy"): f.append("IR-3 the containment ladder is not built in advance, tested and operable without a deploy (block pattern, disable one tool, revoke credential, roll back prompt/model/index, read-only mode, kill switch) - at 2 a.m. the fastest action is taking the whole product offline or editing prompts in production")
    if not con.get("evidence_frozen_before_containment"): f.append("IR-3 evidence is not frozen before or in parallel with containment - a rollback, index rebuild or key rotation can destroy exactly the state the postmortem needs")
    if not con.get("first_hour_protocol"): f.append("IR-3 the first-hour protocol is not written down (declare, freeze evidence, contain and verify by the same signal, scope by indicator, assign comms lead and fix owner, update at a fixed interval) - the first hour is spent arguing instead of stopping the harm")
    rec=d.get("recovery") or {}
    if not rec.get("payloads_to_regression_cases_with_variations"): f.append("IR-4 captured attack payloads are not turned into regression cases with variations (other languages, other encodings, instruction split across documents) - the fix is tested only against the one payload that was seen")
    if not rec.get("replay_at_least_20_samples_per_case"): f.append("IR-4 incident sessions are not replayed against the fixed system with at least 20 samples per case - one clean sample proves little for a sampled model, so a 5% leak can be declared fixed")
    if not rec.get("staged_reenable_tightened_detection_keep_narrow_containment"): f.append("IR-4 re-enabling is not staged (internal first, then a small share) with the firing rule kept tighter for a week and the narrow containment kept permanently - the team relapses by re-opening the exact hole the model-side fix only reduced")
    lea=d.get("comms_learning") or {}
    if not lea.get("notification_obligations_by_class"): f.append("IR-5 notification obligations by class are not written down (GDPR 72h window and the moment of awareness in the timeline, contract windows confirmed by counsel) - the comms lead improvises who must be told and by when")
    if not lea.get("blameless_postmortem_within_week_with_two_times"): f.append("IR-5 there is no blameless postmortem within a week with the required fields (timeline with detection/containment/resolution times, class and final severity, affected users/data, which rung stopped the harm, factors split by model behaviour / permissions / missing detection, actions with owners) and the two tracked times (first harmful event to detection, detection to verified containment) - incidents leave no measurable lesson")
    if not lea.get("feedback_into_severity_containment_regression_and_tests"): f.append("IR-5 new incident classes are not fed back into the severity table, the containment file and the regression suite, switches are not tested quarterly in staging and no tabletop exercise is run - the next responder starts with no more rungs than the last one had")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
