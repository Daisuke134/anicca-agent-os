#!/usr/bin/env python3
"""long-running-harness-check: deterministic gate for the LONG-RUNNING
AGENT HARNESS surface (initializer agent sets up the environment on the
first run, coding agents then make incremental progress one feature at
a time across many context windows, leaving clean state, git commits
and a progress file for the next session, testing end-to-end as a human
before marking a feature done, and running a get-up-to-speed procedure
at the start of every session instead of relying on compaction alone).
Stdlib only, offline.
Canonical source (read in full 2026-11-18, Anthropic Engineering,
"Effective harnesses for long-running agents",
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents,
published 2025-11-26):
- Agents work in discrete sessions; each new session starts with no
  memory. Compaction alone is not sufficient: out of the box a frontier
  model given only a high-level prompt one-shots, runs out of context
  mid-feature leaving it half-implemented and undocumented, or later
  looks around, sees progress, and declares the job done.
- Two-part fix: (1) an initializer agent on the very first run sets up
  init.sh, a claude-progress.txt log and an initial git commit, plus a
  comprehensive feature list (200+ features in the example) in JSON,
  all initially marked failing, editable only in the passes field -
  removing or editing tests is unacceptable. (2) a coding agent in
  every later session works on only one feature at a time, commits
  with descriptive messages, writes structured progress updates, and
  leaves the environment in a clean state fit to merge to main.
- Testing: agents tend to mark features complete without proper
  testing; explicitly prompted to use browser automation and test
  end-to-end as a human user would, they find bugs invisible in code.
- Getting up to speed: each session runs pwd, reads git logs and the
  progress file, reads the feature list and picks the highest-priority
  unfinished feature, runs init.sh and a basic end-to-end smoke test
  before new work, and fixes a broken starting state first; git can
  revert bad changes and recover working states.
- Open questions kept open: single general-purpose agent vs specialized
  testing / QA / cleanup agents, and generalization beyond full-stack
  web apps - neither is settled by the article.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("LH-0 the long-running harness surface is not recorded as a decided surface - how work survives across context windows is left to per-session habit")
    if not dec.get("owner_recorded"): f.append("LH-0 no owner is recorded for the long-running harness - nobody is named to keep the initializer, progress file and session procedure honest")
    if not dec.get("canonical_source_recorded"): f.append("LH-0 the canonical source is not recorded (Anthropic effective harnesses for long-running agents: initializer + incremental coding agent, JSON feature list, progress file plus git, end-to-end testing, get-up-to-speed procedure) - every project invents its own session bridge")
    ini=d.get("initializer") or {}
    if not ini.get("distinct_initializer_first_session"): f.append("LH-1 there is no distinct initializer session with a different first-run prompt that sets up the environment - the first coding session improvises the foundation every later session depends on")
    if not ini.get("feature_list_comprehensive_json_all_failing"): f.append("LH-1 there is no comprehensive feature list in JSON expanding the prompt, all initially marked failing - later agents have no outline of full functionality to work feature by feature against")
    if not ini.get("init_script_and_initial_commit"): f.append("LH-1 the initializer does not leave an init.sh that runs the dev environment plus an initial git commit showing what was set up - starting the environment is re-derived every session")
    inc=d.get("incremental") or {}
    if not inc.get("one_feature_at_a_time"): f.append("LH-2 coding sessions are not limited to one feature at a time - the agent one-shots, runs out of context mid-implementation and leaves the next session a half-implemented, undocumented feature to guess at")
    if not inc.get("clean_state_end_of_session"): f.append("LH-2 sessions do not have to leave the environment in a clean state fit to merge to main (no major bugs, orderly, documented) - the next session cleans up an unrelated mess before it can start")
    if not inc.get("progress_file_updated_each_session"): f.append("LH-2 there is no progress file updated with structured summaries every session alongside git history - a fresh context window cannot quickly understand the state of work")
    tst=d.get("testing") or {}
    if not tst.get("e2e_testing_as_human_before_done"): f.append("LH-3 features are not verified end-to-end as a human user would (browser automation for web apps) before being marked done - unit tests and curl miss the bugs only the real flow shows")
    if not tst.get("tests_immutable_only_status_editable"): f.append("LH-3 the feature / test list is not protected: agents may edit or remove tests instead of changing only the passes status - missing or buggy functionality can be hidden by editing the spec")
    if not tst.get("smoke_test_before_new_feature"): f.append("LH-3 no basic end-to-end smoke test runs before implementing a new feature - a broken starting state is built on and made worse instead of fixed first")
    spd=d.get("speed") or {}
    if not spd.get("bearings_procedure_pwd_logs_progress_featurelist"): f.append("LH-4 there is no get-up-to-speed procedure (pwd, read git logs and progress file, read the feature list, pick the highest-priority unfinished feature) - every session re-orients from scratch and burns tokens figuring out how to test")
    if not spd.get("broken_state_fixed_before_new_work"): f.append("LH-4 a starting state found broken is not fixed before new feature work begins - failures compound across sessions instead of being repaired at the boundary")
    if not spd.get("git_revert_recovery"): f.append("LH-4 git is not used to revert bad changes and recover working states - a bad session's damage has no clean rollback")
    evo=d.get("evolution") or {}
    if not evo.get("compaction_not_sole_bridge"): f.append("LH-5 compaction is relied on as the sole bridge between sessions - it does not always pass perfectly clear instructions to the next agent, so the progress file and git history must carry the state instead")
    if not evo.get("premature_completion_guard"): f.append("LH-5 there is no guard against premature completion: an agent that sees progress can declare the job done instead of checking the feature list for what is still failing")
    if not evo.get("specialization_and_generalization_reviewed"): f.append("LH-5 the open questions are never reviewed (single general-purpose agent vs specialized testing / QA / cleanup agents, and generalization beyond the original domain) - the harness shape is frozen by default, not by decision")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
