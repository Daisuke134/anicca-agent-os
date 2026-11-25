#!/usr/bin/env python3
"""widget-check: judge a home/lock-screen widget state vs the winner form.
Stdlib only, offline, free.
Sources read in full 2026-11-14:
 - I am (winner) widget guide, blog.theiam.app (2026-11-05): sizes small/
   medium/large; fresh affirmation on unlock; per-widget name/category/
   theme/text size/refresh frequency/border in Profile > Widget settings;
   like+share buttons on medium/large only; multiple widgets allowed;
   basic free, advanced per-widget theme/refresh is Premium.
   https://blog.theiam.app/blogs/how-to-add-an-affirmation-widget-to-your-home-screen-iphone-android
 - ASOWin widgets/Live Activities playbook (full read): build around the
   single glanceable core value; design per surface; teach users to add
   the widget at a relevant moment; show widgets in store screenshots;
   measure adoption, taps, retention widget-vs-non with a control
   (correlation is not causation); no sensitive data on lock screen.
   https://www.asowin.com/blog/ios-widgets-live-activities-engagement/
 - Anicca source read 2026-11-14 (canonical checkout apps/mobile/anicca-ios/
   AniccaWidget): families [.systemSmall,.systemMedium,.accessoryRectangular],
   StaticConfiguration, 7 daily entries .atEnd, selection = dayOfYear % count
   over the user's struggles texts, reloadAllTimelines on sync.
Extension W-8..W-13 added 2026-11-21 (anicca-x-search-improve-loop 19:07),
sources read in full 2026-11-21:
 - AppsTemple, iOS Widgets Boost Day-30 Retention: 7 Design Rules (2026)
   https://www.appstemple.com/guides/ios-widget-home-screen-retention/
   (D30 ~7% average, 15%+ surfaces share persistent home-screen presence;
   widget is a retention loop not a feature; interactive vs informational
   decided BEFORE code by whether in-widget completion IS the retention
   behaviour; own-data widgets stay, app-content/promo widgets get deleted;
   first-week deletion = stale data + bad empty state + no small size;
   freshness: reload policy must match when data changes and
   reloadAllTimelines() on underlying change fires outside the background
   budget (~40-70/day); empty state must be instructive / first-action /
   motivating default, never a blank placeholder; small 2x2 first (one
   number, one label, one tap), medium/large extend the same core;
   interactive intents run in the extension, local read/write only, no
   reliable network; measurement: instrument the widget tap with a custom
   event, cohort = adopted (tapped >=1 in first 7 days) vs non, 2-4x gap
   is symptom-vs-driver evidence with self-selection caveat; gallery
   preview of a not-yet-installed app must look populated, not empty.)
 - gr0w, How do apps keep users coming back? (185 founder interviews,
   updated 2026-11-08) https://gr0w.app/learn/increase-app-retention
   (Flame founder: widgets discovered too late -- a home-screen widget
   calls the user back on every unlock and stands out because almost
   every app now only sends notifications; Couplejoy built its social
   strategy around a lock-screen widget and Flame copied it; no separate
   before/after number for widgets alone is given, so none is claimed.)
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
fails=[]; warns=[]
def fail(g,m): fails.append(f"[{g}] {m}")
def warn(g,m): warns.append(f"[{g}] {m}")
def main(path):
    s=json.load(open(path))
    if not s.get("recorded"): fail("W-0","widget state not recorded (unmeasured)")
    inv=s.get("inventory") or {}
    for k in ("families","configuration_type","teach_prompt","measurement"):
        if inv.get(k) is None: fail("W-0",f"inventory.{k} unrecorded (unmeasured)")
    fams=set(inv.get("families") or [])
    for req in ("systemSmall","systemMedium","systemLarge","accessoryRectangular"):
        if req not in fams: fail("W-1",f"family {req} missing (winner I am ships small/medium/large + lock screen)")
    cfg=s.get("configuration") or {}
    if cfg.get("type")!="app_intent": fail("W-2","configuration is not per-widget (AppIntent): winner lets each widget carry its own category/theme/name")
    for k in ("per_widget_category","per_widget_theme","refresh_frequency_selectable"):
        if cfg.get(k) is not True: fail("W-2",f"configuration.{k} is not true (winner Widget settings expose it; advanced is Premium)")
    act=s.get("actions") or {}
    if act.get("like_from_widget") is not True or act.get("share_from_widget") is not True:
        fail("W-3","like/share from the widget (medium/large) missing: winner completes the value action without opening the app")
    c=s.get("content") or {}
    if c.get("uses_user_context") is not True: fail("W-4","widget content does not use the user's own context (struggles/onboarding answers)")
    if c.get("selection")=="day_of_year_rotation": fail("W-4","content selection is a calendar rotation (dayOfYear % count), not the person's state/reaction history")
    if c.get("fallback_when_no_data") is not True: warn("W-4","no recorded fallback when the app was never opened / no data synced (winner: open once, else placeholder guidance)")
    t=s.get("teach") or {}
    if t.get("guide_shown") is not True: fail("W-5","no in-app guide/prompt teaching the user to add the widget (ASOWin: teach at a relevant moment)")
    if t.get("timing")=="first_launch": fail("W-5","widget prompt at first launch: teach after a value moment, not in onboarding")
    st=s.get("store") or {}
    if st.get("widget_shown_in_screenshots") is not True: fail("W-6","widget not shown in store screenshots (users choose apps for their widgets)")
    if st.get("widget_claim_matches_shipped") is not True: warn("W-6","store widget claim not verified against the shipped families")
    m=s.get("measurement") or {}
    for k in ("adoption_rate","taps_into_app","retention_widget_vs_non"):
        if m.get(k) is not True: fail("W-7",f"measurement.{k} not tracked")
    if m.get("retention_read_with_control") is not True: fail("W-7","retention read without a prompt control group: widget users self-select, correlation is not causation")
    if s.get("lock_screen_sensitive_by_default") is True: fail("W-7","sensitive content shown on lock screen by default")
    # --- W-8..W-13 (2026-11-21 extension, AppsTemple + gr0w) ---
    fr=s.get("freshness") or {}
    if fr.get("reload_policy_matches_data_cadence") is not True: fail("W-8","freshness: TimelineReloadPolicy does not match when the underlying data actually changes (stale data is deletion failure #1, most removals happen in week 1)")
    if fr.get("reload_on_underlying_change") is not True: fail("W-8","freshness: reloadAllTimelines() is not called when underlying data changes (that call fires immediately, outside the background-refresh budget)")
    if fr.get("stale_guard_recorded") is not True: fail("W-8","freshness: no recorded guard against showing the same content as yesterday (a widget identical to yesterday is read as useless within a week)")
    es=s.get("empty_state") or {}
    if es.get("designed") is not True: fail("W-9","empty state: not designed (bad empty state is deletion failure #2; the first view after adding the widget decides survival)")
    if es.get("kind") not in ("instructive","first_action_prompt","motivating_default"): fail("W-9","empty state: kind is not instructive / first_action_prompt / motivating_default (a blank 'nothing yet' placeholder signals the widget has nothing to offer)")
    if es.get("gallery_preview_populated") is not True: fail("W-9","empty state: widget-gallery / preview view is not populated and useful (the gallery preview is a discovery surface for not-yet-installed users; an empty preview loses both installs and adoption)")
    ow=s.get("ownership") or {}
    if ow.get("shows_user_own_data") is not True: fail("W-10","ownership: widget does not show the user's own data (own-data widgets stay; app-content widgets get deleted)")
    if ow.get("shows_app_promo_or_editorial") is True: fail("W-10","ownership: widget shows the app's content (promotions / editorial picks / sale items) -- that form reads as an ad and is removed")
    if ow.get("single_retention_behavior_focus") is not True: fail("W-10","ownership: widget is not focused on the single daily-glance retention behaviour (a showcase of everything the app does is a cluttered widget nobody keeps)")
    if ow.get("larger_sizes_extend_same_core") is not True: fail("W-10","ownership: medium/large do not extend the same core concept (larger sizes add context to the same core, not different functionality)")
    ia=s.get("interaction") or {}
    if ia.get("decision_recorded_before_build") is not True: fail("W-11","interaction: the interactive-vs-informational decision is not recorded before building (AppsTemple: this decision changes which entry points you build, so it comes before WidgetKit code)")
    if ia.get("mode") not in ("interactive","informational"): fail("W-11","interaction: mode is not recorded as interactive or informational")
    if ia.get("mode")=="interactive" and ia.get("completion_is_retention_behavior") is not True: fail("W-11","interaction: widget is interactive but in-widget completion is not itself the retention behaviour (if value requires entering the app, the widget must be informational and prompt a tap-through, not resolve the session inside itself)")
    if ia.get("mode")=="informational" and ia.get("prompts_tap_through") is not True: fail("W-11","interaction: informational widget does not surface just enough to prompt a tap-through")
    if ia.get("mode")=="interactive" and ia.get("intents_local_only") is not True: fail("W-11","interaction: interactive intents are not narrowly scoped to local read/write (perform() runs in the extension; network calls there are unreliable -- server round-trips belong in the app)")
    sf=s.get("small_first") or {}
    if sf.get("small_built_first") is not True: fail("W-12","small-first: the small 2x2 was not built first (it is by far the most commonly placed size; shipping only medium/large misses the majority of placements -- deletion failure #3)")
    if sf.get("small_is_one_value") is not True: fail("W-12","small-first: small widget is not reduced to one number / one label / one tap target")
    mm=s.get("measurement_ext") or {}
    if mm.get("widget_tap_event_instrumented") is not True: fail("W-13","measurement: widget taps are not instrumented with a custom event on app entry (ASC does not attribute sessions to widget taps by default; without the event there is no visibility into sessions the widget generates)")
    if mm.get("install_to_adoption_as_first_session_metric") is not True: fail("W-13","measurement: install-to-widget-adoption is not treated as a first-session conversion metric (users who saw the widget in the listing adopt at a higher rate after session one)")
    if mm.get("cohort_definition_first7_tapped") is not True: fail("W-13","measurement: retention cohort is not defined as tapped >=1 in the first 7 days vs non-adopters (the source's cohort definition)")
    if mm.get("gap_read_with_self_selection_caveat") is not True: fail("W-13","measurement: the widget-vs-non retention gap is not read with the self-selection caveat (adopters are already more engaged; a 2-4x gap is symptom-vs-driver evidence, not proof of causation)")
    for w_ in warns: print("WARN",w_)
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1
if __name__=="__main__": sys.exit(main(sys.argv[1]))
