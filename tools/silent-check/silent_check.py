#!/usr/bin/env python3
"""silent-check: deterministic gate for iOS silent / background push
(content-available) -- the invisible refresh channel that pre-loads the
next moment's words before the user opens the app.
Stdlib only, offline, free.
Sources (read 2026-11-15):
- Pushwoosh, "Silent push notifications: how they work & when to use
  them" (full read): a silent push wakes the app in the background with
  no alert/sound/badge; payload is aps {content-available: 1} with no
  visible keys; headers must be apns-push-type: background and
  apns-priority: 5 (priority 10 with background is the most common
  mistake and can be rejected); iOS gives ~30 seconds and the app must
  call the completion handler with a truthful result (.newData/.noData/
  .failed) or iOS throttles future pushes; Apple advises roughly 2-3
  background pushes per hour; the handler is
  application(_:didReceiveRemoteNotification:fetchCompletionHandler:);
  the app target must enable Background Modes -> Remote notifications.
- Practitioner explainer (secondary, signops.dev via Medium,
  2026-11-12): custom keys sit beside aps, not inside it; register for
  remote notifications on every launch; a background push is a hint to
  sync, never a guarantee -- the system can store, delay, coalesce or
  discard it, a force-quit app is not woken, and the app must sync
  again whenever it comes to the foreground.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, refresh_jobs_listed, decision_recorded},
 capability:{background_mode_remote_notification,
   register_for_remote_notifications_on_launch,
   token_registration_failure_handled},
 sender_payload:{content_available_only_no_visible_keys,
   push_type_background_priority_5_evidenced,
   send_rate_within_platform_guidance},
 handler:{fetch_handler_exists,
   handler_checks_content_available_and_does_real_refresh,
   completion_handler_always_called_with_truthful_result},
 fallback:{not_relied_on_as_guaranteed_or_precise,
   foreground_resync_covers_missed_wakeups},
 measurement:{wakeups_and_completion_results_counted,
   refresh_outcome_joined_to_next_open_freshness}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("SP-0 the silent/background-push surface is not inventoried (whether the app can be woken invisibly to refresh content is nowhere recorded; an unrecorded channel cannot be audited)")
    if not inv.get("refresh_jobs_listed"):
        fails.append("SP-0 the refresh jobs a silent push would serve are not listed (for a nudge product: pre-loading today's words, syncing assignment/outcome state, refreshing widget data -- without named jobs the channel has no purpose to be judged against)")
    if not inv.get("decision_recorded"):
        fails.append("SP-0 no recorded decision exists for the silent channel (the honest states are 'silent push is a hint that triggers a bounded refresh, with foreground re-sync as the real guarantee' or an explicit recorded choice not to use it -- silence is not a state)")
    cap = d.get("capability") or {}
    if not cap.get("background_mode_remote_notification"):
        fails.append("SP-1 the remote-notification background mode is not declared (without UIBackgroundModes containing remote-notification, iOS will not wake the app for a background push at all)")
    if not cap.get("register_for_remote_notifications_on_launch"):
        fails.append("SP-1 the app does not register for remote notifications on launch (a stale or missing device token means the server cannot address the device; registration is per-launch, not once-ever)")
    if not cap.get("token_registration_failure_handled"):
        fails.append("SP-1 device-token registration failure is not handled/recorded (didFailToRegister silently swallowed means a whole class of unreachable devices is invisible)")
    sp = d.get("sender_payload") or {}
    if not sp.get("content_available_only_no_visible_keys"):
        fails.append("SP-2 the sender's silent payload is not evidenced as content-available: 1 with no alert/sound/badge keys (visible keys make it an alert push, not a background wake; a sender outside the client repo stays unverified until its payload is read)")
    if not sp.get("push_type_background_priority_5_evidenced"):
        fails.append("SP-2 apns-push-type: background with apns-priority: 5 is not evidenced (priority 10 with a background push type is an error/rejection risk and the most common silent-push mistake; an omitted header silently defaults to 10)")
    if not sp.get("send_rate_within_platform_guidance"):
        fails.append("SP-2 the silent send rate is not bounded to platform guidance (Apple advises roughly 2-3 background pushes per hour per device; more frequent sends are throttled/coalesced by the system and buy nothing)")
    hd = d.get("handler") or {}
    if not hd.get("fetch_handler_exists"):
        fails.append("SP-3 no didReceiveRemoteNotification fetch handler exists (declaring the background mode without the handler is a dead capability: the system may wake the app and there is no code to run)")
    if not hd.get("handler_checks_content_available_and_does_real_refresh"):
        fails.append("SP-3 the handler does not check content-available and perform the actual refresh (a handler that ignores the payload, or one that exists but refreshes nothing, leaves the app exactly as stale as before the wake)")
    if not hd.get("completion_handler_always_called_with_truthful_result"):
        fails.append("SP-3 the completion handler is not always called with a truthful result (.newData/.noData/.failed within the ~30s window; never calling it, or always claiming .newData, teaches the system to throttle the app's future wakeups)")
    fb = d.get("fallback") or {}
    if not fb.get("not_relied_on_as_guaranteed_or_precise"):
        fails.append("SP-4 silent push is relied on as guaranteed or precise (delivery is best-effort: the system can store, delay, coalesce or discard it, Background App Refresh can be off, and a force-quit app is not woken -- a moment-critical path built on it will silently miss)")
    if not fb.get("foreground_resync_covers_missed_wakeups"):
        fails.append("SP-4 there is no foreground re-sync covering missed wakeups (the documented pattern is: silent push is a hint to sync, and the app syncs again whenever it comes to the foreground -- without that, every throttled/discarded wake is permanent staleness)")
    ms = d.get("measurement") or {}
    if not ms.get("wakeups_and_completion_results_counted"):
        fails.append("SP-5 wakeups and their completion results are not counted (sent vs woken vs .newData/.noData/.failed is the only way to see throttling happening; without it a dead channel looks identical to a working one)")
    if not ms.get("refresh_outcome_joined_to_next_open_freshness"):
        fails.append("SP-5 the refresh outcome is not joined to next-open freshness (whether the user opened the app to already-current words -- the entire point of the channel -- is unknowable if wakeups are counted in isolation)")
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
