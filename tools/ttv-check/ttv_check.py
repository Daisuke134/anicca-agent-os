#!/usr/bin/env python3
"""ttv-check: deterministic gate for time-to-first-value (TTV) design.

Sources read in full on 2026-11-14:
- Eleken, "Mobile App Onboarding Best Practices [2026 Guide]"
  https://www.eleken.co/blog-posts/mobile-app-onboarding-best-practices
- Purchasely, "App onboarding: The ultimate guide for 2026"
  https://www.purchasely.com/blog/app-onboarding

Input: a JSON description of an app's first-session design and its
TTV measurement record. This checker judges that record only. It does
not run the app, and a PASS here never means users actually stay.

Definitions used by every gate:
- value_start: the moment the first personalised core value *starts*
  (for Anicca: the first personalised affirmation is on screen and
  playback starts). A stat, a plan reveal or a feature tour is not
  value_start.
- value_complete: the existing activation point, unchanged. For Anicca
  that is the 3-beat completion already fixed elsewhere
  (open -> today's affirmation -> listen to the end). This checker
  invents no new completion point.

Gates:
  TTV-0  Definition: value_start and value_complete are each defined as
         one named event, an owner and the decision the metric informs
         are recorded, and a retention hypothesis for the completion
         point is recorded (Eleken: find the single action that most
         strongly predicts retention, work backward from it).
  TTV-1  Measurement: median and p90 elapsed seconds from first open
         to value_start are recorded, the first-session activation
         rate is recorded, and the denominator is decontaminated real
         first opens (not team / simulator / test devices).
  TTV-2  Speed: median TTV <= 60s and p90 TTV <= 180s. (The
         under-a-minute norm: Eleken tracks TTV alongside the aha
         moment; Duolingo-type flows reach the first lesson in
         60-90s in the secondary teardowns recorded in the spec.)
  TTV-3  Obstacles: every step before value_start is inventoried, and
         no step that does not move the user toward first value sits
         before it: no signup/account, no notification-permission ask,
         no profile completion, no feature tour before value_start
         (Eleken, verbatim rule: those can all come later).
  TTV-4  Visible personalisation: the questions asked before
         value_start are few (<=5, matching the existing OB-2 range),
         and the answers visibly change the first value itself.
         Collecting answers that never influence anything fails
         (Eleken: if a user's answers never appear to influence
         anything, they notice).
  TTV-5  Paywall order: the paywall sits after value_start, not
         before any value was experienced (Purchasely: showing a
         paywall before the user has experienced any value is a
         gamble that rarely pays off; place it toward the end, after
         a preview of the app's value).
  TTV-6  Celebration and repetition: the first meaningful action is
         acknowledged/celebrated, and a second value moment is
         prompted inside the first session or on Day 0 (Purchasely:
         experiencing value once is not enough to form a habit;
         onboarding must connect to repeated value).
  TTV-7  Judgement: retention (D1/D7) is read split by reached vs not
         reached value_complete and by TTV bucket, and onboarding
         completion alone is never the success metric (Purchasely:
         if completion does not predict retention/activation, the
         flow is optimised for the wrong thing). A recorded rule to
         revisit the definition when activation does not predict
         retention is required.
  TTV-8  Promise match: the first value inside the app is the same
         experience/wording that the store page and distribution
         showed to bring the user in, and the outside/inside pair is
         recorded (Purchasely/Carvell golden rule: deliver a
         consistent message; the company's own 2026-11-14 rule:
         what is shown outside must actually exist inside).

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
    # TTV-0 definition
    dfn = d.get("definition") or {}
    if not dfn.get("value_start_event"):
        fail("TTV-0", "value_start event is not defined (when does first value start?)")
    if not dfn.get("value_complete_event"):
        fail("TTV-0", "value_complete (activation) event is not defined")
    if not dfn.get("owner"):
        fail("TTV-0", "no owner recorded for the TTV metric")
    if not dfn.get("decision_informed"):
        fail("TTV-0", "decision_informed is not recorded (what changes when TTV is slow?)")
    if not dfn.get("retention_hypothesis_recorded"):
        fail("TTV-0", "no retention hypothesis recorded for the completion point (is it the action that predicts retention?)")

    # TTV-1 measurement
    m = d.get("measurement") or {}
    median = m.get("median_ttv_seconds")
    p90 = m.get("p90_ttv_seconds")
    if median is None:
        fail("TTV-1", "median TTV (first open -> value_start) is not recorded")
    if p90 is None:
        fail("TTV-1", "p90 TTV is not recorded; a median alone hides the slow tail that churns")
    if m.get("first_session_activation_rate") is None:
        fail("TTV-1", "first-session activation rate (share reaching value_complete in session 1) is not recorded")
    if not m.get("denominator_decontaminated_real_first_opens"):
        fail("TTV-1", "denominator is not recorded as decontaminated real first opens (team/simulator/test traffic inflates the base)")

    # TTV-2 speed
    if median is not None and median > 60:
        fail("TTV-2", f"median TTV {median}s exceeds the under-a-minute bar (60s)")
    if p90 is not None and p90 > 180:
        fail("TTV-2", f"p90 TTV {p90}s exceeds 180s; one in ten users waits over three minutes for first value")

    # TTV-3 obstacles
    ob = d.get("obstacles") or {}
    if not ob.get("steps_before_value_inventoried"):
        fail("TTV-3", "steps before value_start are not inventoried (unlisted steps cannot be removed)")
    n = ob.get("non_value_steps_before_value")
    if n is None:
        fail("TTV-3", "count of non-value steps before value_start is not recorded")
    elif n > 0:
        fail("TTV-3", f"{n} step(s) before value_start do not move the user toward first value")
    if ob.get("signup_before_value"):
        fail("TTV-3", "signup/account creation is required before first value (ask as little as possible, as late as possible)")
    if ob.get("notification_permission_before_value"):
        fail("TTV-3", "notification permission is asked before first value (Eleken: notification setup can come later)")
    if ob.get("profile_completion_before_value"):
        fail("TTV-3", "profile completion is required before first value")
    if ob.get("feature_tour_before_value"):
        fail("TTV-3", "a feature tour sits before first value (tours are passive and hard to remember)")

    # TTV-4 visible personalisation
    p = d.get("personalisation") or {}
    q = p.get("questions_before_value")
    if q is None:
        fail("TTV-4", "number of questions before value_start is not recorded")
    elif q > 5:
        fail("TTV-4", f"{q} questions before first value exceeds the existing 3-5 question range (OB-2)")
    if not p.get("answers_visibly_change_first_value"):
        fail("TTV-4", "answers do not visibly change the first value itself (collecting answers that influence nothing is noticed by users)")
    if p.get("first_value_is_static_generic"):
        fail("TTV-4", "the first value is a static generic text/insight that is the same for every user")
    if not p.get("questions_adapt_to_previous_answers"):
        fail("TTV-4", "questions do not adapt to previous answers (a fixed identical question sequence for everyone; Eleken: use branching logic so the next step follows the person's situation — and the company's 2026-11-14 rule fixes adaptive questions as the next form, with fixed questions recorded as Phase 1 only)")

    # TTV-5 paywall order
    pw = d.get("paywall") or {}
    if pw.get("paywall_before_value_start"):
        fail("TTV-5", "paywall is shown before first value starts (before any value was experienced)")
    if not pw.get("paywall_after_value_preview_or_start"):
        fail("TTV-5", "paywall placement after a value preview/start is not recorded")

    # TTV-6 celebration and repetition
    c = d.get("celebration_repetition") or {}
    if not c.get("first_action_acknowledged"):
        fail("TTV-6", "the first meaningful action is not acknowledged/celebrated (no completion moment recorded)")
    if not c.get("second_value_moment_prompted_first_session_or_day0"):
        fail("TTV-6", "no second value moment is prompted in the first session or on Day 0 (one exposure does not form a habit)")

    # TTV-7 judgement
    j = d.get("judgement") or {}
    if not j.get("retention_split_by_activation"):
        fail("TTV-7", "retention is not read split by reached vs not reached activation")
    if not j.get("retention_split_by_ttv_bucket"):
        fail("TTV-7", "retention is not read split by TTV bucket (slow-first-value cohorts are invisible)")
    if j.get("completion_rate_used_as_sole_success"):
        fail("TTV-7", "onboarding completion rate is used as the sole success metric (a red herring when it does not predict activation/retention)")
    if not j.get("definition_revisit_rule_recorded"):
        fail("TTV-7", "no recorded rule to revisit the activation definition when activation does not predict retention")

    # TTV-8 promise match
    pm = d.get("promise_match") or {}
    if not pm.get("outside_inside_pair_recorded"):
        fail("TTV-8", "the outside promise (store/distribution) and the inside first value are not recorded as a pair")
    if pm.get("shown_outside_not_present_inside"):
        fail("TTV-8", "something shown outside (wording/experience in video, slideshow or store page) does not exist inside the app")
    if not pm.get("first_value_matches_entry_promise"):
        warn("TTV-8", "first-value match with the entry promise is not positively recorded")


def main():
    if len(sys.argv) != 2:
        print("usage: ttv_check.py <ttv-state.json>")
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
