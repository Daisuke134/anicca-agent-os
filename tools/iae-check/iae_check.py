#!/usr/bin/env python3
"""In-App Events gate checker.
Sources (full-text read 2026-11-13):
 - Apple Developer "In-App Events" https://developer.apple.com/app-store/in-app-events/
 - Launchshots "App Store In-App Events: How Small Apps Can Use Them for Visibility"
   https://www.launchshots.com/blog/app-store-in-app-events (published 2026-11-08, full read)
 - Phiture "How to Get Your In-App Events Approved on App Store & Google Play"
   https://phiture.com/mobilegrowthstack/in-app-events-how-to-get-approved/ (full read;
   Phiture's own testing: >50% increases in impressions and first-time downloads during
   live event windows -- vendor testing, not our result)
Gates:
 IE-0 existence: at least one event recorded/planned; portfolio within limits
      (<=10 published at once, <=15 approved in App Store Connect)
 IE-1 real moment: the event is a genuine time-limited in-app activity; NOT a
      repetitive daily task/reward, NOT a price promotion without new content,
      NOT a general awareness promotion
 IE-2 metadata: name <=30 chars, short description <=50, long description <=120;
      no specific price, no unverifiable superlative, no all-caps / excessive
      punctuation, name is the actual event name (not a CTA, tagline or filler)
 IE-3 badge: one of the 7 Apple badges and it matches the actual experience
 IE-4 media: card 16:9 at >=1920x1080, details 9:16 at >=1080x1920, no text or
      logos in media, no borders/gradients added by us, card and details media
      visually related
 IE-5 deep link: universal link, lands on the event itself (not home screen),
      no URL shortener/redirect chain, new-user onboarding path returns to the
      event, pre-start landing screen exists
 IE-6 timing & readiness: duration <=31 days (and >0), promotion <=14 days
      before start, submitted >=7 days before publish date (Phiture buffer;
      ~21 days to fully use the promotion window = warning only), promoted
      content already live in the app at event start, IAP requirement declared
 IE-7 measurement: impressions, details page views, opens, downloads by event
      and notification opt-ins all tracked in App Analytics; the same format
      is repeated before it is judged (a one-off is not a verdict)
Extension added 2026-11-21 (anicca-x-search-improve-loop 12:07), sources read
in full that day:
 - AppsTemple "App Store In-App Events: 7 Types That Rank in 2026"
   https://www.appstemple.com/guides/in-app-events-aso-strategy/
   (fewer than 10% of indie apps publish on a sustained cadence; the benefit
   is cumulative and cadence-dependent -- 51% of top-charting games published
   >5 events last year, median top-200 non-game app = 2/year; editorial
   calendar: Jan fitness, May mental health, Aug back-to-school, Nov-Dec
   holidays, Sep-Oct iOS cycle; editorial-themed events submitted 3-4 weeks
   before the window; review 24-72h normal; a rejection burns 5-7 days of
   the planned window and cannot be resubmitted in the same date window;
   ASC Analytics In-App Events tab: impressions / page views / downloads,
   effective event conversion 15-25%)
 - Marteso "App Store In-App Events: An ASO Lever Most Indie Devs Never Touch"
   https://www.marteso.com/blog/app-store-in-app-events-aso-lever
   (field limits 64/30/50/120 chars; duration 15 min - 31 days; schedule at
   most 14 days ahead; regional starts within 48h; an ended event cannot be
   extended retroactively; a price drop alone is NOT eligible; Apple has NOT
   published whether event name / short description act as a search-ranking
   input -- treat an event as a free, time-boxed TEST of discovery language
   and track it, never as a guaranteed ranking lever)
 - Apple WWDC Tech Talk "Get started with in-app events" (transcript):
   metadata under App Review guidelines 2.3.13 + 2.3.8 (4+); no unverifiable
   claims, no specific prices, do not put the event type in the title or
   descriptions; events are reviewed separately from the app binary.
 IE-8 cadence & calendar (program level): a written event calendar exists;
      >=4 events per app per year (quarterly floor -- one-and-done performs
      no better than never); editorial-themed events are submitted >=3
      weeks before their editorial window; rejections are logged with the
      reason and the 5-7 day window cost.
 IE-9 keyword-as-test discipline (per event): a target keyword cluster is
      recorded, placed naturally in the event name + short description, a
      pre-event rank snapshot exists, rank is rechecked ~2 weeks into the
      window, and the event is NOT recorded as a guaranteed ranking lift
      (indexing-as-ranking-input is unpublished by Apple; vendor claims of
      ~800 indexed chars / 3-8 position lift stay labelled as claims).
"""
import json, sys

