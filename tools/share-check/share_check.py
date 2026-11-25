#!/usr/bin/env python3
"""Gate SH-0..SH-6: content-share loop for a consumer app.
Sources: Insert Affiliate case studies of Duolingo/Calm/Strava referral loops (full read 2026-11-14,
https://insertaffiliate.com/blog/duolingo-calm-strava-referral-loops-scale/) - 5 common principles:
(1) sharing built into the experience, not bolted on; (2) shared content has standalone value before install;
(3) social proof visible; (4) rewards dual-sided; (5) sharing opportunities recur, not once.
Plus Calm lesson: frame sharing as generosity/gifting, not promotion. Appalize growth-loops: K = shares per user x conversion per share.
Stdlib only. Usage: share_check.py <state.json>; exit 0 PASS, 1 FAIL.
"""
import json, sys
def check(s):
    fails, warns = [], []
    if not s.get("share_exists"): fails.append("SH-0: no content-share surface exists at all")
    if not s.get("shared_content_standalone_value"): fails.append("SH-1: shared asset has no standalone value (recipient gets nothing useful before installing)")
    if not s.get("shared_asset_carries_brand"): fails.append("SH-1b: shared asset carries no brand attribution at all")
    if not s.get("share_includes_tappable_link"): fails.append("SH-2: share includes no tappable link (App Store / universal / deferred deep link); plain-text domain does not convert or attribute")
    if not s.get("share_link_attributed"): fails.append("SH-2b: share link carries no attribution parameter, so share->install cannot be measured")
    if not s.get("share_builtin_not_bolted"): fails.append("SH-3: sharing is a bolted-on generic 'share this app' button, not built into the core content experience")
    if not s.get("share_prompt_at_value_moment"): fails.append("SH-3b: no share prompt at a value moment (e.g. after saving/favoriting the content that helped)")
    if not s.get("share_framed_as_gift"): fails.append("SH-3c: sharing framed as promotion, not generosity ('send this to someone who needs it' - Calm gifting lesson)")
    if not s.get("share_recurs"): fails.append("SH-4: sharing opportunity is one-off, not recurring with each new content item/day")
    if s.get("share_forced"): fails.append("SH-5: sharing is forced/gated (creates resentment; must stay optional)")
    if not s.get("share_event_defined"): fails.append("SH-6: no share analytics event defined")
    if s.get("share_event_defined") and not s.get("share_event_fired_on_completion"): fails.append("SH-6b: share event is defined but never fired (no completion handler on the share sheet); shares, channel and completion are unmeasured")
    if not s.get("k_factor_measured"): fails.append("SH-6c: K-factor (shares per user x conversion per share) is not measured")
    if not s.get("dual_sided_benefit"): warns.append("SH-W: no dual-sided benefit beyond the content itself (referrer/recipient reward is referral-gate territory; content-as-gift counts as recipient benefit)")
    return fails, warns
def main():
    s = json.load(open(sys.argv[1]))
    fails, warns = check(s)
    for w in warns: print("WARN", w)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
