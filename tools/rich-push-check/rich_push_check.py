#!/usr/bin/env python3
"""rich-push-check: deterministic gate for iOS rich / actionable notifications.
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Bugfender, "How to Optimize iOS Push Notifications in Production"
  https://bugfender.com/blog/optimize-ios-push-notifications/
  Rich = media attachment via Notification Service Extension + mutable-content;
  interactive actions let users complete simple tasks WITHOUT opening the app
  (mark-as-read / snooze / accept are the canonical background actions);
  a category must be defined in code, registered with UNUserNotificationCenter,
  named in the payload, and the selected action handled in the delegate;
  measurement = campaign_id carried in every payload, push_received /
  push_opened / target-event logged with that id, downstream conversion and
  control-group comparison, not opens alone.
- Pushwoosh rich-push guide (search-read 2026-11-15)
  https://www.pushwoosh.com/blog/rich-push-notifications/
  iOS shows NO rich media without a Notification Service Extension; action
  buttons remove the app-load step whose dropout kills click-through.
- Apple UserNotifications mechanics (via the guides above and framework
  references): threadIdentifier groups notifications in Notification Center;
  interruptionLevel (.timeSensitive) must match real urgency and the
  authorization option alone sets nothing on delivered content;
  relevanceScore orders notifications inside a summary.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, categories_used:[], categories_registered:[]},
 actions:{background_completion_action_ids:[], foreground_action_ids:[]},
 response_handling:{branches_on_action_identifier, dismiss_does_not_navigate,
                    default_tap_routes_to_specific_content},
 extension:{exists, personalizes_body, attaches_media, fallback_on_timeout},
 grouping:{thread_identifier_set, summary_argument_set},
 interruption:{interruption_level_set, time_sensitive_only_for_urgent,
               relevance_score_set},
 measurement:{tap_event_defined, tap_event_fired, action_specific_events,
              dismiss_tracked, payload_id_carried, payload_id_read_in_app}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    # RP-0 inventory
    if not inv.get("recorded"):
        fails.append("RP-0 the notification surface is not inventoried (categories used vs registered are nowhere recorded; an unrecorded surface cannot be audited or fixed in order)")
    used = set(inv.get("categories_used") or [])
    reg = set(inv.get("categories_registered") or [])
    # RP-1 every used category registered
    missing = sorted(used - reg)
    if missing:
        fails.append(f"RP-1 categories used but never registered with setNotificationCategories: {missing} (an unregistered category shows no actions and any extension handling keyed to it is dead code)")
    if not used and not reg:
        fails.append("RP-1 no notification categories at all (every notification is a plain banner the person can only open or dismiss)")
    # RP-2 background completion action
    act = d.get("actions") or {}
    if not (act.get("background_completion_action_ids") or []):
        fails.append("RP-2 no background completion action (every action either opens the app [.foreground] or dismisses; the core task cannot be completed from the notification itself, so the app-load dropout sits on the main intervention path)")
    # RP-3 response handling
    rh = d.get("response_handling") or {}
    if not rh.get("branches_on_action_identifier"):
        fails.append("RP-3 the response handler never branches on actionIdentifier (tap, dismiss and every custom action receive identical handling; with .customDismissAction even a dismissal is routed like a tap)")
    if not rh.get("dismiss_does_not_navigate"):
        fails.append("RP-3 a dismissal can navigate / open content (dismiss means 'not now'; routing it to content punishes the clearest negative signal the user can send)")
    if not rh.get("default_tap_routes_to_specific_content"):
        fails.append("RP-3 a default tap does not route to the specific content the notification promised (outside and inside must be the same experience)")
    # RP-4 service extension
    ext = d.get("extension") or {}
    if ext.get("exists"):
        if not (ext.get("personalizes_body") or ext.get("attaches_media")):
            fails.append("RP-4 a Notification Service Extension exists but mutates nothing (no body personalization, no media attachment; the extension is ceremony, not a surface)")
        if not ext.get("fallback_on_timeout"):
            fails.append("RP-4 the service extension has no timeout fallback (serviceExtensionTimeWillExpire must deliver the best-attempt content; without it a slow fetch can swallow the notification)")
        if not ext.get("attaches_media"):
            warns.append("RP-4 the extension attaches no media (text-first may be a deliberate choice for this category, but it must be a choice, not an oversight -- warning only)")
    # RP-5 grouping
    grp = d.get("grouping") or {}
    if not grp.get("thread_identifier_set"):
        fails.append("RP-5 no threadIdentifier is set (notifications arrive ungrouped; multiple daily nudges stack as unrelated alerts in Notification Center instead of one thread per habit/topic)")
    if not grp.get("summary_argument_set"):
        warns.append("RP-5 no summary argument is set for grouped notifications (the grouped summary cannot name what it summarizes -- warning only)")
    # RP-6 interruption discipline
    itr = d.get("interruption") or {}
    if not itr.get("interruption_level_set"):
        fails.append("RP-6 interruptionLevel is never set on delivered content (requesting the .timeSensitive authorization option sets nothing; without an explicit level every nudge competes at the default level and Focus / summary ordering cannot work as designed)")
    if not itr.get("time_sensitive_only_for_urgent"):
        warns.append("RP-6 time-sensitive use is not restricted to genuinely urgent types (overuse trains Focus to demote the app -- warning only)")
    if not itr.get("relevance_score_set"):
        warns.append("RP-6 relevanceScore is not set (inside a scheduled summary, iOS cannot order this app's notifications by importance -- warning only)")
    # RP-7 measurement
    ms = d.get("measurement") or {}
    if ms.get("tap_event_defined") and not ms.get("tap_event_fired"):
        fails.append("RP-7 the notification-tap event is defined in the analytics enum but fired from 0 call sites (a defined-but-unfired event reads as 'no taps' forever; the funnel step is fiction)")
    if not ms.get("tap_event_defined"):
        fails.append("RP-7 no notification-tap event is defined at all (delivery cannot be connected to any downstream action)")
    if not ms.get("action_specific_events"):
        fails.append("RP-7 custom-action use is not measured separately from taps (which action completes, and which is ignored, is unknowable; the action set can never be pruned or improved)")
    if not ms.get("dismiss_tracked"):
        fails.append("RP-7 dismissals are not tracked (dismissal is the fatigue signal; without it, volume can rise while the only visible metric -- taps -- stays flat)")
    if ms.get("payload_id_carried") and not ms.get("payload_id_read_in_app"):
        fails.append("RP-7 a per-notification id is written into the payload / userInfo but never read in the app (attribution is produced and then discarded; push-to-conversion cannot be computed)")
    if not ms.get("payload_id_carried"):
        fails.append("RP-7 no per-notification / campaign id is carried in the payload (delivery, interaction and conversion cannot be tied together -- Bugfender: without a consistent identifier, attribution is unreliable)")
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
