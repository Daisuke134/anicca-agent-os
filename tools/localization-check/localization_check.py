#!/usr/bin/env python3
"""localization-check: deterministic gate for the LOCALIZATION COMPLETENESS surface.
Stdlib only, offline, free.
Source (Apple Developer, string catalogs / localization):
- Every user-facing string needs a translation in every supported locale;
  a lookup that cannot find the requested localization returns the key
  itself, so a missing key can surface as a raw key in the interface.
- Xcode string catalogs track per-string state (new / needs review /
  translated) precisely so completeness is measurable before release.
The gate generalises the contract: supported locales are decided and
declared consistently, every table is complete in every locale, copied-
but-untranslated values are audited, missing-key fallback is the source
language (never the raw key), and completeness is measured for ALL
supported locales -- not only the two primary ones.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("supported_locales_recorded"): f.append("LC-0 supported locales are not recorded as a decision (which languages the app claims to speak is implicit in whichever .lproj folders happen to exist)")
    if not dec.get("localization_owner_recorded"): f.append("LC-0 no single localization owner is recorded")
    if not dec.get("source_locale_recorded"): f.append("LC-0 the source/development locale is not recorded (no agreed baseline that completeness is measured against)")
    cov=d.get("coverage") or {}
    if not cov.get("every_locale_complete_keys"): f.append("LC-1 not every supported locale has every source key (a locale missing half its keys is a partially-English/raw-key experience, not a supported language)")
    if not cov.get("extra_keys_triaged"): f.append("LC-1 keys present in a locale but absent from the source are not triaged (stale translations for deleted strings ship unexamined)")
    if not cov.get("all_tables_covered"): f.append("LC-1 not all string tables are complete in all locales (completeness claimed from one finished table hides an unfinished main table)")
    unt=d.get("untranslated") or {}
    if not unt.get("identical_to_source_audited"): f.append("LC-2 values identical to the source language are not audited per locale (a present key holding English text counts as translated in a key-count check)")
    if not unt.get("long_identical_zero_or_waived"): f.append("LC-2 long values identical to the source exist without a recorded waiver (full sentences in English inside a non-English locale are untranslated copies, not translations)")
    if not unt.get("placeholder_parity_checked"): f.append("LC-2 placeholder/format-specifier parity between source and translations is not checked (a dropped %@ can crash or corrupt a rendered string)")
    fb=d.get("fallback") or {}
    if not fb.get("missing_key_fallback_is_source_not_key"): f.append("LC-3 the missing-key fallback is not the source language (a lookup configured with value:key renders the raw key, e.g. 'notification_...', to the user)")
    if not fb.get("fallback_behavior_recorded"): f.append("LC-3 missing-key fallback behaviour is not recorded per lookup path (each call site invents its own degradation)")
    decl=d.get("declaration") or {}
    if not decl.get("declared_localizations_match_shipped"): f.append("LC-4 declared localizations do not match the shipped .lproj set (the bundle advertises a different language set than the resources and project regions claim)")
    if not decl.get("known_regions_match_resources"): f.append("LC-4 project knownRegions do not match the shipped .lproj folders")
    ver=d.get("verification") or {}
    if not ver.get("completeness_measured_in_ci"): f.append("LC-5 per-locale completeness (missing keys + identical values) is not measured in CI or a recorded gate (drift accumulates silently as source strings are added in two locales only)")
    if not ver.get("tests_cover_all_supported_locales"): f.append("LC-5 localization tests do not cover all supported locales (tests for EN/JA nudge keys only cannot see a German key that does not exist)")
    if not ver.get("per_locale_render_check_recorded"): f.append("LC-5 no per-locale render/screenshot check is recorded (truncation and raw keys in a real locale build are never looked at)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
