#!/usr/bin/env python3
"""peak-end-check: gate for designing episodes by their peak and end.
Retrospective evaluation is dominated by the most intense moment (peak)
and the final moment (end), with duration largely neglected (Kahneman,
Fredrickson, Schreiber & Redelmeier 1993, Psychol Sci: cold pressor,
60s at 14C vs same 60s + 30s easing to 15C; 22/32 = 69% chose to repeat
the longer trial). Colonoscopy work (Kahneman & Redelmeier 1996) found
the same peak/end weighting in patients. Alaybek et al. (2022) meta-
analysis of 174 effect sizes supports the rule for short lab-style
episodes; day-long / multi-day experiences follow it less well.
Distinct from motivation-peak-check (onboarding sequence timing to the
first paywall) and post-purchase spec: this gate owns (1) identifying
each episode's peak and end, (2) designing a genuine peak and a genuine
better end, (3) measuring remembered evaluation separately from the
in-session average, and (4) never manufacturing a negative peak or a
deceptive end. Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
"""
import json, sys
CHECKS=[
 ("episode_surfaces_recorded_per_app","PE-0 no episode surface (onboarding, daily session, purchase, cancellation, support) is recorded per app, so peak and end cannot be audited"),
 ("peak_identified_per_episode","PE-0 the most intense moment (peak, positive or negative) of each episode is not identified from evidence; an unidentified peak is still the remembered peak, just an undesigned one"),
 ("end_identified_as_last_moment","PE-0 the end is not identified as the literal last moment before exit/close; teams design the 'final screen' they intend, not the error/empty/paywall-rejection screen users actually leave on"),
 ("peak_is_genuine_value_moment","PE-1 the designed peak is not a genuine value moment (first result the user wanted, a real breakthrough line) - manufactured hype, confetti over nothing, or a paywall is not a peak"),
 ("negative_peak_recovery_designed","PE-1 unavoidable negative peaks (wait, failure, rejection, hard news) have no designed recovery, so the negative peak stays the remembered peak instead of the recovery becoming it"),
 ("peak_not_friction_or_error","PE-1 the episode's most intense moment is currently friction or an error state (permission wall, sign-in dialog, crash, price shock) and this is not recorded as the de-facto peak to remove"),
 ("end_designed_positive_close","PE-2 sessions do not end on a designed positive close (the user's own completed thing, warm and specific); ending on a generic menu, an upsell, or nothing leaves the end to chance"),
 ("end_is_genuine_not_deceptive_tail","PE-2 the better end is achieved by deception (fake extension, hidden continuation, a 'one more thing' that traps or re-bills) rather than by genuinely easing/improving the final moments"),
 ("end_gives_saved_state_and_next_step","PE-2 the end does not confirm what is saved/kept and show the single next step, so the remembered end is uncertainty about whether the work counted"),
 ("remembered_evaluation_measured_separately","PE-3 remembered evaluation (return next day, repeat choice, rating, recall) is not measured separately from in-session averages; peak-end predicts the remembered measure, not the average"),
 ("duration_not_used_as_quality_proxy","PE-3 session duration / total time is used as a quality or success proxy (duration neglect: length barely enters retrospective judgement, so longer is not remembered as better or worse)"),
 ("peak_and_end_read_by_cohort","PE-3 peak and end effects are pooled across all users instead of read by cohort/episode type (a peak for a first session and a peak for a returning user are different moments)"),
 ("primary_numbers_quoted_with_design","PE-4 the 69% figure is quoted without its design (22 of 32 male students, cold pressor 60s at ~14C vs +30s easing to ~15C, Kahneman et al. 1993) - bare numbers strip their conditions"),
 ("expectations_discounted_for_episode_length","PE-4 expectations are set at lab effect sizes without discounting: the 2022 meta-analysis (174 effect sizes) supports short lab-style episodes, with weaker fit for day-long and multi-day experiences"),
 ("no_app_effect_promised_from_clinical_data","PE-4 an app retention/rating effect is promised from the colonoscopy/lithotripsy clinical data (Kahneman & Redelmeier 1996) - that data shows remembered pain weighting, not app outcomes"),
 ("no_manufactured_negative_peak","PE-5 a negative peak is manufactured so the end feels like relief (deliberate pain-then-ease, scare-then-sell); exploiting the rule by hurting first is a dark pattern, cf. banned Prayer Lock patterns"),
 ("end_not_used_to_hide_cancellation_or_cost","PE-5 the warm end is used to hide cancellation terms, renewal price, or a cost that appears later (a good remembered end bought with a hidden bill destroys trust and refunds)"),
 ("revenue_claim_tied_to_remembered_chain","PE-5 any revenue claim is not tied to the source chain - peak/end shape remembered evaluation, which shapes repeat/return choice - instead of asserting direct purchase causation the studies did not show"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: peak_end_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
