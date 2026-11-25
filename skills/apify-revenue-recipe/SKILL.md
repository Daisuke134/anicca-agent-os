---
name: apify-revenue-recipe
description: Money recipe for Anicca's Apify Store Actors — wire revenue measurement first (earnings are currently unmeasured), fix reliability, price with pay-per-event, optimize Store SEO/quality score, and iterate a small portfolio into the measurement ledger. Use for any Apify Actor publishing, pricing, monetization, or revenue-measurement work.
---

# Apify Revenue Recipe — Anicca

Purpose: turn our one live Apify Actor into a measured revenue lane. The recipe's
first job is **measurement**: usage stats exist, earnings have never been read.
No earnings number may be quoted until it lands in the ledger from an authenticated
source. Every run ends with a ledger row; a run with no ledger row did not happen.

## 1. Search record (2026-11-21, checked before building this skill)

Founder rule applied: search first, adopt what exists, build only the missing piece
(the missing piece was the Anicca-specific wiring: our Actor, our broken loop, our
ledger, and the earnings read that nobody has ever done).

| Source | What was checked | Adopted / rejected |
|---|---|---|
| `npx skills find apify` | skills.sh catalog | ADOPTED (pointer): found **`samihalawa/apify-store-optimization-expert`** (install: `npx skills add https://github.com/samihalawa/apify-store-optimization-expert`). This is the best existing operator skill for Store optimization — use it alongside this recipe for publication/README/schema/quality-score work instead of reinventing it. Other hits (`apify-cli`, actor-development skills) are build tooling, not revenue operation. |
| `npx skills find "web scraping marketplace"` | skills.sh catalog | Generic scraping skills only (Firecrawl, Crawl4AI, etc.). No marketplace-monetization skill. Rejected for this purpose. |
| `npx skills find gumroad` / `"digital products"` | skills.sh catalog (cross-check) | Nothing usable for Apify. Recorded as checked. |
| Apify official monetization docs (via GitHub mirror) — https://github.com/xyvker-septix-fekdy8/apify-docs/blob/HEAD/sources/platform/actors/publishing/monetize.mdx and https://docs.apify.com/platform/actors/publishing/monetize/ | Pricing models, profit formula, PPR best practices | ADOPTED as ground truth: developer keeps 80%; PPE/PPR profit = `(0.8 × revenue) − platform costs`; a money-losing Actor's monthly profit is floored at $0 (it does not eat other Actors' profit); set memory limits + respect `ACTOR_MAX_PAID_DATASET_ITEMS` / user charge limits so costs can't run away. |
| Apify Academy — "How Actor monetization works" — https://github.com/alman377/apify-docs/blob/HEAD/sources/academy/build-and-publish/apify-store-basics/how_actor_monetization_works.md | Setup flow (Publication → Monetization, billing details, wizard, primary event), price-change rules | ADOPTED: setup sequence; significant price changes (increases, new paid events, model change) need 14-day notice and are rate-limited — decreases/removals are immediate. Plan price experiments around that. |
| Use Apify — "Monetize Apify Actors: PPE Pricing & Payout Rules" — https://use-apify.com/docs/apify-for-developers/monetize-actors (fetched in full) | Payout mechanics, rental sunset, portfolio habits | ADOPTED: **Rental is RETIRED — no new rental listings since 2026-04-01, full retirement 2026-10-01. Never build on rental.** PPE is the flagship model (PPR now expressed as a per-result event inside PPE). Payouts monthly: invoice ~11th, review window ~3 business days (auto-approved if ignored), paid ~21st–25th; minimums $20 PayPal / $100 bank. Console location: Development → Insights → Payouts. Portfolio cross-sell + weekly smoke tests as standing habits. ⚠️ Its "Creator plan $1/mo + $500 prepaid bonus" is a paid offer — NOT adopted (no new payments rule, §5); noted only so nobody buys it by accident. |
| `apify-store-optimization-expert` SKILL.md — https://github.com/samihalawa/apify-store-optimization-expert/blob/HEAD/SKILL.md (fetched) | Full operator playbook: official-source list, idea validation, revenue strategy order, naming/URL rules, PPE implementation, publication checklist | ADOPTED wholesale as the optimization layer: revenue order = product-market fit → reliability → ease of use → output clarity → pricing transparency → Store conversion → SEO → promotion → retention. Key rules kept: charge for valuable outcomes not failed attempts; enable the `apify-actor-start` synthetic event; include concrete README cost examples ("1,000 results ≈ $X"); technical name/URL is a permanent SEO asset — do not rename a live Actor casually; validate demand (Store saturation: 1–5 similar = unproven, 10–30 = healthy, 50+ = saturated) before building adjacent Actors. |
| Apify SEO & promotion docs — https://github.com/lou1sl/apify-docs/blob/HEAD/sources/academy/platform/get_most_of_actors/seo_and_promotion.md ; ApifyForge Learn — https://apifyforge.com/learn | Store/Google SEO ranking factors | ADOPTED: Store search ranks on title match, README keyword density (target keywords in first 100 words), categories, run volume, and quality score; keep success rate >95% — it is both a ranking input and the promotion gate. |
| DEV — "My Apify Promotion Filter" — https://dev.to/the_aientrepreneur_7ae85/my-apify-promotion-filter-scale-clean-apis-hold-back-noisy-demand-2bpg | A working seller's portfolio discipline (63k runs portfolio) | ADOPTED as the promotion rule: promote only Actors at >95% 30-day success; 90–95% = careful lane; <90% = hold back and fix reliability first. Buyer-outcome Actors (lead finders) carry the money pitch; high-volume utility APIs carry trust proof. |
| GitHub — `zarfatinimrod-creator/automaton` revenue-apify-actors SKILL.md — https://github.com/zarfatinimrod-creator/automaton/blob/HEAD/skills/revenue-apify-actors/SKILL.md | Another team's Apify revenue skill (independent project) | PARTIALLY ADOPTED: its discipline — publish free first while a stranger-run count accumulates, separate stranger runs from our own runs, and the warning that **unverified developers are excluded from default Store-API search (discovery is biased low until identity verification)**. Its targets/ceilings are that project's board rulings — rejected, not our numbers. |
| Internal audit — `grep -ril apify ~/workspace/custom-skills /opt/muse/skills ~/workspace/tools`, `~/workspace/anicca-ops/files/skills/` | Our own inventory | No Apify skill existed. One tool exists and is reused: **`~/workspace/tools/measurement/apify_stats.py`** (public stats reader — the source of all ledger rows so far). This recipe is the first Apify skill. |

