#!/usr/bin/env python3
"""Proactive home Gate checker (PH-0..PH-7). Stdlib only, deterministic, offline.
Sources (full-read 2026-11-14):
- PagePerson 'Avoiding Cognitive Overload in Mobile App Interfaces'
  https://www.pageperson.org/blog/avoid-cognitive-overload-mobile-apps/
  Calm home = one daily recommendation + a simple play button + a short
  greeting; the rest of the library lives behind a single tab; users start
  a session without scanning a grid of 30 options. One primary action per
  screen: if a screen has two equally prominent buttons, neither gets
  clicked reliably. Progressive disclosure, bottom tab bar <=5 labelled
  items, hierarchy <=2 levels, one accent colour, 5-second test (show the
  screen 5s; if the person cannot recall the primary action it is too busy),
  onboarding teaches by doing (Headspace: one sentence + one button).
- Digia 'Duolingo's Habit-Forming Reminders: A UX Breakdown'
  https://www.digia.tech/post/duolingo-habit-forming-reminders-retention-architecture/
  (practitioner teardown, secondary): home shows streak + next lesson as a
  persistent state display, not a modal interruption; one lesson/exercise
  at a time with non-relevant features hidden; routine vs save are two
  distinct slots, hard cap 2 pushes/day; every push must clear a behavioural
  or state trigger; timing reads revealed behaviour, not a user-set time
  from weeks ago; urgency escalates only as real risk rises.
House product direction (2026-11-14 00:35, MEMORY): the product is
proactive, not a feed -- open it and the one thing that person needs now
is already selected. Selection material is the same as the personalized
nudge: (1) measured reaction history, (2) onboarding answers.
House rule (2026-11-14): a found best practice beats an original idea.
"""
import json, sys

