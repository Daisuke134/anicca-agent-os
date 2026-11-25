#!/usr/bin/env python3
"""asa-check: deterministic gate checker for Apple Ads (formerly Apple Search Ads) readiness.
Reads a JSON description of an app's Apple Ads state and judges gates ASA-0..ASA-12.
Stdlib only, offline, no API keys, no spend. Exit 0 = PASS, 1 = FAIL.

Sources (full-text read 2026-11-21):
 - Adapty "Apple Search Ads in 2026: Cost, Placements & Bidding"
   https://adapty.io/blog/apple-search-ads/
   (renamed Apple Ads 2025-04-14; Advanced = CPT, Basic = CPI; trial start 3.66% vs 1.45%
    other paid, paid conversion 1.92% vs 0.91%; Apple reporting stops at the download;
    median download $0.51 across 90 markets, weighted $1.34; US CPT $1.58 / download $2.51 /
    CR 62.7%; CPT varies 14x across markets; 5 ad-group structures; Maximize Conversions
    opened 2026-02, target is an average not a ceiling, requires Search Match, optimizes
    downloads only; multiple search ad positions since 2026-03-03 on iOS 26.2+, UK/Japan first;
    CPP: TTR 9.72%->10.90% (+12.1%), CR 63.91%->70.05% (+9.6%), compounded +22.9% downloads,
    build 3-5 intent clusters not per-keyword pages; tailored paywall: install->trial +41.5%,
    trial->paid +24.2%, compounded 1.76x paying users, ROAS uplift 48.4% day 0 -> 82.5% day 92,
    so Day-7 reads sit inside the churn window; cost per paying subscriber <$20 in 24 countries,
    median year-1 LTV $26.04, US $48.25; daily budget x 30.4 = effective monthly spend)
 - Adapty "How to lower Apple Ads CPA: diagnostic guide for 2026"
   https://adapty.io/blog/how-to-lower-apple-ads-cpa/
   (CPA = CPT / CR; diagnose CPT vs same-market median and CR vs niche median, fix the lever
    further from its median; CR range <40% to >78% across 59 sub-categories is wider than the
    CPT range; lowering bids first usually raises CPA; negative keywords protect TTR;
    exact match for high-intent, broad only for discovery; CPP lift TTR +12% / CR +9.6%;
    tailored paywalls lift trial-to-paid +24%; a CPA is only judgeable against LTV/ROAS)
Company rules encoded: no paid growth without a recorded gross-profit case; no auto-reload;
benchmarks are context, never targets.
"""
import json, sys

