#!/usr/bin/env python3
"""dreaming-check: deterministic gate for the Dreams (offline memory
consolidation) surface. Stdlib only, offline, free.

Canonical source (read in full this run, 148 lines):
Anthropic Claude Platform Docs, "Dreams"
https://platform.claude.com/docs/en/managed-agents/dreams
- A dream is an async job: one pre-existing memory store + 1 to 100 past
  sessions in, a NEW reorganized memory store out (duplicates merged,
  stale/contradicted entries replaced with the latest value, new
  insights surfaced). The input store is never modified, so the output
  can be reviewed and discarded.
- The output store ID appears in `outputs` shortly after `running`
  starts (once the input is cloned); a running dream can briefly
  report an empty outputs array.
- `instructions` steers synthesis at a high level (focus areas, what to
  preserve, output conventions) throughout the pipeline. It is a
  synthesis pass, not a text editor: line-targeted directives
  ("change sentence X to Y") generally produce no change; targeted
  edits go through the Memory Stores API on the output store.
- Lifecycle: pending -> running -> completed / failed / canceled.
  Minutes to a few hours, driven by transcript count. While running,
  `session_id` points at the pipeline session whose events can be
  streamed; that session is archived (not deleted) at terminal state.
- Use the output: on completed, review via Memory Stores API / Console,
  then attach the output store to future sessions in place of (or
  alongside) the input, or discard it (delete / archive). On failed or
  canceled the output store persists with partial contents; inspect or
  clean it up via the Memory Stores API. The dream never deletes or
  modifies its inputs.
- Cancel: pending/running -> canceled immediately; canceling a
  completed/failed dream returns 400; canceling a canceled dream is an
  idempotent no-op. Archive: terminal states only, sets archived_at,
  status unchanged, excluded from default lists, no unarchive;
  archiving a pending/running dream returns 400. Archiving a dream
  does not touch its output store.
- Errors: timeout, internal_error, memory_store_org_limit_exceeded,
  input_memory_store_too_large, input_memory_store_unavailable,
  input_session_unavailable.
- Billing: standard API token rates for the chosen model; `usage` on
  the resource reports exact totals; cost scales roughly linearly with
  the number/length of input sessions; start with a small batch.
- Availability: research preview, Managed Agents only. Supported
  models listed: Fable 5.2/5.1/5, Opus 5.5/5/4.8/4.7, Sonnet 5.5/5/4.6.
  Dream endpoints require the `dreaming-2026-04-21` beta header;
  `managed-agents-2026-04-01` alone does not grant dreams; session
  calls use managed-agents-2026-04-01, memory store calls use
  agent-memory-2026-07-22 (SDK sets the right header per call).

Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    f = []
    dec = d.get("decision") or {}
    if not dec.get("decision_recorded"):
        f.append("D-0 the dreaming surface is not recorded as decided (offline consolidation of the memory store is left to habit / ad-hoc cleanups)")
    if not dec.get("access_status_recorded"):
        f.append("D-0 research-preview access status is not recorded (dreams are research preview, request-gated; an unrecorded status reads as available when it may not be)")
    if not dec.get("canonical_source_recorded"):
        f.append("D-0 the canonical source is not recorded (Anthropic Dreams docs: one store + 1-100 sessions in, new store out, input never modified)")
    inp = d.get("inputs") or {}
    if not inp.get("exactly_one_input_store"):
        f.append("D-1 the input is not exactly one pre-existing memory store (a dream verifies/dedupes/reorganizes that one store; feeding several stores or none is outside the job shape)")
    if not inp.get("sessions_between_1_and_100"):
        f.append("D-1 the session batch is not bounded to 1-100 past sessions (outside that range the create is invalid; unbounded history dumps are not a dream input)")
    if not inp.get("input_store_treated_as_immutable"):
        f.append("D-1 the input store is not treated as immutable (the dream never modifies its input; any flow that edits the input in place loses the review-and-discard safety the shape provides)")
    st = d.get("steering") or {}
    if not st.get("model_supported"):
        f.append("D-2 the dreaming model is not confirmed against the supported list (Fable 5.2/5.1/5, Opus 5.5/5/4.8/4.7, Sonnet 5.5/5/4.6 in the docs; an unsupported model cannot run the pipeline)")
    if not st.get("instructions_high_level_only"):
        f.append("D-2 instructions are used as line edits (the pipeline is a synthesis pass: line-targeted directives generally produce no change; instructions are for focus, preservation and output conventions)")
    if not st.get("targeted_edits_via_memory_stores_api"):
        f.append("D-2 targeted edits to individual memories are not routed to the Memory Stores API on the output store (asking the dream to fix a sentence is the known no-op path)")
    lc = d.get("lifecycle") or {}
    if not lc.get("async_poll_by_id"):
        f.append("D-3 the dream is not tracked as an async job polled by ID (minutes to a few hours; a synchronous wait or a fire-and-forget both misread the surface)")
    if not lc.get("empty_outputs_while_running_tolerated"):
        f.append("D-3 an empty outputs array while running is treated as failure (the output ID appears only after the input is cloned; early emptiness is the documented normal state)")
    if not lc.get("cancel_archive_semantics_known"):
        f.append("D-3 cancel/archive semantics are not recorded (cancel completed/failed = 400, archive is terminal-only with no unarchive, archiving a dream does not touch its output store)")
    out = d.get("output") or {}
    if not out.get("reviewed_before_adoption"):
        f.append("D-4 the output store is not reviewed before adoption (the whole point of a separate output is review-then-use-or-discard; auto-swapping an unreviewed consolidation into every future session spreads its errors everywhere)")
    if not out.get("discard_path_known"):
        f.append("D-4 the discard path is not known (delete or archive the output store via the Memory Stores API; without it a bad dream output has no clean exit)")
    if not out.get("partial_output_on_failure_handled"):
        f.append("D-4 partial output on failed/canceled is not handled (the output store persists with partial contents; leaving it uninspected risks a later session mounting a half-consolidated store)")
    co = d.get("cost_errors") or {}
    if not co.get("usage_read_from_resource"):
        f.append("D-5 usage is not read from the dream resource (billing is standard token rates for the chosen model and the resource reports exact totals; estimating instead of reading repeats the unverified-numbers failure)")
    if not co.get("start_small_batch"):
        f.append("D-5 the first run is not a small batch (cost scales roughly linearly with session number/length; the docs' own advice is start small and scale once curation quality is proven)")
    if not co.get("error_types_handled"):
        f.append("D-5 the documented error types are not handled (timeout, internal_error, memory_store_org_limit_exceeded, input_memory_store_too_large, input_memory_store_unavailable, input_session_unavailable - each has a different fix, from shrinking the store to re-checking that inputs still exist)")
    return f

if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    fails = check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        for x in fails:
            print(" -", x)
        sys.exit(1)
    print("PASS (0 fails) --", data.get("app", ""))
