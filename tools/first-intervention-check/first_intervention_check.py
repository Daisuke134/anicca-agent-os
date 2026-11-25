#!/usr/bin/env python3
"""first-intervention-check: deterministic gate for the first intervention
(the "magic moment" first personalised affirmation after onboarding).

Sources read in full on 2026-11-14:
- ASOWin, "App Onboarding Best Practices: Reach Value in Session One"
  https://www.asowin.com/blog/app-onboarding-best-practices/
- UserOnBoarding Academy, "Advanced Guide to Creating Personalized
  Onboarding Experiences"
  https://useronboarding.academy/post/personalized-onboarding

Company rules fixed the same day (2026-11-14) and encoded here:
- The first intervention is "the words that person waited their whole
  life for" (14:59): after the onboarding answers, words/image/figure
  chosen FOR that person start appearing, within seconds / a few
  scrolls, so the person feels "this app understands me".
- Questions adapt: the next question changes with the previous answer
  (15:13). A fixed straight line is Phase 1 only.
- What is shown outside must exist inside (15:12, five-precepts rule).

Existing definitions are reused, not reinvented:
- value_complete stays the 3-beat completion fixed elsewhere
  (open -> today's affirmation -> listen to the end).
- TTV budgets stay in ttv-check (median 60s / p90 180s to value_start).
  This checker judges the SELECTION and PROOF of the first item, not
  the clock. It invents no new completion point and no new timer.

Gates:
  FI-0  Definition: the first intervention is defined as one named
        event, defined both qualitatively (what the person feels:
        words chosen for them) and quantitatively (a measurable
        action inside a time window), with an owner and the decision
        it informs (ASOWin/Reforge form: name the aha moment in plain
        words, pin it to a measurable action).
  FI-1  Validation: the definition was found by comparing retained
        vs churned users' first-session behaviour, and a causal test
        rule is recorded (if more people are pushed to this moment,
        does retention move?). A guessed moment fails.
  FI-2  Answer-to-effect mapping: every onboarding question asked
        before the first intervention has a recorded visible effect
        on what the user sees next; questions are skippable; why each
        question is asked is stated. Any question whose answer feeds
        only analytics/CRM, or changes nothing visible, fails
        (Academy rule 5: every answer must change something visible;
        ASOWin: a question that does not affect the experience is
        friction disguised as personalization).
  FI-3  Selection: the first item is SELECTED from the person's
        answers (at minimum goal + struggles/pain), not by calendar
        rotation, not a static text, not the same for everyone.
        Distinct answer-combinations produce distinct first items
        (distinct_outputs >= 2 recorded from a real audit), and a
        recorded fallback exists for skippers (skip must not mean
        "no personalisation and no path").
  FI-4  Immediacy and order: the result of the answers is shown
        immediately (ASOWin: show users the result of their answers
        immediately, e.g. a personalised plan or curated feed);
        at most one reveal/processing screen sits between the last
        answer and the first intervention; the paywall sits after
        the first intervention, not before it.
  FI-5  Visible reflection: the first intervention / its reveal
        visibly reflects the answers (selection differs per person
        AND the person can see why it is theirs). Name-insertion
        only, or a static insight/stat text shown to everyone,
        fails. Adaptive follow-up (the next question or the second
        item changes with the previous answer/reaction) is recorded.
  FI-6  Measurement: first-intervention reach rate is recorded
        (share of decontaminated real first opens that receive the
        selected first item in session 1), a distinctness audit is
        logged (how many distinct first items were actually served
        across segments), perceived-understanding is measured with a
        real signal (reaction / save / listen-to-end / survey), and
        retention is read split by reached vs not reached.
  FI-7  Promise pair: the first line/words shown outside (store,
        video, slideshow) that brought the person in are recorded
        as a pair with the inside first intervention, and that exact
        wording/experience exists inside as a servable first item.

Exit code 0 = PASS (no failures), 1 = FAIL. Warnings never fail alone.
"""
import json
import sys

FAILS = []
WARNS = []


def fail(gate, msg):
    FAILS.append(f"[{gate}] {msg}")


def warn(gate, msg):
    WARNS.append(f"[{gate}] {msg}")


