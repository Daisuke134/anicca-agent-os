---
name: renderhub-revenue-recipe
description: Money recipe for Anicca's RenderHub store — convert 115 published low-poly listings with zero sales into a selling catalog: iterate the highest-view listings first (SEO titles/tags, thumbnails), ship the tea-ceremony bundle at the winner kit price band, close the FBX/PBR format gaps, use coupons/sales and Karma/gallery levers, set up payout before the $20 threshold matters, and measure every run into the measurement ledger. Use for any RenderHub selling, listing, pricing, or revenue-measurement work.
---

# RenderHub Revenue Recipe — Anicca

Purpose: turn RenderHub from a 115-listing, zero-sale catalog into a measured,
selling 3D-asset lane. Volume got us to Tier 3; conversion is the missing half.
Every run ends with a ledger row; a run with no ledger row did not happen.
No credential values in any file, ever.

Store: vendor "Anicca" — https://www.renderhub.com/anicca/

## 1. Search record (2026-11-21, checked before building this skill)

Founder rule applied: search first, adopt what exists, build only the missing
piece (the missing piece was an Anicca-specific operating recipe — no existing
skill covers our store, our catalog, or our ledger).

| Source | What was checked | Adopted / rejected |
|---|---|---|
| `npx skills find renderhub` | skills.sh catalog | **No skills found.** Nothing to adopt — recorded as checked (empty result). |
| `npx skills find "digital marketplace"` | skills.sh catalog | Only generic/unrelated hits. None operate a 3D-asset store. Rejected. |
| RenderHub official — "How To Sell Your 3D Models" — https://www.renderhub.com/info/how-to-sell-3d-models-on-renderhub (fetched in full) | Vendor tiers + payout rails | ADOPTED as ground truth: revenue share by catalog size — Tier 1 (1–50 items) 55%, Tier 2 (51–100) 60%, **Tier 3 (101–200) 65%**, Tier 4 (201+) 70%; non-exclusive; payouts via PayPal / Venmo / Payoneer / check / US ACH. Our 115 items = Tier 3 at 65%; Tier 4 needs +86 items. |
| RenderHub official — Support / Selling Tips — https://www.renderhub.com/info/contact-support (search-read, incl. "How To Sell Like a Pro", Sale Manager, coupons, vendor analytics) | Featured/promo criteria, discount tooling, traffic data | ADOPTED: (1) featured/email/social promotion requires high-quality, properly cropped main thumbnails + strong promo images; (2) **a price that is too low excludes a product from marketing promotions** — do not race to the bottom; (3) coupons (Coupon Manager) and store-wide sales (Sale Manager) are first-class levers; (4) add a Google Analytics code in Store Settings to see per-item traffic; (5) Karma/gallery/community activity raises store visibility. |
| Tripo — "Selling 3D Models: A Creator's Guide to Success & Profit" — https://www.tripo3d.ai/blog/explore/3d-models-for-sale (search-read) | End-to-end seller playbook | ADOPTED: presentation (renders, descriptions, tags) is as critical as the model; technical quality is non-negotiable (clean topology, proper UVs, PBR sets at 2K/4K, logical naming/hierarchy); treat the first 10–20 uploads as market learning; start concepts from marketplace best-sellers, not from the 3D tool. |
| Tripo — "Building a Niche 3D Store" — https://www.tripo3d.ai/blog/explore/building-a-niche-store-focus-props-characters-environments (search-read) | Niche-store strategy | ADOPTED: a tight niche beats a generalist catalog (ours: Japanese tea-ceremony / shrine / traditional props — already coherent); modular kits are store best-sellers; professional presentation + strategic metadata are the primary sales tools. |
| CGTrader official help — "How to publish 3D models?" — https://help.cgtrader.com/hc/en-us/articles/360015139237-How-to-publish-3D-models (via RenderHub loop, 2026-11-21) | Listing metadata that moves sales | ADOPTED (already loop practice): titles 4–6 words; items with a 50–100-word description sell ~3× no-description items; items with ~20 tags sell ~2× 5-tag items (RenderHub cap is 16 tags — use all 16, mixed specific + broad + property words). |
| Framekit — "The 12 Best Places to Sell 3D Models in 2026 (By Royalty)" — https://framekit.ai/blog/best-places-to-sell-3d-models-2026 (via loop, 2026-11-21) | Cross-marketplace royalty comparison | ADOPTED as context only: royalty spreads are wide (40–88%); a seller with no followers takes reach from a marketplace and margin from their own store — we have 0 followers, so marketplace catalog growth stays the priority; royalty comparison is never by itself a reason to change a price. |
| In-platform winner, measured live by the RenderHub loop (2026-11-21) — Fun Center Kit by Absurdox — https://www.renderhub.com/absurdox/fun-center-kit-415-low-poly-models | Kit economics on RenderHub itself | ADOPTED as the bundle proof: **415 low-poly models for $19.99 sells as a kit** — Mobile + HD versions, FBX + OBJ + GLB, engine import test stated (Godot 4.7), 2D icons included, state variants systematized, AI-assisted procedural generation disclosed. This is the price/format anchor for our bundle #2 (§3). |
| Internal audit — `grep -ril -e whop -e renderhub -e x402` over `~/workspace/custom-skills/`, `/opt/muse/skills/`, `~/workspace/anicca-ops/files/skills/`, `~/workspace/tools/` (2026-11-21) | Our own skill/tool inventory | No existing RenderHub skill anywhere (only false-positive hits: venv data files, a Solana Pay skill inside `tools/paysh-test/node_modules` — different rail, not adopted). This skill is the first. Sibling format copied from `~/workspace/anicca-ops/files/skills/gumroad-revenue-recipe/SKILL.md`. |
| Internal ledgers — `hidden_files/renderhub-loop-*.md` (~150 run logs, latest 2026-11-21-1818), per-asset folders `hidden_files/renderhub-<asset>-<date>/`, cron body `crons/hourly/anicca-renderhub-loop__interval@3h.md` | Our measured state | ADOPTED as the state source of truth (§2). |

