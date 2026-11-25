#!/usr/bin/env python3
"""funnel-definition-check: deterministic gate for FUNNEL STEP DEFINITIONS
(whether the install->purchase funnel's steps are defined by the moment they
fire, the placement they came from, and a server source of truth -- so the
funnel cannot silently lie). Stdlib only, offline, free.
Sources (read in full 2026-11-23):
- Unolink "Onboarding and paywall funnels: what to track" (2026-11-02)
  https://unolink.dev/blog/onboarding-paywall-funnel-metrics
  Keep the funnel to 5-6 actionable steps; the firing MOMENT matters more
  than the name (screen event on appearance, not on button tap; completion
  fired before any paywall/sign-up that follows); every paywall view carries
  its placement (onboarding / feature_gate / settings) because placements
  are different offers to different people; sign_up only for NEW accounts
  (returning sign-ins must not inflate sign-ups); trial/purchase reported by
  the store/server source of truth (RevenueCat), never app-side only, so
  renewals/refunds/closed-app conversions are visible and nothing counts
  twice; fixed short screen names (goal, notifications, plan), never
  positional names like "Screen 3"; NEVER put onboarding answers or
  personal data in analytics event properties; read by install-date cohort,
  count steps unordered by default, wait >=1 day before calling a drop-off,
  trial->paid only on trials old enough to have ended, exclude test devices
  automatically, and require a minimum N before comparing versions.
Boundary: analytics-check owns instrumentation governance (tracking plan,
Lexicon, emission, identity, delivery). This gate owns the DEFINITIONS of
the primary funnel steps and the rules for reading them. Note a recorded
tension: analytics-check AI-2 asks funnel events to "carry the answers";
Unolink forbids answers in analytics events. Resolution recorded in the
spec: categorical answer keys belong in the product-side intervention log
(Manager), not in analytics event properties.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
CHECKS = [
 ("FD-0","funnel_steps_recorded","primary funnel steps are not recorded as a short (5-6 step) actionable list (an unrecorded funnel is whatever each dashboard happens to show)"),
 ("FD-0","each_step_has_firing_moment","not every step has a recorded firing moment (the moment matters more than the name; without it two builds can send the same event at different moments and the funnel compares unlike things)"),
 ("FD-0","primary_funnel_named_and_owned","the primary install->purchase funnel is not named with an owner (funnels nobody owns drift when onboarding or paywall changes)"),
 ("FD-1","screen_event_on_appearance","onboarding screen events are not fired on appearance (tap-based firing loses everyone who saw the screen and left without tapping)"),
 ("FD-1","completion_before_paywall_or_signup","onboarding completion is not fired at the last screen, before any paywall or sign-up that follows (firing it later merges completion with the next step's drop)"),
 ("FD-1","skip_carries_origin_screen","skip events do not carry the screen skipped from (a skip cannot be read as shortcut vs escape)"),
 ("FD-2","paywall_view_every_appearance_with_placement","paywall views are not fired on every appearance with a placement property (onboarding / feature_gate / settings are different offers; mixing them makes both numbers meaningless)"),
 ("FD-2","signup_only_new_accounts","sign_up is not restricted to new accounts (returning users signing in on a new device inflate sign-ups on every reinstall)"),
 ("FD-2","funnel_split_by_source","the funnel is not read per source (creator / search / ad cohorts behave differently; an average across them hides what each needs)"),
 ("FD-3","trial_purchase_from_server_truth","trial starts / purchases are not reported by the store/server source of truth (app-side purchase events miss renewals, refunds and trials converting while the app is closed)"),
 ("FD-3","no_double_counting_app_and_server","app-side and server-side purchase reporting can double count (the same conversion recorded twice inflates the funnel's last step)"),
 ("FD-3","paywall_conversion_read_per_placement","paywall conversion is not read per placement (a single blended rate cannot say which offer works)"),
 ("FD-4","fixed_short_screen_names","screen names are not fixed short semantic names (positional names like 'Screen 3' change meaning the day onboarding is reordered)"),
 ("FD-4","no_answers_or_pii_in_events","analytics event properties are not kept free of onboarding answers and personal data (answers in events turn analytics into an ungoverned personal-data store and complicate privacy answers; answer keys belong in the product-side intervention log)"),
 ("FD-4","test_devices_excluded_automatically","test / TestFlight / sandbox traffic is not excluded automatically (own devices inflate every step and the exclusion must not depend on remembering a filter)"),
 ("FD-5","cohort_by_install_date","rates are not counted by install-date cohort (counting payments this week against installs this week puts late trial conversions in the wrong cohort)"),
 ("FD-5","unordered_counting_and_maturity_rules","reading rules are missing: steps counted unordered by default, drop-off judged only after >=1 day, trial->paid only on trials old enough to have ended"),
 ("FD-5","minimum_n_before_comparison","no minimum-N rule before comparing versions (at small counts one purchase moves conversion by points; comparisons without a floor read noise as signal)"),
]
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = json.load(open(path)) if path != "-" else json.load(sys.stdin)
    fails = [f"{g} {k}: {msg}" for g, k, msg in CHECKS if not data.get(k)]
    if fails:
        print(f"FAIL {len(fails)}/{len(CHECKS)}")
        for f in fails: print(" -", f)
        return 1
    print(f"PASS {len(CHECKS)}/{len(CHECKS)}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
