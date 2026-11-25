#!/usr/bin/env python3
"""seasonal-check: deterministic gate for seasonal / holiday campaigns.
Stdlib only, offline, free. Sources (read in full 2026-11-23):
- RevenueCat, "Holiday offers for subscription apps: data from 5K apps"
  https://www.revenuecat.com/blog/growth/holiday-offers-subscription-apps
  Nearly 5,000 apps, 2025-26 holidays vs Sep 15-Oct 12 baseline. Black Friday
  week (Nov 24-Dec 1): median app WITH a detected promotion +20% new paying
  customers/day, WITHOUT -16%. New Year (Dec 26-Feb 1): +14% vs -4%.
  Christmas-only promotions: no clear advantage (-24% vs -22% without).
  About half the Black Friday increase came from users installed >3 months
  earlier; 55% of BF new payers had installed >=1 day before paying (vs 45%).
  Each BF buyer worth 8% less over 6 months, yet sale-day buyers generated
  12% more 6-month revenue and 60% of apps came out ahead. Annual share of
  first purchases rose 41% -> 49%; lifetime appeared on 35-38% of holiday
  paywalls vs 17% ordinarily. Holiday paywalls: % off on 61% (BF) vs 8%
  ordinarily, crossed-out prices / urgency ~1/3+, single-plan 30-36% vs 20%.
  Caveat in the source itself: groups are described, not predicted; detection
  rests mostly on purchase signals.
- RevenueCat Codelab, "Run a Black Friday or Holiday Sale with Scheduled
  Targeting (2026)" https://revenuecat.github.io/codelabs/holiday-sale-scheduled-targeting.html
  Black Friday Nov 27, 2026; Cyber Monday Nov 30, 2026. Start two weeks
  early (new App Store product needs review). Two shapes: discount the first
  period then regular price, or lock in the sale price via separate products
  (which then live forever; use fixed discount-rate products and reuse them).
  NEVER cut the base price: on the App Store a decrease applies to every
  existing subscriber at next renewal and cannot be reversed. Introductory
  offers exclude anyone who already used an intro offer / trial in the group.
  A free trial can silently win over the discount unless the offer ID is set.
  Mechanism: dedicated holiday Offering + placement + scheduled Targeting
  rule, so the sale switches on/off with no app update. Countdown counts to
  a FIXED date, with an End Stack (standard packages after zero) and a
  Fallback Stack. Price text must use offer variables inside offer rules so
  an ineligible customer never sees a discount they cannot get; keep prices
  and percentages out of Offering metadata.
Delimitation: promo-offer-check owns promotional offers, winback-check owns
lapsed win-back, paywall-decision-check owns model choice. This gate owns
the seasonal campaign as a timed event: window choice, store mechanism,
audience, scheduled presentation, and the 6-month judgement.
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("window_chosen_from_evidence", "SC-0 the campaign window is not chosen from evidence (Black Friday and New Year are where promotions separated from baseline; a Christmas-only campaign is unproven and must not be the sole seasonal plan)"),
    ("baseline_recorded", "SC-0 there is no recorded pre-season baseline (new paying customers/day and revenue, e.g. a Sep 15-Oct 12 window) to judge the campaign against (without it the sale week cannot be read at all)"),
    ("lead_time_two_weeks", "SC-0 preparation did not start at least two weeks before the window (a new sale product must pass store review before it can be sold; same-day preparation forfeits the lock-in shape)"),
    ("mechanism_shape_decided", "SC-1 the offer shape is not recorded: discount the first period then renew at regular price, or lock in the sale price via separate fixed-rate products that will live forever and be reused"),
    ("no_base_price_cut", "SC-1 the sale is implemented by lowering the base subscription price (on the App Store that decrease hits every existing subscriber at next renewal and cannot be reversed; the sale must live in offers / separate products)"),
    ("eligibility_and_trial_conflict_checked", "SC-1 eligibility was not checked: introductory offers exclude anyone who already used an intro offer or trial in the group, and a free trial can silently win over the discount unless the offer ID is pinned on the sale paywall"),
    ("existing_free_users_targeted", "SC-2 the campaign is aimed only at new installs (about half the Black Friday increase in the 5K-app data came from users installed over three months earlier; the existing free base is the first audience)"),
    ("lapsed_and_current_included", "SC-2 current and lapsed subscribers are not considered as a distinct segment (promotional offers / offer codes are their mechanism; in 9% of promoted apps they redeemed at 3x+ the baseline rate)"),
    ("paywall_built_around_missing_features", "SC-2 the holiday paywall is a generic discount banner instead of being built around the paid features long-time free users keep running into, with the discount attached to that upgrade"),
    ("dedicated_offering_scheduled", "SC-3 there is no dedicated holiday Offering switched by a scheduled rule / placement (the regular paywall must stay untouched and the sale must start and end on time with no app update shipped for either)"),
    ("countdown_fixed_date_with_end_stack", "SC-3 the countdown does not count to the fixed real end date with an End Stack of standard packages (a paywall left open past zero must never show an expired price; a resetting or per-visit timer is a fake timer and is banned)"),
    ("price_text_uses_offer_variables", "SC-3 sale price / percentage text is not bound to offer variables inside offer rules (a customer ineligible for the offer must see the regular price, never a discount they cannot get; prices stay out of Offering metadata)"),
    ("six_month_cohort_judgement", "SC-4 the campaign will be judged on sale-week sales instead of the cohort's six-month revenue (Black Friday buyers were worth 8% less each; the win, when it came, was in buyer count over six months)"),
    ("per_buyer_and_total_both_read", "SC-4 revenue per buyer and total cohort revenue will not both be read (per-buyer alone condemns a campaign that 60% of apps came out ahead on; total alone hides the discount's cost)"),
    ("category_benchmark_used", "SC-4 the target is the headline +20% instead of the app's own category gap (Utilities +46% / Health & Fitness +37% vs Education and Social roughly level at Black Friday; the overall median is not your category)"),
    ("lifetime_priced_against_annual", "SC-5 a lifetime option is added for the season without pricing it against what an annual subscriber is worth (lifetime appears on 35-38% of holiday paywalls vs 17% ordinarily; those buyers never renew, so it trades renewals for cash now)"),
    ("no_fake_urgency", "SC-5 urgency copy claims a deadline, scarcity or discount that is not real (limited-time wording is a holiday norm at ~1/3 of paywalls, but a false deadline is the dark pattern already banned in this company)"),
    ("outside_equals_inside_seasonal", "SC-5 store copy, social or email promises a seasonal price or feature that the in-app paywall does not actually deliver to that audience (what is shown outside must exist inside)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__":
    main()
