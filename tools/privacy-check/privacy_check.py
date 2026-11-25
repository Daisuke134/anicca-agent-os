#!/usr/bin/env python3
"""privacy-check: deterministic gate checker for App Store privacy declarations
(privacy nutrition label in App Store Connect + PrivacyInfo.xcprivacy manifest
+ required-reason APIs + third-party SDK manifests). Stdlib only, offline, free.
Exit 0=PASS, 1=FAIL.

Sources (read in full 2026-11-14):
- Apple, "App Privacy Details" https://developer.apple.com/app-store/app-privacy-details/
  (you must identify ALL data you or your third-party partners collect; "collect"
  = transmitted off device and accessible longer than needed to service the
  request in real time; "third-party partners" = analytics tools, ad networks,
  third-party SDKs and other external vendors; optional disclosure only when ALL
  listed criteria hold; you are responsible for keeping answers accurate and up
  to date; tracking = linking app data with third-party data for targeted
  advertising / ad measurement, or sharing with a data broker; data processed
  only on device is not collected; a privacy policy URL is required)
- PocketApp, "Privacy manifest for iOS: what Apple requires in 2026"
  https://blog.pocketapp.co.uk/blog/privacy-manifest-ios
  (PrivacyInfo.xcprivacy declares tracking, tracking domains, collected data
  types and required-reason API categories with approved reason codes; since
  2024-05-01 new/updated apps must declare approved reasons; missing declaration
  = ITMS-91053 and the upload can be rejected; the five categories are file
  timestamps, system boot time, disk space, active keyboards, user defaults;
  use an approved reason only when it truly describes the use; fingerprinting
  is prohibited regardless of consent; you own every line of code you ship,
  including SDKs; keep an SDK register; Xcode aggregates SDK manifests into a
  privacy report that must be reconciled with the label; re-check on every SDK
  add/upgrade; mismatch between manifest, label and privacy notice is the
  first inconsistency a reviewer notices)
Reason codes / purposes below are the Apple-documented values corroborated by
the kxbuild tutorial and theswift.dev audit retrieved 2026-11-14; the checker
validates membership in these documented sets, it does not invent codes.
Vendor lift/compliance claims are NOT encoded as expectations.
"""
import json, sys

APPROVED_REASONS = {
    "NSPrivacyAccessedAPICategoryUserDefaults": {"CA92.1", "1C8F.1"},
    "NSPrivacyAccessedAPICategoryFileTimestamp": {"C617.1", "DDA9.1", "3B52.1", "0A2A.1"},
    "NSPrivacyAccessedAPICategorySystemBootTime": {"35F9.1", "8FFB.1", "3D61.1"},
    "NSPrivacyAccessedAPICategoryDiskSpace": {"E174.1", "85F4.1", "7D9E.1", "B728.1"},
    "NSPrivacyAccessedAPICategoryActiveKeyboards": {"54BD.1", "3EC4.1"},
}
ALLOWED_PURPOSES = {
    "NSPrivacyCollectedDataTypePurposeThirdPartyAdvertising",
    "NSPrivacyCollectedDataTypePurposeDeveloperAdvertising",
    "NSPrivacyCollectedDataTypePurposeAnalytics",
    "NSPrivacyCollectedDataTypePurposeProductPersonalization",
    "NSPrivacyCollectedDataTypePurposeAppFunctionality",
    "NSPrivacyCollectedDataTypePurposeOther",
}

