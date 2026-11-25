#!/usr/bin/env python3
"""iw-check: deterministic gate for iOS interactive widgets (iOS 17+).
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Apple Developer Docs, "Adding interactivity to widgets and Live Activities"
  https://apple-docs.everest.mt/docs/widgetkit/adding-interactivity-to-widgets-and-live-activities/
  Buttons/toggles in a widget offer app functionality WITHOUT launching the
  app (canonical example: Reminders marks a task complete with a toggle).
  The most important actions belong in the widget. Mechanism: Button(intent:)
  / Toggle(isOn:intent:) backed by an AppIntent whose perform() runs in the
  widget-extension process; on return the system reloads the timeline, so
  state must be persisted to a store the timeline provider reads BEFORE
  perform() returns; errors must be handled, not rethrown, and the widget
  updated to show stale/failed state; Toggle reflects optimistically, so
  perform() must reconcile to the persisted truth (incl. failure rollback).
  Views that change should be marked invalidatableContent (used judiciously).
- ASOWin, "App Widgets and Live Activities for Engagement and ASO"
  https://www.asowin.com/blog/ios-widgets-live-activities-engagement/
  Since iOS 17 widgets can complete simple actions (e.g. checking off a
  habit) without opening the app; the winning shape is one-tap completion of
  the core task, taught at the moment of first value, with widget users'
  retention read against non-users in a controlled comparison.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, families:[], interactive_elements:[{kind,intent}]},
 core_action:{intent_exists, perform_does_real_work, opens_app_when_run,
              is_core_task, template_only_control_present},
 shared_state:{app_group_shared, widget_side_can_write, timeline_reads_same_store,
               state_written_before_perform_returns},
 feedback:{view_reflects_new_state, changed_views_invalidatable, error_path_updates_widget},
 routing:{widget_url_or_link_present, routes_to_specific_content},
 measurement:{interaction_event_defined, interaction_event_fired,
              split_by_family_or_widget, downstream_completion_joinable}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("IW-0 the widget surface is not inventoried (families and interactive elements are nowhere recorded; an unrecorded surface cannot be audited or fixed in order)")
    elems = inv.get("interactive_elements") or []
    core = d.get("core_action") or {}
    if not elems:
        fails.append("IW-1 no Button(intent:) / Toggle(isOn:intent:) in any home-screen widget family (every tap is a launcher tap; the core task cannot be completed where the user already looks, so the app-load dropout sits on the main intervention path)")
    if elems and not core.get("intent_exists"):
        fails.append("IW-1 interactive elements exist but are not backed by an AppIntent that performs the action (a tappable view without an intent performs nothing)")
    if core.get("template_only_control_present"):
        fails.append("IW-2 the only intent-backed control in the bundle is an untouched template (its perform() is a comment and its state is hardcoded; a template is not an interactive surface and must be replaced by the core action or removed)")
    if elems and not core.get("perform_does_real_work"):
        fails.append("IW-2 the core intent's perform() does no real work (empty / comment-only perform mutates no state; the tap is theatre)")
    if elems and not core.get("is_core_task"):
        fails.append("IW-2 the widget action is not the app's core task (Apple: make the app's MOST IMPORTANT actions available in the widget; a side action does not move the intervention)")
    if core.get("opens_app_when_run"):
        fails.append("IW-2 the completion intent sets openAppWhenRun (the action launches the app, so it is a deep link wearing a button's clothes, not an in-widget completion)")
    ss = d.get("shared_state") or {}
    if elems:
        if not ss.get("app_group_shared"):
            fails.append("IW-3 no App Group shared store (the intent runs in the extension process with a separate sandbox; without a shared container its writes are invisible to the app and the timeline)")
        if not ss.get("widget_side_can_write"):
            fails.append("IW-3 the widget-side store is read-only (the intent cannot persist the result of the interaction, so the reloaded timeline must show the pre-tap state)")
        if not ss.get("timeline_reads_same_store"):
            fails.append("IW-3 the timeline provider does not read the same store the intent writes (write and read are disconnected; the widget can never reflect the action)")
        if not ss.get("state_written_before_perform_returns"):
            fails.append("IW-3 state is not persisted before perform() returns (the system reloads the timeline on return; anything written after is invisible until an unrelated reload)")
    fb = d.get("feedback") or {}
    if elems:
        if not fb.get("view_reflects_new_state"):
            fails.append("IW-4 the widget view does not reflect the post-interaction state (the person cannot see that the action landed; an invisible completion teaches that tapping does nothing)")
        if not fb.get("error_path_updates_widget"):
            fails.append("IW-4 no error path updates the widget (perform() throws must be handled and the widget must show stale/failed state; a silent failure leaves an optimistic Toggle showing a completion that never happened)")
        if not fb.get("changed_views_invalidatable"):
            warns.append("IW-4 views that change on interaction are not marked invalidatableContent (on slow reloads, e.g. iPhone widgets on Mac, the person gets no waiting signal -- warning only)")
    rt = d.get("routing") or {}
    if not rt.get("widget_url_or_link_present"):
        fails.append("IW-5 no widgetURL / Link anywhere in the home widget (even the launcher tap cannot promise specific content; the tap lands wherever the app happens to open, so outside and inside are different experiences)")
    elif not rt.get("routes_to_specific_content"):
        fails.append("IW-5 the widget tap routes to a generic home / placeholder URL, not the specific content the widget shows (the widget displays one affirmation and the tap must land on that affirmation)")
    ms = d.get("measurement") or {}
    if ms.get("interaction_event_defined") and not ms.get("interaction_event_fired"):
        fails.append("IW-6 the widget-interaction event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'no interactions' forever)")
    if not ms.get("interaction_event_defined"):
        fails.append("IW-6 no widget-interaction event exists at all (widget taps/completions cannot be counted, so the surface Apple calls the strongest cannot be judged)")
    if not ms.get("split_by_family_or_widget"):
        fails.append("IW-6 interactions are not split by widget family / kind (which size completes and which only launches is unknowable; the family set can never be pruned or improved)")
    if not ms.get("downstream_completion_joinable"):
        fails.append("IW-6 widget interactions cannot be joined to the downstream completion (heard-in-full / 3-beat) and retention split (widget users vs non-users, ASOWin controlled comparison), so the widget's effect on behaviour is unmeasurable in principle)")
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