## 2. Current state (measured, 2026-11-21 18:18 JST run)

Source: `~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/renderhub-loop-2026-11-21-1818.md`.

- **Sales: 0. Revenue: $0.00.** Store statement reads "No Transactions" — no
  sales, no balance, ever. (Tasking note said 114 listings; the 2026-11-21 run
  published item #115, so the live count below is the fresher measure.)
- **Catalog: 115 active unique items** (114 at the start of 2026-11-21, +1 Low
  Poly Dobin Teapot, product ID 428924, published that run; item #116, Hanaire
  Flower Vase, already produced and queued). Gallery: 115 (every item has a
  gallery post). **Tier 3 (101–200 items) → 65% revenue share.** Tier 4 (70%)
  at 201 items = +86 to go; winner stores run 300+.
- **Engagement:** Karma 1,750; Likes Received 40; Favorites Received 1;
  **Followers 0**. Per-item views are thin: the best-known item, the Tibetan
  Singing Bowl, has 112 views / 0 likes / 0 favorites after ~2 weeks; most
  items sit at 1–7 views. Discovery, not catalog size, is now the bottleneck.
- **Pricing: flat $5.00 on every single** (Extended Use License), one existing
  bundle at $12. No item is on sale (Sale Manager empty). One coupon exists:
  **ANICCA20, 20% off, Active, expires Dec 08, 2026, public**.
- **Formats per item:** OBJ + GLB, 6 preview images, procedural (script-generated,
  no generative AI — disclosed in descriptions). Known gaps vs the winner form:
  **no FBX** (winners ship FBX + OBJ + GLB), **no PBR texture sets** (materials
  only), no engine import-test statement, no video / in-scene previews.
- **Payout method: NOT set** ("Add Your Payout Information" on the dashboard).
  RenderHub pays monthly after the 15th for the prior month, **$20 minimum** —
  with $0 sales nothing is owed yet, but payout setup must land before the
  first $20 accrues, not after (agent-side form; no tax/ID values in any file).
- **Production pipeline is proven:** one new verified asset per run (geometry
  re-parsed, previews eye-checked, ZIP = Models/ + Preview/ + README), titles
  4–6 words, 16/16 tags, full descriptions. The machine works; it is pointed
  at volume only. This recipe re-points half of it at conversion.

## 3. The money recipe

### Which listings to iterate first (in order)
Conversion work goes where the (few) buyers already look:
1. **Highest-view items first.** Start with the Singing Bowl (112 views, 0
   likes — people arrive and don't bite: thumbnail/title/price-value problem),
   then Yunomi (7), Chazutsu (5), Futaoki (3) and the rest of the top-10 by
   views each week. For each: re-crop/replace the main thumbnail to the
   featured standard (tight crop, clean background, object fills the frame),
   confirm the title is 4–6 buyer words, confirm 16/16 tags, and check the
   first two description lines carry format + poly count + use case.
2. **The bundle candidates.** The tea-ceremony set (Chasen, Chashaku, Chawan,
   Natsume, Hishaku, Kyusu, Mizusashi, Kensui, Yunomi, Chazutsu, Tetsubin,
   Futaoki, Kusenaoshi, Dobin, Hanaire) is one coherent kit — see bundles below.
3. **Everything else** gets the metadata pass in view order, a few per run —
   never a catalog-wide blind rewrite.

### Listing SEO (the per-item standard)
- Title: 4–6 words, buyer vocabulary first ("Low Poly Dobin Teapot" form).
- Tags: all 16 slots — item words + use/scene words (tea ceremony, tea house,
  museum, display) + property words (low poly, game ready, ceramic).
- Description: full SPEC / contents / use-case structure (already our standard;
  CGTrader data says described items sell ~3×). Keep the procedural/no-genAI
  disclosure line — it is both policy compliance and a trust signal.
- Previews: 6-image standard (¾, front, back, detail, scale, wireframe) on
  every new item; upgrade top-viewed old items to the same set before adding
  more new items in that run.
- License: Extended Use License on everything (re-select after Save Draft —
  the field silently blanks; known bug, workaround is in the loop body).

### Pricing bands
- Singles stay **$5.00**. Do not discount singles below $5: RenderHub excludes
  too-cheap products from promotions, and at 65% share a $5 sale nets $3.25 —
  the lane's problem is zero traffic conversion, not price resistance (no item
  has enough views to have tested price at all).
- Bundles are where the money is: existing bundle $12; **bundle #2 (tea set,
  15 items) at $19.99**, anchored on the Fun Center Kit kit-price proof
  ($19.99 for a large low-poly kit on this very platform). A weapons set and a
  shrine-props pack follow the same band ($14.99–$19.99 by item count).
