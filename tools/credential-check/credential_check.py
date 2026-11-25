#!/usr/bin/env python3
"""credential-check: deterministic gate for the CREDENTIAL STORAGE surface
(where the app's own secrets live on the device: access tokens, refresh
tokens, and any other bearer material -- and what happens to them at
sign-out, deletion, migration and reinstall).
Stdlib only, offline, free.
Sources (read 2026-11-16):
- Apple "About Cryptographic Services" (Apple Developer Library archive)
  https://developer.apple.com/library/archive/documentation/Security/Conceptual/cryptoservices/Introduction/Introduction.html
  "Keychains Help You Store Secret Information: If your app stores
  encryption keys, passwords, certificates, and other security-related
  information, use a keychain. Keychains provide secure storage for
  small pieces of information so that it is not accessible by other
  apps running on the system, and so that it is accessible only after
  the user has logged in or unlocked the device."
- Apple Keychain Services reference (linked from the iOS secure-storage
  guide below): an encrypted key/value store designed to hold generic
  passwords, internet passwords, certificates, private keys and
  identities -- i.e. the system's designated place for secrets, as
  opposed to the defaults system, which is a preferences store.
- felixgr/secure-ios-app-dev "Where should I store my data on iOS?"
  (OWASP-aligned community guide, read via raw.githubusercontent.com)
  https://raw.githubusercontent.com/felixgr/secure-ios-app-dev/master/README.md
  Keychain Services is the encrypted store designed for passwords /
  tokens / keys; the defaults system and plain files are not.
- swift-ios-skills credential-storage reference (Tessl registry, read
  2026-11-16): "The iOS Keychain is the only Apple-sanctioned storage
  mechanism for OAuth tokens, API keys, passwords, and other
  credentials... Apple's documentation is explicit: the defaults
  system stores information on disk in an unencrypted format and must
  not be used for personal or sensitive information." Accessibility
  classes: WhenUnlockedThisDeviceOnly for foreground session tokens,
  AfterFirstUnlockThisDeviceOnly when background refresh must read
  the token after first unlock; the deprecated Always classes are
  never acceptable. Keychain items survive app deletion, so a stale
  item must be wiped on first launch after (re)install.
Exit 0 = PASS, 1 = FAIL.
Input JSON: {app,
 inventory:{inventory_recorded, classification_recorded,
   decision_recorded},
 placement:{access_token_in_keychain, refresh_token_in_keychain,
   no_secrets_in_userdefaults, no_secrets_in_app_group_defaults,
   no_secrets_in_plain_files_or_logs},
 keychain_quality:{generic_password_class_used,
   accessibility_class_explicit_and_restrictive,
   this_device_only_or_nonsynchronizable,
   single_keychain_wrapper},
 cleanup:{keychain_deleted_on_signout,
   keychain_deleted_on_account_deletion,
   keychain_deleted_on_revoke_or_reset},
 migration:{legacy_secrets_migrated_to_keychain,
   migration_verified_and_old_keys_removed},
 measurement:{storage_audit_recorded,
   token_logging_audit_recorded,
   reinstall_stale_item_handling_recorded}}
"""
import json, sys