## 2. Current state (measured, 2026-11-21)

Source: `hidden_files/apify-loop-2026-11-19-0915.md` + `measurement-ledger.jsonl`
(`type=apify` rows, verified by grep 2026-11-21).

- **One live Actor:** `salubrious_verity/google-maps-lead-scraper`
  (Actor ID `IquZc7PbcTPm8P7IT`) — a Google Maps lead scraper, i.e. a buyer-outcome
  category, which the sources say is the money lane.
- **Latest measurement (2026-11-19, manual takeover run):** total runs **26**,
  total users **2**, last-30d runs 15 (11 succeeded / 4 timed out / 0 failed,
  **success rate 73.3%**), reviews **0**, bookmarks **0**, last run 2026-11-18.
  Trend: runs 6 → 20 → 26; success rate 0% → 50% → 73.3%. Improving, but far
  below the >95% promotion gate.
- **Pricing:** PAY_PER_EVENT, flat **$1.50 per 1,000 results**. Tiered pricing
  not applied; free-tier funnel not reflected (backlog items B2/B3, still open).
- **Earnings: UNMEASURED — never read, not once.** Every loop record states
  "売上（Earnings）: 未計測（認証が必要）". The public-stats tool cannot see
  earnings; an authenticated read has never been wired. Treat revenue as
  **unknown**, not $0.
- **The standing loop is BROKEN:** `anicca-apify-loop` (daily 10:22) exists, but
  its job body fails the scheduled-task safety review and every run is skipped
  (pattern `job.safety_review_skip`, recurring since 2026-11-03–06 in an earlier
  form). The 2026-11-19 numbers exist only because the lane was hand-run.
  A skipped loop is a stopped lane — per self-healing rules, whoever sees this
  owns the fix until a run lands.
- **Open backlog from the loop record (priority order, all need Console/browser):**
  B1 real example `exampleRunInput` / B2 tiered pricing / B3 free-tier funnel /
  B4 input form + probeUrls / B5 add-ons.

## 3. The money recipe

