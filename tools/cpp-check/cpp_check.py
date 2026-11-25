#!/usr/bin/env python3
"""cpp-check: deterministic gate checker for App Store Custom Product Pages.
Reads a JSON description of an app's CPP state and judges gates CPP-0..CPP-7,
plus the optional organic-search extension CPP-8..CPP-11 (2026-11-22):
intent grouping + in-app evidence per keyword page, no ranking-shortcut
expectation, 70-page cap with thin-page retire rule, per-assigned-query
comparison vs default with downstream quality, joint keyword+creative
change log, and UI-change maintenance. Extension section `organic_search`
is optional for backward compatibility: absent = PARTIAL, exit 2.
Canonical sources (read in full 2026-11-22): Cortex CPP organic search
guide (2026-10-28) and ScreenShipper CPP guide (2026-11-04).
Stdlib only, offline, no API keys. Exit 0 = PASS, 1 = FAIL, 2 = PARTIAL."""
import json, sys

def main():
    if len(sys.argv) < 2:
        print("usage: cpp_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        s = json.load(f)
    fails, warns = [], []
    def req(cond, gate, msg):
        if not cond: fails.append(f"{gate}: {msg}")
    # CPP-0 inventory recorded + plan exists
    req(s.get("inventory_recorded") is True, "CPP-0", "ASC CPP inventory not recorded")
    req(isinstance(s.get("planned_pages"), list) and len(s.get("planned_pages", [])) >= 1, "CPP-0", "no planned CPP pages")
    pages = s.get("planned_pages", [])
    # CPP-1 round-1 page count 1..5
    req(1 <= len(pages) <= 5, "CPP-1", f"round-1 pages = {len(pages)} (must be 1..5)")
    # CPP-2 selection evidence per keyword page
    for p in pages:
        if p.get("type") == "keyword":
            req((p.get("monthly_impressions") or 0) >= 200, "CPP-2", f"{p.get('name')}: impressions < 200/mo")
            req(p.get("converts_below_average") is True, "CPP-2", f"{p.get('name')}: not evidenced below-average conversion")
            req(p.get("branded") is False, "CPP-2", f"{p.get('name')}: branded query page")
            cl = p.get("cluster_size") or 0
            req(2 <= cl <= 6, "CPP-2", f"{p.get('name')}: cluster size {cl} not in 2..6")
    # CPP-3 keyword rules
    seen = {}
    live_kw = set(k.lower() for k in s.get("live_keyword_field", []))
    for p in pages:
        kws = [k.lower() for k in p.get("keywords", [])]
        if p.get("type") == "direct_link":
            req(len(kws) == 0, "CPP-3", f"{p.get('name')}: direct-link page must carry no keywords")
        for k in kws:
            req(k in live_kw, "CPP-3", f"{p.get('name')}: keyword '{k}' not in live keyword field")
            req(k not in seen, "CPP-3", f"keyword '{k}' assigned to more than one page")
            seen[k] = p.get("name")
    # CPP-4 creative rules
    for p in pages:
        req(p.get("cloned_from_default") is True, "CPP-4", f"{p.get('name')}: not cloned from default set")
        req(p.get("ban_list_audited") is True, "CPP-4", f"{p.get('name')}: ban-list audit not done")
        req(p.get("first_screenshot_shows_result") is True, "CPP-4", f"{p.get('name')}: first screenshot is not the result screen")
        pt = p.get("promo_text") or ""
        req(0 < len(pt) <= 170, "CPP-4", f"{p.get('name')}: promo text length {len(pt)} not in 1..170")
        kws = p.get("keywords", [])
        if kws:
            req(kws[0].lower() in pt[:40].lower(), "CPP-4", f"{p.get('name')}: primary keyword not in first 40 chars of promo text")
    # CPP-5 deep link continuity
    for p in pages:
        req(bool(p.get("deep_link_target")), "CPP-5", f"{p.get('name')}: no deep link target")
        req(p.get("lands_on_generic_welcome") is False, "CPP-5", f"{p.get('name')}: lands on generic welcome")
    # CPP-6 measurement plan
    m = s.get("measurement", {})
    req(m.get("baseline_formula_recorded") is True, "CPP-6", "baseline formula not recorded")
    req(m.get("primary_metric") == "revenue_per_page_view", "CPP-6", "primary metric is not revenue per page view")
    req(m.get("d7_retention_guardrail") is True, "CPP-6", "D7 retention guardrail missing")
    req(m.get("reroute_below_1x") is True, "CPP-6", "under-1x reroute rule missing")
    # CPP-7 submission state consistency
    sub = s.get("submitted_pages", 0)
    if sub == 0:
        warns.append("CPP-7: 0 pages submitted (plan-only state)")
    for p in pages:
        if p.get("wired") is True:
            req(p.get("approved") is True, "CPP-7", f"{p.get('name')}: wired before approval")
            req(p.get("unapproved_fallback") is True, "CPP-7", f"{p.get('name')}: no unapproved-ID fallback guard")
    # CPP-8..CPP-11 organic-search extension (optional section)
    partial = False
    os_ = s.get("organic_search")
    if os_ is None:
        partial = True
        warns.append("CPP-8..11: organic_search section not recorded (unknown, PARTIAL)")
    else:
        req(os_.get("queries_grouped_by_intent") is True, "CPP-8", "queries not grouped by intent")
        req(os_.get("ranking_shortcut_expected") is False, "CPP-9", "keyword assignment treated as ranking shortcut")
        total = (os_.get("live_pages") or 0) + len(pages)
        req(total <= 70, "CPP-9", f"live+planned pages = {total} (>70 cap)")
        req(os_.get("thin_page_retire_rule") is True, "CPP-9", "no merge/retire rule for low-traffic pages")
        req(os_.get("compares_vs_default_same_queries") is True, "CPP-10", "no per-assigned-query comparison vs default")
        req(os_.get("downstream_quality_checked") is True, "CPP-10", "downstream quality (retention+proceeds) not checked")
        req(os_.get("sparse_traffic_qualitative_check") is True, "CPP-10", "no qualitative check for sparse traffic")
        req(os_.get("change_log_joint_keyword_creative") is True, "CPP-10", "change log does not record keyword and creative changes together")
        req(os_.get("ui_change_triggers_cpp_refresh") is True, "CPP-11", "UI change does not trigger CPP screenshot refresh")
        req(os_.get("monthly_review_cadence") is True, "CPP-11", "no monthly CPP review cadence")
        req(os_.get("promo_text_not_ranking_factor_acknowledged") is True, "CPP-11", "plan assumes promo text affects ranking")
        seen_intents = {}
        for p in pages:
            if p.get("type") == "keyword":
                iv = (p.get("intent_sentence") or "").strip().lower()
                req(bool(iv), "CPP-8", f"{p.get('name')}: no intent sentence")
                if iv:
                    req(iv not in seen_intents, "CPP-8", f"{p.get('name')}: intent sentence interchangeable with {seen_intents.get(iv)}")
                    seen_intents[iv] = p.get("name")
                req(p.get("evidence_in_app_verified") is True, "CPP-8", f"{p.get('name')}: page promise not verified as real in-app evidence")
    print(f"pages={len(pages)} submitted={sub}")
    for w in warns: print("WARN " + w)
    for f_ in fails: print("FAIL " + f_)
    if fails:
        print(f"result: FAIL ({len(fails)} fails, {len(warns)} warns)"); return 1
    if partial:
        print("result: PARTIAL (organic-search extension unknown)"); return 2
    print(f"result: PASS (0 fails, {len(warns)} warns)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
