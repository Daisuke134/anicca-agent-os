#!/usr/bin/env python3
"""alarmkit-check: deterministic gate for the WAKE / ALARM surface
(the one moment an affirmation app must break through Silent mode and
Focus: the wake-up alert for people whose stated problem is that they
cannot wake up -- AlarmKit on iOS 26+ -- plus the authorization,
scheduling, presentation, measurement and fallback contract around it).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple Developer Documentation "Scheduling an alarm with AlarmKit"
  (apple-docs mirror, updated 2026-11-15)
  https://apple-docs.everest.mt/docs/alarmkit/scheduling-an-alarm-with-alarmkit/
  An alarm is an alert that presents at a pre-determined time based on
  a schedule or after a countdown; it overrides both a device's focus
  and silent mode, if necessary. The app prompts people to authorize
  it by calling requestAuthorization() on AlarmManager; otherwise the
  first alarm triggers the request automatically, and without
  authorization an alarm "isn't scheduled and subsequently doesn't
  alert". The sample includes NSAlarmKitUsageDescription in Info.plist;
  if the key is missing or empty, apps can't schedule alarms with
  AlarmKit. Schedules are one-time or weekly (Alarm.Schedule, .fixed
  or .relative with .never / .weekly recurrence). Presentations cover
  Alert (title, stop button, optional secondary button whose behavior
  is .countdown = repeat after postAlert interval, or .custom = open
  app), plus optional Countdown and Paused states; attributes carry
  tintColor and metadata. Alarms are scheduled with a unique id via
  AlarmManager.schedule(id:configuration:), managed by that id
  (pause/cancel), and the app subscribes to alarmManager.alarmUpdates
  at initialization so it holds the latest state even when it was not
  running. A widget extension customizes the non-alerting Live
  Activity presentations (Dynamic Island, Lock Screen, StandBy).
- Apple WWDC25 session 230 "Wake up to the AlarmKit API" (WWDCNotes)
  https://wwdcnotes.com/documentation/wwdc25-230-wake-up-to-the-alarmkit-api/
  The alert breaks through silent mode and focus, therefore people
  must consent in a permission dialog; authorization can be requested
  manually or happens automatically on first creation, can be changed
  in Settings at any time, and is checked via
  AlarmManager.shared.authorizationState (.notDetermined /
  .authorized / .denied -- when denied, inform the person the alarm
  is not authorized). A fixed schedule is an absolute date that does
  not react to timezone changes; use a relative schedule to account
  for timezone changes (wall-clock wake time). Custom sound is
  possible via AlertSound.named; the file must be in the app's main
  bundle or the Library Sounds folder in the app container. Alarms
  are best for things like a cooking timer or a wake-up alarm; they
  are NOT a replacement for critical alerts or time-sensitive
  notifications.
Note on setup claims: some secondary guides claim a special
AlarmKit entitlement (com.apple.developer.alarmkit) must be requested
from Apple. Neither Apple source above documents such an entitlement,
and a current maintained iOS skill registry entry explicitly warns
not to require com.apple.developer.alarmkit unless a current Apple
source documents it. This gate therefore does NOT require any
entitlement; it requires the documented pieces only (usage
description, authorization, schedule, presentation, updates).
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{decision_recorded, surfaces_enumerated,
   availability_fact_recorded, not_a_notification_replacement_recorded},
 setup:{usage_description_present_nonempty,
   no_unsupported_entitlement_required,
   live_activity_foundation_for_countdown},
 authorization:{state_checked_before_schedule,
   request_at_value_moment_or_first_schedule,
   denied_shows_not_scheduled_and_recovery,
   alarm_permission_tracked_separately_from_notification},
 scheduling:{manager_schedule_used, stable_ids_per_slot,
   relative_wallclock_schedule_for_daily_wake,
   alarm_updates_observed, rescheduled_on_wake_time_or_problem_change},
 presentation:{alert_presentation_with_stop_and_secondary,
   sound_bundled_and_referenced, tint_and_metadata_identify_app},
 measurement:{scheduled_and_authorization_measured,
   fired_and_open_measured, fallback_for_denied_and_older_ios,
   wake_outcome_joined_to_cohort}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("decision_recorded"):
        fails.append("AK-0 no wake-channel decision is recorded (AlarmKit system alarm, local notification, remote push only, or a deliberate mix per surface -- an unrecorded channel means the wake moment inherits whatever the last migration left behind)")
    if not inv.get("surfaces_enumerated"):
        fails.append("AK-0 the wake surfaces are not enumerated (the cant_wake_up wake alert is an alarm surface; the other problem nudges are notification surfaces -- a surface nobody enumerated gets whichever channel happens to be wired, not the one its moment needs)")
    if not inv.get("availability_fact_recorded"):
        fails.append("AK-0 the availability fact is not recorded: AlarmKit requires iOS 26+, so on a deployment target below 26 every wake path needs an availability gate and a defined older-iOS behaviour -- unrecorded, the feature silently exists for nobody below the newest OS")
    if not inv.get("not_a_notification_replacement_recorded"):
        fails.append("AK-0 the boundary is not recorded: Apple states alarms are not a replacement for critical alerts or time-sensitive notifications -- without the boundary on record, an alarm adoption either swallows the notification surfaces or is dismissed as one")
    st = d.get("setup") or {}
    if not st.get("usage_description_present_nonempty"):
        fails.append("AK-1 NSAlarmKitUsageDescription is missing or empty (Apple: if the key is missing or its value is an empty string, apps can't schedule alarms with AlarmKit -- the one documented setup piece, absent, disables the whole surface with no error worth reading)")
    if not st.get("no_unsupported_entitlement_required"):
        fails.append("AK-1 the design requires an entitlement no current Apple source documents (com.apple.developer.alarmkit appears in secondary guides only; gating the surface on an undocumented entitlement stalls it behind a request Apple never asked for)")
    if not st.get("live_activity_foundation_for_countdown"):
        fails.append("AK-1 the Live Activity foundation for the countdown/paused presentations is missing (AlarmKit's non-alerting presentations are a Live Activity customized by a widget extension with NSSupportsLiveActivities; without the foundation the countdown state has no surface)")
    au = d.get("authorization") or {}
    if not au.get("state_checked_before_schedule"):
        fails.append("AK-2 authorizationState is not checked before scheduling (AlarmManager.shared.authorizationState is .notDetermined / .authorized / .denied; scheduling blind means the app believes a wake alarm exists in exactly the denied state where Apple says it is not scheduled and does not alert)")
    if not au.get("request_at_value_moment_or_first_schedule"):
        fails.append("AK-2 authorization is never requested at the value moment or on first schedule (the consent dialog is the price of breaking through Silent and Focus; a surface that never asks can never fire, and a first-schedule automatic prompt with no explanation converts worst)")
    if not au.get("denied_shows_not_scheduled_and_recovery"):
        fails.append("AK-2 a denied authorization does not produce an explicit 'your wake alarm will not ring' state with a recovery path (Apple's sample guidance: if authorization is not granted the alarm isn't scheduled; the person can change it in Settings at any time -- silence here is a wake-up that fails on the morning it mattered)")
    if not au.get("alarm_permission_tracked_separately_from_notification"):
        fails.append("AK-2 the alarm permission is not tracked separately from the notification permission (they are two systems with two prompts and two Settings locations; a dashboard that shows one 'permission granted' number cannot tell a muted notification from an unscheduled alarm)")
    sc = d.get("scheduling") or {}
    if not sc.get("manager_schedule_used"):
        fails.append("AK-3 no alarm is scheduled through AlarmManager.schedule(id:configuration:) (a wake alert delivered as an ordinary notification follows Focus and Silent rules; the system-alarm path is the only one Apple documents as overriding both)")
    if not sc.get("stable_ids_per_slot"):
        fails.append("AK-3 alarms do not carry stable unique ids per wake slot (AlarmKit manages alarms by id -- pause, cancel, update; id-less or random-per-launch scheduling duplicates alarms and makes the wake time unchangeable)")
    if not sc.get("relative_wallclock_schedule_for_daily_wake"):
        fails.append("AK-3 the daily wake does not use a relative (wall-clock) schedule (Apple: a fixed schedule is an absolute date that doesn't react to timezone changes; a wake alarm pinned to an absolute date fires at the wrong local hour after travel, and a one-shot fixed alarm never fires again tomorrow)")
    if not sc.get("alarm_updates_observed"):
        fails.append("AK-3 alarmUpdates is not observed (the app must hold the latest alarm state even when changes happen while it isn't running -- snoozed, stopped, or cancelled from the system UI; unobserved, the app's own screens lie about whether a wake alarm exists)")
    if not sc.get("rescheduled_on_wake_time_or_problem_change"):
        fails.append("AK-3 changing the wake time (or the person's problems) does not reschedule the alarm (the onboarding collects a wake time and the profile can change; an alarm frozen at the first value is a promise kept to a schedule the person already left)")
    pr = d.get("presentation") or {}
    if not pr.get("alert_presentation_with_stop_and_secondary"):
        fails.append("AK-4 the alert presentation lacks the stop button and a secondary action (AlarmPresentation.Alert carries a title, a stop button, and an optional secondary button -- .countdown repeats after the postAlert interval (snooze) or .custom opens the app into the intervention; a wake alert whose only exit is stop wastes the highest-intent moment of the day)")
    if not pr.get("sound_bundled_and_referenced"):
        fails.append("AK-4 the alarm sound is not both bundled and referenced (a custom sound must live in the app's main bundle or Library Sounds and be passed as the configuration's sound; a sound file sitting in the source tree but absent from the target is not a sound anyone will hear)")
    if not pr.get("tint_and_metadata_identify_app"):
        fails.append("AK-4 tint color and metadata do not identify the app's alarms (attributes carry tintColor and metadata so the person can tell this alarm from every other app's alarm on the device, and so the widget extension can render its context)")
    ms = d.get("measurement") or {}
    if not ms.get("scheduled_and_authorization_measured"):
        fails.append("AK-5 scheduled alarms and the alarm-authorization rate are not measured (an unmeasured permission is a silent cliff: the share of cant_wake_up users whose wake alarm actually exists is the first number of this surface)")
    if not ms.get("fired_and_open_measured"):
        fails.append("AK-5 alarm firing and the fire-to-open / fire-to-intervention path are not measured (the wake moment is the daily re-entry point of the product; unmeasured, a broken alarm and an ignored alarm are the same zero)")
    if not ms.get("fallback_for_denied_and_older_ios"):
        fails.append("AK-5 denied and pre-iOS-26 users have no defined fallback that actually schedules something (consent can be revoked in Settings at any time and most devices lag the newest OS; a fallback whose entry point only deletes pending requests is a blackout with extra steps)")
    if not ms.get("wake_outcome_joined_to_cohort"):
        fails.append("AK-5 the wake outcome is not joined to the cant_wake_up cohort and the onboarding wake time (the product already asks when the person wants to wake and whether waking is their problem; unjoined, the team cannot tell whether the alarm surface moves the one behaviour it exists for)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: alarmkit_check.py <state.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    app = d.get("app", "?")
    if fails:
        print(f"FAIL {app}: {len(fails)} gate failures")
        for x in fails:
            print(" -", x)
        return 1
    print(f"PASS {app}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
