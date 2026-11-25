#!/usr/bin/env python3
"""quiet-check: deterministic gate for the Quiet Delivery stack
(per-app presentation settings -> provisional/ephemeral status honesty ->
quiet-state derivation -> diagnosis/recovery -> measurement), for an app
whose product is a timely nudge. Stdlib only, offline, free.
Sources (read 2026-11-15):
- OneSignal iOS provisional push documentation: provisional (direct-to-
  history) notifications are delivered silently to Notification Center
  only -- no banner, no sound, no lock-screen alert; the person's Keep...
  choice offers Deliver Quietly (stays Center-only) or Turn Off.
- Use Your Loaf, "Provisional Authorization of User Notifications":
  requesting .provisional shows no prompt and notifications are delivered
  quietly; in detailed settings alerts are restricted to Notification
  Centre and badges may not be granted even if requested; full alert
  permission exists only if the person changes notification settings.
- UNNotificationSettings (Apple UserNotifications, via Microsoft Learn
  API listing and practitioner guides read 2026-11-15): the settings
  object carries the per-channel presentation state -- alertSetting,
  alertStyle, lockScreenSetting, notificationCenterSetting, soundSetting,
  badgeSetting, scheduledDeliverySetting -- separately from
  authorizationStatus. A person who chose Deliver Quietly (long-press a
  notification > Manage > Deliver Quietly, or Settings toggles) keeps
  authorizationStatus == .authorized while lock screen and banners are
  off: status alone cannot see quiet delivery.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, assumed_channels_listed, decision_recorded},
 status_honesty:{provisional_not_counted_as_alert_authorized,
   ephemeral_not_counted_as_alert_authorized,
   alerts_allowed_derived_from_presentation_not_status_alone},
 presentation:{presentation_settings_reread, quiet_state_derived_center_only,
   reread_on_activation_or_settings},
 recovery:{onboarding_explains_quiet_delivery,
   settings_flow_diagnoses_channel_and_routes_to_notification_settings,
   in_app_fallback_when_quiet},
 provisional:{provisional_use_is_deliberate_decision,
   promotion_path_if_provisional},
 measurement:{event_defined, event_fired, quiet_share_counted,
   outcome_joinable_by_quiet}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("QD-0 the Quiet Delivery surface is not inventoried (which presentation channels the product assumes -- banner, lock screen, Notification Center, sound -- and what happens to a nudge when only the Center is on, are nowhere recorded; an unrecorded surface cannot be audited)")
    if not inv.get("assumed_channels_listed"):
        fails.append("QD-0 the channels the product assumes are not listed (a timely nudge silently assumes lock screen + banner at its moment; if that assumption is not written down, its failure mode -- history-only delivery -- is invisible by design)")
    if not inv.get("decision_recorded"):
        fails.append("QD-0 no recorded decision exists for quiet behaviour (the honest states are 'we detect center-only delivery, explain it, fall back in-app, and count it' or an explicit recorded choice not to -- silence is not a state)")
    sh = d.get("status_honesty") or {}
    if not sh.get("provisional_not_counted_as_alert_authorized"):
        fails.append("QD-1 provisional authorization is counted as alert authorization (provisional notifications are delivered quietly to Notification Center only -- no banner, no sound, no lock-screen alert; a helper named or used as 'authorized for alerts' that returns true for .provisional misclassifies the quietest delivery state as the loudest)")
    if not sh.get("ephemeral_not_counted_as_alert_authorized"):
        fails.append("QD-1 ephemeral authorization is counted as alert authorization (.ephemeral is the App Clip temporary state, also without prominent presentation; counting it as alert-authorized inflates the reachable denominator with sessions that cannot receive a prominent nudge)")
    if not sh.get("alerts_allowed_derived_from_presentation_not_status_alone"):
        fails.append("QD-1 'alerts allowed' is derived from authorizationStatus alone (a person who chose Deliver Quietly keeps status .authorized while lock screen and banners are off; status-only derivation reports such a person as fully reachable while every nudge lands silently in history)")
    pr = d.get("presentation") or {}
    if not pr.get("presentation_settings_reread"):
        fails.append("QD-2 the per-channel presentation settings are never re-read (UNNotificationSettings carries alertSetting, alertStyle, lockScreenSetting, notificationCenterSetting and soundSetting separately from authorizationStatus; reading only the status discards the only client-side signal of how notifications actually present)")
    if not pr.get("quiet_state_derived_center_only"):
        fails.append("QD-2 no quiet state is derived (center enabled while lock screen and alert presentation are disabled is the Deliver Quietly signature; without deriving it, the app cannot distinguish a delivered nudge from a warehoused one)")
    if not pr.get("reread_on_activation_or_settings"):
        fails.append("QD-2 presentation settings are not re-read on activation or in the settings flow (people change delivery to quiet from the notification itself or from system Settings, outside the app; a value read once at onboarding is stale exactly when it matters)")
    rc = d.get("recovery") or {}
    if not rc.get("onboarding_explains_quiet_delivery"):
        fails.append("QD-3 onboarding never explains quiet delivery (the system lets a person move the app to Center-only delivery at any time, including from the first notification's Manage menu; an app whose value is timing that never says what quiet delivery does to its nudges leaves the most consequential delivery choice unexplained)")
    if not rc.get("settings_flow_diagnoses_channel_and_routes_to_notification_settings"):
        fails.append("QD-3 the settings flow does not diagnose which channel is off or route to the notification settings (opening the generic app-settings page without saying 'Lock Screen and Banners are off, Notification Center is on' makes the person hunt for a switch the app already could have read; the notification-specific settings route exists for exactly this)")
    if not rc.get("in_app_fallback_when_quiet"):
        fails.append("QD-3 there is no in-app fallback keyed to the quiet state (if nudges arrive only in history, opening the app must still surface the moment's words at their moment; a fallback that is not keyed to the detected quiet state does not fire for the people who need it)")
    pv = d.get("provisional") or {}
    if not pv.get("provisional_use_is_deliberate_decision"):
        fails.append("QD-4 provisional use is not a deliberate recorded decision (either the app requests .provisional on purpose as a trial with a promotion plan, or it does not request it and does not silently accept the status as full authorization; accepting a status the app never chose, as if it were chosen, is drift)")
    if not pv.get("promotion_path_if_provisional"):
        fails.append("QD-4 there is no promotion path out of provisional/quiet (a person trialling notifications quietly must have a designed moment -- after value is felt -- where prominent delivery is explained and requested; without it the trial state is the permanent state and the moment-bound product never arrives prominently)")
    ms = d.get("measurement") or {}
    if not ms.get("event_defined"):
        fails.append("QD-5 no quiet-delivery measurement event exists at all (the presentation vector or a derived quiet flag at permission/send/open time is unrecorded; whether quiet delivery is eating the intervention is a matter of opinion)")
    elif not ms.get("event_fired"):
        fails.append("QD-5 the quiet event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'delivery is prominent' forever, indistinguishable from the truth)")
    if not ms.get("quiet_share_counted"):
        fails.append("QD-5 the quiet share is not counted (center-only or provisional among authorized users is the surface's exposure denominator; without it a silent-delivery problem cannot be sized)")
    if not ms.get("outcome_joinable_by_quiet"):
        fails.append("QD-5 outcome cannot be joined by quiet versus prominent delivery (opened/responded split by quiet state), so whether history-only delivery costs the response the nudge exists to produce is unknowable")
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
