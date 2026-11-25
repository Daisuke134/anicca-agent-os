---
name: eval-stack
description: Anicca's canonical eval / benchmark / model-improvement stack. Use whenever evaluating a model, a prompt, a notification text, an agent trace, or a product surface; designing a benchmark; comparing models; or deciding whether a change ships. One stack for every agent — do not invent a local method.
metadata:
  version: 1.1.0
  author: Anicca (Muse)
  triggers:
    - eval
    - benchmark
    - ManagerBench
    - model comparison
    - model selection
    - notification eval
    - post-training readiness
---

# Eval Stack — Anicca's One Way to Measure

Every agent (Muse, Codex, Devin, ChatGPT, Grok, Dots, Pickle, Instinct) uses this
stack. If a step is not in here, it is unfinished work: do it the way written here,
then improve this skill. Never grade your own work with a method you invented on
the spot.

## The stack (all free / open source, already installed and run)

| Layer | Tool | Where | What it decides |
|---|---|---|---|
| Eval design | **eval-coach** skill (GitHub BayramAnnakov/eval-coach, MIT) | `files/skills/eval-coach/` in this repo; VM `~/workspace/custom-skills/eval-coach/` | Success definition → dataset design → grader choice → CI automation → production monitoring. 50-40-10 rule; capability vs regression sets stay separate. |
| Execution harness | **promptfoo** (MIT) | VM `~/workspace/tools/promptfoo-eval` (`npx promptfoo@latest eval`) | Declarative YAML eval runs. Deterministic assertions (contains / javascript) run offline with the echo provider at $0. |
| Trace scoring | **rubric-eval** (PyPI, MIT) | VM `~/workspace/tools/rubric-test` | Agent-trace evals: expected / forbidden tools, ToolCallAccuracy, step caps. promptfoo grades text; Rubric grades traces. Semantic / LLM-judge extras are NOT installed (paid-API ban). |
| Causal effect | **jitai-lab** (GitHub Tommycode3/jitai-lab, MIT) | VM `~/workspace/tools/jitai-lab-test` | Micro-randomized trial (MRT) proximal-effect estimation with the WCLS estimator (Boruvka et al. 2018). Use for "did the intervention change the person", never vanity metrics. |
| External bench (canonical yardsticks) | **BehaviorBench** (arXiv 2606.24162), **Psych101** (Centaur), **SSR** official package (pymc-labs/semantic-similarity-rating) | paper / GitHub | The yardsticks themselves, used as-is — see "Benchmark policy" below. We do not build a competing home-grown bench. |

Primary sources (read before designing anything):
- Anthropic, "Demystifying evals for AI agents" (2026-01-09)
- Hamel Husain, "Your AI Product Needs Evals" / "LLM Evals FAQ"
- Langfuse, "Turn user feedback on AI responses into evaluation datasets"
- Anthropic, "Introducing Contextual Retrieval"; "How we built our multi-agent research system"

## Benchmark policy — off-the-shelf is canonical (founder ruling, 2026-11-22)

Connect the dots: the yardstick is an existing, proven benchmark, used
as-is. Building our own model or benchmark while saying "connect the dots"
is a contradiction (founder, 2026-11-22 10:36 JST). Therefore:

- **Canonical yardsticks:** BehaviorBench, Psych101 (Centaur's published
  behavioral-experiment data), the SSR official package (scoring = KS
  similarity + correlation attainment, adopted as-is), and established
  scales (rumination, mindfulness) for effect claims.
- **ManagerBench is not grown as a home-grown yardstick.** Its existing
  assets (frozen restraint-v1 set, case schema, replay CI) remain as
  regression assets and as the pipe that feeds our data into the canonical
  yardsticks — not as a competing bench.
- **What we build is only two things:**
  1. **Connections for data only we hold** — the app's intervention-selection
     log (which words were chosen, with what probability), real user
     responses, expert corrections — plumbed INTO the off-the-shelf
     yardsticks.
  2. **A gap proven missing by measurement** — a named gap, demonstrated
     with numbers, that no existing benchmark covers. As of 2026-11-22 the
     founder's standing judgment is: a good gap has not been found yet.
     Until one is proven, nothing else is built.
