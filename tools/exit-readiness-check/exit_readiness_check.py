#!/usr/bin/env python3
"""exit-readiness-check: deterministic gate for keeping every app SELLABLE
(exit / acquisition readiness maintained as a standing option, not a fire sale).
Stdlib only, offline, free. Exit 0 = PASS, 1 = FAIL.

Sources (read in full 2026-11-21):
- Flippa, Sell Your iOS & Android App / Selling a Mobile App Business in 2026
  https://flippa.com/sell/app
  H1 2026 closed sales: average 2.62x annual NET PROFIT, top quartile 5.46x;
  median sale 2.52x revenue / 2.93x profit. Sold apps averaged >3 years old.
  Buyers price profit QUALITY: predictable subscription/IAP renewal over
  one-off or ad income; they inspect retention, churn, conversion, the
  App Store / Google Play revenue split, and organic vs paid installs
  (paid growth that stops with the budget is discounted). Prepared listings
  (store data, revenue reports, code handover plan ready BEFORE listing)
  are the stated difference between an average and a top-quartile multiple.
  Timing: list when recent numbers are steady, after a release has settled
  and ratings have recovered -- not mid-migration or just after a rejection.
  Sales volume fell 15% HoH; buyers are choosier and reward ready listings.
- BlueThrone (acquirer, 100+ apps bought), How to Sell an iOS App in 2026
  https://bluethrone.io/blog/how-to-sell-my-ios-app
  Buyers start from NET proceeds after Apple's cut, minus the cost of
  running the app WITHOUT the founder. Renewals move price more than
  downloads (a month-12 retention chart beats any install spike). Steps:
  12 months of clean numbers (net proceeds, profit, active subs, M1/M6/M12
  renewals, refunds, installs by source) -> clean house (one repo you
  control, every third-party account listed with its owner, no personal
  data out of place) -> get YOUR valuation first -> LOI -> due diligence
  (buyer verifies revenue in App Store Connect by screen share / read-only)
  -> money into ESCROW -> App Transfer, then hand over code/servers/accounts.
  NEVER transfer before the money is secured. Apple App Transfer criteria:
  both accounts stable + latest agreements accepted, >=1 released version,
  not on pre-order, no version in/waiting review, no IAP product-ID clash,
  no Apple Arcade. Founder checklist: app-specific shared secret generated
  BEFORE transfer (else renewals break), TestFlight builds/testers and
  Xcode Cloud data removed first, Sign in with Apple transfer identifiers
  for every user (+ ungroup shared sign-in), keychain re-login + buyer's
  own push keys after first update, Apple Pay merchant IDs / Wallet passes
  do not transfer, back up everything (app vanishes from seller account).
  The 15% Small Business rate belongs to the ACCOUNT, not the app: after
  transfer the app earns at the buyer's rate, and a careful buyer prices
  that in -- disclose it before agreeing a number. Red flags buyers check
  first: one-off revenue spike, renewal rates not showable by cohort,
  most installs from paid ads with rising CPI, app not updated for latest
  iOS/SDK, code/servers/accounts in someone else's name, unanswered reviews
  mentioning bugs or billing problems.
- Samet Teke, App Due Diligence Checklist for Sellers (2026)
  https://sametteke.com/blog/app-due-diligence-checklist/
  Five buyer checks: revenue (source-system exports, 12-24 months, NOT a
  self-typed spreadsheet; RevenueCat overview for subscription apps),
  costs (ad spend by channel with matching installs), traffic (downloads
  by source type + keyword rankings), product health (code, SDKs, crashes,
  third-party accounts), store history (rejections, warnings, removals;
  INCENTIVIZED OR BOUGHT REVIEWS ARE A DEAL-BREAKER -- manipulating ratings
  violates the App Store Review Guidelines). Share under NDA by screen
  share / screenshots; never hand out the Apple Account password.

Separation from existing gates: sbp-check covers the Small Business fee
rate itself (this gate only requires DISCLOSING that the rate does not
travel with the app); review-prompt / review-response checks cover rating
inflow and replies (this gate only requires a clean, manipulation-free
store record as a sale asset). This gate covers sellability as a standing
option for all six apps: numbers, profit definition, evidence, transfer
mechanics, escrow discipline, and timing.
"""
import json, sys


