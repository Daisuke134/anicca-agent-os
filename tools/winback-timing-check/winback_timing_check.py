#!/usr/bin/env python3
"""winback-timing-check — Win-back Timing Gate (WT-1..WT-12).
Sources (read in full 2026-11-21):
- RevenueCat, When is the best time to send a win-back offer? (2024-08-16, updated 2026-09-11)
  https://www.revenuecat.com/blog/growth/when-is-the-best-time-to-send-a-win-back-offer
  7 triggers: onboarding exit / trial cancel (immediate) / pre-renewal (annual billing-status
  change ~day 290 -> start day 280) / inactivity (typical drop at 30d -> send at 21d) /
  seasonal-event / new feature / post-feedback. Headline rule: as soon as possible.
- RevenueCat (Hannah Parvaz, Aperture), How to win back lost customers (2024-06-27, updated 2026-09-11)
  https://www.revenuecat.com/blog/growth/win-back-customers-how-to-guide
  80% of trial opt-ins in first 2 min; removing the onboarding ask drops opt-ins >80%;
  later trials convert ~20% better; 20% vs 30% discount converted the same (keep margin);
  Curio: ask-for-help + discount together beat discount alone; author's win-back 6% m2 / 8% m6,
  best peer 35% at m6; push lifts conversion >25% (multi-channel is in winback-check, not here).
Distinct from winback-check (Apple offer eligibility/config) and later-paywall-check
(second paywall surface): this gate is ONLY about when each win-back fires.
Free: Python stdlib only. Input: JSON state. Exit 0 = PASS, 1 = FAIL."""
import json, sys
CHECKS = [
 ("WT-1","onboarding_exit_trigger","Onboarding-exit trigger: a user who exits onboarding without completing gets a win-back offer (discount or trial extension) before disengagement"),
 ("WT-2","trial_cancel_immediate_trigger","Trial-cancel trigger fires immediately after trial cancellation, personalised, with a limited-time discount or extra trial period"),
 ("WT-3","prerenewal_timing_from_measured_change_day","Pre-renewal timing is derived from the measured billing-status-change day (e.g. typical change ~day 290 -> outreach starts ~day 280), not a generic calendar guess"),
 ("WT-5","seasonal_event_alignment","Seasonal / event moments relevant to the app category are mapped and used for win-back timing"),
 ("WT-6","new_feature_trigger","Major update / new-feature launches trigger a win-back tied to that feature for inactive/lapsed users"),
 ("WT-7","post_feedback_trigger","Post-feedback / post-survey follow-up sends a win-back that addresses the stated concern"),
 ("WT-8","latency_defined_per_trigger","Every trigger has a defined latency under the as-soon-as-possible rule (immediate / same-day), not a monthly batch blast"),
 ("WT-9","ask_plus_offer_experiment","Ask-for-help + offer combined is in the experiment backlog (Curio: ask + discount together beat discount alone)"),
 ("WT-10","discount_depth_tested_shallow_kept","Discount depth was A/B tested and the shallower depth kept when conversion is equal (20% vs 30% converted the same; margin is kept)"),
 ("WT-11","no_discount_escalation","The sequence does NOT deepen the discount over touches (the Lose It! 20% -> 50% escalation is an anti-pattern here; cf. later-paywall rule)"),
 ("WT-12","winback_rate_benchmarked_by_month","Win-back rate is measured by month 2 / month 6 against a benchmark (author 6% m2 / 8% m6; best peer 35% m6), per trigger, not as one blended rate"),
]
def main(path):
    s=json.load(open(path)); fails=[]
    for gid,key,desc in CHECKS:
        ok = s.get(key) is True
        print(f"{'PASS' if ok else 'FAIL'} {gid} {desc}")
        if not ok: fails.append(gid)
    # WT-4 numeric: inactivity trigger must precede typical dropoff
    trig, drop = s.get("inactivity_trigger_days"), s.get("typical_dropoff_days")
    ok4 = isinstance(trig,(int,float)) and isinstance(drop,(int,float)) and 0 < trig < drop
    print(f"{'PASS' if ok4 else 'FAIL'} WT-4 Inactivity trigger fires BEFORE the typical disengagement point (trigger {trig!r}d < typical dropoff {drop!r}d; winner example 21d vs 30d)")
    if not ok4: fails.append("WT-4")
    total=12; passed=total-len(fails)
    print(f"TOTAL {'PASS' if not fails else 'FAIL'} {passed}/{total}")
    return 0 if not fails else 1
if __name__=="__main__":
    sys.exit(main(sys.argv[1]))
