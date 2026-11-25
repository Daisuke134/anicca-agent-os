#!/usr/bin/env python3
"""Later-paywall Gate checker (LP-0..LP-4). Input: JSON state description. Stdlib only."""
import json, sys

def check(s):
    fails = []
    # LP-0 inventory done for 3 points
    inv = s.get("inventory", {})
    for k in ("premium_tap", "usage_limit", "settings_route"):
        if k not in inv:
            fails.append(f"LP-0 missing inventory: {k}")
    # LP-1 only intent actions trigger
    trig = set(s.get("triggers", []))
    if not trig.issubset({"premium_tap", "usage_limit"}):
        fails.append(f"LP-1 non-intent trigger present: {sorted(trig - {'premium_tap','usage_limit'})}")
    if not trig:
        fails.append("LP-1 no later trigger defined")
    # LP-2 same offering, visible close, no deeper discount
    if s.get("same_offering") is not True: fails.append("LP-2 offering differs from onboarding")
    if s.get("close_visible") is not True: fails.append("LP-2 close button not clearly visible")
    if s.get("later_discount_deeper") is True: fails.append("LP-2 later discount deeper than main")
    # LP-3 holdout + window >= 42 days + RPI primary
    if s.get("holdout") is not True: fails.append("LP-3 no holdout group")
    if int(s.get("judge_window_days", 0)) < 42: fails.append("LP-3 judge window <42d (misses week-6 late conversion)")
    if s.get("primary_metric") != "revenue_per_install": fails.append("LP-3 primary metric is not revenue_per_install")
    # LP-4 subscriber guard
    if s.get("hide_for_subscribers") is not True: fails.append("LP-4 paywall can show to subscribers")
    return fails

if __name__ == "__main__":
    with open(sys.argv[1]) as f: state = json.load(f)
    fails = check(state)
    if fails:
        print(f"FAIL {len(fails)}"); [print(" -", x) for x in fails]; sys.exit(1)
    print("PASS 0 fails"); sys.exit(0)