### Which Actor categories sell (build/keep order)
1. **Buyer-outcome lead generation** (our current Actor's category): Maps/local
   business leads, vertical lead finders (dental, legal, HVAC, restaurants),
   lead enrichment/validation. Buyers pay because output feeds their revenue.
2. **Clean utility APIs with high repeat volume:** email validation, WHOIS/domain
   intelligence, company enrichment, transcript/content extraction. Lower price
   per event, high run counts, trust proof for the portfolio.
3. **E-commerce / social monitoring:** price trackers, review/social exports —
   high demand but higher breakage; only enter with maintenance capacity.
Rule: one money Actor healthy before any adjacent build. Adjacent Actors are
chosen by the validation method in §1 (keyword demand + Store saturation +
community pain language), never by guessing.

### Pricing logic (PPE is the only default)
- **Model: pay-per-event.** Rental is retired — do not propose it. Express
  per-result billing as a PPE event (`apify-default-dataset-item`) so the Actor
  gets flagship placement and MCP/AI compatibility.
- Enable the `apify-actor-start` synthetic event; charge custom events only for
  valuable outcomes (a delivered lead/result), never for failed attempts.
- **Profit check before any price is set:** estimate cost per 1,000 successful
  results from representative runs (compute units × $0.4/CU + proxy), then price
  so `(0.8 × price) − cost_per_1000 > 0` with margin. Current $1.50/1,000 has
  never passed this check because earnings/costs were never read — §4 fixes that.
- Add **tiered pricing** (backlog B2): volume discounts (Bronze/Silver/Gold)
  only where margin stays positive at the lowest tier.
- **Free-tier funnel** (backlog B3): a small free allowance/sample run so a new
  user reaches a first successful result before paying; free users cost platform
  usage only on free runs — cap it via input defaults and max-items settings.
- Price changes: decreases are immediate; increases/new events need 14-day
  notice, max ~monthly. Batch experiments accordingly.

### Reliability before promotion (the gate)
- Promotion gate: **>95% 30-day success**. We are at 73.3% — timeouts are the
  defect (4/15 runs). Fix order: memory limits in actor config, timeout budget
  per target, graceful partial results instead of all-or-nothing runs, retries
  on transient failures, respect user charge limits and stop cleanly.
- Weekly smoke test on a canonical input; a failed smoke test pauses promotion,
  not the Actor.
- Quality score is a ranking input: keep the default-input test green, dataset
  non-empty, issues answered <24h, changelog/README current.

### Store SEO + conversion (via the adopted optimization skill)
- Run `apify-store-optimization-expert` for the full audit; the non-negotiables:
  keyword-rich title/name (the URL is permanent — do not rename the live Actor),
  README that opens with a plain-language outcome statement with target keywords
  in the first 100 words, a concrete cost example, input/output tables with an
  example JSON, correct categories, icon, dataset + output schemas, real
  `exampleRunInput` (backlog B1), and a working "Try for free" path.
- Portfolio cross-sell: README links between our Actors once a second exists;
  document API/webhook/Make/n8n paths — automation buyers convert on easy pipes.
- Off-Store promotion (only after the >95% gate): one high-intent piece per
  cycle — a tutorial article, a community answer in the buyer's own language,
  a demo post. Promotion pointed at an unreliable Actor burns the listing.

### Iteration cadence
- **Daily (loop):** measure (§6), one reliability or listing fix from the
  backlog queue, ledger row.
- **Weekly:** pricing/funnel review against actual earnings + cost per 1,000;
  smoke-test result; decide promote / hold / fix for the next week.
- **Monthly (payout cycle):** reconcile the Console payout invoice (~11th,
  review by ~14th, paid ~21st–25th) against ledger rows; thresholds $20 PayPal /
  $100 bank — below threshold, balance carries and is reported as balance,
  not income.

## 4. Measurement wiring — the first job (exact steps)

Public stats (already wired — keep): `~/workspace/tools/measurement/apify_stats.py`
reads the public Actor stats into `type=apify` ledger rows (runs, users, success
rate, reviews). It cannot see money. Add the authenticated earnings read:

1. **Credentials:** use the Apify API token already in the shared vault
   (anicca-ops `credentials.json`, Apify entry) via the approved credential
   flow. Never print, log, or write the token value into any file, ledger row,
   or report. If no token exists in the vault, stop and report that — do not
   create a paid plan to get one.
2. **Per-Actor earnings (API):** with the token, read the Actor's monetization /
   earnings figures exposed to the owner (Apify API v2 actor + monetization
   endpoints / Console "Insights" data): current-month revenue, platform costs,
   net profit per Actor, paying customers count. Record the exact endpoint used
   in the run note so the read is reproducible.
3. **Payouts/balance (Console, browser task if API lacks it):** Development →
   Insights → Payouts — read accrued balance, last invoice amount + status,
   next payout eligibility vs the $20/$100 thresholds, and whether developer
   identity verification for payouts is complete (unverified developers are
   also hidden from default Store search — if verification is incomplete,
   record it as a blocker with the same weight as the Gumroad one).
4. **Customer split:** from run data, separate **stranger runs** (other users)
   from our own test runs by user ID. Revenue decisions use stranger numbers
   only; our own runs are cost, not demand.
5. **Write it:** extend the `type=apify` ledger row with the §6 earnings fields
   in the same run as the public stats, so one row = one complete measurement.
   First successful earnings read gets `event: "earnings_measurement_wired"`.
6. **Loop repair (part of this job):** the daily loop body must be simplified
   until it passes the scheduled-task safety review (the 2026-11-19 record's
   own diagnosis: strip credential/API-path wording, mirror a passing loop's
   phrasing, bisect the body). A measurement that depends on hand-runs is not
   wired. Verify the fix by a landed scheduled run + ledger row, not by intent.

## 5. P&L guardrail (hard rules)

- **Never spend more than this lane has earned.** Earnings are currently
  unmeasured, so spendable budget is $0 until §4 lands a positive number.
- **No new API payments, ever.** No new Apify plan, no Creator plan, no paid
  add-ons, no auto-reload. Prepaid/existing balance only; when it is gone,
  report "exhausted" instead of buying more.
- Own test runs cost real platform usage — keep them minimal, small-input,
  and counted as lane cost in the ledger row (`own_runs` field).
- PPE pricing must keep `(0.8 × revenue) − platform costs > 0` per Actor per
  month; a negative Actor is repriced or fixed, never subsidized silently
  (Apify floors its payout at $0, but the compute waste is still ours).
- Report revenue, cost, and profit together. Unmeasured = say unmeasured.

## 6. Metrics read each run + ledger format

Read each run: total runs, total users, users 7d/30d, runs 30d (succeeded /
timed out / failed), success rate 30d, reviews + rating, bookmarks, pricing
model + price per 1,000, **earnings month-to-date (gross, platform costs, net)**,
paying customers, accrued payout balance, last payout (amount + status),
stranger vs own runs. Append to
`~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl`
(extending the existing `type=apify` convention):

```json
{"type":"apify","ts":"<ISO-8601 UTC>","event":"daily_run","actor":"salubrious_verity/google-maps-lead-scraper","actor_id":"IquZc7PbcTPm8P7IT","total_runs":null,"total_users":null,"total_users_7d":null,"total_users_30d":null,"reviews":0,"review_rating":0,"bookmarks":0,"runs30d_total":null,"runs30d_succeeded":null,"runs30d_timed_out":null,"runs30d_failed":null,"success_rate30d_computed":null,"pricing_model":"PAY_PER_EVENT","price_per_1000_usd":1.50,"earnings_gross_mtd_usd":null,"platform_costs_mtd_usd":null,"earnings_net_mtd_usd":null,"paying_customers":null,"payout_balance_usd":null,"last_payout_usd":null,"last_payout_status":null,"stranger_runs30d":null,"own_runs30d":null,"change_made":"<one-line: what this run changed>"}
```

Earnings fields stay `null` until the authenticated read in §4 actually returns
them — `null` means unmeasured; never write 0 for "not read".

## 7. Standing loop

- **Existing loop (owner of this recipe): `anicca-apify-loop`**, daily 10:22 —
  file: `~/workspace/goals/anicca-revenue-growth-as-life-manager/crons/daily/anicca-apify-loop__daily@10:22:00.md`.
  It is the right owner but is currently **broken** (safety-review skips, §2).
- **Required repair (recommendation to the parent lane — this skill does not
  edit cron jobs):** rewrite that job's body in the simplified, passing form
  with this one-line body: "Run the apify-revenue-recipe skill: read public
  stats + authenticated earnings, append the type=apify ledger row, make one
  backlog fix (reliability first, promotion only above 95% success), never
  spend more than earned." Verify by the next scheduled run landing a row.
- No new cron is needed once the repair lands; if the repair cannot pass
  review, fold the same body into the hourly measurement pipeline instead and
  record the substitution in the loop record — the lane must not stay dark.
