#!/usr/bin/env python3
"""dataset-task-check: deterministic gate for the EVAL DATASET / TASK DESIGN
surface (how eval tasks are collected, specified and maintained).
Stdlib only, offline, free.
Canonical source (read in full 2026-11-17, Anthropic Engineering,
"Demystifying evals for AI agents", published 2026-01-09,
https://www.anthropic.com/research/demystifying-evals-for-ai-agents):
- Start early: 20-50 simple tasks drawn from real failures is a great start.
- Start with what you already test manually; convert user-reported failures
  (bug tracker / support queue) into test cases, prioritised by user impact.
- Write unambiguous tasks with reference solutions: two domain experts would
  independently reach the same pass/fail verdict; everything the grader
  checks must be clear from the task description; a reference solution proves
  the task is solvable and the graders are configured correctly; 0% pass@100
  is most often a broken task, not an incapable agent.
- Build balanced problem sets: test cases where a behaviour should occur AND
  where it shouldn't; one-sided evals create one-sided optimisation.
- Capability evals start at a low pass rate (a hill to climb); regression
  evals should have a nearly 100% pass rate; high-pass capability tasks
  graduate to the regression suite.
- Non-determinism: run multiple trials per task; pass@k = at least one
  success in k attempts; pass^k = all k trials succeed (consistency, for
  customer-facing agents).
- Harness: each trial isolated from a clean environment; grade what the
  agent produced (outcome), not the path it took; build in partial credit.
- Step 6: read transcripts; failures should seem fair; never take scores at
  face value until transcripts are read.
- Step 7: monitor capability eval saturation (100% = regression signal only).
- Step 8: suites are living artifacts with clear ownership; domain experts
  contribute tasks; practise eval-driven development.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("DT-0 eval dataset / task design is not recorded as a decided surface - tasks accumulate ad hoc and nobody can say what the suite is supposed to measure")
    if not dec.get("owner_recorded"): f.append("DT-0 no single suite owner is recorded (Anthropic Step 8: suites are living artifacts with clear ownership, domain experts contribute tasks) - an unowned suite rots silently")
    if not dec.get("canonical_source_recorded"): f.append("DT-0 the canonical source is not recorded (Anthropic, Demystifying evals for AI agents: start early, unambiguous tasks with reference solutions, balanced sets, capability vs regression) - every suite invents its own task quality rule")
    fou=d.get("foundation") or {}
    if not fou.get("tasks_from_real_failures"): f.append("DT-1 tasks are not drawn from real failures / manual checks / bug tracker / support queue - the suite measures invented cases while production failures go untested")
    if not fou.get("unambiguous_two_expert_test"): f.append("DT-1 tasks have not passed the two-expert test (two domain experts independently reach the same pass/fail verdict; everything graded is clear from the task description) - ambiguity in the spec becomes noise in the metric")
    if not fou.get("reference_solution_per_task"): f.append("DT-1 there is no reference solution per task (a known working output that passes all graders) - solvability is unproven and grader misconfiguration is indistinguishable from agent failure")
    des=d.get("design") or {}
    if not des.get("balanced_positive_negative"): f.append("DT-2 the problem set is not balanced (cases where the behaviour should occur AND where it should not) - one-sided evals create one-sided optimisation, e.g. an agent that over-triggers")
    if not des.get("capability_regression_split"): f.append("DT-2 capability and regression tasks are not split (capability starts low as a hill to climb; regression stays near 100%; graduated tasks move across) - one mixed number hides both stagnation and backsliding")
    if not des.get("initial_size_in_range"): f.append("DT-2 the initial suite is not in the start-early range (20-50 simple tasks) or its size is unrecorded - too few tasks cannot detect change, and waiting for hundreds delays the eval indefinitely")
    met=d.get("metrics") or {}
    if not met.get("multiple_trials_per_task"): f.append("DT-3 tasks are not run with multiple trials - a single stochastic run is read as a capability fact, and a task that passed once may fail next run unnoticed")
    if not met.get("pass_metrics_chosen"): f.append("DT-3 neither pass@k nor pass^k is chosen per product requirement (pass@k: one success in k is enough; pass^k: all k must succeed, for customer-facing consistency) - the headline number does not match what users need")
    if not met.get("zero_pass_triage"): f.append("DT-3 there is no zero-pass triage rule (0% across many trials, e.g. 0% pass@100, is treated first as a broken task / grader bug, not as agent incapacity) - broken tasks get reported as model failures")
    har=d.get("harness") or {}
    if not har.get("isolated_clean_environment"): f.append("DT-4 trials are not isolated from a clean environment (leftover files, cached data, shared state) - correlated infra failures and leaked prior-trial state contaminate the measurement")
    if not har.get("grade_outcome_not_path"): f.append("DT-4 grading is not outcome-first (grade what the agent produced, not a prescribed sequence of steps) - brittle path checks punish valid creative solutions the designers did not anticipate")
    if not har.get("partial_credit"): f.append("DT-4 there is no partial credit for multi-component tasks - an agent that completes most of a task scores the same as one that fails immediately, and the continuum of success is invisible")
    mai=d.get("maintenance") or {}
    if not mai.get("transcripts_read"): f.append("DT-5 transcripts and grades are not read on a cadence (Step 6: failures should seem fair) - scores are taken at face value and grader bugs survive for months")
    if not mai.get("saturation_monitored"): f.append("DT-5 capability saturation is not monitored (a suite at 100% tracks regressions only and gives no improvement signal) - the team hill-climbs a finished hill")
    if not mai.get("suite_health_maintained"): f.append("DT-5 suite health is not maintained as a living artifact (new real failures converted to tasks, stale tasks revised, eval-driven development for planned capabilities) - the suite freezes while the product moves")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
