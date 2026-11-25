#!/usr/bin/env python3
"""product-architecture-check: deterministic gate for SUBSCRIPTION PRODUCT
ARCHITECTURE (how the store product catalog is structured: when a price test
becomes a NEW product, how preserved-price cohorts survive, and why a product
must never be taken off sale to hide it). Stdlib only, offline, free.
Sources (read in full 2026-11-23):
- RevenueCat "Changing Prices" https://www.revenuecat.com/docs/subscription-guidance/price-changes
  Consider creating a NEW product instead of changing an existing product's
  price for Experiments. Grandfathering applies to a price INCREASE only; it
  does NOT apply when an approved subscription is removed from sale -- taking
  it off sale (including clearing its territories) stops renewals for existing
  subscribers too. To keep them renewing, leave the product ON SALE and remove
  it from your OFFERINGS. Price decreases are effective immediately for new
  purchases and apply to active subscriptions at period end. Price changes
  can take 24 hours to propagate. By default RevenueCat assumes renewals at
  the purchase price, so reporting after a non-grandfathered increase is only
  accurate with automatic price detection (V2 server notifications + ASC API key).
- PricePush "Subscriber Grandfathering: Apple vs Google Play"
  https://pricepush.app/glossary/subscriber-grandfathering
  A lapsed subscriber can resubscribe at the preserved price within 60 days
  of expiration on Apple. Scheduled App Store price changes cannot be
  reversed, so the start date must be planned deliberately. Google Play's
  default for existing subscribers is opt-in (no agreement = cancellation);
  grandfathering there is choosing not to apply the increase (legacy cohort).
Boundary: price-check owns WHETHER to change a price; price-consent-check
owns the consent surface for a pending consent-required increase. This gate
owns the CATALOG structure itself: product IDs, offerings mapping, preserved
cohorts, and the off-sale trap.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
CHECKS = [
 ("PA-0","catalog_recorded","the subscription product catalog (product IDs, prices, durations, storefronts) is not recorded in one place (an unrecorded catalog is whatever each console happens to show)"),
 ("PA-0","catalog_owner_recorded","no single owner is recorded for the product catalog (catalog drift is nobody's job until a renewal breaks)"),
 ("PA-0","offerings_mapping_recorded","the mapping from products to RevenueCat offerings / paywall packages is not recorded (nobody can say which product a given paywall actually sells)"),
 ("PA-1","new_product_for_experiments_rule","no recorded rule that a price EXPERIMENT uses a new product ID instead of changing the live product's price (changing the live price contaminates every existing subscriber and cannot be A/B read)"),
 ("PA-1","scheduled_change_irreversible_acknowledged","the irreversibility of a scheduled App Store price change is not recorded as a planning constraint (a scheduled change cannot be reversed; a careless start date is permanent)"),
 ("PA-1","propagation_window_planned","the up-to-24-hour propagation window for price changes is not planned for (paywall copy and store price disagree for a day and support eats the mismatch)"),
 ("PA-2","preserved_cohort_via_increase_only","preserved-price (grandfathered) cohorts are not created ONLY through a price increase with 'keep current price for existing subscribers' (any other mechanism does not preserve anyone)"),
 ("PA-2","product_never_taken_off_sale_to_hide","a product with active subscribers can be taken off sale / territories cleared to hide it (that STOPS renewals for existing subscribers; hiding is done by removing it from offerings, never from sale)"),
 ("PA-2","lapsed_resubscribe_window_known","the 60-day window in which a lapsed subscriber can resubscribe at the preserved price is not recorded (win-back copy promising the old price after day 60 promises what the store will not honor)"),
 ("PA-3","decrease_timing_known","it is not recorded that a price DECREASE applies immediately to new purchases and to active subscriptions at period end (a decrease is not grandfatherable and cannot be tested on new users only)"),
 ("PA-3","paywall_price_matches_store_product","the price shown on the paywall is not verified to be the store product's actual price for that product ID (copy and catalog drifting apart is a rejection and trust risk)"),
 ("PA-3","one_live_product_per_slot","more than one live product can occupy the same paywall slot (weekly/annual/lifetime) without a recorded reason (duplicate live products split reviews, data and subscriber state)"),
 ("PA-4","reporting_price_basis_verified","RevenueCat's reporting price basis is not verified (default = purchase price; after any non-grandfathered increase, renewals are mispriced unless automatic price detection is on)"),
 ("PA-4","legacy_cohorts_counted_separately","preserved/legacy price cohorts are not counted separately in revenue reporting (blending cohorts hides how much MRR sits on old prices and when it decays)"),
 ("PA-4","cross_store_difference_recorded","the Apple vs Google Play difference for existing subscribers (Apple: notice-or-consent; Google: opt-in by default, legacy cohort) is not recorded (a single-store mental model breaks the other store's subscribers)"),
 ("PA-5","catalog_change_register","there is no register of catalog changes (date, product, old/new price, preserved vs moved, reason) (an unregistered change makes every later conversion shift unexplained)"),
 ("PA-5","removal_checklist_exists","no checklist is required before removing any product from an offering (subscribers-on-product count, preserved status, win-back impact) (removal by tidiness is how renewals die)"),
 ("PA-5","periodic_catalog_audit","the catalog is not audited periodically against ASC / Play Console / RevenueCat (three consoles drift independently; only an audit finds it)"),
]
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = json.load(open(path)) if path != "-" else json.load(sys.stdin)
    fails = [f"{g} {k}: {msg}" for g, k, msg in CHECKS if not data.get(k)]
    if fails:
        print(f"FAIL {len(fails)}/{len(CHECKS)}")
        for f in fails: print(" -", f)
        return 1
    print(f"PASS {len(CHECKS)}/{len(CHECKS)}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
