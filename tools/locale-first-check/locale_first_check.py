#!/usr/bin/env python3
"""locale-first-check: deterministic gate for experiment ORDER and paywall
localization scope. Stdlib only, no API, no cost.
Source (read in full 2026-11-13): Chuvak Pavel, "State of App Monetization
2026: Key Trends from RevenueCat and Adapty", Medium 2026-03-25, synthesising
RevenueCat (115,000+ apps) and Adapty (16,000 apps, 105,000 paywalls).
This is a SECONDARY synthesis: numbers below are attributed to Adapty /
RevenueCat as reported there, not measured first-hand by us.
- "locale tests are the highest-ROI experiment type in the entire dataset,
  delivering 62.3% LTV uplift according to Adapty"
- Experiment uplift ranking: locale (translation + currency) 62.3% LTV,
  trial structure 59.6%, plan duration 58.7%, price LAST at 45.5% LTV /
  28.3% conversion uplift
- "translating your paywall into your top five revenue market languages
  delivers 37% more LTV uplift than changing a price"
- "Start with structure, then localization, then copy. Price comes last"
- Fastest-growing, under-targeted markets in dataset: Japan, Mexico, Turkey
URL: https://chuvak-pavel.medium.com/state-of-app-monetization-2026-key-trends-from-revenuecat-and-adapty-8bdc23a4bb6f
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    m = d.get("markets") or {}
    if not m.get("top_markets_recorded"):
        fails.append("L-0 top revenue/download markets are not recorded from actual store data -- 'top five' cannot be chosen by guess or by language the team happens to speak; the locale test is defined on the top five REVENUE markets")
    if m.get("top_markets_recorded") and len(m.get("top_markets") or []) < 5:
        fails.append("L-0 fewer than five top markets are recorded -- the source test is localization into the top FIVE revenue-market languages; a shorter list is a different, smaller test")
    if not m.get("growth_markets_evaluated"):
        warns.append("L-0 fastest-growing markets in the dataset (Japan, Mexico, Turkey) are not explicitly evaluated in the market list -- they may legitimately fall outside a given app's top five, but the evaluation must be recorded, not skipped")
    o = d.get("experiment_order") or {}
    if o.get("next_test_type") == "price":
        fails.append("L-1 the next planned experiment is a PRICE test before a locale test has been run and measured -- in the reported ranking price is the LAST lever (45.5% LTV uplift) and locale is first (62.3%); running price first spends the scarcest resource (test traffic / time) on the weakest lever")
    if o.get("price_test_before_locale_complete"):
        fails.append("L-1 a price test is scheduled before the locale test completes -- sequence in the source is structure, then localization, then copy, price last; a price result measured on an unlocalized paywall does not transfer to the localized one")
    loc = d.get("localization") or {}
    if not loc.get("paywall_translated"):
        fails.append("L-2 the PAYWALL itself is not translated -- a localized store listing with an English paywall localizes discovery, not the purchase decision; the 62.3% figure is for paywall locale tests")
    if not loc.get("currency_localized"):
        fails.append("L-2 currency is not localized on the paywall -- the source defines a locale test as translation AND currency localization together; translation alone is half the test")
    if loc.get("scope") == "store_listing_only":
        fails.append("L-2 localization scope is store-listing only -- listing localization and paywall localization are different experiments with different denominators; counting the listing as the locale test overstates coverage")
    cov = d.get("coverage") or {}
    top = set((m.get("top_markets") or []))
    done = set(cov.get("localized_paywall_languages") or [])
    if top and not top.issubset(done):
        missing = sorted(top - done)
        fails.append(f"L-3 paywall is not localized for all top-five markets -- missing: {', '.join(missing)} (coverage must be judged market by market, not as a language count)")
    ms = d.get("measurement") or {}
    if not ms.get("per_locale_ltv"):
        fails.append("L-4 LTV is not measured per locale -- the claimed effect is an LTV uplift (62.3%); an aggregate LTV that mixes localized and unlocalized markets cannot show it, and a Day-0 conversion read is the wrong window for an LTV claim")
    if not ms.get("denominator_per_locale_recorded"):
        fails.append("L-4 the per-locale denominator (paywall viewers / eligible installs in that market) is not recorded -- without it a locale 'win' can be a traffic-mix change, not a localization effect")
    if not ms.get("price_held_constant_during_locale_test"):
        fails.append("L-4 price is not held constant during the locale test -- changing price and locale together makes the result unattributable, which is exactly why the source orders the tests instead of stacking them")
    if not ms.get("observation_window_recorded"):
        warns.append("L-4 no observation window is recorded for the locale test -- an LTV-uplift claim needs a stated window; an unrecorded window invites reading the test on whatever day looks best")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app','?')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