- Anything else home-made in the yardstick layer is a Connect-the-dots
  violation and is stopped on sight.

## The method (order is fixed)

1. **Error analysis first.** Read real failures, cluster them into failure
   classes. One class at a time. No grader before the failure taxonomy exists.
2. **Freeze the case set.** Cases are version-controlled; every run executes
   the full frozen set (never a "first N of each label" sample — that bug
   invalidated a whole model comparison on 2026-11-17; fixed in PR #302).
   Claims state their scope exactly (e.g. SELECTED_CASES_ONLY).
3. **Held-out discipline.** Cases used for training / post-training are never
   used for grading. A new model ships only when it beats the current one on
   frozen held-out cases it never trained on. The same discipline binds
   **tuning loops** (prompts, notification text, paywall copy, ASO): keep a
   tuning set and a held-out verification set separate. If the tuning set
   improves while held-out stays flat, that is overfitting — do not ship
   (LangChain, "What Is Eval-Driven Development?", 2026-11-09).
4. **Author ≠ grader.** Whoever built it does not score it. A separate agent
   grades against the rubric; disagreements go to an annotation queue.
5. **Deterministic before semantic.** Grounds-checking validators and string /
   regex graders first; LLM judges only where deterministic checks cannot
   reach, and judge-vs-human agreement is measured (Kappa / F1).
6. **Report cost with every run.** Model comparisons run on already-paid
   credit only, auto-reload OFF, and the run's measured cost is reported with
   the results. Always search for the current latest model versions before a
   comparison — never reuse a stale candidate list.
7. **Per-case diff before adoption.** A change is adopted only with a
   per-case diff table over the frozen set (case / before / after /
   verdict). Averages alone never justify adoption: if the average rises
   while named cases regress, the regressions are listed by name and are
   either fixed or explicitly accepted with the reason recorded.

## Fail-first for new work

No new feature, lane, prompt family, or model change starts building until:

1. The behavior spec is written in pass/fail terms: when it triggers, what
   it does, what it must NOT do, what it must not break.
2. An eval expressing that spec exists and has been **run against the
   current version and confirmed to fail**. An eval written after the fix
   tends to be written so it passes (LangChain, 2026-11-09); the failing
   run, kept as evidence, is what makes the eval a gate instead of a
   decoration.
3. The failing eval is frozen into the case set before implementation
   begins.

Work that starts without a confirmed-failing eval is stopped and sent back
to this step.

## Business mapping — every failure class carries a money model

A failure rate is not a priority. Every standing eval records, per failure
class:

| Field | Meaning |
|---|---|
| Unit cost | What one occurrence costs: a churned subscriber, a refund, inference spend burned, a lost conversion — stated in dollars (or, for suffering outcomes, in the named outcome it prolongs). |
| Frequency | Occurrences per month, measured, not guessed. |
| Monthly loss | Unit cost × frequency. Improvement order is decided by this number. |

Rules:

- If the money model is missing for a failure class, the eval is
  **incomplete** and the gap is recorded as `MONEY_MODEL_MISSING` — never
  silently treated as fine.
- A large failure rate can cost $0 (OpenAI Cookbook: an 85% store-name
  mismatch was capitalization only, zero cost) while a rare miss is the
  expensive one (a missed handwritten X cost $75,000/year). Priorities set
  by rate alone repeat that trap.
- House proof: on OpenRouter / Capafy we lost more than we made because no
  failure was converted to money early (founder, 2026-11-22). The P&L audit
  in the Capafy lane is this section applied; every other eval grows the
  same table.

## The three layers of fixing a model (in this order)

1. **Harness layer (no weight changes).** The generator receives only verified
   grounds (profile fields that actually exist). A deterministic validator
   drops any sentence whose claims have no grounds before it can be sent.
2. **Model selection.** All current candidates (Qwen / DeepSeek V-Flash class
   and peers) measured on the same frozen bench; pick on the numbers.
3. **Weights.** Post-training (Tinker when needed; TRL via the
   `trl-training` / `huggingface-llm-trainer` skills) on real intervention
   logs + expert corrections — the corrected right answer, never the disliked
   output itself.

## Standing evals and their pass criteria

### Notification-text eval (gates the model-driven push sender, PR #941)
- Pass = fabrication **0**, failure rate **< 5%** on the sendable set,
  tone violations **0**. Anything else is NO-GO; the sender does not merge.
- v2–v5 all NO-GO. The surviving fabrication class: sentences that fill in
  motives / wishes / quantities absent from the profile, hedged with a
  speculative ending. v6 attacks exactly that class with three structural
  changes only: grounds required per sentence, a deterministic validator,
  and a claim-decomposing judge.

### ManagerBench (model comparison)
- Policy (2026-11-22): ManagerBench is the name of our eval *operation*
  (data connection + regression assets), not a home-grown yardstick — see
  "Benchmark policy" above. The yardsticks are BehaviorBench / Psych101 /
  SSR, used as-is.
- Synthetic census (restraint-v1, 10 cases, all "do not send" correct) is
  landed and independently re-verified: it measures **restraint only** — it
  says nothing about intervention quality or human effect.
- Real intervention cases are still **0**: the app does not yet log which
  words were chosen with what probability. That logging gap is the single
  biggest hole; closing it outranks any model work.
- Effect claims use established scales (rumination, mindfulness) + MRT/WCLS
  via jitai-lab. No effect claim without a measurement.

## Production feedback loop — wiring status (honest, as of 2026-11-22)

The loop every EDD source treats as the third phase — production failures
flow back into the eval set — is **not fully wired**. Stated as it is:

| Piece | Status |
|---|---|
| Trace landing (Langfuse) | **0 traces landed** — spool backlog; repair owned by anicca-ops #222 (OpenCode). Until traces land, there is no production signal to feed back. |
| Online evaluator on live traces | NOT WIRED (depends on trace landing). |
| Annotation queue | File-based substitute in team-outbox (see eval-coach Step 5, Anicca addition); judge-vs-human agreement (Kappa / F1) is recorded there per cycle. |
| Production failure → golden / regression case | Manual weekly batch until the wiring above lands; every converted case is named in the eval run record. |

Rule: a skill or report must state wiring as it is. Claiming this loop
exists while traces land 0 is a false report. When the status changes, this
table is updated in the same commit as the wiring change.

## Gate checkers (deterministic, self-made, VM `~/workspace/tools/<name>-check/`)

Each takes a state-description JSON and decides Gate items deterministically.
Fixtures (compliant design / Anicca current state / control) live in each
tool's `fixtures/`. Specs: goal workspace
`hidden_files/*-gate-spec-2026-11-18.md`. Run pattern:
`python3 ~/workspace/tools/<name>-check/<name>_check.py <state.json>`

Eval / model / data surface: `production-eval-check`, `eval-design-check`,
`error-analysis-check`, `judge-calibration-check`, `dataset-task-check`,
`training-data-check`, `trace-observability-check`, `model-release-check`,
`rollout-check`, `prompt-version-check`, `feedback-loop-check`,
`annotation-check`, `experiment-design-check`, `retrieval-check`,
`cost-efficiency-check`, `incident-response-check`, `multi-agent-check`,
`workflow-pattern-check`.

Product surface (subset): `first-intervention-check`,
`intervention-evidence-check`, `personalized-nudge-check`,
`synthetic-user-check`, `retention-bench-check`, `subs-bench-check`.

Rule for all gates: a state with no record counts as **absent**, not as
passing. "No trace" means the work cannot be verified and does not count
as done.

## Anti-patterns (banned)

- Reporting a comparison measured on a biased case sample as a population claim.
- Grading with cases the model trained on.
- A benchmark of only "do not send" cases presented as intervention quality.
- Inventing a private scoring method instead of this stack.
- Deciding the production model before the bench numbers exist.
- Closing a search with "does not exist" — search Web, then X, then company
  files, then other agents, and report the search record.