def check(d):
    fails = []
    n = d.get("numbers") or {}
    # EX-1 twelve months of clean numbers from source systems
    if (n.get("months") or 0) < 12:
        fails.append(f"EX-1 only {n.get('months')!r} months of numbers assembled (buyers start from 12 months of clean numbers; a shorter or partial history is priced as unproven)")
    if n.get("source") != "source_system_exports":
        fails.append(f"EX-1 numbers source is {n.get('source')!r}, not source_system_exports (due diligence accepts ASC / Play / RevenueCat exports verified by screen share or read-only access -- a self-typed spreadsheet proves nothing)")
    if not n.get("net_proceeds_after_store_cut"):
        fails.append("EX-1 numbers are gross, not net proceeds after the store cut (buyers value what lands in the bank; gross sales overstate the asset by the full commission)")
    # EX-2 profit definition + recorded multiple benchmark
    p = d.get("profit") or {}
    if p.get("basis") not in ("sde", "net_profit"):
        fails.append(f"EX-2 profit basis is {p.get('basis')!r}, not sde/net_profit (apps price as a multiple of annual profit -- Flippa H1 2026 average 2.62x, top quartile 5.46x; pricing on revenue or MRR alone ignores the cost of running the app without the founder)")
    if not p.get("running_costs_without_founder_recorded"):
        fails.append("EX-2 the cost of running the app without the founder is not recorded (buyers subtract it from your number first; an unrecorded cost base makes any valuation fictional)")
    if not p.get("multiple_benchmark_recorded"):
        fails.append("EX-2 no closed-sale multiple benchmark is recorded (Flippa H1 2026: average 2.62x annual profit / median 2.93x profit, top quartile 5.46x -- an asking price with no comp is a guess)")
    # EX-3 renewal / cohort evidence
    r = d.get("retention_evidence") or {}
    if not r.get("renewals_by_cohort"):
        fails.append("EX-3 renewal rates cannot be shown by cohort (M1/M6/M12 renewals move the price more than downloads; 'renewal rates you cannot show by cohort' is a named buyer red flag)")
    if not r.get("churn_and_refunds_tracked"):
        fails.append("EX-3 churn and refunds are not tracked alongside renewals (buyers inspect retention, churn and conversion together; renewals without the refund line hide the leak)")
    # EX-4 revenue quality split
    q = d.get("revenue_quality") or {}
    if not q.get("recurring_vs_oneoff_split"):
        fails.append("EX-4 revenue is not split recurring vs one-off/ad (predictably renewing subscription revenue is worth more than income that can swing with one policy or algorithm change)")
    if not q.get("store_split_recorded"):
        fails.append("EX-4 the App Store / Google Play revenue split is not recorded (buyers look at it explicitly; the two stores carry different fee and billing-failure profiles)")
    if not q.get("organic_vs_paid_installs"):
        fails.append("EX-4 installs are not split organic vs paid (growth that disappears the day the budget stops is treated as rented, not owned, and priced at the bottom of the range)")
    # EX-5 codebase runs without the founder
    c = d.get("codebase") or {}
    if not c.get("single_repo_controlled"):
        fails.append("EX-5 code is not in one repository the company controls (a clean, documented codebase in one controlled repo is a stated top-quartile factor; scattered code is transfer friction)")
    if not c.get("build_release_documented"):
        fails.append("EX-5 build and release are not documented well enough to run without the founder (buyers pay for an app they can run with confidence from day one)")
    # EX-6 third-party inventory and ownership
    t = d.get("third_party") or {}
    if not t.get("accounts_inventoried_with_owners"):
        fails.append("EX-6 third-party accounts / SDKs / APIs are not inventoried with owners (servers, analytics, RevenueCat, push: every account listed with who owns it; an unlisted dependency surfaces in diligence as risk)")
    if t.get("assets_in_personal_or_contractor_name"):
        fails.append("EX-6 code, servers or accounts sit in a personal or former-contractor name (a named buyer red flag: you cannot cleanly sell what you do not cleanly own)")
    # EX-7 clean store record, zero manipulation
    s = d.get("store_record") or {}
    if not s.get("rejections_warnings_explained"):
        fails.append("EX-7 past rejections, warnings or removals are not recorded with explanations (store history is one of the five due-diligence checks; an unexplained gap reads as a hidden removal)")
    if s.get("review_manipulation"):
        fails.append("EX-7 review manipulation is present (incentivized, bought or otherwise manipulated reviews are a deal-breaker for most buyers AND violate the App Store Review Guidelines -- including coordinated 'mark negative reviews unhelpful' schemes)")
    # EX-8 transfer criteria pre-checked
    tr = d.get("transfer") or {}
    if not tr.get("apple_criteria_prechecked"):
        fails.append("EX-8 Apple App Transfer criteria are not pre-checked (released version exists, nothing on pre-order or in/waiting review, latest agreements accepted on both sides, no IAP product-ID clash, not Apple Arcade -- discovering a blocker mid-deal stalls the close)")
    if not tr.get("subscription_handover_plan"):
        fails.append("EX-8 no subscription handover plan (app-specific shared secret generated BEFORE transfer or renewals break on the buyer's servers; Sign in with Apple transfer identifiers for every user; TestFlight / Xcode Cloud cleared first)")
    # EX-9 own valuation before any negotiation
    if not d.get("own_valuation_first"):
        fails.append("EX-9 no valuation of our own exists before listing or negotiation (get your number first -- before anyone else sets it for you)")
    # EX-10 route chosen by size, fees recorded
    rt = d.get("route") or {}
    if rt.get("channel") not in ("marketplace", "broker", "direct"):
        fails.append(f"EX-10 sale route is {rt.get('channel')!r}, not chosen among marketplace / broker / direct (small apps fit public marketplaces, larger ones a broker-run process, profitable ones often direct buyers -- the route decides fees and timeline)")
    if not rt.get("fees_recorded"):
        fails.append("EX-10 route fees are not recorded (listing + success fees are a real cost of the exit; an unrecorded fee is an unmeasured cut of the price)")
    # EX-11 escrow and safe disclosure discipline
    e = d.get("escrow_disclosure") or {}
    if not e.get("escrow_before_transfer"):
        fails.append("EX-11 the rule 'money into escrow before any transfer' is not recorded (never transfer an app before the money is secured -- the transfer is minutes, recovering a transferred app is not)")
    if e.get("password_shared_for_diligence"):
        fails.append("EX-11 account passwords are handed out for due diligence (verification is by screen share, screenshots or read-only access under NDA -- never the Apple Account password)")
    # EX-12 timing gate
    if not d.get("timing_gate_recorded"):
        fails.append("EX-12 no timing gate is recorded (list when recent numbers tell a steady story, after a release has settled and ratings have recovered -- not mid-migration and not just after a rejected update)")
    # EX-13 standing readiness + fee-rate disclosure
    st = d.get("standing") or {}
    if not st.get("data_room_refreshed_on_cadence"):
        fails.append("EX-13 the data room is not refreshed on a standing cadence while NOT selling (readiness kept warm is what makes the sale an option at all; assembling 12 months of proof under a buyer's deadline is how multiples are lost)")
    if not st.get("small_business_rate_disclosed_as_nontransferable"):
        fails.append("EX-13 the Small Business 15% rate is not recorded as account-bound (the rate belongs to the developer account, not the app; after transfer the app earns at the buyer's rate and a careful buyer prices that in -- undisclosed, it becomes a renegotiation)")
    return fails


def main():
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    if fails:
        print(f"FAIL {len(fails)}")
        for x in fails:
            print(" -", x)
        return 1
    print("PASS 13/13")
    return 0


if __name__ == "__main__":
    sys.exit(main())
