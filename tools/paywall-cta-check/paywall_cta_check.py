#!/usr/bin/env python3
"""Deterministic paywall CTA / trust-adjacency checker (stdlib only, free, offline).
Gates from Morphic 7-pattern synthesis of Superwall 4,500+ A/B tests / Adapty 2026:
 C-1 CTA baseline is a low-commitment word (default: Continue); a CTA that names the
     financial commitment (subscribe/buy/unlock/start trial...) fails the baseline check.
 C-2 At least one trust signal (cancel_anytime / trial_timeline / social_proof) sits
     adjacent_below_cta (within one element of the CTA). Header-only placement fails.
 C-3 Price must stay prominent (Apple 3.1.2 / RevenueDot rule): price_prominent must be true.
Usage: paywall_cta_check.py <paywall.json>  -> prints JSON verdict, exit 0 if all pass else 1
"""
import json, sys
COMMITMENT_WORDS = ("subscribe", "buy", "purchase", "unlock", "start my", "start trial", "pay now", "get premium", "go premium")
TRUST_TYPES = {"cancel_anytime", "trial_timeline", "social_proof"}
def check(p):
    cta = (p.get("cta_text") or "").strip().lower()
    c1 = cta == "continue" or not any(w in cta for w in COMMITMENT_WORDS)
    # baseline requires exactly the low-commitment form; non-Continue generic words are flagged as warn via c1_strict
    c1_strict = cta == "continue"
    sigs = p.get("trust_signals") or []
    adjacent = [s for s in sigs if s.get("type") in TRUST_TYPES and s.get("position") == "adjacent_below_cta"]
    c2 = len(adjacent) >= 1
    c3 = p.get("price_prominent") is True
    return {"C-1_cta_no_commitment_wording": c1, "C-1b_cta_is_continue_baseline": c1_strict,
            "C-2_trust_adjacent_below_cta": c2, "C-3_price_prominent": c3,
            "pass": bool(c1 and c2 and c3)}
if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    v = check(data)
    print(json.dumps(v, indent=2))
    sys.exit(0 if v["pass"] else 1)
