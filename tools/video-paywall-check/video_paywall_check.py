#!/usr/bin/env python3
"""video-paywall-check: deterministic gate for video on a paywall.
Stdlib only, offline, free. Sources (read in full 2026-11-21):
- RevenueCat, Video Paywalls for Subscription Apps
  https://www-docs.revenuecat.com/blog/growth/video-paywalls/
  (Fitness AI: adding a video to the paywall gave roughly +80% revenue, reported
  at an App Promotion Summit -- a single-app report, not a guaranteed lift.
  Introduce video only AFTER messaging is validated and the features that drive
  payment are identified. Four legitimate goals: convey emotion / visually
  explain / prove transformation and build trust / capture attention.
  Content: keep it 15-30s, it must work without sound, captions if there is
  dialogue, strong visual hook first, the more dynamic the video the simpler
  the supporting copy. Setup: autoplay is the standard for the hero (click-to-
  play only for optional deeper content), muted by default, short heroes loop
  (a long immersive piece may instead fade to the CTA), never force a long
  watch before the paywall (the forced 30s+ pre-paywall video is called a
  major faux pas). Load: thumbnail immediately, progressive/low-res first,
  local caching, bandwidth optimisation. Returning users must not be forced
  to rewatch the same intense video (FitOn shows a simpler carousel on return).
  Testing roadmap: record the static baseline, Experiment 1 swaps only the
  hero image for a short looping video with copy unchanged, then test content,
  then placement, then setup -- in that order. One flop does not prove video
  does not work. Avoid video when the audience is low-bandwidth with no
  fallback, when the USP is speed/simplicity, or when only low-quality video
  is available -- a low-quality video does more harm than good.)
- Cal AI expectation-match spec (self, 2026-11-07): the same clip that sold the
  app on social/onboarding is reused on the paywall, so the video must show a
  real in-app experience (outside shown = inside shipped; no fabricated
  features -- the company's no-lying rule).
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

GOALS = {"emotion", "visual_explanation", "transformation_trust", "attention"}
PLACEMENTS = {"top", "background", "block", "carousel", "first_screen"}

def check(d):
    fails = []
    if not d.get("inventory_recorded"):
        fails.append("VP-0 paywall video state (present / placement / format / length) is not inventoried")
    pre = d.get("prerequisites") or {}
    if not pre.get("messaging_validated"):
        fails.append("VP-0 messaging is not validated before testing video (video amplifies a message; it does not fix one)")
    if not pre.get("payment_drivers_identified"):
        fails.append("VP-0 the features that drive payment are not identified before testing video")
    goal = d.get("goal") or {}
    if goal.get("declared") not in GOALS:
        fails.append("VP-1 no single declared goal for the video (emotion / visual_explanation / transformation_trust / attention)")
    v = d.get("video") or {}
    if not v.get("present"):
        fails.append("VP-2 no video on the paywall at all (the surface is static; Fitness AI's reported +80% came from adding one, after validation)")
    else:
        secs = v.get("seconds") or 0
        if not (1 <= secs <= 30):
            fails.append(f"VP-2 video length is {secs}s (winner form is 15-30s; over 30s is a forced watch, under 1s is not a video)")
        if not v.get("works_without_sound"):
            fails.append("VP-2 video does not work without sound (most users have sound off)")
        if v.get("dialogue_present") and not v.get("captions_if_dialogue"):
            fails.append("VP-2 dialogue video has no captions")
        if not v.get("strong_hook_first_seconds"):
            fails.append("VP-2 no strong visual hook in the first seconds")
        if not v.get("shows_real_app_experience"):
            fails.append("VP-2 video does not show the real in-app experience (outside shown must exist inside; no stock/generic substitute)")
        if v.get("fabricated_features_present"):
            fails.append("VP-2 video shows features that do not exist in the app (fabrication is prohibited)")
        if v.get("dynamic_video") and not v.get("supporting_copy_minimal"):
            fails.append("VP-2 dynamic video is paired with heavy copy (cognitive load: dynamic video wins with minimal copy)")
    pl = d.get("placement") or {}
    if pl.get("type") not in PLACEMENTS:
        fails.append("VP-3 placement is not recorded as one of top / background / block / carousel / first_screen")
    st = d.get("setup") or {}
    if st.get("forced_watch_before_access"):
        fails.append("VP-4 user is forced to watch the video before reaching the paywall/CTA (called a major faux pas in the source)")
    if v.get("present"):
        if not st.get("hero_autoplay_or_optional_click_only"):
            fails.append("VP-4 hero is neither autoplay nor a clearly optional click-to-play (testimonials/deep content only)")
        if not st.get("muted_by_default"):
            fails.append("VP-4 video is not muted by default")
        if not (st.get("loops") or st.get("fades_to_cta")):
            fails.append("VP-4 short hero neither loops nor (for a long immersive piece) fades to the CTA")
    pf = d.get("performance") or {}
    if v.get("present"):
        if not pf.get("poster_or_thumbnail_immediate"):
            fails.append("VP-5 no poster/thumbnail shown immediately while the video loads")
        if not (pf.get("optimized_or_progressive_load") or pf.get("locally_cached")):
            fails.append("VP-5 video is neither size-optimised/progressively loaded nor locally cached (load time is the known cost of video)")
        if not pf.get("static_fallback_if_load_fails"):
            fails.append("VP-5 no static fallback if the video fails to load (the paywall must never block on the video)")
    au = d.get("audience") or {}
    if au.get("low_quality_video_present"):
        fails.append("VP-6 a low-quality video is shipped (the source: low quality does more harm than good)")
    if v.get("present") and not au.get("low_bandwidth_considered"):
        fails.append("VP-6 low-bandwidth / limited-data audiences were not considered (no fallback decision recorded)")
    rt = d.get("returning") or {}
    if rt.get("returning_forced_same_intense_video"):
        fails.append("VP-7 returning users are forced to rewatch the same intense video every time (FitOn switches returners to a simpler carousel)")
    ts = d.get("testing") or {}
    if not ts.get("baseline_static_recorded"):
        fails.append("VP-8 the static-paywall baseline (conversion / trial starts) is not recorded before the video test")
    if not ts.get("first_test_single_variable"):
        fails.append("VP-8 the first video test is not single-variable (hero image -> video, copy unchanged)")
    if ts.get("test_order") != "content_placement_setup":
        fails.append("VP-8 test order is not content -> placement -> setup")
    if not ts.get("judged_on_trial_and_revenue"):
        fails.append("VP-8 video is not judged on trial starts / trial-to-paid / revenue (views and watch time are not the decision metric)")
    if ts.get("video_banned_after_one_test"):
        fails.append("VP-8 video was written off after a single failed version (one test proves that version failed, not that video fails)")
    cs = d.get("consistency") or {}
    if not cs.get("clip_consistency_recorded"):
        fails.append("VP-9 whether the paywall clip is the same clip as onboarding/social is not recorded (expectation match cannot be checked)")
    if cs.get("expectation_match_goal") and not cs.get("same_clip_as_onboarding"):
        fails.append("VP-9 goal is expectation match but the paywall clip differs from the onboarding/social clip")
    if d.get("shown_to_subscribed_users"):
        fails.append("VP-9 video paywall is shown to subscribed users (the paywall itself must never be shown to them)")
    return fails

def main():
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"{d.get('app','?')}: fails={len(fails)}")
    for x in fails:
        print(" FAIL", x)
    print("PASS" if not fails else "FAIL")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
