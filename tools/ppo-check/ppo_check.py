#!/usr/bin/env python3
"""ppo-check: deterministic gate checker for App Store Product Page Optimization (PPO).
Stdlib only, offline, free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-14):
- Stora, "How to A/B test App Store screenshots in 2026: a complete Product Page
  Optimization guide" https://stora.sh/blog/2026-04-29-app-store-screenshot-ab-testing-product-page-optimization-guide
  (1 test at a time; up to 3 treatments + original; up to 90 days, no pause/resume;
  icon must be an alternate icon already in the shipped binary; ~100,000 impressions
  across the test period rule of thumb or fewer treatments / bigger differences /
  skip and ship directly; priority: first screenshot > full set as story > preview >
  icon; triangulate with 3 treatments = image-only / copy-only / combined; define
  minimum detectable effect before starting; read confidence interval, per-storefront
  breakdown, and downstream day-1 retention / IAP rate / crash-free, not headline lift)
- 3Nsofts, "Product Page Optimization vs Custom Product Pages: An App Store
  Conversion Testing Playbook"
  https://www.3nsofts.com/insights/app-store-product-page-optimization-vs-custom-product-pages
  (PPO = randomized choice on the default page; CPP = persistent audience page, NOT a
  test; strong brief = audience + confusion + change + baseline + primary outcome
  (first-time download conversion) + locale + decision for win/lose/inconclusive;
  change one coherent variable; truth / continuity / legibility checks; fewer
  treatments when traffic is limited; do not copy a universal sample-size number;
  do not stop as soon as a preferred treatment looks ahead; full experiment record
  with the exact asset files saved)
Apple mechanics corroborated via search results (Airbridge / Playio summaries of
Apple documentation): Ready for Distribution required; PPO not available for CPPs;
traffic proportion split evenly across treatments; wait for >=90% confidence before
applying or stopping; applying mid-test ends the test; a new version changing the
assets under test can affect results; winning icon still needs a future binary.
Vendor lift claims (1.5-2x, +5-15% etc.) are NOT encoded as expectations.
"""
import json, sys

