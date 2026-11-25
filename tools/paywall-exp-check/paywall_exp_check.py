#!/usr/bin/env python3
"""Paywall experiment decision gate checker.
Source: Superwall "How to A/B Test a Paywall" (2026-05-29)
https://superwall.com/blog/how-to-ab-test-a-paywall
Gates:
 X-0 recorded + hypothesis + one variable only + variants otherwise identical
 X-1 primary metric pre-registered; decision metric must be D30 retained RPI/ARPU
     (trial-start alone as decision = fail); refund watched as secondary/safety
 X-2 sample size + stop date pre-registered; per-variant sample meets table for
     baseline+MDE; low volume (<1000 views/week & baseline<10%) => big changes only
 X-3 duration >=7d always; >=14d if decision needs trial-to-paid or D30
 X-4 no peeking early stop; stop only at pre-registered date or safety stop
     (refund divergence >2pp); peeking requires sequential/Bayesian method
 X-5 deterministic hash assignment (not per-session random); cohort tracked to D30+
 X-6 no overlapping test on same placement/users; segment check by channel+country;
     long-term holdout 5-10% kept
"""
import json, sys

# table from source: (baseline, mde_relative) -> min per variant (approx)
TABLE = {(0.05,0.20):9000,(0.05,0.50):1500,(0.15,0.20):2500,(0.15,0.50):400,(0.30,0.20):1000}
def required_sample(baseline, mde):
    # pick closest baseline bucket, require at least the table value for that MDE band
    buckets = sorted(set(b for b,_ in TABLE))
    b = min(buckets, key=lambda x: abs(x-baseline))
    band = 0.20 if mde <= 0.30 else 0.50
    return TABLE.get((b,band), 2000)

def check(d):
    fails=[]; warns=[]
    exp=d.get("experiment",{})
    if not exp.get("recorded"): fails.append("X-0 experiment not recorded")
    if not exp.get("hypothesis"): fails.append("X-0 hypothesis missing")
    if exp.get("variables_changed",0)!=1: fails.append(f"X-0 variables_changed={exp.get('variables_changed')} != 1")
    if not exp.get("variants_otherwise_identical"): fails.append("X-0 variants differ beyond the single variable")
    m=d.get("metrics",{})
    if not m.get("primary_preregistered"): fails.append("X-1 primary metric not pre-registered")
    if m.get("decision_metric") not in ("d30_retained_rpi","d30_retained_arpu","d90_retained_rpi"):
        fails.append(f"X-1 decision_metric={m.get('decision_metric')} is not D30/D90 retained revenue per install/ARPU")
    if not m.get("refund_watched"): warns.append("X-1 refund rate not watched (over-promising check)")
    s=d.get("sample",{})
    if not s.get("size_preregistered"): fails.append("X-2 sample size not pre-registered")
    if not s.get("stop_date_preregistered"): fails.append("X-2 stop date not pre-registered")
    req=required_sample(float(s.get("baseline_rate",0.15)), float(s.get("mde_relative",0.20)))
    if int(s.get("per_variant_views",0)) < req:
        fails.append(f"X-2 per_variant_views={s.get('per_variant_views')} < required ~{req} for baseline={s.get('baseline_rate')} MDE={s.get('mde_relative')}")
    if float(s.get("weekly_paywall_views",99999))<1000 and float(s.get("baseline_rate",1))<0.10 and exp.get("change_size")!="big":
        fails.append("X-2 low volume + low baseline: only big changes (offer matrix / full redesign) are testable, not micro-copy")
    dur=int(d.get("duration_days",0))
    if dur<7: fails.append(f"X-3 duration {dur}d < 7d minimum (full weekly cycle)")
    if m.get("decision_metric") in ("d30_retained_rpi","d30_retained_arpu","trial_to_paid") and dur<14:
        fails.append(f"X-3 duration {dur}d < 14d required when decision needs trial-to-paid/D30")
    st=d.get("stopping",{})
    if st.get("stopped_early_on_peek"): fails.append("X-4 stopped early on peeking (false-positive rate ~25-30%)")
    if st.get("peeked") and not st.get("sequential_method"): fails.append("X-4 peeked without sequential/Bayesian method")
    if st.get("stopped_reason") not in (None,"preregistered_date","safety_refund","sample_reached"):
        fails.append(f"X-4 stopped for non-registered reason: {st.get('stopped_reason')}")
    a=d.get("assignment",{})
    if not a.get("deterministic_hash"): fails.append("X-5 assignment is not deterministic hash of user id")
    if a.get("randomize_per_session"): fails.append("X-5 randomize per session (same user sees different paywalls)")
    if not a.get("cohort_tracked_to_d30"): fails.append("X-5 cohort not tracked to D30+")
    o=d.get("operations",{})
    if o.get("overlapping_same_placement"): fails.append("X-6 overlapping test on same placement/users")
    if not o.get("segment_check_channel_country"): fails.append("X-6 winner not checked by channel and country")
    h=float(o.get("holdout_pct",0))
    if not (5 <= h <= 10): fails.append(f"X-6 holdout {h}% not in 5-10% long-term holdout band")
    return fails,warns

if __name__=="__main__":
    d=json.load(open(sys.argv[1]))
    f,w=check(d)
    for x in w: print("WARN",x)
    for x in f: print("FAIL",x)
    print(f"RESULT {'PASS' if not f else 'FAIL'} fails={len(f)} warns={len(w)}")
    sys.exit(0 if not f else 1)
