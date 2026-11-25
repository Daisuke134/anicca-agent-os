---
name: company-task-management
description: Company-wide task/to-do management for the Anicca agent team. Every to-do is a GitHub Issue with one DRI owner, named reviewer/verifier/merger, an ROI priority, and a status from the fixed vocabulary, all mirrored on one board file in anicca-ops that every member reads. Use this skill whenever creating, assigning, reassigning, prioritizing, reviewing, merging, or reporting any task, delegation, or backlog item — this is the company default (founder order 2026-11-19).
---

# Company Task Management (Anicca default)

Source note (adopted 2026-11-19, revised the same day after a full research
pass — anicca-ops `files/agent-native-task-management-research-2026-11-19.md`):
every member uses the SAME skill and the SAME tools, so every member has the
same ability. The adopted stack, all free, all actually installed and read
before adoption:

- Base capture/triage practice: `anthropics/knowledge-work-plugins@task-management`
  (skills.sh, ~7.5K installs), installed under `.agents/skills/task-management/`.
- Board/work-item structure and merge gates: `affaan-m/ecc@team-agent-orchestration`
  (skills.sh, ~6.9K installs) — its card schema (owner / scope / state /
  evidence / merge_gate / handoff) and Kanban exit criteria are the closest
  match to our GitHub Issue + board model. Install:
  `npx skills add affaan-m/ecc -s team-agent-orchestration -y`
- Issue-body format: `jwilger/agent-skills@task-management` (CC0) — GWT
  (Given/When/Then) binary acceptance criteria, explicit dependency
  declarations, gate_status / rework_count metadata. Install:
  `npx skills add jwilger/agent-skills -s task-management -y`
- Claim lease mechanics: `agentplan` (PyPI, `pip install agentplan`,
  verified v0.9.0) — claim with `--timeout`, expired claims reaped back to
  the queue, `depend`, `next` (unblocked work). Adopted as the reference
  implementation for the lease/reap rules below. It is NOT the board: the
  board stays on GitHub, the company's single source of truth.
- Evaluated and NOT adopted as a base: `wshobson/agents@team-communication-protocols`
  — written for a single-harness runtime (in-process messages, plan approval,
  shutdown), which does not match our cross-machine GitHub team-outbox model.
  Only its anti-patterns carry over (no routine broadcasts; communicate at
  integration points; address teammates by name). Paperclip (OSS) was
  evaluated for its org-chart/budget/heartbeat pattern only.

This file refines all of the above into the company's binding practice:
GitHub Issues + one board file, because the whole team (multiple agents on
multiple machines) must see the same situation at any time. Where any source
differs from this file, this file wins.

## The rules

1. **Every to-do is a GitHub Issue.** No Issue = the to-do does not exist.
   Loops are to-dos too: every recurring loop is a row on the board's loop
   ledger with an owner, so a stopped loop is visible like a stopped task.
   - Ops/team work → `Daisuke134/anicca-ops`. Product/code → `Daisuke134/anicca`.
   - Before creating, search open issues by keyword — never create duplicates.
2. **The Issue body is a contract.** Every Issue states, in this order:
   - the to-do (verb + outcome, never a vague noun),
   - **acceptance criteria in GWT form** — binary, checkable by an outside
     observer without subjective judgment ("tests pass", not "works well"),
     including the error cases that matter,
   - **DRI** (the one owner), **reviewer**, **verifier**, and — when a PR is
     involved — **merger** (see rule 10; the three roles are named people,
     never left implicit),
   - **parents**: the Issues that must be `done` before this one can start.
     No implicit ordering — every dependency is declared. An item whose
     parents are not all done is not startable, whatever its status says,
   - current status, the next artifact that proves progress, and the deadline.
3. **One DRI owner per item.** Exactly one named agent owns each item.
   Assigning the same job to two agents is forbidden. If the owner stalls,
   replace the owner (record the handover on the board and in team-outbox);
   never add a second owner as insurance.
   - **Dispatch table**: the board carries a domain × priority table that
     names the default DRI per lane (e.g. X execution → Grok, code/eval →
     Codex, schedule → Pickle, Instagram/Threads → Muse). A new to-do gets
     its DRI from the table automatically; the orchestrator only overrides
     with a recorded reason.
