#!/usr/bin/env python3
"""app-intents-check: deterministic gate for iOS App Intents / App Shortcuts.
Stdlib only, offline, free. Sources (full read 2026-11-14):
- Apple Developer Docs, Adopting App Intents to support system experiences
  https://apple-docs.everest.mt/docs/appintents/adopting-app-intents-to-support-system-experiences/
  App Intents is the common foundation for Siri, Spotlight, Shortcuts,
  Action button, controls and widgets: intents are the verbs (core
  actions), entities are the nouns (core content). One shared definition
  serves the app and its extensions. Entities donated via IndexedEntity +
  CSSearchableIndex.indexAppEntities become findable in Spotlight.
  An intent's perform() must do the work and return a result/dialog.
- Apple WWDC, Bring your app's core features to users with App Intents /
  Get to know App Intents: App Shortcuts are provided through a single
  AppShortcutsProvider, are available as soon as the app is installed
  with no setup, and surface in Spotlight, Siri, Shortcuts and the
  Action button. A shortcut is an intent plus phrases, a title and an
  image; phrases are what a person says or types to Siri.
- Apple Newsroom, Top apps make everyday tasks even easier with Siri
  Shortcuts https://www.apple.com/newsroom/2018/10/top-apps-make-everyday-tasks-even-easier-with-siri-shortcuts/
  Winner form in this niche: Headspace / 10% Happier expose exactly one
  core action -- instantly start a meditation for any time of day --
  via Siri, suggested on the Lock screen and in Search.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
"""
import json, sys