- Use Sale Manager for time-boxed store sales (e.g. bundle at −20% for a launch
  week) instead of permanent price cuts; keep ANICCA20 as the standing coupon
  and put its code in gallery posts and descriptions of top items.

### Bundle strategy
1. Ship bundle #2 (tea-ceremony set, $19.99) before item #130. One bundle
   listing with a composite thumbnail showing the full set.
2. Every bundle also stays available as singles (non-exclusive, no deletion).
3. A bundle sale is the fastest route past the $20 payout minimum: one bundle
   at Tier 3 ≈ $13.00 credit; two ≈ payout territory. Track progress to $20
   in every §5 row.

### Closing the format gaps (winner parity)
- **FBX:** the single biggest technical gap. Winners ship FBX + OBJ + GLB.
  Route: add an FBX export step to the procedural pipeline (Blender headless
  on the VM) for new items first, then backfill top-10 viewed items. Until
  FBX exists, say so honestly in descriptions (current OBJ + GLB statement).
- **PBR:** add at least a basic PBR set (albedo/normal/roughness) for bundle
  items and top sellers; materials-only is acceptable for $5 singles.
- **Engine statement:** once any item is import-tested (Godot/Blender), state
  it on that listing exactly as winners do; never claim an untested import.

### In-platform distribution levers
- **Gallery + Karma:** every new item already gets a gallery post — keep it
  (Karma 1,750 and rising is our only visibility asset). Add comments/reviews
  on community work and forum presence in the loop's winner-copy step; Karma
  activity is RenderHub's own stated visibility input.