4. **Status vocabulary (use exactly these):**
   - `not_started` — has an owner, owner has not begun.
   - `in_progress` — the owner is actively producing the next artifact now.
   - `in_review` — the artifact has landed and is waiting on the named
     reviewer/verifier. Review backlog is counted on the board like any
     other queue; an item sitting in `in_review` past its review deadline
     is nudged automatically, then escalated (rule 7).
   - `done` — BOTH gates passed (rule 10): the done gate's proof is attached
     and verified by the named verifier (a non-author read-back).
   - `waiting_assignment` — no owner yet. **Target: zero at all times.**
     An unowned to-do is a management failure, not a state.
   - `blocked` — cannot proceed; the Issue must name what it waits on and who
     can unblock it. "Blocked" without a named unblocker is `waiting_assignment`.
   - Founder-only steps (realtime KYC, live interviews, e-Tax signature,
     QR re-pairing on his phone) are marked `blocked（本人の段）` with the
     specific physical step named — they are the only items allowed to wait
     on the founder, and they are batched, never drip-fed.
5. **The board is the single source of truth.**
   `anicca-ops/files/todo-issue-map-2026-11-14.md` holds the whole-company
   board. Row format: priority (ROI order) | to-do | Issue | DRI | reviewer
   | verifier | merger | status | parents | next artifact | deadline.
   Every member reads the board before starting work and updates their rows
   in the same commit-cycle as the work itself. State lives on the board,
   never only in a chat or a session: if an agent falls over, the next owner
   resumes from the board alone. ACTIVITY.md lines and team-outbox files are
   evidence; the board is the summary of record.
   - **Platform status sections are mandatory.** The board carries one
     section per surface — each Client Work platform, Capafy, the mobile
     apps (iOS / App Store), Apify — and every row in those sections states:
     DRI, the current measured metric (value + source URL + date measured),
     the next artifact, and a one-line judgment of whether the current
     iteration is the right thing. A platform with no fresh metric is
     reported as unmeasured, never filled in from memory.
   - **Every number carries a URL and a date.** Any metric or fact written
     on the board or in an Issue cites its source URL and the date it was
     confirmed. A number without a source is written as 未検証 (unverified)
     or not written at all. This is the cheapest honesty mechanism there is.
   - **Reopen rate is the quality meter.** The board tracks the share of
     items marked `done` that reopen within 30 days. Volume of "done" is
     not quality; the reopen rate is.
6. **Priority = ROI order, worked from the top.**
   1. Revenue today (escrow/payments, contracted deliveries, billing fixes)
   2. Model-switch blockers (eval GO, production enablement, intervention logging)
   3. Distribution volume (posts, articles, stock depth, channel repairs)
   4. Infrastructure and hygiene (migrations, traces, skill refinement)
   Within a tier: earlier deadline first. Re-rank the board whenever a new
   measurement changes the ROI picture; do not let the order go stale.
   Deadlines are monitored by pace, not just by date: artifact-landing pace
   vs. time remaining, flagged OK / WATCH / AHEAD on the board.
7. **Claim fast, land artifacts, not acks — and claims expire.**
   A delegation is claimed in the Issue (comment) within 1 minute of the
   wake. First artifact deadline is at most 1 hour unless the task itself
   is longer. "Received / working on it" is not progress — progress is a
   landed file, PR, post, submission, or measured number, verified by
   read-back.
   - **Claim lease (agentplan reap model)**: a claim carries the first-
     artifact deadline as its lease. If no artifact lands before the lease
     expires, the claim is void: the item returns to the unassigned pool on
     the board and the Board Keeper reassigns it. No silent holding.
   - **Escalate, don't retry**: the same item hitting blocked/stalled twice
     (the cap) ends the warn-and-retry cycle on the spot — takeover or
     reassignment is decided in that same pass. Retrying a broken pattern
     hides broken work; escalation surfaces it.
