#!/usr/bin/env python3
"""eval-design-check: deterministic gate for agent-eval suite design.

Source of the gates: Anthropic, "Demystifying evals for AI agents"
(2026-01-09), read in full on 2026-11-14.
https://www.anthropic.com/research/demystifying-evals-for-ai-agents

Input: a JSON description of an eval suite's *design and operation*.
This checker judges the design record only. It does not run any eval,
and a PASS here never means the agent itself is good.

Gates:
  ED-0  Suite identity: name, owner, and what decision the suite informs
        are recorded. (Step 8: suites are living artifacts with owners.)
  ED-1  Capability vs regression split: both suites exist (or a recorded
        reason one does not), capability starts at a low pass rate,
        regression sits near 100%, and mastered capability tasks
        "graduate" into the regression suite.
  ED-2  Task provenance and size: tasks come from real failures / real
        usage, and the suite size is recorded (20-50 real-failure tasks
        is Anthropic's stated great start; larger is fine, unrecorded
        is not).
  ED-3  Task quality: every task is unambiguous (two experts would give
        the same verdict) and has a reference solution that passes all
        graders, proving the task is solvable and graders are wired.
  ED-4  Balanced problem sets: both should-occur and should-not-occur
        cases are present (one-sided sets create one-sided optimization).
  ED-5  Non-determinism handling: trials per task > 1 for agent suites,
        and the reported metric matches the product need
        (pass@k when one success is enough, pass^k when consistency is
        essential, e.g. customer-facing agents). A single-run accuracy
        with no trial structure fails.
  ED-6  Grader design: graders grade the outcome (final state), not only
        the transcript/path; deterministic graders are preferred where
        possible; LLM judges, if used, are calibrated against humans and
        have an "Unknown" escape; partial credit exists for multi-part
        tasks.
  ED-7  Long-term health: transcripts are actually read on a recorded
        cadence (failures must look fair), saturation is monitored
        (a suite at 100% gives no improvement signal), and the harness
        isolates trials (clean environment per trial, no shared state).

Exit code 0 = PASS (no failures), 1 = FAIL. Warnings never fail alone.
"""
import json
import sys

FAILS = []
WARNS = []


def fail(gate, msg):
    FAILS.append(f"[{gate}] {msg}")


def warn(gate, msg):
    WARNS.append(f"[{gate}] {msg}")


