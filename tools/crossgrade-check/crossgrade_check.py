#!/usr/bin/env python3
"""crossgrade-check: deterministic gate for Apple subscription PLAN CHANGES
(upgrade / downgrade / crossgrade inside a subscription group). Stdlib only.
Sources (read in full 2026-11-13):
- RevenueCat docs "Upgrades, Downgrades, & Management": developers cannot
  change a customer's subscription; only the customer can. iOS needs no code
  changes. Upgrade = higher level of service, immediate, prorated refund of
  old plan. Downgrade = lower level, takes effect at next renewal at the
  lower price. Crossgrade = same level; same duration begins immediately,
  different duration at next renewal. Upgrading during an introductory
  period (incl. free trial) does NOT cancel the intro offer -- it stays
  active alongside the upgraded product, so two products in one group can
  be active simultaneously. PRODUCT_CHANGE webhooks are informative only;
  the change is in effect on RENEWAL (Apple) / INITIAL_PURCHASE (Google).
  Apple prorated revenue is NOT shown in Customer History but IS counted
  in charts/overview.
  https://production-docs.revenuecat.com/docs/subscription-guidance/managing-subscriptions
- Marteso "Subscription Group Levels" (2026-09-10, citing Apple help):
  the LEVEL number -- not price -- decides upgrade/downgrade/crossgrade.
  Level 1 = most access. One group holds up to 100 subscriptions; a
  subscriber can hold only ONE product per group at a time, so products
  meant to be held simultaneously must be in separate groups. In-group
  switches do not reset the 70%->85% proceeds clock (accumulated paid
  days resume even after a lapse of up to 60 days).
  https://www.marteso.com/blog/app-store-connect-subscription-group-levels-upgrade-downgrade-crossgrade
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    g = d.get("group") or {}
    if not g.get("recorded"):
        fails.append("X-0 subscription group structure is not recorded (which products share one group, and their levels, must be written down before any plan-change behaviour can be predicted -- an unrecorded group makes every switch a surprise)")
    if g.get("recorded"):
        if not g.get("switchable_plans_in_one_group"):
            fails.append("X-0 plans users should switch between are not all in ONE subscription group (switching across groups is a new subscription, not an upgrade/downgrade/crossgrade: no prorated refund, no shared intro eligibility, and the proceeds clock restarts)")
        if g.get("simultaneously_holdable_in_same_group"):
            fails.append("X-0 products meant to be held at the same time sit in the same group -- a subscriber can hold only ONE product per group, so putting a core plan and an add-on in one group silently caps ownership at one of them; simultaneous products need separate groups")
        if (g.get("products_in_group") or 0) > 100:
            fails.append("X-0 group holds more than 100 subscriptions (Apple's per-group cap)")
    lv = d.get("levels") or {}
    if not lv.get("recorded"):
        fails.append("X-1 subscription levels are not recorded (level 1 must be the product offering the most access; without a recorded level map nobody can say whether a given switch bills immediately or at renewal)")
    if lv.get("assigned_by") == "price":
        fails.append("X-1 levels are assigned by PRICE -- Apple decides upgrade vs downgrade vs crossgrade from the level number, not the price; a pricier plan ranked as a lower level produces a 'downgrade' prompt and next-renewal timing for what the paywall sells as an upgrade")
    if lv.get("recorded") and not lv.get("same_access_same_level"):
        fails.append("X-1 same-access durations (e.g. monthly and annual of the same tier) are not on the same level -- different levels turn a billing-period switch into an upgrade/downgrade with the wrong timing; same access must be same level so the switch is a crossgrade")
    cp = d.get("copy") or {}
    if cp.get("promises_immediate_downgrade"):
        fails.append("X-2 paywall/support copy promises a downgrade takes effect immediately -- Apple applies downgrades at the NEXT renewal at the lower price; promising immediate effect creates refund requests and chargeback-grade confusion")
    if cp.get("promises_immediate_crossgrade_different_duration"):
        fails.append("X-2 copy promises an immediate switch between different durations at the same level -- a crossgrade with different durations takes effect at the next renewal; only same-duration crossgrades begin immediately")
    if not cp.get("upgrade_timing_disclosed"):
        fails.append("X-2 upgrade timing is not disclosed where plans are compared (an upgrade bills the new plan in full immediately and refunds the unused old plan prorated -- users who expect end-of-period switching meet an immediate full charge)")
    sw = d.get("switching") or {}
    if sw.get("app_claims_to_switch_for_user"):
        fails.append("X-3 the product claims the app itself switches the user's plan -- stores do not allow developers to upgrade/downgrade on a customer's behalf; only the customer can change it, via the store purchase/management flow")
    if not sw.get("management_path_present"):
        warns.append("X-3 no subscription management path (managementURL / store management screen) is recorded -- users who want to change plans need a reachable route, and RevenueCat exposes managementURL for exactly this")
    en = d.get("entitlements") or {}
    if not en.get("handles_dual_active_during_intro_upgrade"):
        fails.append("X-4 entitlement logic does not handle two simultaneously active products in one group -- when a customer upgrades during an introductory period (including a free trial), Apple keeps the intro offer active alongside the upgraded product; code that assumes exactly one active product per group will misread that state")
    rv = d.get("revenue_model") or {}
    if rv.get("resets_proceeds_clock_on_in_group_switch"):
        fails.append("X-5 the revenue model resets the 70%->85% proceeds clock when a subscriber switches plans inside the group -- in-group upgrades/downgrades/crossgrades do NOT reset accumulated paid service; modelling a reset understates proceeds for switchers")
    ms = d.get("measurement") or {}
    if ms.get("judges_on_product_change_event"):
        fails.append("X-6 plan changes are judged on the PRODUCT_CHANGE event -- RevenueCat marks it informative only; the change is actually in effect on the following RENEWAL (Apple), so counting PRODUCT_CHANGE as an effective switch overstates switches that are only scheduled (every downgrade, every different-duration crossgrade)")
    if not ms.get("prorated_revenue_handling_recorded"):
        warns.append("X-6 prorated-revenue handling is not recorded (Apple prorated revenue from upgrades is absent from Customer History but included in charts/overview -- reconciling the two without this note reads as missing revenue)")
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
