#!/usr/bin/env python3
"""quick-action-check: deterministic gate for Home Screen quick actions.
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Apple HIG, Home Screen quick actions
  https://apple-docs.everest.mt/docs/design/human-interface-guidelines/home-screen-quick-actions/
  Create quick actions for compelling, high-value tasks; people expect at
  least one useful quick action; total of four. Avoid unpredictable changes
  to dynamic actions (update on location / recent activity / time of day /
  settings, in ways people can predict). Succinct title that instantly
  communicates the result; subtitle for context; no app name, keep short to
  avoid truncation, take localization into account. Familiar icon, prefer
  SF Symbols; never an emoji in place of a symbol.
- Diamantidis, How to Create Dynamic Quick Actions in iOS (2026-05-10)
  https://diamantidis.github.io/2026/05/10/how-to-create-dynamic-quick-actions-ios-swift
  Static = Info.plist UIApplicationShortcutItems, available from install,
  cannot adapt. Dynamic = UIApplicationShortcutItem assigned to
  UIApplication.shared.shortcutItems, adapts to user state. Registration
  alone does nothing: handling is required in BOTH states -- cold launch
  via connectionOptions.shortcutItem in scene(willConnectTo:) and running
  via windowScene(performActionFor:). Handler keys on shortcutItem.type
  and routes to the specific task.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, core_tasks:[]},
 actions:{static_defined, dynamic_defined, total_count,
   titles_succinct_no_app_name, icons_sf_symbols_not_emoji, localized},
 dynamic:{updates_only_on_meaningful_state_change, predictable_changes},
 handling:{cold_launch_handled, running_handled, routes_by_type,
   lands_on_specific_task},
 measurement:{event_defined, event_fired, per_type, joinable_to_completion}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("QA-0 quick actions are not inventoried (which core tasks deserve a Home Screen entry, and whether any action exists at all, are nowhere recorded; an unrecorded free surface cannot be audited -- Apple: people tend to expect every app to provide at least one useful quick action)")
    tasks = inv.get("core_tasks") or []
    if not tasks:
        fails.append("QA-0 no core task is named for a quick action (the app has obvious high-value tasks -- today's affirmation, checking a habit -- yet none is named; an action nobody names is an entry point that never gets built)")
    act = d.get("actions") or {}
    if not (act.get("static_defined") or act.get("dynamic_defined")):
        fails.append("QA-1 no quick action is defined at all (no UIApplicationShortcutItems in Info.plist and no UIApplicationShortcutItem assigned at runtime; long-pressing the icon offers only system items -- the free Home Screen entry does not exist)")
    else:
        total = act.get("total_count") or 0
        if total > 4:
            fails.append(f"QA-1 {total} quick actions are defined but the system shows a total of four (Apple HIG); the rest are dead definitions that create a false sense of coverage")
        if total == 0:
            fails.append("QA-1 actions are claimed defined but total_count is 0 (definition and count disagree; count is the ground truth)")
        if not act.get("titles_succinct_no_app_name"):
            fails.append("QA-1 titles are not verified succinct and app-name-free (Apple: a succinct title that instantly communicates the result, no app name or extraneous information, short enough to avoid truncation; a truncated or branded title fails at the exact glance it exists for)")
        if not act.get("icons_sf_symbols_not_emoji"):
            fails.append("QA-1 icons are not verified as SF Symbols / template icons (Apple: prefer SF Symbols, never use an emoji in place of a symbol -- emoji are full colour and break Dark Mode contrast)")
        if not act.get("localized"):
            warns.append("QA-1 quick action titles are not localized (Apple: take localization into account as you write the text; warning only, justification should be recorded)")
    dyn = d.get("dynamic") or {}
    if act.get("dynamic_defined"):
        if not dyn.get("updates_only_on_meaningful_state_change"):
            fails.append("QA-2 dynamic actions are not restricted to meaningful state changes (Apple: avoid unpredictable changes; update on recent activity / time of day / settings -- churning actions train users to ignore the menu)")
        if not dyn.get("predictable_changes"):
            fails.append("QA-2 dynamic action changes are not predictable to the user (Apple: make sure actions change in ways people can predict; a menu that reshuffles arbitrarily is worse than a static one)")
    hd = d.get("handling") or {}
    if act.get("static_defined") or act.get("dynamic_defined"):
        if not hd.get("cold_launch_handled"):
            fails.append("QA-3 cold-launch taps are not handled (no shortcutItem read from connectionOptions / launchOptions; Diamantidis: registration alone does nothing -- a tap from a terminated state just launches the app normally)")
        if not hd.get("running_handled"):
            fails.append("QA-3 taps while the app is already running are not handled (no performActionFor path; the second of the two lifecycle states Apple/Diamantidis require is missing)")
    else:
        fails.append("QA-3 no handling exists because no action exists (both lifecycle paths -- cold launch and already-running -- are absent together with the actions themselves)")
    if (act.get("static_defined") or act.get("dynamic_defined")):
        if not hd.get("routes_by_type"):
            fails.append("QA-3 handling does not route by shortcutItem.type (without type routing every action collapses into the same generic launch)")
        if not hd.get("lands_on_specific_task"):
            fails.append("QA-3 a quick action tap does not land on the specific task it promised (the whole value is skipping navigation; landing on the home feed re-imposes the friction the action was meant to remove)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("QA-4 the quick-action arrival event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'quick actions bring nobody' forever)")
    if not ms.get("event_defined"):
        fails.append("QA-4 no quick-action arrival event exists at all (without the app's own arrival event, this free surface's contribution is unknowable in principle)")
    if (act.get("static_defined") or act.get("dynamic_defined")) and not ms.get("per_type"):
        fails.append("QA-4 arrivals are not measured per action type (with up to four actions, an aggregate count cannot say which task earns its slot and which should be replaced)")
    if not ms.get("joinable_to_completion"):
        fails.append("QA-4 quick-action arrivals cannot be joined to downstream completion (session / habit completion / purchase), so whether Home Screen entry works cannot be judged")
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
