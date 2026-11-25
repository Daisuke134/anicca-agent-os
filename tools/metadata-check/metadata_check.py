#!/usr/bin/env python3
"""metadata-check: deterministic gate checker for App Store search metadata.
Reads a JSON description of an app's store metadata (per locale) and judges
gates MD-0..MD-7. Stdlib only, offline, no API keys. Exit 0 = PASS, 1 = FAIL.

Rules are taken from sources read in full on 2026-11-14:
- AppScreenshotStudio, "App Store App Name, Subtitle, Keywords: 30/30/100 (2026)"
  https://appscreenshotstudio.com/blog/app-store-metadata-for-indie-devs-title-subtitle-keywords-2026
  (title 30 chars strongest weight, subtitle 30 second, keyword field 100;
   description is NOT indexed; no word repeated across the three fields;
   keyword field comma-separated with no spaces, single words, no plurals,
   no "app"/"free"/category words; title form Brand: Primary Keyword;
   promo text 170, conversion only; each locale is a fresh 160-char budget;
   measure ranks weekly, review metadata every 90 days)
- ScreenFast, "App Store Listing Optimization Checklist (2026)"
  https://screenfast.app/blog/app-store-listing-optimization-checklist
  (keyword field is a 100-BYTE budget in Apple's field reference;
   keywords longer than 2 characters; no duplicating app/company name;
   no other apps' or companies' names in the keyword field)
Winner benchmark measured live 2026-11-14 from the public store pages:
  I am (874656917) US title "I am - Daily Affirmations", subtitle
  "Positive widgets & motivation", 14 languages.
"""
import json, re, sys

BANNED = {"app", "apps", "free", "best", "new", "#1", "sale", "cheap"}
STOP = {"the", "a", "an", "and", "&", "-", ":", "for", "to", "of"}

def words(text):
    if not text:
        return []
    toks = re.split(r"[^a-z0-9']+", text.lower())
    return [t for t in toks if t and t not in STOP]

def main():
    if len(sys.argv) < 2:
        print("usage: metadata_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f:
        s = json.load(f)
    fails, warns = [], []
    def req(cond, gate, msg):
        if not cond: fails.append(f"{gate}: {msg}")
    def warn(cond, gate, msg):
        if not cond: warns.append(f"{gate}: {msg}")

    locales = s.get("locales", [])
    # MD-0 every locale's three fields recorded (keyword field included)
    req(len(locales) >= 1, "MD-0", "no locales recorded")
    for loc in locales:
        name = loc.get("locale", "?")
        req(bool(loc.get("title")), "MD-0", f"{name}: title not recorded")
        req(bool(loc.get("subtitle")), "MD-0", f"{name}: subtitle not recorded")
        req(loc.get("keyword_field_recorded") is True, "MD-0",
            f"{name}: keyword field not recorded (it lives only in ASC; unrecorded = unmeasured, never assumed compliant)")
        # MD-1 limits: title/subtitle <=30 chars, keyword field <=100 UTF-8 bytes, promo <=170 chars
        req(len(loc.get("title") or "") <= 30, "MD-1", f"{name}: title {len(loc.get('title') or '')} chars > 30")
        req(len(loc.get("subtitle") or "") <= 30, "MD-1", f"{name}: subtitle {len(loc.get('subtitle') or '')} chars > 30")
        kw = loc.get("keyword_field") or ""
        if loc.get("keyword_field_recorded") is True:
            req(len(kw.encode("utf-8")) <= 100, "MD-1", f"{name}: keyword field {len(kw.encode('utf-8'))} bytes > 100")
        promo = loc.get("promo_text")
        if promo is not None:
            req(len(promo) <= 170, "MD-1", f"{name}: promo text {len(promo)} chars > 170")
        # MD-2 no word repeated across title / subtitle / keyword field
        tw, sw = words(loc.get("title")), words(loc.get("subtitle"))
        kw_words = [w.strip().lower() for w in kw.split(",")] if kw else []
        seen = {}
        for src, ws in (("title", tw), ("subtitle", sw), ("keyword_field", kw_words)):
            for w in ws:
                if w in seen and seen[w] != src:
                    fails.append(f"MD-2: {name}: word '{w}' appears in both {seen[w]} and {src} (repeated words buy no new eligibility)")
                seen.setdefault(w, src)
        # MD-3 keyword field format
        if loc.get("keyword_field_recorded") is True and kw:
            req(", " not in kw and not kw.startswith(" ") and not kw.endswith(" "),
                "MD-3", f"{name}: keyword field contains spaces (commas with no spaces; every space is a wasted byte)")
            for w in kw_words:
                req(len(w) > 2, "MD-3", f"{name}: keyword '{w}' is 2 chars or fewer (Apple minimum is >2)")
                req(w not in BANNED, "MD-3", f"{name}: keyword '{w}' is banned/redundant (app/free/category/promo words)")
                req(" " not in w, "MD-3", f"{name}: keyword '{w}' is a phrase (single words only; Apple recombines them)")
            brand = set(words(s.get("brand", "")))
            for w in kw_words:
                req(w not in brand, "MD-3", f"{name}: keyword '{w}' duplicates the brand/app name (already indexed from the title)")
            for comp in (s.get("competitor_names") or []):
                for w in words(comp):
                    req(w not in kw_words, "MD-3", f"{name}: keyword field contains competitor name word '{w}'")
        # MD-4 title form: brand + primary keyword phrase, separator, no banned promo words
        title = loc.get("title") or ""
        req(any(sep in title for sep in (":", "-", "–", "|")), "MD-4",
            f"{name}: title has no separator (winning form is Brand <sep> Primary Keyword so Apple can recombine the words)")
        req(bool(set(words(title)) & set(words(s.get("primary_keyword_phrase", "")))),
            "MD-4", f"{name}: title does not contain the primary keyword phrase")
        for w in words(title):
            req(w not in BANNED, "MD-4", f"{name}: title contains banned promo word '{w}'")
        # MD-5 subtitle form: adds words the title lacks (dup is MD-2), no banned words
        for w in words(loc.get("subtitle")):
            req(w not in BANNED, "MD-5", f"{name}: subtitle contains banned promo word '{w}'")
    # MD-6 locale multiplication vs winner benchmark
    bench = s.get("winner_locale_count")
    req(isinstance(bench, int) and bench > 0, "MD-6", "winner locale-count benchmark not recorded")
    if isinstance(bench, int) and bench > 0:
        warn(len(locales) >= bench, "MD-6",
             f"locales with recorded metadata = {len(locales)} vs winner benchmark {bench} (each missing locale is a fresh 160-char search budget left unused)")
    # MD-7 measurement cadence + description not treated as search surface
    m = s.get("measurement", {})
    req(m.get("rank_tracked_weekly") is True, "MD-7", "target-keyword ranks are not tracked weekly")
    req(m.get("review_cycle_days") is not None and m.get("review_cycle_days") <= 90, "MD-7",
        "metadata review cycle is not recorded or exceeds 90 days")
    req(m.get("description_treated_as_indexed") is not True, "MD-7",
        "plan treats the description as search-indexed (on iOS it is not; the search surface is title+subtitle+keywords = 160 chars)")

    print(f"locales={len(locales)}")
    for w in warns: print("WARN " + w)
    for f_ in fails: print("FAIL " + f_)
    print(f"result: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
