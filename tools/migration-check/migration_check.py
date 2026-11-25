#!/usr/bin/env python3
"""migration-check: deterministic gate for the LOCAL DATA MIGRATION /
PERSISTENCE surface (whether the user data already on the phone survives
the next app update: every persisted user-data store is inventoried and
its format decided, every user-data payload carries a schema version
with the shipped versions frozen and kept readable, step-up transforms
-- not just a range check that rejects -- move old payloads forward, a
decode failure is logged and the failed payload is preserved instead of
being silently replaced by an empty state and then overwritten by the
next save, a last-known-good / pre-change copy exists with a restore
path, the surfaces that share data (app / widget / extension) read one
format at one version, continuity across reinstall / device change is
decided rather than accidental, and migration is rehearsed with
per-version payload tests, a corruption rehearsal and record-count
preservation checks).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Touhidul Islam Rukon, Safe SwiftData Migrations: VersionedSchema and
  Backups (practitioner write-up of a shipped local-first app, SpenDrop)
  https://www.rukon.dev/blog/swiftdata-versioned-schema-migration-without-losing-data
  Freeze the shipped model as a VersionedSchema before changing it and
  never edit the frozen copy; an ordered SchemaMigrationPlan with
  lightweight / custom stages moves old stores forward; copy the store
  BEFORE opening it with a changed schema (decided from the store's own
  metadata, not only a cached fingerprint); a failed open NEVER deletes
  -- the app starts in safe mode on an in-memory store and leaves the
  files untouched; inferred migration can drop an unrecognised entity
  with no error, so test the case where migration "succeeds"; backups
  keep history (the backup you need is the one from before something
  disappeared) and refuse payloads written by a newer app version;
  rehearse every migration on copies of real stores and record
  record-count preservation.
- Apple UserDefaults documentation (via developer guidance summaries):
  the defaults system is a preferences store -- small key-value pairs
  loaded at launch; user content / records belong in a real store
  (SwiftData / Core Data / files), not in preferences blobs.
Distinct from the Synthetic User Data Gate (that governs WHAT the
synthetic record may contain) and the Credential Storage Gate (secrets
placement): this gate governs whether ANY locally persisted user data
survives version change, corruption and surface sharing.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("all_stores_inventoried_with_format_and_owner"):
        fails.append("LM-0 no inventory of persisted user-data stores exists (the tree holds 39 distinct defaults keys and 11 files decoding Codable blobs from defaults, but no record lists which stores hold user data, in what format, owned by whom -- a format change can be shipped without anyone knowing what it breaks)")
    if not inv.get("storage_technology_decision_recorded"):
        fails.append("LM-0 no storage-technology decision is recorded (SwiftData / Core Data / CloudKit appear zero times; all user data lives in UserDefaults JSON blobs and one JSONL file store by accumulation, not by a recorded decision with a migration story)")
    if not inv.get("user_data_separated_from_preferences"):
        fails.append("LM-0 user content is not separated from preferences (memories the user wrote, liked quotes, the synthetic-user conditioning record and nudge history are all Codable blobs inside the preferences defaults -- the store Apple reserves for small settings -- so every launch loads user records as preferences and no store-level tooling applies to them)")
    ver = d.get("versioning") or {}
    if not ver.get("every_userdata_payload_carries_schema_version"):
        fails.append("LM-1 not every user-data payload carries a schema version (exactly one store, SyntheticUser, has schemaVersion; Memory, LikedQuotes, DailyAffirmation, NudgeStats, CustomHabit and the personalisation profile blobs have none -- their format can change in any release with no way to even detect old data)")
    if not ver.get("shipped_versions_frozen_and_kept_readable"):
        fails.append("LM-1 shipped payload versions are not frozen and kept readable (no frozen copy of any shipped format exists; readability of old data depends on today's Codable structs happening to stay decode-compatible)")
    if not ver.get("step_up_transforms_exist_for_versioned_stores"):
        fails.append("LM-1 no step-up transform moves old payloads forward (SyntheticUser.load only range-checks 1...current and returns nil outside it -- v1 reads today only because the added field is optional; the first required-field change turns every existing synthetic user into a silent nil, and a newer payload read by an older build is discarded the same way; only the DecisionPointRecorder JSONL store has a real legacy transform)")
    fai = d.get("failure_behaviour") or {}
    if not fai.get("decode_failure_logged_or_measured"):
        fails.append("LM-2 decode failures are not logged or measured (store after store decodes with try? and falls back to an empty state with no Logger call and no analytics event on the failure path -- a format break in the field is indistinguishable from users simply having no data)")
    if not fai.get("failed_payload_preserved_not_overwritten"):
        fails.append("LM-2 a failed payload is not preserved (there is no quarantine, backup key or move-aside anywhere in the tree -- the in-memory empty state is written back over the same single key on the next save, making the loss permanent and unrecoverable)")
    if not fai.get("safe_mode_or_recovery_path_exists"):
        fails.append("LM-2 there is no safe mode or recovery path (when a payload cannot be read the app proceeds as a fresh user -- re-onboarding over an existing person -- instead of leaving the data untouched and offering restore; the one recovery-shaped behaviour, reselecting today's affirmation, works only because that datum is disposable)")
    bak = d.get("backup") or {}
    if not bak.get("last_known_good_or_pre_change_copy_taken"):
        fails.append("LM-3 no last-known-good or pre-change copy is taken (every store keeps exactly one copy under one key; nothing snapshots data before an overwrite, a version change or a migration -- the copy you need is the one from before something disappeared, and it is never made)")
    if not bak.get("restore_path_exists"):
        fails.append("LM-3 no restore path exists (no import/restore code path reads a preserved copy back; even if a user or support somehow obtained the old payload, the app has no way to take it)")
    if not bak.get("newer_version_payload_handled_without_loss"):
        fails.append("LM-3 a payload written by a newer version is not handled without loss (SyntheticUser.load returns nil for a future schemaVersion and refresh() then builds and saves a fresh record over it -- a downgrade, a TestFlight switch or a staged rollout straddling two versions silently resets the conditioning record and its intervention history)")
    con = d.get("continuity") or {}
    if not con.get("shared_surfaces_read_one_format_version"):
        fails.append("LM-4 the surfaces that share data do not provably read one format at one version (app, widget and notification-service share an App Group suite, but the shared payloads carry no version, so a format change in one target can break the others with no detection)")
    if not con.get("reinstall_device_change_continuity_decided"):
        fails.append("LM-4 continuity across reinstall / device change is not decided (CloudKit / iCloud key-value sync appear zero times and no record states whether the synthetic user, memories and likes are server-backed, synced, or deliberately local-only -- today they are local-only by accident, so a new phone restarts personalisation from zero)")
    if not con.get("deletion_clears_every_store_and_surface"):
        fails.append("LM-4 account deletion is not verified to clear every store and surface (deletion code exists in AppState, but no check enumerates all 39 keys, the App Group suite and the JSONL files against it -- an unlisted store survives deletion silently)")
    tst = d.get("verification") or {}
    if not tst.get("per_version_payload_migration_tests"):
        fails.append("LM-5 per-version payload tests do not cover the persisted surface (SyntheticUser has v1/v2/reject tests, but the other blob stores -- memories, likes, nudge stats, habits, profile -- have no old-payload tests at all, so their next format change ships unrehearsed)")
    if not tst.get("corruption_rehearsal_exists"):
        fails.append("LM-5 no corruption rehearsal exists (no test feeds a truncated or corrupted payload to any store and asserts the data survives or is preserved -- the dangerous case is untested, and the silent-drop case, where decode 'succeeds' into an empty state, is untested too)")
    if not tst.get("record_count_preservation_checked"):
        fails.append("LM-5 record-count preservation is not checked (no migration or load test asserts counts before/after -- 23 records in, 23 records out -- so a partial silent drop would pass every existing test)")
    return fails

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        data = json.load(f)
    failures = check(data)
    if failures:
        print(f"FAIL ({len(failures)}):")
        for x in failures:
            print(" -", x)
        sys.exit(1)
    print("PASS")
