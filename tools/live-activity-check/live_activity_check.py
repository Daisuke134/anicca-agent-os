#!/usr/bin/env python3
"""live-activity-check: deterministic gate for iOS Live Activities.
Stdlib only, offline, free. Sources (full read 2026-11-14):
- Apple Human Interface Guidelines, Live Activities (via HIG text):
  for tasks and events with a defined beginning and end, ideally not
  exceeding eight hours; focus on glanceable, important information;
  no ads or promotions; avoid sensitive information (Lock Screen and
  Always-On are visible to casual observers) -- show an innocuous
  summary and let people tap through, or redact and let people
  configure it; match the app's visual aesthetic in light and dark;
  include a logo mark without a container, never the whole app icon;
  use large, medium-weight-or-heavier text.
- Apple ActivityKit, Displaying live data with Live Activities:
  a Live Activity can be active for up to eight hours; after that the
  system ends it and removes it from the Dynamic Island, and it stays
  on the Lock Screen up to four more hours (12 hours maximum total).
  Each Live Activity runs in its own sandbox and can't access the
  network or receive location updates; update it with ActivityKit in
  the app or with ActivityKit push notifications. Always end it
  immediately when the task or event ends; a custom dismissal time
  proportional to duration is usually 15 to 30 minutes.
- ASOWin, App Widgets and Live Activities for Engagement and ASO
  https://www.asowin.com/blog/ios-widgets-live-activities-engagement/
  Live Activities show real-time updates for ongoing events (deliveries,
  rides, sports scores, workouts, timers) and end when the event
  finishes; they are ideal for time-bound tasks where users would
  otherwise keep opening the app. Worked example: a habit tracker adds
  a Live Activity for timed habits like meditation. Metrics: widget
  adoption, taps into the app, Live Activity usage, retention of users
  vs non-users read with a prompt control (correlation is not causation).
In-house prior decisions reused, not reinvented: widget-check W-0..W-7
already governs home/lock-screen widgets, and its spec records that a
standing affirmation display is NOT a Live Activity use (a Live
Activity is for time-bounded ongoing events, not a permanent surface).
Exit 0 = PASS, 1 = FAIL, 2 = PARTIAL (new section unrecorded).
Extension LA-8..LA-11 (2026-11-21, remote updates / push-to-start):
- Apple, Starting and updating Live Activities with ActivityKit push
  notifications (updated 2026-11-15, full read 2026-11-21):
  https://apple-docs.everest.mt/docs/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications/
  priority 5 does not count toward the hourly push budget, priority 10
  does -- try 5 first, mix 5/10, reserve 10 for updates needing
  immediate attention; push tokens arrive asynchronously via
  pushTokenUpdates, change mid-activity, old tokens must be
  invalidated server-side; frequentPushesEnabled must be read and the
  server frequency adjusted when people turn frequent pushes off;
  push-to-start (pushToStartTokenUpdates, iOS 17.2+) is exemplified
  only for recurring events a person opted to auto-track; stale-date
  advances with each update and the stale state gets an outdated UI;
  relevance-score is relative and decides Dynamic Island placement
  when several activities run; content-state decodes with default JSON
  strategies, so custom encoding breaks updates.
- aifitnessapi, Live Activity Updates per Hour (full read 2026-11-21):
  https://aifitnessapi.com/engagement/activitykit-live-activity-workout
  4 KB combined payload cap; check areActivitiesEnabled before
  requesting and treat a thrown request as a normal outcome; sweep
  Activity.activities at next launch and end orphans; timers tick
  on-device via Text(timerInterval:) instead of per-second pushes;
  update only when a displayed value changed. (Its 2-minute stale
  window is the author's choice, not Apple's; this gate judges only
  that a staleDate is set and advanced, never its number.)
New input section "remote" is optional for backward compatibility:
absent = WARN (PARTIAL, exit 2 when nothing else fails), present =
LA-8..LA-11 judged deterministically. remote.used=false (pure local
design) exempts LA-8 and the token/priority parts of LA-9.
"""
import json, sys