def check(d):
    fails, warns = [], []
    # PH-0 existence + selection rule recorded, feed is not the default
    if d.get("proactive_home_implemented") is not True:
        fails.append("PH-0: proactive home (one selected intervention on open) is not implemented")
    if d.get("selection_rule_recorded") is not True:
        fails.append("PH-0: the rule that selects the one intervention is not recorded (cannot audit or eval an unrecorded selector)")
    if d.get("default_surface") != "selected_one":
        fails.append(f"PH-0: default surface on open is {d.get('default_surface')!r}, not 'selected_one' (a feed/list/grid as default is the rejected form)")
    # PH-1 exactly one primary action (PagePerson / Calm form)
    pa = d.get("primary_actions_on_home")
    if pa is None:
        fails.append("PH-1: primary-action count on home not recorded")
    elif pa != 1:
        fails.append(f"PH-1: home has {pa} primary actions, not exactly 1 (two equally prominent buttons: neither gets clicked reliably)")
    if d.get("equally_prominent_ctas") is None:
        fails.append("PH-1: equally-prominent CTA count not recorded")
    elif (d.get("equally_prominent_ctas") or 0) > 1:
        fails.append(f"PH-1: {d.get('equally_prominent_ctas')} equally prominent CTAs compete on home (must be 1)")
    if d.get("library_behind_single_tab") is not True:
        fails.append("PH-1: full library/content is not behind a single tab (Calm form: library behind one tab, not on home)")
    # PH-2 selection inputs: BOTH reaction history and onboarding answers, with fallback
    s = d.get("selection") or {}
    if s.get("uses_reaction_history") is not True:
        fails.append("PH-2: selection does not use the person's measured reaction history")
    if s.get("uses_onboarding_answers") is not True:
        fails.append("PH-2: selection does not use onboarding answers (collected but unused, or never collected)")
    if s.get("stored_per_user") is not True:
        fails.append("PH-2: selection inputs are not stored per user")
    fb = s.get("fallback_when_no_history")
    if fb == "blank_or_feed":
        fails.append("PH-2: users with no history get a blank screen or the feed (fallback must select the general-best / onboarding-based one, never drop to a feed)")
    elif fb != "general_best_or_onboarding":
        fails.append("PH-2: no recorded fallback for new users (general-best or onboarding-based selection)")
    if s.get("recomputed_on_state_change") is not True:
        warns.append("PH-2: selection is not recorded as recomputed when the person's state changes (a stale selection is a broadcast in disguise)")
    # PH-3 no choice grid before the action
    v = d.get("visible_options_before_action")
    if v is None:
        fails.append("PH-3: visible options before the primary action not recorded")
    elif v > 3:
        fails.append(f"PH-3: {v} options are visible before the primary action (Calm form is 1 recommendation; a grid of 30 is the documented failure form; ceiling here is 3 incl. the selected one)")
    tabs = d.get("tab_bar_items")
    if tabs is None:
        fails.append("PH-3: tab-bar item count not recorded")
    elif tabs > 5:
        fails.append(f"PH-3: tab bar has {tabs} items, over the 5-item working-memory ceiling")
    depth = d.get("hierarchy_depth_to_core")
    if depth is None:
        fails.append("PH-3: hierarchy depth to the core action not recorded")
    elif depth > 2:
        fails.append(f"PH-3: core action is {depth} levels deep, over the 2-level ceiling")
    if d.get("progressive_disclosure_for_secondary") is not True:
        fails.append("PH-3: secondary options are not behind progressive disclosure (they compete on home)")
    # PH-4 state shown persistently, no modal interruption, urgency matches real state
    st = d.get("state_display") or {}
    if st.get("persistent_state_on_home") is not True:
        fails.append("PH-4: the person's current state/progress is not shown as a persistent display on home (Duolingo form: streak/progress visible without a message)")
    if st.get("modal_reminder_on_open") is True:
        fails.append("PH-4: a modal reminder interrupts on open (Duolingo form: persistent display does the work; a modal that tells users what they can already see erodes the session)")
    if st.get("urgency_matches_real_state") is not True:
        fails.append("PH-4: urgency on home does not match real state (flat urgency = everything urgent, so nothing is; save-type urgency only when something is genuinely about to be lost)")
    if st.get("includes_rest_or_no_action_state") is not True:
        fails.append("PH-4: home has no rest / no-action state (when the right intervention is none -- already done today, or rest -- the selector must be able to select nothing)")
    # PH-5 one tap to a short completion
    taps = d.get("taps_from_open_to_start")
    if taps is None:
        fails.append("PH-5: taps from open to starting the selected intervention not recorded")
    elif taps > 1:
        fails.append(f"PH-5: {taps} taps from open to start, over the 1-tap Calm play-button form")
    mins = d.get("selected_action_minutes")
    if mins is None:
        fails.append("PH-5: duration of the selected intervention not recorded")
    elif not (1 <= mins <= 5):
        fails.append(f"PH-5: selected intervention takes {mins} min, outside the 1-5 min short-completion band (Duolingo lesson ~3 min; onboarding quick win 2-4 min)")
    if d.get("one_exercise_at_a_time") is not True:
        fails.append("PH-5: the intervention itself does not present one step at a time with non-relevant features hidden")
    # PH-6 measurement: eligible opens denominator, control, 5-second test, harm side
    m = d.get("measurement") or {}
    if m.get("denominator_is_eligible_opens") is not True:
        fails.append("PH-6: headline completion rate does not use eligible opens as the denominator")
    if m.get("compares_proactive_vs_feed_or_list") is not True:
        fails.append("PH-6: proactive home is never compared against a feed/list control (no evidence the selection itself helps)")
    if m.get("five_second_test_passed") is not True:
        fails.append("PH-6: 5-second test not passed/recorded (show home 5s; the person must be able to recall the primary action)")
    if m.get("tracks_completion_and_retention_and_dismissal") is not True:
        fails.append("PH-6: judgement reads starts alone, without completion + retention + dismissal/opt-out beside it")
    # PH-7 selector accountability + ground truth
    ev = d.get("evaluation") or {}
    if ev.get("selection_logged_with_reason") is not True:
        fails.append("PH-7: each selection is not logged with its inputs/reason (an unlogged selector cannot be evaluated or improved -- Data pillar missing)")
    if ev.get("real_reaction_is_ground_truth") is not True:
        fails.append("PH-7: simulated/predicted reactions are treated as ground truth (house rule: real measured reactions only; simulation is scaffolding)")
    if ev.get("method") not in ("mrt_wcls", "controlled_cohort"):
        fails.append("PH-7: proactive-vs-control effect is not judged by a causal method (MRT with WCLS, or a controlled cohort)")
    return fails, warns

def main():
    if len(sys.argv) != 2:
        print("usage: proactive_home_check.py <fixture.json>"); return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    fails, warns = check(d)
    for w in warns:
        print(f"WARN: {w}")
    for x in fails:
        print(f"FAIL: {x}")
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
