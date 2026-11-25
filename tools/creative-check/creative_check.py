#!/usr/bin/env python3
"""creative-check: deterministic gate for App Store Creative Assets
(product page header + search results asset), live since 2026-10-05.
Stdlib only, no API, no cost.
Sources (read in full 2026-11-13):
- AppScreens, "Apple Creative Assets: Product Page Header Guide"
  (updated 2026-11-12, synthesising Apple specs / best practices /
  WWDC26) https://appscreens.com/blog/apple-creative-assets-app-store
- Adapty, "App Store Asset Library is live: headers, search, PPO, Duo"
  (2026-10-06) https://adapty.io/blog/app-store-asset-library/
- Mac Observer, "App Store product page headers now take images and
  videos up to 30 seconds" (2026-10-17, Guideline 2.3.14)
  https://www.macobserver.com/news/app-store-creative-assets-header-video-asset-library/
Key facts encoded:
- Two placements with different jobs: search is seen BEFORE the tap
  (brief it first), header is the first visual AFTER the tap.
- Header image: 3840x1646 (21:9, JPEG/PNG) or 5244x2950 (16:9, PNG only).
  Search image: 3:2 from 1920x1280 to 3840x2560, or 5244x2950 PNG.
  Universal = 5244x2950 PNG only. No alpha / transparency.
  Video: 5-30s, 30/60fps, placement ratio; search video cannot be
  unmuted, so it must work silent. Safe areas: header 1646x661,
  search 2168x1030, universal 1402x962.
- Guideline 2.3.14 + best practices: no specific/discounted pricing,
  no URLs, no copyright symbols, no unverifiable claims or awards,
  no Apple recognitions, no other-platform logos, 4+ for every asset,
  must pertain to the app's content/functionality or brand.
  Header = single clear idea; search = purpose obvious at a glance.
- Workflow: standalone Asset Library review (no new version needed to
  swap approved assets on a live version); preview across devices /
  orientations / Dark Mode / languages; poster frame cannot be edited
  after approval; role must be Account Holder/Admin/App Manager/
  Marketing.
- Assets are per-localization; an English header in a non-English
  storefront is the same mistake as an English screenshot set.
- PPO: change ONE placement per treatment (search first); assets show
  only on iOS/iPadOS 27+, so results describe that slice only; no
  performance benchmark exists yet and assets do not change keyword
  rankings -- never claim a ranking effect.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def img_ok_header(a):
    w, h, fmt = a.get("width"), a.get("height"), (a.get("format") or "").lower()
    if (w, h) == (3840, 1646) and fmt in ("jpeg", "jpg", "png"):
        return True
    if (w, h) == (5244, 2950) and fmt == "png":
        return True
    return False

def img_ok_search(a):
    w, h, fmt = a.get("width"), a.get("height"), (a.get("format") or "").lower()
    if (w, h) == (5244, 2950) and fmt == "png":
        return True
    if w and h and abs(w / h - 1.5) < 0.01 and 1920 <= w <= 3840 and 1280 <= h <= 2560 and fmt in ("jpeg", "jpg", "png"):
        return True
    return False

def check_asset(a, kind, fails, warns):
    label = "header" if kind == "header" else "search results"
    if not a:
        fails.append(f"CA-0 no {label} asset is recorded -- since 2026-10-05 both placements exist in App Store Connect (Header and Search Results tab / Asset Library); an unrecorded placement is not 'later', it is an empty first impression on iOS 27+")
        return
    if a.get("kind") == "screenshot_reuse":
        fails.append(f"CA-2 the {label} asset is a reused/upscaled screenshot -- creative assets are a separate upload type with landscape canvases; a portrait screenshot scaled up matches no accepted size and keeps the 'show UI' job in a slot whose job is brand/value (screenshots keep their own slot)")
    if a.get("kind") == "video":
        dur, fps = a.get("duration_s"), a.get("fps")
        if dur is None or not (5 <= dur <= 30):
            fails.append(f"CA-2 {label} video length is outside 5-30 seconds (recorded: {dur})")
        if fps not in (30, 60):
            fails.append(f"CA-2 {label} video frame rate is not 30 or 60 fps (recorded: {fps})")
        if kind == "search" and not a.get("works_muted"):
            fails.append("CA-2 search results video is not designed to work muted -- search videos are muted and cannot currently be unmuted; a message that needs sound is absent in search")
        if not a.get("poster_frame_final_before_approval"):
            fails.append(f"CA-4 {label} video poster frame is not final before approval -- poster frames cannot be edited after approval, and videos autoplay/loop, so the poster IS the still asset most viewers judge")
    else:
        ok = img_ok_header(a) if kind == "header" else img_ok_search(a)
        if not ok:
            fails.append(f"CA-2 {label} image size/format is not an accepted creative-asset canvas (header: 3840x1646 JPEG/PNG or 5244x2950 PNG; search: 3:2 1920x1280-3840x2560 or 5244x2950 PNG; recorded: {a.get('width')}x{a.get('height')} {a.get('format')})")
        if a.get("has_alpha"):
            fails.append(f"CA-2 {label} image carries an alpha channel / transparency -- creative asset images cannot include alpha channels or transparencies")
    c = a.get("content") or {}
    bans = [
        ("contains_pricing_or_discount", "specific or discounted pricing (banned by Guideline 2.3.14 and best practices)"),
        ("contains_url", "a website URL (banned)"),
        ("contains_copyright_symbol", "a copyright symbol (banned)"),
        ("contains_unverifiable_claim", "an unverifiable product claim or award (banned by 2.3.14)"),
        ("contains_apple_recognition", "an Apple recognition such as Editor's Choice / App of the Day (banned)"),
        ("contains_other_platform_logo", "a logo or reference to another platform or marketplace (banned)"),
        ("not_pertinent_to_app", "content that does not pertain to the app's content, functionality or overarching brand (2.3.14)"),
    ]
    for key, desc in bans:
        if c.get(key):
            fails.append(f"CA-3 {label} asset contains {desc}")
    if not c.get("meets_4plus"):
        fails.append(f"CA-3 {label} asset is not confirmed 4+ appropriate -- every asset shown on the App Store must meet a 4+ age rating even if the app's own rating is higher")
    if not c.get("focal_in_safe_area"):
        fails.append(f"CA-3 {label} asset does not keep its focal artwork inside the official safe area (header 1646x661, search 2168x1030, universal 1402x962) -- outside the safe area, key art is clipped across devices and orientations")
    if kind == "header" and not c.get("single_clear_idea"):
        fails.append("CA-3 header does not focus on a single, clear idea -- Apple's header guidance is one idea per header; a header that lists features is a screenshot gallery moved to the top of the page")
    if kind == "search" and not c.get("purpose_obvious_at_glance"):
        fails.append("CA-3 search asset does not make the app's purpose obvious at a glance -- that is the stated job of the search placement, which is read before any tap, at small size, next to competitors")

def check(d):
    fails, warns = [], []
    if not d.get("winner_usage_measured"):
        fails.append("CA-0 the fixed winner's use of creative assets (I am: header / search asset present or absent, and its form) has not been measured -- shipping our own first, unmeasured, repeats the 'build before looking' error; the winner check is a store-page read, not a project")
    strat = d.get("strategy") or {}
    if not strat.get("search_briefed_first"):
        fails.append("CA-1 the search results asset was not briefed first -- search is what a searcher meets before any tap and Adapty's rule is explicit: brief search first, header second; header-first spends the design budget on the placement fewer people reach")
    if not strat.get("placements_have_distinct_jobs"):
        fails.append("CA-1 the two placements are not recorded with distinct jobs (search = relevance/purpose before the tap; header = brand/first impression after the tap) -- one undifferentiated 'store artwork' task produces one image stretched across two different decisions")
    if strat.get("counts_screenshots_as_creative"):
        fails.append("CA-1 screenshots are being counted as creative assets -- they are separate asset types with separate jobs (screenshots show the real UI; creative assets market brand/value/offer/content) and creative assets do not replace screenshot requirements")
    check_asset(d.get("header_asset"), "header", fails, warns)
    check_asset(d.get("search_asset"), "search", fails, warns)
    if d.get("uses_universal") and d.get("header_asset") and d.get("search_asset"):
        h, s = d["header_asset"], d["search_asset"]
        if (h.get("width"), h.get("height")) != (5244, 2950) or (s.get("width"), s.get("height")) != (5244, 2950):
            fails.append("CA-2 the plan claims one universal asset for both placements but the recorded sizes are not both 5244x2950 -- 16:9 at exactly 5244x2950 PNG is the ONLY size both placements accept; a generic 16:9 canvas is not a universal asset")
    wf = d.get("workflow") or {}
    if not wf.get("review_path_recorded"):
        fails.append("CA-4 no review path is recorded (with-version vs standalone Asset Library submission) -- standalone submission exists precisely so creative does not wait for a release; an unrecorded path defaults to waiting for the next version")
    if not wf.get("preview_checked"):
        fails.append("CA-4 the App Store Connect preview tool check is not recorded (devices, orientations, Dark Mode, languages) -- crop, contrast and localization failures are exactly what the preview exists to catch before review")
    if not wf.get("role_confirmed"):
        warns.append("CA-4 the managing role (Account Holder / Admin / App Manager / Marketing) is not confirmed recorded -- asset management is role-gated; discovering that at upload time turns a ready asset into a blocked one")
    loc = d.get("localization") or {}
    main_markets = loc.get("main_markets") or []
    done = set(loc.get("localized_markets") or [])
    if main_markets and not set(main_markets).issubset(done):
        missing = sorted(set(main_markets) - done)
        fails.append(f"CA-5 creative assets are not localized for all main markets -- missing: {', '.join(missing)} (assets are set per localization; an English header in a non-English storefront is the same mistake as an English screenshot set)")
    if loc.get("english_only_in_nonenglish_storefront"):
        fails.append("CA-5 an English-only asset is planned for a non-English storefront -- localization of creative is not optional polish; the asset is the first text a searcher in that market reads")
    ms = d.get("measurement") or {}
    if ms.get("ppo_changes_both_placements"):
        fails.append("CA-6 the planned PPO test changes header and search assets in the same treatment -- change only the search results asset first, header on its own next; changing both makes the result unattributable")
    if not ms.get("ios27_slice_acknowledged"):
        fails.append("CA-6 the measurement plan does not record that creative assets show only on iOS/iPadOS 27+ -- any read mixes 'asset effect' with 'OS-slice composition' unless the slice is the stated denominator")
    if ms.get("claims_ranking_effect"):
        fails.append("CA-6 a keyword-ranking effect is claimed for creative assets -- the sources are explicit that new assets do not change keyword rankings; the lever is conversion of existing demand, and claiming ranking invents a second effect that will be 'measured' forever")
    if ms.get("treats_early_numbers_as_benchmark"):
        warns.append("CA-6 early placement numbers are being treated as a benchmark -- no performance data on these placements exists yet in the sources; early numbers are a hypothesis, not a target")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app','?')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
