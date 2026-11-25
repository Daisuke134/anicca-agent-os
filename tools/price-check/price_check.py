#!/usr/bin/env python3
"""price-check: deterministic gate for subscription PRICE CHANGES (increase/decrease,
existing-subscriber treatment). Stdlib only, offline, free.
Sources (read in full this run, 2026-11-13):
- RevenueCat docs, "Changing Prices": on the App Store an increase notifies affected
  subscribers by email/push and may require agreement; if opt-in is required and they
  do not agree, the subscription expires at the end of the current billing cycle.
  Grandfathering (keep existing at the lower price, raise for new only) needs no consent.
  Grandfathering applies to increases only; removing a product from sale (incl. clearing
  territories) stops renewals for existing subscribers too -- to keep them renewing, leave
  the product on sale and remove it from offerings instead. Decreases are immediate for new
  purchases and apply to active subscriptions at the end of the billing period. Price
  changes take ~24h to propagate. RevenueCat reporting stays accurate after a raise only
  if existing subscribers are grandfathered, unless automatic price detection is enabled
  (V2 App Store Server Notifications + ASC API key uploaded). Google Play: legacy price
  cohort by default; an increase notifies 7 days after the change and subscribers then
  have 30 days to agree or are cancelled at the next renewal.
  https://www.revenuecat.com/docs/subscription-guidance/price-changes
- Launch with Voyage, "When to raise your membership price" (2026-10-13; cites Memberful
  and RevenueCat's TalkingParents case): successful raisers move every 12-18 months;
  memberships retaining >=75%/yr can usually raise up to ~20% without harm. Break-even
  churn = 1 - old/new (+10% -> 9.1% can leave, +20% -> 16.7%, +25% -> 20%, +50% -> 33.3%,
  +100% -> 50%). TalkingParents doubled $4.99 -> $9.99, initially lost ~25% of those
  customers, and still made ~50% more revenue from that tier. Do not raise into a
  retention problem (rising cancels / falling joins / nothing changed since the price was
  set -- a rise speeds the leak up). Apple consent is required when the increase is >50%
  AND >~$5/period (~$50/yr annual), when there was another increase in the past 12 months,
  or where local law requires it; an increase that has taken effect cannot be reversed.
  Give >=30 days' notice (announcement + a reminder 7-10 days before). Announce honestly:
  reason, old and new side by side, generous notice, easy to cancel, more than one message.
  After the change, watch for 2 months: cancels in the 30 days after notice and after the
  first renewal at the new price vs a normal month, joins at the new price, replies
  (complaints from <1% of users are not a cause for concern per RevenueCat).
  https://www.launchwithvoyage.com/guides/when-to-raise-your-membership-price
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    ch = d.get("change") or {}
    is_increase = ch.get("direction") == "increase"
    applies_existing = bool(ch.get("applies_to_existing"))
    # P-0 recorded decision
    if not ch.get("recorded"):
        fails.append("P-0 the price change is not recorded as a decision (old price, new price, scope, effective date, and the reason must exist in writing before ASC is touched -- an unrecorded change cannot be measured or reverted)")
    if ch.get("old_price") is None or ch.get("new_price") is None:
        fails.append("P-0 old and/or new price is missing from the record (the break-even maths and the after-watch both need the exact pair)")
    if not ch.get("scope_recorded"):
        fails.append("P-0 the scope (new subscribers only vs existing too) is not recorded -- on the App Store this choice is the consent question itself, not an implementation detail")
    # P-1 preconditions (increases)
    pre = d.get("preconditions") or {}
    if is_increase:
        if pre.get("retention_problem_unresolved"):
            fails.append("P-1 an unresolved retention problem is present (rising cancels / falling joins) -- both primaries say a price rise does not fix a retention problem, it speeds it up; fix the leak first")
        if not pre.get("value_added_since_price_set"):
            fails.append("P-1 nothing has been added since the price was set (the evidenced trigger for a raise is that members now get clearly more than when the price was fixed; costs alone are not a reason)")
        months = pre.get("months_since_last_increase")
        if months is not None and months < 12:
            fails.append(f"P-1 last increase was {months} months ago (<12) -- successful raisers move every 12-18 months, and on iOS a second increase inside 12 months itself triggers the consent requirement")
    # P-2 break-even maths
    be = d.get("breakeven") or {}
    old, new = ch.get("old_price"), ch.get("new_price")
    if is_increase and old and new and new > old:
        expected_loss = 1 - old / new
        got = be.get("max_tolerable_churn")
        if got is None:
            fails.append(f"P-2 break-even churn is not computed (at {old} -> {new} the change still earns the same if up to {expected_loss:.1%} of affected subscribers leave; without this number there is no line at which the raise is judged a failure)")
        elif abs(got - expected_loss) > 0.02:
            fails.append(f"P-2 recorded break-even churn {got:.1%} does not match 1 - old/new = {expected_loss:.1%} for {old} -> {new} (the maths is fixed: +10% -> 9.1%, +20% -> 16.7%, +25% -> 20%, +50% -> 33.3%, +100% -> 50%)")
        if not be.get("assumed_churn_recorded"):
            fails.append("P-2 no assumed churn scenario is recorded (the primaries model the raise with an explicit assumption -- e.g. TalkingParents doubled and initially lost ~25%, inside the 50% break-even -- not with hope)")
    # P-3 consent mechanics (existing subscribers, increases)
    con = d.get("consent") or {}
    if is_increase and applies_existing:
        pct = (new - old) / old if old and new else 0
        consent_trigger = pct > 0.5 or (pre.get("months_since_last_increase") is not None and pre.get("months_since_last_increase") < 12) or con.get("consent_required_by_law")
        if consent_trigger and not con.get("opt_in_flow_understood"):
            fails.append(f"P-3 this increase ({pct:.0%}) hits an Apple consent trigger (>50%, or a second increase within 12 months, or local law) but the opt-in flow is not accounted for: subscribers who do not agree expire at the end of the current billing cycle -- that expiry wave must be in the model before the change, not discovered after")
        if con.get("removes_product_from_sale"):
            fails.append("P-3 the plan removes the product from sale / clears territories to effect the change -- RevenueCat is explicit that this stops renewals for existing subscribers too; keep the product on sale and remove it from the offering instead")
        if not con.get("grandfathering_considered"):
            fails.append("P-3 grandfathering (existing keep the lower price, new pay the higher) was not considered and rejected/accepted in writing -- it is the lowest-risk form, needs no consent, and costs time rather than members")
    if is_increase and not applies_existing and not con.get("grandfathering_considered"):
        warns.append("P-3 new-subscribers-only scope is recorded but grandfathering is not marked as the considered mechanism (they are the same choice; record it so the next change inherits the reasoning)")
    # P-4 notice & announcement
    nt = d.get("notice") or {}
    if is_increase and applies_existing:
        days = nt.get("notice_days") or 0
        if days < 30:
            fails.append(f"P-4 notice is {days} days (<30) -- both primaries set 30 days as the floor for moving existing subscribers, with a reminder 7-10 days before")
        if not nt.get("reminder_scheduled"):
            fails.append("P-4 no reminder is scheduled 7-10 days before the effective date (the evidenced timeline is announcement at -30d, reminder at -7..-10d, sales surfaces updated on the day)")
        ann = nt.get("announcement") or {}
        if not (ann.get("reason_explained") and ann.get("old_new_side_by_side") and ann.get("easy_to_cancel")):
            fails.append("P-4 the announcement is incomplete (RevenueCat's guide: honest reason, old and new prices side by side, generous notice, easy to cancel, more than one message -- a silent or store-only change teaches subscribers the price is a trap)")
    # P-5 measurement integrity
    ms = d.get("measurement") or {}
    if is_increase and applies_existing and not (ms.get("grandfathered") or ms.get("auto_price_detection_enabled")):
        fails.append("P-5 RevenueCat price integrity is not protected: after a non-grandfathered raise, RevenueCat keeps assuming the purchase price at renewal unless automatic price detection is enabled (V2 server notifications + ASC API key) -- MRR after the change would be read off a wrong price")
    if not ms.get("watch_two_months"):
        fails.append("P-5 no 2-month after-watch is scheduled (cancels in the 30 days after notice AND after the first renewal at the new price vs a normal month, joins at the new price, replies -- a raise is judged on the renewal after it, not the week of it)")
    if ms.get("primary_metric") == "revenue_week_1":
        fails.append("P-5 the change is judged on first-week revenue (the failure mode is the first renewal at the new price; week-1 revenue rises mechanically even when the raise is losing)")
    if ms.get("complaint_threshold_percent") is None:
        warns.append("P-5 no complaint threshold is recorded (RevenueCat's guide: complaints from <1% of users are not a cause for concern -- without the line, the first loud reply can reverse a sound change)")
    # P-6 localization (added 2026-11-22; source: FirstApp pricing guide, full read --
    # RevenueCat SOSA 2026 D35 conversion NA 2.6% vs IN/SEA 1.4%, Y1 LTV $32 vs $14.
    # Optional section: absent = WARN unknown, never a pass. Spec:
    # hidden_files/price-localization-gate-spec-2026-11-22.md)
    loc = d.get("localization")
    if loc is None:
        warns.append("P-6 localization is unrecorded (unknown, not a pass -- a single auto-FX-converted US price is not localization; priority markets, benchmark, PPP ratio, pilot and review cadence are all unmeasured)")
    else:
        if not loc.get("priority_markets_identified_from_delta"):
            fails.append("P-6 priority markets were not identified from the downloads-vs-conversion delta by country (the evidenced signal of a local pricing problem is high downloads with low conversion in ASC/Play data, not a guess)")
        if not loc.get("benchmark_source_recorded"):
            fails.append("P-6 no per-country category benchmark is recorded (the primary names the Adapty Pricing Index -- real transaction medians by country/category -- as the objective starting point, not GDP estimates or feel)")
        if not loc.get("ppp_ratio_recorded"):
            fails.append("P-6 no PPP ratio against the US reference price is recorded (best-converting apps price emerging markets at 0.3-0.6 of the US price; without a recorded ratio the local price is just FX conversion)")
        ratio = loc.get("emerging_ratio")
        if ratio is not None and not (0.3 <= ratio <= 0.6) and not loc.get("out_of_band_reason"):
            fails.append(f"P-6 emerging-market ratio {ratio} is outside the evidenced 0.3-0.6 band with no recorded reason (outside the band is allowed only as a deliberate, written exception)")
        pilot = loc.get("pilot") or {}
        n = pilot.get("market_count")
        if n is None or not (2 <= n <= 3):
            fails.append(f"P-6 pilot market count is {n} (the primary's method: test on 2-3 markets first -- a worldwide rollout of untested local prices is the named mistake)")
        days = pilot.get("days") or 0
        if days < 30:
            fails.append(f"P-6 pilot ran {days} days (<30) -- the primary's floor is 30 days of measurement before adjusting or rolling out")
        judged = set(pilot.get("judged_on") or [])
        if not ({"conversion", "ltv"} <= judged):
            fails.append("P-6 the pilot is not judged on BOTH conversion and LTV (judging on subscriber volume alone is the named 'low price vs adapted price' mistake -- the goal is total LTV, not headcount)")
        if not loc.get("cross_platform_consistency_checked"):
            fails.append("P-6 iOS/Android localized-price consistency was not checked (large store gaps confuse users and break platform switching; the stores must be set consistently)")
        if not loc.get("annual_review_scheduled"):
            fails.append("P-6 no annual review of localized prices is scheduled (markets move -- inflation alone invalidates ratios; the primary's floor is a revisit at least once a year)")
        if not loc.get("premium_markets_considered"):
            fails.append("P-6 premium markets were not considered (some markets show LTV above the US and can justify at-or-above US pricing; a blanket discount without this check leaves revenue on the table)")
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