def check(d):
    fails, warns = [], []
    def fail(g, msg): fails.append(f"{g} {msg}")
    def warn(g, msg): warns.append(f"{g} {msg}")

    # LA-0 declaration vs reality, and a recorded end-state decision
    if d.get("recorded") is not True:
        fail("LA-0", "Live Activity state not recorded (declaration, lifecycle calls and shipped content must be read together, not assumed)")
    decision = d.get("decision")
    if decision not in ("ship_real", "remove"):
        fail("LA-0", f"no lawful end-state decision recorded (decision={decision!r}): either ship a real time-bounded Live Activity or remove the declaration and template -- declared-but-dead is not an end state")
    declared = d.get("declared_supports_live_activities") is True
    has_request = d.get("lifecycle", {}).get("request_on_user_action") is True
    if declared and not has_request and decision != "remove":
        fail("LA-0", "NSSupportsLiveActivities is declared but no Activity.request exists in the app: a declared-but-never-started surface (dead code carried into every review and build)")
    if decision == "remove":
        if d.get("template_removed") is not True:
            fail("LA-0", "decision is 'remove' but the template/placeholder Live Activity code is still in the bundle")
        if declared:
            fail("LA-0", "decision is 'remove' but NSSupportsLiveActivities is still declared")
        # removal path: event/content/lifecycle/privacy/update gates do not apply
        if d.get("measurement", {}).get("decision_recorded_with_reason") is not True:
            fail("LA-7", "removal decision is not recorded with its reason (the next builder will re-add the template)")
        return fails, warns

    # ship_real path
    ev = d.get("event", {})
    if ev.get("defined_begin_and_end") is not True:
        fail("LA-1", "the tracked thing has no defined beginning and end (HIG: Live Activities are for tasks/events with a defined beginning and end)")
    dur = ev.get("duration_max_hours")
    if dur is None or dur > 8:
        fail("LA-1", f"duration_max_hours={dur!r} exceeds the 8-hour system limit (the system ends it at 8h; Lock Screen residue lasts at most 4 more)")
    if ev.get("started_by_user_action") is not True:
        fail("LA-1", "not started by a deliberate in-app user action (a Live Activity must follow something the person started, not appear uninvited)")
    if ev.get("is_ongoing_event") is not True:
        fail("LA-1", "not an ongoing event: a standing/permanent display (e.g. a daily quote pinned forever) belongs on a widget, not a Live Activity (house widget spec already decided this)")

    c = d.get("content", {})
    if c.get("has_placeholder_strings") is True:
        fail("LA-2", "template/placeholder strings ship in the Live Activity (sample text such as Hello/Leading/Trailing/L/T is not content; a reviewer and a user see a template, not the product)")
    fields = c.get("content_state_fields") or []
    if not c.get("carries_real_dynamic_data"):
        fail("LA-2", "content state carries no real dynamic data of the event (the state must change as the event progresses: e.g. session kind, remaining time, current line)")
    if fields and set(fields) <= {"emoji"}:
        fail("LA-2", "content state is emoji-only (an emoji is decoration, not the event's data)")
    if c.get("shows_ads_or_promos") is True:
        fail("LA-2", "ads or promotions in a Live Activity (HIG: only information related to the ongoing event or task)")
    if c.get("widget_url_target") != "relevant_screen":
        fail("LA-4", f"tap target (widgetURL) is {c.get('widget_url_target')!r}, not the relevant in-app screen for this event (an external or generic URL strands the user outside the moment)")

    lc = d.get("lifecycle", {})
    if lc.get("request_on_user_action") is not True:
        fail("LA-3", "no request on user action (the lifecycle starts when the person starts the event)")
    if lc.get("updates_on_change") is not True:
        fail("LA-3", "no updates as the event's state changes (a static Live Activity is a widget with an expiry date)")
    if lc.get("ends_at_event_end") is not True:
        fail("LA-3", "does not end immediately when the event ends (Apple: always end it immediately when the task or event ends)")
    if lc.get("dismissal_set_proportional") is not True:
        fail("LA-3", "no proportional dismissal time set (default guidance: dismissal proportional to duration, usually 15-30 minutes; leaving the ended activity on the Lock Screen for hours is residue, not design)")

    s = c.get("surfaces", {})
    for k, label in [("lock_screen", "Lock Screen"), ("compact", "Dynamic Island compact"), ("minimal", "Dynamic Island minimal"), ("expanded", "Dynamic Island expanded")]:
        if s.get(k) is not True:
            fail("LA-4", f"{label} presentation carries no real content (every shipped presentation is seen by someone; a placeholder in one presentation is a placeholder in the product)")
    if c.get("keyline_matches_brand") is not True:
        fail("LA-4", "keyline tint does not match the app's content/brand (a template colour reads as someone else's app around the Dynamic Island)")
    if c.get("background_matches_brand") is not True:
        warn("LA-4", "Lock Screen background tint not confirmed to match the app's aesthetic in light and dark appearances")

    p = d.get("privacy", {})
    if p.get("sensitive_shown_by_default") is True:
        fail("LA-5", "sensitive content shown by default on the Lock Screen (Live Activities are visible without unlocking, to casual observers; struggles/pain details need an innocuous summary plus tap-through)")
    if p.get("innocuous_summary") is not True:
        fail("LA-5", "no innocuous summary form (HIG: show an innocuous summary and let people tap through for detail)")
    if p.get("user_configurable") is not True:
        warn("LA-5", "what appears on the Lock Screen is not user-configurable (HIG offers redact/configure as the alternative when a summary is not enough)")

    u = d.get("updates", {})
    if d.get("frequent_updates_enabled") is True and u.get("frequent_updates_justified") is not True:
        fail("LA-6", "NSSupportsLiveActivitiesFrequentUpdates is enabled with no recorded justification (frequent updates spend a system budget; an activity that never starts or rarely changes has no claim on it)")
    if u.get("assumes_network_or_location") is True:
        fail("LA-6", "design assumes the Live Activity itself can reach the network or location (it cannot: it runs in its own sandbox; data must arrive via the app or ActivityKit push)")
    if u.get("budget_accounted") is not True:
        warn("LA-6", "update budget / push priority not accounted for (updates arrive via the app or ActivityKit push within system budgets)")

    m = d.get("measurement", {})
    for k, label in [("starts_tracked", "starts"), ("ends_tracked", "ends/completion"), ("tap_through_tracked", "tap-through into the relevant screen"), ("retention_with_control", "retention read with a control (Live Activity users self-select; correlation is not causation)")]:
        if m.get(k) is not True:
            fail("LA-7", f"measurement missing: {label}")

    # Extension LA-8..LA-11 (2026-11-21): remote updates / push-to-start.
    # Optional section for backward compatibility: absent = PARTIAL.
    r = d.get("remote")
    if r is None:
        warn("LA-8..LA-11", "remote section not recorded (push-to-start discipline / push budget and priority / stale+relevance+payload / start robustness are unjudged, PARTIAL)")
    else:
        used = r.get("used") is True
        if used:
            # LA-9 token lifecycle (applies to any remote-update design)
            if r.get("push_token_observed_via_updates") is not True:
                fail("LA-9", "push token not observed via pushTokenUpdates (the token is not available synchronously after request; Apple: observe the async sequence and send every new token to the server)")
            if r.get("old_push_tokens_invalidated") is not True:
                fail("LA-9", "old push tokens are not invalidated server-side when a token rotates (Apple: invalidate the previous, now-outdated token or subsequent updates fail)")
            # LA-9 budget and priority
            if r.get("default_priority") != 5:
                fail("LA-9", f"default apns-priority is {r.get('default_priority')!r}, not 5 (priority 10 -- and the unspecified default -- counts toward the hourly ActivityKit push budget; Apple: consider priority 5 first, mix 5 and 10)")
            if r.get("priority_10_reserved_for_attention") is not True:
                fail("LA-9", "priority 10 is not reserved for updates that need immediate attention (routine updates at priority 10 spend the budget and invite throttling)")
            if r.get("frequent_setting_checked") is not True:
                fail("LA-9", "frequentPushesEnabled is not read / honoured (people can turn frequent pushes off in Settings; Apple: read the setting, subscribe to its updates, and adjust server frequency accordingly)")
        if r.get("push_to_start_used") is True:
            if r.get("push_to_start_opt_in") is not True:
                fail("LA-8", "Live Activities are started remotely with no recorded prior opt-in (Apple's push-to-start example is a recurring event the person chose to auto-track; a remote start without that expectation is an uninvited appearance, LA-1's user-action rule in remote form)")
            if r.get("push_to_start_min_os_handled") is not True:
                fail("LA-8", "push-to-start is relied on without handling iOS < 17.2 (push start is unavailable on 17.1 and earlier; pushToStartTokenUpdates arrives in 17.2)")
            if r.get("push_to_start_token_rotation_handled") is not True:
                fail("LA-8", "push-to-start token rotation is not handled (observe pushToStartTokenUpdates, send updates to the server, invalidate the old token)")
        # LA-9 cadence (local and remote alike)
        if r.get("updates_only_on_displayed_change") is not True:
            fail("LA-9", "updates are not limited to displayed-value changes (Apple HIG: update only when new content is available; continuous values are interpolated on-device, e.g. Text(timerInterval:), not pushed per second)")
        # LA-10 stale / relevance / payload honesty
        if r.get("stale_date_set_and_advanced") is not True:
            fail("LA-10", "no staleDate set and advanced with each update (without it a disconnected activity presents frozen data as live; Apple: advance the stale date with every update)")
        if r.get("stale_ui_shown") is not True:
            fail("LA-10", "no stale-state UI (when activityState becomes stale the person must be told the information is outdated, not shown a confident frozen number)")
        if r.get("multiple_activities_possible") is True and r.get("relevance_score_relative") is not True:
            fail("LA-10", "multiple activities can run but no relative relevanceScore is assigned (the system shows the highest score in the Dynamic Island; unassigned, the first-started wins regardless of importance)")
        kb = r.get("payload_max_kb")
        if kb is None or kb > 4:
            fail("LA-10", f"payload_max_kb={kb!r} exceeds the 4 KB combined cap (static + dynamic + push payload; oversized payloads are rejected)")
        if r.get("custom_json_encoding") is True:
            fail("LA-10", "custom JSON encoding strategies are used for content-state (the system always decodes Live Activity payloads with its default strategies; custom encoding results in update failures)")
        # LA-11 start robustness
        if r.get("activities_enabled_checked") is not True:
            fail("LA-11", "areActivitiesEnabled is not checked before requesting (people can turn Live Activities off per app; offering a start that cannot work is a broken promise)")
        if r.get("request_failure_handled") is not True:
            fail("LA-11", "a thrown Activity.request error is not treated as a normal outcome (start can fail on a healthy device; an unhandled throw is a crash or a silent dead button)")
        if r.get("orphan_sweep_at_launch") is not True:
            fail("LA-11", "no launch sweep of Activity.activities (after a crash or system stop, Apple recommends ending activities that are no longer relevant at next launch; orphans linger on the Lock Screen)")
        if r.get("assets_within_presentation_size") is not True:
            fail("LA-11", "image assets are not confirmed within presentation size (Apple: an asset larger than its presentation can make the Live Activity fail to start)")
    return fails, warns

def main():
    if len(sys.argv) < 2:
        print("usage: live_activity_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f: d = json.load(f)
    fails, warns = check(d)
    for w in warns: print(f"WARN  {w}")
    for f_ in fails: print(f"FAIL  {f_}")
    partial = d.get("remote") is None and d.get("decision") == "ship_real"
    if fails:
        print(f"FAIL: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app','?')}")
        return 1
    if partial:
        print(f"PARTIAL: 0 fail(s), {len(warns)} warning(s) -- {d.get('app','?')} (LA-8..LA-11 unrecorded)")
        return 2
    print(f"PASS: 0 fail(s), {len(warns)} warning(s) -- {d.get('app','?')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
