#!/usr/bin/env python3
"""web-funnel-check: deterministic gate for web-to-app / web checkout funnels.
Stdlib only, offline, free. Exit 0 = PASS, 1 = FAIL.

Source (read in full 2026-11-21): Airbridge, "Does Web to App Improve
Profitability? The Real Numbers" (published 2026-05-27, updated 2026-11-05)
https://www.airbridge.io/en/blog/does-web-to-app-improve-profitability
- RevenueCat controlled IAP-vs-web test (Dipsea, ~3,100 users/variant):
  trial starts 27.0% IAP vs 18.1% web (-33%); trial-to-paid 25.0% vs 26.3%;
  web produced $0.93 take-home per $1.00 of IAP. Fee savings were real;
  the conversion loss was larger.
- Rule: if annual ARPU is below $60, stay with IAP. Below ~18% web
  conversion the channel loses money; break-even is ~21-22% against a
  25% IAP conversion; validate landing conversion above 20% before
  committing to full funnel infrastructure.
- Adapty (16,000+ apps, via Airbridge): Month 1 retention web 84.5% vs
  in-app 48.2%, but by Month 8 web ~20% vs in-app ~30%; average LTV
  web $10.8 vs in-app $40.1 -- the gap is a retention story, not a fee story.
- Web-acquired users overlap only ~15% with mobile-acquired users
  (Paddle via Business of Apps): the value is a genuinely new audience,
  not rerouted App Store traffic. Rerouting existing traffic adds
  friction to a working funnel and destroys value.
- Durable ROI cases typically meet at least 2 of 4 conditions: high
  annual price, genuinely new web audience, B2B/invoice need that IAP
  cannot serve, pricing-flexibility need. Web-to-app is a growth
  channel, not a billing hack; it carries ongoing maintenance
  (landing pages, payment compliance, entitlement sync, attribution).

Separation from existing gates: external-purchase-check covers store
policy for external purchase links; winback / revenuecat-web-winback
cover lapsed-subscriber recovery on the web. This gate is only the
acquisition-side decision: whether a web checkout funnel should exist
at all, and under what evidenced conditions.
"""
import json, sys


def check(d):
    fails = []
    dec = d.get("decision") or {}
    # WF-1 decision recorded, framed as growth channel not billing hack
    if not dec.get("recorded") or dec.get("framed_as_fee_saving_only"):
        fails.append("WF-1 no recorded decision framing web-to-app as a growth channel (Airbridge: the most expensive mistake is applying it as a cost-reduction / billing tactic; the fee savings are real but smaller than they look)")
    arpu = d.get("arpu") or {}
    # WF-2 ARPU audited before any build
    if not arpu.get("audited"):
        fails.append("WF-2 annual ARPU has not been audited before the funnel decision (the source's first check is: audit your ARPU; below $60/year the fee savings at realistic web conversion cannot cover the overhead)")
    # WF-3 ARPU >= $60 OR at least 2 of the 4 durable-ROI conditions
    val = arpu.get("annual_arpu_usd") or 0
    cond = dec.get("conditions_met") or 0
    if val < 60 and cond < 2:
        fails.append(f"WF-3 annual ARPU is ${val} (< $60) and only {cond} of the 4 durable-ROI conditions are met (source: below $60 stay with IAP; durable cases typically hit at least 2 of: high annual price / genuinely new audience / B2B-invoice need / pricing flexibility)")
    aud = d.get("audience") or {}
    # WF-4 web-only audience hypothesis defined
    if not aud.get("web_only_hypothesis_defined"):
        fails.append("WF-4 no web-only audience hypothesis is defined (which users would respond on the web but would not find the app in the store? If that cannot be answered, the funnel reroutes existing traffic instead of adding revenue)")
    # WF-5 guardrail: does not reroute existing store traffic
    if aud.get("reroutes_existing_store_traffic"):
        fails.append("WF-5 the funnel reroutes existing App Store traffic through web checkout (adding friction to a path that already works loses 25-35% of conversions and nets less revenue)")
    # WF-6 audience overlap measured or measurement planned (~15% benchmark)
    if not aud.get("overlap_measured_or_planned"):
        fails.append("WF-6 audience overlap with existing store cohorts is neither measured nor planned (benchmark: web-acquired users overlap only ~15% with mobile-acquired; without an overlap read, incrementality is assumed, not shown)")
    v = d.get("validation") or {}
    # WF-7 validated before full build
    if not v.get("test_before_full_build"):
        fails.append("WF-7 the funnel was not validated with a small test before full infrastructure was committed (source: test before you scale; validate low overlap and landing conversion first)")
    # WF-8 landing conversion validated >= 20%
    lc = v.get("landing_conversion_pct") or 0
    if lc < 20:
        fails.append(f"WF-8 validated landing conversion is {lc}% (< 20%; break-even against IAP is ~21-22% and below ~18% the channel loses money -- most web funnels start at 15-20%, so an unvalidated or low figure is a forecast of loss, not a funnel)")
    e = d.get("economics") or {}
    # WF-9 net-per-user economics vs IAP, fees and conversion both in
    if not e.get("net_per_user_compared_to_iap"):
        fails.append("WF-9 economics are not computed as net revenue per acquired user versus IAP (fee percentage saved alone is the headline error: RevenueCat's controlled test netted $0.93 per $1.00 of IAP after the full fee saving)")
    # WF-10 trial-start drop budgeted
    if not e.get("trial_start_drop_budgeted"):
        fails.append("WF-10 the forecast does not budget the web trial-start drop (controlled test: 27.0% IAP vs 18.1% web, a ~33% relative decline; a forecast that keeps IAP trial starts and adds web fee savings double-counts)")
    r = d.get("retention") or {}
    # WF-11 web cohort tracked separately through month 8+, LTV not month-1
    mh = r.get("cohort_tracked_months") or 0
    if not r.get("web_cohort_separate") or mh < 8 or r.get("judged_on_month1_only"):
        fails.append(f"WF-11 the web cohort is not tracked separately for at least 8 months (tracked={mh}mo, separate={r.get('web_cohort_separate')}, month1_only={r.get('judged_on_month1_only')}); Adapty 16k apps: web Month 1 retention 84.5% beats in-app 48.2% but reverses by Month 8 (~20% vs ~30%) and average LTV is $10.8 vs $40.1 -- judging on Month 1 alone inverts the verdict")
    o = d.get("operations") or {}
    # WF-12 entitlement sync + email capture + subscription-event attribution + owner
    if not (o.get("entitlement_sync") and o.get("email_capture_at_checkout")
            and o.get("attribution_to_subscription_events") and o.get("maintenance_owner_named")):
        fails.append("WF-12 the operating basics are incomplete (entitlement sync between web purchase and in-app access, email capture at checkout -- the primary CRM asset web creates -- attribution carried to subscription events rather than installs, and a named maintenance owner; the source warns teams underestimate the ongoing work of landing pages, payment compliance, sync and attribution)")
    return fails


def main():
    if len(sys.argv) != 2:
        print("usage: web_funnel_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    total = 12
    passed = total - len({x.split()[0] for x in fails})
    for x in fails:
        print(f"FAIL {x}")
    print(f"RESULT {'PASS' if not fails else 'FAIL'} app={d.get('app')} pass={passed}/{total} fails={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
