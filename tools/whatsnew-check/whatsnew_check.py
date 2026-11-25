#!/usr/bin/env python3
"""whatsnew-check: deterministic gate checker for App Store What's New notes.
Stdlib only, offline. Exit 0=PASS, 1=FAIL.
Sources read in full 2026-11-14:
- AppGrowKit release-notes guide https://www.appgrowkit.com/release-notes-generator
  (4000 char cap; first ~170 chars visible before 'more'; lead with user benefit
   not the change; avoid 'bug fixes and performance improvements' - specific
   notes lift update adoption 30-50% per their testing, attributed claim;
   no version number in body; end with an invitation, not a sign-off;
   lead aim 80-200 chars; blend: one human benefit sentence + specific bullets)
- Spreadcast/Appalize guides via search results 2026-11-14: Apple Guideline
  2.3.12 requires What's New to clearly describe new features/changes;
  generic description allowed only for simple bug-fix releases; notes are
  NOT search-indexed (write for humans); read by most engaged users and by
  prospective users judging active maintenance.
- Coderio 2026 guide: top apps update every 20-40 days; minor updates
  every 2-4 weeks.
Winner benchmark measured live 2026-11-14 via iTunes Lookup API:
  I am 7.9.0 (2026-11-12): bullets, ends with review invitation.
  Anicca 1.9.12 (2026-11-12): benefit-led lead, generic tail, no invitation.
"""
import json, re, sys
from datetime import date

GENERIC = ["bug fixes and performance improvements", "bug fixes & performance improvements"]
INVITE = ["tell us", "let us know", "what to build next", "reply", "feedback", "review", "support@", "contact", "email us", "share your"]

