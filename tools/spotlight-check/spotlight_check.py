#!/usr/bin/env python3
"""spotlight-check: deterministic gate for Spotlight / Siri Suggestions discoverability.
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Apple, App Search Programming Guide (archive)
  https://apple-docs.everest.mt/docs/apple-archive/documentation/General/Conceptual/AppSearch/
  All apps should use NSUserActivity; Core Spotlight indexes persistent
  content without a visit; view frequency is captured ONLY through
  NSUserActivity and drives ranking; index only items users are most
  likely to search for; keep indexes up to date (remove/update); minimise
  time from tapping a result to viewing the content.
- Nil Coalescing, Core Spotlight integration
  https://www.nilcoalescing.com/blog/CoreSpotlightIntegration/
  CSSearchableItem + attribute set (title/thumbnail), named index,
  onContinueUserActivity(CSSearchableItemActionType) -> identifier ->
  navigate to the exact item; client-state batching avoids re-indexing
  every launch; lastUsedDate + isUpdate re-donation feeds ranking;
  Apple recommends a reindexing extension (CSIndexExtensionRequestHandler).
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, indexable_content:[]},
 core_spotlight:{implemented, attribute_fields:[], stable_unique_ids},
 user_activity:{donated_at_viewing, eligible_for_search, eligible_for_prediction, become_current},
 continuation:{handles_searchable_item_action, lands_on_specific_content},
 freshness:{updates_or_deletes_on_change, ranking_signal_fed, reindex_handler_present},
 scope:{only_likely_searched, personal_content_publicly_indexed},
 measurement:{spotlight_event_defined, spotlight_event_fired, joinable_to_completion}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("SP-0 Spotlight discoverability is not inventoried (which content is indexable, which surface donates it, and whether the layer exists at all are nowhere recorded; an unrecorded free discovery surface cannot be audited)")
    if not (inv.get("indexable_content") or []):
        fails.append("SP-0 no indexable content is identified (the app holds persistent, searchable content -- saved/liked affirmations and habits -- yet none of it is named as indexable; content nobody names is content the system can never surface)")
    cs = d.get("core_spotlight") or {}
    if not cs.get("implemented"):
        fails.append("SP-1 Core Spotlight indexing is not implemented (CSSearchableItem / CSSearchableIndex hits are zero; persistent content that a user has not opened recently can never appear in Spotlight, because unlike NSUserActivity, Core Spotlight is the only route that indexes content without a visit)")
    else:
        fields = set(cs.get("attribute_fields") or [])
        missing = {"title", "content_description", "keywords"} - fields
        if missing:
            fails.append(f"SP-1 attribute sets are missing {sorted(missing)} (title is what displays, content_description and keywords are what matching and semantic search run on; an item without them is indexed in name only)")
        if not cs.get("stable_unique_ids"):
            fails.append("SP-1 searchable items have no stable unique identifiers (continuation and update/delete both key on the identifier; unstable ids orphan results and duplicate entries)")
    ua = d.get("user_activity") or {}
    if not ua.get("donated_at_viewing"):
        fails.append("SP-2 no NSUserActivity is donated when content is viewed (Apple: all apps should use NSUserActivity, and view frequency -- the ranking signal -- is captured ONLY through it; without donation there is no Siri Suggestion and no ranking input, however good the content is)")
    else:
        if not ua.get("eligible_for_search"):
            fails.append("SP-2 donated activities are not eligibleForSearch (the activity exists but is never offered to the on-device search index)")
        if not ua.get("eligible_for_prediction"):
            fails.append("SP-2 donated activities are not eligibleForPrediction (no proactive Siri Suggestions on the Lock Screen / in Search -- the free re-engagement surface is switched off)")
        if not ua.get("become_current"):
            warns.append("SP-2 donated activities never becomeCurrent() (donation without activation is weaker; warning only, justification should be recorded)")
    ct = d.get("continuation") or {}
    if not ct.get("handles_searchable_item_action"):
        fails.append("SP-3 taps on Spotlight results are not handled (no CSSearchableItemActionType continuation; by default the app just launches to its initial page, breaking the promise the result made)")
    if not ct.get("lands_on_specific_content"):
        fails.append("SP-3 a Spotlight tap does not land on the specific content shown (Apple: minimise the time between tapping a result and viewing the content; a generic launch is a dropout step at the exact moment of highest intent)")
    fr = d.get("freshness") or {}
    if cs.get("implemented") or ua.get("donated_at_viewing"):
        if not fr.get("updates_or_deletes_on_change"):
            fails.append("SP-4 the index is never updated or deleted when content changes (stale results for deleted/unliked content teach the system -- and the user -- that the app's results are wrong; Apple: keep the indexes up to date)")
        if not fr.get("ranking_signal_fed"):
            fails.append("SP-4 no ranking signal is fed back (no lastUsedDate/isUpdate re-donation and no NSUserActivity view frequency; engagement is what ranking runs on, so un-fed results sink)")
        if not fr.get("reindex_handler_present"):
            warns.append("SP-4 no reindex handler/extension is present (Apple recommends one so a lost or corrupted index can be rebuilt while the app is not running; warning only)")
    sc = d.get("scope") or {}
    if sc.get("personal_content_publicly_indexed"):
        fails.append("SP-5 personal content is marked eligible for PUBLIC indexing (private affirmations, problems and habits belong in the private on-device index only; public indexing of personal content is a privacy failure, not a growth tactic)")
    if (cs.get("implemented") or ua.get("donated_at_viewing")) and not sc.get("only_likely_searched"):
        fails.append("SP-5 indexing is not limited to items users are most likely to search for (Apple's explicit guidance; indexing everything dilutes relevance and performance)")
    ms = d.get("measurement") or {}
    if ms.get("spotlight_event_defined") and not ms.get("spotlight_event_fired"):
        fails.append("SP-6 the Spotlight-arrival event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'Spotlight brings nobody' forever)")
    if not ms.get("spotlight_event_defined"):
        fails.append("SP-6 no Spotlight / user-activity arrival event exists at all (the system reports nothing back; without the app's own arrival event, a free discovery surface's contribution is unknowable in principle)")
    if not ms.get("joinable_to_completion"):
        fails.append("SP-6 Spotlight arrivals cannot be joined to downstream completion (session / habit / purchase), so whether search-driven re-engagement works cannot be judged")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
