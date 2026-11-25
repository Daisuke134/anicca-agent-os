#!/usr/bin/env python3
"""account-deletion-check: deterministic gate for the in-app account
deletion surface required of every app that supports account creation.
Stdlib only, offline, free.
Sources (read 2026-11-15):
- Apple App Review Guideline reference 5.1.1(v), "Offering account
  deletion in your app" (primary, developer.apple.com/help/app-review/
  guideline-reference/5-1-1-account-deletion): apps that support
  account creation must let people initiate deletion within the app;
  deleting removes the account from the developer's records along with
  associated data the developer is not legally required to maintain;
  the option must be easy to find (typically account settings);
  offering only temporary deactivation/disable is insufficient; if a
  website finishes the process, link directly to that page; apps
  outside highly regulated industries must not require a phone call,
  email or support flow; reauthentication/confirmation steps are
  allowed; deletion need not be instantaneous but its timeframe must
  be transparent; for Sign in with Apple apps, use the Sign in with
  Apple REST API to revoke the user's tokens when the account is
  deleted; deleting the account does not cancel an auto-renewable
  subscription, so point people to subscription management.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{account_creation_surface_recorded, deletion_decision_recorded,
   deletion_scope_defined},
 entry:{delete_option_in_account_settings, display_condition_used_by_view,
   localized_strings_referenced},
 server:{client_calls_delete_endpoint, server_deletion_evidenced,
   local_wipe_not_sole_mechanism},
 apple:{token_revocation_evidenced, keychain_refresh_token_removed_on_delete,
   credential_state_checked_on_launch},
 honesty:{confirmation_with_irreversible_warning,
   no_support_contact_required, subscription_consequence_disclosed,
   sign_out_not_presented_as_deletion},
 completion:{wipe_sequenced_after_server_success,
   deletion_events_counted, completion_confirmed_to_user}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("account_creation_surface_recorded"):
        fails.append("AD-0 the account-creation surface is not recorded (which sign-in creates a server account, and where -- an unrecorded creation surface makes the deletion obligation itself unauditable)")
    if not inv.get("deletion_decision_recorded"):
        fails.append("AD-0 no recorded deletion decision exists (the honest states are 'deletion is offered in-app and removes the server record' or an explicit recorded reason the app creates no account -- a code comment on a local wipe is not a decision)")
    if not inv.get("deletion_scope_defined"):
        fails.append("AD-0 the deletion scope is not defined in one place (account record, profile/synthetic-user data, tokens, on-device stores, and what is legally retained -- undefined scope means 'deleted' has no testable meaning)")
    en = d.get("entry") or {}
    if not en.get("delete_option_in_account_settings"):
        fails.append("AD-1 there is no delete-account option in account settings (Apple: the option must be easy to find, typically in account settings; a settings sheet offering only sign-out does not initiate deletion)")
    if not en.get("display_condition_used_by_view"):
        fails.append("AD-1 the signed-in display condition for the delete option is not used by any view (a tested helper that no screen calls is a dead gate: the option is shown to no one)")
    if not en.get("localized_strings_referenced"):
        fails.append("AD-1 the delete-account localized strings are not referenced by any code (translated copy sitting in .strings files with zero references is a label for a button that does not exist)")
    sv = d.get("server") or {}
    if not sv.get("client_calls_delete_endpoint"):
        fails.append("AD-2 the client never calls a backend account-deletion endpoint (no delete URL in the app's endpoint config; signing out and wiping UserDefaults leaves the server account record -- the thing 5.1.1(v) requires removing -- fully intact)")
    if not sv.get("server_deletion_evidenced"):
        fails.append("AD-2 server-side removal of the account record and associated personal data is not evidenced (a server outside the audited source stays unverified until its deletion handler is read; an unevidenced deletion is an assumed deletion)")
    if not sv.get("local_wipe_not_sole_mechanism"):
        fails.append("AD-2 the local wipe is the sole deletion mechanism (resetting on-device state is the last step of deletion, never the whole of it; presented alone it makes 'delete' a synonym for 'sign out and forget locally')")
    ap = d.get("apple") or {}
    if not ap.get("token_revocation_evidenced"):
        fails.append("AD-3 Sign in with Apple token revocation at deletion is not evidenced (Apple requires revoking the user's tokens via the Sign in with Apple REST API when an account created with it is deleted; zero revocation code means the Apple-side credential outlives the 'deleted' account)")
    if not ap.get("keychain_refresh_token_removed_on_delete"):
        fails.append("AD-3 the stored refresh token is not removed on deletion/sign-out (a refresh token left in the Keychain after 'deletion' can silently resurrect a session for an account the person believes is gone)")
    if not ap.get("credential_state_checked_on_launch"):
        fails.append("AD-3 the Apple credential state is not checked on launch (without getCredentialState, an account revoked or deleted on another device keeps presenting as signed in here)")
    ho = d.get("honesty") or {}
    if not ho.get("confirmation_with_irreversible_warning"):
        fails.append("AD-4 there is no wired confirmation step carrying the irreversible warning (Apple allows confirmation/reauthentication steps; the warning copy existing only as unreferenced strings confirms nothing to anyone)")
    if not ho.get("no_support_contact_required"):
        fails.append("AD-4 deletion requires a support contact (apps outside highly regulated industries must not require a phone call, email or chat/support flow to delete an account)")
    if not ho.get("subscription_consequence_disclosed"):
        fails.append("AD-4 the subscription consequence is not disclosed at deletion (deleting the account does not cancel an auto-renewable subscription; without telling the person and pointing to subscription management, 'deleted' users keep being charged)")
    if not ho.get("sign_out_not_presented_as_deletion"):
        fails.append("AD-4 sign-out or deactivation is presented as deletion (Apple: only offering to deactivate/disable is insufficient, and sign-out ends a session while the account and its data remain)")
    co = d.get("completion") or {}
    if not co.get("wipe_sequenced_after_server_success"):
        fails.append("AD-5 the local wipe is not sequenced after a confirmed server deletion (a wipe function with zero callers, and no server call to sequence after, means the completion path does not exist as a path)")
    if not co.get("deletion_events_counted"):
        fails.append("AD-5 deletion initiated/completed is not counted (initiations, server confirmations and failures are the only way to know the surface works; without them a broken deletion path looks identical to an unused one)")
    if not co.get("completion_confirmed_to_user"):
        fails.append("AD-5 completion (or its timeframe) is not confirmed to the user (deletion need not be instantaneous, but Apple requires the process to be transparent -- the person must learn that it finished, or when it will)")
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
