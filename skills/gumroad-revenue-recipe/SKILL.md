---
name: gumroad-revenue-recipe
description: Money recipe for Anicca's Gumroad store — unblock payouts (agent-side ID verification), ship the ready bundle, optimize Discover + affiliates + email, and measure every run into the measurement ledger. Use for any Gumroad selling, listing, pricing, or revenue-measurement work.
---

# Gumroad Revenue Recipe — Anicca

Purpose: turn Gumroad from a blocked, unmeasured storefront into a measured, recurring
digital-product lane. One product live and selling beats ten drafts. Every run ends with
a ledger row; a run with no ledger row did not happen.

## 1. Search record (2026-11-21, checked before building this skill)

Founder rule applied: search first, adopt what exists, build only the missing piece
(the missing piece was an Anicca-specific operating recipe — no existing skill covers
our store, our blocker, or our ledger).

| Source | What was checked | Adopted / rejected |
|---|---|---|
| `npx skills find gumroad` | skills.sh catalog | Nothing returned. No Gumroad skill exists there. Rejected: nothing to adopt. |
| `npx skills find "digital products"` | skills.sh catalog | Only generic hits (e.g. `build-product-visuals`, social caption skills). None operate a Gumroad store. Rejected. |
| `npx skills find apify` / `"web scraping marketplace"` | skills.sh catalog (cross-checked for shared patterns) | Found `samihalawa/apify-store-optimization-expert` — Apify-only, adopted for the Apify sibling skill, not here. |
| J.A. Watte — "Gumroad Discover: Passive Sales From a 1.6 Million…" — https://jwatte.com/blog/blog-gumroad-discover-marketplace/ (fetched in full) | Discover ranking factors, tag strategy, commission boost, free-companion funnel, cross-promotion, Discover analytics | ADOPTED as the Discover playbook core: 5-tag formula (1 broad + 2 specific + 1 format + 1 audience; target tags with 50–500 products), Markdown description structure (problem → what's included → who it's for → how to use → proof), commission boost 20–30% for first 30 days then reduce, free product as email capture, recommended-products cross-promotion on every page. |
| Joy Healey — "The Gumroad Playbook" — https://joyhealey.com/the-gumroad-playbook-why-most-sellers-never-make-real-money-and-exactly-how-the-winners-do/ | 146,271-product dataset: median product sells 28× at $13; $30–$49 converts ~28% better than <$10; 4.5–4.9★ products average 1,197 sales vs 18 with no rating; PWYW gets ratings 2.6× faster | ADOPTED: price in the $29–$49 band (our $29 bundle already sits at the floor of it), chase first ratings aggressively, validate demand (3–10 competitors = proof) before building new products. |
| TierIncome — "Sell Digital Products on Gumroad" — https://tierincome.com/ideas/sell-digital-products-gumroad | Honest counterpoint: Discover alone is thin; traffic must be supplied; catalog of 3–8 products is where revenue compounds; narrow-specific products win; video walkthrough raises perceived value 3–5× | ADOPTED as the corrective to Discover optimism: Gumroad is checkout + delivery, distribution comes from our own surfaces (blog, SNS, email). Build a catalog, not a single listing. |
| Timo Mason via Robin Sanah — "10 Gumroad Hacks That Made Me 8,000+ Sales" — https://robinsanah.substack.com/p/gumroad-sales-hacks | Settings-level conversion tweaks across 45+ products / 8,000+ sales; animated (GIF) thumbnails stand out in Discover | ADOPTED: GIF/demo thumbnail test; audit every settings-panel lever before buying traffic. |
| Fee/payout references — https://saastracker.org/products/gumroad ; https://bestcreatorplatforms.com/reviews/gumroad/ ; https://gb.hostadvice.com/blog/how-to-make-money-online/make-money-on-gumroad/ | Current fee structure | ADOPTED as pricing inputs (verify on gumroad.com/pricing before any price change): direct/profile sales 10% + $0.50 (card processing extra per Gumroad's fees page), Discover sales flat 30% all-in, direct fee drops to 5% + $0.50 above $20k in a calendar month, Gumroad is merchant of record (collects/remits tax since 2025-01-01), weekly payouts above a $10 balance, **email sending unlocks only after $100 earned after fees + a payout received**. |
| GitHub search (web) for gumroad seller playbooks/skills | GitHub-hosted playbooks | No Gumroad seller skill/playbook repo found worth adopting (results were Apify docs and unrelated). Recorded as checked. |
| Internal audit — `grep -ril gumroad ~/workspace/custom-skills /opt/muse/skills ~/workspace/tools`, `~/workspace/anicca-ops/files/skills/` | Our own skill/tool inventory | No existing Gumroad skill or tool anywhere. This skill is the first. |

