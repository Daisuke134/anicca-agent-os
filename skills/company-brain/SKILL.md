---
name: company-brain
description: Use the team's shared company brain (GBrain) — the single read/write memory layer all agents share on top of the GitHub canonical store. Read before answering from memory; write facts, decisions and episodes with provenance.
---

# Company Brain (GBrain) — shared memory for the whole team

The company brain is **GBrain** (garrytan/gbrain, MIT, free to self-host), adopted
2026-11-17 after a trial run. Full evaluation + trial evidence:
anicca-ops `files/company-brain-shared-memory-2026-11-17.md`.

## The one rule that does not change

**GitHub (anicca-ops) remains the canonical store.** The brain is an
index/recall layer over git Markdown — pages written through the brain land as
files in the source repo (`gbrain sources push` commits them back). If the
brain and GitHub ever disagree, GitHub wins. Never let knowledge exist only
inside the brain's database: facts saved with `remember` are DB-only until
they are also put on a page.

## Provenance is mandatory

A shared brain amplifies errors exactly like it amplifies facts. Every entry
carries, in its body or `--provenance`:

- `Source:` where it came from (file path + commit, API read, founder directive with date)
- `Verification:` verified (how) / unverified

No credential values, ever. Corrections are first-class: supersede or
`gbrain forget` a wrong fact instead of silently editing around it.

## Daily verbs (CLI, keyless — keyword search)

```bash
export PATH="$HOME/.bun/bin:$PATH"
gbrain search "<phrase>"            # keyword search across all sources
gbrain query "<question>"           # hybrid search (same while embeddings off)
gbrain get <slug>                   # read one page
gbrain put <slug> < page.md         # write/update a page (lands in the git source)
gbrain remember "<fact>" --entity <slug> --provenance "source: …; verification: …"
gbrain recall [<entity>]            # read saved facts back
gbrain forget <fact-id>             # withdraw a fact
gbrain sync --all                   # re-index after editing source files (commit first)
gbrain doctor                       # health check
```

MCP (any agent harness): `gbrain serve` (stdio) exposes the same verbs —
`search`, `get_page`, `put_page`, `recall`, `remember`, `forget`, plus graph
and timeline tools. Per-harness guides live in the gbrain repo under
`docs/mcp/` (Claude Code, Codex, Grok Bot, ChatGPT, Muse, …) and
`docs/guides/muse.md`, `docs/guides/grok-bot.md`.

## Current deployment state (2026-11-17)

- Trial brain on this VM: `~/workspace/company-brain-trial/` (PGLite,
  `--no-embedding`, keyword search). Bun 1.4.4 + gbrain 0.60.733.0 in `~/.bun`.
- Embeddings are OFF by choice: recall is keyword-only and gbrain says so on
  every degraded result — never report "not found" from a keyword-only miss.
  Turning semantic search on needs an embedding provider decision (a free
  local option must be evaluated first; no paid API without approval).
- Production wiring is a separate, scheduled step: point a source at the real
  anicca-ops checkout, run `gbrain setup <harness>` per agent, and expose the
  brain to off-VM agents with `gbrain mcp expose` (Tailscale). Do not wire
  harnesses ad hoc from this skill alone.

## Page conventions (from gbrain's company-brain model)

- `facts.md` — numbers and statements agents may repeat, each with provenance.
- `decisions.md` — each decision with date, reason, and who made it.
- `episodes/` — what we tried and what happened (the episodic layer GitHub
  search could not give us).

## Verification (mandatory, added 2026-11-17)

Work done through the brain is verified against the canonical store, not against the brain itself. Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) No fact is served from the brain without `Source:` and `Verification:` in its body or provenance; a provenance-less hit is treated as a rumor, not a fact. (b) Nothing durable exists only in the brain's database: every fact that matters also lands as a page in the GitHub source repo. (c) On any disagreement between the brain and GitHub, GitHub wins and the brain entry is corrected or forgotten — never the reverse. (d) While embeddings are off, a keyword "not found" is reported as "not found by keyword search", never as "does not exist".
2. **Grader.** A different agent or session recalls the same fact through a separate surface (CLI vs MCP) and compares it against the GitHub source file. The writer's own recall in the same process is not the grade.
3. **E2E evidence.** A write is proven cross-process: put a page or fact through one surface, read it back through another, and confirm the page file exists in the git source with the expected content (the trial's process-A-writes / process-B-recalls test is the model).
4. **Differential oracle.** The anicca-ops GitHub file at its commit is the oracle for every recalled fact. A brain answer that cannot be traced to a source file and commit is downgraded to unverified before it is used.
5. **Repeat failures.** A second provenance-less or DB-only fact found in use becomes a pre-write check in the workflow that produced it, and the wrong entry is superseded or forgotten the same day — a shared brain amplifies errors exactly like it amplifies facts.
