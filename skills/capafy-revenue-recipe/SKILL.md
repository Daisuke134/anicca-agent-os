---
name: capafy-revenue-recipe
description: Money recipe for Anicca's Capafy marketplace lane — winner-verbatim listing creation, a deterministic review-proofing gate (display model == credential model, English notes, canonical openclaw config), per-listing OpenRouter P&L gate, in-platform distribution iteration, and a rejection-recovery cycle. Use for any Capafy publishing, pricing, model-migration, distribution, or revenue work. Execution routes through the capafy-autopublish skill; this recipe is the revenue/iteration layer above it.
---

# Capafy Revenue Recipe — Anicca

Purpose: turn our 94-listing Capafy catalog (74 online) back into a growing
recurring-revenue lane. The lane used to make money (90-day net $179.67) and
has stalled at ~$9.99/7d because submissions sit blocked, paid models burn the
prepaid balance on free orders, and the distribution loop is disabled.
Every loop run ends with a record row; a run with no record did not happen.
Nothing in this recipe authorizes a new payment of any kind.

## 1. Search record (2026-11-21, checked before building this skill)

Founder rule applied: search first, adopt what exists, build only the missing
piece. The missing piece was never publishing mechanics — we own a full
pipeline (`capafy-autopublish`). The missing piece is the revenue layer above
it: review-proofing as a gate, per-listing P&L, distribution cadence, and
rejection recovery, in one place the loops consume.

