#!/usr/bin/env python3
"""alternate-icon-check: deterministic gate for alternate app icons
(seasonal / perk / PPO variants). Stdlib only, offline, free.
Sources (read this run):
- Apple App Review Guidelines 2.3.8 / HIG via Mockiso guide (2026):
  icons incl. alternate icons must be similar to the app name/primary icon,
  suitable for 4+, rights cleared (2.3.9); PPO icon tests need every variant
  inside the binary of the published app (icon test = new version first).
  https://mockiso.com/blog/app-store-icon-requirements
- Apple alternate-icon mechanism (iOS 10.3+, setAlternateIconName):
  alternate icons must be included as files at submission/review; the system
  shows a confirmation alert on change; HIG prohibits changing the icon
  without user request. First movers MLB/NHL user-selectable icons.
  https://forums.appleinsider.com/discussion/199367
- Winner practice, Duolingo (successful consumer app, company statement via
  Distractify/TechBriefly): limited-time icon changes (melting / sick Duo)
  whose stated purpose is "to encourage learners to open the app"; Super and
  Streak Society icons are paid/streak perks, reverting to default when the
  subscription ends. https://techbriefly.com/2023/10/20/melting-duolingo-app-icon-confuses/
  https://duolingoguides.com/how-to-change-duolingo-app-icon/
Exit 0 = PASS, 1 = FAIL."""
import json, sys
def check(d):
    f=[]
    v=d.get("variants") or {}
    if not d.get("primary_icon_recorded"): f.append("AI-0 primary icon is not recorded (alternates are judged against the primary; no primary record, no similarity judgement)")
    if (v.get("count") or 0) < 1: f.append("AI-0 no alternate icon variant exists (the home screen is the one surface an installed user sees daily; a single static icon forfeits the seasonal/perk re-open lever winners use)")
    if (v.get("count") or 0) >= 1 and not v.get("bundled_in_binary"): f.append("AI-1 variants are not recorded as bundled in the submitted binary (alternate icons cannot be delivered later -- an icon designed after the version ships cannot appear until the next version)")
    if (v.get("count") or 0) >= 1 and not v.get("review_approved"): f.append("AI-1 variants are not recorded as App Review approved (every alternate icon passes review with the binary; an unapproved variant switches nobody)")
    if (v.get("count") or 0) >= 1 and not v.get("similar_to_primary"): f.append("AI-2 variants are not recorded as similar to the primary icon/name (Guideline 2.3.8: alternate icons must stay recognisably the same app -- a seasonal variant users cannot find is a lost icon, not a campaign)")
    if (v.get("count") or 0) >= 1 and not v.get("four_plus_suitable"): f.append("AI-2 variants are not recorded as 4+ suitable (2.3.8 applies to alternate icons exactly as to the primary)")
    if (v.get("count") or 0) >= 1 and not v.get("rights_cleared"): f.append("AI-2 rights to every element in the variants are not recorded as cleared (2.3.9 -- the developer is responsible for rights in icons too)")
    s=d.get("switching") or {}
    if (v.get("count") or 0) >= 1 and not s.get("user_initiated_or_confirmed"): f.append("AI-3 switching is not recorded as user-initiated or system-alert confirmed (Apple prohibits changing the icon without the user's request; a silent swap reads as a different app)")
    if s.get("silent_switching"): f.append("AI-3 silent icon switching is in use (prohibited pattern: no request, no confirmation alert)")
    if (v.get("count") or 0) >= 1 and not s.get("restore_default_available"): f.append("AI-3 no restore-to-default option is recorded (Duolingo keeps 'Restore Original Icon'; a variant with no way back traps the user in a campaign)")
    se=d.get("seasonal") or {}
    if se.get("used"):
        if not se.get("calendar_recorded"): f.append("AI-4 seasonal use has no recorded calendar (windows, bundle-by version, revert date -- an unrecorded season starts after the binary that needed to carry it)")
        if not se.get("window_bounded"): f.append("AI-4 seasonal window is not bounded with start and end dates (a limited-time icon with no end is a permanent unreviewed rebrand)")
        if not se.get("bundled_before_window"): f.append("AI-4 the seasonal variant was not bundled in a version live before the window opens (the binary deadline is the real deadline; designing in-window ships after the season)")
        if not se.get("revert_automatic_or_scheduled"): f.append("AI-4 no automatic/scheduled revert to the primary at window end (a Christmas icon in January is an expired claim on the home screen)")
    p=d.get("perk") or {}
    if p.get("used"):
        if not p.get("gating_recorded"): f.append("AI-4 perk icon gating is not recorded (which plan/streak unlocks it -- Duolingo: Super / Streak Society; unrecorded gating cannot be honoured or audited)")
        if not p.get("reverts_on_expiry"): f.append("AI-4 perk icon does not revert when the subscription/streak lapses (Duolingo's returns to default on expiry; keeping the badge after lapse misstates the user's status)")
    m=d.get("measurement") or {}
    if (v.get("count") or 0) >= 1 and not m.get("opens_tracked"): f.append("AI-5 opens/re-opens are not tracked around icon changes (the winner's stated purpose is opens, not installs -- judging a home-screen lever by store installs measures the wrong surface)")
    if m.get("judged_on_installs_only"): f.append("AI-5 icon changes are judged on installs only (installed users see the icon; new users see the store page -- the two surfaces must not be conflated)")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
