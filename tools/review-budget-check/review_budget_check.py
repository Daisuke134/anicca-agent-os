#!/usr/bin/env python3
"""review-budget-check: deterministic gate for the REVIEW PROMPT BUDGET surface.
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple HIG, Ratings and reviews https://developer.apple.com/design/human-interface-guidelines/ratings-and-reviews
  Ask only after demonstrated engagement; avoid first launch / onboarding; do not interrupt a task;
  do not pester (consider at least a week or two between requests, after additional engagement);
  prefer the system prompt; the system limits display to 3 occurrences per app within 365 days;
  people can opt out for all apps. (Anicca's onboarding placement is a recorded user-ordered
  deviation from the HIG onboarding guidance -- see spec -- this checker does not re-litigate
  placement; it gates whether the shared 3-per-365 budget is managed as one budget.)
- Apple StoreKit review-request contract (via documentation summaries read 2026-11-16):
  a call is a request, not a display; the app receives no callback on whether the prompt appeared;
  SKStoreReviewController.requestReview(in:) is deprecated in iOS 18 in favour of
  AppStore.requestReview(in:) / RequestReviewAction.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("entry_points_inventoried"): f.append("RB-0 every requestReview call site is not inventoried in one record (a second entry point can burn the shared 3-per-365-day budget invisibly)")
    if not dec.get("budget_owner_recorded"): f.append("RB-0 no single budget owner is recorded for review requests (nobody owns the annual 3-display budget across entry points)")
    if not dec.get("onboarding_placement_decision_recorded"): f.append("RB-0 the onboarding placement decision (and its deviation from HIG onboarding guidance) is not recorded with its reasoning, so a future reader cannot tell a deliberate, user-ordered placement from an accident")
    led=d.get("ledger") or {}
    if not led.get("all_entries_write_same_last_request_record_before_call"): f.append("RB-1 not every entry point writes the same last-request record before calling (an entry that writes nothing leaves the shared budget ledger blind to its call)")
    if not led.get("all_entries_read_same_record"): f.append("RB-1 not every entry point reads the same last-request record before calling (an entry that never reads the ledger cannot respect a call another entry already made)")
    if not led.get("has_requested_flag_read_as_gate"): f.append("RB-1 the has-requested flag is write-only (it is set and loaded but never read as a gate, so it records history without ever preventing a duplicate ask)")
    if not led.get("app_version_recorded_at_request"): f.append("RB-1 the app version at each request is not recorded (Apple's own sample never asks twice for the same version; without the version, a repeat ask for one build is indistinguishable from a new-version ask)")
    eli=d.get("eligibility") or {}
    if not eli.get("onboarding_entry_respects_cooldown_or_consumes_budget"): f.append("RB-2 the onboarding entry neither respects the shared cooldown nor consumes budget in a way that blocks the post-value entry (onboarding on day 1 plus post-value from day 3 spends 2 of 3 annual displays in the first week)")
    if not eli.get("postvalue_requires_distinct_days_and_value_moment"): f.append("RB-2 the post-value entry does not require both sustained use (distinct days) and a completed value moment")
    if not eli.get("total_planned_calls_first_365d_within_budget_with_reserve"): f.append("RB-2 planned calls across all entries in the first 365 days are not capped within Apple's 3-display budget with a reserve (unplanned entries plus a 120-day cooldown alone can plan 4 calls into a 3-display budget)")
    if not eli.get("no_entry_fires_on_first_screen_or_before_value"): f.append("RB-2 an entry point can fire on the first screen or before any value moment (the first-launch pattern Guideline 5.6.3 rejected for a sibling app)")
    mea=d.get("measurement") or {}
    if not mea.get("entries_distinguishable_in_analytics"): f.append("RB-3 entry points are not distinguishable in analytics (both track the same event with no source property, so which entry burned budget -- and which one earns reviews -- can never be measured)")
    if not mea.get("calls_counted_per_entry_not_displays"): f.append("RB-3 calls are not counted per entry as calls (the system gives no display callback; counting a call as a display, or not counting per entry at all, fabricates the funnel)")
    if not mea.get("ratings_readback_compared_to_calls"): f.append("RB-3 App Store ratings/reviews readback is never compared against calls per entry (the 48-review result that justified the onboarding placement cannot be re-verified or attributed under the current build)")
    pre=d.get("presentation") or {}
    if not pre.get("system_dialog_only"): f.append("RB-4 the rating dialog is not system-only (a custom star dialog is not a substitute for the system prompt)")
    if not pre.get("decline_or_skip_path_exists_on_preprompt"): f.append("RB-4 the pre-prompt screen has no decline/skip path (the only button calls requestReview, so completing onboarding requires tapping Rate -- a forced tap is not a freely given rating moment, and the defined no-tap analytics event can never fire from this screen)")
    if not pre.get("no_custom_star_gating_or_incentive"): f.append("RB-4 sentiment gating or an incentive is present around the review ask (both are prohibited)")
    ver=d.get("verification") or {}
    if not ver.get("interaction_tests_cover_both_entries"): f.append("RB-5 no test covers the interaction of the entry points (policy tests cover the gated entry alone; the onboarding entry's effect on the shared budget is untested)")
    if not ver.get("suppressed_dialog_fallback_tested"): f.append("RB-5 the suppressed-dialog fallback (advance after a timeout when Apple shows nothing) exists in code but is untested (if it regresses, onboarding can stall on a dialog that will never appear)")
    if not ver.get("testflight_no_effect_recorded"): f.append("RB-5 the TestFlight fact is not recorded (review requests have no effect in TestFlight builds, so beta can never validate this surface -- pretending otherwise wastes a beta cycle)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
