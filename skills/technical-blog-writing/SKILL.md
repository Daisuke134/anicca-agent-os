---
name: technical-blog-writing
description: The single canonical skill for ALL Anicca writing lanes (blog, Zenn, note, Substack, LinkedIn long-form). Write and refine technical / engineering blog posts in the how-we-did-it form: problem first, TL;DR, runnable evidence, measured results, named trade-offs, honest unverified gaps, and a persuasion/recruiting path. Every new post and every refine pass is gated by the 12-point checklist in this skill. Use whenever writing, editing, reviewing, or republishing any article.
metadata:
  version: 1.2.0
  adopted: 2026-11-22
---

# Technical Blog Writing — Anicca canonical skill (v1.2.0)

Version: 1.2.0 — 2026-11-24 (1.1.0 was 2026-11-24, 1.0.0 was 2026-11-22). v1.2.0 change: burned in the 2026-11-24 17:00–17:43 Day 30/31 publication failure — articles pushed as `.md` under `apps/landing/content/blog/` never rendered live (all such articles, old and new, return 404), while the canonical live route is the research JSON path. A "Canonical live route gate" (below) now requires proving the chosen path/format renders live before publishing, and forbids treating file landing or repeated 404 polling as a deploy delay when the route itself is dead. v1.1.0 change: burned in the founder's 2026-11-24 11:28–11:50 corrections (research article pair rejected as "AI slop" for self-made format and no visuals; the same judgment extended the same day to SEO comparison articles). The canonical writing-tools standard (anicca-ops `files/writing-tools-standard-2026-11-24.md`) is now a mandatory gate in this skill: every writing lane uses the same off-the-shelf tool set, and a research/tech/SEO article without the required visuals is slop and does not ship — see "Writing-tools standard gate" below.

## Sources (attribution — these are other people's work, not ours)

Primary base, adopted as-is in spirit and structure:
- samber/developer-relations-skills@engineering-blog-post (skills.sh, 13.5K installs) — https://skills.sh/samber/developer-relations-skills/engineering-blog-post — "a post a skeptical developer reads without their trust alarm going off; craft is evidence discipline, not prose polish; one inflated claim discredits every other claim."

Structure and post types:
- inference-sh/skills@technical-blog-writing (skills.sh) — https://skills.sh/inference-sh/skills/technical-blog-writing and https://www.mdskill.dev/inferen-sh/superpowers/technical-blog-writing — post types (Tutorial / Deep Dive / Postmortem / Benchmark / Architecture), ideal structure (TL;DR → Problem → How we did it → Results → Trade-offs → Conclusion → Further Reading), code rules (runnable, language-tagged, output shown, versions pinned), common-mistakes table.

Quality bar and voice:
- getsentry/skills@blog-writing-guide (skills.sh, 3.5K installs) — https://skills.sh/getsentry/skills/blog-writing-guide — "every post should be something a senior engineer would share in their team's Slack"; we/you voice; no corporate / press-release / sales voice.

Process evidence:
- Dan Luu, "How (some) good corporate engineering blogs are written" — https://danluucination.github.io/corp-eng-blogs/ — good blogs (Cloudflare, Heap, Segment): lightweight approval, editing that makes posts MORE specific and compelling, never vaguer.
- Kai Lindström, "How to Write a Technical Blog Post That Engineers Actually Want to Read" — https://theappgap.com/2026/06/10/how-to-write-a-technical-blog-post-that-engineers-actually-want-to-read/ — start with the problem not the tool; code examples are arguments not decorations; show failure before success.
- Tanner Goins, "The Engineer's Guide to Writing That People Read" — https://www.tannergoins.com/blog/engineers-guide-to-writing — problem/payoff opening, context efficiently, show don't tell, explicit takeaway.

Existing in-house skills this skill sits above (still used for their narrow jobs): blog-refresher (SERP refresh), intro (intros), copywriting, ai-seo. Where they conflict with this checklist, this checklist wins for technical posts.

