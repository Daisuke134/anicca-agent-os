#!/usr/bin/env python3
"""export-rights-check: deterministic gate for EXPORT COMPLIANCE + CONTENT RIGHTS.
Stdlib only, offline, free.
Sources (read in full 2026-11-22):
- Newly, App Store Export Compliance (Apple docs read 2026-10-03)
  https://newly.app/how-to/app-store-export-compliance
  HTTPS is encryption; the plist question is NON-EXEMPT encryption.
  ITSAppUsesNonExemptEncryption=NO claims no encryption or only exempt
  encryption across the WHOLE binary incl. third-party libraries linked.
  OS-provided encryption (URLSession HTTPS) is typically exempt. Three cases:
  OS-only = no documents; standard algorithm OS does not provide = French
  declaration if distributing in France; proprietary/not standards-accepted
  = US CCATS + French declaration. Middle case has no published plist value:
  answer in App Store Connect, never copy a tutorial value. Cleared documents
  return ITSEncryptionExportComplianceCode. Without the key ASC asks every
  version; a build without an answer is Missing Compliance (also blocks
  external TestFlight). Clearing needs Account Holder/Admin/App Manager.
  Complete documents clear in ~2 business days; set description+availability
  before uploading documents. Exempt use may still require a year-end BIS
  self-classification report. Google Play asks no questionnaire but takes a
  one-time US export-laws acknowledgement at app creation.
- Newly, App Store Content Rights Question (Apple docs read 2026-10-21)
  https://newly.app/how-to/app-store-content-rights-question
  Content Rights is a required App Information field with exactly two API
  values: DOES_NOT_USE_THIRD_PARTY_CONTENT / USES_THIRD_PARTY_CONTENT.
  Scope verbs: contain, show, access -- per country/region law. Nothing is
  uploaded at declaration time; Guideline 5.2.2/5.2.3 require authorization
  to be provided UPON REQUEST (during review or months after launch).
  5.2.1: submitter must own or have licensed the IP; no protected third-party
  material / misleading copycat names or metadata without permission.
  5.2.3: no save/convert/download of media from third-party sources without
  explicit authorization. 5.2.4: no implied Apple endorsement. 5.2.5: no
  confusingly similar Apple product/interface, no Apple emoji in apps,
  extensions, keyboards or sticker packs. Keep a per-item provenance list
  (font/image/feed/sound + who permitted it) reachable within a day;
  unprovable content is removed before answering.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    ec=d.get("export_classification") or {}
    if not ec.get("dependency_inventory_incl_libraries"): f.append("ER-0 no dependency inventory including third-party libraries (the exemption claim covers the whole binary, not only first-party code -- a crypto library three levels down changes the answer)")
    if not ec.get("strongest_crypto_case_determined"): f.append("ER-0 the strongest cryptography in the binary is not classified into Apple's three cases (OS-only / standard-not-in-OS / proprietary) -- picking by the app's own code alone misclassifies bundled libraries")
    if not ec.get("determination_own_not_copied"): f.append("ER-0 the determination is not recorded as the team's own (Apple publishes no plist value for the middle standard-algorithm case and puts liability for a wrong exemption claim on the developer; copying a tutorial value is an unsigned legal statement)")
    if not ec.get("https_read_as_encryption_but_exempt"): f.append("ER-0 HTTPS is not read correctly (HTTPS use IS encryption use, and OS-provided HTTPS is typically EXEMPT -- answering 'no encryption' or panicking into non-exempt paperwork are both wrong)")
    pl=d.get("plist_declaration") or {}
    if not pl.get("plist_key_set_before_first_upload"): f.append("ER-1 ITSAppUsesNonExemptEncryption is not set in Info.plist before first upload (without it App Store Connect asks on every version and builds sit at Missing Compliance, blocking review and external TestFlight)")
    if not pl.get("plist_value_matches_case"): f.append("ER-1 the plist value is not verified to match the classified case (NO = no encryption or only exempt encryption incl. libraries; YES = non-exempt; a value that contradicts the inventory is a false declaration)")
    if not pl.get("middle_case_answered_in_asc_not_copied"): f.append("ER-1 the middle case (standard algorithm from a bundled library) is not handled by answering in App Store Connect (Apple publishes documents for it but no plist value, so any copied value is invented)")
    if not pl.get("compliance_code_key_recorded_when_cleared"): f.append("ER-1 ITSEncryptionExportComplianceCode handling is not recorded (when Apple clears submitted documents it returns a code that belongs in this second key; losing it reopens the document flow)")
    doc=d.get("documents_timing") or {}
    if not doc.get("france_distribution_checked"): f.append("ER-2 France distribution is not checked (a standard or proprietary algorithm plus distribution in France requires a French encryption declaration even when the US side is settled)")
    if not doc.get("ccats_required_only_for_proprietary"): f.append("ER-2 CCATS handling is not recorded (proprietary / not-standards-accepted encryption needs a US CCATS classification; OS-only and standard cases do not -- filing it needlessly or skipping it when required both stall release)")
    if not doc.get("two_business_day_buffer_and_prereqs"): f.append("ER-2 no ~2-business-day document-clearing buffer with prerequisites (Apple expects about two business days for complete documents, and description + availability must be set before uploading them or sufficiency cannot be judged)")
    if not doc.get("year_end_self_classification_considered"): f.append("ER-2 the year-end self-classification report is not considered (exempt encryption can still require a year-end BIS report; 'exempt from Apple documents' is not 'exempt from all filing')")
    if not doc.get("play_export_acknowledgement_recorded"): f.append("ER-2 the Google Play export position is not recorded (Play asks no questionnaire but takes a one-time US export-laws acknowledgement at app creation and leaves the determination to the developer -- 'Play asked nothing' is not compliance)")
    cr=d.get("content_inventory") or {}
    if not cr.get("third_party_inventory_contain_show_access"): f.append("ER-3 no third-party content inventory across contain / show / access (a bundled sound, a rendered logo and an API call to someone else's service are all in scope; unlisted items make the declaration a guess)")
    if not cr.get("permission_reachable_within_a_day_per_item"): f.append("ER-3 per-item permission is not held somewhere reachable within a day (5.2.2/5.2.3: authorization must be provided upon request -- during review or months after launch; a permission that takes a week to reconstruct is effectively absent)")
    if not cr.get("unprovable_content_removed_before_answering"): f.append("ER-3 unprovable content is not removed before answering (the honest move for an item with no reachable permission is removal before declaration, not declaring and hoping no request arrives)")
    dec=d.get("content_declaration") or {}
    if not dec.get("declaration_value_matches_inventory"): f.append("ER-4 the Content Rights declaration is not set to the value matching the inventory (exactly two values exist -- DOES_NOT_USE_THIRD_PARTY_CONTENT / USES_THIRD_PARTY_CONTENT -- and the field is required; a 'no' with third-party fonts/feeds/sounds in the app is false)")
    if not dec.get("submitter_owns_or_licenses_ip"): f.append("ER-4 the submitter-owns-or-licenses rule is not verified (5.2.1: apps should be submitted by the person/legal entity that owns or has licensed the IP and other relevant rights -- a client/partner brand shipped from the wrong account is itself a 5.2.1 rejection)")
    if not dec.get("no_misleading_trademark_or_copycat_metadata"): f.append("ER-4 trademarks / copycat names and metadata are not checked (5.2.1 also bars misleading, false or copycat representations, names or metadata in the bundle or developer name, not only in-app content)")
    sub=d.get("guideline_52_subrules") or {}
    if not sub.get("service_terms_permission_522"): f.append("ER-5 third-party service terms permission is not verified (5.2.2: use/access/monetize/display of a service's content must be specifically permitted under that service's terms, with authorization producible on request)")
    if not sub.get("no_media_download_without_auth_523"): f.append("ER-5 media save/convert/download is not checked against 5.2.3 (no saving, converting or downloading media from sources like Apple Music/YouTube/SoundCloud/Vimeo without explicit authorization; streaming access must also be checked against terms)")
    if not sub.get("no_apple_endorsement_or_emoji_524_525"): f.append("ER-5 Apple endorsement / Apple-product rules are not checked (5.2.4: never imply Apple supplies or endorses the app, Editor's Choice badges are Apple's to apply; 5.2.5: no confusingly similar Apple product/interface and no Apple emoji in apps, extensions, keyboards or sticker packs)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
