#!/usr/bin/env python3
"""batch-check: deterministic gate for the BATCH PROCESSING surface
(which LLM workloads run asynchronously in batches at half price, how
batches are built, tracked and matched, and how the discount, expiry
and retrieval window are accounted).
Stdlib only, offline.
Canonical source (read in full 2026-11-18):
- Anthropic Claude Platform Docs "Batch processing"
  https://platform.claude.com/docs/en/build-with-claude/batch-processing
  (383 lines read in full): the Message Batches API asynchronously
  processes large volumes of Messages requests; most batches finish in
  under 1 hour while reducing costs by 50 percent and increasing
  throughput. A batch is limited to 100,000 requests or 256 MB,
  whichever comes first; results are accessible when all messages
  complete or after 24 hours, whichever comes first, and batches
  expire if processing does not complete within 24 hours; results
  stay downloadable for 29 days after creation (from created_at, not
  ended_at). Each request needs a unique custom_id (1-64 chars,
  ^[a-zA-Z0-9_-]{1,64}$) plus standard Messages params; results come
  back in .jsonl in any order and must be matched by custom_id. Four
  result types: succeeded / errored / canceled / expired - only
  succeeded requests are billed. Unsupported params return validation
  errors: stream:true, speed (Fast mode), fallbacks, max_tokens:0
  (cache pre-warming). All active models are supported; vision, tool
  use incl. server tools, system messages, multi-turn and extended
  thinking can be batched, mixed in one batch. Prompt caching stacks
  with the batch discount on a best-effort basis (typical hit rates
  30-98 percent): include identical cache_control blocks in every
  request, keep a steady stream so 5-minute entries do not expire,
  share as much cached content as possible (secondary guides note the
  1-hour cache duration is recommended for shared batch context).
  Best practices: monitor status and implement retry logic for failed
  requests; use meaningful custom_id values because order is not
  guaranteed; split very large datasets into multiple batches; dry
  run a single request shape with the Messages API first to avoid
  validation errors. One request's failure does not affect others.
  Batches are Workspace-scoped and may go slightly over the Console
  spend limit; processing can slow under demand, expiring more
  requests. Batch data is stored server-side up to 29 days and a
  batch can be deleted after processing (cancel first if running).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("BA-0 the batch-processing surface is not recorded as a decided surface - which workloads run synchronously at full price is left to habit, not a decision")
    if not dec.get("owner_recorded"): f.append("BA-0 no owner is recorded for batch economics and correctness (what gets batched, what the discount actually saved, what expired) - silent full-price spend and silent expiry have no accountable reader")
    if not dec.get("workload_inventory_classified"): f.append("BA-0 there is no inventory classifying each LLM workload by latency tolerance and volume - batchable bulk work is indistinguishable from interactive work")
    eli=d.get("eligibility") or {}
    if not eli.get("latency_tolerance_classified_per_workload"): f.append("BA-1 latency tolerance is not classified per workload against the batch contract (most batches under 1 hour, hard expiry at 24 hours) - a workload whose deadline is shorter than the worst case can be batched into expiry")
    if not eli.get("latency_tolerant_workloads_exist_as_scheduled_jobs"): f.append("BA-1 no latency-tolerant bulk workloads are identified at all (evals, classification, extraction, nightly generation) - the surface the API exists for has no named candidates")
    if not eli.get("interactive_surfaces_excluded"): f.append("BA-1 interactive, user-waiting surfaces are not explicitly excluded from batching - anything a person or a live intervention waits on must never sit in an asynchronous queue")
    con=d.get("construction") or {}
    if not con.get("custom_id_unique_and_meaningful"): f.append("BA-2 requests do not carry unique, meaningful custom_id values (1-64 chars, ^[a-zA-Z0-9_-]{1,64}$) - results return in any order and cannot be matched back to their inputs")
    if not con.get("unsupported_params_excluded"): f.append("BA-2 batch-unsupported parameters are not excluded by construction (stream:true, speed/Fast mode, fallbacks, max_tokens:0 each return a validation error) - whole batches can fail on one copied synchronous request shape")
    if not con.get("dry_run_single_request_first"): f.append("BA-2 a single request shape is not dry-run through the synchronous Messages API before batch submission - validation errors are discovered at batch scale instead of on one cheap call")
    lif=d.get("lifecycle") or {}
    if not lif.get("polling_or_tracking_implemented"): f.append("BA-3 batch completion is not tracked (poll processing_status until ended, or list/retrieve per batch) - submitted batches can sit ended, canceling or expired with nobody retrieving them")
    if not lif.get("results_matched_by_custom_id_not_order"): f.append("BA-3 results are not matched to requests by custom_id - the docs guarantee no result order, so positional matching silently pairs outputs with the wrong inputs")
    if not lif.get("result_types_handled_and_failed_retried"): f.append("BA-3 the four result types (succeeded / errored / canceled / expired) are not each handled, with retry logic for failed requests only - one request's failure must not fail the batch, and unbilled failures must be resubmitted, not dropped")
    eco=d.get("economics") or {}
    if not eco.get("batch_discount_accounted_in_unit_cost"): f.append("BA-4 the 50 percent batch discount is not accounted in cost per successful task (only succeeded requests are billed) - unit economics compare a synchronous price the workload never had to pay")
    if not eco.get("caching_stacked_deliberately"): f.append("BA-4 prompt caching is not deliberately stacked inside batches (identical cache_control on every request, shared prefix maximized, steady stream or 1-hour duration against the 5-minute expiry; hits are best-effort at a measured 30-98 percent) - the second discount is left to chance")
    if not eco.get("spend_overshoot_and_expiry_risk_accounted"): f.append("BA-4 batch accounting ignores its two documented leaks: batches may go slightly over the Workspace spend limit, and under demand more requests expire at 24 hours unbilled but undelivered - neither risk has a number or an owner")
    ops=d.get("operations") or {}
    if not ops.get("results_retrieved_within_retention_window"): f.append("BA-5 result retrieval is not guaranteed inside the 29-day window counted from created_at (not ended_at) - a batch can succeed and still lose its results to late collection")
    if not ops.get("limits_respected_by_splitting"): f.append("BA-5 the per-batch limits (100,000 requests or 256 MB, whichever first; 413 request_too_large beyond it) are not respected by splitting large datasets into multiple batches by design")
    if not ops.get("batch_events_logged_with_counts"): f.append("BA-5 batch events are not logged per workload with request_counts by result type and realized cost - nobody can tell what was batched, what succeeded, what expired, or what the discount saved")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