- **Featured eligibility:** main thumbnails on top items must meet the
  featured bar (properly cropped, high quality) — that is the gate for email/
  social promotion, per RenderHub support.
- **Store Settings:** add the Google Analytics tracking code so per-item
  traffic is readable outside the dashboard (support-documented feature).
- **Off-platform:** link the store + bundle from aniccaai.com and the AI Monk
  Database surfaces; one SNS/gallery cross-post per new bundle (free only).

### Iteration cadence
- **Every loop run (3h):** measure (§5); publish the queued new asset (volume
  continues — Tier 4 needs +86); AND do one conversion action (top-item
  thumbnail/metadata pass, bundle progress, or format backfill). Volume-only
  runs are now a recipe violation.
- **Weekly:** re-rank items by views; move the conversion queue to the new
  top-10; review bundle sales path to the $20 payout threshold.

## 4. P&L guardrail (hard rules)

- **Never spend more than this lane has earned.** RenderHub lane earnings are
  $0, so lane spend is $0: no paid ads, no paid promotion, no paid tools.
- **No new API payments, ever.** Prepaid balances only. Asset production is
  local procedural generation (free); if a step needs new paid credit, stop
  and report instead.
- The only "spend" allowed is percentage-of-sale: RenderHub's 35% Tier-3 share
  — zero unless a sale happens. Net per $5 single = $3.25; per $19.99 bundle
  = $12.99. Both positive by construction.
- Report revenue, cost, and profit together, per run. Unmeasured = say unmeasured.

## 5. Metrics read each run + ledger format

Read each run (dashboard + public pages, never estimated): items live, tier +
share %, sales (period + lifetime), earnings $ (period + lifetime), payout
balance + payout-method status, store Karma, likes/favorites received,
followers, per-item views for the top 10, coupon status, items on sale,
bundle count + bundle sales, progress to $20 payout minimum.
Append one row per run to
`~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl`:

```json
{"type":"renderhub","ts":"<ISO-8601 UTC>","event":"loop_run","items_live":115,"tier":3,"revenue_share_pct":65,"units_sold_period":0,"units_sold_lifetime":0,"gross_usd":0,"net_usd":0,"payout_balance_usd":0,"payout_method_set":false,"karma":1750,"likes_received":40,"favorites_received":1,"followers":0,"top_item_views":112,"bundles_live":1,"bundle_sales":0,"coupon_active":true,"change_made":"<one-line: what this run changed>"}
```

Use `null`, never a guessed number, for anything not actually read. Also keep
the per-run narrative log at `hidden_files/renderhub-loop-YYYY-MM-DD-HHMM.md`
and cross-platform totals in `hidden_files/sales-platform-expansion.md`
(existing loop conventions).

## 6. Standing loop

- **Owner exists:** `anicca-renderhub-loop` — every 3h, cron body at
  `~/workspace/goals/anicca-revenue-growth-as-life-manager/crons/hourly/anicca-renderhub-loop__interval@3h.md`,
  single writer for RenderHub. It already measures, winner-copies, publishes
  one new asset per run, verifies Add-to-Cart, and tracks payout status.
- **Recommended amendment (parent lane to apply — do not edit cron from inside
  this skill):** add to the loop body: "Run the renderhub-revenue-recipe skill
  (`~/workspace/custom-skills/renderhub-revenue-recipe/SKILL.md`): every run
  pairs the new-asset publish with one §3 conversion action; bundle #2 ships
  before item #130; append the type=renderhub row (§5) every run."
- First iteration action for the next run: conversion pass on the Singing
  Bowl (112 views / 0 likes) — featured-standard main thumbnail + first-two-
  lines description check — alongside the already-queued Hanaire publish.
