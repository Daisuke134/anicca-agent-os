#!/usr/bin/env python3
"""trace-observability-check: deterministic gate for the TRACE OBSERVABILITY
surface (complete transcripts/traces for every agent trial and production run,
linked to outcomes, read regularly, redacted, and fed back into evals).
Stdlib only, offline, free.
Canonical sources (read 2026-11-17):
- Anthropic, "Demystifying evals for AI agents"
  https://www.anthropic.com/research/demystifying-evals-for-ai-agents
  Transcript = complete record of a trial: outputs, tool calls, reasoning,
  intermediate results and all interactions. Outcome = final state in the
  environment, distinct from what the transcript claims. Step 6: read the
  transcripts and grades from many trials regularly; a failure transcript
  tells whether the agent erred or the grader rejected a valid solution.
  Scores are not taken at face value until someone reads transcripts.
  Complete picture = automated evals + production monitoring + A/B tests +
  user feedback + manual transcript review + systematic human studies.
- Company rule (2026-11-16): traceability is the base of the 3-layer
  verification; work with no trace cannot be verified and does not count
  as complete.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TO-0 trace observability is not recorded as a decided surface - runs are claimed complete with no trace requirement")
    if not dec.get("owner_recorded"): f.append("TO-0 no single owner is recorded for trace observability - when traces go missing, nobody is responsible")
    if not dec.get("canonical_source_recorded"): f.append("TO-0 the canonical source is not recorded (Anthropic: transcript = complete record incl. tool calls and intermediate results; outcome is separate) - every loop invents its own definition of a trace")
    cap=d.get("capture") or {}
    if not cap.get("complete_transcript_captured"): f.append("TO-1 complete transcripts (outputs, tool calls, intermediate results) are not captured for every trial/run - only final messages or summary logs survive, so failures cannot be reconstructed")
    if not cap.get("outcome_linked_to_transcript"): f.append("TO-1 the environment outcome (landed artifact / final state) is not linked to each transcript - a transcript claiming success cannot be checked against what actually exists")
    if not cap.get("trace_id_on_every_run"): f.append("TO-1 not every run carries a real trace_id (spooled/unknown ids do not count) - runs cannot be retrieved, counted, or audited after the fact")
    ide=d.get("identity") or {}
    if not ide.get("session_user_linkage"): f.append("TO-2 traces are not linked to session/user/task identity - cost and quality cannot be attributed, and a user's experience cannot be reconstructed")
    if not ide.get("prompt_model_version_recorded"): f.append("TO-2 prompt and model versions are not recorded on each trace - a quality change cannot be tied to the version that produced it")
    if not ide.get("cost_latency_tokens_recorded"): f.append("TO-2 cost, latency and token usage are not recorded per trace - gross-profit and performance regressions are invisible at run level")
    read=d.get("reading") or {}
    if not read.get("transcripts_read_regularly"): f.append("TO-3 transcripts are not read regularly by a human/agent reviewer (Anthropic Step 6) - graders and scores are taken at face value")
    if not read.get("failure_triage_from_transcripts"): f.append("TO-3 failures are not triaged from transcripts (agent error vs grader/task error) - unfair graders and ambiguous tasks stay hidden behind aggregate scores")
    if not read.get("grader_validated_against_transcripts"): f.append("TO-3 graders are not validated against read transcripts - a grader rejecting valid solutions keeps scoring while nobody notices")
    priv=d.get("privacy") or {}
    if not priv.get("redaction_before_storage"): f.append("TO-4 redaction is not applied and tested before trace storage - traces become a leak surface for user data")
    if not priv.get("secrets_excluded"): f.append("TO-4 secrets/credentials are not provably excluded from traces - a complete record that includes credentials is a breach, not observability")
    if not priv.get("retention_recorded"): f.append("TO-4 trace retention and access are not recorded - traces accumulate forever with no owner, or vanish before they can be audited")
    use=d.get("use") or {}
    if not use.get("scores_attached_to_traces"): f.append("TO-5 scores/grades are not attached to the traces they judge - a score cannot be inspected against the run that produced it")
    if not use.get("traces_feed_error_analysis_and_ci"): f.append("TO-5 traces do not feed error analysis and the CI dataset - production experience is recorded but never converted into regression protection")
    if not use.get("trace_delivery_verified"): f.append("TO-5 trace delivery itself is not verified/alerted (spool-only or unknown-id emission counts as missing) - observability can be silently down while every report claims it is on")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