def check(d):
    # ED-0 identity / ownership
    if not d.get("suite_name"):
        fail("ED-0", "suite_name is not recorded")
    if not d.get("owner"):
        fail("ED-0", "owner is not recorded (a suite without an owner rots)")
    if not d.get("decision_informed"):
        fail("ED-0", "decision_informed is not recorded (what ships/changes based on this suite?)")

    # ED-1 capability vs regression split
    split = d.get("split") or {}
    if not split.get("capability_exists"):
        fail("ED-1", "no capability suite recorded (what can it do? where is the hill?)")
    if not split.get("regression_exists"):
        fail("ED-1", "no regression suite recorded (what stops backsliding?)")
    cap_rate = split.get("capability_pass_rate")
    if cap_rate is not None and cap_rate >= 0.95:
        fail("ED-1", f"capability pass rate {cap_rate} is ~saturated; it gives no improvement signal (graduate tasks and add harder ones)")
    if cap_rate is None and split.get("capability_exists"):
        warn("ED-1", "capability pass rate not recorded; saturation cannot be judged")
    reg_rate = split.get("regression_pass_rate")
    if reg_rate is not None and reg_rate < 0.95:
        fail("ED-1", f"regression pass rate {reg_rate} is below the near-100% bar; a drop means something is broken and must be treated as such")
    if not split.get("graduation_rule_recorded"):
        fail("ED-1", "no graduation rule recorded (mastered capability tasks -> regression suite)")

    # ED-2 provenance and size
    prov = d.get("tasks") or {}
    n = prov.get("count")
    if n is None:
        fail("ED-2", "task count is not recorded")
    elif n < 20:
        warn("ED-2", f"task count {n} is below Anthropic's 20-50 real-failure starting range (acceptable only as a recorded early stage)")
    if not prov.get("from_real_failures"):
        fail("ED-2", "tasks are not recorded as drawn from real failures / real usage (synthetic-only suites drift from the product)")
    if not prov.get("prioritized_by_user_impact"):
        warn("ED-2", "task prioritization by user impact is not recorded")

    # ED-3 task quality
    q = d.get("task_quality") or {}
    if not q.get("unambiguous_verdicts"):
        fail("ED-3", "unambiguous verdicts not established (two experts, same pass/fail call); ambiguity becomes metric noise")
    if not q.get("reference_solution_passes_all_graders"):
        fail("ED-3", "no reference solution recorded as passing all graders; solvability and grader wiring are unproven")
    if not q.get("grader_checks_visible_from_task"):
        fail("ED-3", "not recorded that everything the grader checks is stated in the task (agents must not fail on hidden expectations)")

    # ED-4 balance
    b = d.get("balance") or {}
    if not b.get("has_should_occur"):
        fail("ED-4", "no should-occur cases recorded")
    if not b.get("has_should_not_occur"):
        fail("ED-4", "no should-not-occur cases recorded (one-sided evals create one-sided optimization: over/under-triggering goes unmeasured)")

    # ED-5 non-determinism
    nd = d.get("nondeterminism") or {}
    trials = nd.get("trials_per_task")
    if trials is None:
        fail("ED-5", "trials_per_task is not recorded; a single run cannot represent a stochastic agent")
    elif trials < 2:
        fail("ED-5", f"trials_per_task={trials}: one trial per task; pass@k / pass^k are undefined and run-to-run variance is invisible")
    metric = nd.get("metric")
    if metric not in ("pass@k", "pass^k", "pass@k+pass^k"):
        fail("ED-5", f"metric {metric!r} is not a pass@k / pass^k family metric matched to the product need")
    need = nd.get("product_need")
    if need == "consistency_essential" and metric == "pass@k":
        fail("ED-5", "product needs consistency (customer-facing) but only pass@k is reported; pass^k is the consistency metric")

    # ED-6 graders
    g = d.get("graders") or {}
    if not g.get("grades_outcome_not_only_path"):
        fail("ED-6", "graders do not grade the outcome/final state, or grade only the path (rigid step checks punish valid solutions)")
    if g.get("uses_llm_judge"):
        if not g.get("llm_judge_calibrated_with_humans"):
            fail("ED-6", "LLM judge is used without recorded calibration against human experts")
        if not g.get("llm_judge_has_unknown_escape"):
            fail("ED-6", "LLM judge has no 'Unknown' escape; forced verdicts hallucinate grades")
    if not g.get("partial_credit_for_multipart"):
        warn("ED-6", "no partial credit for multi-part tasks; near-misses and total failures score the same")

    # ED-7 long-term health
    h = d.get("health") or {}
    if not h.get("transcripts_read_cadence_recorded"):
        fail("ED-7", "no recorded cadence for reading transcripts; unfair graders and ambiguous tasks stay invisible")
    if not h.get("saturation_monitored"):
        fail("ED-7", "saturation is not monitored; a suite at 100% silently stops giving improvement signal")
    if not h.get("trials_isolated_clean_env"):
        fail("ED-7", "trial isolation (clean environment per trial, no shared state) is not recorded; shared state corrupts trials")


def main():
    if len(sys.argv) != 2:
        print("usage: eval_design_check.py <suite-design.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    check(d)
    for w in WARNS:
        print(f"WARN  {w}")
    for f_ in FAILS:
        print(f"FAIL  {f_}")
    print(f"RESULT: {'PASS' if not FAILS else 'FAIL'} ({len(FAILS)} failures, {len(WARNS)} warnings)")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
