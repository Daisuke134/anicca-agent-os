#!/usr/bin/env python3
"""store-origin-check: deterministic gate for purchases that start
OUTSIDE the in-app paywall (App Store promoted IAP, win-back offers,
offer codes, signed promotional offers). Stdlib only, offline, free.
Sources (read in full 2026-11-15):
- RevenueCat, "iOS Subscription Offers"
  (www-docs.revenuecat.com/docs/subscription-guidance/
  subscription-offers/ios-subscription-offers): offer types and their
  mechanics -- introductory (eligibility checkable), promotional
  (signed; getPromotionalOffer + purchase(package:promotionalOffer:)),
  offer codes (presentCodeRedemptionSheet since SDK 3.8.0, or the
  apps.apple.com/redeem link + syncPurchases on return; no success
  callback, so receivedUpdated/listener must pick the transaction up),
  win-back (iOS 18+; Streamlined Purchasing on by default; with it
  disabled the SDK calls readyForPromotedProduct and the app must do
  its pre-purchase actions and only then call startPurchase;
  StoreKit messages auto-present the win-back sheet unless
  showStoreMessagesAutomatically=false in SDK 5.6.0+, in which case
  showStoreMessages() must be called manually; RC recommends deferring
  until after an entitlement check so an entitled subscriber is not
  double-sold; paywall redemption needs SDK 5.10.0+).
- RevenueCat community / SDK guidance on promoted purchases: if the
  app cannot purchase at the moment the delegate fires (e.g. user has
  not signed in), cache the startPurchase/deferment block and call it
  when the app is ready.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{channels_recorded, asc_config_evidenced,
   sdk_version_supports},
 entry:{delegate_registered_at_configure, promoted_callback_present,
   transaction_updates_observed},
 readiness:{readiness_checked_before_start,
   completion_handles_all_outcomes, completion_syncs_server},
 winback:{store_messages_timing_decided,
   winback_paywall_or_link_path, winback_not_shown_to_entitled},
 offer_codes:{redemption_sheet_or_link_present,
   return_triggers_sync},
 measurement:{store_originated_outcomes_counted,
   promotional_offer_path_decided}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("channels_recorded"):
        fails.append("SO-0 the store-originated channels are not recorded as decided (promoted IAP / win-back / offer codes / signed promotional offers / intro eligibility each need an explicit use-or-not-use decision; an unrecorded channel is a channel nobody owns)")
    if not inv.get("asc_config_evidenced"):
        fails.append("SO-0 the App Store Connect side is not evidenced (which offers exist, the in-app purchase key uploaded to RevenueCat, and the Streamlined Purchasing setting are half of every store-originated flow; client code alone cannot show they exist)")
    if not inv.get("sdk_version_supports"):
        fails.append("SO-0 the purchases SDK version does not support the current store-originated surface (win-back paywall redemption needs SDK 5.10.0+, deferred StoreKit messages 5.6.0+, streamlined-off win-back 5.9.0+)")
    en = d.get("entry") or {}
    if not en.get("delegate_registered_at_configure"):
        fails.append("SO-1 the purchases delegate is not registered at configure time (a promoted or streamlined-off win-back purchase that arrives before the delegate exists has nowhere to land)")
    if not en.get("promoted_callback_present"):
        fails.append("SO-1 no readyForPromotedProduct callback (with Streamlined Purchasing disabled, or for App Store promoted IAP, this delegate is the only door from the store into the app)")
    if not en.get("transaction_updates_observed"):
        fails.append("SO-1 transaction/CustomerInfo updates are not observed continuously (offer-code redemption has no success callback at all; the listener/delegate picking up the new transaction is the whole completion path)")
    re_ = d.get("readiness") or {}
    if not re_.get("readiness_checked_before_start"):
        fails.append("SO-2 the promoted startPurchase block is fired immediately and unconditionally (RevenueCat's contract: do the pre-purchase actions first -- sign-in state, configuration finished, not already entitled, no purchase already in flight -- cache the block and call it when ready; firing it during onboarding or before configure completes spends the user's one store intent on the wrong moment)")
    if not re_.get("completion_handles_all_outcomes"):
        fails.append("SO-2 the promoted completion does not distinguish success / error / cancellation (ignoring the error and cancelled parameters makes a failed store-originated purchase indistinguishable from a successful one, in the UI and in the record)")
    if not re_.get("completion_syncs_server"):
        fails.append("SO-2 a completed store-originated purchase does not trigger the server-side entitlement sync (the client knowing is not the server knowing; server-gated delivery keeps treating the payer as free until a sync lands)")
    wb = d.get("winback") or {}
    if not wb.get("store_messages_timing_decided"):
        fails.append("SO-3 the StoreKit message timing is not decided (with the default, the win-back sheet auto-presents whenever StoreKit sends it -- including over onboarding or a first-run moment; deferring with showStoreMessagesAutomatically=false plus an explicit showStoreMessages() call site is a decision that must be made, not inherited)")
    if not wb.get("winback_paywall_or_link_path"):
        fails.append("SO-3 there is no in-app win-back redemption path (no eligibleWinBackOffers on the paywall and no win-back URL handling; a lapsed subscriber who returns to the app -- the highest-intent return there is -- meets a full-price paywall)")
    if not wb.get("winback_not_shown_to_entitled"):
        fails.append("SO-3 nothing stops the win-back sheet being shown to an already-entitled subscriber (RevenueCat recommends checking entitlements before displaying, to avoid selling a second win-back to someone who already has one)")
    oc = d.get("offer_codes") or {}
    if not oc.get("redemption_sheet_or_link_present"):
        fails.append("SO-4 there is no offer-code redemption entry (no presentCodeRedemptionSheet and no apps.apple.com/redeem link; a code sent by a campaign, a partner or support is a dead letter -- the user has nowhere in the product to spend it)")
    if not oc.get("return_triggers_sync"):
        fails.append("SO-4 returning from an out-of-app redemption does not trigger syncPurchases (RevenueCat's documented requirement for the redeem-link path; without it the payer returns to an app that still shows them as free until some unrelated refresh)")
    me = d.get("measurement") or {}
    if not me.get("promotional_offer_path_decided"):
        fails.append("SO-5 the signed promotional-offer purchase path is not decided (getPromotionalOffer + purchase(package:promotionalOffer:) is how existing/lapsed subscribers are given a priced reason to stay or return inside the app; a retention sheet that only re-sells a regular package is not this path, and 'not used' must be a recorded decision)")
    if not me.get("store_originated_outcomes_counted"):
        fails.append("SO-5 store-originated purchase outcomes are not counted split by channel (promoted / win-back / offer code / promotional: starts and results; uncounted channels cannot be told apart from broken ones)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: store_origin_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"app: {d.get('app','?')}")
    if fails:
        print(f"FAIL ({len(fails)})")
        for x in fails:
            print(f" - {x}")
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
