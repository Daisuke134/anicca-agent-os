#!/usr/bin/env python3
"""screentime-check: deterministic gate for the iOS Screen Time API stack
(FamilyControls / ManagedSettings / DeviceActivity) used as a
temptation-moment shield. Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple WWDC21, Meet the Screen Time API
  https://nonstrict.eu/wwdcindex/wwdc2021/10123/
  Three frameworks: FamilyControls (authorization + privacy; the picker
  returns opaque tokens -- nobody outside the device learns which apps
  or sites were selected), ManagedSettings (the restrictions themselves,
  including shielding applications with the app's own branding),
  DeviceActivity (schedules and usage events call a monitor extension
  at window start/end and at thresholds, without launching the app).
- Emrld Labs, Family Controls Screen Time API: iOS Focus App Guide
  https://emrldlabs.com/blog/screen-time-family-controls-focus-app-privacy-first/
  The com.apple.developer.family-controls entitlement is required, and
  for App Store distribution Apple must manually approve it (a human
  reviews the request before you can ship). Authorization and shielding
  cannot be tested in the Simulator -- a real device is required. The
  selection comes back as applicationTokens / categoryTokens /
  webDomainTokens with no readable identity: you cannot log which apps
  someone blocked, because you were never handed that information.
  ManagedSettingsStore.shield is what actually blocks; a
  ShieldConfiguration extension customizes the shield screen (copy,
  color, button).
- Marcus Taylor, iOS Screen Time API: Fixing Shields, Timers and
  Permissions (production postmortem)
  https://www.marcustaylor.org/blog/ios-screen-time-timed-access
  Authorization via AuthorizationCenter.requestAuthorization(for:
  .individual); selection saved to the shared App Group so host app and
  extensions agree; shield buttons handled by ShieldActionDelegate;
  DeviceActivityMonitor callbacks restore/clear restrictions while the
  host app is backgrounded; DeviceActivity has a fifteen-minute minimum
  monitoring interval, which constrains timed-pass designs.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, temptation_problems_named,
   problems:[...]},
 authorization:{entitlement_present,
   distribution_entitlement_request_planned,
   authorization_requested_for_individual,
   requested_at_value_moment_not_launch,
   denial_handled_without_false_claims},
 selection_monitoring:{picker_used, selection_persisted_in_app_group,
   schedule_registered, monitor_extension_exists,
   monitor_applies_and_clears_shield},
 shield:{shield_applied_via_managed_settings,
   shield_configuration_customized, shield_shows_persons_own_words,
   primary_action_opens_app, secondary_action_lets_person_proceed,
   shield_clears_at_window_end},
 honesty:{user_chose_apps_and_windows, can_disable_anytime,
   no_permanent_lockout, no_claim_of_blocking_without_shield,
   selection_tokens_never_logged_as_app_names},
 measurement:{event_defined, event_fired, shield_shown_counted,
   proceed_rate_counted, joinable_to_outcome}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("ST-0 the Screen Time shield state is not inventoried (which temptation-moment problems exist, what is declared, and what actually runs today are nowhere recorded; an unrecorded surface cannot be audited)")
    if not inv.get("temptation_problems_named"):
        fails.append("ST-0 no temptation-moment problem is named (a shield is justified only by a problem whose moment is an action -- opening an app, acting on an urge; with no such problem named, the honest decision may be not to build it, but that decision must be recorded, not drifted into)")
    auth = d.get("authorization") or {}
    if not auth.get("entitlement_present"):
        fails.append("ST-1 the Family Controls entitlement (com.apple.developer.family-controls) is absent from every entitlements file, so no code path in this app can ever request Screen Time authorization or shield anything")
    if auth.get("entitlement_present") and not auth.get("distribution_entitlement_request_planned"):
        warns.append("ST-1 the entitlement is present for development but no distribution-entitlement request to Apple is planned (distribution requires Apple's manual approval; discovering that at submission time strands the feature)")
    if not auth.get("authorization_requested_for_individual"):
        fails.append("ST-1 AuthorizationCenter.requestAuthorization(for: .individual) is never called (without the person's own authorization the whole stack is inert; for an own-device habit product .individual is the applicable mode)")
    if auth.get("authorization_requested_for_individual") and not auth.get("requested_at_value_moment_not_launch"):
        fails.append("ST-1 authorization is requested at launch or in a settings corner, not at the value moment (the person must be standing in the problem they chose -- e.g. setting up their late-night window -- when the system asks; a launch-time ask reads as surveillance and is denied)")
    if not auth.get("denial_handled_without_false_claims"):
        fails.append("ST-1 denial is not handled honestly (when authorization is denied the app must keep working with notifications only and must never describe itself as blocking or protecting; an unhandled denial either crashes the flow or silently upgrades the claim)")
    sel = d.get("selection_monitoring") or {}
    if not sel.get("picker_used"):
        fails.append("ST-2 the system FamilyActivityPicker is never presented (the person must choose the apps/categories themselves in Apple's picker; an app that picks for them -- or hardcodes a list -- violates both the API's privacy design and the person's authorship of the intervention)")
    if not sel.get("selection_persisted_in_app_group"):
        fails.append("ST-2 the selection is not persisted to the shared App Group (host app, monitor extension, and shield extensions are separate processes; a selection that lives only in the host app is invisible to the extensions that must enforce it)")
    if not sel.get("schedule_registered"):
        fails.append("ST-2 no DeviceActivity schedule is registered (without a schedule nothing turns the shield on or off at the person's chosen windows; a shield that depends on the app being opened is a shield that is off exactly when it matters)")
    if not sel.get("monitor_extension_exists"):
        fails.append("ST-2 no DeviceActivityMonitor extension exists (window start/end and threshold callbacks are delivered to the monitor extension, not the app; without the extension the schedule fires into nothing)")
    if not sel.get("monitor_applies_and_clears_shield"):
        fails.append("ST-2 the monitor does not apply and clear the ManagedSettings shield at window boundaries (applying without clearing is a permanent lockout; clearing without applying is a notification with extra steps)")
    sh = d.get("shield") or {}
    applied = bool(sh.get("shield_applied_via_managed_settings"))
    if not applied:
        fails.append("ST-3 no ManagedSettings shield is ever applied (ManagedSettingsStore.shield is the only mechanism that actually interrupts opening a chosen app; everything else -- notifications, widgets, in-app screens -- is advice the moment can ignore)")
    if applied and not sh.get("shield_configuration_customized"):
        fails.append("ST-3 the shield uses Apple's default configuration (the shield screen is the intervention surface; a generic system screen carries none of the person's context and reads as punishment rather than help)")
    if applied and not sh.get("shield_shows_persons_own_words"):
        fails.append("ST-3 the shield does not show the person's own words (the affirmation or reason the person chose for this problem is the content that makes the interruption an intervention; generic copy on the shield is a lock screen, not a nudge)")
    if applied and not sh.get("primary_action_opens_app"):
        fails.append("ST-3 the shield's primary action does not open the app at the promised place (the shield's button is the conversion point of the whole surface; it must land on the session/screen for this problem, not the app root)")
    if applied and not sh.get("secondary_action_lets_person_proceed"):
        fails.append("ST-3 the shield gives the person no way to proceed (a shield with no exit is a lockout: the person who genuinely needs the app is punished, learns to disable the feature entirely, and the design copies the punitive shape -- not the helpful one)")
    if applied and not sh.get("shield_clears_at_window_end"):
        fails.append("ST-3 the shield does not clear when the person's chosen window ends (restrictions that outlive their window are experienced as the app taking the phone hostage)")
    hon = d.get("honesty") or {}
    if not hon.get("no_claim_of_blocking_without_shield"):
        fails.append("ST-4 the product claims blocking/protection it does not implement (copy that says 'we block distracting apps' while only sending notifications is a false capability claim; what is shown outside must exist inside)")
    if applied and not hon.get("user_chose_apps_and_windows"):
        fails.append("ST-4 the shielded apps or windows were not chosen by the person (shielding imposed by the app's defaults rather than the person's own picker selection and schedule converts help into control)")
    if applied and not hon.get("can_disable_anytime"):
        fails.append("ST-4 the person cannot disable the shield at any time from inside the app (an intervention the person cannot switch off owns them; revocability is what keeps this a tool)")
    if not hon.get("no_permanent_lockout"):
        fails.append("ST-4 a permanent or punitive lockout exists (no window end, no proceed path, or a penalty for proceeding; reported dark-pattern lock-ins are a store-removal risk and are never copied)")
    if not hon.get("selection_tokens_never_logged_as_app_names"):
        fails.append("ST-4 selected apps are logged or reported as names (the picker returns opaque tokens by design -- the app never learns which apps were chosen; any analytics field claiming app names from a selection is fabricated data)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("ST-5 the shield measurement event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'the shield works' forever, indistinguishable from the truth)")
    if not ms.get("event_defined"):
        fails.append("ST-5 no shield measurement event exists at all (shield applied/shown/proceeded are unknowable in principle; note the event can only carry tokens/counts, never app names)")
    if applied and not ms.get("shield_shown_counted"):
        fails.append("ST-5 shield impressions are not counted (the denominator of the whole surface -- how many temptation moments were actually interrupted -- is missing)")
    if applied and not ms.get("proceed_rate_counted"):
        fails.append("ST-5 the proceed rate is not counted (proceeding after seeing one's own words is the surface's core behavioural read: near-100% means the shield is wallpaper, near-0% with disables rising means it is a punishment)")
    if not ms.get("joinable_to_outcome"):
        fails.append("ST-5 shield events cannot be joined to outcome (shield shown -> proceeded or turned away -> that night's problem-nudge result), so whether the interruption earns its intrusiveness is a matter of opinion")
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
