#!/usr/bin/env python3
"""intro-eligibility-check: deterministic gate for the INTRODUCTORY OFFER
ELIGIBILITY surface (free-trial / intro-price honesty). Stdlib only,
offline, free.
Sources:
- Apple (App Store Connect Help / StoreKit): an introductory offer may be
  redeemed only ONCE per subscription group per Apple Account. New
  subscribers are always eligible; returning subscribers are eligible only
  if they never redeemed an intro offer in the group; current subscribers
  are never eligible, including on upgrade/downgrade/crossgrade. Check
  eligibility (StoreKit isEligibleForIntroOffer, per group) before
  rendering trial copy. The offer existing on a product says nothing
  about whether THIS user may claim it.
- RevenueCat Codelabs "Check Free Trial & Intro Price Eligibility":
  call checkTrialOrIntroDiscountEligibility(productIdentifiers:) for every
  product on the paywall and read IntroEligibilityStatus per product.
  Show free-trial copy ONLY when .eligible; .ineligible and
  .noIntroOfferExists show standard pricing; .unknown is neutral copy
  plus a RE-CHECK once the SDK has the data (receipt/history available).
  Treating a non-nil introductoryDiscount as eligibility shows
  "Start Free Trial" to users who will be charged full price immediately.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("presentation_decision_recorded"): f.append("IO-0 how trial presentation follows eligibility status is not recorded as a decision (eligible / ineligible / no-offer / unknown each need a decided presentation, in code or in a spec - drift is not a decision)")
    if not dec.get("owner_recorded"): f.append("IO-0 no single intro-eligibility owner is recorded")
    if not dec.get("group_structure_recorded"): f.append("IO-0 the subscription-group structure is not recorded (eligibility is per GROUP, not per product: if weekly and annual share one group, a trial on either burns the trial on both - an unrecorded group structure makes every per-product display a guess)")
    if not dec.get("asc_intro_config_verified"): f.append("IO-0 the App Store Connect introductory-offer configuration is not verified (which products carry a free-trial intro offer, its period, and its eligibility setting - read from ASC, not assumed from the offering payload)")
    chk=d.get("check") or {}
    if not chk.get("checks_all_paywall_products"): f.append("IO-1 eligibility is not checked for every product displayed on the paywall (an unchecked product falls back to offer-existence copy, which promises a trial to users who already used theirs)")
    if not chk.get("trial_copy_only_when_eligible"): f.append("IO-1 trial language (duration text, trial timeline, trial disclosure) is not gated on status == eligible (offer existence - introductoryDiscount != nil - is not eligibility)")
    if not chk.get("cta_only_when_eligible"): f.append("IO-1 the trial call-to-action is not gated on status == eligible (a 'Start free trial' button shown to an ineligible user is a promise the store will not honor: they are charged full price immediately)")
    st=d.get("states") or {}
    if not st.get("ineligible_shows_standard"): f.append("IO-2 ineligible / no-intro-offer users do not get clean standard-pricing presentation (trial language must disappear entirely, including the disclosure footnote - a footnote trial mention under a standard CTA is still a promise)")
    if not st.get("unknown_shows_neutral_only"): f.append("IO-2 the unknown status does not fall back to neutral / conditional copy only (unknown must never render as a trial promise; RevenueCat: do not assume eligibility, use neutral copy)")
    if not st.get("unknown_triggers_recheck"): f.append("IO-2 an unknown result does not trigger a re-check once the data the SDK needs becomes available (receipt / CustomerInfo refresh, restore, foreground) - on a fresh install the first check commonly returns unknown, so without a re-check the paywall is stuck in its fallback for the whole session)")
    care=d.get("ineligible_care") or {}
    if not care.get("ineligible_treatment_decided"): f.append("IO-3 the ineligible segment has no decided treatment (they silently lose the trial with no explanation copy, no alternative offer, and no recorded decision to show standard pricing only - the highest-intent returning users meet an unexplained price jump)")
    if not care.get("external_promises_match"): f.append("IO-3 external trial promises (store page, screenshots, ads, social posts) are not verified against eligibility reality (an unconditional '3 days free' outside the app is false for every returning user who already redeemed - outside and inside must be the same offer)")
    mea=d.get("measurement") or {}
    if not mea.get("status_logged_per_view"): f.append("IO-4 the eligibility status is not emitted with paywall views / purchase attempts (the funnel cannot be split into eligible / ineligible / unknown, so a conversion problem in one segment is invisible in the blended rate)")
    if not mea.get("purchase_flag_reflects_eligibility"): f.append("IO-4 the purchase / funnel trial flag reflects offer existence instead of this user's eligibility or the actual trial start (has_trial = introductoryDiscount != nil labels ineligible full-price purchases as trial starts and corrupts every downstream trial metric)")
    if not mea.get("unknown_rate_measured"): f.append("IO-4 the unknown-status rate is not measured (unknown is the silent failure mode of this surface: if it spikes, eligible users stop seeing the trial and nobody knows)")
    ver=d.get("verification") or {}
    if not ver.get("unit_tests_all_statuses"): f.append("IO-5 the presentation resolution is not unit-tested for all four statuses (eligible / ineligible / no-offer / unknown, plus the no-trial product case)")
    if not ver.get("sandbox_trialed_account_e2e"): f.append("IO-5 the already-trialed-account case is not end-to-end verified in sandbox (the ineligible path is exactly the one manual testing with fresh accounts never exercises)")
    if not ver.get("debug_override_guarded"): f.append("IO-5 a debug / test override that forces eligible presentation is not confined to debug builds or is unrecorded (an override that reaches release, screenshots or E2E recordings shows a trial the audience cannot get)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
