#!/usr/bin/env python3
"""commitment-check: deterministic gate for Apple's monthly price with a
12-month commitment (a billing option on an existing annual plan).
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.

Sources (read in full 2026-11-23):
- Galva, "App Store Retention Messaging and subscription offers: a growth
  team's guide" (2026-10-08, citing Apple Developer documentation,
  Oct 2026) https://galva.io/blog/app-store-retention-messaging-offers-guide
  Facts used: the subscriber pays monthly but commits to the full year,
  which lets the developer offer a more affordable monthly price; if they
  cancel, they stop next year's renewal, not the payments left in this
  one, and Apple reminds them of that on the cancel screen; customers
  need iOS 26.4 or later and the app needs the iOS 26.5 SDK; available
  in every storefront except the US and Singapore; offers are set per
  billing option, so a win-back offer for the annual plan does not
  automatically apply to the monthly-commitment version; the billing
  grace period does not apply to monthly plans with a 12-month
  commitment.

Separation: product-architecture-check = ASC catalog structure;
price-check / price-consent-check = price changes and consent;
paywall-decision-check = model choice; winback-check = win-back offers
on the standard option. This gate owns only the decision and handling
of the 12-month-commitment monthly billing option.
"""
import json, sys

CHECKS = [
    # CM-0 inventory and decision
    ("evaluation_recorded", "CM-0 no recorded evaluation of the 12-month-commitment monthly option (an unevaluated billing option is an unmade decision, not a decision to skip it)"),
    ("owner_named", "CM-0 no named owner for the commitment-option decision"),
    ("per_app_decision_recorded", "CM-0 no per-app decision recorded (adopt / defer with reason / reject with reason, per app, not one blanket assumption for all 6 apps)"),
    # CM-1 eligibility and storefronts
    ("us_sg_exclusion_acknowledged", "CM-1 the US and Singapore exclusion is not acknowledged (the option is unavailable in those storefronts; a plan that assumes it works in the US -- a primary storefront -- is built on a false premise)"),
    ("storefront_scope_decided", "CM-1 no storefront scope decided (which sold storefronts would offer it, and what those subscribers see instead where it is unavailable)"),
    ("sdk_and_ios_floor_verified", "CM-1 the version floor is not verified (customers need iOS 26.4 or later and the app must be built with the iOS 26.5 SDK; older-OS subscribers need a defined fallback to the standard options)"),
    # CM-2 economics
    ("monthly_times_12_recorded", "CM-2 the commitment total (monthly price x 12) is not recorded next to the upfront annual price (the comparison the subscriber effectively makes, and the revenue comparison the team must make)"),
    ("total_vs_upfront_annual_compared", "CM-2 the commitment total has not been compared with the upfront annual price (a lower monthly figure that sums above the annual price, or far below it, changes what this option is: discount, financing premium, or cannibalisation)"),
    ("remaining_payments_understood", "CM-2 the team has not recorded that cancelling stops next year's renewal, not the payments left in the current year (support, copy and refund handling that assume cancel-anytime monthly will mishandle these subscribers)"),
    # CM-3 disclosure, outside = inside
    ("commitment_term_shown_before_purchase", "CM-3 the 12-month commitment term is not shown before purchase (the commitment is the defining fact of this option; hiding it until after purchase makes the outside unlike the inside)"),
    ("not_presented_as_cancel_anytime_monthly", "CM-3 the option is presented as an ordinary cancel-anytime monthly plan (it is not one; presenting it that way is a false claim about the product)"),
    ("cancel_screen_wording_matches", "CM-3 in-app wording about cancelling has not been checked against Apple's own cancel-screen reminder (Apple tells these subscribers the current year's payments continue; app copy that contradicts it creates the dispute)"),
    # CM-4 offers and lifecycle, per billing option
    ("offers_configured_per_billing_option", "CM-4 offers have not been configured per billing option (offers are set per billing option: a win-back or retention offer on the annual plan does not automatically apply to the monthly-commitment version)"),
    ("grace_period_not_assumed", "CM-4 the billing grace period is assumed to cover this option (it does not apply to monthly plans with a 12-month commitment; entitlement handling built on that assumption drops paying subscribers on a failed payment)"),
    ("entitlement_handles_commitment_state", "CM-4 entitlement handling has not been verified for the commitment state (remaining-payments-due subscribers who turned off renewal are still entitled until the commitment year ends)"),
    # CM-5 measurement
    ("commitment_cohort_measured_separately", "CM-5 commitment subscribers are not measured as a separate cohort (mixing them with ordinary monthly subscribers makes both cohorts' churn and revenue unreadable)"),
    ("full_year_completion_tracked", "CM-5 completion of the full commitment year is not tracked (the option's value is only known at month 12 and at the first renewal after it; month-1 numbers cannot judge it)"),
    ("decision_review_date_set", "CM-5 no review date is set for the adopt/defer/reject decision (storefront availability, OS floors and offer support change; a decision with no review date silently expires)"),
]
def main(path):
    s = json.load(open(path))
    fails = []
    for key, msg in CHECKS:
        if s.get(key) is not True:
            fails.append(msg)
    for f in fails:
        print("FAIL", f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: commitment_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
