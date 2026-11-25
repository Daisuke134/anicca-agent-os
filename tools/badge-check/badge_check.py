#!/usr/bin/env python3
"""badge-check: deterministic gate for the app-icon badge stack
(authorization honesty -> absolute-count setting -> clearing on open ->
HIG semantics -> measurement), for an app whose delivery is remote
push nudges. Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple Human Interface Guidelines, Notifications / Badging (HIG text
  read via https://appguidelines.com/human-interface-guidelines/version/9/notifications/
  and https://apple-docs.everest.mt/docs/design/human-interface-guidelines/notifications/):
  a badge is a small filled oval with a number on the app icon showing
  how many unread notifications are available; after people address
  them the badge disappears. Use a badge ONLY for unread notifications
  -- never for weather, dates/times, stock prices, or game scores.
  Badging must not be the only channel for essential information
  (people can turn badges off). Keep badges up to date: update as soon
  as people open the corresponding notifications; you do not want
  people to think new notifications exist when they have viewed them
  all. Avoid custom images/components that mimic a badge.
- Soarias, SwiftUI badge count implementation (practitioner canon,
  reviewed 2026-05-11) https://www.soarias.com/swiftui/how-to-implement-badge-count/
  Request .badge authorization, then UNUserNotificationCenter
  .setBadgeCount(_:) (introduced iOS 16, replaces the deprecated
  applicationIconBadgeNumber) sets the count and 0 clears it. The
  count must be persisted/tracked (UserDefaults or server) and
  re-applied; check notificationSettings().badgeSetting because the
  person can disable badges separately, and mirror the count inside
  the app with an accessibility label because VoiceOver does not
  announce badge counts.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, badge_meaning_defined, decision_recorded},
 authorization:{badge_option_requested, badge_actually_set_somewhere,
   badge_setting_reread, badge_not_only_channel},
 setting:{absolute_count_source_tracked, server_payload_sets_badge,
   local_or_nse_sets_badge, willpresent_includes_badge},
 clearing:{clears_on_open_corresponding, clears_on_foreground_when_none_left,
   uses_modern_setbadgecount},
 semantics:{number_is_unread_notifications_only, no_unrelated_numeric_use,
   custom_badge_mimic_in_use, count_mirrored_in_app_accessibly},
 measurement:{event_defined, event_fired, badge_enabled_share_counted,
   joinable_to_outcome}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("BDG-0 the badge surface is not inventoried (whether the app requests .badge, whether anything ever sets a count, and what a count would mean are nowhere recorded; an unrecorded surface cannot be audited)")
    if not inv.get("badge_meaning_defined"):
        fails.append("BDG-0 what the badge number counts is not defined in one sentence (Apple HIG: the number is the count of unread notifications available. An app that cannot say 'our badge counts X' in one sentence has no badge semantics, only a permission bit)")
    if not inv.get("decision_recorded"):
        fails.append("BDG-0 no recorded decision exists for the badge (the only two honest states are 'we use it, with this lifecycle' or 'we removed .badge from the authorization request'. Requesting a permission the product never uses, forever, by drift, is neither)")
    auth = d.get("authorization") or {}
    if auth.get("badge_option_requested") and not auth.get("badge_actually_set_somewhere"):
        fails.append("BDG-1 .badge is requested at authorization but no code path in the app ever sets a badge count (the person grants a capability the product never exercises: the permission sheet promises a surface that does not exist, and the Settings > Notifications > Badges toggle controls nothing)")
    if not auth.get("badge_setting_reread"):
        fails.append("BDG-1 notificationSettings().badgeSetting is never re-read (badges have their own Settings toggle, separate from alerts and sounds; a person who turned badges off gets silence from setBadgeCount calls, and an app that never reads the setting cannot tell a disabled badge from a delivered one)")
    if not auth.get("badge_not_only_channel"):
        fails.append("BDG-1 the badge is the only channel for essential information (Apple HIG: people can turn badging off, so anything essential that lives only in the badge count will be missed by exactly the people who opted out)")
    st = d.get("setting") or {}
    badge_used = bool(auth.get("badge_actually_set_somewhere"))
    if not st.get("absolute_count_source_tracked"):
        fails.append("BDG-2 no source of truth tracks the absolute badge count (iOS gives no API to read the current system badge; the count must be maintained server-side or persisted on device and sent as an absolute value -- increment-by-hope from multiple writers corrupts the one number the person trusts)")
    if not st.get("server_payload_sets_badge") and not st.get("local_or_nse_sets_badge"):
        fails.append("BDG-2 no delivery path ever sets the badge (for remote delivery the APNs payload must carry aps.badge as the absolute unacted count, or the Notification Service Extension must compute it; for local delivery the content must set .badge. A badge that no path sets can never appear, whatever the payload console shows)")
    if badge_used and not st.get("willpresent_includes_badge"):
        warns.append("BDG-2 willPresent does not include .badge (foreground arrivals will not be badged by presentation; acceptable only if a separate foreground sync sets the count -- recorded here as a warning, not assumed)")
    cl = d.get("clearing") or {}
    if not cl.get("clears_on_open_corresponding"):
        fails.append("BDG-3 the badge is not updated when the person opens the corresponding notification (Apple HIG: keep badges up to date -- update as soon as people open the corresponding notifications. A count that survives being acted on teaches the person the number lies, and a lying badge is worse than none)")
    if not cl.get("clears_on_foreground_when_none_left"):
        fails.append("BDG-3 entering the foreground with nothing left unacted does not clear the badge to zero (the home screen is where the badge lives; opening the app and finding nothing new while the icon still claims otherwise is the exact frustration the HIG passage names)")
    if (cl.get("clears_on_open_corresponding") or cl.get("clears_on_foreground_when_none_left")) and not cl.get("uses_modern_setbadgecount"):
        fails.append("BDG-3 clearing uses the deprecated applicationIconBadgeNumber instead of UNUserNotificationCenter.setBadgeCount (iOS 16+; the legacy property also deletes delivered notifications from Notification Center when set to 0, a side effect the modern API does not have -- the choice must be deliberate, not inherited)")
    sm = d.get("semantics") or {}
    if not sm.get("number_is_unread_notifications_only"):
        fails.append("BDG-4 the badge number is not the count of unread notifications (Apple HIG: use a badge only to show how many unread notifications people have -- a streak, a day count, or a score in the badge oval borrows the system's most trusted attention signal for a number it does not mean)")
    if not sm.get("no_unrelated_numeric_use"):
        fails.append("BDG-4 the badge conveys numeric information unrelated to notifications (dates, times, prices, streaks or scores are named exclusions in the HIG; each one converts a notification signal into an advertisement the person cannot distinguish from a real unread item)")
    if sm.get("custom_badge_mimic_in_use"):
        fails.append("BDG-4 a custom in-app component mimics the system badge's appearance or behaviour while in use (Apple HIG: people who turned badges off will be frustrated by an apparent badge they cannot turn off; an in-app count must be visibly the app's own element, in the app's own language)")
    if badge_used and not sm.get("count_mirrored_in_app_accessibly"):
        fails.append("BDG-4 the badge count is not mirrored inside the app with an accessible label (badge counts are not announced by VoiceOver; a count that exists only on the icon is information a VoiceOver user is structurally excluded from)")
    ms = d.get("measurement") or {}
    if not ms.get("event_defined"):
        fails.append("BDG-5 no badge measurement event exists at all (badge set / badge cleared / badge-visible share are unknowable in principle; whether the badge earns its permission bit is a matter of opinion)")
    elif not ms.get("event_fired"):
        fails.append("BDG-5 the badge event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'the badge works' forever, indistinguishable from the truth)")
    if not ms.get("badge_enabled_share_counted"):
        fails.append("BDG-5 the badge-enabled share is not counted (badgeSetting == enabled among authorized users is the surface's reach denominator; without it a zero effect cannot be separated from a zero audience)")
    if not ms.get("joinable_to_outcome"):
        fails.append("BDG-5 badge state cannot be joined to outcome (badge shown -> app opened from icon, versus opened from the notification itself), so whether the persistent icon signal brings anyone back is unknowable")
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