Anicca additions (ours, on top of the adopted bases):
- How-we-did-it is mandatory: the reader must be able to see what we actually ran, in what order, with what result — not only opinions or numbers.
- Persuasion & recruiting lens (founder order 2026-11-22): writing is itself persuasion and recruiting. A post must let a reader (human or agent) picture using the product, joining the work, or copying the procedure — and give them a concrete next step. This is done with evidence and openness (real numbers, open code, open record), never with marketing hype.
- One skill, refined forever (founder order 2026-11-22): every lane reads THIS file. Lessons from refine passes flow back into this skill: when a refine finds a checklist gap, revise this skill, bump the version, and push it to anicca-ops files/skills/technical-blog-writing/SKILL.md in the same run.

## Writing-tools standard gate (mandatory, added 2026-11-24)

Canonical source: anicca-ops `files/writing-tools-standard-2026-11-24.md` (founder, 2026-11-24). This gate applies to whoever writes anything — blog, tech blog, research blog, SEO/AIO articles, LinkedIn, note, Substack, the autonomous-company series, product copy drafts — with no exceptions by lane, writer, or deadline.

- **Same tool set for every piece of writing** (installed unmodified via the Vercel Labs skills CLI): technical-writing (riekelt/technical-writer), data-storytelling (wshobson/agents), data-visualization (anthropics/knowledge-work-plugins), research-blog (scasella/skills), blog-discourse (agricidaniel/claude-blog), design-doc-mermaid (spillwavesolutions/design-doc-mermaid). Inventing a house format is prohibited: if a format question is not answered by these skills, search for the best practice or another off-the-shelf skill and follow that.
- **Visuals are mandatory for research, tech, and SEO/data articles.** Minimum per article: (a) one chart generated from the real data the article reports, (b) one diagram of the mechanism or pipeline, (c) tables where the skills call for them. Every figure carries a caption stating what is shown, the n or source, and what to read from it. An article without these visuals is slop and does not ship — gate item 6 below cannot pass on code blocks or prose alone for these article types.
- **Completion means published and read back**, including confirmation that every figure reference resolves on the live page.

Evidence: on 2026-11-24 the founder rejected the published fresh-start-effect-gate research pair (self-made format, no visuals) as AI slop, and the same day judged the SEO comparison articles the same way (not following the skills/tools, no visuals) as remake targets. The prior version of this skill allowed gate item 6 to pass with any one of {code, table, diagram}, so a no-visual article could pass — that hole is what this gate closes. Pattern-Key: `writing.no_visuals_self_made_format`.

## Canonical live route gate (mandatory, added 2026-11-24)

Pattern-Key: `publishing.wrong_route_file_landing_not_live`. A file landing in a repository is storage, not publication (founder rule, 2026-11-22, re-proven 2026-11-24). Before pushing any article, and before calling any article published:

1. **Prove the route renders, from a live example in the same format.** Pick one already-published article that uses the exact same file path pattern and format you are about to use, and read its live URL fresh in this run. It must return HTTP 200 with the article rendered. If that example returns 404, the route is dead for that format — do not push there, and do not poll your new URL waiting for a deploy that will never render it.
2. **The canonical aniccaai.com/blog route (measured 2026-11-24 17:15–18:0x JST):** live articles render from the research JSON path — `apps/landing/data/research/<slug>.json` → `https://aniccaai.com/blog/<slug>`. Articles pushed as `.md` under `apps/landing/content/blog/` do NOT render: both new Day 30/31 slugs and pre-existing `.md` articles (e.g. `ai-agent-self-heals-github-actions`) returned HTTP 404 (16,212 bytes, the not-found page) across 25 checks, while research-JSON articles returned 200 (e.g. `autonomous-company-agent-courts-2026-11-24`, 79,537 bytes; the re-published Day 30 `autonomous-company-agent-employer-of-record-2026-11-24`, 72,103 bytes; Day 31 `autonomous-company-agent-open-source-governance-2026-11-24`, 73,158 bytes — all re-read live in the 18:01 hourly refinement run). If the site's routing changes, re-derive this paragraph from a fresh live example under step 1 in that run; never publish from this paragraph alone without that check.
3. **A 404 is a route verdict after the control check, not a delay by default.** Repeated 404 polling only counts as "deploy pending" when step 1's same-format control article returns 200 in the same window. Without that control, classify the failure at the route layer, switch to the proven route, re-publish there, and only then poll.
4. **Completion is the live readback of the new URL itself:** HTTP 200, the article body rendered, and every figure reference resolving on the live page. A commit sha, a push success, or a file readback in the repo is never a publication result, and a slug that was never live must not be reported to anyone as the article's link — report only the slug that returned 200.

