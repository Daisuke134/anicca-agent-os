#!/usr/bin/env python3
"""restore-check: deterministic gate for the Restore Purchases surface.
Stdlib only, offline, free.
Sources (read 2026-11-15):
- RevenueCat Codelabs, "Restore Purchases on iOS" (official,
  revenuecat.github.io/codelabs/restore-purchases-ios.html): Apple's
  App Store Review Guidelines 3.1.1 require any app with in-app
  purchases to include a way to restore them, or the app can be
  rejected. The official sample handles all three outcomes with a
  user-visible message: restored successfully / "No active purchases
  found. If you believe this is an error, please contact support." /
  failure with the error. It also warns: log the user in with
  logIn(appUserID) before restore when the app has its own auth, and
  never auto-restore on launch (restore only on an explicit tap;
  syncPurchases is the no-prompt sync path).
- RevenueCat staff guidance (community.revenuecat.com): the restore
  action "should live inside a Paywall or/and from your own (e.g
  Setting) app screen".
- RevenueCat Customer Center docs (www-docs.revenuecat.com/docs/
  tools/customer-center/customer-center-configuration): the default
  configuration includes a "Missing Purchases" path that restores
  past purchases, and the no-subscription management screen typically
  only offers restore. A dashboard-side configuration, so a linked
  CustomerCenterView only counts once the project configuration is
  verified to include that path.
- RevenueCat Restore Behavior docs (www-docs.revenuecat.com/docs/
  projects/restore-behavior): what happens when a receipt belongs to
  a different identified App User ID is decided by a dashboard
  dropdown (default: transfer to the new App User ID) that affects
  every app in the project -- a project-level decision that must be
  recorded, not an accident of the default.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{purchase_surfaces_recorded, restore_outcomes_defined,
   transfer_behavior_recorded},
 entry:{restore_on_paywall, restore_in_settings_direct,
   settings_restore_string_referenced},
 mechanism:{calls_restore_purchases, user_initiated_only,
   identity_login_linking_evidenced},
 outcomes:{success_advances_flow, no_entitlement_message_shown,
   failure_message_shown, cancellation_distinguished},
 customer_center:{customer_center_linked_in_settings,
   customer_center_restore_config_verified},
 measurement:{restore_started_counted, restore_result_counted,
   restore_results_connected_to_revenue}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("purchase_surfaces_recorded"):
        fails.append("RP-0 the purchase surfaces are not recorded (every surface that can sell -- each paywall entry point and Settings -- must be enumerated before restore coverage can be audited)")
    if not inv.get("restore_outcomes_defined"):
        fails.append("RP-0 the restore outcomes are not defined as a set (restored / nothing-to-restore / failed / cancelled are four different answers a person can get; an undefined outcome set means at least one of them has no designed result)")
    if not inv.get("transfer_behavior_recorded"):
        fails.append("RP-0 the RevenueCat restore/transfer behavior for receipts owned by another App User ID is not recorded (it is a dashboard decision affecting every app in the project; an unrecorded default is an unmade decision)")
    en = d.get("entry") or {}
    if not en.get("restore_on_paywall"):
        fails.append("RP-1 there is no restore action on the paywall (Guideline 3.1.1 requires a restore mechanism, and the paywall is where a returning payer looks for it first)")
    if not en.get("restore_in_settings_direct"):
        fails.append("RP-1 Settings offers no direct, labelled restore action (RevenueCat staff guidance: restore should live in the paywall and/or the app's own Settings screen; a restore that exists only inside a third-party management view, under a different name, is not findable by someone looking for the words 'Restore Purchases')")
    if not en.get("settings_restore_string_referenced"):
        fails.append("RP-1 the localized Settings restore string is not referenced by any code (translated 'Restore Purchases' copy in .strings with zero references is a label for a button that does not exist)")
    me = d.get("mechanism") or {}
    if not me.get("calls_restore_purchases"):
        fails.append("RP-2 the restore action never calls restorePurchases() (syncPurchases alone does not link the receipt to previous owners; the documented user-tapped restore is restorePurchases)")
    if not me.get("user_initiated_only"):
        fails.append("RP-2 restore is triggered without an explicit user tap (restorePurchases can raise OS sign-in prompts; calling it on launch shows a sign-in sheet to people who never asked to restore)")
    if not me.get("identity_login_linking_evidenced"):
        fails.append("RP-2 identity linking before restore is not evidenced (with the app's own auth, the documented order is logIn(appUserID) first so restored purchases attach to the signed-in customer, not to a stray anonymous ID)")
    ou = d.get("outcomes") or {}
    if not ou.get("success_advances_flow"):
        fails.append("RP-3 a successful restore does not advance the flow (restoring an active entitlement must unlock and move the person forward in the same action; a restore that only updates silent state strands a payer on the paywall)")
    if not ou.get("no_entitlement_message_shown"):
        fails.append("RP-3 the nothing-to-restore outcome shows the person nothing (the official sample answers it with a visible 'No active purchases found' message plus a support route; silence reads as a broken button and is the top restore complaint)")
    if not ou.get("failure_message_shown"):
        fails.append("RP-3 a failed restore shows no failure message (the person cannot tell a network failure from 'you own nothing'; the official sample surfaces the error)")
    if not ou.get("cancellation_distinguished"):
        fails.append("RP-3 a user cancellation is not distinguished from a failure (dismissing the OS sign-in prompt is not an error; showing a raw system error for it punishes the person for changing their mind)")
    cc = d.get("customer_center") or {}
    if not cc.get("customer_center_linked_in_settings"):
        fails.append("RP-4 Settings does not link the Customer Center (the self-serve management view is the documented home for missing-purchase recovery outside the paywall)")
    if not cc.get("customer_center_restore_config_verified"):
        fails.append("RP-4 the Customer Center configuration is not verified to include the Missing Purchases restore path (the path is in the default configuration, but the project configuration lives in the dashboard outside the source; an unverified config is an assumed restore path)")
    ms = d.get("measurement") or {}
    if not ms.get("restore_started_counted"):
        fails.append("RP-5 restore starts are not counted (without starts, the result counts have no denominator and a dead restore button is indistinguishable from an unused one)")
    if not ms.get("restore_result_counted"):
        fails.append("RP-5 restore results are not counted by outcome (restored / no-entitlement / failed must be separable, or the silent outcome can never be measured)")
    if not ms.get("restore_results_connected_to_revenue"):
        fails.append("RP-5 restore results are not connected to recovered revenue (restores are recovered payers; until restored entitlements are read next to subscription state, the surface's revenue value is invisible)")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
