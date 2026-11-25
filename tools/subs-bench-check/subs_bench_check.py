#!/usr/bin/env python3
"""subs-bench-check: judge a subscription state description against
RevenueCat State of Subscription Apps 2026 primary benchmarks.
Stdlib only, offline, deterministic.
Benchmarks (primary source, read 2026-11-14):
 https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026
 - Hard paywall median D35 download-to-paid 10.7% vs freemium 2.1% (~5x)
 - RPI day60 hard $3.09 vs freemium $0.38 (8x)
 - Trial 17-32d trial-to-paid 42.5% vs <4d 25.5% (~70% better)
 - 55.4% of 3-day trial cancellations occur on Day 0; 84% by Day 1
 - Month 1 = 35% of all annual cancellations; ~72% of annual subs cancel in Year 1
 - Billing failures: 14% of App Store cancellations, 31% Google Play
"""
import json, sys
fails=[]; warns=[]
def fail(g,m): fails.append(f"[{g}] {m}")
def warn(g,m): warns.append(f"[{g}] {m}")
def main(path):
    s=json.load(open(path))
    # SB-0 record
    if not s.get("recorded"): fail("SB-0","state not recorded (unmeasured)")
    pt=s.get("paywall_type")
    if pt is None: fail("SB-0","paywall_type unrecorded (unmeasured)")
    td=s.get("trial_days")
    if td is None: fail("SB-0","trial_days unrecorded (unmeasured)")
    # SB-1 paywall type
    if pt=="freemium": fail("SB-1","freemium: benchmark D35 2.1% vs hard 10.7% (RevenueCat 2026)")
    elif pt=="soft": warn("SB-1","soft paywall: compare on paywall-view basis, not download basis")
    elif pt=="hard": pass
    elif pt is not None: fail("SB-1",f"unknown paywall_type {pt}")
    # SB-2 trial length
    if td is not None:
        if td<=0: fail("SB-2","no trial: paywall-with-trial benchmark not reachable")
        elif td<=4: fail("SB-2",f"trial {td}d in <=4d bucket: trial-to-paid median 25.5% vs 42.5% for 17-32d")
        elif td<=16: warn("SB-2",f"trial {td}d between buckets (25.5% <=4d / 42.5% 17-32d): test longer")
        elif td<=32: pass
        else: warn("SB-2",f"trial {td}d above studied 17-32d band")
    # SB-3 trial display truth
    if td and td>0 and s.get("trial_shown_on_paywall") is not True:
        fail("SB-3","trial exists in store offer but is not shown truthfully on paywall")
    # SB-4 Day 0
    d0=s.get("day0") or {}
    if d0.get("aha_in_first_session") is not True: fail("SB-4","no verified aha moment in first session (55.4% of 3-day trial cancels are Day 0)")
    if d0.get("day0_cancellation_measured") is not True: fail("SB-4","Day 0 cancellation share unmeasured")
    # SB-5 measured vs benchmark
    m=s.get("metrics") or {}
    d35=m.get("d35_download_to_paid_pct")
    if d35 is None: fail("SB-5","D35 download-to-paid unmeasured (benchmark: hard median 10.7%)")
    elif d35<2.1: fail("SB-5",f"D35 {d35}% below even freemium median 2.1%")
    elif d35<10.7: warn("SB-5",f"D35 {d35}% below hard-paywall median 10.7%")
    # SB-6 annual month-1
    a=s.get("annual") or {}
    if a.get("month1_cancellation_measured") is not True: fail("SB-6","annual Month-1 cancellation unmeasured (Month 1 = 35% of annual cancels)")
    if a.get("winback_in_first_2_months") is not True: fail("SB-6","no win-back running in first 2 months")
    # SB-7 billing recovery
    b=s.get("billing") or {}
    if b.get("grace_period_enabled") is not True: warn("SB-7","grace period not verified enabled")
    if b.get("winback_enabled") is not True: fail("SB-7","billing/win-back recovery not enabled (billing = 14% of App Store cancels)")
    if b.get("billing_failure_share_pct") is None: warn("SB-7","billing failure share unmeasured")
    for w in warns: print("WARN",w)
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1
if __name__=="__main__": sys.exit(main(sys.argv[1]))
