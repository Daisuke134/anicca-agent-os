#!/usr/bin/env python3
"""install-velocity-check: deterministic gate for the INSTALL VELOCITY surface
(founder correction 2026-11-22: the target is NOT 100 installs/day across
6 apps; it is 100/day PER app = 600/day total, and 1,000/day for the flagship
Anicca alone. Current state then: ~1.7/day total, Anicca 3 in 7 days).
Stdlib only, offline, free.
Owns install-target definition, daily-velocity measurement, category-relative
calibration, install-to-revenue coupling and the scale loop. Not CPP/ASO
keyword assignment (cpp-check), not UGC program structure (ugc-maxing-check).
Sources (read 2026-11-22):
- Ar.Bhavesh Panse, "How many downloads it takes to rank, honestly"
  (updated 2026-11-07) https://www.arbhaveshpanse.com/playbooks/app-store-optimization/downloads-needed-to-rank
  Ranking is VELOCITY and category-relative: downloads per day against the
  category incumbents, not a lifetime total. 500/day now outranks 1M lifetime
  at 50/day. Chart position is a lagging readout of this week and decays when
  the push ends. The bar rises every year (US top-chart requirement +37%
  2016-2019, Sensor Tower via TechCrunch). Owning specific search terms
  compounds; chart-chasing rents a position by the day. A burst is worth it
  only attached to a moment that can hold altitude (launch, feature).
- App Masters / GTM Sauce (2026-11-14, secondary summary of practitioner
  numbers): a niche app at ~100 installs/day with ~13% install-to-trial and
  ~35% trial-to-paid produced ~$8-10K/month after a hard-paywall subscription
  was added. Installs only become revenue multiplied by the funnel rates.
  https://gtmsauce.com/episodes/2026-11-14-he-built-46-apps-then-he-did-this-to-get-to-10k-mrr
- House rules (founder, primary): paid growth is never even considered --
  scale is free and organic only; a stopped or tiny lane is a SYSTEM problem
  to fix on the spot, never an accepted state; volume is judged against the
  biggest winner, never against past self or cumulative counts.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    t=d.get("target") or {}
    if not t.get("corrected_per_app_target_recorded"): f.append("IV-0 the corrected per-app target is not recorded (100/day per app = 600/day total and 1,000/day for Anicca alone; the superseded '100/day total' understates the goal 6x and quietly lowers every lane's ambition)")
    if not t.get("target_is_daily_velocity_not_cumulative"): f.append("IV-0 the target is stated as a cumulative total (stores rank on daily velocity -- 500/day now outranks 1M lifetime at 50/day; a lifetime number changes nothing)")
    if not t.get("flagship_target_separated_from_portfolio"): f.append("IV-0 the flagship target is not separated from the portfolio (Anicca's 1,000/day is a different job from each other app's 100/day; averaging them hides the flagship gap)")
    if not t.get("current_daily_baseline_measured_per_app"): f.append("IV-0 the current daily baseline is not measured per app (a gap cannot be managed from a portfolio blur; the known state -- ~1.7/day total, Anicca 3 in 7 days -- must be per-app and dated)")
    v=d.get("velocity") or {}
    if not v.get("daily_rate_measured_per_app_not_lifetime"): f.append("IV-1 installs are read as lifetime totals (anything that changes rank must change the daily rate; totals are a trophy, velocity is the dial)")
    if not v.get("rolling_7day_velocity_tracked"): f.append("IV-1 no rolling 7-day velocity is tracked (one-day spikes and one-day zeros both lie; the week is the smallest honest window)")
    if not v.get("velocity_source_is_store_first_downloads"): f.append("IV-1 the velocity source is not store first-downloads (panel estimates and rating-derived bases are models, not the app's own install record)")
    if not v.get("rank_read_as_lagging_readout_not_goal"): f.append("IV-1 chart rank is treated as the goal (rank is a lagging readout of this week's velocity and decays the moment the push ends; chasing it rents a position by the day)")
    c=d.get("category") or {}
    if not c.get("category_neighbour_daily_rate_estimated"): f.append("IV-2 the category neighbours' daily rate is not estimated (the useful question is what the apps holding the wanted positions do per day -- your target is set by your neighbours, not a universal threshold)")
    if not c.get("search_term_ownership_prioritized_over_charts"): f.append("IV-2 owning specific search terms is not prioritized over chart position (search positions compound as history and reviews build and reach people mid-problem; chart browsers convert worst)")
    if not c.get("bar_rechecked_as_it_rises"): f.append("IV-2 the required velocity bar is not re-checked (it inflates every year -- +37% for a US top spot in 2016-2019 alone; a plan pencilled three years ago is already too small)")
    r=d.get("revenue_coupling") or {}
    if not r.get("install_to_trial_and_paid_tracked_per_app"): f.append("IV-3 install-to-trial and trial-to-paid are not tracked per app (the practitioner arithmetic is installs x rates: ~100/day at ~13% and ~35% is ~$8-10K/month; installs without the rates are vanity)")
    if not r.get("revenue_per_install_tracked"): f.append("IV-3 revenue per install is not tracked (velocity from segments that never pay inflates the dial while gross profit stays flat -- the governing test is gross profit, not downloads)")
    if not r.get("nonpaying_segment_velocity_flagged"): f.append("IV-3 velocity from non-paying segments is not flagged separately (a day can hit its install number and miss its revenue number entirely; the two must be readable apart)")
    o=d.get("organic") or {}
    if not o.get("velocity_is_free_and_organic_only"): f.append("IV-4 velocity depends on paid acquisition (house rule: paid growth is never even considered -- scale is free and organic only; bought velocity also stops the day the spend stops)")
    if not o.get("bursts_only_attached_to_real_moments_with_hold_plan"): f.append("IV-4 bursts are not restricted to real moments with a hold plan (outside a launch or feature window, a burst rents altitude that decays in days; the moment must be able to hold what the spike wins)")
    if not o.get("no_new_accounts_for_velocity"): f.append("IV-4 new accounts are created to chase velocity (house rule: no new SNS accounts; volume grows on the existing surfaces and their proven formats)")
    l=d.get("loop") or {}
    if not l.get("daily_velocity_reviewed_on_a_loop"): f.append("IV-5 daily velocity is not reviewed on a loop (a rate that is only read when someone asks is not managed; the check must run whether or not anyone is watching)")
    if not l.get("rung_ladder_with_next_rung_action"): f.append("IV-5 there is no rung ladder with a named next-rung action (10 -> 100 -> 1,000/day per app; each rung needs its own owner and action, not a wish)")
    if not l.get("shortfall_treated_as_system_problem"): f.append("IV-5 a shortfall is accepted as a state (house rule: a lane stopped or tiny for a day is a system problem to dig to the root and fix on the spot -- 'about 1.7/day' is a finding, not a resting place)")
    if not l.get("gap_judged_against_winners_not_past_self"): f.append("IV-5 the gap is judged against past self (house rule: volume is judged against the biggest winner's daily rate, never against our own history or cumulative counts)")
    return f
def main():
    d=json.load(open(sys.argv[1]))
    fails=check(d)
    for x in fails: print("FAIL", x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
