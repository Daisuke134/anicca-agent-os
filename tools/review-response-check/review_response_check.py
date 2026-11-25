#!/usr/bin/env python3
"""Review-response Gate checker (RR-0..RR-7). Stdlib only, deterministic, offline.
Sources:
- House winner spec 2026-11-06 (Gett/AppFollow case): reply rate to 96%, target 95%,
  first response time cut to 1/5, daily 2x checks, 1-2 star first, 4-part reply shape,
  no verbatim templates, billing/emotional handwritten, weekly theme tagging
  (>=5 same complaint in 7 days -> theme), re-reply after fix, measurement order.
- AppsTemple 'Responding to App Reviews: The Strategy That Lifts Your Rating in 2026'
  (full read 2026-11-13): >=50% response -> +0.3-0.7 stars/90d (platform tracking,
  secondary), 38% update after a response, triage 1-2 star last 30 days first,
  specific before vague, then 4-5 star, two-sentence negative reply
  (acknowledge specific + concrete resolution path), reply within 24h,
  negative <150 words / positive <75 words, no template, no arguing,
  no rating-update ask in the first response, fixed schedule.
- Apple rules as quoted by appranker/appbot (secondary quoting Apple):
  one response per review, reviewer notified and can update, concise/respectful,
  no personal information / marketing / spam, personalise rather than generic,
  prioritise lowest ratings and technical issues on the current version.
Role note: 2026-11-06 house spec recorded Account Holder/Admin/App Manager, while
2026 secondary sources (marteso, citing current ASC Help) record Account Holder/
Admin/Customer Support. The checker therefore requires the role to be recorded AND
verified in ASC, and does not itself assert which list is current.
"""
import json, sys

def check(d):
    fails, warns = [], []
    # RR-0 existence: program, ASC baseline, verified responder role
    if d.get("program_recorded") is not True:
        fails.append("RR-0: no review-response program recorded")
    base = d.get("asc_baseline") or {}
    for k in ["avg_rating", "review_count", "unanswered_count"]:
        if base.get(k) is None:
            fails.append(f"RR-0: ASC baseline {k} not measured")
    if not d.get("responder_role"):
        fails.append("RR-0: responder role not recorded")
    elif d.get("role_verified_in_asc") is not True:
        fails.append("RR-0: responder role recorded but not verified in ASC (role lists differ between 2026-11-06 spec and 2026 secondary sources)")
    # RR-1 coverage and speed
    rate = d.get("response_rate")
    if rate is None:
        fails.append("RR-1: response rate not measured (denominator = all reviews in period)")
    elif rate < 0.50:
        fails.append(f"RR-1: response rate {rate} below the 50% floor tied to rating lift")
    elif rate < 0.95:
        warns.append(f"RR-1: response rate {rate} above 50% floor but below winner target 95% (Gett reached 96%)")
    hrs = d.get("median_first_response_hours")
    if hrs is None:
        fails.append("RR-1: median first-response time not measured")
    elif hrs > 24:
        fails.append(f"RR-1: median first response {hrs}h over 24h (update probability drops after 72h)")
    if (d.get("checks_per_day") or 0) < 2:
        fails.append("RR-1: review queue not checked 2x/day (house winner rhythm 9:00 / 16:00 JST)")
    # RR-2 triage order
    t = d.get("triage") or {}
    if t.get("low_star_last_30d_first") is not True:
        fails.append("RR-2: 1-2 star reviews from the last 30 days are not triaged first")
    if t.get("specific_before_vague") is not True:
        fails.append("RR-2: specific complaints are not handled before vague ones")
    if t.get("positive_after_low_star") is not True:
        fails.append("RR-2: 4-5 star reviews are not answered after low-star triage")
    if t.get("crash_billing_escalated_immediately") is not True:
        fails.append("RR-2: crash / login / billing / lost-progress mentions are not escalated immediately")
    # RR-3 reply shape (per sampled reply)
    neg = d.get("sample_negative_reply") or {}
    if not neg:
        fails.append("RR-3: no negative reply sampled/recorded")
    else:
        if neg.get("acknowledges_specific_issue") is not True:
            fails.append("RR-3: negative reply does not acknowledge the specific issue in the reviewer's words")
        if neg.get("concrete_resolution_path") is not True:
            fails.append("RR-3: negative reply has no concrete resolution path (fix + version, or one next step)")
        if (neg.get("words") or 999) > 150:
            fails.append("RR-3: negative reply over 150 words")
        if neg.get("apology_chain") is True:
            warns.append("RR-3: negative reply stacks multiple apologies (reads as a template)")
    pos = d.get("sample_positive_reply") or {}
    if pos and (pos.get("words") or 999) > 75:
        fails.append("RR-3: positive reply over 75 words")
    # RR-4 prohibitions
    for key, msg in [
        ("uses_verbatim_template", "RR-4: verbatim template replies used (42% of replies in a 2026 survey were verbatim repeats)"),
        ("argues_with_reviewer", "RR-4: reply argues with / publicly corrects the reviewer"),
        ("asks_rating_update_in_first_response", "RR-4: first response asks for a rating update (resolution must come first)"),
        ("includes_personal_information", "RR-4: reply includes personal information (Apple prohibition)"),
        ("includes_marketing_language", "RR-4: reply includes marketing language or spam (Apple prohibition)"),
    ]:
        if d.get(key) is True:
            fails.append(msg)
    # RR-5 handwritten line
    if d.get("billing_and_emotional_handwritten") is not True:
        fails.append("RR-5: billing / payment / emotional complaints are not handwritten")
    if d.get("automation_limited_to_short_positive_and_common") is not True:
        fails.append("RR-5: automation is not limited to short positive thanks and common questions")
    # RR-6 follow-through
    if d.get("re_reply_after_fix") is not True:
        fails.append("RR-6: no re-reply (edited response) recorded after a fix shipped for a reported issue")
    th = d.get("theme_tagging") or {}
    if th.get("weekly") is not True:
        fails.append("RR-6: reviews are not tag-aggregated weekly")
    if th.get("theme_threshold") != 5:
        fails.append("RR-6: theme threshold is not '>=5 same complaints in 7 days -> theme to product owner'")
    if th.get("shared_with_product_loop") is not True:
        fails.append("RR-6: top themes are not shared with the product loop")
    # RR-7 measurement order
    m = d.get("metrics") or {}
    for k in ["response_rate", "median_first_response_hours", "rating_change", "updates_after_response"]:
        if m.get(k) is None:
            fails.append(f"RR-7: metric {k} not measured")
    if m.get("looks_beyond_rating") is not True:
        fails.append("RR-7: judgement stops at rating alone (must also read conversion / installs / retention after exit)")
    return fails, warns

def main():
    with open(sys.argv[1]) as f: d = json.load(f)
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for x in fails: print("FAIL:", x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__": main()
