#!/usr/bin/env python3
"""answer-persistence-check: gate for whether onboarding answers are
SAVED as durable user attributes and actually USED later.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- CMM, "Long quiz onboardings earn more per user, yet few apps use the
  answers" (2026-11-19), summarising Adapty State of Onboarding 2026
  https://www.cmm-tech.com/blog/adapty-state-of-onboarding-2026-length-personalization/
  21+ screen flows earn $1.39 gross revenue per onboarding open vs
  $0.36 for 1-5 screens (completion 62.8% vs 89.7%; report itself
  notes this is NOT causal - long flows cluster in Health & Fitness /
  Education). Only 19.2% of apps save new user attributes during
  onboarding (large apps 40.9% vs small 15.0%). 52% of top-grossing US
  apps personalise onboarding, but only 9% of paywalls mention the
  user's name, goal or target date. 23.5% ran an onboarding A/B test;
  only 1 in 6 found a clear winner on paid conversion, with the median
  variation collecting just 43 paid conversions. CMM's rule: every
  question should either change what the user sees later or be
  removed; size tests for revenue (e.g. revenue per open), not
  completion; saving answers as attributes is a small engineering
  task that makes later personalisation possible.
Separation: onboarding-adaptation-check owns in-flow branching while
the flow runs; paywall-personalization-second-offer owns headline /
second-offer mechanics; install-paid-check owns the decision metric
for changes. This gate owns only the persistence-and-reuse chain:
collect -> save durably -> play back -> use on paywall -> reuse in
lifecycle -> measure the chain itself.
"""
import json, sys
CHECKS=[
 ("question_inventory_recorded","AP-0 no recorded inventory of onboarding questions (list every question asked; a question nobody can list is a question nobody decided to ask)"),
 ("each_question_mapped_to_later_use_or_flagged","AP-0 not every question is mapped to a later surface it changes, or flagged for removal (CMM/Adapty: every question should either change what the user sees later or be removed; unmapped questions are pure friction)"),
 ("answer_schema_recorded","AP-0 no recorded answer schema (attribute names/types for the answers; without a schema, 'saving' degrades into free-text logs nobody can segment on)"),
 ("answers_saved_as_durable_attributes","AP-1 answers are not saved as durable user attributes (Adapty: only 19.2% of apps save attributes during onboarding; session-only state dies with the session and cannot personalise anything later)"),
 ("saved_before_paywall_and_survives_relaunch","AP-1 answers are not saved before the paywall and verified to survive an app kill/relaunch (a crash or swipe-away between quiz and paywall loses the only copy)"),
 ("attribute_write_verified_in_backend","AP-1 the attribute write has never been verified in the backend (analytics user properties / subscriber attributes); an unverified write is an assumed write"),
 ("answers_played_back_before_paywall","AP-2 the user never sees their own answers played back before the paywall (plan summary / insight built from their answers; Superwall host caution via gr0w: ask personal questions then give everyone the same generic result and people notice)"),
 ("generic_prepaywall_screen_replaced_by_recap","AP-2 a generic screen still sits immediately before the paywall instead of a value recap / plan reveal (Lazyweb via RevenueDot: generic screen in 28 of 40 flows; a recap belongs there)"),
 ("playback_includes_goal_or_target_date","AP-2 the playback does not include the user's goal or target date (the two answer fields a paywall can most concretely echo; Adapty: only 9% of paywalls mention name, goal or target date)"),
 ("paywall_references_at_least_one_saved_answer","AP-3 the paywall references none of the saved answers (headline/body ignores name, goal and target date entirely - the collected answers stop at the paywall door)"),
 ("plan_or_offer_varies_by_answer_or_decided","AP-3 the recommended plan/offer neither varies by answer nor has a recorded decision not to vary it (silent uniformity is an unmade decision, not a design)"),
 ("missing_answer_fallback_defined","AP-3 no fallback is defined for missing/skipped answers (personalisation must degrade to an honest generic, never fabricate an answer the user did not give)"),
 ("attributes_reused_in_lifecycle_surface","AP-4 saved attributes are reused in no lifecycle surface (trial reminder, notification, win-back or home; attributes used only inside onboarding are a cost with no compounding)"),
 ("attributes_available_for_segmentation","AP-4 attributes are not available for messaging/audience segmentation (if the messaging tool cannot read them, lifecycle reuse is manual and will not happen on a loop)"),
 ("answer_refresh_path_exists","AP-4 there is no path to refresh stale answers (goals change; attributes with no update path or versioning silently personalise toward who the user was at install)"),
 ("persistence_rate_measured","AP-5 the persistence rate is not measured (% of installs with attributes actually saved; a silent write failure reads as 'personalisation does not work')"),
 ("personalisation_read_by_cohort_on_revenue","AP-5 personalisation is not read by cohort (attributed vs not) on a revenue metric such as revenue per open or install-to-paid (completion-only reads cannot price the extra screens)"),
 ("test_sizing_rule_recorded","AP-5 no recorded test-sizing rule for onboarding tests (Adapty: median variation collected just 43 paid conversions and only 1 in 6 tests found a winner; record a minimum paid-conversion threshold or an explicit low-volume sequential/pre-post decision)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: answer_persistence_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