def main():
    if len(sys.argv) < 2:
        print("usage: ppo_check.py <state.json>"); return 2
    s = json.load(open(sys.argv[1]))
    fails, warns = [], []
    def req(c, g, m):
        if not c: fails.append(f"{g}: {m}")
    def warn(c, g, m):
        if not c: warns.append(f"{g}: {m}")

    decision = s.get("decision")  # start_now | defer_direct_ship | running | completed | None
    # PPO-0 record & eligibility
    req(s.get("record_exists") is True, "PPO-0", "no PPO experiment record exists (unrecorded page changes are unmeasured, not experiments)")
    req(s.get("app_ready_for_distribution") is True, "PPO-0", "app is not recorded as Ready for Distribution (PPO eligibility)")
    req(s.get("target_is_default_page") is True, "PPO-0", "target is not the default product page (PPO is unavailable for Custom Product Pages; a CPP is a persistent audience page, not a test treatment)")
    req(s.get("purpose_is_randomized_choice") is True, "PPO-0", "purpose is not a randomized choice between creative alternatives on the default page (segmented stories belong to CPPs)")
    req(s.get("no_other_ppo_running") is True, "PPO-0", "another PPO test is running or not recorded as absent (one test at a time)")
    req(s.get("direct_changes_without_record") is not True, "PPO-0", "default-page assets were changed directly with no hypothesis / traffic assessment / record (those changes taught nothing and cannot be attributed)")

    # PPO-1 decision question / strong brief
    h = s.get("hypothesis") or {}
    for k, label in [("audience","audience"),("confusion","confusion / problem"),("change","change"),("baseline","baseline page"),("primary_outcome","primary outcome"),("locale","locale")]:
        req(bool(h.get(k)), "PPO-1", f"hypothesis brief missing {label}")
    req(h.get("primary_outcome") == "first_time_download_conversion", "PPO-1", f"primary outcome is {h.get('primary_outcome')} (PPO measures first-time download conversion; downstream is a guardrail, not the primary)")
    d = s.get("decisions_precommitted") or {}
    req(d.get("if_win") and d.get("if_lose") and d.get("if_inconclusive"), "PPO-1", "win / lose / inconclusive decisions are not all pre-committed before the test starts (a test whose outcomes change nothing is decorative)")

    # PPO-2 traffic floor & MDE
    t = s.get("traffic") or {}
    req(t.get("impressions_last7d") is not None, "PPO-2", "last-7d impressions not recorded (traffic floor cannot be assessed)")
    req(t.get("page_views_last7d") is not None, "PPO-2", "last-7d product page views not recorded")
    proj = t.get("projected_90d_impressions")
    req(proj is not None, "PPO-2", "projected 90-day impressions not computed from measured traffic")
    req(t.get("mde_percent") is not None, "PPO-2", "minimum detectable effect not defined before starting (a test that cannot detect its expected effect inconclusives-out and burns the 90-day slot)")
    treatments = s.get("treatments_planned") or 0
    req(1 <= treatments <= 3, "PPO-2", f"treatments planned = {treatments} (must be 1-3 plus the original)")
    if decision == "start_now":
        req((proj or 0) >= 100000, "PPO-2", f"starting now with projected 90d impressions {proj} (< ~100,000 rule of thumb): the test will likely end inconclusive; use fewer treatments / a bigger difference, or defer and ship the winner-copy change directly")
        if (proj or 0) < 100000:
            pass
        per = (proj or 0) / max(treatments, 1)
        req(per >= 25000 or (proj or 0) >= 100000, "PPO-2", f"projected impressions per treatment {per:.0f} (< ~25,000 practitioner floor) with {treatments} treatments")
    if decision == "defer_direct_ship":
        req(t.get("defer_reason_recorded") is True, "PPO-2", "deferred, but the traffic-floor reason is not recorded (deferral without a recorded floor check becomes silent abandonment)")
        req(s.get("direct_ship_uses_winner_copy") is True, "PPO-2", "deferred PPO, but the direct change is not the fixed winner's copy (deferring the test is not a licence for original creative)")
        req(t.get("floor_recheck_cadence_days") is not None and (t.get("floor_recheck_cadence_days") or 999) <= 31, "PPO-2", "no monthly (<=31d) traffic-floor recheck recorded for the deferred test")
    warn((t.get("floor_recheck_cadence_days") or 999) <= 31, "PPO-2", "traffic floor is not rechecked at least monthly")

    # PPO-3 one coherent variable, priority, triangulation
    v = s.get("variable") or {}
    req(v.get("asset_type") in ("first_screenshot","screenshots_full_set","preview","icon"), "PPO-3", f"asset type {v.get('asset_type')} is not a PPO-testable asset (icon / screenshots / preview only)")
    req(v.get("priority_order_checked") is True, "PPO-3", "priority order not checked (first screenshot > full set as story > preview > icon; test details before positioning is a wasted slot)")
    req(v.get("single_coherent_variable") is True or v.get("bundle_is_positioning_decision") is True, "PPO-3", "treatment bundles several variables without declaring it a positioning-bundle decision (a win would be unattributable)")
    if treatments == 3 and v.get("asset_type") in ("first_screenshot","screenshots_full_set"):
        req(v.get("triangulation_plan") is True, "PPO-3", "3 treatments planned without a triangulation plan (image-only / copy-only / combined), so the slot cannot isolate the lever")
    req(v.get("first_screenshot_is_outcome_led_or_tested_as_such") is True, "PPO-3", "first screenshot is not outcome-led and is not being tested as such (the first screenshot carries the page; a feature tour first is the known weak form)")

    # PPO-4 readiness / mechanics
    r = s.get("readiness") or {}
    req((r.get("duration_days_planned") or 999) <= 90, "PPO-4", f"planned duration {r.get('duration_days_planned')}d > 90d cap")
    req(r.get("no_pause_resume_acknowledged") is True, "PPO-4", "no-pause / no-resume and cannot-modify-after-start not acknowledged in the plan")
    req(r.get("treatment_review_planned") is True, "PPO-4", "App Review for new treatment metadata not planned (treatments do not go live instantly)")
    if v.get("asset_type") == "icon":
        req(r.get("alternate_icons_in_binary") is True, "PPO-4", "icon test planned but alternate icons are not in the shipped binary (untestable)")
    if v.get("asset_type") in ("first_screenshot","screenshots_full_set"):
        req(r.get("all_device_sizes_covered") is True, "PPO-4", "screenshot treatment does not cover all required device sizes (untouched sizes silently fall back to the original and dilute the treatment)")
    req(r.get("starts_in_top_locale_first") is True, "PPO-4", "test does not start in the single highest-value locale (PPO runs per-locale; a global thin split learns nothing)")

    # PPO-5 promise truth
    p = s.get("promise") or {}
    req(p.get("claims_shipped_and_true") is True, "PPO-5", "a screenshot/preview claim is not visibly supported by the shipped app (conversion from a misleading promise moves the mismatch into onboarding, retention, ratings and refunds)")
    req(p.get("first_run_fulfills_quickly") is True, "PPO-5", "first-run experience does not fulfill the page promise quickly (continuity check failed)")
    req(p.get("legible_at_display_size") is True, "PPO-5", "caption / UI not legible at App Store display size")

    # PPO-6 reading discipline (required as a pre-committed plan; checked in full when running/completed)
    m = s.get("measurement") or {}
    req(m.get("wait_for_90pct_confidence") is True, "PPO-6", "decision rule does not wait for >=90% confidence before applying or stopping (Apple's rule; an early lead is not a conclusion)")
    req(m.get("no_early_stop_on_lead") is True, "PPO-6", "early stopping on a preferred treatment's lead is not ruled out (that converts randomized testing into confirmation bias)")
    req(m.get("reads_confidence_interval") is True, "PPO-6", "reading plan does not include the confidence interval, only headline lift")
    req(m.get("reads_per_storefront") is True, "PPO-6", "reading plan does not include per-storefront / per-device breakdown (an aggregate win can hide a loss in top non-home markets)")
    req(m.get("reads_downstream") is True, "PPO-6", "reading plan does not check downstream day-1 retention / IAP rate / crash-free for the test cohort (a converting but harder-churning treatment is not a win)")
    req(m.get("install_rate_only") is not True, "PPO-6", "measurement reads install / conversion rate only")
    req(m.get("release_overlap_logged_or_avoided") is True, "PPO-6", "new-version releases during the test are not logged / avoided (a release changing the assets under test contaminates the comparison)")

    # PPO-7 record & apply
    rec = s.get("record_completeness") or {}
    req(rec.get("exact_asset_files_saved") is True, "PPO-7", "exact asset files are not saved with the experiment record ('blue screenshots won' is useless if nobody can identify which ones)")
    req(rec.get("configuration_saved") is True, "PPO-7", "configuration (treatments, allocation, dates, locale) not saved with the record")
    req(rec.get("confounders_saved") is True, "PPO-7", "confounders (releases, pricing, featuring, campaigns, seasonality) not saved with the record")
    req(rec.get("inconclusive_preserved_as_evidence") is True, "PPO-7", "inconclusive results are not preserved as evidence about test sensitivity (no-decision is still a result)")
    if decision == "completed":
        req(rec.get("decision_applied_recorded") is True, "PPO-7", "completed test has no recorded apply / keep / revise / rerun decision")
        warn(s.get("icon_win_binary_update_scheduled") is not False, "PPO-7", "icon win: check that a future binary update is scheduled (applying an icon treatment does not change the default icon by itself)")

    print(f"app={s.get('app')} decision={decision} treatments={treatments} projected_90d_impressions={proj}")
    for f in fails: print(" FAIL", f)
    for w in warns: print(" WARN", w)
    print("RESULT", "FAIL" if fails else "PASS", f"({len(fails)} fails, {len(warns)} warns)")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
