#!/usr/bin/env python3
"""blackout-check: deterministic gate for notification blackout / fallback.
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Daily Pills practitioner write-up, "Medication Reminders That Actually
  Fire" (dev.to, app live since May 2020):
  http://dev.to/aryansbtloe/medication-reminders-that-actually-fire-local-notifications-the-64-notification-limit-and-supply-2m4h
  A reminder whose time is knowable on-device is scheduled locally with a
  repeating UNCalendarNotificationTrigger (hour/minute only, so it fires at
  local wall-clock time after travel/DST), deterministic identifiers
  (rescheduling replaces, cancelling one item cannot touch another), a
  pending-queue budget (system keeps the soonest 64; the rest are silently
  discarded; repeating requests count as one), a pending audit comparing
  what you think is scheduled with what the system has, and a rolling
  window topped up whenever the app becomes active. "Never assume
  scheduled once means scheduled forever."
- Apple, Local and Remote Notification Programming Guide (archive):
  https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/SupportingNotificationsinYourApp.html
  Local notifications are generated on-device; remote notifications need
  APNs registration, whose failure path is a real app state, not an edge
  case to ignore.
- HabStick (habit reminder product, live page read 2026-11-15):
  https://www.habsticks.in/features/habit-reminders
  The shipped promise form: reminders are scheduled locally, fire offline
  with no server/account, and a denied exact-alarm permission falls back
  to inexact delivery instead of failing silently.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 decision:{recorded, contradictory_claims_present},
 fallback:{entry_exists, entry_adds_requests, entry_only_removes,
           uses_repeating_calendar_trigger, deterministic_ids,
           pending_budget_checked_le64, pending_audit_exists,
           topup_on_become_active},
 branches:{remote_not_enabled_ends_scheduled, http_error_ends_scheduled,
           network_error_ends_scheduled,
           apns_registration_failure_ends_scheduled},
 dedup:{local_cancelled_only_after_remote_confirmed,
        cancel_scope_is_specific},
 content:{fallback_uses_users_own_times, fallback_uses_users_own_problems,
          fallback_claimed_personalized_but_generic},
 measurement:{blackout_state_event_defined, blackout_state_event_fired,
              pending_count_readback_exists,
              delivery_split_remote_vs_local}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    dec = d.get("decision") or {}
    if not dec.get("recorded"):
        fails.append("NB-0 the delivery-mode decision (remote-only / local-only / hybrid, and what happens in each failure state) is not recorded in one place (an unrecorded mode cannot be audited; the next editor re-decides it from comments)")
    if dec.get("contradictory_claims_present"):
        fails.append("NB-0 contradictory claims about the fallback coexist in the source (one site promises a fail-safe local restore, another says there is no local fallback by design, a third says the local scheduler is retired -- three different products described in one build; a user in the gap gets whichever comment lost)")
    fb = d.get("fallback") or {}
    if not fb.get("entry_exists"):
        fails.append("NB-1 no fallback entry point exists at all (when remote delivery is unavailable there is no code path whose job is to keep reminders firing on-device)")
    else:
        if not fb.get("entry_adds_requests"):
            fails.append("NB-1 the fallback entry point never adds a notification request (a restore function with zero add() calls restores nothing; the name promises delivery and the body delivers silence)")
        if fb.get("entry_only_removes"):
            fails.append("NB-1 the fallback entry point only removes pending requests (calling it in a failure branch actively deletes the user's remaining local reminders -- the fail-safe is a fail-deadly: every remote failure makes the blackout more complete)")
        if fb.get("entry_adds_requests") and not fb.get("uses_repeating_calendar_trigger"):
            fails.append("NB-2 the fallback does not use a repeating calendar trigger (one-off dates exhaust themselves; a daily reminder needs UNCalendarNotificationTrigger with hour/minute and repeats:true so it fires at local wall-clock time after travel and DST)")
        if fb.get("entry_adds_requests") and not fb.get("deterministic_ids"):
            fails.append("NB-2 the fallback does not use deterministic identifiers (without stable ids, rescheduling duplicates and cancelling one reminder can touch another's; ids are how a schedule is replaced, not stacked)")
        if fb.get("entry_adds_requests") and not fb.get("pending_budget_checked_le64"):
            fails.append("NB-2 the fallback never checks the 64 pending-request budget (the system keeps the soonest 64 and silently discards the rest; an unchecked schedule over the cap fails with no error anywhere)")
        if not fb.get("pending_audit_exists"):
            fails.append("NB-3 no pending audit exists (nothing ever compares what the app thinks is scheduled with pendingNotificationRequests(); a silently dropped or deleted schedule is invisible until the user notices the silence)")
        if fb.get("entry_adds_requests") and not fb.get("topup_on_become_active"):
            warns.append("NB-3 the fallback schedule is not topped up when the app becomes active (a rolling window that is never refilled runs out; 'scheduled once' is not 'scheduled forever' -- warning only, but the refill site must be recorded)")
    br = d.get("branches") or {}
    branch_labels = {
        "remote_not_enabled_ends_scheduled": "the server says remote delivery is not enabled for this user (e.g. a free / non-entitled user)",
        "http_error_ends_scheduled": "token registration returns a non-2xx response",
        "network_error_ends_scheduled": "token registration throws a network error",
        "apns_registration_failure_ends_scheduled": "APNs registration itself fails (didFailToRegisterForRemoteNotificationsWithError)",
    }
    for key, label in branch_labels.items():
        if not br.get(key):
            fails.append(f"NB-4 a failure branch ends with nothing scheduled: {label} (this is the blackout state -- authorized, expecting reminders, receiving none, with no error shown to anyone)")
    dd = d.get("dedup") or {}
    if not dd.get("local_cancelled_only_after_remote_confirmed"):
        fails.append("NB-5 local reminders are cancelled before remote delivery is confirmed for this user (cancelling on token upload alone -- before the server confirms it will actually send -- trades a working local schedule for a promise)")
    if not dd.get("cancel_scope_is_specific"):
        fails.append("NB-5 cancellation is not scoped to specific ids / a specific prefix (an unscoped cancel can delete schedules that belong to a different feature or a different mode)")
    ct = d.get("content") or {}
    if fb.get("entry_adds_requests"):
        if not ct.get("fallback_uses_users_own_times"):
            fails.append("NB-6 the fallback does not use the user's own reminder times (a fallback that fires at default times the user never chose is a different product arriving uninvited; the per-problem / per-habit schedule data must be the fallback's input)")
        if not ct.get("fallback_uses_users_own_problems"):
            fails.append("NB-6 the fallback does not use the user's own problems / habits (generic content at generic times is not the reminder the user set up)")
    if ct.get("fallback_claimed_personalized_but_generic"):
        fails.append("NB-6 the fallback is described as personalised while its content is generic (outside-inside mismatch: the promise says 'your reminders keep working', the delivery is a placeholder -- what is shown outside must exist inside)")
    ms = d.get("measurement") or {}
    if ms.get("blackout_state_event_defined") and not ms.get("blackout_state_event_fired"):
        fails.append("NB-7 the blackout state has an event defined but it is never fired (a defined-but-unfired event reads as zero blackouts forever -- the worst state in the product is the one the dashboard cannot see)")
    if not ms.get("blackout_state_event_defined"):
        fails.append("NB-7 the blackout state is not even defined as a measurable state (authorized + remote-unconfirmed + zero pending local = a countable condition; if it is not counted, its size is a guess)")
    if not ms.get("pending_count_readback_exists"):
        fails.append("NB-7 there is no pending-count readback anywhere (the one number that proves a fallback worked -- pending requests after a failure branch -- is never read, so 'restored' is a claim, not a measurement)")
    if not ms.get("delivery_split_remote_vs_local"):
        warns.append("NB-7 deliveries are not split remote vs local in measurement (without the split, a fallback that silently became the main path -- or died -- cannot be told from healthy remote delivery; warning only)")
    return fails, warns

def main():
    if len(sys.argv) < 2:
        print("usage: blackout_check.py <input.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails, warns = check(d)
    verdict = "FAIL" if fails else "PASS"
    print(json.dumps({"app": d.get("app"), "verdict": verdict,
                      "fails": fails, "warnings": warns},
                     indent=2, ensure_ascii=False))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
