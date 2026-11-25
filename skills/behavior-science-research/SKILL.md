---
name: behavior-science-research
description: Anicca's complete recipe for behavior-science × AI research. Use whenever researching a behavior problem (rumination, avoidance, habit failure, hard days), extracting an intervention from the literature or the field, turning it into an app nudge / SNS post / onboarding copy, or designing how its effect will be measured. One recipe for every agent — research that does not end in a measurable stimulus→response record is unfinished.
metadata:
  version: 1.0.0
  author: Anicca (Muse)
  triggers:
    - behavior science research
    - behavioral research
    - intervention research
    - rumination research
    - nudge research
    - 行動科学リサーチ
    - 介入リサーチ
---

# Behavior Science Research — Anicca's One Recipe

Every agent (Muse, Codex, Devin, ChatGPT, Grok, Dots, Pickle, Instinct) uses
this recipe. It connects assets that already exist — the behavior-science
skills, the field-expert loop, the paper loop, the persuasion ledger,
ManagerBench — into one pipeline. Do not invent a private research method;
if a step is missing here, do it this way, then improve this skill.

**The thesis this recipe serves:** the company is one pipeline —
behavior simulation (Manager) + behavior benchmark (ManagerBench) +
behavior intervention (the agents / the app). Every research run feeds that
pipeline. A research output is not an essay; it is a **(stimulus → predicted
response → surface → measurement → return path)** record that will become
real behavioral data: how actual people responded to an actual stimulus.

## The recipe (order is fixed)

### Step 1 — Explore the field (find what already exists)

Search in this order, and record the search itself (what was searched,
where, what was found — a search with no record did not happen):

1. **Company files first** — `anicca-ops files/behavior-field-catalog.md`
   (the field catalog, maintained by the daily field-expert loop), past
   paper-loop outputs, the persuasion ledger. Someone on the team may
   already have run this.
2. **Papers** — arXiv / PubMed / Google Scholar for the target pattern
   (e.g. "rumination intervention RCT", "JITAI", "micro-randomized trial").
   Prefer RCTs and meta-analyses over narrative reviews; prefer the
   originator's own paper (Nolen-Hoeksema, Watkins, Kross) over summaries.
3. **X** — practitioners and researchers post results, replications and
   failures there first. Use the fxtwittergo / grok_x_search routes.
4. **GitHub / skills.sh** — existing implementations, datasets and skills
   (`npx skills find <keyword>`). If a tool or dataset exists, use it;
   build only the missing piece (Connect the dots).
5. **Winners in the market** — what the winning apps / accounts already do
   about this pattern (I am, the fixed winner per surface). Field evidence
   counts, labeled as field evidence, never dressed up as a paper.

### Step 2 — Extract the intervention (name the theory and the lever)

From what Step 1 found, extract exactly one candidate intervention per run
and state:

- **Target pattern** — the specific, measurable behavior pattern (not a
  vague theme): e.g. "abstract evaluative rumination after a setback",
  not "feeling bad".