def check(d):
    # FI-0 definition
    dfn = d.get("definition") or {}
    if not dfn.get("first_intervention_event"):
        fail("FI-0", "first intervention is not defined as one named event")
    if not dfn.get("qualitative_definition"):
        fail("FI-0", "no qualitative definition (what the person feels: words chosen for them, not a generic welcome)")
    if not dfn.get("owner"):
        fail("FI-0", "no owner recorded for the first-intervention metric")
    if not dfn.get("decision_informed"):
        fail("FI-0", "decision_informed is not recorded (what changes when the first item does not land?)")

    # FI-1 validation
    v = d.get("validation") or {}
    if not v.get("found_by_retained_vs_churned_comparison"):
        fail("FI-1", "the moment was not found by comparing retained vs churned users' first-session behaviour (ASOWin: find it in the data, do not guess it)")
    if not v.get("causal_test_rule_recorded"):
        fail("FI-1", "no causal test rule recorded (pushing more people to this moment must be tested against retention, not assumed)")
    if v.get("definition_is_assumed_untested"):
        fail("FI-1", "the definition is recorded as assumed/untested and treated as settled")

    # FI-2 answer-to-effect mapping
    a = d.get("answer_mapping") or {}
    qs = a.get("questions")
    if qs is None:
        fail("FI-2", "onboarding questions before the first intervention are not inventoried")
    elif not (3 <= qs <= 5):
        fail("FI-2", f"{qs} questions before the first intervention is outside the existing 3-5 range (OB-2); the primary sources use 1-3 light questions")
    mapped = a.get("questions_with_visible_effect")
    if qs is not None and mapped is None:
        fail("FI-2", "count of questions with a recorded visible effect is not recorded")
    elif qs is not None and mapped is not None and mapped < qs:
        fail("FI-2", f"only {mapped} of {qs} questions change something visible; every answer must change something the user sees (Academy rule 5)")
    if a.get("any_question_feeds_only_analytics_or_crm"):
        fail("FI-2", "at least one question feeds only analytics/CRM and changes nothing visible (ask it later, or not at all)")
    if not a.get("questions_skippable"):
        fail("FI-2", "questions are not skippable (Academy: make each question skippable)")
    if not a.get("why_asked_stated"):
        warn("FI-2", "why each question is asked is not stated to the user (Academy: say why you are asking)")

    # FI-3 selection
    s = d.get("selection") or {}
    if not s.get("selected_from_answers"):
        fail("FI-3", "the first item is not selected from the person's answers")
    if s.get("selected_by_calendar_rotation"):
        fail("FI-3", "the first item is selected by calendar/date rotation (the same item for everyone that day is not personalisation)")
    if s.get("is_static_same_for_everyone"):
        fail("FI-3", "the first item is a static text that is the same for everyone")
    used = s.get("answer_fields_used") or []
    for need in ("goals", "struggles"):
        if need not in used:
            fail("FI-3", f"selection does not use the '{need}' answer field")
    distinct = s.get("distinct_outputs_across_segments")
    if distinct is None:
        fail("FI-3", "distinct first items served across answer segments are not recorded (no distinctness audit)")
    elif distinct < 2:
        fail("FI-3", f"only {distinct} distinct first item(s) across segments; different answers must visibly produce different first items")
    if not s.get("fallback_for_skippers_recorded"):
        fail("FI-3", "no recorded fallback first item/path for users who skip the questions")

    # FI-4 immediacy and order
    im = d.get("immediacy") or {}
    if not im.get("result_shown_immediately_after_answers"):
        fail("FI-4", "the result of the answers is not shown immediately (ASOWin: show the result of their answers immediately)")
    between = im.get("screens_between_last_answer_and_first_item")
    if between is None:
        fail("FI-4", "screens between the last answer and the first item are not recorded")
    elif between > 1:
        fail("FI-4", f"{between} screens sit between the last answer and the first item; at most one reveal/processing screen is allowed")
    if im.get("paywall_before_first_intervention"):
        fail("FI-4", "the paywall sits before the first intervention (value before the ask)")

    # FI-5 visible reflection
    r = d.get("reflection") or {}
    if not r.get("reveal_visibly_reflects_answers"):
        fail("FI-5", "the reveal/first item does not visibly reflect the person's answers (the person cannot see why this is theirs)")
    if r.get("name_insertion_only"):
        fail("FI-5", "personalisation is name-insertion only (the basic form; the real form reacts to goals, pain and behaviour)")
    if r.get("reveal_is_static_localized_text"):
        fail("FI-5", "the reveal is static localised text shown identically to everyone (no answer is interpolated or selected on)")
    if not r.get("adaptive_followup_recorded"):
        fail("FI-5", "no adaptive follow-up recorded (next question / second item does not change with the previous answer or reaction; fixed straight line is Phase 1 only)")

    # FI-6 measurement
    m = d.get("measurement") or {}
    if m.get("first_intervention_reach_rate") is None:
        fail("FI-6", "first-intervention reach rate (share of real first opens receiving the selected first item in session 1) is not recorded")
    if not m.get("denominator_decontaminated_real_first_opens"):
        fail("FI-6", "denominator is not recorded as decontaminated real first opens")
    if not m.get("distinctness_audit_logged"):
        fail("FI-6", "no distinctness audit is logged (which distinct first items were actually served, per segment)")
    if not m.get("perceived_understanding_measured"):
        fail("FI-6", "perceived understanding is not measured with a real signal (reaction/save/listen-to-end/survey); impressions alone do not prove the person felt understood")
    if not m.get("retention_split_by_reached"):
        fail("FI-6", "retention is not read split by reached vs not reached the first intervention")
    if m.get("completion_rate_used_as_sole_success"):
        fail("FI-6", "onboarding completion rate is used as the sole success metric (ASOWin: measure activation, not tutorial completion)")

    # FI-7 promise pair
    pm = d.get("promise_pair") or {}
    if not pm.get("outside_inside_pair_recorded"):
        fail("FI-7", "the outside promise and the inside first intervention are not recorded as a pair")
    if pm.get("shown_outside_not_servable_inside"):
        fail("FI-7", "words/experience shown outside cannot be served inside as a first item (outside must exist inside)")
    if not pm.get("entry_wording_servable_as_first_item"):
        warn("FI-7", "entry wording being servable as a first item is not positively recorded")


def main():
    if len(sys.argv) != 2:
        print("usage: first_intervention_check.py <first-intervention-state.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    check(d)
    for w in WARNS:
        print(f"WARN  {w}")
    for f_ in FAILS:
        print(f"FAIL  {f_}")
    print(f"RESULT: {'PASS' if not FAILS else 'FAIL'} ({len(FAILS)} failures, {len(WARNS)} warnings)")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
