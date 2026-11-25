#!/usr/bin/env python3
"""testflight-check: deterministic gate for the TESTFLIGHT BETA surface.
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple App Store Connect Help, View tester feedback
  https://developer.apple.com/help/app-store-connect/test-a-beta-version/view-tester-feedback
Extension gate TF-6 (added 2026-11-22, spec:
 hidden_files/testflight-beta-review-gate-spec-2026-11-22.md; sources read in full
 2026-11-22: generateideas.app TestFlight guide; StoreShot "Using TestFlight to catch
 rejection risks before Apple does", 2026-10-04):
 TF-6 beta-review rehearsal: the exact build is smoke-tested internally BEFORE it is
 added to an external group; the schedule carries ~24h for the first build of each
 version to clear Beta App Review (later builds of the same version usually skip it);
 beta review information is complete (plain description, reachable contact, and a
 working non-expiring demo account where sign-in exists -- a missing demo account is
 the canonical avoidable beta rejection); export compliance is answered so it does
 not block the build; at least one uncoached external pass runs (invite only, no
 walkthrough -- where strangers stall is the reviewer signal); a beta rejection is
 recorded and its CAUSE fixed, not just the symptom; the build submitted to App
 Review is the exact externally tested build, not a fresh archive; and a beta pass
 is never recorded as an App Review pass (beta review barely inspects the listing,
 so listing accuracy stays a separate manual check).
 beta_review (optional): {internal_smoke_exact_build_first,
   lead_time_24h_in_schedule, review_info_complete, demo_account_works_or_na,
   export_compliance_answered, uncoached_external_pass_done,
   rejection_cause_fix_recorded, submit_exact_tested_build,
   beta_pass_not_conflated_with_app_review}
 Absent section = WARN unknown (PARTIAL, exit 2), never a pass.
  Feedback (screenshots, crash comments, general comments) from TestFlight 2.3+ appears in
  App Store Connect; viewable/filterable by platform, version, build group, build, OS, device;
  crash .zip downloads available 120 days; unresponsive-app crashes carry no report;
  feedback can be disabled per tester group (a tester in any disabled group falls back to email only);
  public-link testers appear anonymous; viewing requires Account Holder/Admin/App Manager/Developer/Marketing.
- Apple Developer, TestFlight overview https://developer.apple.com/testflight/
  Add test information telling testers what to test; provide a feedback email to monitor/respond;
  testers share screenshot feedback (with markup) and crash reports with context.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]; w=[]
    dec=d.get("decision") or {}
    if not dec.get("beta_purpose_recorded_per_build"): f.append("TF-0 no per-build beta purpose is recorded (builds are uploaded -- fastlane reads latest_testflight_build_number -- but why each build is in beta, and what decision it must inform, is written nowhere)")
    if not dec.get("feedback_owner_with_required_role"): f.append("TF-0 no feedback owner holding an App Store Connect role that can view feedback (Account Holder/Admin/App Manager/Developer/Marketing) is named")
    if not dec.get("test_information_and_feedback_email_set"): f.append("TF-0 Test Information / feedback email is not recorded as set (testers have no recorded route to reach the team, and older-TestFlight testers fall back to exactly this email)")
    sco=d.get("scope") or {}
    if not sco.get("groups_recorded_internal_external"): f.append("TF-1 tester groups (internal vs external) are not recorded anywhere (who is testing the build is unknowable after the fact)")
    if not sco.get("feedback_enabled_verified_per_group"): f.append("TF-1 feedback-enabled state is not verified per group (feedback can be disabled per group, and a tester in any one disabled group can only email -- silence would be misread as 'no problems')")
    if not sco.get("public_link_anonymity_understood"): f.append("TF-1 public-link anonymity is not recorded (public-link testers appear anonymous, so follow-up cannot be planned as if every report were attributable)")
    wtt=d.get("what_to_test") or {}
    if not wtt.get("what_to_test_written_per_build"): f.append("TF-2 no per-build What to Test notes exist (testers are given uploads, not questions; unguided beta produces unguided feedback)")
    if not wtt.get("testers_told_how_to_send_screenshot_feedback"): f.append("TF-2 testers are not told how to send screenshot feedback from inside the app (the highest-signal channel is opt-in knowledge most testers do not have)")
    rea=d.get("readback") or {}
    if not rea.get("screenshot_feedback_read_on_cadence"): f.append("TF-3 screenshot feedback in App Store Connect is never read back on a recorded cadence (the Feedback > Screenshots queue has no reader and no schedule)")
    if not rea.get("crash_feedback_read_on_cadence"): f.append("TF-3 crash feedback is never read back on a recorded cadence (beta crashes -- the one crash channel that exists before any in-app reporting SDK -- go unseen)")
    if not rea.get("crash_download_120d_window_respected"): f.append("TF-3 the 120-day crash-report download window is not tracked (reports expire undownloaded; an unresponsive-app crash carries no report at all and must be caught another way)")
    tri=d.get("triage") or {}
    if not tri.get("every_feedback_classified_with_owner"): f.append("TF-4 feedback is not classified item-by-item with an owner (no fix-now / task / duplicate / deferred record exists, so the same report can be triaged twice or never)")
    if not tri.get("severity_order_crash_and_dataloss_first"): f.append("TF-4 no severity order is recorded (crashes and data-loss/privacy reports must outrank cosmetic screenshot notes; without the order, triage order is arrival order)")
    if not tri.get("survivors_become_issues"): f.append("TF-4 surviving feedback items do not become tracked Issues (TestFlight has no reply channel, so an item that is not written into the tracker exists only in a console nobody opens)")
    mea=d.get("measurement") or {}
    if not mea.get("build_metrics_read_per_build"): f.append("TF-5 per-build beta metrics (installs / sessions / crashes) are not read back (beta signal is reduced to whether the build number incremented)")
    if not mea.get("expiry_90d_tracked"): f.append("TF-5 the 90-day build expiry is not tracked (a beta build silently stops working for every tester 90 days after upload)")
    if not mea.get("beta_learnings_recorded_before_submission"): f.append("TF-5 no beta learnings record is kept before App Review submission (what beta changed is asserted from memory, not measured from feedback)")
    # TF-6 beta-review rehearsal (optional section; absent = unknown, never a pass)
    br=d.get("beta_review")
    if br is None:
        w.append("TF-6 beta_review is unrecorded (unknown, not a pass -- internal-first order, beta-review lead time, review-info completeness, uncoached pass, rejection handling and exact-build submission are all unmeasured)")
    else:
        if not br.get("internal_smoke_exact_build_first"): f.append("TF-6 the exact build was not smoke-tested internally before external distribution (internal testing is the fast, review-free loop that catches staging backends, launch crashes and pipeline breakage; external testers -- and Beta App Review -- should never be the first eyes on a build)")
        if not br.get("lead_time_24h_in_schedule"): f.append("TF-6 the schedule carries no ~24h lead time for Beta App Review of the first build of a version (that review gates external availability; a plan that assumes instant external access slips by a day per version bump)")
        if not br.get("review_info_complete"): f.append("TF-6 beta app review information is incomplete (plain beta description + reachable contact are required before external testers can install; incomplete review info delays the whole external round)")
        if not br.get("demo_account_works_or_na"): f.append("TF-6 no working, non-expiring demo account is recorded for the reviewer (or its not-applicable reason) -- a reviewer stopped at a login wall they cannot pass is the canonical avoidable beta rejection")
        if not br.get("export_compliance_answered"): f.append("TF-6 export compliance is not answered (a Missing Compliance state blocks the build from testing entirely; answering it once in the target removes the recurring per-upload ambush)")
        if not br.get("uncoached_external_pass_done"): f.append("TF-6 no uncoached external pass is recorded (invite only, no walkthrough: where strangers stall, what they never find, and what looks broken is exactly the reviewer experience; coached testers forgive what reviewers reject)")
        if not br.get("rejection_cause_fix_recorded"): f.append("TF-6 beta-rejection handling is not recorded (a beta rejection is the cheapest rejection Apple offers -- the note must be read and the CAUSE fixed, e.g. the untested device family behind a crash, not only the symptom)")
        if not br.get("submit_exact_tested_build"): f.append("TF-6 the submitted build is not recorded as the exact externally tested build (a fresh archive with one more quick fix resets the rehearsal's value to zero; the binary strangers exercised is the binary that should be reviewed)")
        if not br.get("beta_pass_not_conflated_with_app_review"): f.append("TF-6 a beta pass is treated as evidence of App Review readiness (Beta App Review is lighter and barely inspects the listing -- screenshot/description accuracy and judgment-call guidelines remain a separate manual check)")
    return f,w
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails,warns=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]
        [print(" ~ warn:",x) for x in warns]; sys.exit(1)
    if warns:
        print(f"PARTIAL ({len(warns)} unknown):")
        [print(" ~ warn:",x) for x in warns]; sys.exit(2)
    print("PASS")
