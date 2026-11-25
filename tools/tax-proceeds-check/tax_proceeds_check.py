#!/usr/bin/env python3
"""tax-proceeds-check: deterministic gate for App Store tax categories and
net proceeds (the money that actually lands, not the sticker price).
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.

Sources (read in full 2026-11-23):
- Apple, "Set a tax category for In-App Purchases" (App Store Connect Help)
  https://developer.apple.com/help/app-store-connect/configure-in-app-purchase-settings/set-a-tax-category-for-in-app-purchases
  IAPs default to the app's tax category; a per-IAP override is then managed
  separately (later app-level changes no longer affect it); "Match to parent
  app" restores the default; changes affect future transactions only and do
  not change the price. Roles: Admin, Marketing, or App Manager.
- Apple tax/price notice of 2026-11-17, as reported in full by PPC Land
  https://ppc.land/apples-california-buyers-face-2027-sales-tax-on-dating-boosts-and-software/
  New taxes already modified proceeds in Botswana (14% VAT), Cameroon (3% SEP),
  Cote d'Ivoire (3% SEP), Rwanda (18% VAT); Dec 3 2026 price updates for
  Botswana/Colombia/Egypt/Rwanda/Turkiye EXCLUDE auto-renewable subscriptions,
  so on subscriptions the new tax comes out of the developer's share unless
  the developer changes the price; proceeds are calculated on price minus
  applicable taxes; a new "SaaS" attribute is available for the App Store
  Software, Software Training Material, Dating and Boosting categories;
  apps never assigned a category default to App Store Software; a category
  that does not fit breaches the developer agreements and local tax law;
  from 2027-01-01 California sales/use tax applies to SaaS, App Store
  Software, Software Training Material, Dating and Boosting -- US prices are
  tax-exclusive so proceeds do not change but the customer's total may rise;
  US/CA transaction taxes appear in a transaction tax report in Payments and
  Financial Reports from the first full month after configuration.

Separation: price-check = price points/changes; price-consent-check = price
increase consent; sbp-check = Small Business Program commission tier;
paywall-locale-ppp = locale/PPP pricing; commitment-check = commitment
billing option. This gate owns only tax-category assignment and the
proceeds (after-tax) reading of revenue.
"""
import json, sys

CHECKS = [
    ("per_app_category_recorded", "TX-0 no per-app tax category is recorded from App Store Connect (an unrecorded category is an unmade decision; apps never assigned one silently default to App Store Software)"),
    ("per_iap_override_inventory_recorded", "TX-0 no inventory of per-IAP tax category overrides (an overridden IAP is managed separately -- later app-level changes no longer reach it, so an unlisted override drifts forever)"),
    ("owner_named", "TX-0 no named owner for tax category and proceeds (only Admin / Marketing / App Manager roles can change the setting; an unnamed owner means nobody can)"),
    ("category_fits_product_not_default_assumed", "TX-1 the category is the unexamined default rather than the category that best describes the product (Apple: choose the category that best describes the IAP; a category that does not fit breaches the developer agreements and local tax law)"),
    ("subcategory_and_attributes_answered", "TX-1 subcategory / attribute questions are unanswered (selections can require a subcategory and attributes; a half-finished selection is not a classification)"),
    ("saas_attribute_evaluated", "TX-1 the new SaaS attribute (App Store Software, Software Training Material, Dating, Boosting) has not been evaluated for fit (from 2026-11-17 it exists in App Store Connect, and SaaS is one of the categories named for California tax from 2027-01-01)"),
    ("proceeds_are_price_minus_tax_recorded", "TX-2 it is not recorded that proceeds are calculated on the price minus applicable taxes (gross sticker price is not revenue; in tax-inclusive storefronts the tax comes out before commission)"),
    ("net_proceeds_by_top_storefronts_tabulated", "TX-2 net proceeds per sold plan are not tabulated for the top storefronts (the same $59.99 lands differently in the US, JP, DE and BR; pricing and LTV decisions made on the US figure alone are made on the best case)"),
    ("tax_inclusive_vs_exclusive_understood", "TX-2 the tax-inclusive vs tax-exclusive split is not recorded (most storefronts display tax-inclusive prices; the US displays prices exclusive of tax, so the same nominal price is a different product in each)"),
    ("apple_tax_notices_monitored", "TX-3 Apple tax and price notices are not monitored on a cadence (the 2026-11-17 notice had already modified proceeds in four countries when published, and gave 16 days to the Dec 3 price update; a team that reads notices late learns about its own pay cut late)"),
    ("subscription_exclusion_from_price_updates_understood", "TX-3 it is not recorded that Apple's scheduled price updates exclude auto-renewable subscriptions (in Botswana and Rwanda the new VAT therefore comes out of the developer's share on every renewal unless the developer changes the subscription price)"),
    ("manual_storefront_tax_responsibility_recorded", "TX-3 it is not recorded that storefronts whose prices are manually managed are the developer's own responsibility for taxes and exchange rates (Apple will not adjust them)"),
    ("california_2027_applicability_decided", "TX-4 California 2027 applicability is undecided (from 2027-01-01 sales/use tax applies in California to SaaS, App Store Software, Software Training Material, Dating and Boosting; an app left on the default App Store Software category is in scope)"),
    ("california_proceeds_unchanged_customer_total_rises_recorded", "TX-4 it is not recorded that California tax leaves proceeds unchanged but raises the customer's total (US prices are tax-exclusive; support and pricing copy that assume the listed price is the charged total will be wrong for California buyers)"),
    ("transaction_tax_report_location_known", "TX-4 the transaction tax report is not located (US/Canadian transaction taxes appear in Payments and Financial Reports from the first full month after configuration; without reading it, category correctness is unverifiable)"),
    ("sales_vs_payments_reconciled_monthly", "TX-5 sales reports and payments are not reconciled monthly (taxes, withholding, refunds and Apple's monthly FX rate sit between the two; an unreconciled gap is unexplained gross-profit leakage)"),
    ("category_change_future_only_understood", "TX-5 it is not recorded that a category change affects future transactions only and does not change the price (a fix does not repair past proceeds, and expecting a price change from it double-counts the effect)"),
    ("decision_review_date_set", "TX-5 no review date is set for the tax-category decision (Apple added three tax notices in 2026 alone and a new attribute in November; a category chosen once and never re-read silently expires)"),
]
def main(path):
    s = json.load(open(path))
    fails = [msg for key, msg in CHECKS if s.get(key) is not True]
    for f in fails: print("FAIL", f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__ == "__main__":
    if len(sys.argv) != 2: print("usage: tax_proceeds_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
