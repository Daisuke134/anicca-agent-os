---
name: whop-revenue-recipe
description: Money recipe for Anicca's Whop store — finish payout/tax setup before the 2026-11-30 banner deadline (agent-side), fix the disabled Buy button and unauthenticated CLI, restructure the one-time $29 bundle toward the winner form (recurring community + course + free funnel), work Discover/affiliates/own-traffic levers, and measure every run into the measurement ledger. Use for any Whop selling, listing, pricing, or revenue-measurement work.
---

# Whop Revenue Recipe — Anicca

Purpose: turn Whop from a $0, unverifiable storefront into a measured, recurring
digital-product lane. Whop's winners sell access, community, and tools on
recurring plans — not one-time downloads. Every run ends with a ledger row;
a run with no ledger row did not happen. No credential values in any file, ever.

Store: https://whop.com/anicca-ac43/

## 1. Search record (2026-11-21, checked before building this skill)

Founder rule applied: search first, adopt what exists, build only the missing
piece (the missing piece was an Anicca-specific operating recipe — no existing
skill covers our store, our disabled Buy button, our payout blocker, or our ledger).

| Source | What was checked | Adopted / rejected |
|---|---|---|
| `npx skills find whop` | skills.sh catalog | Hits were integration-oriented (e.g. Higgsfield Whop integration / whop-seller skills — API/store plumbing, ~2.5K installs on the seller entry). ADOPTED as a pointer: Whop API/CLI-first management is the sanctioned route (matches our own bp finding, §2). REJECTED as the recipe itself: none covers winner-copy iteration, payout unblocking, or our ledger. Note: a repeat CLI run on 2026-11-21 timed out on slow npx network; first-run results stand as recorded. |
| `npx skills find "digital marketplace"` | skills.sh catalog | Only generic/unrelated hits (real-estate, SEO, caption skills). None operate a digital-product storefront. Rejected. |
| `npx skills find "api monetization"` (cross-check) | skills.sh catalog | Generic API-monetization hits only; nothing Whop-specific. Rejected for this lane. |
| Web/GitHub: community Whop skills — `whop-digital-store` / `whop-digital-sales` (RA-Skills / ClawHub mirrors, https://github.com/lord1egypt/ra-skills/blob/HEAD/skills/community/clawhub/w/whop-digital-store/SKILL.md and …/whop-digital-sales/SKILL.md) | Store automation via Whop REST API v1; product strategy (free → paid ladder) | PARTLY ADOPTED: the free/paid ladder shape and API-first product management. REJECTED: stub scripts (`pass # Whop REST API`), invented earnings claims ("avg creator $7,300/mo", "5% fee") — never quote unverified numbers; our fee facts come from Whop docs/our loop logs only. |
| Official Whop skill on skills.sh — https://www.skills.sh/whopio/whop-payments-network-skill | Whop's own published skill (payments network) | Recorded as checked. Payments-network scope, not a seller revenue recipe. Not adopted. |
| InsightRaider — "Sell on Whop 2026: 0% Platform Fee (Full Seller Guide)" — https://insightraider.com/en/blog/whop-marketplace-guide (search-read) | What sells on Whop; marketplace discovery; fee shape (0% platform fee + 2.7% + $0.30 processing on direct sales) | ADOPTED: (1) Whop's marketplace sends buyers — discovery/category/trending placement is a real channel, unlike Gumroad; (2) Tier-1 sellers are private communities + software/tool access on recurring plans; courses are Tier-2; one-time downloads are Tier-3 (hardest). Our current offer is Tier-3 form — see §3 restructure. |
| MoveToWhop — "How to Sell on Whop: First-Sale Setup" — https://movetowhop.com/guides/how-to-sell-on-whop (search-read) | Setup checklist per Whop help center (2026-10-03) | ADOPTED as setup hygiene: detailed product page (Whop reviews it), never label one-time pricing "lifetime access" (Seller Terms ban indefinite access — state an access period + auto-expire; our page already states "Access for 1 year"), free trials only on recurring plans, checkout links above $2,500 need approval. |
| aitoolbox.hk — "Whop Review 2026" — https://www.aitoolbox.hk/tools/whop/ (read in full by the Whop loop, 2026-11-21) | Seller-experience review | ADOPTED (already in loop practice): paid community is the money center; one-time packs need own traffic; **Discover takes ~30% vs ~3% direct** — treat Discover as a bonus channel, price so the Discover case still nets positive; don't depend on Whop alone (own surface = aniccaai.com); launch affiliates from day one. |
| In-platform winners, measured live by the Whop loop (2026-11-21) | Income Secrets — https://whop.com/ai-mastery-coaching-hub/income-secrets/ ($9.99/mo, strike $39.96 "Save 75%", 4.9★, 24 ratings); AutomationFlow Pro / WhopFlow — https://whop.com/automateit/automateit/ ($14.99/mo, 3-day free trial, 228 members, 4.6★, 79 ratings, scarcity copy) | ADOPTED as the copy target: recurring monthly price + trial + ratings + members count + transformation headline + "What you get" + guarantee. Our gap list vs these winners is 25 items (§2). |
| Internal audit — `grep -ril -e whop -e renderhub -e x402` over `~/workspace/custom-skills/`, `/opt/muse/skills/`, `~/workspace/anicca-ops/files/skills/`, `~/workspace/tools/` (2026-11-21) | Our own skill/tool inventory | No existing Whop skill anywhere (custom-skills and /opt hits: none; anicca-ops skills dir holds only apify/client-work/gumroad recipes + video-caption-fix; tools hits were venv/binary false positives). This skill is the first. Sibling format copied from `~/workspace/anicca-ops/files/skills/gumroad-revenue-recipe/SKILL.md`. |
| Internal ledgers — `hidden_files/whop-loop-*.md` (~150 run logs, latest 2026-11-21-1833), `hidden_files/contract-platform-ledger.md`, cron body `crons/hourly/anicca-whop-loop__interval@3h.md` | Our measured state | ADOPTED as the state source of truth (§2). |

## 2. Current state (measured, 2026-11-21 18:33 JST run)

Source: `~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/whop-loop-2026-11-21-1833.md` (live browser + curl + CLI readback).

- **Sales: $0, everywhere.** Total balance $0.00; both products All-time revenue
  $0.00; Active users 0; Payments all categories 0 ("No payments yet"); Analytics
  Today Profit / Money in / New customers / Successful payments all $0/0; MRR $0.00;
  Affiliates 0 (default rate 30% is on, unused).
- **Products (2):**
  1. `prod_gb5Fzi06ziXyj` — "AI Monk Database (Full Data) + The Art of AI Monks —
     Bundle", **$29 one-time** (strike $36.25, "Save 20%"), Visible, "Access for
     1 year", 3 attached files, apps shown "F C C C +3".
     URL: https://whop.com/anicca-ac43/ai-monk-database-full-data-the-art-of-ai-monks-bundle/
     Traffic: 9 views / 1 visitor all-time (loop's own verification visits included —
     not demand evidence).
  2. `prod_38KmbP1yeB73V` — "aniccaai.com", **Free**. Headline + Description were set
     on 2026-11-21 ("Free: Inside the AI monk niche — start here"), BUT Visibility
     shows "API" — it does **not** appear in the public store product list, so the
     free funnel is copy-ready but not exposed.
- **Buy now is DISABLED** on the paid product even after page load (DOM
  `[disabled]`, no "You own this product", no reason shown). Guest (logged-out)
  purchasability is still unverified. No test purchase has been made. Do not assert
  a cause (payouts-inactive correlation is unproven).
- **Payouts INACTIVE.** Verifications: Payouts / Whop Card / Bank deposits all
  Inactive (identity verification incomplete). Home shows "No payouts set up" /
  "Get verified". **Tax/payout banner deadline: 2026-11-30** (standing banner from
  setup; the 2026-11-21 run found no banner in Tax/Payments/Home views and VAT/GST
  "Not registered" — treat 2026-11-30 as the deadline regardless; it is 9 days out).
- **Setup checklist "Earn your first dollar": 4/6.** Done: Create a product, Add a
  website, Add your logo, Preview checkout. Remaining: "Share your store link",
  "Verify your account".
- **Whop CLI unauthenticated.** CLI 0.34.1 present; `auth status` = loggedIn false /
  hasSecret false; `products list` = NOT_AUTHENTICATED; API key env unset. All
  measurement/changes currently go through the live browser session. (CLI is
  production-acting, no sandbox — per loop bp note 2026-11-09, from Whop's official
  CLI launch post + docs.)
- **Legal gap:** 4 legal documents "No document uploaded", Require-terms-acceptance
  OFF. aniccaai.com /privacy and /terms exist but cover the iOS app only — they do
  NOT cover Whop payment/refund terms; do not upload them as-is (§3).
- **Winner gap count: 25 open differences** vs in-platform winners (form, social
  proof, value structure, scarcity, free-entry exposure, price ladder, Discover,
  VSL, popup, tracking/checkout links, adaptive pricing, gallery, home posts,
  social links, affiliate ops, funnel, tiered pricing/upsell, cadence, terms
  clarity, clip funnel, legal, onboarding/start-here, iOS price markup, embedded
  checkout). Full list lives in the latest whop-loop log; close ≥1 per run.

## 3. The money recipe

### Step 0 — before anything else (deadline work)
1. **Finish payout/tax setup before 2026-11-30.** This is agent-side work, never
   founder work. Identity verification on Whop is a document/photo-upload flow:
   use the saved government ID photo on file for agent-side KYC
   (`~/workspace/user/media_library/image/photo-2.jpg` — path only, never copy it
   into any repo/skill). If a step demands a *live* realtime check, stop, record it
   in `hidden_files/kyc-pending-list.md` as realtime KYC, and report — that is the
   only founder-class step. Complete tax forms with values already in the shared
   vault/ledgers; never invent a tax ID or address.
2. **Authenticate the Whop CLI** with the company API key from the shared vault
   (anicca-ops `credentials.json`, Whop entry — metadata only in logs: key present
   yes/no, never the value). CLI-first for products/plans/stats thereafter
   (`whop products list`, `whop stats time-series list`); browser only for what
   the CLI cannot do. Remember: CLI acts on production.
3. **Fix purchasability:** reproduce Buy-now-disabled in a logged-out/guest
   session; if guest checkout works, record that and move on; if not, isolate the
   blocker (payouts status vs product config vs visibility) with one variable at a
   time and fix what is fixable in-lane. No test purchases (standing loop rule).

### What to ship/sell (in order)
1. **Make the free product actually public.** Flip `prod_38KmbP1yeB73V` from
   "API" visibility to store-visible so the free funnel exists in fact: free
   entry ("Inside the AI monk niche — start here") → paid bundle upsell inside.
   Free members are the review/affiliate/email seed pool.
2. **Restructure toward the winner form (recurring).** Winners sell community +
   content on $9.99–$14.99/mo with a 3-day trial, ratings, and a member count.
   Build the recurring twin of the bundle: same deliverables + Chat/Forum apps +
   Courses app modules (the database as modules, updated monthly), priced in the
   winner band ($9.99–$14.99/mo, 3-day free trial), keeping the $29 one-time
   bundle as the anchor/upsell ("own it outright for 1 year"). Do not delete the
   existing product — add, don't replace (no-deletion rule).
3. **Then a 3-product ladder:** Free (funnel) → Monthly community (recurring
   core) → $29 bundle (anchor). Later additions only from material we already
   produce (behavior-intervention research packs, datasets), each needing 3–10
   live Whop competitors as demand proof first.

### Pricing logic
- Direct sale net ≈ price − (2.7% + $0.30) (0% platform fee per InsightRaider;
  verify on Whop's fee docs before any price change; international cards add
  ~1.5% + ~1% FX per aitoolbox — price with that margin in mind).
- Discover sale net ≈ price × 0.70. Discover is paid acquisition at ~30%, never
  the plan; own traffic (aniccaai.com, SNS, articles) is the main channel.
- Affiliate commission (30% default, already on) is percentage-of-sale only —
  the net after fees + commission must stay positive on every plan.
- Keep the 20% launch discount framing only while it is true; state access
  periods explicitly ("1 year"), never "lifetime".

### In-platform distribution levers
- **Discover:** prerequisites per loop record = ≥1 review + store completion
  (checklist 6/6). Get the first review legitimately (free-product members,
  existing users of the same bundle on other platforms — ask, never fake).
  Pick the most specific category; marketplace ranking rewards sales velocity +
  ratings, so concentrate launch pushes in one window.
- **Product packaging:** headline = transformation outcome (winner form), then
  "What you get" bullets, FAQ (5 items — already present), guarantee/terms line,
  gallery images that show the actual deliverable, and a short VSL/demo video
  (gap #8 — winners convert on video; static-only pages underperform).
- **Affiliates:** 30% is enabled but has 0 affiliates. Recruit from our own
  surfaces first (bundle buyers, monk-niche creators in the AI Monk Database
  itself); give each a tracking/checkout link (gap #10) so affiliate sales are
  attributable in the §5 metrics.
- **Free community funnel:** free product members get the paid offer inside the
  Whop (pinned post / start-here, gap #23), plus automatic welcome message
  (already configured per loop record). Every free join is a measured funnel step.
- **Off-platform:** store/product links live on aniccaai.com (database + monk
  pages — loop verifies reachability each run), blog articles, and SNS profiles.
  "Share your store link" checklist item closes when these are all live.
- **Legal as conversion protection:** draft a Whop-specific Return Policy (+
  Terms addendum covering Whop transactions), upload the 4 documents, turn
  Require-terms-acceptance ON. This is also dispute protection once money moves.

### Iteration cadence
- **Every loop run (3h):** measure (§5), close ≥1 winner-gap item with a named
  source, verify Buy-button + link reachability, re-check payout/banner status
  until verified. One variable per change; record it in the ledger row.
- **Weekly:** one bigger move from the queue — recurring-product launch, VSL,
  price test, affiliate outreach batch — chosen by last week's numbers.

## 4. P&L guardrail (hard rules)

- **Never spend more than this lane has earned.** Whop lane earnings are $0, so
  lane spend is $0: no paid ads, no paid tools, no paid promotion, ever, until
  revenue exists — and then only from revenue.
- **No new API payments, ever.** Prepaid balances only. If a step needs new paid
  credit, stop and report instead.
- The only allowed "spend" is percentage-of-sale: Whop processing fees, the
  Discover ~30%, affiliate commissions — all zero unless a sale happens, net
  positive on every plan.
- Report revenue, cost, and profit together, per run. Unmeasured = say unmeasured.

## 5. Metrics read each run + ledger format

Read each run (dashboard/CLI, never estimated): total balance, per-product
all-time + period revenue, units sold, active users/members, payments by status,
Analytics profit / money in / new customers / successful payments, MRR, product
page views + visitors, store views, checklist step count, payouts status,
affiliate count + affiliate-sourced users/sales, Discover status (listed or not).
Append one row per run to
`~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl`:

```json
{"type":"whop","ts":"<ISO-8601 UTC>","event":"loop_run","store_url":"https://whop.com/anicca-ac43/","checklist_done":4,"payouts_status":"inactive","buy_button_enabled":null,"cli_authenticated":false,"products_live":2,"units_sold_period":null,"units_sold_lifetime":0,"gross_usd":0,"fees_usd":0,"net_usd":0,"mrr_usd":0,"active_members":0,"page_views_period":null,"affiliates":0,"affiliate_sales":0,"discover_listed":false,"ratings":0,"change_made":"<one-line: what this run changed>"}
```

Use `null`, never a guessed number, for anything not actually read. Also keep the
per-run narrative log at `hidden_files/whop-loop-YYYY-MM-DD-HHMM.md` and the
cross-platform totals in `hidden_files/contract-platform-ledger.md` (existing
loop conventions).

## 6. Standing loop

- **Owner exists:** `anicca-whop-loop` — every 3h, cron body at
  `~/workspace/goals/anicca-revenue-growth-as-life-manager/crons/hourly/anicca-whop-loop__interval@3h.md`,
  single writer for Whop. It already measures, winner-copies (≥1 gap closed per
  run), verifies purchasability, and tracks the 2026-11-30 banner. This recipe
  is its operating manual.
- **Recommended amendment (parent lane to apply — do not edit cron from inside
  this skill):** add to the loop body: "Run the whop-revenue-recipe skill
  (`~/workspace/custom-skills/whop-revenue-recipe/SKILL.md`): Step 0 first until
  payouts are verified and the CLI is authenticated; append the type=whop row
  (§5) every run." Also add a **daily** deadline watch until 2026-11-30: if
  payouts are still Inactive on 2026-11-27, escalate in the daily report —
  the banner must never go dark.
- First iteration action for the next run: make the free product store-visible
  (gap #5 exposure) and reproduce the Buy-button state logged-out — the two
  cheapest unlocks, both $0.
