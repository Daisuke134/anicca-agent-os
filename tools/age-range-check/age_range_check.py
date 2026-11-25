#!/usr/bin/env python3
"""age-range-check: deterministic gate for the DECLARED AGE RANGE / AGE ASSURANCE surface.
Stdlib only, offline, free.
Source (Apple Developer):
- "Requesting people's age range information in your app" (Declared Age Range):
  https://developer.apple.com/documentation/declaredagerange
  The app supplies up to three age gates (>=2 years apart); the system returns
  a range (lowerBound/upperBound), never an exact birthdate. Requires the
  com.apple.developer.declared-age-range entitlement. In nonregulated regions
  sharing can be declined (declinedSharing); responses are cached and only
  re-prompted on the anniversary of the original declaration.
- "Age assurance frameworks Q&A" https://developer.apple.com/support/age-assurance
  isEligibleForAgeFeatures (iOS 26.2+) says whether age assurance is legally
  required for this person/region; requiredRegulatoryFeatures (iOS 26.4+)
  says which obligations apply. Full frameworks require building against the
  iOS 26.2 SDK (Xcode 26.2+). PermissionKit covers parental consent for
  significant app changes; a change in the app's age rating is itself treated
  as a significant change in regulated regions.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("age_gates_recorded"): f.append("AR-0 the app's age gates (up to three thresholds, >=2 years apart, e.g. 13/16/18) are not recorded as a decision - which ages matter to this app is undecided")
    if not dec.get("age_owner_recorded"): f.append("AR-0 no single age-assurance owner is recorded")
    if not dec.get("adoption_decision_recorded"): f.append("AR-0 no recorded decision on whether Declared Age Range is adopted or deferred with a reason - the surface is absent by drift, not by decision")
    if not dec.get("age_rating_consistency_recorded"): f.append("AR-0 the App Store age rating and the in-app age gates have not been checked against each other as a recorded decision (a rating change is itself a significant change in regulated regions)")
    ent=d.get("entitlement") or {}
    if not ent.get("entitlement_present_all_targets"): f.append("AR-1 com.apple.developer.declared-age-range entitlement is not present on the app targets (without it requestAgeRange cannot run)")
    if not ent.get("sdk26_build_decision_recorded"): f.append("AR-1 no recorded build decision for the iOS 26.2+ SDK that the age-assurance frameworks require (Xcode 26.2+) - the app cannot reach these APIs by accident")
    if not ent.get("availability_guard_for_pre_ios26"): f.append("AR-1 no availability guard / recorded fallback for people below iOS 26 (the API simply does not exist there, so the unguarded path is a crash or a silent skip)")
    eli=d.get("eligibility") or {}
    if not eli.get("is_eligible_checked"): f.append("AR-2 AgeRangeService.isEligibleForAgeFeatures is never checked - the app cannot know whether this person is in a region that legally requires age assurance")
    if not eli.get("required_regulatory_features_read"): f.append("AR-2 requiredRegulatoryFeatures is never read - even an eligible person gets no distinction between obligations (declared range vs significant-change consent vs adult notification)")
    if not eli.get("declined_sharing_handled"): f.append("AR-2 declinedSharing has no recorded handling (in nonregulated regions people may decline; in some regulated regions they cannot - one code path for both is wrong)")
    req=d.get("request") or {}
    if not req.get("request_implemented"): f.append("AR-3 requestAgeRange is not implemented (no DeclaredAgeRange import, no AgeRangeService call anywhere in the tree)")
    if not req.get("response_drives_experience"): f.append("AR-3 the returned age range does not drive any age-appropriate routing (a minor and an adult receive the identical experience, so collecting the range would be decoration)")
    if not req.get("no_exact_birthdate_for_age_assurance"): f.append("AR-3 age is derived from a stored exact birthdate instead of the system-declared range (the API exists precisely so the birthdate never has to be collected or kept for this purpose)")
    if not req.get("cached_response_respected"): f.append("AR-3 the system's cached-response / anniversary behaviour is not respected in the design (re-prompting or re-asking in-app defeats the privacy design and trains people to dismiss it)")
    sig=d.get("significant_change") or {}
    if not sig.get("significant_update_acknowledgement_wired"): f.append("AR-4 significant-update acknowledgement / PermissionKit consent is not wired (regulated regions require parental consent or adult notification for significant app changes)")
    if not sig.get("minor_consent_routing_recorded"): f.append("AR-4 no recorded routing for a declared minor (consent path, restricted experience, or block) - the minor case is discovered in production, not designed")
    ver=d.get("verification") or {}
    if not ver.get("e2e_cases_tested"): f.append("AR-5 the three response cases (minor / adult / declinedSharing) plus the eligible-region case are not end-to-end tested")
    if not ver.get("age_metrics_measured"): f.append("AR-5 age-feature outcomes are not measured (eligible count, shared vs declined, minor routing) - no way to know whether the surface works or is silently skipped")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
