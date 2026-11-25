#!/usr/bin/env python3
"""review-notes-check: deterministic gate for the APP REVIEW NOTES surface.
Stdlib only, offline, free.
Sources (read 2026-11-22):
- ASO Pilot, How to write App Store Notes for Review that pass (2026-10-19)
  https://asopilot.co/blog/app-store-notes-for-review
  Guideline 2.3.1(a): all new features/functionality/product changes described
  with specificity in Notes for Review (generic descriptions rejected) and
  accessible for review. Notes field limit is 4000 BYTES (UTF-8: Japanese
  ~3 bytes/char). Guideline 2.5.19 (2026-10-16): no hidden/dormant/undocumented
  features; flags/remote config documented and ON for review accounts; never
  add functionality by server switch after approval. Demo rules (2.1(a)):
  credentials must work at submit and not expire/rotate during review; one
  account in Sign-in Information, extra roles in Notes; auto-renewable subs
  need an EXPIRED-subscription demo account so reviewer can run purchase flow;
  one-time codes provided in advance (otherwise a call, typically 3-5 business
  days); seed the account with realistic data; allowlist review accounts vs
  rate/geo/device/fraud blockers. Apple complete-review page wants: changed
  items + where to find them, purpose/audience, tested devices/OS, external
  services, regional differences. IAPs in this version listed with location
  (2.1(b)). What's New is written separately for users (2.3.12). Contact
  phone in international format with +.
- BellExpan ASC Wiki, Notes for Review templates (2026-06-27)
  https://www.bellexpan.com/en/asc-wiki/notes-for-review-templates/
  Minimization: include only how to exercise every feature (demo account, 2FA
  workaround, reproduction steps, backend-live confirmation); leave out
  marketing, unbuilt-feature teasers, gray-area self-justification. Numbered
  reproduction steps for permission/hardware/conditional features; demo video
  is a supplement, never a substitute for on-device testability. Plain English.
Exit 0=PASS, 1=FAIL, 2=PARTIAL (reserved; this gate has no optional section).
"""
import json, sys
def check(d):
    f=[]
    spec=d.get("specificity") or {}
    if not spec.get("notes_written_per_version"): f.append("RN-0 no Notes for Review are written per version (an empty field fails 2.3.1(a) whenever the version changes anything, and the reviewer has no instructions before touching the app)")
    if not spec.get("each_change_specific_with_path"): f.append("RN-0 changes are not each described specifically with a reach path (Tab > Screen > Control and what it needs) -- generic lines like 'bug fixes and improvements' are the documented 2.3.1 rejection pattern")
    if not spec.get("notes_under_4000_bytes_checked"): f.append("RN-0 the 4000-BYTE limit is not checked as bytes (Japanese text costs ~3 bytes/char, so a character-count check silently overflows and truncates the note mid-instruction)")
    if not spec.get("whatsnew_written_separately"): f.append("RN-0 What's New is not written separately for users (2.3.12) -- pasting the user text into Notes, or the reviewer note into What's New, serves neither reader")
    if not spec.get("minimization_applied"): f.append("RN-0 minimization is not applied (marketing copy, unbuilt-feature teasers and gray-area self-justification in Notes only widen the surface a reviewer can challenge; Notes are only 'how to exercise every feature')")
    demo=d.get("demo") or {}
    if not demo.get("demo_account_works_and_seeded"): f.append("RN-1 the demo account is not verified working and seeded with realistic data at submit time (a broken or empty account reads as an unfinished app under 2.1 and is the classic rejection)")
    if not demo.get("demo_valid_whole_review_no_rotation"): f.append("RN-1 demo validity for the whole review period is not guaranteed (credentials that expire or rotate while the build is in queue may be rejected before review starts; backend must stay live throughout)")
    if not demo.get("extra_roles_listed_in_notes"): f.append("RN-1 additional account roles are not listed in Notes (Sign-in Information holds one account; admin/member/expired variants the reviewer cannot reach become 'feature not found' rejections)")
    if not demo.get("expired_subscription_account_included"): f.append("RN-1 no expired-subscription demo account is included (for auto-renewable subscriptions Apple asks for one so the reviewer can run the entire purchase flow; a live-Pro account can never test buying)")
    if not demo.get("otp_method_preprovided"): f.append("RN-1 no one-time-code method is pre-provided (if sign-in needs a code, it must be fixed/automated and written in Notes in advance -- otherwise review stalls on a call that typically takes 3-5 business days, and relaying codes from a personal phone cannot work across time zones)")
    if not demo.get("review_blockers_allowlisted"): f.append("RN-1 review blockers are not checked/allowlisted (rate limits, geo blocking, device limits and fraud checks are common reasons a reviewer cannot sign in with otherwise-valid credentials)")
    reach=d.get("reachability") or {}
    if not reach.get("flags_listed_and_on_for_review"): f.append("RN-2 feature flags / remote config are not listed with everything ON for review accounts (2.5.19: no hidden, dormant or undocumented features; an off-flag feature is an undocumented one)")
    if not reach.get("no_post_approval_server_switch_additions"): f.append("RN-2 the no-post-approval-switch rule is not recorded (using a server switch to add functionality after approval is the bait-and-switch pattern Apple named in 2.5.19, punishable by removal)")
    if not reach.get("regional_differences_stated"): f.append("RN-2 regional differences are not stated (Apple's complete-review page asks for them explicitly, or a confirmation the app works the same everywhere)")
    if not reach.get("external_services_named"): f.append("RN-2 external services are not named (auth, payment, AI and data providers the app depends on -- an unnamed AI service behind a feature is both a review question and a data-use question)")
    ctx=d.get("context") or {}
    if not ctx.get("tested_devices_os_listed"): f.append("RN-3 tested device models and OS versions are not listed (Apple asks for them; without them a device-specific failure cannot be triaged against the team's own test matrix)")
    if not ctx.get("iaps_listed_with_location"): f.append("RN-3 in-app purchases in this version are not listed with where to find them (2.1(b) -- an unfindable subscription is reviewed as a missing one)")
    if not ctx.get("reproduction_steps_for_special_features"): f.append("RN-3 no numbered reproduction steps exist for permission/hardware/conditional features (a feature the reviewer cannot figure out is treated as if it does not exist; a demo video is a supplement, never a substitute for on-device testability)")
    if not ctx.get("contact_international_format"): f.append("RN-3 the review contact phone is not in international format with a leading + (a domestic-format number is undialable from the review team's country and turns a 5-minute clarification into a rejection)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
