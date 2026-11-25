#!/usr/bin/env python3
"""Featuring Nomination gate checker.
Sources (full-text read 2026-11-13):
 - Apple Developer "Getting Featured on the App Store"
   https://developer.apple.com/app-store/getting-featured/
   (free, Featuring Nominations in App Store Connect, minimum 2 weeks notice,
    up to 3 months in advance recommended, 7 considerations: user experience,
    UI design, innovation, uniqueness, accessibility, localization, product page;
    promotional artwork may be requested by email to Admin/App Manager/Marketing roles)
 - Kickstart "How to get featured on the App Store: nominations, timing, and what editors want"
   https://www.kickstart.tools/blog/how-to-get-featured-on-the-app-store-nominations-timing-and-what-editors-want
   (types App Launch / App Enhancements / New Content; up to 5 supplemental URLs
    incl. TestFlight; story over feature list; nominate selectively 1-2/year;
    at least 3 weeks, 6+ weeks for seasonal moments; silence is the default)
 - AppsTemple "Get Featured on the App Store: What Apple's Editorial Team Actually Looks For (2026)"
   https://www.appstemple.com/guides/app-store-editorial-featuring-strategy/
   (published 2026-10-13; 8-12 weeks before a window, submit in October for January;
    accessibility baseline: VoiceOver core flow, Dynamic Type, tap targets >=44pt,
    contrast 4.5:1; asset pack prepared before submitting; Today story paragraph
    200-300 words. Its tens-of-thousands estimate is a vendor/guide estimate,
    not our result.)
Gates:
 F-0 existence & access: at least one nomination recorded; a holder of an
     Admin / App Manager / Marketing role can submit; selectivity kept
     (significant nominations only, ~1-2 per year; warning above 2)
 F-1 type & moment: type is one of Apple's 3 and matches the actual release;
     a named moment (seasonal / OS launch / cultural / major update) and a
     publish date or range are recorded
 F-2 lead time: >=14 days is Apple's floor (fail below), >=21 days is the
     practitioner floor (fail below 21 for a seasonal window), 8-12 weeks
     before a major window is the ideal (warning below 56 days)
 F-3 story, not a feature list: hook in the first sentence, the 3-sentence
     story present (why built / what is interesting about the team / what is
     genuinely new), pitch 200-300 words, not a feature list only
 F-4 supplemental evidence: <=5 supplemental URLs, includes a TestFlight
     build an editor can try, includes a short preview video
 F-5 seven criteria audited before submitting: UX, UI design, innovation and
     uniqueness each named with evidence; accessibility baseline passed
     (VoiceOver core flow, Dynamic Type, tap targets >=44pt, contrast >=4.5:1);
     localization covers the targeted storefronts; product page passes
     (outcome-first screenshots legible at thumbnail size, consistent frames,
     preview reflects the current major version, ratings/reviews read as
     validated -- a very thin review base is a warning, not an invented floor)
 F-6 readiness if picked: promotional asset pack prepared BEFORE submitting;
     the App Store Connect contact inbox is actually read daily (Apple may
     email Admin/App Manager/Marketing roles with a tight deadline)
 F-8..F-11 program (2026-11-22 extension, sources: ZeroRaised 2026-11-15 check
     https://zeroraised.com/blog/how-to-get-featured-on-the-app-store and
     AppRanker https://appranker.net/blog/how-to-get-featured-on-the-app-store):
     a 12-month featuring calendar per app anchored to real milestones;
     CSV imports auto-submit and cannot be saved as drafts; priority stated
     honestly and description free of superlatives / competitor names /
     download counts; build approved and live by the featuring date (review
     buffer); pitch is for featuring in general, not one slot; detection is
     via ASC Analytics "App Store browse" source, not search; featuring is a
     bonus, not the plan (launch works without it, nomination reused for a
     later window if not picked); Google Play counterpart is eligibility-
     checked first (premium growth tools thresholds / new-title 2-quarter
     window), featuring-requested promotional content >=14 days ahead,
     review up to 4 days, images contain no text. The `program` section is
     optional for backward compatibility: missing = WARN unknown, not fail.
 F-7 measurement & interpretation: baseline funnel recorded before the window
     (impressions -> product page views -> installs); silence is read as the
     default, not as a rejection; if featured, the share assets are used
     broadly and the before/after window is recorded before any lift is claimed
"""
import json, sys

TYPES = {"App Launch", "App Enhancements", "New Content"}

