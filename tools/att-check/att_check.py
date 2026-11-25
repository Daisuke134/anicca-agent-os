#!/usr/bin/env python3
"""ATT (App Tracking Transparency) permission funnel gate checker.
Sources (full-text read 2026-11-13):
 - AppsFlyer "Redefining ATT opt-in measurement for data accuracy"
   https://www.appsflyer.com/blog/measurement-analytics/att-opt-in-measurement/
   (true opt-in = only users who actually saw the prompt; true rate 40%;
    broader rate incl. restricted/system-denied = 30%; prompt shown after
    engagement 45% vs before SDK init 36%; exclude restricted / children /
    system-level off from the denominator)
 - Adrop "The Publisher's Guide to ATT Opt-In: The 1.6x eCPM Gap"
   https://adrop.io/en/adrop/adtech-att-consent-ecpm-guide
   (AdControl 8 months Jan-Aug 2026: opted-in eCPM ~1.6x opt-out, CTR 2.99%
    vs 1.69%; opted-in = 32% of impressions, 43% of revenue; exactly ONE
    system prompt per app; permitted: pre-permission prompt, timing after
    core-feature engagement, sparing Settings route; prohibited: incentives,
    feature gating, mimicking system UI, shaming, forced re-prompt)
 - Apple WWDC / AppTrackingTransparency (via search-result full text):
   NSUserTrackingUsageDescription required (app crashes without it if the
   prompt is shown), one-time prompt remembered until reinstall, check
   trackingAuthorizationStatus on every launch, track only when authorized.
Gates:
 A-0 decision: whether the app tracks across other companies' apps/sites is
     recorded. If it does not track, no prompt may be shown and the privacy
     label must say no tracking. If it does, a prompt plan must exist.
 A-1 purpose string: NSUserTrackingUsageDescription present, specific
     (names a user benefit), not a generic placeholder.
 A-2 timing & once: prompt NOT on first launch before value; timing is a
     named post-value moment; shown at most once per install.
 A-3 pre-prompt rules: a pre-prompt exists, explains the benefit, does not
     mimic system UI, offers no incentive, gates no feature, does not shame.
 A-4 denominator: opt-in rate = authorized / (authorized+denied) among users
     who actually saw the prompt; restricted / system-off / children are
     excluded and recorded separately; statuses split; split by timing and
     by country.
 A-5 level: when measured with n>=100 prompt-seen users, true opt-in below
     20% fails (BROKEN), below 40% (AppsFlyer true rate) warns.
 A-6 denied handling: no re-prompt attempt; Settings route, if any, is
     sparing and non-obstructive; app is fully functional without tracking;
     an aggregated fallback (SKAdNetwork / AdAttributionKit / store
     analytics) is in place.
"""
import json, sys

POST_VALUE_TIMINGS = {"after_onboarding", "after_first_value", "after_core_action", "after_first_success"}

def main(path):
    d = json.load(open(path))
    fails, warns = [], []
    tracks = d.get("tracks_across_apps")
    if tracks is None:
        fails.append("A-0 tracking decision is not recorded (does the app track across other companies' apps/sites?)")
        tracks = True  # judge the prompt path as well
    if tracks is False:
        if d.get("prompt_shown"):
            fails.append("A-0 app declares no tracking but shows the ATT prompt")
        if not d.get("privacy_label_says_no_tracking"):
            fails.append("A-0 privacy label does not record 'no tracking'")
        # non-tracking path ends here
        return fails, warns
    # A-1
    ps = (d.get("purpose_string") or "").strip()
    if not ps:
        fails.append("A-1 NSUserTrackingUsageDescription is missing")
    else:
        if len(ps) < 20:
            fails.append("A-1 purpose string is too short to be specific")
        if ps.lower() in ("tracking", "we track you", "for ads", "advertising"):
            fails.append("A-1 purpose string is a generic placeholder")
        if not any(k in ps.lower() for k in ("personal", "relevant", "recommend", "experience", "free", "improve", "measure")):
            warns.append("A-1 purpose string names no user benefit keyword (personal/relevant/recommend/experience/free/improve/measure)")
    # A-2
    timing = d.get("prompt_timing")
    if timing == "first_launch_immediate":
        fails.append("A-2 prompt fires immediately on first launch, before value")
    elif timing not in POST_VALUE_TIMINGS:
        fails.append(f"A-2 prompt_timing {timing!r} is not a named post-value moment")
    if d.get("prompt_max_shows_per_install") != 1:
        fails.append("A-2 system prompt must be shown at most once per install")
    # A-3
    pp = d.get("preprompt") or {}
    if not pp.get("exists"):
        fails.append("A-3 no pre-permission prompt before the system prompt")
    else:
        if not pp.get("explains_benefit"): fails.append("A-3 pre-prompt does not explain the benefit")
        if pp.get("mimics_system_ui"): fails.append("A-3 pre-prompt mimics the system UI (prohibited)")
        if pp.get("offers_incentive"): fails.append("A-3 incentive offered for consent (prohibited)")
        if pp.get("gates_features"): fails.append("A-3 functionality gated on consent (prohibited)")
        if pp.get("shames_decline"): fails.append("A-3 pre-prompt shames declining (prohibited)")
    # A-4 / A-5
    m = d.get("measurement") or {}
    if not m.get("statuses_split"):
        fails.append("A-4 ATT statuses (authorized/denied/restricted/not_determined) are not recorded separately")
    if not m.get("denominator_excludes_restricted"):
        fails.append("A-4 denominator does not exclude restricted / system-off / children (true rate = prompt-seen only)")
    if not m.get("split_by_timing"): fails.append("A-4 opt-in is not split by prompt timing")
    if not m.get("split_by_country"): fails.append("A-4 opt-in is not split by country")
    n = m.get("prompt_seen_users") or 0
    rate = m.get("true_opt_in_rate")
    if rate is None:
        warns.append("A-5 true opt-in rate is unmeasured")
    elif n >= 100:
        if rate < 0.20: fails.append(f"A-5 true opt-in {rate:.0%} is BROKEN (<20%, prompt-seen denominator)")
        elif rate < 0.40: warns.append(f"A-5 true opt-in {rate:.0%} is below the AppsFlyer true rate of 40%")
    # A-6
    dh = d.get("denied_handling") or {}
    if dh.get("reprompt_attempted"): fails.append("A-6 re-prompt attempted after denial (prohibited / impossible)")
    if not dh.get("app_fully_functional_without_tracking"): fails.append("A-6 app is not fully functional without tracking")
    if not dh.get("aggregated_fallback"): fails.append("A-6 no aggregated fallback (SKAdNetwork/AdAttributionKit/store analytics)")
    if dh.get("settings_route") and not dh.get("settings_route_sparing"): warns.append("A-6 Settings route exists but is not recorded as sparing/non-obstructive")
    return fails, warns

if __name__ == "__main__":
    fails, warns = main(sys.argv[1])
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    sys.exit(0 if not fails else 1)