def main():
    if len(sys.argv) < 2:
        print("usage: privacy_check.py <state.json>"); return 2
    s = json.load(open(sys.argv[1]))
    fails, warns = [], []
    def req(c, g, m):
        if not c: fails.append(f"{g}: {m}")
    def warn(c, g, m):
        if not c: warns.append(f"{g}: {m}")

    inv = s.get("inventory") or {}
    man = s.get("manifest")  # None when no manifest exists
    label = s.get("label") or {}
    rec = s.get("reconciliations") or {}
    proc = s.get("release_process") or {}
    sdks = inv.get("sdk_register") or []

    # PVY-0 inventory & manifest existence
    req(inv.get("manifest_present_in_source") is True, "PVY-0",
        "no PrivacyInfo.xcprivacy found in the app source (a missing manifest is unmeasured, not compliant)")
    req(inv.get("manifest_in_bundle_verified") is True, "PVY-0",
        "manifest presence inside the built .app/.ipa is not verified (source presence alone does not prove the shipped bundle carries it)")
    req(bool(sdks), "PVY-0", "SDK register is empty (every shipped dependency must be listed; you own all code in the app, including SDKs)")
    for sdk in sdks:
        req(bool(sdk.get("name")) and bool(sdk.get("version")) and bool(sdk.get("purpose")),
            "PVY-0", f"SDK register entry incomplete (name/version/purpose required): {sdk.get('name')}")
    req(inv.get("code_api_usage_checked") is True, "PVY-0",
        "own-code required-reason API usage was not inventoried (categories actually used must be known before declaring)")

    # PVY-1 required-reason APIs: every category used must be declared with an approved reason
    used = set(inv.get("code_api_categories_used") or [])
    declared = {}
    if man:
        for e in (man.get("accessed_api_types") or []):
            declared[e.get("category")] = e.get("reasons") or []
    for cat in sorted(used):
        req(cat in declared, "PVY-1",
            f"required-reason API category used in code but not declared in the manifest: {cat} (missing declaration = ITMS-91053 risk)")
        if cat in declared:
            req(len(declared[cat]) >= 1, "PVY-1", f"declared category has no approved reason code: {cat}")
    for cat, reasons in declared.items():
        req(cat in APPROVED_REASONS, "PVY-1", f"declared category is not one of Apple's five documented categories: {cat}")
        if cat in APPROVED_REASONS:
            for r in reasons:
                req(r in APPROVED_REASONS[cat], "PVY-1",
                    f"reason code is not an Apple-approved reason for {cat}: {r} (codes may not be invented or copied from unrelated uses)")
    req(s.get("fingerprinting_claimed") is not True, "PVY-1",
        "fingerprinting is prohibited regardless of user consent; no reason code legitimises it")

    # PVY-2 manifest collected data types: linked / tracking flags + at least one documented purpose each
    if man is None:
        req(False, "PVY-2", "no manifest exists, so collected data types are declared nowhere in machine-readable form")
    else:
        types = man.get("collected_data_types") or []
        req(len(types) >= 1 or s.get("collects_no_data") is True, "PVY-2",
            "manifest declares no collected data types and the app does not record a collects-no-data position")
        for t in types:
            req(t.get("linked") is not None and t.get("used_for_tracking") is not None,
                "PVY-2", f"collected type lacks linked / used-for-tracking flags: {t.get('type')}")
            ps = t.get("purposes") or []
            req(len(ps) >= 1, "PVY-2", f"collected type has no declared purpose: {t.get('type')}")
            for p in ps:
                req(p in ALLOWED_PURPOSES, "PVY-2", f"purpose is not an Apple-documented purpose value: {p}")

    # PVY-3 tracking consistency across manifest, label and the ATT determination
    label_track = label.get("track") or []
    if man is None:
        req(False, "PVY-3", "no manifest exists, so NSPrivacyTracking / tracking domains cannot be reconciled with the label")
    else:
        req((man.get("tracking") is True) == (len(label_track) > 0), "PVY-3",
            "manifest NSPrivacyTracking disagrees with the label's Data Used to Track You section (the three declarations - manifest, label, privacy notice - must say the same thing)")
        domains = man.get("tracking_domains") or []
        if man.get("tracking") is True:
            req(len(domains) >= 1, "PVY-3", "tracking is declared but NSPrivacyTrackingDomains is empty")
        else:
            req(len(domains) == 0, "PVY-3", "tracking domains are listed while tracking is declared false (domains may only be listed for tracking connections)")
    req(rec.get("tracking_determination_recorded") is True, "PVY-3",
        "no recorded tracking determination (whether any partner links app data with third-party data for advertising/measurement or shares it with a data broker) reconciles the label, the manifest and the SDK set")

    # PVY-4 label completeness against the shipped SDK reality
    req(label.get("published") is True, "PVY-4", "no published App Privacy label is recorded")
    req(label.get("privacy_policy_url_present") is True, "PVY-4",
        "privacy policy URL is missing (a publicly accessible privacy policy URL is required)")
    all_label = set(label_track) | set(label.get("linked") or []) | set(label.get("not_linked") or [])
    if inv.get("has_purchase_sdk") is True:
        req("Purchases" in all_label or rec.get("purchases_explained") is True, "PVY-4",
            "a purchase/subscription SDK is integrated but the label declares no Purchases type and no reconciliation explains why (purchase history handled by a third-party partner is still collected data)")
    if inv.get("has_analytics_sdk") is True:
        req("Usage Data" in all_label, "PVY-4",
            "an analytics SDK is integrated but the label declares no Usage Data type")
        req("Diagnostics" in all_label or rec.get("diagnostics_explained") is True, "PVY-4",
            "analytics/diagnostics collection is present but the label declares no Diagnostics type and no reconciliation explains why")
    req(label.get("details_recorded") is True, "PVY-4",
        "only the label's category summary is recorded; the per-type purposes / linked / tracking detail behind See Details is not recorded, so accuracy cannot be audited")

    # PVY-5 linkage consistency
    if "Identifiers" in (label.get("linked") or []) and "Usage Data" in (label.get("not_linked") or []) and inv.get("has_analytics_sdk") is True:
        req(rec.get("usage_linkage_explained") is True, "PVY-5",
            "label links Identifiers to the user but claims Usage Data is not linked while analytics SDKs bind the two; without a recorded de-identification justification this reads as inconsistent (data is not linked only when linkage is stripped before collection and never re-linked)")

    # PVY-6 SDK manifests & signatures
    for sdk in sdks:
        if sdk.get("on_apple_privacy_impacting_list") is True:
            req(sdk.get("sdk_manifest_present") is True, "PVY-6",
                f"SDK on Apple's privacy-impacting list has no verified own privacy manifest: {sdk.get('name')} (an SDK may not rely on the app's manifest to declare its API use)")
        if sdk.get("on_apple_privacy_impacting_list") is None:
            warn(False, "PVY-6", f"whether this SDK is on Apple's privacy-impacting list is unrecorded: {sdk.get('name')}")

    # PVY-7 living process
    req(proc.get("recheck_on_sdk_change") is True, "PVY-7",
        "no release rule re-checks the manifest when an SDK is added or upgraded (the manifest is a living file, not set-and-forget)")
    req(proc.get("privacy_report_generated") is True, "PVY-7",
        "no Xcode privacy report was generated and reconciled for the current release (the aggregated report is how the label is checked against the SDK manifests)")
    req(proc.get("network_traffic_verified") is True, "PVY-7",
        "actual network traffic was never verified against the declarations (a manifest describes what you believe happens; key journeys must be observed)")
    days = label.get("reconciled_days_ago")
    req(days is not None, "PVY-7", "label reconciliation date is unrecorded (answers must be kept accurate and up to date)")
    if isinstance(days, (int, float)):
        warn(days <= 90, "PVY-7", f"label was last reconciled {days} days ago (>90 days)")

    for f in fails: print(f"FAIL {f}")
    for w in warns: print(f"WARN {w}")
    print(f"privacy-check: {len(fails)} fails, {len(warns)} warns")
    if fails:
        print("RESULT: FAIL"); return 1
    print("RESULT: PASS"); return 0

if __name__ == "__main__":
    sys.exit(main())
