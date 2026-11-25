#!/usr/bin/env python3
"""intervention-evidence-check: deterministic gate for the INTERVENTION
EVIDENCE EXPORT surface (decision-point records leaving the device and
becoming real eval cases). Stdlib only, offline, free.
Sources (read 2026-11-17):
- Anthropic, "Demystifying evals for AI agents" (2026-01-09)
  https://www.anthropic.com/research/demystifying-evals-for-ai-agents :
  an eval case is task + transcript (the complete record of a trial) +
  outcome (the final state in the environment). A record that never
  reaches the eval harness is not a case; grading runs on transcripts
  and outcomes the harness actually holds.
- Off-policy evaluation logging requirements (Google, WSDM '19 Top-K
  Off-Policy Correction, logging table; Farhadi, "The Hidden Foundation
  of Off-Policy Evaluation"): the log must store, at decision time, the
  context, the action taken, the reward/outcome, AND the logging
  policy's exact probability pi_0(a|s) for the chosen action, after all
  rules and gating. Without the propensity the importance weight is
  undefined; without the candidate set / support, coverage cannot be
  audited; propensities reconstructed after the fact are not the
  propensity. Decisions NOT to act are part of the support record.
Exit 0=PASS, 1=FAIL.
Input JSON sections: decision, record, export, join, privacy, verification.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("IE-0 treating intervention evidence export (decision records becoming eval cases) as a decided surface is not recorded - the records exist by accident of a local store, not by a decision that they must reach the eval")
    if not dec.get("dataset_destination_named"): f.append("IE-0 no dataset destination is named for exported cases (which eval dataset, owned by whom) - records with nowhere to land stay on the device that made them")
    if not dec.get("export_owner_recorded"): f.append("IE-0 no single export owner is recorded (capture, upload, join and dataset counts are ongoing work, not a store implementation detail)")
    rec=d.get("record") or {}
    if not rec.get("probability_logged_exact"): f.append("IE-1 the chosen intervention's exact assignment probability (0<p<=1, computed by the deciding policy at decision time, never reconstructed) is not logged on the decision row - off-policy grading has no denominator")
    if not rec.get("candidate_set_logged"): f.append("IE-1 the candidate set (which interventions were eligible and how many) is not persisted on the case - coverage/support cannot be audited, and a probability without its candidate set cannot be re-derived or checked")
    if not rec.get("negative_decisions_logged"): f.append("IE-1 decisions NOT to intervene (unavailable moments, do_not_send) are not recorded - the eval only sees moments where something was sent, so it cannot learn when silence was the right action")
    exp=d.get("export") or {}
    if not exp.get("full_case_export_exists"): f.append("IE-2 no path carries the full case (situation + stimulus + measured response) off the device - a local JSONL the eval never reads produces zero real cases, however complete the rows are")
    if not exp.get("export_retry_idempotent"): f.append("IE-2 export is not retried and idempotent by deliveryId - a failed or duplicated upload silently loses or double-counts the exact cases the eval is graded on")
    if not exp.get("decision_metadata_reaches_analytics"): f.append("IE-2 not even decision metadata (ids, probability, policy version) reaches the analytics pipeline - there is no server-side trace that decisions are happening at all")
    j=d.get("join") or {}
    if not j.get("sender_join_measured"): f.append("IE-3 the join rate for externally-decided interventions (sender decision row vs on-device outcome row) is not measured - invalid or missing assignment payloads are dropped silently and the loss is invisible")
    if not j.get("pending_observations_bounded"): f.append("IE-3 unmatched outcome observations are not bounded (no expiry, cap or escalation) - the pending file grows forever and old outcomes can join the wrong future decision or none")
    if not j.get("outcome_window_handled"): f.append("IE-3 the outcome observation window is not handled (responses inside the window join the case; outside-window responses are segregated, not silently merged or dropped)")
    pri=d.get("privacy") or {}
    if not pri.get("pseudonymous_no_freetext"): f.append("IE-4 exported cases are not guaranteed pseudonymous and free-text-free (no message text, no raw profile, no name) - the eval dataset becomes a privacy liability instead of evidence")
    if not pri.get("deletion_propagates"): f.append("IE-4 account deletion does not propagate to the evidence (local store files and already-exported rows survive) - a deleted user's interventions remain in the dataset")
    if not pri.get("person_id_bound_to_identity"): f.append("IE-4 the evidence personId is not bound to the durable app identity - a device-local UUID lost on reinstall splits one person's history into unrelated people")
    ver=d.get("verification") or {}
    if not ver.get("case_validity_tests"): f.append("IE-5 no automated test covers case validity (probability range, join keys, window logic) - a refactor can silently corrupt every future case")
    if not ver.get("e2e_device_to_dataset"): f.append("IE-5 no end-to-end proof that a case produced on a device lands in the eval dataset (count > 0 read back from the dataset side) - 'logging exists' is being read as 'eval has data'")
    if not ver.get("drop_failure_visible"): f.append("IE-5 dropped/failed record writes are not visible (no counter, no metric, callers discard the failure) - the dataset's missing cases have no signal anywhere")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
