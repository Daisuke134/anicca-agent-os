#!/usr/bin/env python3
"""ts-check: deterministic gate for iOS Time Sensitive notifications
(UNNotificationInterruptionLevel / interruption-level in the APNs payload).
Stdlib only, offline, free. Sources (read 2026-11-15):
- Apple Human Interface Guidelines, Managing notifications
  https://apple-docs.everest.mt/docs/design/human-interface-guidelines/managing-notifications/
  Specify a system-defined interruption level for EACH noncommunication
  notification. Time Sensitive = information that directly impacts the
  person and requires immediate attention; it overrides scheduled
  delivery and breaks through Focus, but does not override the
  Ring/Silent switch. Use Time Sensitive ONLY for notifications relevant
  in the moment -- about an event happening now or within an hour.
  NEVER use Time Sensitive for a marketing notification. Build trust by
  accurately representing urgency: people can turn off Time Sensitive,
  or all notifications. The first Time Sensitive arrival triggers a
  system explanation with an opt-out, and the system periodically
  re-offers that evaluation -- every misuse is judged again.
- Courier, iPhone Priority Notifications: A Developer Guide to iOS
  Interruption Levels https://www.courier.com/blog/developer-guide-to-ios-26-priority-notifications
  The `interruption-level` key in the `aps` dictionary sets the level
  for remote pushes; local notifications set content.interruptionLevel.
  Sending time-sensitive requires the Time Sensitive capability
  (entitlement) AND the level on each notification -- the capability
  alone changes nothing about delivery.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, types:[{name, intended_level, moment_bound, marketing}]},
 capability:{entitlement_present, authorization_option_requested,
   onboarding_requires_ts_enabled, onboarding_explains_ts},
 delivery:{any_path_sets_level, level_set_per_type,
   payload_verified_in_canonical_source, service_extension_sets_level},
 honesty:{ts_only_for_moment_bound, no_marketing_at_ts,
   non_moment_types_at_active_or_passive, critical_not_claimed},
 user_state:{ts_setting_read_beyond_onboarding, fallback_when_ts_disabled,
   disabled_state_asked_honestly},
 measurement:{event_defined, event_fired, per_level,
   ts_disabled_rate_tracked, joinable_to_outcome}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    types = inv.get("types") or []
    if not inv.get("recorded"):
        fails.append("TS-0 the interruption-level state is not inventoried (which notification types exist, what level each is intended to carry, and what is actually sent today are nowhere recorded; an unrecorded urgency policy cannot be audited)")
    if not types:
        fails.append("TS-0 no notification types are named (an interruption level is assigned per notification, per Apple HIG -- with no type list there is nothing to assign levels to)")
    else:
        if any(t.get("intended_level") in (None, "", "unspecified") for t in types):
            fails.append("TS-0 at least one notification type has no intended interruption level (Apple HIG: specify a system-defined interruption level for each noncommunication notification you send; an unspecified type silently defaults to active and its urgency was never decided)")
    cap = d.get("capability") or {}
    has_capability = bool(cap.get("entitlement_present")) and bool(cap.get("authorization_option_requested"))
    if not cap.get("entitlement_present"):
        fails.append("TS-1 the Time Sensitive entitlement (com.apple.developer.usernotifications.time-sensitive) is absent, so no notification from this app can ever be delivered as time-sensitive, whatever the payload claims")
    if not cap.get("authorization_option_requested"):
        fails.append("TS-1 the .timeSensitive authorization option is never requested, so the person is never asked for the capability the entitlement declares")
    if cap.get("onboarding_requires_ts_enabled") and not cap.get("onboarding_explains_ts"):
        warns.append("TS-1 onboarding counts permission as granted only when Time Sensitive is enabled, yet its copy never explains Time Sensitive or Focus breakthrough -- the person is held to a privilege they were never told they granted")
    dlv = d.get("delivery") or {}
    any_sets = bool(dlv.get("any_path_sets_level"))
    if has_capability and not any_sets:
        fails.append("TS-2 the capability is declared and demanded but never spent: no delivery path sets an interruption level (no content.interruptionLevel locally, no verified interruption-level key in the APNs payload) -- every notification arrives at the default active level and cannot break through Focus or Scheduled Summary, so the entitlement and the onboarding demand are a promise the delivery never keeps)")
    if not has_capability and not any_sets:
        fails.append("TS-2 no delivery path sets an interruption level and no capability exists either (urgency is entirely unimplemented, not merely unwired)")
    if any_sets:
        if not dlv.get("level_set_per_type"):
            fails.append("TS-2 the level is not set per notification type (one blanket level for every push is exactly the cry-wolf shape Apple HIG warns against; urgency is a per-type decision)")
        if not dlv.get("payload_verified_in_canonical_source"):
            fails.append("TS-2 the level-setting code/payload cannot be verified in the canonical source (an interruption level that lives only in an unrecorded server configuration is not evidence; from the auditable source the delivery is indistinguishable from never setting it)")
    hon = d.get("honesty") or {}
    ts_types = [t for t in types if t.get("intended_level") == "time-sensitive"]
    if ts_types:
        if not hon.get("ts_only_for_moment_bound"):
            fails.append("TS-3 a type is assigned time-sensitive without being moment-bound (Apple HIG: Time Sensitive only for an event happening now or within an hour; a daily content push whose value does not expire within the hour does not qualify)")
        if not hon.get("no_marketing_at_ts"):
            fails.append("TS-3 marketing content is sent at time-sensitive (Apple HIG, verbatim rule: never use the Time Sensitive interruption level to send a marketing notification)")
    if types and not hon.get("non_moment_types_at_active_or_passive"):
        fails.append("TS-3 non-moment-bound types are not held at active or passive (everything escalated is the same as nothing escalated -- the person learns to turn Time Sensitive off for the whole app)")
    if not hon.get("critical_not_claimed"):
        fails.append("TS-3 the critical level is claimed without Apple's special approval (critical bypasses the mute switch and is reserved for health/public-safety apps Apple approves; claiming it unapproved is a false capability)")
    us = d.get("user_state") or {}
    if not us.get("ts_setting_read_beyond_onboarding"):
        fails.append("TS-4 timeSensitiveSetting is read only during onboarding, never at delivery planning (the person can turn Time Sensitive off at any time -- from Settings, from the Lock Screen, or at the system's periodic re-prompt; a state read once at signup describes a person who may no longer exist)")
    if not us.get("fallback_when_ts_disabled"):
        fails.append("TS-4 there is no fallback when Time Sensitive is disabled (the notification silently degrades to summary timing; for a scheduled-moment product the words then arrive hours late with no in-app or next-open recovery, and nobody records that this happened)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("TS-5 the interruption-level event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'urgency works' forever, indistinguishable from the truth)")
    if not ms.get("event_defined"):
        fails.append("TS-5 no per-notification interruption-level event exists at all (whether any nudge ever broke through a Focus, and what that did to opens, is unknowable in principle)")
    if any_sets and not ms.get("per_level"):
        fails.append("TS-5 delivery/open rates are not measured per interruption level (time-sensitive spends user trust; without a per-level read its return can never be compared against its cost in disabled settings)")
    if not ms.get("ts_disabled_rate_tracked"):
        fails.append("TS-5 the share of users with Time Sensitive disabled is not tracked (that share is the direct price of urgency misuse -- Apple surfaces the opt-out at first arrival and periodically after; an app that never reads it cannot know it is crying wolf)")
    if not ms.get("joinable_to_outcome"):
        fails.append("TS-5 interruption level cannot be joined to outcome (delivered-in-Focus -> opened -> session started), so whether breakthrough earns anything is a matter of opinion")
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