## 2. Current state (measured, 2026-11-21)

- **Payouts BLOCKED — identity verification UNSUBMITTED.** Gumroad requires a
  government-issued ID photo upload. Status per
  `~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/kyc-pending-list.md`
  (updated 2026-11-21 08:22 JST): verification notice arrived 2026-11-17 16:14, payments
  are paused, a payout-info reminder arrived 2026-11-20 (logged, no reply needed).
  Gate registry #53: "agent-side, submission/review landing unconfirmed."
  Owner of record: Instinct (per fast-response-log). This is an **agent-side task** —
  see §4. It is never founder work.
- **Sales revenue: UNMEASURED.** `measurement-ledger.jsonl` contains **zero**
  `type=gumroad` rows (verified by grep, 2026-11-21). Do not quote any Gumroad sales
  figure until a ledger row exists.
- **One product is ready to ship, not yet confirmed live:** the 2026-11-01 bundle in
  `hidden_files/gumroad-bundle-2026-11-01/` — "AI Monk Database (Full Data) + The Art of
  AI Monks — Bundle", priced **$29**, listing copy finished (`listing-draft.md`),
  deliverables verified (78-record JSON 651 KB, PDF 71 pp, EPUB, cover thumbnail
  candidates). Whether it is actually published on Gumroad is **unverified** — the first
  run of this recipe must check the live storefront and record it.
- Email sending is locked until $100 earned after fees + first payout (platform rule,
  §1) — which is itself gated on the ID verification. Unblocking §4 unlocks everything.

## 3. The money recipe

### What to ship/sell (in order)
1. **Ship the ready bundle first** ($29 AI Monk Database + book). It exists, it is
   verified, and $29 sits in the data-backed $29–$49 conversion band. Do not build
   anything new until this is live, measured, and has its first rating.
2. **Free companion product** (Discover + email engine): a free slice of the database
   (e.g. top-20 accounts extract) or a free chapter sampler. Free "purchases" still
   capture an email and download volume boosts profile visibility in Discover.
3. **Catalog to 3–5 products** from material we already produce: behavior-intervention
   research packs, prompt/word libraries, datasets, template/checklist tools priced
   $5–$15 for impulse tools and $29–$49 for bundles. Narrow and specific beats generic
   ("for [specific person] to stop [specific problem]"). Every new product idea needs
   3–10 existing Gumroad competitors as demand proof before build time is spent.
4. Each product gets a short demo/walkthrough (video or GIF thumbnail) — measured
   3–5× perceived-value lift in the sources above.

### Pricing logic
- Anchor band $29–$49 for substantive products; $5–$15 only for small tools.
- Net math per sale (direct link): price − (10% + $0.50) − card processing.
  Via Discover: price × 0.70. Price so the Discover case is still profitable —
  Discover is paid acquisition at 30%, not a discount channel.
- Bundle > single: offer the bundle as the anchor, singles below it.
- First product may launch Pay-What-You-Want (min $0 or low floor) **only** as a
  ratings-seeding tactic (PWYW reaches 10+ ratings ~2.6× faster); switch to fixed
  pricing once ratings exist. Reviews are the conversion multiplier (rated products
  outsell unrated ~66× in the dataset) — every buyer gets a review ask via workflow.

### In-platform distribution levers
- **Discover optimization:** exactly 5 tags per product (1 broad category, 2 specific
  topic, 1 format, 1 audience; prefer tags with 50–500 existing products); Markdown
  description in the §1 structure; cover image that shows the actual deliverable
  (test a GIF demo thumbnail); commission boost 20–30% for the first 30 days of a
  new product to buy sales velocity, then step down to 10%/off; recency boost means
  a listing refresh/new product is itself a distribution event.
- **Cross-promotion:** set "recommended products" on every product page pointing at
  the rest of the catalog, both directions.
- **Affiliates:** enable the affiliate program per product once it has sales proof;
  start at a commission that keeps the direct-sale net positive after all fees;
  recruit from our own surfaces first. Affiliates are distribution we only pay for
  on a sale — compatible with the P&L guardrail (§5).
- **Email list:** every transaction (including free) captures email. Until Gumroad
  email unlocks ($100 + payout), export the customer list (CSV) each run and keep it
  in the goal workspace; after unlock, set Workflows: purchase thank-you + review
  ask, new-subscriber welcome, abandoned-cart (default 24h) — then use broadcasts
  for each new product launch. The list is the compounding asset; the store is not.