def check(d):
    fails, warns = [], []
    def fail(g, msg): fails.append(f"{g} {msg}")
    def warn(g, msg): warns.append(f"{g} {msg}")

    # AI-0 recorded state + lawful end-state decision
    if d.get("recorded") is not True:
        fail("AI-0", "App Intents state not recorded (intents, provider, phrases, controls and shipped template text must be read together, not assumed)")
    decision = d.get("decision")
    if decision not in ("ship_real", "remove_template"):
        fail("AI-0", f"no lawful end-state decision recorded (decision={decision!r}): either ship a real core-action intent or remove the template intent/control -- template-only is not an end state")
    if d.get("template_only") is True and decision != "remove_template":
        fail("AI-0", "the only AppIntent in the tree is an untouched Xcode template (a timer example): the system surfaces advertise a feature the product does not have")
    if decision == "remove_template":
        if d.get("template_removed") is not True:
            fail("AI-0", "decision is 'remove_template' but template intent/control code is still in the bundle")
        if d.get("measurement", {}).get("decision_recorded_with_reason") is not True:
            fail("AI-7", "removal decision is not recorded with its reason (the next builder will re-add the template)")
        return fails, warns
    if decision != "ship_real":
        # no decision: still evaluate what was recorded so the count is honest
        pass

    # AI-1 core action is real and perform() does it
    core = d.get("core_intent", {})
    if core.get("exists") is not True:
        fail("AI-1", "no app intent exposes the app's core action (for Anicca: start today's affirmation / listening session -- the action the product exists for)")
    if core.get("perform_does_real_work") is not True:
        fail("AI-1", "core intent perform() does no real work (an empty stub returning .result() is a promise the system makes and the app breaks)")
    if core.get("title_names_real_action") is not True:
        fail("AI-1", "intent title does not name the real core action (a template title such as 'Start a timer' describes someone else's app)")
    if core.get("description_names_real_action") is not True:
        fail("AI-1", "intent/control description does not describe the real action (template text such as 'an example control' ships to users and reviewers)")

    # AI-2 single provider, available at install, phrases
    prov = d.get("provider", {})
    if prov.get("exists") is not True:
        fail("AI-2", "no AppShortcutsProvider: no App Shortcut is available at install, in Siri, Spotlight, Shortcuts or the Action button")
    n = prov.get("shortcut_count") or 0
    if n < 1:
        fail("AI-2", f"shortcut_count={n}: zero App Shortcuts shipped")
    if n > 10:
        fail("AI-2", f"shortcut_count={n} exceeds the App Shortcuts limit of 10")
    if prov.get("single_provider") is not True and prov.get("exists") is True:
        fail("AI-2", "shortcuts are not provided through a single AppShortcutsProvider (Apple: define a single provider containing all App Shortcuts)")
    phrases = prov.get("phrases") or []
    if prov.get("exists") is True and not phrases:
        fail("AI-2", "provider ships no phrases: a person cannot invoke the shortcut by speaking or typing to Siri")
    for p in phrases:
        if "app_name" not in p:
            fail("AI-2", f"phrase set {p!r} does not include the app-name token: Siri phrases must carry the app name placeholder so the system can attribute the request")
    if prov.get("each_shortcut_has_title_and_image") is not True and prov.get("exists") is True:
        fail("AI-2", "not every App Shortcut has a title and a system image (a shortcut is an intent plus phrases, a title and an image)")

    # AI-3 legacy-only path
    if d.get("legacy_sirikit_only") is True:
        fail("AI-3", "discoverability relies on legacy SiriKit / donation only: Apple documents SiriKit as legacy support; modern Siri, Spotlight and Apple Intelligence run on App Intents")

    # AI-4 result / dialog / landing
    r = d.get("result", {})
    if core.get("exists") is True and r.get("returns_dialog_or_value") is not True and r.get("opens_relevant_screen") is not True:
        fail("AI-4", "perform() returns neither a dialog/value with the real content nor opens the relevant in-app screen (for Anicca the dialog/value should carry today's line, or open today's session)")
    if r.get("opens_generic_home") is True:
        fail("AI-4", "intent lands on a generic home screen instead of the relevant screen for the action invoked")

    # AI-5 entity / Spotlight indexing (only a failure when searchability is claimed)
    ent = d.get("entity", {})
    if ent.get("searchability_claimed") is True:
        if ent.get("indexed_entity") is not True:
            fail("AI-5", "content searchability is claimed but no entity conforms to IndexedEntity")
        if ent.get("donated_to_spotlight") is not True:
            fail("AI-5", "entities are never donated to the Spotlight index (CSSearchableIndex.indexAppEntities): content cannot be found in Spotlight")
        if ent.get("stable_ids") is not True:
            fail("AI-5", "entity IDs are not stable across devices (Siri cannot resolve the same entity across devices)")
    else:
        if ent.get("indexed_entity") is not True:
            warn("AI-5", "no IndexedEntity: app content (today's line, saved lines) is not findable in Spotlight -- acceptable only if searchability is explicitly not claimed")

    # AI-6 control, if shipped, must control a real feature with real state
    ctl = d.get("control", {})
    if ctl.get("shipped") is True:
        if ctl.get("controls_real_feature") is not True:
            fail("AI-6", "shipped Control Center control does not control a real feature of the app (a template timer toggle in Control Center is a false surface)")
        if ctl.get("current_value_reads_real_state") is not True:
            fail("AI-6", "control provider currentValue does not read real state (a hardcoded value lies to Control Center about whether the feature is running)")
        if ctl.get("action_perform_does_real_work") is not True:
            fail("AI-6", "control's action intent perform() does no real work")

    # AI-8..AI-12 Apple Intelligence layer (extension 2026-11-21).
    # Sources (full read 2026-11-21): Apple WWDC26-240 "Build intelligent
    # Siri experiences with App Schemas" (apple-docs.everest.mt) and
    # WWDC26-343 "Explore advanced App Intents features for Siri and Apple
    # Intelligence" (wwdcnotes.com). The `intelligence` section is optional:
    # absent = WARN (unknown, not a pass); present-but-wrong = FAIL.
    intel = d.get("intelligence")
    if intel is None:
        for g in ("AI-8", "AI-9", "AI-10", "AI-11", "AI-12"):
            warn(g, "intelligence section not recorded: unknown, not a pass")
    else:
        # AI-8 app schemas + semantic resolution
        if intel.get("schema_domain_available") is True and intel.get("core_uses_app_schema") is not True:
            fail("AI-8", "an App Schema domain exists for the core action but the intent is custom-only: Siri cannot reason about or execute an action it has no schema contract for")
        res = intel.get("resolution")
        if res not in ("indexed_semantic", "string_query_with_reason"):
            fail("AI-8", f"entity resolution is {res!r}: the primary path is IndexedEntity semantic indexing; EntityStringQuery is lawful only with the infeasibility reason recorded")
        if res == "string_query_with_reason" and intel.get("string_query_reason_recorded") is not True:
            fail("AI-8", "string-query resolution claimed but the reason indexing is infeasible is not recorded")
        if res == "indexed_semantic" and intel.get("indexing_key_properties_recorded") is not True:
            fail("AI-8", "IndexedEntity adopted but the indexingKey properties (which fields are semantically searchable) are not recorded")
        # AI-9 onscreen awareness
        if intel.get("onscreen_annotation") not in ("user_activity", "view_annotation", "collection_annotation"):
            fail("AI-9", "the primary screen is not annotated for onscreen awareness (userActivity for one primary item, view/collection appEntityIdentifier for many): Siri cannot resolve 'this' on screen")
        if intel.get("persistent_identifiers") is not True:
            fail("AI-9", "onscreen entity identifiers are not persistent stable internal IDs: a view-derived or per-launch identifier makes two sightings of the same content different entities")
        if intel.get("transient_entities_for_integrations") is True:
            fail("AI-9", "TransientAppEntity is used for notification/now-playing/alarm integrations: the source states these cannot use transient entities because the persistent identifier is missing")
        if intel.get("fast_display_representations") is not True:
            fail("AI-9", "entity query does not serve fast displayRepresentations honoring requestedComponents: slow resolution makes Siri ask for clarification or give up")
        # AI-10 donations + responses
        if intel.get("donates_on_real_use") is not True:
            fail("AI-10", "core-action use is not donated via IntentDonationManager with parameters and result: Siri cannot learn when this person actually wants the action")
        if intel.get("donation_excessive") is True:
            fail("AI-10", "donations are excessive: the system may ignore donations fired too often, so donation must ride real use, not a timer or a loop")
        if intel.get("dialog_names_outcome") is not True:
            fail("AI-10", "perform() returns no ProvidesDialog dialog naming what actually happened (the result must say the real outcome, e.g. today's line started, not a generic success)")
        if intel.get("clarification_via_request_value") is not True:
            warn("AI-10", "missing optional values are not clarified via requestValue: an ambiguous Siri request fails instead of asking one question")
        # AI-11 ownership / confirmation honesty
        if intel.get("entities_default_private") is not True:
            fail("AI-11", "entities are not private by default: Siri's default assumption is private, and widening it is a disclosure decision, not a default")
        if intel.get("personal_content_marked_public") is True:
            fail("AI-11", "personal content (a person's intervention lines, reactions, history) is marked public via OwnershipProvidingEntity: ownership conformance is only for genuinely public/shared entities, never to skip confirmation")
        if intel.get("uses_ownership_conformance") is True and intel.get("ownership_only_for_public_shared") is not True:
            fail("AI-11", "OwnershipProvidingEntity is used but not restricted to genuinely public/shared entities with a real ownership state")
        # AI-12 cross-surface annotation
        if intel.get("notifications_annotated_with_entity_ids") is not True:
            fail("AI-12", "notifications carry no appEntityIdentifiers: Siri cannot act on 'this' notification, which for a notification-native product is the main surface left unconnected")
        if intel.get("search_in_app_intent") is not True:
            fail("AI-12", "no .system.searchInApp intent re-runs a Siri search inside the app: a system search that cannot continue in-app dead-ends")

    # AI-7 measurement
    m = d.get("measurement", {})
    for k, label in [("invocations", "intent invocations"), ("system_originated_sessions", "Siri/Spotlight/Shortcut-originated sessions"), ("completion", "invocation-to-session completion"), ("retention_vs_control", "retention read against a control (invokers are not a random sample)")]:
        if m.get(k) is not True:
            fail("AI-7", f"not measured: {label}")
    return fails, warns

def main():
    if len(sys.argv) != 2:
        print("usage: app_intents_check.py <state.json>"); return 2
    with open(sys.argv[1]) as f: d = json.load(f)
    fails, warns = check(d)
    for x in fails: print("FAIL", x)
    for x in warns: print("WARN", x)
    print(f"{'PASS' if not fails else 'FAIL'} {len(fails)} fail(s) {len(warns)} warn(s)")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
