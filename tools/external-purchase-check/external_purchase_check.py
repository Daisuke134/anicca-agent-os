#!/usr/bin/env python3
"""external-purchase-check: deterministic gate for the EXTERNAL PURCHASE /
APP2WEB surface (linking out / alternative checkout instead of, or alongside,
Apple IAP). Stdlib only, offline, free.
Sources:
- RevenueCat "App2web: a developer's guide to external purchases"
  (revenuecat.com/blog/engineering/app-to-web-purchase-guidelines, read in
  full): rules differ by storefront. US web link-out currently 0% Apple
  commission, no program application, in-app third-party checkout not
  generally permitted. EU (terms effective 2026-10-01): in-app alt checkout
  20%/10% reduced, web link-out 15%/10% reduced, IAP must get equal or
  greater prominence when offered alongside, and the payment-option
  election holds 12 months across all EU storefronts. Japan: 21%/10% and
  15%/10%, IAP must be offered alongside, web offers prohibited under 13
  and parental approval 13-17. In EU/Japan/Brazil the link-out commission
  applies to purchases within 7 days of the tap, with monthly reporting
  covering renewals and refunds. Full cost = Apple commission + processor
  fees + billing support + reporting; web purchases must be tied back to
  the customer's app account so entitlements unlock on return.
- ZeroSettle "External Purchase Reporting" (docs.zerosettle.io, secondary
  automation doc, read in full): where reporting applies (EU DMA, EEA
  music, Japan MSCA iOS 26.4+; US: no token, no report, no commission
  today), setup is entitlement
  com.apple.developer.storekit.external-purchase-link (+ custom-purchase-
  link allowed-regions), SKExternalPurchase* Info.plist keys matching the
  entitlement regions, minimum iOS 17.4 for link-out / 18.1 for custom-link
  token minting, an external-purchase token minted at checkout initiation
  carrying the true App Store storefront, and reports sent via Apple's
  External Purchase Server API with the In-App Purchase key. Token-less
  transactions (old iOS, missing entitlement, declined) must be surfaced,
  not silently dropped.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded_per_storefront"): f.append("EP-0 whether external purchase is used, in which form (link-out vs in-app alt checkout), on which storefronts, is not recorded as a per-storefront decision - the regimes differ in fees, entitlement and reporting, so one global impression is drift, not a decision")
    if not dec.get("owner_recorded"): f.append("EP-0 no single external-purchase owner is recorded")
    if not dec.get("profit_calc_current_terms"): f.append("EP-0 no gross-profit calculation on current terms per regime (Apple commission for that regime + processor fees + billing/refund/tax load vs IAP, including the conversion room it leaves) - a calculation on superseded rates, or none, cannot justify adding or rejecting the surface")
    if not dec.get("entitlement_and_plist_verified"): f.append("EP-0 the entitlement (com.apple.developer.storekit.external-purchase-link where the regime requires it) and the SKExternalPurchase* Info.plist keys are not verified against the app target, with declared regions matching the entitlement regions")
    eli=d.get("eligibility") or {}
    if not eli.get("storefront_from_storefront_api"): f.append("EP-1 the storefront is not taken from the StoreKit Storefront (the user's actual App Store region) - locale, IP or card country misclassifies travellers and expats into the wrong legal regime")
    if not eli.get("eligibility_checked_before_presenting"): f.append("EP-1 eligibility for external purchase on this device/storefront (StoreKit canPresent / external-purchase availability, minimum iOS for the flow) is not checked before the option is presented - ineligible users tap a button that cannot work")
    if not eli.get("minors_excluded_where_required"): f.append("EP-1 minors are not excluded or parent-gated where the regime requires it (EU: not to minors; Japan: web offers prohibited under 13, parental approval 13-17; Brazil: no web offers under 18) - age handling cannot be an afterthought on a payment surface")
    if not eli.get("iap_prominence_and_election_respected"): f.append("EP-1 where IAP must accompany the alternative (EU equal-or-greater prominence and the 12-month election across EU storefronts; Japan/Brazil IAP alongside), that constraint is not recorded as respected - removing or demoting IAP is the Cal AI-style removal risk, not a fee saving")
    flo=d.get("flow") or {}
    if not flo.get("disclosure_sheet_via_storekit"): f.append("EP-2 Apple's system disclosure sheet is not presented through the StoreKit external-purchase API before the user leaves for external checkout where the regime requires it - a hand-rolled warning or a direct browser jump does not satisfy the regime and risks review rejection")
    if not flo.get("token_minted_and_attached"): f.append("EP-2 no external-purchase token is minted at checkout initiation and attached to the transaction where the regime requires one (EU/Japan reporting regimes) - without the token the sale cannot be reported and the commission cannot be settled")
    if not flo.get("destination_own_no_intermediary"): f.append("EP-2 the link does not go directly to the developer's own checkout destination (an intermediary / landing hop breaks the link-entitlement terms in the regimes that forbid it)")
    if not flo.get("purchase_tied_to_app_account"): f.append("EP-2 a completed web purchase is not tied back to the customer's app account so the entitlement unlocks on return - a paid user who comes back still locked out has bought support load, not revenue")
    rep=d.get("reporting") or {}
    if not rep.get("transactions_reported_in_window"): f.append("EP-3 external transactions (including the 7-day post-tap attribution window, renewals and refunds in EU/Japan/Brazil-type regimes) are not reported to Apple within the regime's window via the External Purchase Server API / a reporting integration - unreported sales are a terms breach, not a saving")
    if not rep.get("tokenless_coverage_measured"): f.append("EP-3 token-less transactions (unsupported iOS, missing entitlement, user declined) are not surfaced and measured - the silent coverage hole is exactly where unreportable revenue accumulates")
    if not rep.get("server_verifies_before_granting"): f.append("EP-3 the server does not verify the web purchase (billing provider / RevenueCat record) before granting the entitlement - trusting a return deep-link alone grants premium to anyone who crafts the link")
    mea=d.get("measurement") or {}
    if not mea.get("funnel_per_storefront_measured"): f.append("EP-4 the link-tap -> checkout -> purchase funnel is not measured per storefront/regime (a US 0% regime and an EU 15% regime averaged together hide which one loses money)")
    if not mea.get("net_revenue_after_all_fees_measured"): f.append("EP-4 net revenue after ALL fees (Apple commission for the regime + processor + refunds/chargebacks/tax load) is not measured against IAP net - gross web revenue overstates the saving by exactly the costs the developer took over from Apple")
    ver=d.get("verification") or {}
    if not ver.get("storefront_matrix_e2e"): f.append("EP-5 the storefront matrix is not end-to-end verified (eligible regime presents and completes; ineligible storefront never sees the option; IAP still completes everywhere) - a single-storefront manual test cannot exercise a regime-gated surface")
    if not ver.get("unit_tests_disclosure_token_fallback"): f.append("EP-5 disclosure presentation, token minting/failure fallback and eligibility gating are not unit-tested (token failure must not block or silently misreport checkout)")
    if not ver.get("debug_link_guarded"): f.append("EP-5 a debug/test path that forces the external-purchase option is not confined to debug builds or is unrecorded (an override reaching release, screenshots or E2E recordings offers a checkout the audience's regime may not allow)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
