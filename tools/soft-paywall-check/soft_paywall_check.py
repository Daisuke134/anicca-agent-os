#!/usr/bin/env python3
"""soft-paywall-check: deterministic gate for soft paywall / freemium tier design.
Stdlib only, offline, free. Sources:
- RevenueCat Freemium Playbook: dismissible contextual prompts, genuine free-tier value,
  clear free/premium distinction, paywall shown when premium feature is selected.
  https://production-docs.revenuecat.com/docs/playbooks/guides/freemium
- Airbridge hard vs soft vs freemium (RevenueCat 2026 data): hard 10.7% vs freemium 2.1%
  median Day-35 conversion; 23% of freemium conversions happen 6+ weeks after download;
  performance varies by acquisition channel -> judge on revenue per install, late window, by channel.
  https://www.airbridge.io/en/blog/hard-vs-soft-paywalls
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    # S-1 dismissible
    if d.get("paywall_dismissible") is not True:
        fails.append("S-1 paywall is not dismissible (blocks free content)")
    # S-2 genuine free core incl. aha
    free = d.get("free_core") or []
    if not free:
        fails.append("S-2 free_core is empty (no genuine free tier)")
    if d.get("free_core_includes_aha") is not True:
        fails.append("S-2 core aha is not reachable for free (first value held hostage)")
    # S-3 split documented + clear distinction
    prem = d.get("premium_features") or []
    if d.get("split_documented") is not True:
        fails.append("S-3 free/premium split is not documented")
    if not prem:
        fails.append("S-3 premium_features is empty (no upgrade path)")
    overlap = sorted(set(free) & set(prem))
    if overlap:
        fails.append(f"S-3 features listed as both free and premium: {overlap}")
    # S-4 contextual re-prompts
    trig = set(d.get("reprompt_triggers") or [])
    if "locked_feature_tap" not in trig:
        fails.append("S-4 no paywall prompt when a premium feature is selected")
    if len(trig) < 2:
        fails.append(f"S-4 fewer than 2 reprompt triggers defined: {sorted(trig)}")
    # S-5 judged on revenue per install with late window >=42d
    metrics = set(d.get("judge_metrics") or [])
    if "revenue_per_install" not in metrics:
        fails.append("S-5 revenue_per_install is not a judge metric (conversion alone misleads for freemium)")
    w = d.get("observation_window_days") or 0
    if w < 42:
        fails.append(f"S-5 observation window {w}d < 42d (23% of freemium conversions land 6+ weeks out)")
    # S-6 channel breakdown
    if d.get("channel_breakdown") is not True:
        fails.append("S-6 results are not broken down by acquisition channel")
    # warnings
    if d.get("refund_rate_tracked") is not True:
        warns.append("W-1 refund rate not tracked (benchmark context: hard ~5.8% vs freemium ~3.4%, RevenueCat 2025 via secondary summary)")
    return fails, warns

def main():
    if len(sys.argv) != 2:
        print("usage: soft_paywall_check.py <design.json>"); return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails, warns = check(d)
    for w in warns: print(f"WARN {w}")
    if fails:
        for x in fails: print(f"FAIL {x}")
        print(f"RESULT FAIL app={d.get('app')} model={d.get('model')} fails={len(fails)}")
        return 1
    print(f"RESULT PASS app={d.get('app')} model={d.get('model')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
