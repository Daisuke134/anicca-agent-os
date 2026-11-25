#!/usr/bin/env python3
"""anchor-check: gate for anchoring a new tiny behaviour to an existing
reliable routine (Tiny Habits ABC: Anchor-Behaviour-Celebration) in a
behaviour app - the anchor must be a discrete completed action the user
already does daily (not a clock time or a vague intention), the behaviour
must be tiny enough to survive a low-motivation day, celebration must be
immediate and genuine, and habit timelines must be read from Lally et al.
(2010) as a wide range, not a 21-day or fixed 66-day promise.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read 2026-11-24):
- Fogg (2009) Fogg Behavior Model B=MAP; Tiny Habits (2020): recipe
  "After I [anchor], I will [tiny behaviour], then I will celebrate".
  Anchor = existing stable routine; behaviour shrunk until it needs
  almost no motivation; celebration immediately after wires the habit
  (practitioner claim, less established than cue-repetition evidence).
- Lally, van Jaarsveld, Potts & Wardle (2010) EJSP 40:998-1009: 96
  volunteers, daily behaviour in same context for 84 days; among 39
  good-fit curves, median time to 95% of automaticity asymptote was
  66 days, range 18-254 days; values above 84 days are projections;
  a single missed occasion did not materially reset automaticity.
Separation: ifthen-check owns the user's written if-then plan;
contextual-trigger-check owns in-app trigger timing; freshstart-check
owns landmark timing. This gate owns only the anchor: what existing
routine the new behaviour is attached to, how tiny it is, and the
immediate celebration.
NOT adopted: clock-time anchors presented as anchors, behaviours that
need high motivation, delayed/end-of-day celebration, and promising
habit formation in 21 days or exactly 66 days.
"""
import json, sys
CHECKS=[
 ("anchor_surfaces_recorded_per_app","AN-0 no surface where a new behaviour is introduced (onboarding plan, notification follow-up, home first action) is recorded per app, so there is nowhere an anchor could be applied or audited"),
 ("anchor_is_discrete_completed_action","AN-0 the anchor is a clock time, a vague intention, or a mood rather than a discrete completed action the user already does (Fogg: a time is not a prompt the body notices; the anchor must be a specific finished routine such as after I pour my coffee)"),
 ("anchor_already_reliable_daily","AN-0 the anchor routine is not already reliable and daily for this user (attaching to a routine that itself is aspirational stacks two unformed habits and both fail together)"),
 ("recipe_written_after_anchor_i_will","AN-1 no explicit recipe in the form After [anchor], I will [tiny behaviour] is recorded (without the written recipe the pairing is a hope, not a design that can be checked)"),
 ("behaviour_tiny_enough_for_worst_day","AN-1 the behaviour is not shrunk to a version doable on a tired, ill, or disrupted day (Fogg: design for the worst day; a behaviour that needs high motivation fails exactly when the habit is most at risk)"),
 ("behaviour_immediately_after_anchor","AN-1 the behaviour is not placed immediately after the anchor moment (a gap lets the prompt decay; the recipe is anchor then behaviour with nothing in between)"),
 ("one_anchor_per_new_behaviour","AN-2 several new behaviours are attached to the same anchor at once (one anchor carries one tiny behaviour; a stack of new demands on one cue overloads the moment and none wires in)"),
 ("celebration_immediate_within_seconds","AN-2 celebration is delayed, batched to end of day, or absent (in the Tiny Habits method the immediate felt success is the wiring step; a weekly summary is a report, not a celebration)"),
 ("celebration_genuine_not_forced_theatre","AN-2 the celebration is forced theatre the user does not actually feel (Fogg's own caveat: the emotion must be genuine; a canned animation the user finds empty does not supply the affect the method claims)"),
 ("failure_diagnosed_as_map_not_character","AN-3 a missed behaviour is recorded as a motivation or character failure instead of diagnosing which of Motivation, Ability, or Prompt was missing (B=MAP: exactly one factor was absent; blaming the person designs nothing)"),
 ("shrink_before_abandon","AN-3 when the behaviour is missed, the response is to abandon or scold rather than shrink the behaviour further or move the anchor (the method's repair order is smaller behaviour, better anchor, then re-test)"),
 ("single_miss_not_treated_as_reset","AN-3 a single missed day is treated as a reset to zero (Lally et al. 2010: one missed occasion did not materially affect automaticity development; a reset display contradicts the source and punishes resumption)"),
 ("timeline_read_as_range_not_promise","AN-4 habit formation is promised in 21 days or exactly 66 days (Lally et al. 2010: 66 days is the median of 39 good-fit curves, range 18-254 days, with values past 84 days projected; it is not a deadline for any individual)"),
 ("automaticity_measured_not_assumed","AN-4 automaticity is assumed from streak length alone without any measure of how automatic the behaviour feels (Lally measured self-reported automaticity, not attendance; a long streak of effortful behaviour is not yet a habit)"),
 ("same_context_repetition_preserved","AN-4 the behaviour is deliberately varied in context each day for novelty (Lally's design repeated the behaviour in the same context daily; varying the cue prevents the cue-behaviour link the anchor exists to build - novelty belongs in content, not in the cue)"),
 ("celebration_claim_labelled_practitioner","AN-5 the claim that emotion wires the habit faster than repetition is presented as settled science (it is Fogg's practitioner claim; the broader literature supports cue-based repetition robustly and the specific affect claim is less established - the label must travel with the claim)"),
 ("primary_numbers_quoted_with_design","AN-5 the 66-day figure is quoted without its design (96 volunteers, 84 days, 39 good-fit curves, median 66, range 18-254 - a bare 66 days strips the number of its conditions)"),
 ("anchor_not_used_as_dark_pattern","AN-5 the anchor is used to smuggle an unrelated upsell or paywall moment into a trusted routine (attaching a sales prompt to a personal routine borrows trust the routine earned; anchors carry the behaviour they were agreed for, nothing else)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: anchor_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