def check(d):
    fails = []
    inv = d.get("inventory") or {}
    if not inv.get("inventory_recorded"):
        fails.append("CS-0 the credential inventory is not recorded (every bearer material the app holds -- access token, refresh token, any API credential -- enumerated with its storage location; an unenumerated secret is stored wherever the code that created it happened to put it)")
    if not inv.get("classification_recorded"):
        fails.append("CS-0 secrets are not classified apart from identifiers and preferences (a userId is an identifier, a JWT is a secret, a theme flag is a preference; unclassified, all three inherit the weakest store any of them uses)")
    if not inv.get("decision_recorded"):
        fails.append("CS-0 no storage decision is recorded per credential type (which store, which accessibility class, and why -- an unrecorded split, e.g. refresh token in Keychain but access token in defaults, reads as a design when it is an accident of two code paths written at different times)")
    pl = d.get("placement") or {}
    if not pl.get("access_token_in_keychain"):
        fails.append("CS-1 the access token is not stored in the Keychain (Apple: if your app stores security-related information, use a keychain; a bearer token in the defaults plist is readable from device backups and by anything with container access)")
    if not pl.get("refresh_token_in_keychain"):
        fails.append("CS-1 the refresh token is not stored in the Keychain (the longest-lived credential the app holds gets the strongest store, not the weakest; a refresh token outside the Keychain is a permanent session for whoever extracts it)")
    if not pl.get("no_secrets_in_userdefaults"):
        fails.append("CS-1 secrets are present in UserDefaults (the defaults system stores an unencrypted plist included in backups; any struct encoded there as JSON that contains a token field is a secret in plaintext, whatever the struct is named)")
    if not pl.get("no_secrets_in_app_group_defaults"):
        fails.append("CS-1 secrets are present in App Group shared defaults (the shared container is readable by every extension in the group; identifiers the extension needs are fine there, bearer material is not)")
    if not pl.get("no_secrets_in_plain_files_or_logs"):
        fails.append("CS-1 secrets are present in plain files or logs (a token written to a file or printed to a log leaves the Keychain's protection entirely; log output is collected, synced and read by tools the secret was never meant for)")
    kq = d.get("keychain_quality") or {}
    if not kq.get("generic_password_class_used"):
        fails.append("CS-2 Keychain items are not stored as generic-password items (kSecClassGenericPassword is the documented class for passwords and tokens; ad-hoc classes or raw file encryption re-implement what the system already provides)")
    if not kq.get("accessibility_class_explicit_and_restrictive"):
        fails.append("CS-2 the Keychain accessibility class is not explicit and restrictive (an unset class inherits a default nobody chose; the deprecated Always classes expose the item whenever the device has ever unlocked -- choose the most restrictive class the real flows tolerate, e.g. AfterFirstUnlock only where background refresh genuinely reads the token)")
    if not kq.get("this_device_only_or_nonsynchronizable"):
        fails.append("CS-2 items are not ThisDeviceOnly / non-synchronizable, and no decision records why (a synchronizable or backup-migrating refresh token silently copies the session to other devices and backups; if sync is a product decision it must be recorded as one)")
    if not kq.get("single_keychain_wrapper"):
        fails.append("CS-2 Keychain access is not funnelled through a single wrapper (SecItem calls scattered across the tree drift in class, accessibility and error handling; one wrapper is the only place the storage contract can be enforced and audited)")
    cl = d.get("cleanup") or {}
    if not cl.get("keychain_deleted_on_signout"):
        fails.append("CS-3 the Keychain credential is not deleted on sign-out (Keychain items survive what UserDefaults removal does not; a sign-out that clears defaults but leaves the refresh token has ended the session on screen and kept it alive in storage)")
    if not cl.get("keychain_deleted_on_account_deletion"):
        fails.append("CS-3 the Keychain credential is not deleted on account deletion (deletion that wipes defaults and profile but leaves a live refresh token in the Keychain has not deleted the account's means of access)")
    if not cl.get("keychain_deleted_on_revoke_or_reset"):
        fails.append("CS-3 the Keychain credential is not deleted when the credential is revoked or reset server-side (a token the server has killed must also die on the device; otherwise every launch retries a dead credential and the failure reads as a network problem)")
    mg = d.get("migration") or {}
    if not mg.get("legacy_secrets_migrated_to_keychain"):
        fails.append("CS-4 existing installs' legacy secrets are not migrated into the Keychain (fixing the store for new installs leaves every current device holding its token in the old plaintext location indefinitely; migration on first launch after update is part of the fix, not a follow-up)")
    if not mg.get("migration_verified_and_old_keys_removed"):
        fails.append("CS-4 the migration is not verified with the old keys removed (a copy that leaves the defaults key in place has two live copies of the secret, and the plaintext one is the one an extractor finds first)")
    ms = d.get("measurement") or {}
    if not ms.get("storage_audit_recorded"):
        fails.append("CS-5 no storage audit is recorded (a periodic grep-level audit -- token-shaped fields in defaults, files, logs -- is the only way the placement gates stay true after the next feature lands; unaudited, the surface regresses silently)")
    if not ms.get("token_logging_audit_recorded"):
        fails.append("CS-5 no token-logging audit is recorded (authorization headers, token values and refresh responses must be verified absent from logs and analytics; an unverified 'we never log tokens' is a hope, and analytics properties are the usual place they leak)")
    if not ms.get("reinstall_stale_item_handling_recorded"):
        fails.append("CS-5 the reinstall behaviour is not recorded (Keychain items survive app deletion on iOS; without a first-launch stale-item decision, a reinstalled app can resurrect a previous user's or a deleted account's refresh token)")
    return fails

def main():
    if len(sys.argv) != 2:
        print("usage: credential_check.py <state.json>")
        return 2
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    app = d.get("app", "?")
    if fails:
        print(f"FAIL {app}: {len(fails)} gate failures")
        for x in fails:
            print(" -", x)
        return 1
    print(f"PASS {app}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
