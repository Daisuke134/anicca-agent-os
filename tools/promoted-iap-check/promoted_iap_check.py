#!/usr/bin/env python3
"""promoted-iap-check: deterministic gate for App Store Promoted In-App Purchases.
Stdlib only, offline, free. Sources (read in full 2026-11-23):
- ASOWin, "Promoted In-App Purchases on the App Store: Full Guide"
  https://www.asowin.com/blog/promoted-in-app-purchases-ios/
  Up to 20 promoted IAPs (subscriptions and non-consumables); they appear on the
  product page, in search results and in editorial placements. Each needs a
  1024x1024 promotional image, a display name and a description in App Store
  Connect; order and per-storefront visibility are controllable. Tapping one
  opens/downloads the app and the purchase continues in-app via StoreKit, so the
  app must receive store-initiated purchases and may defer them (e.g. until
  onboarding completes). Promote products with clear value for NEW users, order
  by appeal, rotate seasonal products into top positions, keep the promoted
  price/offer identical to what the user sees in-app, and measure purchases
  initiated from promoted IAPs, product-page conversion and test results --
  with baseline, release date, audience and markets recorded before reading
  movement. Common mistakes: obscure products, dense unreadable images, a
  broken store-initiated flow, and set-up-once-never-test.
- Mobile Marketing Masterclass / Checkaso (search-read 2026-11-23):
  only the promoted IAP TITLE (<=30 chars) is indexed by App Store search; the
  description (<=45 chars) is not indexed, so keywords belong in the title and
  benefit copy in the description. Consumables cannot be promoted.
  https://mobile-marketing-masterclass.com/blog/how-to-promote-and-optimize-in-app-purchases-on-ios/
Delimitation: iap-name-check owns in-app product naming, availability-check
owns pre-order visibility, cpp-check owns custom product pages, keyword-field-
check owns the 100-char keyword field. This gate owns the promoted-IAP surface
itself: which products are promoted, their indexed titles and images, the
store-initiated purchase flow, and the honesty of its measurement.
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("promoted_iap_inventory_recorded", "PI-0 the promoted-IAP inventory is not recorded per app (which products are promoted, in which order, in which storefronts -- read from App Store Connect, not assumed; an unrecorded surface is an unmanaged one)"),
    ("promoted_iap_exists_for_main_subscription", "PI-0 the main subscription is not promoted at all (promoted IAPs are the only purchasable surface that appears in search results and on the product page before install; without one, store traffic can only install, never start a purchase)"),
    ("only_eligible_product_types_promoted", "PI-1 a consumable or otherwise ineligible product is promoted (only subscriptions and non-consumables can be promoted; a promoted consumable is rejected surface, not a growth lever)"),
    ("promoted_count_within_limit_and_curated", "PI-1 the promoted set is not curated within Apple's limit of 20 (promoting everything promotable is a catalogue dump; the surface is a shortlist ordered by appeal)"),
    ("title_within_30_chars_with_indexed_keywords", "PI-2 a promoted title exceeds 30 characters or carries no indexed keyword (the title is the ONLY promoted-IAP text App Store search indexes; keywords placed in the description are invisible to search)"),
    ("description_within_45_chars_benefit_led", "PI-2 a promoted description exceeds 45 characters or is not benefit-led (the description is not indexed, so its only job is to state the benefit in a few words for a new user)"),
    ("promo_image_1024_readable_at_small_size", "PI-2 a promotional image is not 1024x1024, is dense with text, or is unreadable at search-result size (the image is what competes on the search screen; dense text loses at small sizes)"),
    ("no_misleading_image_or_copy_claims", "PI-2 a promotional image or copy makes a claim the product does not deliver (promoted IAPs are reviewed store surface; a misleading claim is both a rejection risk and a lie to the user)"),
    ("products_selected_for_new_user_clarity", "PI-3 promoted products were not selected for clear value to NEW users (obscure packs that only make sense to experienced users waste the surface; the audience meeting it has never opened the app)"),
    ("order_set_by_appeal_and_tested", "PI-3 promoted order is not set by appeal and never tested (order is a controllable ranking inside your own page; set-up-once-never-test is the documented common mistake)"),
    ("seasonal_rotation_planned", "PI-3 no seasonal rotation into top positions is planned (the promoted order can follow the seasonal windows the seasonal gate already fixes, e.g. New Year 12-21 to 1-10, instead of staying static all year)"),
    ("storekit_promotion_handler_implemented", "PI-4 the app does not implement the StoreKit handling for store-initiated purchases (a tap on a promoted IAP opens/downloads the app and continues the purchase in-app; without the handler the visibility converts into a broken flow)"),
    ("deferral_until_onboarding_or_signin_defined", "PI-4 deferral of a store-initiated purchase is not defined (the purchase must be continuable after onboarding/sign-in completes, not forced before account creation where it fails, and not silently dropped)"),
    ("not_installed_download_path_tested", "PI-4 the not-installed path was never tested (search-result taps often arrive before install; the download-then-purchase continuation is the highest-friction case and the one that breaks)"),
    ("promoted_price_and_offer_match_in_app", "PI-5 the promoted price/offer does not match what the user sees in-app on arrival (store page and in-app paywall must show the same offer and price; a mismatch converts store trust into a refund request)"),
    ("per_storefront_visibility_reviewed", "PI-5 per-storefront visibility/order was never reviewed (promotion can differ by storefront; one global order assumes every market wants the same product first)"),
    ("store_initiated_purchases_measured_with_baseline", "PI-5 purchases initiated from promoted IAPs and product-page conversion are not measured with a pre-change baseline recorded (baseline, release date, audience and markets must be fixed before movement is interpreted)"),
    ("outside_equals_inside_promoted", "PI-5 the promoted surface promises an experience the app does not contain (what is shown outside must exist inside; a promoted bundle or benefit that is not in the product is a lie, not ASO)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
