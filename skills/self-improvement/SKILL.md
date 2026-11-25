# Self-Improvement: Capture, Promote, Extract

Version: 1.1

Adopted 2026-11-19 via skills.sh on the founder's instruction ("use their skills, and also for self improving as well"). Source: `botlearn-ai/botlearn-skills@botlearn-selfoptimize` (35 installs), itself a remake of `pskoett/pskoett-ai-skills` `self-improvement` — the companion skill to the `self-healing` skill whose mechanisms were merged into `loop_self_repair` v2. Team adaptations, marked where they occur: (1) the original's external BotLearn community escalation is replaced by our GitHub team-outbox escalation (named owner, ≤1h deadline, ownership until verified) — we never post learnings to third-party communities; (2) the graduation-test section is omitted (it depends on a separate assessment skill we have not adopted); (3) ledger and promotion paths are mapped to this workspace (goal `hidden_files/`, AGENTS.md, TOOLS.md, MEMORY.md, custom-skills).

Purpose: log learnings and errors to markdown files for continuous improvement. Agents later process these into fixes, and important learnings get promoted to durable memory or extracted as skills. Self-healing (loop_self_repair) restores a live failure and files the verified fix; self-improvement is what turns the accumulated record into permanent prevention.

## Quick reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` with category `correction` |
| User wants a missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found a better approach | Log to `.learnings/LEARNINGS.md` with category `best_practice` |
| Similar to an existing entry | Link with `**See Also**`, consider a priority bump |
| Broadly applicable learning | Promote to `AGENTS.md`, `MEMORY.md`, `TOOLS.md`, or a skill (see Promotion) |
| Unresolved after local attempts | Escalate inside the team via team-outbox (see Escalation) |

## Where the ledger lives

- Loop and goal work: the goal's `hidden_files/.learnings/` (durable, next to the loop logs and incident records).
- Workspace-level work: `~/workspace/.learnings/`.
- Create the three files with headers on first use: `LEARNINGS.md`, `ERRORS.md`, `FEATURE_REQUESTS.md`.
- Heal records from loop repairs (loop_self_repair) live in the loop logs with Pattern-Keys; when a heal's lesson generalizes, file the distilled learning here and cross-link by Pattern-Key.

## Logging format

### Learning entry — append to `.learnings/LEARNINGS.md`

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-20250110-001 (if related to an existing entry)
- Pattern-Key: lower.snake.case (for recurring-pattern tracking)
- Recurrence-Count: 1
- First-Seen: YYYY-MM-DD
- Last-Seen: YYYY-MM-DD

---
```

### Error entry — append to `.learnings/ERRORS.md`

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
```
Actual error message or output
```

### Context
- Command/operation attempted
- Input or parameters used
- Environment details if relevant

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001 (if recurring)

---
```

### Feature request entry — append to `.learnings/FEATURE_REQUESTS.md`

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: medium
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built, what it might extend

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name