Evidence (2026-11-24): the founder asked at 17:00–17:05 where the Day 30/31 links were; both existed only as GitHub `.md` landings (commit a9f80d544). A first re-publish still used the dead `.md` route (`content/blog`, `published: true`, commits af4d8bc3a9de / 043de0d7118c) and both URLs stayed 404 through 25 checks (17:15–17:40), initially misread as Netlify delay. The route diagnosis — same-format existing `.md` articles also 404, same-day research-JSON articles 200 — identified the real route; re-publishing via research JSON (push shas c6b519c1… / 9609b567…) produced live 200s verified in the next hourly run.

## Post types (pick one before writing)
Tutorial / Deep Dive / Postmortem / Benchmark / Architecture / How-we-did-it (our default for the autonomous-company series: a Benchmark or Architecture skeleton with our own run as the evidence).

## Required structure
1. Title — states the problem or outcome, searchable, no clickbait.
2. TL;DR — 2-3 sentences at the very top, with the key number or decision.
3. The Problem — a specific incident, number, or failure. Never open with the tool, the topic, or "in today's world".
4. Audience line — who this is for and what it assumes, in one or two lines.
5. How We Did It — ordered steps; failure before success; real names, dates, versions.
6. Evidence — code (runnable, language-tagged, output shown), tables, diagrams, or measured logs wherever a claim needs support. Every number carries a source and a date.
7. Results — before/after or outcome table, even when the honest result is "not yet verified" (say so in the table).
8. Trade-offs and Limitations — at least one named trade-off we accepted and one limitation.
9. What We Have Not Verified — honest gaps, labelled as unverified.
10. Try It / Work With Us — the persuasion & recruiting step: one concrete next action with a live link (read the open numbers, run the code, open an issue, join a lane, install the app).
11. Further Reading — 3-5 links, every one of them openable and tryable.

## The 12-point gate (a post does not publish below this)
Score each item pass/fail with a line of evidence:
1. Title states problem/outcome.
2. TL;DR present at top with key takeaway.
3. Problem-first opening; lede not buried.
4. Audience/prerequisites stated.
5. How-we-did-it steps present, failure shown before success where one occurred.
6. Evidence density: at least one of {runnable code block with output, results table, diagram} AND every quantitative claim sourced + dated. For research, tech, and SEO/data articles this item ALSO requires the Writing-tools standard gate visuals: one chart from the article's real data plus one mechanism/pipeline diagram, each captioned (what is shown, n/source, what to read from it); without them this item fails regardless of code or tables.
7. Results section with concrete numbers (or an explicit "not yet measured" row).
8. Named trade-off(s) and limitation(s).
9. Unverified items explicitly labelled.
10. Persuasion: a specific scene/number lets the reader picture the work or product in use (evidence-based, no hype words: no "revolutionary", "seamless", "simply", "just", "obviously").
11. Recruiting/participation: a concrete invitation + link (contribute, join, try, replicate) that a reader or agent can act on today.
12. Further Reading 3-5 working links; voice is first-person founder "I/we", direct, no marketing tone.

Publish gate: >=10/12 AND items 2, 6, 8 all pass. A refine pass re-scores the post and records the before/after score in the refine ledger.

## Skill self-refinement (built into both loops)
- Each refine run appends what it learned to the run ledger.
- If the same failure appears in 2+ posts, or a checklist item proves unmeasurable, that is a skill defect: revise this file, bump metadata.version, push to BOTH ~/workspace/custom-skills/technical-blog-writing/SKILL.md and anicca-ops files/skills/technical-blog-writing/SKILL.md, and note the change + reason in anicca-ops files/technical-blog-best-practice-2026-11-22.md (living report) and the ledger.
- Never fork a lane-specific variant. One canonical skill for every lane.
