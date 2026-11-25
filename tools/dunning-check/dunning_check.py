#!/usr/bin/env python3
"""dunning-check: deterministic gate for involuntary (billing-error) churn recovery.
Stdlib only, offline, free. Sources (in-house primaries, read in full when written):
- affirmation-involuntary-churn-recovery-spec-2026-11-05 (RevenueCat, Google Play billing
  error churn, 2026-04-02, full 219 lines): billing errors are 15.2% of App Store and
  32.3% of Google Play cancellations (RevenueCat State of Subscription Apps 2026,
  115,000+ apps / $16B); Apple retries 60 days automatically; Billing Grace Period is
  the developer switch, 28 days resolves ~90% of issues (Apple data); defaults alone
  recover ~10-15%, grace + account hold optimisation ~33%, full stack (Truecaller)
  40%; trigger is the RevenueCat BILLING_ISSUE event (not CANCELLATION, which is too
  late); pushes Day 0 / 1-3 / 7 / 14 then stop (diminishing returns), stop instantly
  on RENEWAL, hand off to win-back on EXPIRATION; grace-period UI is non-blocking,
  modal only after access stops; tone never blames the user; no discount (a card
  problem is not a price problem); no pre-dunning email to active users.
  https://www-docs.revenuecat.com/blog/growth/google-play-billing-error-churn-how-to-fix/
- Apple official correction recorded 2026-11-08 in the same spec: grace choices are
  3/16/28 days but weekly plans are capped at an effective 6 days; scope is All
  Renewals vs Only Paid to Paid Renewals (only All Renewals covers trial->paid
  failures); the setting is per-app, not per-product.
  https://developer.apple.com/help/app-store-connect/manage-subscriptions/enable-billing-grace-period-for-auto-renewable-subscriptions/
- grace-period-surge-early-warning-spec-2026-11-11 (CancelFlow + AppCherish, full
  reads): grace period is opt-in and OFF by default (retry != grace); three settings
  decisions = duration / scope / environment (Sandbox Only vs Production and Sandbox
  -- a sandbox-only setting is effectively no setting); state subtypes must stay
  separate (DID_FAIL_TO_RENEW+GRACE_PERIOD = recoverable, GRACE_PERIOD_EXPIRED,
  DID_RENEW+BILLING_RECOVERY = saved, EXPIRED+BILLING_RETRY = final churn); read
  inflow RATE (grace entries / renewal attempts, typical band ~2-4% as a reference
  only), surge = 2-3x own baseline; within-grace resolution rate (healthy reference
  60-70%) is a SEPARATE metric from the full-window BILLING_ISSUE->RENEWAL recovery
  rate and the two are never merged.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app, grace_period:{recorded, enabled, duration_days, scope,
 environment, weekly_cap_understood}, trigger_event, involuntary_separated_from_voluntary,
 discount_offered_to_billing_error, access:{continues_in_grace, non_blocking_ui_in_grace,
 modal_only_after_grace, one_tap_manage_link, in_app_payment_form},
 messaging:{touches_days, weekly_touches_days, stops_on_renewal, stops_on_expiration_to_winback,
 quiet_hours_respected, tone, names_specific_loss, pre_dunning_email_to_active},
 state_separation:{subtypes_distinguished, entitlement_from_live_state},
 surge:{inflow_rate_tracked, denominator, surge_threshold_defined, resolution_rate_within_grace_tracked,
 resolution_rate_merged_with_full_recovery},
 measurement:{denominator, recovery_rate_tracked, billing_issue_mrr_share_tracked,
 split_by_plan, benchmark_recorded}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    g = d.get("grace_period") or {}
    if not g.get("recorded"):
        fails.append("D-0 grace period setting is not recorded from App Store Connect (a spec saying 'set it to 28 days' is not a setting; the in-house spec's completion condition 1 has been open since 2026-11-05)")
    if not g.get("enabled"):
        fails.append("D-0 Billing Grace Period is not enabled (it is opt-in and OFF by default -- Apple's 60-day retry runs anyway, but without grace the subscriber's paid service pauses on the first failed renewal)")
    if g.get("duration_days") not in (28,):
        fails.append(f"D-1 grace duration is {g.get('duration_days')!r} days, not 28 (Apple offers 3/16/28; ~90% of billing issues resolve within 28 days and 28 days covers 47% of the 60-day retry window vs 5% at 3 days)")
    if g.get("scope") != "all_renewals":
        fails.append(f"D-1 grace scope is {g.get('scope')!r}, not all_renewals (Only Paid to Paid leaves trial->paid failures -- the highest-value first charges -- outside grace entirely)")
    if g.get("environment") != "production_and_sandbox":
        fails.append(f"D-1 grace environment is {g.get('environment')!r}, not production_and_sandbox (a sandbox-only setting is effectively no setting for real subscribers)")
    if not g.get("weekly_cap_understood"):
        fails.append("D-1 weekly-plan effective cap (6 days even when 28 is selected) is not recorded as understood (weekly recovery windows and messaging must be compressed to days 0-3, not run on the monthly cadence)")
    if d.get("trigger_event") != "BILLING_ISSUE":
        fails.append(f"D-2 recovery trigger is {d.get('trigger_event')!r}, not BILLING_ISSUE (CANCELLATION with cancel_reason BILLING_ERROR fires after the fact -- recovery started there starts late by construction)")
    if not d.get("involuntary_separated_from_voluntary"):
        fails.append("D-2 involuntary (billing-error) churn is not separated from voluntary churn (they have different causes, tools and tones; one flow for both fixes neither)")
    if d.get("discount_offered_to_billing_error"):
        fails.append("D-2 a discount is offered for a billing error (a card problem is not a price problem; discounting it burns margin and cannot fix the card)")
    a = d.get("access") or {}
    if not a.get("continues_in_grace"):
        fails.append("D-3 paid access does not continue during grace (continuation is the entire point of grace; locking the user out converts a recoverable failure into a re-decision at a paywall)")
    if not a.get("non_blocking_ui_in_grace"):
        fails.append("D-3 in-grace UI is blocking or absent (during grace the only UI is a non-blocking banner/snackbar; the user has done nothing wrong)")
    if not a.get("modal_only_after_grace"):
        fails.append("D-3 modal escalation is not reserved for after grace expiry (a modal while access still continues punishes a user whose card, not intent, failed)")
    if not a.get("one_tap_manage_link"):
        fails.append("D-3 no one-tap path to payment management (StoreKit showManageSubscriptions / RevenueCat managementURL; a fix that takes hunting for will not happen inside a 6-day weekly window)")
    if a.get("in_app_payment_form"):
        fails.append("D-3 an in-app payment form exists (payment methods cannot be edited in-app for store billing; a home-built form is dead friction -- link out to the store's management screen)")
    m = d.get("messaging") or {}
    touches = m.get("touches_days") or []
    if touches != [0, 2, 7, 14]:
        fails.append(f"D-4 monthly/annual push cadence is {touches!r}, not [0, 2, 7, 14] (Day 0 on BILLING_ISSUE, one touch in days 1-3, Day 7, Day 14, then stop -- after Day 14 returns diminish and extra touches are harassment)")
    wt = m.get("weekly_touches_days") or []
    if not wt or max(wt) > 3:
        fails.append(f"D-4 weekly cadence is {wt!r} (the weekly grace window is effectively 6 days; touches must be compressed inside days 0-3, not spread over the monthly schedule)")
    if not m.get("stops_on_renewal"):
        fails.append("D-4 messaging does not stop instantly on RENEWAL (telling a recovered subscriber to fix their payment trains distrust in every future message)")
    if not m.get("stops_on_expiration_to_winback"):
        fails.append("D-4 on EXPIRATION the flow does not stop and hand off to win-back (dunning and win-back in one flow means discount offers land on card problems and recovery pushes land on people who already left)")
    if not m.get("quiet_hours_respected"):
        fails.append("D-4 quiet hours are not respected (in-house push rule: nothing between 22:00 and 08:00)")
    if m.get("tone") != "non_blaming_card_problem":
        fails.append(f"D-4 message tone is {m.get('tone')!r}, not non_blaming_card_problem (the user did nothing wrong -- the card did; threatening or shaming copy is the documented anti-pattern)")
    if not m.get("names_specific_loss"):
        fails.append("D-4 messages do not name the specific loss (streak / saved affirmations by name; a generic 'payment problem' gives no reason to act now)")
    if m.get("pre_dunning_email_to_active"):
        fails.append("D-4 pre-dunning warnings are sent to active users before any failure (asking people to reconsider continuing before anything failed manufactures churn; in-app prompts only)")
    s = d.get("state_separation") or {}
    if not s.get("subtypes_distinguished"):
        fails.append("D-5 notification subtypes are not distinguished (GRACE_PERIOD entry, GRACE_PERIOD_EXPIRED, BILLING_RECOVERY and final BILLING_RETRY expiry are four different states; a single subscribed/not flag mislabels recoverable subscribers as churned)")
    if not s.get("entitlement_from_live_state"):
        fails.append("D-5 entitlement is not read from live store/RevenueCat state (a cached boolean closes the gate on grace-period subscribers who are still entitled)")
    su = d.get("surge") or {}
    if not su.get("inflow_rate_tracked"):
        fails.append("D-6 grace inflow is tracked as counts, not as a rate (counts rise with the subscriber base; the rate -- entries / renewal attempts -- is the early-warning signal that precedes churn data by days)")
    if su.get("denominator") != "renewal_attempts":
        fails.append(f"D-6 inflow-rate denominator is {su.get('denominator')!r}, not renewal_attempts")
    if not su.get("surge_threshold_defined"):
        fails.append("D-6 no surge threshold is defined (own baseline x2 = watch, x3 = surge, triaged the same week: cohort cluster, then external Apple outage, then price-change cohort)")
    if not su.get("resolution_rate_within_grace_tracked"):
        fails.append("D-6 within-grace resolution rate is not tracked (it is the first number that moves after a grace change and the denominator/window differ from full-window recovery)")
    if su.get("resolution_rate_merged_with_full_recovery"):
        fails.append("D-6 within-grace resolution is merged with full-window recovery (different windows -- grace days vs the full 60-day retry -- merged into one rate they describe neither)")
    me = d.get("measurement") or {}
    if me.get("denominator") != "billing_issue_events":
        fails.append(f"D-7 recovery denominator is {me.get('denominator')!r}, not billing_issue_events (recovery = BILLING_ISSUE starts that reach RENEWAL, on a fixed window; any other denominator inflates or hides the leak)")
    if not me.get("recovery_rate_tracked"):
        fails.append("D-7 recovery rate is not tracked (defaults alone recover ~10-15% and optimised grace ~33% -- without the rate there is no way to know which side of that gap the app is on)")
    if not me.get("billing_issue_mrr_share_tracked"):
        fails.append("D-7 the Billing Issue cohort's share of MRR is not tracked (that share is the money at risk this week, and the before/after test of any grace change within one billing cycle)")
    if not me.get("split_by_plan"):
        fails.append("D-7 recovery is not split by plan (weekly has a 6-day window and monthly/annual 28 -- an unsplit average hides a broken weekly window inside a healthy annual one)")
    if not me.get("benchmark_recorded"):
        warns.append("D-7 no recovery benchmark recorded (reference only, never a target: defaults ~10-15%, grace+hold optimisation ~33%, full stack ~40% -- and billing errors are 15.2% of App Store cancellations)")
    # D-8 recovery surface (added 2026-11-22, RevenueCat Codelabs primary read in full:
    # https://revenuecat.github.io/codelabs/recover-involuntary-churn-billing-retry.html )
    # Optional section for backward compatibility: absence is WARN (unknown), never PASS.
    rs = d.get("recovery_surface")
    if rs is None:
        warns.append("D-8 recovery_surface is not recorded (detection signal, fix surface, Play two-phase state and sandbox E2E are unknown -- unrecorded is not compliant)")
    else:
        if rs.get("detection_signal") != "isActive_and_billingIssueDetectedAt":
            fails.append(f"D-8 detection signal is {rs.get('detection_signal')!r}, not isActive_and_billingIssueDetectedAt (the codelab's exact signal: entitlement stays isActive=true in grace and billingIssueDetectedAt is set; unsubscribeDetectedAt is the voluntary signal and must never drive the billing banner)")
        if not rs.get("checked_on_foreground"):
            fails.append("D-8 billing-issue state is not checked on app foreground (a check only at cold start misses failures that begin mid-session)")
        if not rs.get("customerinfo_listener_clears_banner"):
            fails.append("D-8 no CustomerInfo listener clears the banner on recovery (billingIssueDetectedAt clears when payment recovers; a banner that survives recovery trains distrust, same failure as messaging that does not stop on RENEWAL)")
        fix = rs.get("fix_surface")
        if fix not in ("customer_center", "management_url"):
            fails.append(f"D-8 fix surface is {fix!r} (must be customer_center or management_url -- the two routes the primary supports; a home-built screen is dead friction, see D-3)")
        if fix == "customer_center" and not rs.get("customer_center_plan_eligible"):
            fails.append("D-8 Customer Center is claimed but plan eligibility is not recorded (Customer Center requires a RevenueCat Pro or Enterprise plan; without eligibility the recorded route must be management_url)")
        if fix == "management_url" and not rs.get("management_url_null_guarded"):
            fails.append("D-8 managementURL is opened without a null guard (managementURL can be null with no active store subscription and is unsupported for Amazon/Stripe; an unguarded open crashes or dead-ends exactly the users in billing retry)")
        if not rs.get("webhook_deadline_from_event"):
            fails.append("D-8 out-of-app dunning does not take its deadline from the BILLING_ISSUE event's grace_period_expiration_at_ms (the deadline is a real field on the event when grace is configured; an invented or fixed-day deadline can promise time the store will not give, or cut time it would)")
        gp = rs.get("google_play") or {}
        if rs.get("android_sold"):
            if not gp.get("two_phase_recorded"):
                fails.append("D-8 Google Play two-phase state is not recorded (Play is grace period -- access kept -- then account hold -- access lost while retry continues; treating Play like Apple's single phase misstates when access stops)")
            if not gp.get("per_base_plan_recorded"):
                fails.append("D-8 Play grace/hold are not recorded per base plan (on Play the setting lives on each subscription's base plan, not per-app as on Apple; one recorded value does not cover all products)")
            if gp.get("grace_plus_hold_days") is not None and gp.get("grace_plus_hold_days") < 30:
                fails.append(f"D-8 Play grace+hold totals {gp.get('grace_plus_hold_days')} days, below the 30-day minimum (grace plus account hold must total at least 30 days)")
            if not gp.get("values_read_live_not_hardcoded"):
                fails.append("D-8 Play grace/hold values are hardcoded (since 2025-12-01 Google auto-calculates hold as 60 days minus grace by default; read the live Console values instead of baking in numbers that silently drift)")
        elif not gp.get("not_applicable_reason"):
            fails.append("D-8 android_sold is false/absent but no not-applicable reason is recorded for the Play two-phase checks (an unrecorded platform scope is an unknown, not an exemption)")
        if not rs.get("sandbox_e2e_verified"):
            fails.append("D-8 the recovery loop has not been verified end-to-end in sandbox (primary's 5-step check: enable grace in sandbox, trigger a renewal failure, confirm entitlement isActive + billingIssueDetectedAt set and banner appears, confirm BILLING_ISSUE webhook carries grace_period_expiration_at_ms, recover payment and confirm banner clears and RENEWAL arrives; sandbox timing is store-controlled and accelerated, so behaviour is verified live, never assumed)")
    return fails, warns

def main():
    with open(sys.argv[1]) as fh:
        d = json.load(fh)
    fails, warns = check(d)
    for w in warns:
        print(f"WARN {w}")
    for f in fails:
        print(f"FAIL {f}")
    print(f"{'PASS' if not fails else 'FAIL'} {d.get('app','?')}: {len(fails)} fail(s), {len(warns)} warning(s)")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
