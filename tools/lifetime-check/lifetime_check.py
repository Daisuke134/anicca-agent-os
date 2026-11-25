#!/usr/bin/env python3
"""lifetime-check: gate for the LIFETIME / one-time purchase rail next to a
subscription - priced from the app's own renewal rate (not a guess), tested on
owned channels and targeted segments before the main paywall, with metered
costs kept out, the subscriber-switch double-charge handled, and lifetime
revenue read separately from recurring. Stdlib only, offline, free.
Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- Airbridge, "Should You Offer a Lifetime Subscription? When It Makes Sense"
  https://www.airbridge.io/en/blog/should-you-offer-a-lifetime-subscription
  One-time/lifetime grew 6.4% -> 10.3% of monetisation models 2023-2025
  (Adapty 2026, 16,000+ apps / $3B); 35% of apps combine subscriptions with
  one-time/lifetime (RevenueCat SOSA 2025, 75,000+ apps). Lifetime is a
  non-consumable IAP, NOT a subscription: no standard free trial, and switching
  from a subscription requires the customer to manually cancel first - the
  two-step regularly produces double charges, refunds and years of support.
  Pricing ranges 2x-12x annual, successful premium offers land at 5x+; the
  number that matters is LTV by cohort (the highest-retention segment's
  3/5/7-year value is the FLOOR, average LTV is dangerous - a 4-year $79/yr
  subscriber is worth ~$316, so a $299 lifetime "gain" was a loss). Yearly
  first-renewal median 66.3% (RevenueCat SOSA 2025). Launch: test via owned
  channels (email/push) before the paywall, target lapsed users and
  long-tenure subscribers first, A/B the multiplier (3.5x vs 5x vs 7x), watch
  refund/support for 14 days; if lifetime exceeds 20-30% of total revenue the
  MRR trajectory is likely being compressed. Red lights: high per-user AI /
  compute costs, funding round within 12 months, multi-tier upsells central,
  not enough retention data to model multi-year LTV.
- ShotCanvas, "How to price a lifetime plan next to a subscription"
  https://www.shotcanvas.app/blog/lifetime-plan-pricing
  Break-even lifetime price = annual price / (1 - annual renewal rate), using
  YOUR OWN renewal rate from ASC/Play retention reports (at r=40% -> 1.67x,
  60% -> 2.5x, 75% -> 4x annual). Break-even is a floor, not a target: buyers
  self-select from the most loyal cohort. Cannibalisation shadow: if annual
  sales drop by roughly as many as lifetime sales arrive, you are converting
  subscribers, not finding new money. Costs never stop: keep features with a
  real marginal cost per use OUT of the lifetime unlock (meter separately);
  if the metered feature IS the app, do not offer lifetime. Commission: a
  one-time purchase never reaches the subscription's year-2 15% rate on
  standard Apple terms (Small Business Program erases the difference).
  Family Sharing on an IAP cannot be turned off once enabled - decide before
  launch. Placement: always-visible third option = anchor (price well clear
  of annual; under ~2 years of annual is underpriced), decline-only, or
  time-boxed. Raising the lifetime price later reads normal; cutting it tells
  earlier buyers they overpaid. Count lifetime revenue on its own line and
  judge growth on recurring revenue alone. Google Play: a one-time purchase
  must be acknowledged within 3 days or Google refunds it automatically.
  Buying lifetime does NOT cancel an existing subscription: on iOS only the
  user can cancel, so direct them to the manage-subscriptions sheet.
Separation: price-check owns subscription price changes/grandfathering;
paywall-structure-check owns plan layout; winback-check owns cancel save
flows. This gate owns only the one-time lifetime rail beside a subscription.
NOT adopted: pushing lifetime on the main paywall to all users as the first
move (both sources name it the worst rollout), and pre-sale lifetime pumping
(gtmsauce records acquirers discounting apps pumped with lifetime revenue).
"""
import json, sys
CHECKS=[
 ("lifetime_surface_recorded_per_app","LT-0 no lifetime / one-time purchase surface is recorded per app (without a recorded surface there is no price arithmetic, placement or read)"),
 ("lifetime_is_nonconsumable_iap_not_subscription","LT-0 the lifetime offer is not implemented as a non-consumable IAP / one-time product (it is not a subscription under store rules: no standard free trial exists for it, and treating it as a subscription product breaks restore and entitlement handling)"),
 ("decision_uses_cohort_ltv_not_average","LT-0 the offer decision is not based on LTV by cohort (the highest-retention segment's multi-year value is the floor; pricing off average LTV sells your most loyal renewers at a discount - Airbridge worked example: 4y x $79 = ~$316 vs a $299 lifetime)"),
 ("lifetime_price_at_or_above_breakeven_formula","LT-1 the lifetime price is below the break-even floor annual / (1 - own annual renewal rate), computed from the app's own ASC/Play retention reports (renewal 40% -> 1.67x, 60% -> 2.5x, 75% -> 4x annual; break-even is a floor, not a target, because buyers self-select loyal)"),
 ("lifetime_multiplier_tested_not_guessed","LT-1 the lifetime multiplier was never tested across candidate multipliers on equivalent segments (Airbridge: A/B 3.5x vs 5x vs 7x before committing; market range is 2x-12x with successful premium offers at 5x+)"),
 ("commission_difference_accounted","LT-1 the price arithmetic ignores the commission difference (on standard Apple terms a one-time purchase stays at the full rate while subscriptions drop to 15% after year one; the comparison must use the app's actual programme terms)"),
 ("lifetime_tested_via_owned_channels_first","LT-2 the lifetime offer was not tested via owned channels (email / push / in-app message) before any main-paywall placement (owned channels keep targeting precise and do not disturb the main conversion flow; broaden only after 2-3 months of owned-channel numbers)"),
 ("lifetime_targets_lapsed_and_long_tenure_first","LT-2 the offer is not targeted first at lapsed users (win-back) and long-tenure subscribers who renewed 2-3 times (placing it on the main paywall for all users is the worst rollout - it cannibalises people who would have subscribed anyway)"),
 ("paywall_placement_deliberate_and_priced_clear","LT-2 the paywall placement is not a deliberate choice (always-visible anchor / decline-only / time-boxed), or an always-visible lifetime is priced under ~2 years of annual (under two years of annual, anyone expecting to stay two years should pick it - the arithmetic says it is underpriced)"),
 ("marginal_cost_features_metered_or_excluded","LT-3 features with a real marginal cost per use (AI calls, server, sync, support-heavy) are inside the lifetime unlock unmetered (a lifetime buyer pays once and can run up costs indefinitely; meter the expensive part separately - and if the metered feature IS the app, do not offer lifetime)"),
 ("family_sharing_decided_before_launch","LT-3 the Family Sharing setting for the lifetime IAP was not decided before launch (on Apple, once Family Sharing is on for an in-app purchase it cannot be turned off - the whole family group gets the unlock at one price)"),
 ("lifetime_scope_and_future_tiers_defined","LT-3 what the lifetime unlock includes is not defined, or future premium tiers are unaddressed (a lifetime buyer believes they bought 'everything'; converting them to a later tier is structurally harder than moving a monthly subscriber - an undefined scope is a multi-year support and upsell liability)"),
 ("subscriber_switch_handles_cancellation","LT-4 the subscriber-to-lifetime switch does not handle the existing subscription (buying lifetime does NOT cancel it: on iOS only the user can cancel, so they must be told plainly and sent to the manage-subscriptions sheet; on Google the server cancels via the Play Developer API - an unhandled switch produces double charges and justified refunds)"),
 ("google_purchase_acknowledged_within_3_days","LT-4 Google Play one-time purchases are not acknowledged within 3 days (an unacknowledged purchase is automatically refunded by Google - lifetime sales lost to a missed server call)"),
 ("refund_support_load_tracked_14_days","LT-4 refund and support volume is not tracked for the 14 days after lifetime purchases (double-charge complaints and refund spikes are the launch's early-warning signal - Airbridge)"),
 ("lifetime_revenue_tracked_separate_from_recurring","LT-5 lifetime revenue is not tracked on its own line with growth judged on recurring revenue alone (a lifetime burst reads like traction while removing your keenest users from next year's recurring revenue - cash now is not growth)"),
 ("revenue_mix_cap_watched","LT-5 the lifetime share of total revenue is not watched against the 20-30% compression zone (above it, the MRR trajectory is likely being compressed by the offer itself - Airbridge)"),
 ("cannibalization_shadow_watched","LT-5 the cannibalisation shadow is not watched (if annual sales drop by roughly as many as lifetime sales arrive, the rail is converting existing subscribers into one-time buyers instead of reaching the subscription-averse - ShotCanvas)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: lifetime_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