def main():
    if len(sys.argv) < 2:
        print("usage: asa_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        s = json.load(f)
    fails, warns = [], []
    def req(cond, gate, msg):
        if not cond: fails.append(f"{gate}: {msg}")
    def warn(cond, gate, msg):
        if not cond: warns.append(f"{gate}: {msg}")

    # ASA-0 inventory + decision
    req(s.get("inventory_recorded") is True, "ASA-0", "Apple Ads account/campaign state not recorded")
    req(s.get("decision_recorded") is True, "ASA-0", "no recorded decision (readiness-only vs spend)")
    req(s.get("auto_reload_enabled") is not True, "ASA-0", "auto reload / uncapped spend enabled")
    if s.get("campaigns_running"):
        req(s.get("gross_profit_case_recorded") is True, "ASA-0", "campaigns running without a recorded gross-profit case")

    # ASA-1 revenue attribution before spend decisions
    a = s.get("attribution", {})
    req(a.get("joined_to_subscription_events") is True, "ASA-1", "Apple Ads data not joined to subscription events (Apple stops at downloads)")
    req(a.get("keyword_level_trial_and_subscriber_visible") is True, "ASA-1", "no keyword-level trial/subscriber visibility")
    req(a.get("decisions_on_downloads_only") is not True, "ASA-1", "budget decisions are made on downloads only")

    # ASA-2 allowable CPA from own LTV
    e = s.get("economics", {})
    req(e.get("allowable_cpa_derived_from_own_ltv") is True, "ASA-2", "allowable CPA / max CPT not derived from own LTV")
    req(e.get("benchmarks_are_context_only") is True, "ASA-2", "global benchmarks ($0.51 median etc.) are being used as targets")
    req(bool(e.get("benchmark_denominator_recorded")), "ASA-2", "benchmark market+niche denominator not recorded")

    # ASA-3 funnel-first diagnostic
    d = s.get("diagnostic", {})
    req(d.get("compares_cpt_and_cr_to_same_market_medians") is True, "ASA-3", "no CPT-vs-CR same-market median diagnostic")
    req(d.get("fixes_cr_before_bid_changes") is True, "ASA-3", "bid changes come before funnel (CR) fixes")
    req(d.get("bid_cut_is_first_move") is not True, "ASA-3", "lowering bids is the first move (usually raises CPA)")

    # ASA-4 structure
    st = s.get("structure", {})
    req(st.get("campaigns_split_by_country_cluster") is True, "ASA-4", "campaigns not split by country cluster (CPT varies 14x; blended campaigns let expensive markets eat the budget)")
    types = set(st.get("ad_group_types") or [])
    req({"brand","competitor","category","feature","discovery"} <= types, "ASA-4", f"ad-group types incomplete: {sorted(types)}")
    req(st.get("naming_convention_recorded") is True, "ASA-4", "campaign naming convention not recorded")

    # ASA-5 match types
    m = s.get("match_types", {})
    req(m.get("exact_for_brand_and_high_intent") is True, "ASA-5", "exact match not reserved for brand/high-intent terms")
    req(m.get("search_match_only_in_discovery") is True, "ASA-5", "Search Match runs outside a dedicated discovery group")
    req(m.get("winners_promoted_to_manual_groups") is True, "ASA-5", "Search Match winners are not promoted into manual groups")

    # ASA-6 negatives
    n = s.get("negatives", {})
    req(n.get("maintained_from_day_one") is True, "ASA-6", "negative keyword list not maintained from day one")
    req((n.get("review_cadence_days") or 999) <= 7, "ASA-6", "negative keyword review cadence > 7 days")

    # ASA-7 CPP intent mapping
    c = s.get("cpp_mapping", {})
    cl = c.get("intent_clusters") or 0
    req(3 <= cl <= 5, "ASA-7", f"intent clusters = {cl} (winner form is 3-5 clusters, not per-keyword pages)")
    req(c.get("one_intent_one_group_one_page") is True, "ASA-7", "mapping is not 1 intent -> 1 ad group -> 1 CPP -> 1 active custom ad")
    req(c.get("first_screenshot_is_searched_result") is True, "ASA-7", "CPP first screenshot is not the searched-for result")
    req(c.get("brand_stays_on_default_page") is True, "ASA-7", "brand traffic is routed to a CPP instead of the default page")

    # ASA-8 paywall match + window
    p = s.get("paywall_match", {})
    req(p.get("paywall_matches_cpp_intent_per_cluster") is True, "ASA-8", "paywall does not match the CPP/search intent per cluster")
    req(p.get("judged_on_revenue_not_cr") is True, "ASA-8", "tailored variants judged on conversion rate, not revenue")
    req((p.get("measurement_window_days") or 0) >= 90, "ASA-8", f"measurement window {p.get('measurement_window_days')}d < 90d (Day-7 reads sit in the churn window; uplift grows to day 92)")

    # ASA-9 bid strategy guardrails
    b = s.get("bidding", {})
    req(b.get("maximize_conversions_only_for_discovery") is True, "ASA-9", "Maximize Conversions used beyond discovery (it optimizes downloads, requires Search Match, target is an average not a ceiling)")
    req(b.get("manual_cpt_on_known_converters") is True, "ASA-9", "known converting terms are not on manual CPT bidding")
    req(b.get("monthly_cap_from_daily_x_30_4_recorded") is True, "ASA-9", "effective monthly cap (daily budget x 30.4) not recorded")

    # ASA-10 market selection
    mk = s.get("markets", {})
    req(mk.get("ranked_by_cost_per_paying_subscriber") is True, "ASA-10", "markets ranked by CPT/downloads, not cost per paying subscriber vs LTV")
    req(mk.get("starts_where_organic_already_performs") is True, "ASA-10", "launch markets are not the 3-5 where the app already performs organically")
    req(mk.get("high_cpa_high_cr_not_auto_killed") is True, "ASA-10", "high-CPA/high-CR markets are auto-killed (that quadrant is priced correctly)")

    # ASA-11 keyword evidence
    k = s.get("keyword_evidence", {})
    req(k.get("demand_evidence_recorded_per_cluster") is True, "ASA-11", "no demand evidence recorded per intent cluster (OwlASO / Apple suggestions / Search Match mining)")
    req(k.get("generic_head_terms_flagged") is True, "ASA-11", "generic head terms not flagged as awareness/budget-burn risk")

    # ASA-12 spend guardrails (company rules)
    g = s.get("spend_guardrails", {})
    req(g.get("budget_cap_recorded") is True, "ASA-12", "no budget cap recorded")
    req(g.get("no_spend_without_gross_profit_case") is True, "ASA-12", "spend is possible without a gross-profit case (company rule: paid growth is not considered without one)")

    print(f"app={s.get('app')} running={s.get('campaigns_running')}")
    for w in warns: print("WARN " + w)
    for f_ in fails: print("FAIL " + f_)
    print(f"result: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
