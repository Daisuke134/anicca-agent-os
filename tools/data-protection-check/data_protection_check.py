#!/usr/bin/env python3
"""data-protection-check: deterministic gate for the DATA PROTECTION AT REST surface.
Stdlib only, offline, free.
Source (read 2026-11-16): Apple Developer, "Encrypting Your App's Files"
https://developer.apple.com/documentation/uikit/encrypting-your-app-s-files
- Data protection encrypts files on disk; four classes: none (always accessible),
  completeUntilFirstUserAuthentication (the DEFAULT when no class is specified),
  completeUnlessOpen, complete (accessible only while unlocked).
- Set protection at creation via Data.write(to:options:) with e.g. .completeFileProtection,
  or on existing files via NSURL.setResourceValue(URLFileProtection, forKey: .fileProtectionKey).
- Files containing personal information about the user, or created directly by the user,
  always deserve the strongest level (complete); manage access with
  applicationProtectedDataWillBecomeUnavailable / DidBecomeAvailable.
- Files a background feature may touch need a class compatible with locked access;
  complete is only for files accessed while the app is in the foreground.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("on_disk_stores_inventoried"): f.append("DP-0 on-disk stores are not inventoried in one record (a store nobody listed is a store nobody protected)")
    if not dec.get("protection_owner_recorded"): f.append("DP-0 no single data-protection owner is recorded")
    if not dec.get("sensitivity_classified"): f.append("DP-0 stores are not classified by sensitivity (which stores hold user-created / personal data is not recorded, so no class choice can follow from it)")
    cls=d.get("class_assignment") or {}
    if not cls.get("user_created_files_assigned_complete"): f.append("DP-1 user-created / personal files are not assigned the complete class (Apple: such files always deserve the strongest level)")
    if not cls.get("default_reliance_decided"): f.append("DP-1 reliance on the system default (completeUntilFirstUserAuthentication) is not a recorded decision (every file silently inherits it)")
    if not cls.get("default_protection_entitlement_decided"): f.append("DP-1 the default-data-protection entitlement decision is not recorded (the app-wide default class is whatever the absence of the entitlement happens to mean)")
    if not cls.get("no_none_class_for_user_data"): f.append("DP-1 the none class (always accessible) is in reach of user data")
    wrt=d.get("writes") or {}
    if not wrt.get("writes_pass_protection_option"): f.append("DP-2 file writes do not pass a data-protection option (a write with only .atomic inherits the default class by accident, not by decision)")
    if not wrt.get("existing_files_reclassed"): f.append("DP-2 existing on-disk files are not reclassed (setResourceValue / fileProtectionKey) — a class chosen today does not reach files already on users' devices")
    if not wrt.get("directory_protection_for_new_files"): f.append("DP-2 no directory-level protection is set, so future files created by new code paths again inherit the undecided default")
    lif=d.get("lifecycle") or {}
    if not lif.get("protected_data_delegate_handled"): f.append("DP-3 applicationProtectedDataWillBecomeUnavailable / DidBecomeAvailable are not handled (complete-class files are not closed/reopened around lock, so access fails unpredictably)")
    if not lif.get("background_access_files_class_compatible"): f.append("DP-3 files touched by background work or extensions have no recorded class compatible with locked access (complete on a background-touched file breaks the feature; the default on a sensitive file weakens it)")
    if not lif.get("locked_access_failures_handled"): f.append("DP-3 locked-device access failures are not handled or logged as a distinct case (a protection failure reads as generic data loss)")
    spc=d.get("special_stores") or {}
    if not spc.get("shared_container_classified"): f.append("DP-4 the app-group shared container's files are not classified or assigned (the widget / notification extension read a store whose protection nobody decided)")
    if not spc.get("defaults_held_user_content_decided"): f.append("DP-4 user content held in UserDefaults has no recorded protection decision (defaults files inherit the default class; holding user records there makes that inheritance the de-facto policy)")
    if not spc.get("extension_read_paths_considered"): f.append("DP-4 extension read paths (widget / notification service) are not checked against the chosen classes (an extension that cannot open a locked file fails silently on the lock screen)")
    ver=d.get("verification") or {}
    if not ver.get("locked_device_test_recorded"): f.append("DP-5 no locked-device / before-first-unlock test is recorded (the one state where classes actually differ is the one state never exercised)")
    if not ver.get("protection_attributes_read_back"): f.append("DP-5 protection attributes are never read back on real files (the assigned class is asserted by the writing code, never verified on disk)")
    if not ver.get("protection_failures_measured"): f.append("DP-5 protection-related access failures are not measured (there is no number for how often the lock state costs the user their data path)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
