#!/usr/bin/env python3
"""contextual-trigger-check: gate for WHEN a later/contextual paywall fires.
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- AppsTemple, "Contextual Paywall Design: 5 Triggers" (2026-06-30)
  https://www.appstemple.com/guides/contextual-paywall-design/
  Behavioural not chronological triggers; RevenueCat case: +50% revenue
  changing ONLY when the paywall appeared. Highest intent: feature-gate
  tap, limit reached (after success, not item 1), export/share attempt;
  then session-success and return-engagement (e.g. 7 sessions/14d,
  conditioned on depth). Worst moment = before first win; window is
  roughly first 5 sessions before 'free' hardens. Headline must name the
  trigger (test: could it appear unchanged in any app at any moment?).
  Separate placement per trigger; read trigger-to-trial per placement,
  never dismissal alone. Cap 2-3/week for dismissers, hard stop after
  5-7 total dismissals.
- FirstApp, "Optimize a mobile app paywall" (read in full 2026-11-24)
  https://www.firstapp.fr/en/blog/comment-optimiser-paywall-application-mobile
  10 triggers (aha, export/save/share, 2nd use, personalisation, natural
  block, return session 2-3, positive feedback, explore/compare, success,
  ask-for-more). Anti-spam non-negotiables: <=1 paywall/24h per user;
  never first screen without value; after 2 closes wait 72h or a new
  strong trigger; always keep a clear continue path.
Separation: later-paywall-check owns the later surface's existence/offer/
holdout; paywall-exposure owns reach rate; install-paid-check owns the
decision metric for changes. This gate owns only trigger choice and
repetition discipline for contextual/later placements.
"""
import json, sys
CHECKS=[
 ("trigger_map_recorded","CTX-0 no recorded trigger map (list every action signalling demonstrated need before designing anything; AppsTemple: map the trigger before you redesign the paywall)"),
 ("triggers_ranked_by_engagement_depth","CTX-0 triggers are not ranked by observed engagement depth (pick the 2-3 deepest; an unranked list fires the shallowest trigger as often as the deepest)"),
 ("timer_only_triggers_removed_or_flagged","CTX-0 a timer/session-count-only trigger still fires unflagged (AppsTemple: 'show after session 3' treats a day-1 feature tapper and a passive opener identically)"),
 ("first_win_defined","CTX-1 no single first win is defined (the completed core action/result after which a contextual ask is earned)"),
 ("no_contextual_paywall_before_first_win","CTX-1 a contextual paywall can fire before the first win (AppsTemple: worst moment; FirstApp: never first screen without value)"),
 ("feature_gate_trigger_present","CTX-2 no feature-gate trigger (tap on a locked feature = highest intent; headline must name that feature, not 'Upgrade to Pro')"),
 ("limit_trigger_after_success_not_first_item","CTX-2 the limit trigger can fire at the first item/action (AppsTemple: showing it on item 1 is the common mistake; let users succeed first, copy quantifies where they are and what is beyond)"),
 ("success_or_return_trigger_present","CTX-2 no session-success or return-engagement trigger (success = celebrate first then pitch; return = threshold conditioned on depth, e.g. 7 sessions/14d, not raw days)"),
 ("separate_placement_per_trigger","CTX-3 triggers share one placement (per-placement copy/layout/analytics are a dashboard decision in RevenueCat/Adapty/Nami; one placement makes every trigger read as a generic interrupt)"),
 ("headline_names_the_trigger","CTX-3 a headline does not name its trigger (limit names the limit, export names the export, success acknowledges the achievement; generic copy wastes a high-intent moment)"),
 ("copy_fixed_before_layout_test","CTX-3 layout is being tested before contextual copy is fixed (AppsTemple: bad copy suppresses a good trigger's signal before it can be seen; fix copy, then test layout)"),
 ("weekly_cap_for_dismissers","CTX-4 no weekly cap for users who dismissed (AppsTemple: 2-3/week; FirstApp: <=1/24h per user)"),
 ("hard_stop_after_5_to_7_dismissals","CTX-4 no hard stop after 5-7 total dismissals (repeated exposure without conversion is a trigger/offer problem, not an impressions problem)"),
 ("cooldown_72h_after_2_dismissals","CTX-4 after 2 closes there is no 72h wait or new-strong-trigger requirement before re-showing (FirstApp anti-spam rule)"),
 ("clear_continue_free_path","CTX-4 no clear continue-for-free path at a contextual paywall (FirstApp: blocking completely creates churn, not conversion)"),
 ("per_placement_conversion_measured","CTX-5 conversion is not read per placement/trigger (aggregate views+trial starts cannot diagnose which trigger works; read trigger-to-trial per placement)"),
 ("dismissal_rate_not_judged_alone","CTX-5 dismissal rate is judged in isolation (AppsTemple: a paywall dismissed often but starting more trials overall is performing better, not worse)"),
 ("contextual_vs_timer_test_or_decision","CTX-5 the top contextual trigger has never been A/B-tested against the timer default nor explicitly decided against with a reason (diagnose in order if it loses: trigger intent, generic copy, trial too short)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: contextual_trigger_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
