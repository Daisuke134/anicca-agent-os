#!/usr/bin/env python3
"""onboarding-length-check: deterministic gate for onboarding-length decisions.
Stdlib only, offline, free.
Primary source (read in full this run, 2026-11-23):
- RevenueCat, Everlove A/B test (published 2026-11-19):
  28 steps vs 19 steps, 24,000 users. Short: completion 78.1%->86.7% (+8.6pp),
  paywall reach 74.26%->83.92% (+9.66pp), ~700 more paywall viewers on a
  SMALLER cohort; trial starts per paywall viewer 3.83%->3.13% (-18% relative);
  initial conversion 3.35% vs 3.11% (no significant difference) -- the two
  effects cancelled. LTV/registered user $0.1163 vs $0.1592 (+36.9%, weak
  p=0.093). Takeaway in the source itself: length is not the first decision;
  find where the funnel leaks first, and measure BOTH halves.
  https://www.revenuecat.com/blog/growth/everlove-onboarding-experiment
Exit 0 = PASS, 1 = FAIL."""
import json, sys
def check(d):
    f=[]
    diag=d.get("diagnosis") or {}
    if not diag.get("leak_location_identified"): f.append("OL-0 leak location (onboarding vs paywall) is not identified BEFORE any length decision (source: 'Find where you lose the most people. Answer that before you touch length')")
    if not diag.get("both_halves_measured"): f.append("OL-0 both halves are not measured (onboarding completion rate AND conversion per paywall viewer; one half alone cannot judge a length change -- the winner test's two halves moved in opposite directions)")
    if not diag.get("funnel_counts_recorded"): f.append("OL-0 funnel counts are not recorded (starts, completions, paywall views, trial starts; rates without counts hide a smaller cohort putting more people at the paywall, as in the source test)")
    q=d.get("question_audit") or {}
    if not q.get("every_question_mapped_to_prior_value"): f.append("OL-1 not every onboarding question is checked against what the user has got out of the product by that point (source rule 4: a question arriving before the user understands why it is worth answering must move later or be dropped)")
    if q.get("heavy_questions_before_first_value"): f.append("OL-1 heavy/emotional questions sit before the first value experience (the source flow front-loaded 'what is broken' questions at the funnel's most fragile point; that placement, not the questions, was the problem)")
    if not q.get("removed_questions_relocated_not_deleted"): f.append("OL-1 removed questions are deleted outright instead of scheduled to be re-asked after product use (source: 'Put the removed questions back later, not never' -- they still personalise, without costing users at the start)")
    t=d.get("test_design") or {}
    if not t.get("single_variable"): f.append("OL-2 more than onboarding length differs between arms (source test: 'onboarding length is the only difference between the two arms'; a length read contaminated by a simultaneous paywall change attributes nothing)")
    if not t.get("concurrent_test_exposure_controlled"): f.append("OL-2 concurrent-test exposure is not controlled/recorded (the source window ended when both variants became equally exposed to a concurrent paywall test; uncontrolled overlap silently re-labels the result)")
    if not t.get("scope_and_significance_recorded"): f.append("OL-2 audience scope and significance standard are not recorded (source ran worldwide because US volume was too small below the top of funnel; a local read at tiny volume is noise presented as a verdict)")
    r=d.get("reading") or {}
    if r.get("split_result_treated_as_broken"): f.append("OL-3 a split result (one half up, the other down) is treated as a broken test (source: 'One going up while the other goes down is the normal result, not a broken test')")
    if not r.get("judged_on_net_conversion"): f.append("OL-3 the change is not judged on net conversion per registered user (completion gain alone would have claimed a win while trial starts per viewer fell 18% and net conversion was flat)")
    if not r.get("ltv_and_plan_mix_checked"): f.append("OL-3 LTV per registered user and plan mix are not checked (source: fewer buyers can each be worth more -- +36.9% LTV signal, weak -- and 'look at what people bought, not just how many bought')")
    n=d.get("next_action") or {}
    if not n.get("action_matches_leak"): f.append("OL-4 the next action does not match the diagnosed leak (onboarding leak -> shorten; paywall leak with plenty of traffic -> fix the paywall, do NOT shorten -- shortening 'just sends it more of the same problem')")
    if not n.get("paywall_reinforced_after_shortening"): f.append("OL-4 after shortening, the paywall is not reinforced for the less-committed cohort it now receives (source next step: make the paywall work harder -- reinforce value, address objections the shortened onboarding no longer handles)")
    if not n.get("relocated_questions_retest_scheduled"): f.append("OL-4 no separate retest is scheduled for the relocated questions (source: re-asking after use 'should be tested on its own'; bundling it into the next change destroys attribution)")
    g=d.get("guardrails") or {}
    if not g.get("baseline_recorded_before_change"): f.append("OL-5 no pre-change baseline is recorded (without the long-flow baseline counts, the post-change read has nothing to cancel against)")
    if g.get("length_decided_by_fashion"): f.append("OL-5 length is being decided by prevailing advice/fashion (source notes the advice 'has swung back and forth' and currently leans long because of Noom's 113 steps; copying a length without a leak diagnosis is originality, not a winner copy)")
    if not g.get("decision_recorded_with_numbers"): f.append("OL-5 the length decision is not recorded with its numbers (completion, reach, trial-start-per-viewer, net conversion, LTV; an unrecorded decision cannot be revisited when the funnel's stuck point moves)")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
