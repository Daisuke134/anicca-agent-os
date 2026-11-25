#!/usr/bin/env python3
"""keyword-field-check: deterministic gate for the App Store keyword field
(100 chars) + name/subtitle allocation per release. Stdlib only, offline.
Sources (read in full 2026-11-23):
- dev.to/ASOClimb summary of Apple's own guidance (checked vs Apple pages
  2026-11-01) https://dev.to/abhinayguptha/app-store-keyword-field-how-to-use-all-100-characters-flo
  100-char limit (ASC Help: up to 100 bytes; non-Latin counts differ, trust
  ASC), commas no spaces, never repeat name/subtitle/category words, no
  plurals of held words, no generic 'app'/category names, no filler, no
  special chars unless brand, no trademarks/competitor/irrelevant terms
  (improper keywords are a common rejection cause), promo text does NOT
  affect ranking, localize per market, field changes only with a version.
- Kwern worked example https://kwern.app/blog/app-store-keywords : a 94-char
  draft added ~0 new words; rewrite added 15. NOTE: Kwern asserts Apple
  assembles cross-field phrases; dev.to notes Apple does NOT document that
  combining. This gate follows the documented side: each word once, placed
  where it fits best; no plan may rest on undocumented combining.
Delimitation: metadata-check owns general metadata, cpp/ppo own page tests,
OwlASO owns keyword scoring. This gate owns only the per-release allocation
of the 160 indexed characters (name 30 + subtitle 30 + keywords 100).
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("fields_read_from_asc_per_release", "KF-0 the current name, subtitle and keyword field were not read verbatim from App Store Connect for this release (auditing from memory means the duplicates nobody remembers stay in)"),
    ("allocation_recorded_per_release", "KF-0 no per-release allocation record exists (which word sits in which field and why; the field is written once at first submission and never reopened in most listings)"),
    ("byte_length_verified_in_asc", "KF-0 length was not verified as ASC accepts it (guidance says 100 characters, ASC Help says up to 100 bytes; accented/non-Latin terms can overflow a plain character count)"),
    ("no_repeat_across_fields", "KF-1 a word is repeated across name/subtitle/keyword field/category (Apple indexes it once; every repeat burns characters that could carry new search intent)"),
    ("no_plural_duplicates", "KF-1 a plural sits next to its singular (Apple treats climb/climbs as duplicates; the second form earns nothing)"),
    ("no_generic_or_filler", "KF-1 generic or filler words remain ('app', category names, 'the'/'to', special characters without brand meaning: all named by Apple as waste)"),
    ("no_competitor_or_trademark", "KF-2 competitor names, unauthorized trademarks, celebrity or irrelevant popular terms are present (improper keywords are a documented rejection cause, and irrelevant traffic that does not convert teaches Apple the page fails that search)"),
    ("every_term_relevant_and_true", "KF-2 not every term describes a capability the app actually has (a term for a feature the app lacks is an outside/inside mismatch and a conversion tax)"),
    ("candidates_from_evidence", "KF-3 candidates did not come from evidence (search suggestions, Apple Ads search-terms report, review vocabulary, competitors' public descriptive words) but from internal terminology (users search in their words, not the team's)"),
    ("scored_by_popularity_difficulty_relevance", "KF-3 candidates were not scored on popularity, difficulty and relevance, with relevance as a hard filter (a small app chasing one broad term loses to making many reachable combinations possible)"),
    ("strongest_phrase_in_name", "KF-3 the strongest phrase is not placed in the app name and the next in a readable subtitle (the visible 60 characters are both indexed and read by every searcher; the hidden field is for what did not fit)"),
    ("single_words_preferred", "KF-4 phrases are used where single words would do (single words keep the field compact and auditable; multi-word phrases are kept only when the phrase itself is the searched unit, e.g. Apple's own 'Real Estate' example)"),
    ("no_spaces_after_commas", "KF-4 there are spaces after commas (each space is a character spent on nothing; over a full field they cost a word or two)"),
    ("field_near_full", "KF-4 the field is materially under-filled (under ~90 of 100 characters with scored candidates still unused means coverage was left on the table)"),
    ("localized_per_market", "KF-5 keywords are not localized per market (Apple recommends tailoring per market; one English field pasted into every storefront wastes the non-English storefronts)"),
    ("promo_text_not_used_for_keywords", "KF-5 promotional text is being used as keyword space (Apple states promo text does not affect search ranking; it is a conversion surface, editable without a version)"),
    ("change_batched_and_logged", "KF-5 the change is not batched with a planned release with the OLD field written down (the field only changes with a new version, so tries are scarce; an unlogged change can never be read)"),
    ("post_release_read_scheduled", "KF-5 no post-release read is scheduled (at least two weeks after go-live, search impressions/downloads vs the prior two weeks; impressions up with flat downloads = the words bring people the page does not convince)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__":
    main()