- **Theory / mechanism** — the named framework that says why it works
  (Response Styles Theory, Rumination-Focused CBT, COM-B / Behaviour
  Change Wheel, Hook Model, Cialdini's principles…).
- **Lever** — the specific technique, at BCT-taxonomy granularity where
  possible, chosen with `intervention-lever-selector` when the barrier is
  confirmed.
- **Evidence grade** — RCT / meta-analysis / field winner / practitioner
  claim. State the grade; never upgrade it in the retelling.

### Step 3 — Convert to an implementation (pick the surface)

Translate the lever into words on exactly one primary surface per run
(drafts for other surfaces may be noted, but one is the test surface):

| Surface | Drafting skill | Notes |
|---|---|---|
| App push notification / in-app nudge | `lever-content-drafter` | Must pass the eval-stack notification eval before sending (fabrication 0). The sender is Manager (model-generated), never a static rotation. |
| SNS post / slideshow | `lever-content-drafter` + `slideshow-production` | Copy the fixed winner's format for that surface 100% except wording; the post is an intervention aimed at strangers, measured like one. |
| Onboarding copy / question | `lever-content-drafter` + `design-behavior-change-plan` | One question per screen; answers build the synthetic user the intervention is then personalized from. |

Every drafted line is tagged with its lever and principle at draft time —
an untagged stimulus can never be learned from.

### Step 4 — Design the measurement (before anything ships)

No intervention ships without its measurement design written first:

- **Response metric** — the observable human response: for the app, the
  proximal outcome (state change on an established scale, next-action
  taken, return next day); for SNS, save / share / comment-with-content —
  **not** views alone (views are reach, not response).
- **Window** — when the response is read (proximal: minutes–hours after
  the stimulus for a nudge; 24h for a post; state the window).
- **Control** — what the response is compared against: no-nudge /
  prior-wording / held-out keyword set / the prior model. A number with
  no control is a vanity metric and supports no claim.
- **Causal discipline** — see "Statistics" below.

### Step 5 — Route the data back (name the return path)

Every run names exactly where its results land:

| Return path | What goes there |
|---|---|
| **Persuasion ledger** | Every shipped stimulus (post or nudge), tagged by principle/lever, with its measured response. This is the shared record across all surfaces. |
| **ManagerBench case** | Any (state → intervention → observed response) record clean enough to grade models against. Real intervention cases are the scarcest asset the company has. |
| **Model training data** | Intervention logs with the chosen words, their selection probability, and the observed response — the post-training corpus for Manager. |
| **Field catalog** (`anicca-ops files/behavior-field-catalog.md`) | New tools / datasets / field findings from Step 1, so the next run starts from more dots. |
| **Paper loop / gate specs** | Findings strong enough to become a standing rule become a gate spec, not a chat message. |

## Which skill for which question (usage table)

19 existing skills, one recipe. Pick by the question you are holding:

| # | Question you are holding | Skill |
|---|---|---|
| 1 | "Design a whole behavior-change plan for this person / product" | `design-behavior-change-plan` |
| 2 | "The barrier is confirmed — which intervention fits it?" | `intervention-lever-selector` (Behaviour Change Wheel / COM-B / BCT) |
| 3 | "Design the choice environment / defaults / framing" | `apply-nudge-design-principles` |
| 4 | "Which persuasion principle is this stimulus using?" | `persuasion-principles` (Cialdini 6+1) |
| 5 | "Is this persuasion honest — no fake proof, no coercion?" | `ethical-persuasion-design` |
| 6 | "Design the habit loop / trigger / re-engagement" | `hooked-ux` (Hook Model) |
| 7 | "Make the behavior itself stick (cue–routine–reward, stacking)" | `habit-formation` |
| 8 | "Turn the intention into an if–then plan" | `implementation-intention-designer` |
| 9 | "Write the actual words for the chosen technique" | `lever-content-drafter` |
| 10 | "CBT tools: thought records, restructuring, behavioral activation" | `cognitive-behavioral-therapy-tools` |
| 11 | "The person is ambivalent / resisting — advice isn't landing" | `run-motivational-interviewing` |
| 12 | "Self-criticism / shame is the active pattern" | `apply-self-compassion-practice` |
| 13 | "Rumination is the active pattern" | `apply-rumination-interruption` |
| 14 | "Attentional bias toward the negative is the pattern" | `apply-gratitude-journaling` |
| 15 | "Chronic stress / anxiety — a structured mindfulness protocol" | `apply-mindfulness-based-stress-reduction` |
| 16 | "Design the eval / benchmark / grader for this" | `eval-stack` (+ `eval-coach` for strategy) |
| 17 | "Run a growth experiment / A-B test on a funnel" | `growth-experimenter` / `ab-test-setup` |
| 18 | "Did the intervention *cause* the change?" | `jitai-lab` (tool: MRT + WCLS estimator, `~/workspace/tools/jitai-lab-test`) — not a skill; the causal layer of this recipe |
| 19 | "What does the field already have for this?" | Field-expert loop output: `anicca-ops files/behavior-field-catalog.md` — read before searching |

## Statistics (the discipline — non-negotiable)

- **Effect claims require causal evidence.** "It worked" is claimable only
  from (a) a micro-randomized trial estimated with WCLS via `jitai-lab`,
  or (b) at minimum a controlled comparison (intervention vs. a named
  control, same window, same population). Anything else is reported as
  "observed, not attributed".
- **Vanity metrics never carry an effect claim.** Views, impressions and
  follower counts measure reach. Saves, shares, substantive comments,
  next-day return and scale-measured state change measure response.
- **One variable at a time.** The proven base (winner format, proven
  wording structure) stays fixed; change one lever per test window, or
  the response cannot be attributed to anything.
- **Windows are declared in advance.** A format or intervention is judged
  only after its pre-declared window / minimum sample completes — never
  killed or doubled mid-window on a single reading (rankings and views
  oscillate; daily snapshots and 7-day trends are the unit of judgment).
- **Held-out discipline** (from `eval-stack`): cases used to train or
  tune are never used to grade. Author ≠ grader.

## Output format (every research run — the 5-point set)

```markdown
## Run NNN — <target pattern> — <date>
1. **Stimulus** — the exact words / post / nudge, tagged with lever + principle.
2. **Predicted response** — what the theory says people will do, and the
   evidence grade behind the prediction (with source URL).
3. **Surface** — where it ships (app push / SNS account+format / onboarding),
   and the winner whose format it follows, if any.
4. **Measurement** — response metric, window, control. Written before shipping.
5. **Return path** — which of: persuasion ledger / ManagerBench case /
   training data / field catalog / gate spec — and the file it lands in.
```

A run that cannot fill in all five points is not finished research; it is
reading. Reading is Step 1, not the output.

## Anti-patterns (banned)

- Inventing an intervention from intuition when the literature or a winner
  already has one (originality is a failure mode here — copy, then refine).
- Reporting reach (views) as if it were response or effect.
- Changing the format, the wording and the timing in the same window and
  then claiming to know what worked.
- Research that ends in a chat message. Findings land in files (GitHub),
  tagged and measurable, or they do not exist.
- Closing a search with "does not exist" — search company files, papers,
  X, GitHub/skills.sh, then other agents, and report the search record.