def check_nomination(nm, fails, warns):
    name = nm.get("name", "?")
    if nm.get("type") not in TYPES:
        fails.append(f"F-1 [{name}] type {nm.get('type')!r} is not one of Apple's 3 nomination types")
    if not nm.get("type_matches_release"):
        fails.append(f"F-1 [{name}] nomination type does not match the actual release (wrong type routes to a different team)")
    if not nm.get("moment_named"):
        fails.append(f"F-1 [{name}] no named moment (seasonal / OS launch / cultural / major update) -- a dateless 'please feature us' pitch")
    if not nm.get("publish_date_recorded"):
        fails.append(f"F-1 [{name}] no publish date or date range recorded")
    if not nm.get("is_significant"):
        fails.append(f"F-0 [{name}] not a significant launch/update/content moment (point releases dilute selectivity)")
    lead = nm.get("lead_days")
    if lead is None:
        fails.append(f"F-2 [{name}] lead time not recorded")
    else:
        if lead < 14:
            fails.append(f"F-2 [{name}] lead {lead}d < Apple's 2-week minimum")
        elif lead < 21:
            fails.append(f"F-2 [{name}] lead {lead}d < the 3-week practitioner floor")
        elif lead < 56 and nm.get("is_major_window"):
            warns.append(f"F-2 [{name}] lead {lead}d is inside the 8-12 week ideal for a major window (submit earlier next window)")
    st = nm.get("story", {})
    if not st.get("hook_first_sentence"):
        fails.append(f"F-3 [{name}] no hook in the first sentence")
    if st.get("is_feature_list_only"):
        fails.append(f"F-3 [{name}] pitch is a feature list only (editors publish stories, not feature lists)")
    if not st.get("three_sentences_present"):
        fails.append(f"F-3 [{name}] 3-sentence story missing (why built / team / what is genuinely new)")
    w = st.get("pitch_words")
    if w is None or not (200 <= int(w) <= 300):
        fails.append(f"F-3 [{name}] pitch is {w} words, outside the 200-300 word Today-card form")
    urls = nm.get("supplemental_urls_count")
    if urls is None or int(urls) > 5:
        fails.append(f"F-4 [{name}] supplemental URLs {urls} exceeds Apple's maximum of 5")
    elif int(urls) == 0:
        fails.append(f"F-4 [{name}] no supplemental URLs (editors cannot see the work for themselves)")
    if not nm.get("includes_testflight"):
        fails.append(f"F-4 [{name}] no TestFlight build among the supplemental URLs")
    if not nm.get("includes_preview_video"):
        warns.append(f"F-4 [{name}] no short preview video among the supplemental URLs")
    cr = nm.get("criteria", {})
    for key, label in (("ux", "user experience"), ("ui_design", "UI design"),
                       ("innovation", "innovation"), ("uniqueness", "uniqueness")):
        if not cr.get(key):
            fails.append(f"F-5 [{name}] Apple criterion not audited with evidence: {label}")
    acc = cr.get("accessibility", {})
    for key, label in (("voiceover_core_flow", "VoiceOver core flow"),
                       ("dynamic_type_ok", "Dynamic Type without breakage"),
                       ("tap_targets_44", "tap targets >=44pt"),
                       ("contrast_45", "contrast >=4.5:1")):
        if not acc.get(key):
            fails.append(f"F-5 [{name}] accessibility baseline missing: {label}")
    loc = cr.get("localization", {})
    if not loc.get("target_storefronts_covered"):
        fails.append(f"F-5 [{name}] localization does not cover the targeted storefronts (featuring is curated per storefront)")
    if int(loc.get("languages_count", 0)) < 2:
        warns.append(f"F-5 [{name}] only {loc.get('languages_count')} language(s) -- localization is an explicit Apple criterion")
    pp = cr.get("product_page", {})
    for key, label in (("screenshots_outcome_first", "outcome-first screenshots"),
                       ("screenshots_legible_thumbnail", "screenshots legible at thumbnail size"),
                       ("frames_consistent", "consistent screenshot frames"),
                       ("preview_current", "preview reflects the current major version")):
        if not pp.get(key):
            fails.append(f"F-5 [{name}] product page baseline missing: {label}")
    if not pp.get("review_base_meaningful"):
        warns.append(f"F-5 [{name}] review base is very thin -- Apple publishes no minimum, but editors read the page as validated or not")
    if not nm.get("asset_pack_ready_before_submit"):
        fails.append(f"F-6 [{name}] promotional asset pack not prepared before submitting (the artwork request arrives with a tight deadline)")
    m = nm.get("measurement", {})
    if not m.get("baseline_recorded"):
        fails.append(f"F-7 [{name}] no pre-window baseline funnel recorded (impressions -> page views -> installs)")
    if not m.get("silence_read_as_default"):
        fails.append(f"F-7 [{name}] silence is not recorded as the default outcome (no reply is not a rejection signal)")

