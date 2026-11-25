#!/usr/bin/env python3
"""memory-check: deterministic gate for the AGENT MEMORY surface
(persistent memory across conversations: a client-side store outside the
context window, checked at the start of every session, written under
relevance guidance, updated in place instead of appended into
contradiction, retrieved just-in-time in relevant selection, actually
influencing decisions, paired with compaction/context editing, guarded
by path-traversal and scope validation, stripped of sensitive data with
size caps, honoring expiration and user deletion, evaluated against
outcomes, cleaned under a forgetting policy, and versioned as a schema
whose changes are evaluated before promotion).
Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic Claude Platform Docs,
"Memory tool", https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool):
- The memory tool lets an agent store and retrieve information across
  conversations in a directory of memory files, building knowledge over
  time without keeping everything in the context window. It is
  client-side: the model requests operations, the application runs them
  against storage it controls (per-user directory or database keys).
- Memory supports just-in-time retrieval: record what is learned, read
  it back on demand; the active context stays focused on the current task.
- When the tool is enabled, the agent automatically checks its memory
  directory before starting a task, and the directory is kept organized.
  Writes can be guided ("only write information relevant to <topic>").
- Commands are view / create / str_replace / insert / delete / rename:
  updates replace text in place; delete must reject the memory root;
  rename must not overwrite an existing destination.
- Security is the application's responsibility: validate every path
  stays inside /memories (canonical resolution, reject ../, ..\\ and
  URL-encoded traversal), strip sensitive information before writing,
  track file sizes and cap growth / view returns, and periodically
  delete files not accessed in a long time (memory expiration).
- Pair memory with compaction and context editing for long-running
  agents: compaction keeps the active context small, memory preserves
  what must survive summarization.
- Multisession pattern: an initializer session sets up deliberate memory
  files (progress log, feature checklist) before substantive work; each
  later session opens by reading them; each session ends by updating
  the log; a feature is marked complete only after end-to-end
  verification, so the log stays accurate across sessions.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("ME-0 the agent-memory surface is not recorded as a decided surface - what the agent remembers across conversations, where, and under what rules, is left to habit")
    if not dec.get("owner_recorded"): f.append("ME-0 no memory owner is recorded - nobody is named to keep what is stored, stale entries and memory-driven mistakes honest")
    if not dec.get("canonical_source_recorded"): f.append("ME-0 the canonical source is not recorded (Anthropic Memory tool: client-side persistent files outside the context window, checked at session start, just-in-time retrieval, in-place updates, path/scope security, expiration, paired with compaction) - every surface invents its own remembering")
    st=d.get("storage") or {}
    if not st.get("persistent_store_outside_context"): f.append("ME-1 there is no persistent memory store outside the context window - everything the agent learns dies with the conversation, and long work restarts from re-exploration every session")
    if not st.get("scoped_per_user_or_agent_isolated"): f.append("ME-1 memory is not scoped and isolated per user / per agent (per-user directory or keys, one principal cannot read another's store) - memories leak across the very people they describe")
    if not st.get("checked_at_start_of_session"): f.append("ME-1 memory is not checked at the start of every session / task - stored knowledge exists but is never the starting point, so prior decisions get retraced and contradicted")
    wr=d.get("writing") or {}
    if not wr.get("write_criteria_relevance_guided"): f.append("ME-2 there are no write criteria (what is relevant enough to store is unguided) - memory fills with clutter until retrieval returns noise instead of signal")
    if not wr.get("updates_replace_stale_not_append_only_contradictions"): f.append("ME-2 updates do not replace stale text in place (str_replace-style) - append-only memory accumulates contradictory versions of the same fact and the agent cannot tell which one is current")
    if not wr.get("provenance_and_freshness_recorded"): f.append("ME-2 entries carry no provenance or freshness (source, date, last-verified) - a memory from a superseded decision is read with the same confidence as a current one")
    us=d.get("use") or {}
    if not us.get("retrieved_just_in_time_relevant_selection"): f.append("ME-3 memory is not retrieved just-in-time in relevant selection (whole store dumped up front, or never read back) - either the context window drowns in old notes or the memory never affects the task it was kept for")
    if not us.get("memory_actually_influences_decisions_and_logged"): f.append("ME-3 there is no record that memory actually influenced a decision (which entry, used for what, in the decision log / trace) - 'we have memory' is asserted while behaviour is indistinguishable from having none")
    if not us.get("paired_with_compaction_or_context_editing"): f.append("ME-3 memory is not paired with compaction / context editing for long-running work - what must survive summarization is not separated from what can be summarized away, so long sessions lose exactly the facts they needed to keep")
    sa=d.get("safety") or {}
    if not sa.get("path_traversal_and_scope_validation"): f.append("ME-4 memory operations are not validated to stay inside the memory scope (canonical path resolution, rejection of ../, ..\\ and URL-encoded traversal, root itself undeletable) - a requested path can read or overwrite files outside memory")
    if not sa.get("sensitive_data_stripped_and_size_capped"): f.append("ME-4 sensitive information is not stripped/validated before writing and file size / view size are not capped - memory becomes an unguarded second copy of secrets and grows until retrieval is unusable")
    if not sa.get("expiration_and_user_deletion_honored"): f.append("ME-4 there is no expiration for long-unaccessed memory and no honored user-deletion path - the agent remembers forever by default, including what the person asked to forget")
    ev=d.get("evolution") or {}
    if not ev.get("memory_quality_evaluated_against_outcomes"): f.append("ME-5 memory quality is never evaluated against outcomes (does having this memory change results; do stale entries cause measurable harm) - a memory system that hurts is indistinguishable from one that helps")
    if not ev.get("forgetting_and_cleanup_policy_applied"): f.append("ME-5 no forgetting / cleanup policy is applied in practice (periodic review, superseded entries removed, progress log updated at session end and features marked complete only after end-to-end verification) - the store drifts from the world it describes")
    if not ev.get("memory_schema_versioned_and_changes_evaluated"): f.append("ME-5 the memory schema / organization is not versioned and changes to it are not evaluated before promotion - a reorganization silently breaks every reader that depended on the old shape")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
