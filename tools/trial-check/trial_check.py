#!/usr/bin/env python3
"""trial-check: deterministic gate for free-trial length / conversion / reminders.
Stdlib only, offline, free. Sources (read in full this run):
- RevenueCat, "How long should your free trial be? Data from 17,000+ apps"
  (Aug 2025-Jul 2026): overall trial-to-paid median 42.5% at 17-32d vs 25.5% at <=4d;
  weekly conv 22.3% (<=4d) -> 24.3% (5-9d), first renewal 57.9% -> 65.9%;
  monthly conv 39.6% -> 45.9% (5-9d) -> 46.6% (10-16d, peak) -> 43.7% (17-32d),
  renewal 54.2% -> 62.8% -> 72.0% -> 77.5%; annual conv 24.0% -> 33% -> 43% -> 44.6%,
  renewal 18.3% -> 25.3% -> 36.4% -> 47.5% (both rise with length);
  Health & Fitness monthly conv 46.8% (5-9d) > 40.4% (10-16d) while renewal rises
  51.5% -> 77.1% with length; AI monthly conv falls 38.5% -> 31.8% past 16d (wall);
  no-trial renewal weekly 35.9% / monthly 49.5% (below trialled);
  explicit caveat: correlation, not causation (survivorship).
  https://www.revenuecat.com/blog/growth/free-trial-length
- Admiral Media trial guide (RevenueCat State of Subscription Apps 2026,
  115,000+ apps): Day-0 share OF CANCELLATIONS: 3d trials 55.4% on day 0, 84% day 0-1;
  7d 64% day 0-1; 30d ~31% day 0. Framework: anchor length to time-to-value,
  engineer the first hour (first session delivers core outcome, not a tour),
  match trial to plan, judge on cost per paid subscriber + day-60 revenue per
  install (never trial-to-paid alone), measure at cohort level incl. retry window.
  https://admiral.media/app-free-trial-optimization/
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    plans = d.get("plans") or {}
    # T-0 existence per sold plan
    for name in ("weekly","monthly","annual"):
        p = plans.get(name) or {}
        if p.get("sold") and (p.get("trial_days") is None):
            fails.append(f"T-0 {name} is sold but its trial length is not recorded (an unrecorded length is an undecided length)")
        if p.get("sold") and (p.get("trial_days") or 0) == 0:
            fails.append(f"T-0 {name} is sold with no trial at all (no-trial renewal is lower on weekly/monthly -- 35.9%/49.5% vs 57.9%+/54.2%+ trialled -- so a zero trial must be a tested choice with a recorded result, not a default absence; in-house target spec 2026-11-05 already decided trials for weekly and annual)")
    # T-1 plan-matched bands
    w = (plans.get("weekly") or {}).get("trial_days") or 0
    m = (plans.get("monthly") or {}).get("trial_days") or 0
    a = (plans.get("annual") or {}).get("trial_days") or 0
    if (plans.get("weekly") or {}).get("sold") and w and not (5 <= w <= 9):
        fails.append(f"T-1 weekly trial is {w}d, outside the evidenced 5-9d band (conv 24.3% / renewal 65.9% at 5-9d vs 22.3% / 57.9% at <=4d; >9d weekly evidence is <20 apps in the primary and cannot support a longer pick)")
    if (plans.get("monthly") or {}).get("sold") and m and not (5 <= m <= 16):
        fails.append(f"T-1 monthly trial is {m}d, outside 5-16d (conversion peaks at 10-16d, 46.6%; 17-32d converts lower at 43.7% overall and AI monthly falls to 31.8% past 16d -- longer is not free)")
    if (plans.get("monthly") or {}).get("sold") and m and m <= 4:
        fails.append(f"T-1 monthly trial is only {m}d (<=4d converts 39.6% vs 45.9-46.6% at 5-16d and renews 54.2% vs 62.8-72.0%)")
    if (plans.get("annual") or {}).get("sold") and a and a <= 4:
        fails.append(f"T-1 annual trial is only {a}d (annual is the one plan where both conversion and renewal rise monotonically with length: 24.0%/18.3% at <=4d vs 43%/36.4% at 10-16d and 44.6%/47.5% at 17-32d -- a 3-day annual trial leaves the largest evidenced gap on the table)")
    if (plans.get("annual") or {}).get("sold") and a and a > 32:
        fails.append(f"T-1 annual trial is {a}d, beyond the longest evidenced band (17-32d); beyond-band lengths delay revenue with no benchmark support")
    # T-2 time-to-value anchor
    act = d.get("activation") or {}
    if not act.get("event_defined"):
        fails.append("T-2 no activation (aha) event is defined (both primaries require anchoring length to time-to-value; a length picked without the event it must cover is a copied round number)")
    if act.get("median_days_to_aha") is None:
        fails.append("T-2 median days to the activation event is not recorded (length should be ~2-3x that median; without the median the multiple cannot be checked)")
    if not act.get("length_multiple_recorded"):
        fails.append("T-2 the length-to-aha multiple / justification is not recorded per plan")
    # T-3 first hour + Day-0 diagnosis
    fh = d.get("first_hour") or {}
    if not fh.get("core_outcome_in_first_session"):
        fails.append("T-3 the first session after trial start does not deliver the core outcome (Admiral: onboarding and trial start are one flow -- the paywall makes a promise and the next screen must keep it; a tour does not)")
    if not fh.get("day0_cancel_share_tracked"):
        fails.append("T-3 the day-0 share of trial cancellations is not tracked (for 3d trials 55.4% of cancellations land on day 0 and 84% by day 1 -- without this split a first-session failure is invisible and gets misread as a length problem)")
    # T-4 judgement bundle
    ms = d.get("measurement") or {}
    if not ms.get("trial_to_paid_tracked"):
        fails.append("T-4 trial-to-paid conversion is not tracked by plan")
    if not ms.get("first_renewal_tracked"):
        fails.append("T-4 first renewal of trial converts is not tracked (length moves renewal independently of conversion -- monthly renewal 54.2%->77.5% across bands; a conversion-only win that loses renewal is a failure)")
    if not ms.get("revenue_per_install_tracked"):
        fails.append("T-4 revenue per install (day-35/60) is not tracked (Admiral/RevenueCat: score length tests on cost per paid subscriber and RPI, not trial-to-paid alone -- longer trials delay cash and can win conversion while losing the business)")
    if not ms.get("refund_rate_tracked"):
        fails.append("T-4 refund rate of trial converts is not tracked (a harder/longer trial can win on count and lose on refunds and angry reviews; refunds sit next to conversion on the same cohort)")
    if not ms.get("split_by_plan"):
        fails.append("T-4 metrics are not split by plan (weekly/monthly/annual favour different lengths -- annual rises monotonically, monthly peaks at 10-16d; a blended rate hides the plan that is wrong)")
    if ms.get("primary_metric") == "trial_to_paid_only":
        fails.append("T-4 trial-to-paid alone is the primary metric (explicitly rejected by both primaries; the bundle is conversion + first renewal + revenue per install + refunds)")
    if not ms.get("cohort_window_includes_retry"):
        warns.append("T-4 cohort window does not include the billing-retry window end (conversions landing in retry get undercounted; warning only)")
    # T-5 correlation discipline
    cl = d.get("claims") or {}
    if cl.get("asserts_longer_causally_better"):
        fails.append("T-5 'longer trials cause higher conversion' is asserted as causal (the primary itself flags survivorship: a user still present on day 25 was always likelier to pay -- the median is a test hypothesis, not a setting to copy)")
    if cl.get("headline_median_copied_without_plan_split"):
        fails.append("T-5 the headline 42.5% vs 25.5% median was copied as a single setting without the plan split (the same primary shows monthly peaking at 10-16d and Health & Fitness monthly converting better at 5-9d -- one number for all plans contradicts the source)")
    # T-6 reminders / no surprise charge
    rm = d.get("reminder") or {}
    if not rm.get("implemented"):
        fails.append("T-6 no pre-charge trial reminder is implemented (stores/RevenueCat send no days-before webhook -- the reminder must be scheduled from expiration_at at trial start; a spec for a reminder is not a reminder)")
    if rm.get("implemented") and not rm.get("in_app_banner"):
        warns.append("T-6 reminder relies on push alone with no in-app banner (push reaches only permission-granted users; the in-house spec makes the banner the primary channel -- warning only)")
    if not rm.get("timing_by_plan_recorded"):
        fails.append("T-6 reminder timing by plan is not recorded (weekly: day before only; 14d+: 3 days before + day before -- one timing for all lengths fires mid-experience on short trials)")
    if rm.get("implemented") and not rm.get("suppresses_cancelled_or_converted"):
        fails.append("T-6 reminders are not suppressed for already-cancelled or already-converted users (reminding a cancelled user to keep a trial they ended is a trust and complaint risk; re-check state at fire time)")
    if rm.get("discount_in_reminder"):
        fails.append("T-6 the reminder carries a discount (the reminder's job is an informed stay/leave decision; buying the stay with a discount repeats the cancel-screen error both retention primaries reject)")
    if not rm.get("terms_clear_on_paywall"):
        fails.append("T-6 trial terms (end date + first charge amount) are not clear on the paywall (surprise charges are the fastest route to refunds and one-star reviews)")
    # T-7..T-10 reminder sequence + delivery architecture (added 2026-11-22).
    # Source (read in full): RevenueCat engineering, "How to add trial
    # notifications to your subscriptions" (pub 2026-04-22, upd 2026-09-11):
    # a lightweight THREE-notification pattern -- (1) activation nudge on day 0
    # highlighting a feature not yet tried, to reach the first aha during the
    # trial; (2) mid-trial reminder two days before end (cancellations here are
    # expected and are a win-back capture chance, not a failure); (3) trial-
    # ending alert on the morning of the last day, transparent wording ("Your
    # trial ends today. Keep access by staying on your plan -- or cancel
    # anytime."). Delivery: LOCAL schedules from the entitlement expirationDate
    # but can only update when the app opens (a store-side cancel is invisible
    # until then; device-off / Android exact-time limits also apply); REMOTE
    # listens to RevenueCat webhooks (INITIAL_PURCHASE / CANCELLATION /
    # EXPIRATION / TRIAL_CONVERTED), stores push tokens in Attributes
    # ($apnsTokens/$fcmTokens), cancels immediately on unsubscribe, and can
    # change content without an app update. Optional section for backward
    # compatibility: absent = WARN (unknown), never a silent pass.
    # https://www.revenuecat.com/blog/engineering/how-to-add-trial-notifications-to-your-subscriptions
    rs = d.get("reminder_sequence")
    if rs is None:
        warns.append("T-7 reminder_sequence section is absent (the 3-touch sequence and delivery architecture are unknown, not passed -- RevenueCat primary, 2026-04-22)")
    else:
        if not rs.get("activation_nudge_same_day"):
            fails.append("T-7 no same-day activation nudge (touch 1 of 3: day-0, highlights an untried feature so the first aha lands inside the trial; a reminder set that only speaks at expiry wastes the trial's first day)")
        if not rs.get("midtrial_reminder_2d_before"):
            fails.append("T-7 no mid-trial reminder two days before end (touch 2 of 3; cancellations surfacing here are expected -- they convert a surprise charge into an informed exit and a win-back capture chance)")
        if not rs.get("ending_alert_morning_last_day"):
            fails.append("T-7 no trial-ending alert on the morning of the last day (touch 3 of 3; if expiry falls in the morning, the primary schedules it the previous evening -- a single mid-trial ping is not the sequence)")
        if rs.get("activation_nudge_same_day") and not rs.get("activation_nudge_targets_untried_feature"):
            fails.append("T-8 the activation nudge does not target an untried feature / the aha (its job is activation, not a generic 'your trial started' receipt; a content-free day-0 push trains users to ignore the later two touches)")
        arch = rs.get("architecture")
        if arch not in ("local", "remote", "hybrid"):
            fails.append("T-9 delivery architecture is not recorded as local / remote / hybrid (the two have opposite failure modes -- local goes stale until the next app open, remote needs a webhook backend; an unrecorded choice cannot be audited)")
        if arch == "local" and not rs.get("local_resync_on_open"):
            fails.append("T-9 local-only reminders with no resync-on-open recorded (local schedules only update when the app opens: a user who cancelled in store settings keeps getting 'keep your trial' reminders until they reopen the app -- the primary states this trade-off explicitly)")
        if arch in ("remote", "hybrid"):
            if not rs.get("push_token_in_attributes"):
                fails.append("T-9 remote/hybrid delivery but push tokens are not stored in subscriber Attributes ($apnsTokens/$fcmTokens) (without the token in Attributes the webhook backend has no address to send to)")
            if not rs.get("webhook_cancels_on_unsubscribe"):
                fails.append("T-9 remote/hybrid delivery but webhooks do not cancel reminders on unsubscribe/CANCELLATION (immediate cancellation without an app open is the entire reason to pay the backend cost)")
        if not rs.get("scheduled_from_expiration_at"):
            fails.append("T-10 reminders are not scheduled from the entitlement expiration date at trial start (no store or RevenueCat webhook fires days before conversion -- the schedule must be derived from expiration_at when the trial begins, not polled for later)")
        if not rs.get("ending_alert_shows_price_and_cancel_path"):
            fails.append("T-10 the ending alert does not show the first-charge price and how to cancel (the primary's model wording pairs 'keep access' with 'cancel anytime'; hiding the cancel path in the last touch is the surprise-charge pattern that produces refunds and one-star reviews)")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