def main():
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails, warns = [], []
    if not d.get("nominations_recorded"):
        fails.append("F-0 no featuring nomination recorded at all (the form is free, with no fee and no minimum download threshold)")
    noms = d.get("nominations", [])
    if d.get("nominations_recorded") and not noms:
        fails.append("F-0 nominations_recorded is true but the nominations list is empty")
    if not d.get("submitter_role_confirmed"):
        fails.append("F-0 no confirmed Admin / App Manager / Marketing role holder who can see and submit the form")
    if not d.get("contact_inbox_read_daily"):
        fails.append("F-6 App Store Connect contact inbox is not read daily (consideration emails and artwork requests go there)")
    annual = d.get("annual_nomination_count")
    if annual is not None and int(annual) > 2:
        warns.append(f"F-0 {annual} nominations this year -- the practitioner form is selective (about 1-2 significant nominations a year)")
    for nm in noms:
        check_nomination(nm, fails, warns)
    prog = d.get("program")
    if prog is None:
        warns.append("F-8 program section missing -- calendar/priority/detection/Play program unrecorded (unknown, not a pass)")
    else:
        if not prog.get("calendar_12mo_exists"):
            fails.append("F-8 no 12-month featuring calendar (nominations become afterthoughts, lead times are missed)")
        if not prog.get("milestones_recorded_per_app"):
            fails.append("F-8 real milestones are not recorded per app (every real milestone should get a nomination)")
        if prog.get("uses_csv_import") and not prog.get("csv_autosubmit_understood"):
            fails.append("F-8 CSV import used without recording that CSV nominations auto-submit and cannot be saved as drafts")
        if not prog.get("priority_stated_honestly"):
            fails.append("F-9 priority level not stated honestly in the description (Apple asks for purpose and priority; inflating a minor update burns credibility)")
        if not prog.get("description_clean"):
            fails.append("F-9 description contains superlatives, competitor names or download counts (editors want what the app does for people, not marketing copy)")
        if not prog.get("build_live_by_featuring_date"):
            fails.append("F-9 no plan for the build to be approved and live by the featuring date (count back from the featuring date, leave review buffer)")
        if not prog.get("pitch_general_not_single_slot"):
            warns.append("F-9 pitch targets one specific slot -- pitch for featuring in general; collections/lists/events are where a small app lands first")
        if not prog.get("detection_via_browse_source"):
            fails.append("F-10 featuring detection is not defined as an App Store browse-source spike in ASC Analytics (browse is separate from search; Apple does not always notify in advance)")
        if not prog.get("launch_plan_works_without_featuring"):
            fails.append("F-10 launch plan depends on being featured -- featuring is a bonus, not a plan; the launch must work without it")
        if not prog.get("reuse_if_not_featured"):
            warns.append("F-10 no reuse rule if not featured (submit for a later window instead of treating silence as the end)")
        if not prog.get("play_eligibility_checked"):
            fails.append("F-11 Google Play eligibility not checked before planning promotional content (premium growth tools are threshold-gated; new titles get a 2-quarter window)")
        elif prog.get("play_eligible"):
            lead = prog.get("play_lead_days")
            if lead is None or int(lead) < 14:
                fails.append(f"F-11 Play featuring-requested promotional content lead is {lead}d (<14d minimum)")
            if not prog.get("play_images_text_free"):
                fails.append("F-11 Play promotional images contain text/logos (Play requires text-free images)")
            if not prog.get("play_review_buffer_days") or int(prog.get("play_review_buffer_days")) < 4:
                warns.append("F-11 Play review buffer under 4 days (review can take up to 4 days)")
    for w in warns:
        print(f"WARN {w}")
    for f_ in fails:
        print(f"FAIL {f_}")
    if fails:
        print(f"RESULT FAIL {len(fails)} fail(s), {len(warns)} warning(s)")
        return 1
    print(f"RESULT PASS 0 fail(s), {len(warns)} warning(s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