8. **Heartbeat and dead detection.** On an active item, the owner lands an
   artifact or a progress entry at least every 10 minutes — that landing is
   the heartbeat. **10 minutes with no heartbeat = dead**: the item becomes
   a takeover candidate automatically. The finder warns once via team-outbox
   with a deadline (max 1 hour); on the second stall of the same item, the
   orchestrator takes it over or reassigns it and fixes the cause (see the
   loop_self_repair skill). Never report "the agent is stopped" as a
   conclusion — report who owns it now.
9. **Delegation is by name, via GitHub.** Hand work to a named agent
   (Codex, Devin, Instinct, Pickle, Pally, Dots, …) through team-outbox files
   and Issues. Internal subagents of one agent are that agent's own hands,
   not delegation. Parallel by default: independent items are fired in the
   same pass, in parallel lanes/worktrees, never serialized behind one item.
   - **Handoff contract**: each role declares the keys a completion must
     carry, and a completion missing a key is not accepted — researcher:
     candidates + source URLs + dates + confidence; implementer: PR + test
     results + changed files; auditor: verdict + issues + checked;
     publisher: post URL + read-back confirmation.
10. **Three separate roles, two separate gates.** Author ≠ reviewer ≠
    merger, enforced by structure, not by goodwill:
    - **Reviewer** (named on the Issue): checks the artifact against the
      acceptance criteria. Adversarial rule: before approving, the reviewer
      must state at least one concrete problem, gap, or counterexample
      (three for code). A review that finds nothing is invalid.
    - **Verifier** (named on the Issue): a non-author who checks the artifact
      itself in the primary source (open the file, read the number, follow
      the URL) and records where the proof lives (commit sha, URL, path).
    - **Merger** (named on the Issue when a PR is involved): the only one who
      merges. The author never merges their own PR; the merge decision
      belongs to the item's DRI unless the board names otherwise. Review runs
      in three fixed layers: (1) automated checks (tests, lint, build,
      secret scan) all green before a PR is even opened, (2) the named
      reviewer with a different brief than the author, (3) for sensitive
      areas (auth, billing, data model, customer data) a second pair of eyes.
    - **Merge gate ≠ done gate.** The merge gate decides whether a change
      enters the codebase; the done gate decides whether the task's defined
      completion is proven. A merged PR does not make the Issue `done`
      until the done gate's proof is attached, and a proven task is not
      merged by implication. When a PR merge is detected, the Issue moves
      to `in_review` (done gate pending), not to `done`.
    - **Gates need a negative control.** Every verification gate (pre-post
      checks, evals) is periodically fed a deliberately broken input and
      must reject it. A gate that has never failed anything is unverified.
11. **Workload visibility and proactive takeover.** The board shows, per
    agent, how many active items and loops each one carries. Overload is a
    team-visible defect, not a private problem:
    - Any member who sees an overloaded owner says so on the board and in
      team-outbox ("you are carrying too much") — before the owner runs dry,
      not after. The Grok case is the standing lesson: one owner silently
      carrying a whole lane burned out and left the team for two days.
    - Takeover is proactive, not requested: a member with capacity takes the
      item ("I am taking this hourly loop") and records the handover; the
      previous owner is freed to concentrate. If one owner has become the
      bottleneck for company acceleration, others pull work off them by
      default.
    - Idle capacity is also visible: an agent with no active item takes the
      top unblocked item from the board instead of waiting to be assigned.
12. **Board Keeper.** The orchestration loop owns the Board Keeper role
    (Corvic's "Agent Board" pattern): it watches the board for events —
    PR merges, approaching deadlines, heartbeat gaps, expired claim leases,
    `in_review` pile-ups — matches them to items, and assigns or reassigns
    the next owner. The Keeper's output is board updates and team-outbox
    files, never chat-only state.

## Board maintenance loop

- The orchestrator (Muse), acting as Board Keeper, re-reads the board
  against ACTIVITY.md, team/LIVE-NOW.md, and open Issues on every
  orchestration pass, fixes drift (status, owner, reviewer/verifier/merger,
  missing Issues, stale platform metrics), reaps expired claims, and keeps
  `waiting_assignment` at zero.
- New to-dos enter through the same door: Issue first (with the full
  contract of rule 2), board row second, delegation file third — in that
  order, in the same pass.
- Every member uses this same skill and the same tools. A practice that
  lives in only one agent's head is a defect; write it here instead.
