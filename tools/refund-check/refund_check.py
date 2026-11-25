#!/usr/bin/env python3
"""Refund rate / refund handling gate checker.
Sources (full-text read 2026-11-13):
 - Adapty "Understanding refund rate benchmarking"
   https://adapty.io/blog/refund-rate-metrics-and-benchmarking/
 - Arjun Maheta "5 Ways App Developers Can Use Purchase Data to Reduce Refund Losses"
   https://medium.com/@arjun_1882/5-ways-app-developers-can-use-purchase-data-to-reduce-refund-losses-24d0cf6ab167
Gates:
 F-0 refund rate is measured: transactions rate AND revenue rate, attributed to the
     original transaction period (not refund processing date), partial refund counts
     as a refunded transaction
 F-1 lag discipline: monthly cohorts judged only after >=30d window, annual after
     >=90d operational floor (source: annual lag is longer, unspecified); no cohort or
     experiment judgement before the lag closes; pricing tests wait >=1 full billing
     cycle + refund lag
 F-2 benchmark band: rate classified on the scale (<2 excellent / 2-5 normal /
     5-10 concerning / >10 critical); concerning band without a recorded
     investigation = fail; critical band = fail
 F-3 segmentation: weekly review split by plan duration, region, price tier,
     paywall/model, channel and product; a segment at >=2x baseline is flagged as a
     product problem, not left as a support statistic
 F-4 consumption-data readiness (Apple): CONSUMPTION_REQUEST handled with a response
     inside 12 hours, consumption/usage data retained >=30d (60d = full history per
     source guidance, warn below), original transaction ID stored, purchase-history
     fields recorded, a named owner for the clock
 F-5 post-refund loop: access revoked on refund notification, every request logged
     with reason code + product ID, decision log kept
 F-6 judgement integration: LTV/RPI include the refund effect, paywall and pricing
     decisions are refund-adjusted; a hard paywall (benchmark 5.8% vs freemium 3.4%)
     requires recorded expectation work (onboarding / value communication)
"""
import json, sys

def check(d):
    fails=[]; warns=[]
    m=d.get("measurement",{})
    if not m.get("recorded"): fails.append("F-0 refund rate not recorded/measured")
    if not m.get("transactions_rate"): fails.append("F-0 transactions refund rate missing (refunded / paid transactions)")
    if not m.get("revenue_rate"): fails.append("F-0 revenue refund rate missing")
    if not m.get("attributed_to_original_period"): fails.append("F-0 refunds attributed to processing date, not the original transaction period")
    if not m.get("partial_counts_as_refunded"): fails.append("F-0 partial refunds not counted as refunded transactions")
    lag=d.get("lag",{})
    mw=int(lag.get("monthly_window_days",0))
    if mw<30: fails.append(f"F-1 monthly observation window {mw}d < 30d (source band 30-45d)")
    aw=int(lag.get("annual_window_days",0))
    if aw<90: fails.append(f"F-1 annual observation window {aw}d < 90d operational floor (annual refunds arrive months later)")
    if lag.get("judged_before_lag_closed"): fails.append("F-1 cohort/experiment judged before the refund lag closed")
    if not lag.get("pricing_test_waits_full_cycle_plus_lag"): fails.append("F-1 pricing tests do not wait for a full billing cycle + refund lag")
    r=d.get("rate",{})
    rate=r.get("refund_rate_pct")
    if not r.get("band_classified"): fails.append("F-2 refund rate not classified on the benchmark band scale")
    if rate is None:
        warns.append("F-2 refund rate value unmeasured (band cannot be verified)")
    else:
        rate=float(rate)
        if rate>10: fails.append(f"F-2 refund rate {rate}% is in the critical band (>10%, store-action risk per source)")
        elif rate>=5 and not r.get("investigation_recorded"): fails.append(f"F-2 refund rate {rate}% is in the concerning band (5-10%) with no recorded investigation")
        elif rate>=5: warns.append(f"F-2 refund rate {rate}% in concerning band; investigation recorded")
    s=d.get("segmentation",{})
    if not s.get("weekly_review"): fails.append("F-3 refund data not reviewed weekly")
    for k,label in [("by_plan_duration","plan duration"),("by_region","region"),("by_price_tier","price tier"),("by_paywall_or_model","paywall/model"),("by_channel","channel"),("by_product","product")]:
        if not s.get(k): fails.append(f"F-3 refund rate not split by {label} (a single global rate hides the problem segment)")
    if not s.get("double_baseline_rule_recorded"): fails.append("F-3 no recorded rule that a segment at >=2x baseline is a product problem")
    if s.get("segment_over_2x_unflagged"): fails.append("F-3 a segment at >=2x baseline exists and was not flagged")
    c=d.get("consumption",{})
    if not c.get("handles_consumption_request"): fails.append("F-4 Apple CONSUMPTION_REQUEST not handled (Apple decides without the app's usage data)")
    if not c.get("response_within_12h"): fails.append("F-4 consumption response is not inside the 12-hour window")
    ret=int(c.get("retention_days",0))
    if ret<30: fails.append(f"F-4 consumption/usage data retained {ret}d < 30d (Apple guidance)")
    elif ret<60: warns.append(f"F-4 retention {ret}d meets the 30d floor but is below the 60d purchase-history guidance")
    if not c.get("original_transaction_id_stored"): fails.append("F-4 original transaction ID not stored per purchase")
    if not c.get("purchase_history_fields_recorded"): fails.append("F-4 purchase-history fields (txn/product/price/time/first use/usage/prior refunds) not recorded")
    if not c.get("owner_named"): fails.append("F-4 no named owner for the refund clocks (48h / 12h / 1 business day)")
    p=d.get("post_refund",{})
    if not p.get("access_revoked_on_refund"): fails.append("F-5 access is not revoked when a refund notification arrives")
    if not p.get("reason_code_and_product_logged"): fails.append("F-5 refund requests not logged with reason code + product ID")
    if not p.get("decision_log_kept"): fails.append("F-5 no refund decision log (reason / rule / outcome)")
    j=d.get("judgement",{})
    if not j.get("ltv_includes_refund"): fails.append("F-6 LTV/RPI ignore refunds (a 3-5% refund rate overstates acquisition ROI)")
    if not j.get("paywall_decisions_refund_adjusted"): fails.append("F-6 paywall/pricing decisions are not refund-adjusted")
    if j.get("model")=="hard" and not j.get("expectation_work_for_hard"):
        fails.append("F-6 hard paywall (refund benchmark 5.8% vs freemium 3.4%) without recorded expectation work (onboarding / value communication)")
    return fails,warns

if __name__=="__main__":
    d=json.load(open(sys.argv[1]))
    f,w=check(d)
    for x in w: print("WARN",x)
    for x in f: print("FAIL",x)
    print(f"RESULT {'PASS' if not f else 'FAIL'} fails={len(f)} warns={len(w)}")
    sys.exit(0 if not f else 1)
