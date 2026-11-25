---
name: delegate-first
description: Activate when the user requests delegation-first execution or invokes /delegate-first. The main agent plans and verifies; subagents execute.
---

# Delegate First

## Roles

- **Main agent:** Define goals, constraints, strategy, acceptance criteria, and final delivery. Independently verify outcomes.
- **Subagents:** Execute research, coding, edits, tests, and fixes autonomously; return artifacts and evidence.
- **Model selection:** The main agent chooses an available subagent model suited to the task, with a capability tier **no higher than its own**. Prefer the least costly model likely to meet the acceptance criteria. Where cross-provider tiers are unclear, use a clearly lower-tier option or disclose the uncertainty.

## Workflow

1. **Scope:** Identify inputs, deliverables, constraints, and testable success criteria.
2. **Delegate:** Prefer one subagent per coherent task; parallelize only independent work. Supply relevant context, paths, permissions, and acceptance criteria.
3. **Execute:** Give subagents discretion over implementation and routine troubleshooting. Escalate decisions affecting scope, permissions, or major risks.
4. **Verify:** Review artifacts, diffs, sources, or test evidence in proportion to risk. Treat completion claims as reports, not proof.
5. **Correct:** Return specific failures and pass conditions to the subagent. After repeated failure, revise scope or take over essential work.
6. **Deliver:** Report the result, verification status, and remaining issues concisely.

## Efficiency

Delegate substantive execution by default. The main agent handles judgment, brief checks, and tasks where delegation costs more than direct work. Pass only necessary context; request concise, evidence-backed reports. Update the user at meaningful milestones or when a decision is needed.

Apply this mode when invoked, until the user ends it. Model routing depends on available tools and configuration.

## Verification (mandatory, added 2026-11-17)

A delegation under this skill is verified, not merely returned. Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) Every delegated task carried testable acceptance criteria written before execution started; work delegated without criteria is a brief failure, not a worker failure. (b) The subagent's model tier never exceeds the main agent's own tier. (c) No completion claim from a subagent is reported upward as fact until the main agent has opened the artifact it names — a summary of the work is not the work.
2. **Grader.** The main agent grades against the criteria, and for high-risk work (external sends, production changes, money movement) a second, different check — another subagent or a deterministic tool — re-verifies the artifact before delivery. The executing subagent never grades its own output.
3. **E2E evidence.** Open the landed artifact itself: read the full diff, the file, or the test output, in the form its real consumer will use it. A test suite is run, not described; a document is read, not skimmed by title.
4. **Differential oracle.** The acceptance criteria from the Scope step are the oracle, kept verbatim from before execution began. Criteria edited after seeing the result invalidate the grade — re-scope openly instead.
5. **Repeat failures.** The same acceptance criterion failed twice by the same route means the scope or the route changes (revise, split, or take over), and the failure mode is written into the next brief as an explicit check.
