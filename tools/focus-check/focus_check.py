#!/usr/bin/env python3
"""focus-check: deterministic gate for iOS Focus Filters
(Settings > Focus > [mode] > Focus Filters, via SetFocusFilterIntent).
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Apple Sample Code, Defining your app's Focus filter
  https://www.applesamplecode.com/App%20Intents/Defining%20your%20app%E2%80%99s%20Focus%20filter.html
  Purpose: customize the app's behavior to reflect the device's current
  Focus. The filter type conforms to SetFocusFilterIntent, lives in an
  AppIntents extension, shares an AppDataModel with the app, and offers
  suggestedFocusFilters(for:) so the system can propose ready-made
  configurations per Focus.
- Soarias, How to Implement a Focus Filter in SwiftUI (full read,
  reviewed 2026-05-11)
  https://www.soarias.com/swiftui/how-to-implement-focus-filter/
  Conform a struct to FocusFilterIntent, declare @Parameter knobs users
  set per Focus in Settings, the system calls perform() when a matching
  Focus activates, and the app reads `Filter.current` to adjust behavior.
  perform() runs in a short-lived extension process: persist the config
  to a shared App Group suite, never to in-memory state or a private
  defaults domain. Re-read .current on didBecomeActive (Focus can change
  while backgrounded; no polling). No-filter must reset to defaults.
  FocusFilterIntent shipped in iOS 16; DynamicOptionsProvider and the
  async .current behave reliably on iOS 17+, so older targets need a
  recorded fallback. If a filter hides content, show a visible
  explanation (ContentUnavailableView / banner) -- never hide silently.
- Apple user guidance via UMA Technology (full read of search extract)
  http://umatechnology.org/how-to-use-focus-filters-to-customize-apps-while-a-focus-is-on/
  Filters change what information an app shows; they are separate from
  notification permissions and do not themselves silence notifications.
  Focus settings can share across devices, but Focus Filters themselves
  do NOT sync across devices -- setup is per device.
- Practitioner examples (iMore, full read of search extract)
  https://www.imore.com/apps/ios-16s-sleeper-hit-focus-filters
  CardPointers shows business cards in Work Focus and personal cards in
  Personal Focus; Fantastical limits displayed calendars per Focus;
  Drafts tailors workspaces per context. The pattern is one app, whose
  content set changes with the person's context -- not a second app.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, context_modes:[], filterable_content:[]},
 definition:{defined, title_specific, description_accurate,
   parameters_are_real_content_knobs, parameters_have_defaults,
   suggested_filters_offered},
 activation:{perform_does_real_work, perform_persists_to_shared_suite,
   perform_uses_standard_defaults_only},
 reading:{app_reads_current, reread_on_foreground, no_filter_resets_defaults,
   content_actually_branches, visible_indication_when_filtered},
 availability:{deployment_covers_filter_base, fallback_decision_recorded,
   per_device_setup_guidance_in_app},
 truth_privacy:{claims_notification_silencing, no_sensitive_content_forced,
   parameters_expose_private_content},
 measurement:{event_defined, event_fired, per_mode, joinable_to_completion}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("FF-0 Focus Filters are not inventoried (which Focus contexts -- Sleep, Mindfulness, Work, Personal -- should change what this app shows, and what exists today, are nowhere recorded; an unrecorded system surface cannot be audited)")
    if not (inv.get("context_modes") or []):
        fails.append("FF-0 no Focus context mode is named (for a suffering/affirmation app the obvious modes are Sleep -- tonight's calming words only, nudges quiet -- and Mindfulness/Personal -- the one thing needed now; Apple/practitioners: the filter's whole value is content that changes with context)")
    if not (inv.get("filterable_content") or []):
        fails.append("FF-0 no filterable content set is named (a filter needs something real to filter -- e.g. affirmations by problem type, habit list, nudge cadence; naming none means the surface has nothing to act on even if defined)")
    dfn = d.get("definition") or {}
    defined = bool(dfn.get("defined"))
    if not defined:
        fails.append("FF-1 no Focus Filter is defined at all (no SetFocusFilterIntent / FocusFilterIntent anywhere; the app never appears in Settings > Focus > Focus Filters, so a person who lives in Sleep or Mindfulness Focus gets the identical app as at noon -- the context surface is absent)")
    else:
        if not dfn.get("title_specific"):
            fails.append("FF-1 the filter title is not specific to what it changes (the title is what a person reads in Settings > Focus > Add Filter; a generic or app-name-only title cannot be chosen deliberately)")
        if not dfn.get("description_accurate"):
            fails.append("FF-1 the filter description is missing or inaccurate (the description is shown at configuration time; placeholder text there is a false promise at the exact moment of adoption)")
        if not dfn.get("parameters_are_real_content_knobs"):
            fails.append("FF-1 the @Parameter knobs are not real content knobs (parameters must change what the app shows or does -- content theme, quiet nudges, which habits -- not decorative flags nothing reads)")
        if not dfn.get("parameters_have_defaults"):
            fails.append("FF-1 a parameter has no default (Apple sample/Soarias: every @Parameter carries a default so an unconfigured Focus behaves as the unfiltered app, never as a broken one)")
        if not dfn.get("suggested_filters_offered"):
            fails.append("FF-1 no suggestedFocusFilters are offered (Apple's sample provides suggested configurations per context so adoption is one tap in Settings; without suggestions each person must invent the configuration, and most never do)")
    act = d.get("activation") or {}
    if defined:
        if not act.get("perform_does_real_work"):
            fails.append("FF-2 perform() does no real work (activation that only returns .result() means the Focus turns on and the app learns nothing -- the filter is decoration)")
        if not act.get("perform_persists_to_shared_suite"):
            fails.append("FF-2 perform() does not persist the configuration to the shared App Group suite (Soarias/Apple: perform() runs in a short-lived extension process; in-memory or private state is unreachable from the app, so the filter silently never applies)")
        if act.get("perform_uses_standard_defaults_only"):
            fails.append("FF-2 perform() persists only to UserDefaults.standard (the extension's standard defaults are not the app's; the shared suite is the wire, exactly as with widgets and controls)")
    else:
        fails.append("FF-2 no filter activation exists at all (no perform() runs when a Focus with this app's filter turns on)")
    rd = d.get("reading") or {}
    if defined:
        if not rd.get("app_reads_current"):
            fails.append("FF-3 the app never reads Filter.current (a persisted configuration nobody reads changes nothing; reading .current is the only bridge from Settings to the home screen)")
        if not rd.get("reread_on_foreground"):
            fails.append("FF-3 the app does not re-read the filter when it returns to the foreground (Focus can be toggled while the app is backgrounded; Soarias: re-read on didBecomeActive, no polling)")
        if not rd.get("no_filter_resets_defaults"):
            fails.append("FF-3 the no-filter case does not reset to defaults (when no matching Focus is active, .current throws/absents and the app must fall back to the unfiltered experience; a stale filter left applied after Focus ends is a lying app state)")
        if not rd.get("content_actually_branches"):
            fails.append("FF-3 no content or behavior actually branches on the filter (reading a value that no selection, cadence, or screen consults is measurement theatre, not a filter)")
        if not rd.get("visible_indication_when_filtered"):
            fails.append("FF-3 filtered content is hidden with no visible indication (Soarias accessibility rule: if a filter narrows what is shown, say so on screen; silently missing words or habits reads as data loss)")
    else:
        fails.append("FF-3 nothing in the app can react to Focus at all (no .current read, no content branch; the person's context never reaches the one screen that is supposed to show the one thing needed now)")
    av = d.get("availability") or {}
    if not av.get("deployment_covers_filter_base"):
        fails.append("FF-4 the deployment targets / availability handling do not cover the filter's base OS (FocusFilterIntent is iOS 16+, .current/DynamicOptionsProvider are reliable on iOS 17+; mixed targets of 15.0/16.0/16.6 with no gating or fallback is a build/behavior accident, not a decision)")
    if not av.get("fallback_decision_recorded"):
        fails.append("FF-4 no recorded decision covers users below the reliable filter base or without any Focus configured (the unfiltered experience must be the deliberate default, recorded as such)")
    if defined and not av.get("per_device_setup_guidance_in_app"):
        fails.append("FF-4 the app gives no in-app guidance that Focus Filters are set per device in Settings > Focus (Apple: filters do not sync across devices even with Share Across Devices on; without guidance, a person who set it on one phone concludes it is broken on the other)")
    tp = d.get("truth_privacy") or {}
    if tp.get("claims_notification_silencing"):
        fails.append("FF-5 the filter claims to silence notifications (Apple user guidance: filters change what information an app shows; they are separate from notification permissions and do not silence notifications -- claiming otherwise is a false promise)")
    if defined and not tp.get("no_sensitive_content_forced"):
        fails.append("FF-5 the filter can force sensitive content into a context the person did not choose for it (a Work Focus must never surface private journal/affirmation text by default; parameters choose content sets, they do not leak them)")
    if tp.get("parameters_expose_private_content"):
        fails.append("FF-5 a parameter exposes private content in Settings (parameter titles/options are visible in system Settings outside the app; private problem types or journal labels there are a disclosure)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("FF-6 the focus-filter event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'Focus brings nobody' forever)")
    if not ms.get("event_defined"):
        fails.append("FF-6 no focus-filter applied/arrival event exists at all (the system reports nothing back, so without the app's own event this free surface's contribution is unknowable in principle)")
    if defined and not ms.get("per_mode"):
        fails.append("FF-6 filter use is not measured per Focus mode / parameter set (an aggregate count cannot say whether Sleep or Mindfulness is the mode worth designing for)")
    if not ms.get("joinable_to_completion"):
        fails.append("FF-6 filter-applied sessions cannot be joined to downstream completion (session heard / habit checked), so whether context-matched content works cannot be judged")
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