- **Off-platform traffic (we supply it):** link the store from aniccaai.com product
  pages, blog articles, and SNS profiles. Discover is a bonus channel (sources put
  it at ~20–35% of revenue when optimized), never the plan by itself.

### Iteration cadence
- **Weekly:** one improvement per run from this queue — tag/description/thumbnail
  test, price test, new free product, affiliate outreach batch, email broadcast —
  chosen by last week's numbers. Change one variable, record it in the ledger row.
- **Monthly:** catalog review — kill nothing (never delete published content),
  reprice losers upward or bundle them, double down on whatever Discover picked up.

## 4. Unblock path — agent-side ID verification (DO THIS FIRST)

This needs a **browser task** (live Gumroad session). A text fetch cannot do it.
The parent lane must dispatch a browser task with exactly these steps:

1. Sign in to Gumroad with the **agent-owned account credentials from the shared
   vault** (anicca-ops `credentials.json`, Gumroad entry). Never use founder
   credentials; never ask the founder for a code — any 2FA goes to the agent
   route per standing rules.
2. Open Settings → Payments / the verification prompt from the 2026-11-17 notice
   (payouts are paused until this completes).
3. At the identity-verification step, choose the **photo-upload** path and upload
   the saved government ID photo: `~/workspace/user/media_library/image/photo-2.jpg`
   (verified present, JPEG, 2026-11-21). Upload only that file. Do not photograph
   anything new; do not route any step to the founder — photo-upload KYC is
   explicitly agent-side (founder rule, 2026-11-17).
4. Complete any remaining payout details already on file; if a field needs a value
   that exists in the vault/ledgers, use it from there. If a step demands a
   **live/realtime** check (live selfie/liveness), STOP: that is the only
   founder-class step — record it in `kyc-pending-list.md` as realtime KYC and
   report; do not improvise around it.
5. Submit, then screenshot/record the confirmation state. Write the outcome
   (submitted / under review / approved, with timestamp) into
   `hidden_files/kyc-pending-list.md` and append a `type=gumroad` ledger row (§6)
   with `event: "id_verification_submitted"`.
6. On approval: confirm payouts unpaused, confirm the $10 payout threshold state,
   and note the date the $100 email-unlock threshold tracking starts.

## 5. P&L guardrail (hard rules)

- **Never spend more than this lane has earned.** Gumroad has no monthly fee; keep
  it that way — no paid ads, no paid tools, no new subscriptions for this lane.
- **No new API payments, ever.** Prepaid balances only. If a step needs new paid
  credit, stop and report instead.
- The only "spend" allowed is percentage-of-sale: Gumroad fees, the temporary
  Discover commission boost, and affiliate commissions — all are zero unless a
  sale happens, and the net after them must stay positive on every product.
- Report revenue, cost, and profit together, per run. Unmeasured = say unmeasured.

## 6. Metrics read each run + ledger format

Read from Gumroad dashboard/analytics each run: products live (count + names),
units sold (per product, period + lifetime), gross revenue, fees, net revenue,
payout balance / last payout, Discover views, Discover sales, Discover conversion,
total customers/subscribers (email captures), ratings per product, affiliate sales.
Append one row per run to
`~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl`:

```json
{"type":"gumroad","ts":"<ISO-8601 UTC>","event":"weekly_run","id_verified":false,"payouts_paused":true,"products_live":0,"units_sold_period":null,"units_sold_lifetime":null,"gross_usd":null,"fees_usd":null,"net_usd":null,"payout_balance_usd":null,"discover_views":null,"discover_sales":null,"email_captures_total":null,"ratings":{},"affiliate_sales":null,"change_made":"<one-line: what this run changed>"}
```

Use `null`, never a guessed number, for anything not actually read. The first row
must record `products_live` truthfully (is the $29 bundle actually published?).

## 7. Standing loop

- **No dedicated Gumroad loop exists today.** Nearest existing consumers:
  `anicca-kyc-morning-list` (daily 08:22) already tracks the §4 blocker, and
  `anicca-sales-platform-loop` (every 3h) / `anicca-platform-expansion-loop`
  (hourly) mention Gumroad only in passing. None of them runs this recipe.
- **Recommended addition (do not create from inside this skill — parent lane to
  register):** cron `anicca-gumroad-loop`, **daily ~10:22 JST** (offset from the
  Apify loop), body: "Run the gumroad-revenue-recipe skill: verify ID-verification
  status until approved, keep the catalog live and optimized (Discover tags,
  boost window, cross-promo), make one recorded improvement, read all §6 metrics,
  and append the type=gumroad ledger row. Never spend more than earned; no new
  API payments."
- Until that cron exists, the KYC morning list keeps the blocker visible daily —
  the blocker must never go dark.