def main():
    if len(sys.argv) < 2:
        print("usage: whatsnew_check.py <state.json>"); return 2
    s = json.load(open(sys.argv[1]))
    fails, warns = [], []
    def req(c,g,m):
        if not c: fails.append(f"{g}: {m}")
    def warn(c,g,m):
        if not c: warns.append(f"{g}: {m}")
    notes = s.get("release_notes") or ""
    low = notes.lower()
    # WN-0 record
    req(bool(notes), "WN-0", "release notes not recorded")
    req(bool(s.get("version")), "WN-0", "version not recorded")
    req(bool(s.get("release_date")), "WN-0", "release date not recorded")
    req(s.get("changes_verified") is True, "WN-0", "notes not verified against shipped changes (invented claims forbidden)")
    if not notes:
        print("FAIL"); [print(" FAIL",f) for f in fails]; return 1
    # WN-1 length + lead
    req(len(notes) <= 4000, "WN-1", f"notes {len(notes)} chars > 4000")
    first_line = notes.strip().split("\n")[0].lstrip("-• ").strip()
    req(20 <= len(first_line) <= 220, "WN-1", f"lead line {len(first_line)} chars (aim 80-200, must carry the top benefit alone)")
    lead170 = notes.strip()[:170]
    req(any(ch in lead170 for ch in ".!") or len(notes.strip())<=170, "WN-1", "first 170 chars contain no complete sentence (the visible window must land a full benefit)")
    # WN-2 generic boilerplate
    generic_present = any(g in low for g in GENERIC)
    specific_lines = [l for l in notes.split("\n") if l.strip() and not any(g in l.lower() for g in GENERIC)]
    if generic_present:
        req(len(specific_lines) >= 1 and len(" ".join(specific_lines)) >= 60, "WN-2", "generic boilerplate with no specific change named (Guideline 2.3.12: significant changes must be listed)")
        warn(False, "WN-2", "generic phrase 'bug fixes and performance improvements' present even alongside specifics - it dilutes the specific lead")
    # WN-3 no version number in body
    req(not re.search(r"\bversion\s+\d+\.\d+", low), "WN-3", "version number in body (Apple shows it above the notes; it wastes the visible window)")
    req(not re.search(r"\bv\d+\.\d+\.\d+\b", low), "WN-3", "version string in body")
    # WN-4 structure: lead + at least one more specific line/bullet
    req(len([l for l in notes.split('\n') if l.strip()]) >= 2 or len(notes) > 220, "WN-4", "single short line only: no specific change listed below the lead")
    warn(len(notes) <= 1500, "WN-4", f"notes {len(notes)} chars > 1500 recommended (long changelogs belong on a changelog page)")
    # WN-5 ends with invitation
    tail = low[-max(120, len(low)//4):]
    req(any(k in tail for k in INVITE), "WN-5", "notes do not end with an invitation (feedback / review / what to build next) - ends as a sign-off or changelog")
    # WN-6 cadence
    rd = s.get("release_date"); td = s.get("today")
    if rd and td:
        try:
            gap = (date.fromisoformat(td) - date.fromisoformat(rd)).days
            req(gap <= 40, "WN-6", f"last release {gap} days ago (>40: outside the 20-40 day top-app cadence)")
        except ValueError:
            fails.append("WN-6: unparseable dates")
    # WN-7 localization of notes
    locs = s.get("notes_locales") or []
    warn(len(locs) >= 3, "WN-7", f"notes localized in {len(locs)} locales (top storefronts should not ship English-only notes)")
    # WN-8 release decision layer (added 2026-11-22, spec:
    # hidden_files/whatsnew-release-decision-gate-spec-2026-11-22.md;
    # source read in full: ScreenShipper ratings explainer 2026-11-04,
    # citing Apple ASC Help / HIG): the summary-rating reset is a
    # per-release decision -- deliberate, recorded, sparing. A reset
    # applies to ALL territories at once, is irreversible once the
    # version is released, and does NOT remove written reviews. Reset
    # only when the top complaint behind low ratings is actually fixed;
    # the page then shows fewer ratings (HIG: can discourage downloads),
    # so a rebuild forecast and a working rating prompt in the new
    # version are prerequisites. Apple's AI review summary (iOS 18.4+)
    # cannot be edited -- it is read after release and improved only by
    # fixing what reviewers complain about; inaccuracies go through
    # Report a Concern in ASC. Optional/backward compatible: absent
    # section -> WARN unknown, never counted as a pass.
    rd8 = s.get("release_decision")
    if rd8 is None:
        warn(False, "WN-8", "release_decision section not recorded - the rating-reset decision and post-release summary read are unknown (not a pass)")
    else:
        req(rd8.get("decision_recorded") is True, "WN-8", "the reset-or-keep decision for this release is not recorded with its reason - an unrecorded reset decision is made by whoever submits, by default")
        if rd8.get("reset_chosen") is True:
            req(rd8.get("top_complaint_fixed_and_verified") is True, "WN-8", "reset chosen but the top complaint behind the low ratings is not recorded as fixed and verified in this version - resetting to hide a persistent problem restarts the same ratings")
            req(rd8.get("all_territories_irreversible_understood") is True, "WN-8", "reset chosen without recording that it applies to all territories at once and cannot be undone once the version is released")
            req(rd8.get("rebuild_forecast_recorded") is True, "WN-8", "reset chosen with no rebuild forecast (expected new ratings per month) - after a reset the page shows few ratings, which Apple HIG warns can discourage downloads")
            req(rd8.get("prompt_ready_in_new_version") is True, "WN-8", "reset chosen but the new version cannot yet prompt for ratings within Apple's limits - the summary has no way to refill")
        if rd8.get("version_released") is True:
            req(rd8.get("review_summary_checked_within_7d") is True, "WN-8", "version released but Apple's AI review summary was not read within 7 days - the summary is generated from written reviews (which a reset does not remove) and can carry a rough release to the product page within days")
        if rd8.get("fixes_named_review_complaint") is True:
            req(rd8.get("notes_name_the_fixed_complaint") is True, "WN-8", "this release fixes a complaint named in reviews but the What's New notes do not say so - closing the loop in the notes is what turns a fix into updated ratings")
    print(f"notes_chars={len(notes)} lead_chars={len(first_line)} locales={len(locs)}")
    for f in fails: print(" FAIL", f)
    for w in warns: print(" WARN", w)
    print("RESULT", "FAIL" if fails else "PASS", f"({len(fails)} fails, {len(warns)} warns)")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