BADGES = {"Challenge", "Competition", "Live Event", "Major Update",
          "New Season", "Premiere", "Special Event"}

def check_event(e, fails, warns):
    n = e.get("name", "?")
    if not e.get("is_time_limited_real"):
        fails.append(f"IE-1 [{n}] not a genuine time-limited in-app activity")
    if e.get("is_repetitive_daily_task"):
        fails.append(f"IE-1 [{n}] repetitive daily task/reward (Apple poor candidate)")
    if e.get("is_price_promo_without_content"):
        fails.append(f"IE-1 [{n}] price promotion without new content (Apple poor candidate)")
    if e.get("is_general_awareness_only"):
        fails.append(f"IE-1 [{n}] general awareness promotion only (Apple poor candidate)")
    if int(e.get("name_chars", 999)) > 30:
        fails.append(f"IE-2 [{n}] event name {e.get('name_chars')} chars > 30")
    if int(e.get("short_desc_chars", 999)) > 50:
        fails.append(f"IE-2 [{n}] short description {e.get('short_desc_chars')} chars > 50")
    if int(e.get("long_desc_chars", 999)) > 120:
        fails.append(f"IE-2 [{n}] long description {e.get('long_desc_chars')} chars > 120")
    if e.get("has_specific_price"):
        fails.append(f"IE-2 [{n}] specific price in event text (rejection cause)")
    if e.get("has_unverifiable_claim"):
        fails.append(f"IE-2 [{n}] unverifiable superlative claim in event text")
    if e.get("has_all_caps_or_excess_punct"):
        fails.append(f"IE-2 [{n}] all caps / excessive punctuation in event text")
    if e.get("name_is_cta_or_filler"):
        fails.append(f"IE-2 [{n}] event name is a CTA/tagline/filler, not the actual event name")
    if e.get("badge") not in BADGES:
        fails.append(f"IE-3 [{n}] badge {e.get('badge')!r} is not one of Apple's 7 badges")
    if not e.get("badge_matches_content"):
        fails.append(f"IE-3 [{n}] badge does not match the actual experience (rejection cause)")
    cm = e.get("card_media", {})
    if cm.get("ratio") != "16:9" or int(cm.get("w", 0)) < 1920 or int(cm.get("h", 0)) < 1080:
        fails.append(f"IE-4 [{n}] card media must be 16:9 at >=1920x1080")
    dm = e.get("details_media", {})
    if dm.get("ratio") != "9:16" or int(dm.get("w", 0)) < 1080 or int(dm.get("h", 0)) < 1920:
        fails.append(f"IE-4 [{n}] details media must be 9:16 at >=1080x1920")
    for label, m in (("card", cm), ("details", dm)):
        if m.get("has_text_or_logo"):
            fails.append(f"IE-4 [{n}] {label} media contains text or logos (Apple crops/overlays itself)")
        if m.get("has_border_or_gradient"):
            fails.append(f"IE-4 [{n}] {label} media adds borders/gradients (Apple applies its own)")
    if not e.get("media_visually_related"):
        fails.append(f"IE-4 [{n}] card and details media are not visually related")
    dl = e.get("deep_link", {})
    if not dl.get("is_universal_link"):
        fails.append(f"IE-5 [{n}] deep link is not a universal link")
    if not dl.get("lands_on_event"):
        fails.append(f"IE-5 [{n}] deep link lands on home screen, not the event")
    if dl.get("uses_shortener_or_redirect"):
        fails.append(f"IE-5 [{n}] deep link uses a shortener/redirect (Apple warns against)")
    if not dl.get("handles_new_user_onboarding"):
        fails.append(f"IE-5 [{n}] no path back to the event after new-user onboarding")
    if not dl.get("pre_start_landing"):
        fails.append(f"IE-5 [{n}] no landing screen for the pre-start promotion period")
    dur = float(e.get("duration_days", 0))
    if dur <= 0 or dur > 31:
        fails.append(f"IE-6 [{n}] duration {dur}d outside (0, 31]")
    if float(e.get("promote_before_days", 99)) > 14:
        fails.append(f"IE-6 [{n}] promotion starts {e.get('promote_before_days')}d before start > 14d max")
    lead = int(e.get("submit_lead_days", 0))
    if lead < 7:
        fails.append(f"IE-6 [{n}] submitted only {lead}d ahead (<7d buffer for rejection/re-review)")
    elif lead < 21:
        warns.append(f"IE-6 [{n}] submitted {lead}d ahead; ~21d is needed to fully use the 14d promotion window")
    if not e.get("content_live_at_start"):
        fails.append(f"IE-6 [{n}] promoted content is not live in the app at event start")
    if e.get("requires_iap_declared") is None:
        fails.append(f"IE-6 [{n}] IAP-requirement declaration missing (must state whether participation needs a specific IAP)")

