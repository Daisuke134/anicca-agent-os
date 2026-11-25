#!/usr/bin/env python3
"""motivation-peak-check: gate for the SEQUENCE before the first paywall -
JTBD capture, micro-commitments, a single personal aha, paywall timed to
the motivation peak, and the goal echoed on the paywall.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Source (read in full 2026-11-24):
- Airbridge, "App Onboarding Before Paywall: 5 Steps"
  https://www.airbridge.io/en/blog/5-steps-app-onboarding-before-the-paywall
  82% of trial starts happen on Day 0 (RevenueCat State of Subscription
  Apps 2025, cited there); onboarding+trial is the top configuration at
  1.78% install-to-conversion (Adapty State of In-App Subscriptions 2026,
  cited there). Conversion = motivation x trust / friction. Sequence:
  (1) capture the job-to-be-done in the first 30s with ONE goal question
  (Duolingo: goal+commitment in first 3 screens, MAU-to-paid ~4% -> >9%
  2020-2025, investor-relations figure cited there); (2) 2-3 interactive
  micro-commitments BEFORE value (Noom: 100+ screens / 10-15 min of
  invested effort before pricing); (3) ONE clear personal aha before the
  paywall (Headspace: a real 3-min session, paywall right after noticing
  the shift); (4) paywall IMMEDIATELY after the aha - run the 3-check
  (intent expressed? value experienced? paywall moves forward, not
  blocks?) - if any is no, it is too early; the moment should feel
  inevitable; (5) echo the Step-1 goal in the paywall headline (one
  string match beats most layout tests). On the screen: outcome first,
  value second, reassurance third, price fourth, CTA last; trust signals
  matched to the user's goal, not generic quotes; a building/loading
  screen is the paywall's opening argument only when it signals real
  personalised work. Most apps run BOTH an onboarding paywall and a
  contextual paywall; late converters retain better, so read quality by
  cohort, not Day-0 volume alone.
Separation: install-paid-check owns outcome judging (install-to-paid);
contextual-trigger-check owns later/contextual triggers;
answer-persistence-check owns saving/reusing answers;
flow-navigation-check owns navigation mechanics. This gate owns only
the ORDER and TIMING of the first-paywall sequence.
"""
import json, sys
CHECKS=[
 ("sequence_map_recorded","MPS-0 no recorded first-paywall sequence map (every step before the first paywall, in order, with its job; an unmapped sequence cannot be re-timed)"),
 ("jtbd_single_goal_question_first_30s","MPS-0 no single job-to-be-done goal question in the first ~30 seconds / first screens (Airbridge Step 1: one goal question - 'what are you trying to achieve?' - not a feature wishlist; one question per screen)"),
 ("micro_commitments_2_to_3_before_value","MPS-1 fewer than 2-3 micro-commitments before the value moment (Airbridge Step 2: a slider, a short quiz, a preference pick - small interactive steps build the emotional investment that makes leaving feel like abandoning started work)"),
 ("micro_commitments_are_interactive","MPS-1 the pre-value steps are passive screens, not interactive commitments (taps/choices the user makes; passive benefit slides do not create investment)"),
 ("aha_single_outcome_defined","MPS-2 no single defined aha outcome for the first paywall (Airbridge Step 3: one most-compelling outcome for this user, not a feature tour)"),
 ("aha_reflects_stated_goal","MPS-2 the aha/preview does not reflect the user's stated goal (a generic benefit statement wastes Steps 1-2; the preview must be built from this user's answers)"),
 ("aha_delivered_before_paywall","MPS-2 the aha is not guaranteed delivered/experienced before the first paywall (value seen or felt first - Headspace delivers a real session before asking)"),
 ("three_check_passes_before_paywall","MPS-3 the recorded 3-check does not pass before the paywall (intent expressed? value experienced? paywall moves the user forward rather than blocking progress? - any 'no' means too early)"),
 ("paywall_immediately_after_aha","MPS-3 the paywall does not appear immediately after the aha (not 3 screens later, not after account creation; delay lets the motivation peak decay)"),
 ("no_friction_inserted_at_peak","MPS-3 friction is inserted at the peak (account wall, permission cluster or extra forms between the aha and the paywall - conversion = motivation x trust / friction, and friction at the peak is the most expensive kind)"),
 ("paywall_headline_echoes_goal","MPS-4 the paywall headline does not echo the user's stated goal (Airbridge Step 5 / one-question rule: a single string match from the goal screen outperforms most layout experiments)"),
 ("paywall_order_outcome_first_price_last","MPS-4 the paywall information order is not outcome -> value -> reassurance -> price -> CTA (leading with price creates a friction spike before evaluation finishes)"),
 ("trust_signals_matched_to_goal","MPS-4 trust signals are generic, not matched to the user's goal/segment (generic superlatives reduce trust; matched proof answers 'will this work for me?')"),
 ("building_screen_signals_real_work","MPS-4 any pre-paywall building/loading screen does not signal real personalised work from the user's inputs (a filler wait is not an opening argument; never fabricate work that did not happen)"),
 ("both_paywall_types_decided","MPS-5 no recorded decision on running BOTH an onboarding paywall and a contextual paywall (onboarding captures the Day-0 majority; contextual captures users who need more time - one alone leaves a cohort unserved)"),
 ("sequencing_tested_before_copy_design","MPS-5 paywall underperformance is being treated as a copy/design problem before sequencing is tested (Airbridge: most of the time it is a sequencing problem; the fix is upstream, timing beats design)"),
 ("day0_window_owned","MPS-5 the Day-0 window is not explicitly owned (82% of trial starts happen on Day 0; once the first session ends without a start there is no recovery mechanism in this sequence)"),
 ("late_converter_quality_read_separately","MPS-5 late converters are not read separately for quality/retention (late converters retain better than Day-0 converters; Day-0 volume alone misjudges the contextual cohort)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: motivation_peak_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
