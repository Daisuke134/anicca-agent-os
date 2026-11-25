#!/usr/bin/env python3
"""preview-check: deterministic gate checker for App Store App Preview videos.
Stdlib only, offline. Exit 0=PASS, 1=FAIL.
Consolidates: hidden_files/app-preview-video-gate-spec-2026-11-10.md (Gate V-0,
Rules V-1..V-3) + AppFollow ASO Video Strategies 2026 playbook (read in full
2026-11-14: specs 15-30s / max 30fps / 500MB / up to 3 per locale; poster frame
is critical on iOS; first 3s carry disproportionate weight; muted autoplay;
match keyword promise to creative promise; localize beyond translation;
measure CVR/TTR before rebuilding) + AppScreenshotStudio 2026 guide and
Launchshots 2026 (poster defaults to ~5s mark if not chosen; beats 2-4s,
under 1s per shot reads as a flashy ad; in-app footage only, no hands).
Vendor lift claims (20-40% etc.) are NOT encoded as expectations.
"""
import json, sys

def main():
    if len(sys.argv) < 2:
        print("usage: preview_check.py <state.json>"); return 2
    s = json.load(open(sys.argv[1]))
    fails, warns = [], []
    def req(c,g,m):
        if not c: fails.append(f"{g}: {m}")
    def warn(c,g,m):
        if not c: warns.append(f"{g}: {m}")
    # PV-0 inventory
    req(s.get("inventory_recorded") is True, "PV-0", "preview inventory not recorded (existence must be read per device/locale, not left unmeasured)")
    exists = s.get("preview_exists")
    req(exists is not None, "PV-0", "preview existence not stated (null = unmeasured; record true/false per surface)")
    req("iphone" in (s.get("devices_checked") or []), "PV-0", "iPhone surface not checked in inventory")
    req(len(s.get("locales_checked") or []) >= 1, "PV-0", "no locale checked in inventory")
    if exists is True:
        # PV-1 technical
        d = s.get("duration_s") or 0
        req(15 <= d <= 30, "PV-1", f"duration {d}s outside 15-30s")
        req((s.get("fps") or 99) <= 30, "PV-1", f"fps {s.get('fps')} > 30")
        req((s.get("size_mb") or 9999) <= 500, "PV-1", f"size {s.get('size_mb')}MB > 500MB")
        req((s.get("format") or "").lower() in ("mp4","mov","m4v"), "PV-1", f"format {s.get('format')} not in mp4/mov/m4v")
        req(1 <= (s.get("videos_per_locale") or 0) <= 3, "PV-1", "videos per locale must be 1-3")
        req(s.get("orientation") == s.get("screenshots_orientation"), "PV-1", "preview orientation differs from screenshots (landscape video + portrait screenshots is demoted to Closer Look)")
        # PV-2 first 3 seconds
        f3 = s.get("first3s") or {}
        req(f3.get("opens_with") == "value_moment", "PV-2", f"opens with {f3.get('opens_with')} (logo/splash openings waste the only guaranteed seconds)")
        req(1 <= (f3.get("opening_caption_words") or 0) <= 7, "PV-2", f"opening caption {f3.get('opening_caption_words')} words (one caption, under 7 words, outcome-focused)")
        req(f3.get("opening_caption_outcome_focused") is True, "PV-2", "opening caption is not outcome-focused")
        req(f3.get("keyword_promise_matches_first_frame") is True, "PV-2", "first frame does not show the keyword/search promise immediately")
        # PV-3 muted-first pacing
        mu = s.get("muted") or {}
        req(mu.get("works_muted") is True, "PV-3", "does not communicate with sound off (autoplay is muted)")
        req(mu.get("captions_large") is True, "PV-3", "captions not large/high-contrast enough for muted reading")
        req((mu.get("max_beat_s") or 99) <= 4, "PV-3", f"longest beat {mu.get('max_beat_s')}s > 4s (static scenes stall the preview)")
        req((mu.get("min_beat_s") or 0) >= 1, "PV-3", f"shortest beat {mu.get('min_beat_s')}s < 1s (sub-second cuts read as a flashy ad, not a demo)")
        # PV-4 poster frame
        po = s.get("poster") or {}
        req(po.get("poster_selected") is True, "PV-4", "poster frame not explicitly selected (Apple defaults to an arbitrary/~5s frame, often black or blurred)")
        req(po.get("poster_matches_screenshot1_story") is True, "PV-4", "poster frame does not continue the first screenshot's story")
        req(po.get("poster_readable_static") is True, "PV-4", "poster frame does not read as a compelling static image (on cellular it IS the asset)")
        # PV-5 content rules
        co = s.get("content") or {}
        req(co.get("in_app_footage_only") is True, "PV-5", "footage is not in-app only (Apple requires app screen capture; no live-action wrappers)")
        req(co.get("hands_or_live_action") is not True, "PV-5", "hands / live-action present (prohibited in App Preview)")
        req(co.get("price_or_discount_shown") is not True, "PV-5", "price or discount shown in preview (prohibited)")
        req(co.get("external_cta_shown") is not True, "PV-5", "external CTA shown in preview (prohibited; end on an in-app destination screen)")
        req(co.get("unshipped_features_shown") is not True, "PV-5", "features shown that are not shipped/reachable (expectation mismatch drives bad reviews and refunds)")
        req(co.get("paywall_consistent") is True, "PV-5", "value shown in preview is inconsistent with what is reachable around the paywall")
        # PV-6 localization
        lo = s.get("localization") or {}
        req(len(lo.get("preview_locales") or []) >= 1, "PV-6", "no preview locale recorded")
        req(lo.get("top_locale_covered") is True, "PV-6", "top storefront locale falls back to a foreign-language preview silently")
        warn(lo.get("opening_caption_localized") is True, "PV-6", "opening caption not localized (if nothing else is localized, the first caption must land in the viewer's language)")
    elif exists is False:
        fails.append("PV-1: no App Preview on the product page (the first gallery slot is static while the category winner surface is motion-first in search)")
    # PV-7 sequencing + measurement (applies regardless of existence)
    sq = s.get("sequencing") or {}
    req(sq.get("screenshots_before_after_done") is True, "PV-7", "screenshots 1-3 before/after comparison not completed before preview production (2026-11-10 spec Gate V-0-3: preview is the next variable, not a simultaneous one)")
    req(sq.get("single_variable") is True, "PV-7", "preview change is not isolated as a single variable")
    me = s.get("measurement") or {}
    req(me.get("reads_cvr") is True, "PV-7", "measurement does not read product-page CVR")
    req(me.get("reads_download_to_paid") is True, "PV-7", "measurement does not read Download-to-Paid conversion (WWDC25 App Analytics)")
    req(me.get("reads_proceeds_per_download") is True, "PV-7", "measurement does not read proceeds per download")
    req(me.get("install_rate_only") is not True, "PV-7", "measurement reads install rate only (install-only wins are not wins)")
    req((me.get("window_days") or 0) >= 30, "PV-7", f"measurement window {me.get('window_days')}d < 30d")
    print(f"exists={exists} devices={s.get('devices_checked')} locales={s.get('locales_checked')}")
    for f in fails: print(" FAIL", f)
    for w in warns: print(" WARN", w)
    print("RESULT", "FAIL" if fails else "PASS", f"({len(fails)} fails, {len(warns)} warns)")
    return 1 if fails else 0
if __name__ == "__main__":
    sys.exit(main())