| Source | What was checked | Adopted / rejected |
|---|---|---|
| `npx skills find capafy` / `"agent marketplace"` / `"digital product selling"` / `marketplace` | skills.sh catalog via Vercel Labs CLI. Background run 7.6 min produced zero result lines; foreground retry timed out at 100 s with no output | **UNREACHABLE, not empty.** VM egress was degraded all evening (same failure killed every `gh` search). Do not read this as "no skill exists". Re-run the four queries when egress recovers; until then this recipe stands on the sources below. |
| GitHub search (`gh search repos capafy`, `gh api search/repositories?q=capafy`, code search for SKILL.md) | All three timed out (180 s batch, exit 124; 60 s retry, exit 124) | **UNREACHABLE tonight**, same egress failure. Known independently: the only Capafy publisher skill that matters is Capafy's own (next row) plus our own pipeline. |
| Capafy official Publisher Skill — install via `https://api.capafy.ai/install-publisher-skill.md` (per Capafy's own guide) | The platform's official publishing skill/runtime | **ADOPTED — already vendored.** Lives at `~/workspace/tools/capafy-publisher-skill/capafy-publisher/` and inside `capafy-autopublish/vendor/`. It is the execution layer (packager, API client, route scan). Never invoke it directly; `capafy-autopublish` routes through it. |
| Capafy official guide "How to Make Money With AI: Sell AI Skills on Capafy" — https://capafy.ai/blog/how-to-make-money-with-ai | Platform's own seller doctrine | ADOPTED: publishers keep **80%** (20% platform share; subscription sales may also carry a platform sandbox fee — check margin after it, §4); price by **value received**, not by prompt/file count; Agent Card must answer 5 questions (what / who for / what user provides / what user receives / why worth paying); successful Skills = one defined deliverable (their examples: football analysis, stock tracker, a 7-image listing plan). |
| Capafy "Become a Publisher" — https://capafy.ai/earn/ | Live top-earner board + fee facts | ADOPTED as demand evidence: top earners shown are **KOL Hunter Pro US$200k+/mo, Financial Report Analyst US$10,000+/mo, SEO Content Planner US$5,000+/week** — finance/intel and content-planning verticals carry the money. One-time certification fee US$0.99 exists (already paid historically; never pay anything new without founder order). |
| Capafy guide "How to Monetize Open-Source AI Skills From GitHub" — https://capafy.ai/blog/monetize-open-source-ai-skills | Funnel doctrine | ADOPTED: GitHub README → paid Agent is a sanctioned free funnel; offer paid online version + premium tier of things we already open-source. Fits our open-source-everything rule. |
| Web sweep of Capafy homepage/marketplace (2026-11-21) | Live catalog: Alpha Consensus 1,157 sold @ $8.33/mo; Serenity Stock Tracker; Ocup Football Analysis; ProspectIQ | ADOPTED as market shape: recurring-input analysis (stocks, football, sales intel) dominates sold counts. Same families our own BEST_PRACTICES sweeps found (§3.1). |
| X search for Capafy seller practices (`site:x.com` query) | No results returned | Recorded as checked. No X playbook adopted. |
| Internal: `~/workspace/life-manager/skills/capafy-autopublish/` (SKILL.md, BEST_PRACTICES.md, PUBLISHING_RUNBOOK.md, scripts/) | Our own proven pipeline + winner data (13+ live listings, market sweeps 2026-06→09) | **ADOPTED wholesale as the execution + winner layer.** This recipe references it instead of copying it: winner-verbatim rule, sellable test, pricing bands, honesty bans, lint gate, CP1/CP2/CP3 flow, FROZEN-seller guard all live there. |
| Internal: anicca-ops `team/capafy/CAPAFY-STATUS.md` (2026-11-15 evidence audit) | Portfolio truth | ADOPTED as baseline discipline: only 9 of 77 public listings had any sales; **bank received from Capafy = $0** (payouts sit in wallet); views are UNKNOWN (no API) — never invent them; salesVolume is a uses proxy, not cash. |
| Sibling skill `~/workspace/custom-skills/apify-revenue-recipe/SKILL.md` | Same-day recipe built under the same founder rule | ADOPTED as this skill's shape: search record → measured current state → recipe → hard P&L guardrails → metrics + exact ledger → loop wiring with flagged (not silent) cron changes. |

## 2. Current state (measured, 2026-11-21 18:14 JST, hourly run #135)

Source: `hidden_files/capafy-recurring-2026-11-21-1814.md` (Capafy official API
+ OpenRouter Management API). Full history: `hidden_files/capafy-recurring-*.md`.

- **Catalog:** 94 listings — online **74** / draft 3 / offline 12 /
  review_rejected 4 / under_review 1. Zero state transitions in weeks.
- **Sales:** 30d = 2,144 orders, gross $129.87, refunds $32.97, **net $96.90**;
  7d net **$9.99** (one repeat subscription unit — the only recurring signal);
  today 3 orders, $0 (all free). 90d net $179.67. New buyers are ~99% free
  units: volume exists, payment does not.
- **Payout wallet:** pending $7.60 / confirmed $57.20 / balance $83.78.
  Historical bank receipt is still $0 (CAPAFY-STATUS §2) — wallet balance is
  not income until a payout lands.
- **OpenRouter:** total_credits **$155.00** (invariant — proves no top-up /
  auto-reload), total_usage $98.62, balance **$56.38**. Capafy host-key usage
  increment this hour: $0. Spend is prepaid balance only.
- **Model mix (online 74):** DeepSeek V4.1 Flash 26 / **Claude Sonnet 5 28 /
  Claude Sonnet 4.6 9** / Gemini 3.5 Flash Lite 5 / null 6. The 37 Sonnet
  listings are the P&L migration queue (P&L audit classes: RISK = Sonnet 4.6,
  WATCH = Sonnet 5, CHECK = model null).
- **F1 (7069327619) blocked 21 consecutive runs** at the final gate:
  `isConfirmedConfigKeys = 0`. Everything else is done (corrected v1.0.3
  package uploaded, credential model now reads `deepseek/deepseek-v4.1-flash`,
  English update note saved, `isConfirmedSkills = 1`). The console offers no
  confirm-only UI: it demands the full host-key value typed in, and key values
  never travel in plaintext through chat/logs (§5).
- **Distribution loop is OFF:** `anicca-capafy-loop` (3h, metrics →
  improvements → articles/social → funnel) has `enabled: false`. The hourly
  measurement/P&L loop runs, but nothing ships distribution. Traffic
  concentrates in free downloads (Free Clip Map 2,757 uses) converting ~0%.
  **2026-11-22 refresh:** Free Clip Map is at **2,919 uses (+162/week)** —
  the free engine still grows on its own while sellers have had zero
  marketing since 2026-11-14. This is now the lane's #1 measured diff
  (recovery plan §2, D1).

## 2.1 What actually sold (measured seller table, 2026-11-22)

Per-listing paid evidence — the only listings that may be called sellers.
Sources: `team/metrics/capafy-paid-orders.csv` (Gmail-notified orders,
2026-06-23 → 2026-10-30, 10 orders, $77.91) + public-API salesVolume pulls
2026-11-15 and 2026-11-22. Per-listing cash beyond the Gmail file is NOT
exposed by the API — do not invent it.

| Listing | Paid evidence | Units (salesVolume) |
|---|---|---|
| 8123079349 Hook Lab | $9.99 order 2026-08-09; $34.88 cumulative (BEST_PRACTICES §13) | 12 |
| 9425449917 Series Continuity Planner | $9.99/wk order 2026-10-23 | 4 → 5 |
| 2844813315 TikTok Script Pro | $1.99 order 2026-09-22 | 4 |
| 7686597754 YouTube Script Writer | $1.99 order 2026-09-27 | 4 |
| 8354665033 NHL Goalie Matchup Brief | $9.99/wk order 2026-10-28 | 2 |
| 4699090343 TikTok Storytime Script | $6.99/wk order 2026-10-30 | 3 |
| 9563867391 Marketing Strategist | $6.99 order 2026-09-16 | 2 |
| 8828622062 Slide Maker | $9.99 order 2026-09-06 | 2 |
| 6839055303 Academic Humanizer | $9.99 download order 2026-06-23 (first on file) | 1 |
| 3332784488 Japanese Humanizer | $9.99 download; per-order cash not in Gmail file | 37 |
| 7095835081 Free Clip Map / 2455220100 Hook Grader | free — traffic, not cash | 2,919 / 102 |

Facts the table forces:
- **Every paid order is creator content, a humanizer download, or a sports
  brief.** The 80+ enterprise "evidence deck" listings have zero paid
  orders, ever. Build and market only in the proven families (§3.1).
- **9 of 12 sellers gained zero units 2026-11-15 → 2026-11-22.** The lane
  did not decay; it was switched off (no distribution, no shipping).
- The "~$100 MRR" era = 30d net $96.90, mostly **new-buyer** units. The
  only measured renewal is one $9.99 returning-buyer order (2026-11-20,
  listing not identifiable — aggregate API). Never report the $96.90 as
  recurring revenue.
- **Hook Lab price conflict — UNRESOLVED.** FROZEN.json says all 12 paid
  orders were at "September prices" and v1.0.8 restored them 2026-10-16;
  the live listing reads $12.99 / $29.99 / $149.99 (2026-11-15 and
  2026-11-22) and the only verified order is $9.99. Read the console
  version history and correct one record before citing either story.
  Hook Lab is FROZEN either way — no edit follows from the conflict.

## 3. The recipe

### 3.1 What sells (build/keep order — winner families only)

From Capafy's top-earner board + our own market sweeps (BEST_PRACTICES §10–13)
+ our revenue history (every yen we ever made is short-form creator content):

1. **Finance/intel analysis on recurring input** — earnings/stock/KOL trackers,
   match analysis. Structure only: a structured report from input the buyer
   pastes or a named subject. Never claim live data in a `run_online` sandbox.
2. **Short-form creator content** — hooks, scripts, captions (Hook Lab is our
   top earner, $34.88). Variants inside the family, but **no near-identical
   mass uploads** (Capafy doc 4.2; Hook Lab variant test sold 0 in 30d).
3. **Content planning / copy** — SEO content planner class, conversion copy.
4. **Pro deliverables** — slide/deck builders, data analyst on pasted data.

Sellable test (from capafy-autopublish, hard): `run_online` = model + pasted
input only. If the value needs web/tools/accounts/files, it is not sellable
as run_online — sell it as a download or don't build it.

### 3.2 Listing creation (execution = capafy-autopublish, verbatim)

1. Find a proven seller via the market CLI (`POST /agent/agents/search`),
   read its live record (`GET /agent/agent/agents/<id>`).
2. **Copy the winner's facts verbatim** — price, cap, category, plan shape,
   structure. Write original words. Never invent a price or cap.
3. Build the skill (pure-LLM, sandbox-complete), write LISTING.md in the
   canonical shape, lint until PASS (`lint_listing.py`).
4. Publish via the split flow: `publish_prepare.sh` → CP1 agentic card →
   `publish_finish.sh` → remote readback (`status=1 ∧ cfg=1 ∧ run_online ∧
   title ∧ model ∧ pricing`). Browser render check after the ✅.
5. Record in `capafy-autopublish/state/published.jsonl`, commit + push.

### 3.3 Review-proofing gate (run BEFORE every submit — deterministic)

A submission may not leave until every line passes. This gate exists because
F1 v1.0.2 was rejected on lines 1–2 and then blocked 21 runs on line 6.

1. **Display model == credential model.** The public model string and
   `requiredCredentials.url_proxy[0].model` must be the same model
   (e.g. display "DeepSeek V4.1 Flash" ⇔ `deepseek/deepseek-v4.1-flash`,
   model_id 541). Read both from the detail API
   (`GET /agent/agents/{id}`, plural — the singular path is a broken
   platform route that returns code 500 in a 200 body).
2. **Canonical config in the package.** `.openclaw/openclaw.json` present,
   exactly the team's shape (publish_prepare.sh writes it): provider
   `openrouter`, baseUrl `https://openrouter.ai/api/v1`, api
   `openai-responses`, apiKey = the env reference
   `${CAPAFY_HOST_OPENROUTER_KEY}` (**never a literal key**), models[0] =
   {id, name = id, maxTokens}, `agents.defaults.model.primary` =
   `openrouter/<model_id>`, `skipBootstrap: true`. A package with no config
   leaves the credential model at whatever the platform last held — that is
   how F1 shipped Sonnet under a DeepSeek label.
3. **English only** in every platform-facing field, including
   versionUpdateInfo. A Japanese update note is a measured rejection cause.
4. **Honesty lint passes.** No live/real-time/browse/scrape/fetch/retrieval,
   no posts/sends/schedules, no file-download claims, no guaranteed/
   undetectable — unless negated (BEST_PRACTICES §6 list is canonical).
5. **Field limits:** title ≤ 50 chars, shortDescription ≤ 500, pricing table
   present and identical in LISTING.md, card, and API billings.
6. **Both confirmations read back = 1** before submit is counted:
   `isConfirmedSkills = 1` ∧ `isConfirmedConfigKeys = 1`. If the console
   demands the full key value to confirm, use only the secure vault→console
   direct-entry route (the 2026-11-07 founder order for the 3h loop: read
   `openrouter_host_key` from the vault, type it into the Agent Workspace,
   never print it). If no safe entry route exists in that run, record the
   blocker with the exact console state — do not route the value through
   chat, logs, or files.
7. **Slot discipline:** max 5 unlisted (status 0–3) Agents at once;
   publish-init fails when full. A seller update under review also burns a
   slot — another reason §3.7 forbids touching sellers.
8. **FROZEN check:** if the Agent is in `skills/capafy/FROZEN.json` (it has
   sold), stop. No reprice, no model switch, no card/package edit. Only an
   UPDATE.json carrying `dais_approved_exception` overrides.

### 3.4 Pricing and request-cap math

- **Anchor ladder (winner band):** Weekly **$12.99** / Monthly **$29.99** /
  Yearly **$149.99**, exactly three plans, **No Free Trial on every plan**
  (measured: top-10 sellers = 1/10 carry a trial; our own 69 free-trial
  units earned $0 and burned Sonnet cost). Market bands for clones: week
  median $6.99, month p25 $12.99 / median $19.10 / p75 $22.99, year median
  $149.99 — copy your specific winner first, band second.
- **Contribution per cycle** = `0.8 × price − cap × cost_per_request −
  sandbox fee`. Worked with measured OpenRouter prices (assume ~4k input +
  1k output tokens per request; state your own assumption when re-pricing):
  - DeepSeek V4.1 Flash ($0.091 in / $0.182 out per MTok): ≈ **$0.0006/req**
    → cap 40/mo costs ≈ $0.02. Margin is not the constraint; demand is.
  - Claude Sonnet 5 ($2.00 / $10.00 per MTok): ≈ **$0.018/req** → cap 40/mo
    ≈ $0.72; cap 480/yr ≈ $8.64. Fine on a *paying* plan — fatal on free
    units at volume. Hence the trial ban and §3.5.
- **Cap is a cost control, not a feature.** Copy the winner's cap; never
  raise it to look generous. Expensive models get low caps (winners run
  10–27 requests/month on Sonnet-class).
- Refunds are a price signal: 30d refunds $32.97 on $129.87 gross (25%).
  A listing with repeat refunds gets its promise rewritten (honesty gap),
  not its price cut.

### 3.5 Per-listing OpenRouter P&L gate (hard — full spec in the P&L file)

Standing audit file: anicca-ops `files/capafy-openrouter-pnl-2026-11-21.md`
(§3 classes, §4 pause rules, §6 loop definition). The rules:

1. **Prepaid only.** Spend comes from the existing OpenRouter balance
   ($56.38). No new payment, no top-up, no auto-reload — ever. Auto-reload
   OFF is *proven*, not assumed: total_credits must read **$155.00**
   invariant every run; any increase = reload event, report immediately.
2. **Classes, recomputed each run from the detail API:** PASS (DeepSeek-class
   or revenue-covering) / WATCH (Sonnet 5) / RISK (Sonnet 4.6) / CHECK
   (model null — read the console before judging).
3. **Migration queue:** RISK → WATCH, zero-revenue listings first, via the
   publisher CLI route; read the model string back from the detail API
   after every migration before recording it. A listing whose *measured*
   revenue covers its Sonnet cost with margin keeps its model — the
   2026-10-07 lesson (sellers died after a Sonnet→DeepSeek switch) and the
   2026-11-16 restart decision reconcile here: **we migrate listings that
   have no sales to lose; we never touch listings whose sales pay for
   their model.** FROZEN sellers are excluded regardless (§3.3 line 8).
   **Queue order as of 2026-11-22 (recovery plan §3 P5):** online RISK =
   7785270416 Data Analyst FIRST (verified winner clone — Best Data
   analysis, 18 sales; prep package ready in goal
   `hidden_files/capafy-r1-fix-7785270416/`), then 8416888650, 4866150011,
   6667600273, 8875030146, 8750239743 (bundle trial removal + day-plan
   removal into the same version), 6959704729. **7599205243 goes LAST**:
   it is in `skills/capafy/RETIRED.json` (retired 2026-10-05, near-duplicate
   academic/humanizer family, doc 4.2) yet still online — the lane decides
   separately whether it stays online at all; do not spend a review slot
   migrating it before that decision. **3332784488 Japanese Humanizer is
   EXCLUDED**: download listing (credential model reads null → no hosted
   inference cost) and a proven seller (37 units); its RISK class is a
   display-string artifact. Sellers on Sonnet 5 are not a diff — platform
   winners run Sonnet-class too (§2.1).
4. **Window check:** if host-key spend in a window exceeds Capafy net
   revenue in the same window, flag it in the run record. Pausing/delisting
   has **no API route** (publisher api-docs lifecycle gap) — queue the exact
   console steps in the record; never write "paused" from an API record.
5. Report revenue, cost, and profit **together**, per window and cumulative.
   Unmeasured = say unmeasured (per-listing revenue split is not exposed by
   the sales API; do not fabricate it from aggregates).

### 3.6 In-platform distribution (the disabled half — turn it back on)

In-platform first (it is free and it is where buyers already are):

- **Title / category / tags are the search surface.** Title = outcome-first,
  ≤50 chars, the words buyers search (copy the winner's keyword pattern).
  Category = the winner's categoryId intent (JP label in the CP1 dropdown).
  Tags = winner's tags + the market-search terms that surface the winner.
- **Test discipline:** one variable per listing per week, non-sellers only,
  changed via the normal version flow with an English note; record the
  before/after (orders, detail views where the console shows them) in the
  run record. No silent edits — an unrecorded test did not happen.
- **Free→paid funnel:** free downloads are our traffic engine (Clip Map
  2,919 uses on 2026-11-22, +162/week, ≈ 54% of inflow at ~0% conversion).
  The fix is routing, not more free assets: free listing descriptions point
  to the paid winner-family listing; the paid listing's welcome message
  names the free one as the trial path. Measure the click/buy delta per
  run. **Standing weekly check (added 2026-11-22):** every weekly cycle
  verifies by console readback that 7095835081 and 2455220100 descriptions
  still carry the routing line to Hook Lab — as of 2026-11-22 they do NOT
  (recovery plan D2); wiring them is plan step P2, and a missing line found
  by the check is fixed in that same cycle.
- **External rotation (owned channels only, $0):** the
  `capafy-distribute` pattern — a free aniccaai.com article + X via Postiz
  per slot, rotating listings, every link carrying its registered `ct=`
  parameter. The top earner (Hook Lab) takes **half of all distribution
  slots**; sellers get the marketing, non-sellers get the tests.
- **GitHub funnel:** every open-source skill repo README links its paid
  Capafy Agent (official guide, §1). We open-source everything — this is
  our cheapest shelf.

### 3.7 Iteration / shipping cadence

- **Hourly (measurement loop):** §4 metrics + P&L classes + migration queue
  advance + rejection cycle (§3.8). No run ends on "noted" — a detected
  blocker is worked or explicitly handed over with an owner.
- **Per 3h cycle (distribution loop, when re-enabled):** metrics diagnosis
  → one improvement shipped → article/social distribution executed →
  funnel check. A cycle that only polished is a failed cycle.
- **Weekly:** ≥1 NEW listing shipped (winner clone, §3.2) — new Agents are
  the growth unit; iteration of non-sellers happens only after the new
  ship. One distribution test concluded and recorded. Migration queue
  shorter than last week.
- **Monthly:** payout reconciliation — wallet (pending/confirmed/balance)
  vs platform net vs bank receipt, three layers kept separate
  (CAPAFY-STATUS §2). Balance is not income until the bank shows it.
- **Never touch a seller** (FROZEN rule). Every historical seller update
  preceded its sales stopping. Marketing goes to sellers; building goes to
  new Agents; fixing goes to non-sellers.

### 3.8 Rejection recovery playbook

1. **Read the reason in the console** (`capafy.ai/developer/myAgent`, saved
   login). The detail API does not expose reasons — console read is the
   only primary source.
2. **Classify:** (a) model mismatch → §3.3 lines 1–2; (b) non-English text
   → line 3; (c) overclaim → line 4, rewrite to the honest reframe;
   (d) config-keys unconfirmed → line 6; (e) other → quote the console
   text verbatim in the record before acting.
3. **Fix and resubmit in the same run.** Prepare the corrected package
   first (F1 pattern: recovered original + canonical config added, skill
   content byte-identical), set the English update note, pass §3.3, submit.
4. **Read back `under_review`** from the detail API. "Submitted" without
   the readback is not a state.
5. **Same reason twice in a row** → escalate to main with the reason, the
   fixes attempted, and the exact remaining blocker (F1's key-entry route
   is the standing example). Until approval lands, keep cycling — a
   rejected listing that nobody resubmits is a stopped lane.
6. Current queue: review_rejected 2590720317 Conversion Copywriter /
   3040652346 TikTok Slideshows via ReelFarm API / 6839055303 Academic
   Humanizer / 4437197514 Anicca Life Manager; under_review 2672128973
   Social Post Writer (watch for verdict each run).

## 4. Metrics read each run + the exact ledgers

Read each hourly run (Capafy API + OpenRouter Management API, nothing else
counts): inventory by status (online/draft/offline/review_rejected/
under_review) with transitions vs last run; orders + gross + refunds + net
for today / 7d / 30d / 90d from `/agent/sales/trend` (new vs repeat split);
payout wallet (pending / confirmed / balance); OpenRouter total_credits
(invariant $155.00), total_usage, balance, per-key usage increments
(`capafy-host-2026-11-06`, `capafy-agents-20261115`); model mix across all
listings from the detail API (plural endpoint); per-listing P&L class;
FROZEN/rejection queue states; the one change this run made.

Write to, every run:
1. `~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/capafy-recurring-YYYY-MM-DD-HHMM.md`
   — the run record (the format of run #135 is canonical).
2. anicca-ops `files/capafy-openrouter-pnl-2026-11-21.md` — dated P&L audit
   entry (classes, window spend vs revenue, migration readbacks), commit +
   push, origin readback verified.
3. `capafy-autopublish/state/published.jsonl` — on any publish/version event.

## 5. Hard rules (no exceptions)

- No new API payments; no OpenRouter top-up or auto-reload; prepaid balance
  only; exhaustion is reported, never bought around.
- Credential values never appear in chat, logs, records, commits, or this
  skill. Key entry is vault→console direct only (§3.3 line 6). fal keys are
  revoked and banned — never read, enter, or use them.
- Never edit a FROZEN seller. Never delete a listing to fix a problem.
- Numbers are measured or written as unmeasured. Views do not exist in the
  API — they are UNKNOWN, always.
- No questions, approvals, or cards to the founder from any loop using this
  recipe.

## 6. Loop wiring (who consumes this recipe)

- **`anicca-capafy-recurring-hourly`** (hourly, enabled) — owner of §3.3
  (gate on every submission it makes), §3.5 (P&L audit, its step 6), §3.8
  (rejection cycle, its step 5), §4 (metrics + ledgers). Its job body
  already references the P&L file; add this skill as its recipe pointer
  (change flagged below, not silently applied).
- **`anicca-capafy-loop`** (3h) — the natural owner of §3.6 distribution +
  §3.7 shipping cadence, and currently **`enabled: false`**. The lane has
  no running distribution owner until this is resolved.
- **Exact change needed (recommendation — do not apply silently):**
  1. Re-enable `anicca-capafy-loop` with its body simplified to one line:
     "Run the capafy-revenue-recipe skill (§3.6 + §3.7): diagnose the
     funnel from the latest hourly record, ship one improvement and the
     distribution rotation with ct= links, verify by landed URLs, record
     in the run file." Keep its existing overrides (key sufficiency, fal
     ban, 100%-copy gate) as an appendix, not the body.
  2. In `anicca-capafy-recurring-hourly`'s body, add one line after the
     P&L step: "Recipe正本: custom-skills/capafy-revenue-recipe (review
     gate §3.3, P&L gate §3.5, rejection cycle §3.8)."
  3. Register both on the company to-do board with the hourly lane as DRI
     for Capafy revenue, per company-task-management.
  Verify any change by the next scheduled run landing its record file.

## 7. Recovery findings (2026-11-22 — founder-ordered revenue recovery)

Full plan: anicca-ops `files/capafy-revenue-recovery-2026-11-22.md`
(commit e686e4f5). The findings this skill now carries:

1. **The lane was switched off, not out-competed.** Sellers froze when
   distribution stopped (last artifact 2026-11-14) and shipping stalled in
   the review queue. Recovery order is therefore: distribution ON (P1) →
   free→paid routing (P2) → review queue unblocked (P3) → one new
   winner-clone per week (P4) → cost queue (P5). Cost work never outranks
   distribution work in this lane again.
2. **Revenue judge, restated:** a run that improves listings but ships no
   distribution and unblocks no queue is a failed run, however clean its
   measurements are. The hourly record must name the one revenue-moving
   action it took (shipped, submitted, routed, or marketed) — "measured
   only" is a finding, not a result.
3. **Winner diff is a weekly artifact,** not a one-off audit: the weekly
   cycle re-reads the live top-earner board + the top-3 sellers' live
   cards and re-diffs our top-3 sellers (price ladder, caps, trial,
   category, card structure), recording every diff by name in the run
   record. Zero diff is the standard; a diff carried two weeks without a
   fix or a FROZEN reason is escalated to main.
4. **Conflicts are flagged, never averaged** (Hook Lab price story, §2.1).
   When two primary records disagree, the plan names both and the exact
   read that would settle it.