def check(d):
    fails = []; warns = []
    if not d.get("events_recorded"):
        fails.append("IE-0 no in-app event recorded/planned")
    events = d.get("events", [])
    if d.get("events_recorded") and not events:
        fails.append("IE-0 events_recorded is true but the events list is empty")
    p = d.get("portfolio", {})
    if int(p.get("published_count", 0)) > 10:
        fails.append(f"IE-0 published events {p.get('published_count')} > 10 at once")
    if int(p.get("approved_count", 0)) > 15:
        fails.append(f"IE-0 approved events {p.get('approved_count')} > 15 in App Store Connect")
    for e in events:
        check_event(e, fails, warns)
    m = d.get("measurement", {})
    for key, label in (("tracks_impressions", "event impressions"),
                       ("tracks_details_views", "event details page views"),
                       ("tracks_opens", "app opens from events"),
                       ("tracks_downloads_by_event", "downloads attributed by event"),
                       ("tracks_notification_optins", "notification opt-ins")):
        if not m.get(key):
            fails.append(f"IE-7 {label} not tracked in App Analytics")
    if not m.get("repeat_format_before_judging"):
        fails.append("IE-7 format is judged on a one-off run (repeat the same format before judging)")
    # IE-8 cadence & calendar (program level, added 2026-11-21)
    pg = d.get("program", {})
    if not pg.get("calendar_exists"):
        fails.append("IE-8 no written in-app event calendar (the discovery benefit is cadence-dependent; an unplanned surface decays to one-and-done, which performs no better than never publishing)")
    if int(pg.get("events_per_app_per_year", 0)) < 4:
        fails.append(f"IE-8 only {pg.get('events_per_app_per_year')!r} events per app per year planned (<4 quarterly floor; AppsTemple: median top-200 non-game app runs 2/year and one-and-done publishers gain nothing)")
    for e in events:
        if e.get("editorial_themed") and int(e.get("editorial_submit_lead_weeks", 0)) < 3:
            fails.append(f"IE-8 [{e.get('name', '?')}] editorial-themed event submitted {e.get('editorial_submit_lead_weeks')!r} weeks before its window (<3; editorial alignment needs a 3-4 week lead)")
    if not pg.get("rejections_logged_with_cost"):
        fails.append("IE-8 rejections are not logged with reason and window cost (a rejection burns 5-7 days and cannot be resubmitted in the same date window; an unlogged rejection repeats)")
    # IE-9 keyword-as-test discipline (per event, added 2026-11-21)
    for e in events:
        n = e.get("name", "?")
        kw = e.get("keyword_test", {})
        if not kw.get("target_cluster_recorded"):
            fails.append(f"IE-9 [{n}] no target keyword cluster recorded (the name + short description are the only card text; an event with no recorded target tests nothing)")
        if not kw.get("placed_in_name_and_short_desc"):
            fails.append(f"IE-9 [{n}] target terms are not placed naturally in the event name + short description (the two user-facing, searchable card fields)")
        if not kw.get("pre_event_rank_snapshot"):
            fails.append(f"IE-9 [{n}] no pre-event keyword rank snapshot (without a before-reading, any later movement is unattributable)")
        if not kw.get("rank_rechecked_two_weeks"):
            fails.append(f"IE-9 [{n}] keyword rank not rechecked ~2 weeks into the event window (the prescribed read point for the discovery-language test)")
        if kw.get("treated_as_guaranteed_lift"):
            fails.append(f"IE-9 [{n}] event recorded as a guaranteed ranking lift (Apple has not published that event text is a ranking input; vendor lift claims stay labelled as claims, the event stays a measured test)")
    # IE-10 purpose singularity, stagger, off-store promotion, post-event
    # retention read (extension added 2026-11-22, anicca-x-search-improve-loop
    # 03:07). Sources read in full that day:
    #  - Moburst "In-App Events: A Guide to Driving User Loyalty" (updated
    #    2026-11-16) https://www.moburst.com/blog/in-app-events-101/
    #    (stagger the calendar: one event running while the next is already
    #    visible in its promotion window; promote outside the store via
    #    email/ads/social/push; judge each event on whether lapsed users
    #    stayed AFTER the event ended, not on the spike)
    #  - LaunchShots "App Store In-App Events: The 2026 ASO Surface Indies
    #    Miss" https://launchshots.app/blog/app-store-in-app-events-aso-2026
    #    (event purpose -- attract new users vs bring back -- is the single
    #    biggest configuration decision; one event targeting both audiences
    #    dilutes performance; a low-quality event video hurts more than no
    #    video. NOTE: this source's claim that events are a proven search
    #    ranking surface with up to 8.6% conversion lift is NOT adopted --
    #    it conflicts with the settled IE-9 position that Apple has not
    #    published event text as a ranking input; the claim stays a claim.)
    # Section `purpose_program` is optional for backward compatibility:
    # absent = WARN (unknown, not a pass), present = judged as fails.
    pp = d.get("purpose_program")
    if pp is None:
        warns.append("IE-10 purpose_program section not recorded (purpose singularity / stagger / off-store promotion / post-event retention read unjudged -- unknown is not a pass)")
    else:
        if not pp.get("purpose_recorded_per_event"):
            fails.append("IE-10 event purpose is not recorded per event (purpose decides which audience sees the event; an unrecorded purpose is an unmade decision)")
        if pp.get("any_event_targets_both_audiences"):
            fails.append("IE-10 at least one event targets acquisition AND re-engagement at once (LaunchShots: pick one job per event; copy that works for one audience does not work for the other)")
        if not pp.get("stagger_overlap_planned"):
            fails.append("IE-10 calendar is not staggered (Moburst: with a 14-day promotion window, the next event should already be visible while the current one runs; gaps return the surface to zero)")
        if not pp.get("off_store_promotion_planned"):
            fails.append("IE-10 no off-store promotion planned (Moburst/Apple: link the event from email, social and push; the store card alone under-reaches the lapsed audience it exists to bring back)")
        if not pp.get("post_event_retention_read"):
            fails.append("IE-10 no post-event retention read (Moburst: judge on whether returning users stayed after the event ended; a spike that leaves is not a win)")
        if pp.get("low_quality_video_shipped"):
            fails.append("IE-10 a low-quality event video was shipped (LaunchShots: a poor video hurts more than no video; omit video below the quality bar)")
    return fails, warns

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails, warns = check(d)
    for w in warns:
        print("WARN:", w)
    for x in fails:
        print("FAIL:", x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    sys.exit(0 if not fails else 1)