---
```

ID format: `TYPE-YYYYMMDD-XXX` — TYPE is `LRN` / `ERR` / `FEAT`, XXX sequential or random 3 chars.

## Resolving entries

When an issue is fixed, update the entry: change `**Status**: pending` → `**Status**: resolved` and add after Metadata:

```markdown
### Resolution
- **Resolved**: ISO-8601 timestamp
- **Commit/PR**: abc123 or #42
- **Notes**: Brief description of what was done
```

Other status values: `in_progress`, `wont_fix` (add the reason in Resolution notes), `promoted`, `promoted_to_skill`.

## Self-limitation / self-made-procedure audit (Pattern-Key: limit.self_imposed_cap_and_originality)

Added 2026-11-24 (hourly refinement, from the founder's same-day corrections). A number or a procedure that Muse invented is a failure, even when it looks like diligence.

**Gate — run before writing or approving any job body, skill step, plan, or lane instruction:**

1. **Every quantity needs an external source.** Any number that sets volume, frequency, a floor, a cap, scope, or cadence (posts/day, articles/day, replies/day, batch size, retry count, slot count) must cite its source in the same document: a named existing skill/tool, a best-practice source read this run, or a measured winner. A number with no citation is a self-imposed limit: delete it, then find the best-practice skill/tool (Vercel Labs skills CLI `npx skills find <keyword>`, GitHub, skills.sh — several in parallel, never one) and adopt the quantity it prescribes, even if that is 100/day per product. A self-set floor is still a cap: "at least 3/day" was set by Muse for SEO on 2026-11-24 10:50 and corrected by the founder at 10:54 as self-limitation — the floor itself was the error.
2. **Every procedure needs an existing owner.** If a step is written in Muse's own words and an existing skill/tool covers that step, the step is self-made: replace it with a reference to that skill/tool and follow it verbatim. Do not patch a skill with a home-grown step (founder correction 2026-11-24 09:04–09:12, repeated 10:51/10:55 for blog/research writing formats). Searching for the existing thing comes before writing anything.
3. **Audit daily, by name.** Each day, list per lane: (a) self-made procedures found, (b) self-imposed limits found, (c) what each was replaced with and its source. Record the list in the skill-refinement ledger. "None found" is not an acceptable audit result without the search record (which lanes, which files, which numbers were checked).
4. **Verification:** a quantity/procedure passes only when the citing source can be opened and the number/step matches it. Report the source path/URL alongside the number, never the number alone.

Recurrence note: this pattern recurred at least 3 times on 2026-11-24 alone across lanes (slideshow hook step self-written 09:04; SEO floor 10:50→10:54; blog/research format self-made 10:51–10:55) and across multiple tasks, so it meets the promotion threshold below — the founder already promoted the underlying rule to AGENTS.md/MEMORY.md on 2026-11-23–24; this section is the operational gate inside this skill.

## Recurring pattern detection

If logging something similar to an existing entry:

1. **Search first**: `grep -rn "Pattern-Key: <key>" .learnings/` (and the loop logs).
2. **Link entries**: add `**See Also**` in Metadata.
3. **Bump priority** if the issue keeps recurring.
4. **Consider a systemic fix**: recurring issues usually mean missing documentation (→ promote), missing automation (→ AGENTS.md), or an architectural problem (→ open a GitHub Issue with one owner).

## Promotion to durable memory

Promote a learning when it applies across multiple files/features, is knowledge any agent on the team should have, prevents recurring mistakes, or documents a project convention.

| Target | What belongs there |
|--------|-------------------|
| `AGENTS.md` | Standing rules, workflows, automation conventions (founder-level rules land here) |
| `MEMORY.md` / `~/memory/` | Durable facts about the user, the company, decisions |
| `TOOLS.md` | Tool capabilities, usage patterns, integration gotchas |
| A skill in `~/workspace/custom-skills/` | A repeatable procedure (see Skill extraction) |

How: distill the learning into a concise rule or fact (not the incident write-up), add it to the right section of the target, then update the entry: `**Status**: promoted`, `**Promoted**: <target file>`. Promoted rules are written as prevention guidance — what to do before or while working — in the target file's own style. Per the founder's rule, learning is only complete when it is written to a file and the path is reported.

### Promotion rule (threshold)

Promote when **all** are true: `Recurrence-Count >= 3`, seen across at least 2 distinct tasks, within a 30-day window. This matches the heal-promotion threshold in loop_self_repair v2 — the two skills share one recurrence ledger discipline (stable Pattern-Keys).

## Skill extraction

Extract a learning into a reusable skill when **any** apply: recurring (See Also links to 2+ similar issues); verified (status `resolved` with a working fix); non-obvious (required real debugging); broadly applicable (not project-specific); user-flagged ("save this as a skill").

Workflow:

1. Create `~/workspace/custom-skills/<skill-name>/SKILL.md` from the learning: frontmatter title, the distilled procedure, and a mandatory Verification section (house style: invariants / grader / E2E / oracle).
2. Quality gates before extraction: solution tested and working; description clear without the original context; examples self-contained; no project-specific hardcoded values or credentials; name is lowercase-with-hyphens or underscores matching the folder.
3. Update the learning: `**Status**: promoted_to_skill`, add `**Skill-Path**`.
4. Publish the skill to GitHub anicca-ops `files/skills/` (gh api single-file route) and read back, per the house rule that artifacts live on GitHub.

## Escalation (team adaptation)

When local resolution has failed and the issue is recurring (`Recurrence-Count >= 2`), high/critical priority, or novel with no prior art: escalate inside the team, never to the user and never to external communities. Write a team-outbox file in anicca-ops (`team-outbox/muse/to-<owner>-<date>-<slug>.md`) naming one owner, the learning entry ID, what was tried, and a deadline of at most 1 hour for the first response. The escalator keeps ownership until the fix is verified landed (founder rule, 2026-11-19: delegation is to a named teammate via GitHub; telling is not finishing).

## Periodic review

Review `.learnings/` at natural breakpoints: before starting a major task, after completing a feature, when working in an area with past learnings, and in the weekly skill-refinement pass.

```bash
grep -h "Status\*\*: pending" .learnings/*.md | wc -l            # pending count
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["     # pending high-priority items
```

Review actions: resolve fixed items, promote applicable learnings, link related entries, escalate recurring issues.

## Detection triggers

Log automatically when you notice:

- **Corrections** (→ learning, `correction`): "No, that's not right…", "Actually, it should be…", "That's outdated…"
- **Feature requests** (→ feature request): "Can you also…", "I wish you could…", "Why can't you…"
- **Knowledge gaps** (→ learning, `knowledge_gap`): the user provides information you didn't know; documentation you referenced is outdated; an API behaves differently than you understood.
- **Errors** (→ error entry): non-zero exit codes, exceptions, unexpected output, timeouts.

## Priority guidelines

| Priority | When |
|----------|------|
| `critical` | Blocks core functionality, data-loss risk, security issue |
| `high` | Significant impact, common workflows, recurring |
| `medium` | Moderate impact, workaround exists |
| `low` | Minor inconvenience, edge case, nice-to-have |

## Best practices

1. **Log immediately** — context is freshest right after the issue.
2. **Be specific** — a future agent must understand it in one read.
3. **Include reproduction steps** — especially for errors.
4. **Link related files and entries** — fixes get easier.
5. **Suggest concrete fixes** — not just "investigate".
6. **Promote aggressively** — if in doubt, it belongs in durable memory or a skill.
7. **Close the loop** — when a fix lands, resolve the entry; when a rule lands, mark it promoted.
