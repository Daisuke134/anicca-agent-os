#!/usr/bin/env python3
"""Deterministic gate for App Store in-app-purchase / subscription display names.

Source: indie-aso (2026-10-27) "Your In-App Purchase Names Are Searchable"
https://indieaso.icedtealabs.com/blog/app-store-in-app-purchase-names-subscription-keywords
- Apple indexes IAP display names as searchable text (helper signal, not a main lever).
- Display name <= 30 chars, short description <= 45 chars.
- Name it like a feature, not a tier ("Pro" -> "Unlimited Habit Tracking").
- Words must come from user language (reviews), not be invented.
- Do not repeat title/subtitle words only: Apple combines fields, repetition adds nothing.
  At least one NEW content word is required.
- Accurate, natural on a purchase sheet, no stuffing, no superlative/claim words,
  no competitor brand names.
- Promote only 1-2 items; record rename date + target phrases and change no other
  metadata for ~2 weeks so the effect can be read.

Input JSON:
{
  "app": "Anicca",
  "title": "Daily Affirmations - Anicca",
  "subtitle": "Positive widgets & motivation",
  "competitor_brands": ["i am", "monkey taps"],
  "promoted_count": 0,               // null / missing = unmeasured (warning)
  "measurement_plan_recorded": false,
  "items": [
    {"name": "Annual Premium", "description": "", "accuracy_attested": false}
  ]
}
Gates per item: I-1 length, I-2 feature-not-tier, I-3 novelty vs title/subtitle,
I-4 no stuffing/claims/brands, I-5 accuracy attestation (warning if missing).
App-level: I-6 promoted count / measurement plan (warnings if unmeasured).
Exit 1 if any FAIL, else 0. Warnings never pass a FAIL.
"""
import json, re, sys

TIER = {"premium","pro","weekly","monthly","annual","yearly","lifetime","plan","retention",
        "month","year","week","day","days","months","years","weeks","subscription","subs",
        "gold","plus","basic","standard","offer","deal","1","2","3","6","12"}
STOP = {"the","a","an","for","with","and","&","-","(",")","of","to","in","on"}
BANNED = {"best","top","free","cheapest","guaranteed","no1","#1","ultimate","perfect"}

def tokens(s):
    return [t for t in re.split(r"[^a-z0-9\-]+", (s or "").lower()) if t]

def stem(t):
    return t[:-1] if t.endswith("s") and len(t) > 3 else t

def main():
    data = json.load(open(sys.argv[1]))
    title_words = {stem(t) for t in tokens(data.get("title",""))} | {stem(t) for t in tokens(data.get("subtitle",""))}
    brands = [b.lower() for b in data.get("competitor_brands", [])]
    fails, warns = [], []
    for it in data.get("items", []):
        name = it.get("name","")
        desc = it.get("description","") or ""
        toks = tokens(name)
        content = [t for t in toks if t not in TIER and t not in STOP and t not in {stem(x) for x in []}]
        # brand names of the app itself count as tier-like (no job content)
        app_words = {stem(t) for t in tokens(data.get("app",""))}
        content = [t for t in content if stem(t) not in app_words]
        if len(name) > 30:
            fails.append(f"I-1 '{name}': name {len(name)} chars > 30")
        if len(desc) > 45:
            fails.append(f"I-1 '{name}': description {len(desc)} chars > 45")
        if not content:
            fails.append(f"I-2 '{name}': tier/brand-only name, zero job/feature words")
        novel = [t for t in content if stem(t) not in title_words]
        if content and not novel:
            fails.append(f"I-3 '{name}': every content word already in title/subtitle {sorted(title_words)}")
        low = name.lower()
        if {stem(t) for t in toks} & BANNED:
            fails.append(f"I-4 '{name}': contains banned claim word")
        if any(b in low for b in brands):
            fails.append(f"I-4 '{name}': contains competitor brand")
        if len(toks) > 6:
            fails.append(f"I-4 '{name}': {len(toks)} words > 6 (stuffing risk)")
        if not it.get("accuracy_attested"):
            warns.append(f"I-5 '{name}': accuracy not attested (name must describe what the purchase actually gives)")
    pc = data.get("promoted_count")
    if pc is None:
        warns.append("I-6 promoted_count unmeasured (promote only 1-2 items)")
    elif pc == 0 or pc > 2:
        fails.append(f"I-6 promoted_count={pc}: promote exactly 1-2 items")
    if not data.get("measurement_plan_recorded"):
        warns.append("I-6 measurement plan not recorded (rename date + target phrases, no other metadata change for ~2 weeks)")
    for w in warns: print("WARN", w)
    for f in fails: print("FAIL", f)
    print(f"items={len(data.get('items',[]))} fails={len(fails)} warns={len(warns)} verdict={'FAIL' if fails else 'PASS'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
