#!/usr/bin/env python3
"""aasa-check: deterministic gate for iOS Universal Links (Associated Domains / AASA).
Stdlib only, offline, free. Source (read in full 2026-11-14 via live browser):
Apple Developer Documentation, "Supporting associated domains"
https://developer.apple.com/documentation/xcode/supporting-associated-domains
Rules taken from that page only:
- AASA file named apple-app-site-association (no extension) in /.well-known/,
  served over https with a valid certificate and NO redirects.
- applinks appIDs format: <Application Identifier Prefix>.<Bundle Identifier>
- details applies only to applinks; components is an array of pattern dicts
  ("/" path, "?" query, "#" fragment, "exclude": true opts a URL out).
- App must carry a matching Associated Domains Entitlement:
  <service>:<fully qualified domain> — FQDN only, no path/query/trailing slash.
- Apps listed in the AASA must have a matching entitlement (pairing both ways).
- Since iOS 14/macOS 11 the file is fetched via Apple CDN (within 24h);
  devices re-check about weekly after install.
NOT from that page (deliberately not gated): Content-Type and 128KB size claims
appear in third-party write-ups but were not on the page read; recorded as warnings only.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app, domain, expected_app_id,
 live_check:{recorded, checked_on, wellknown_status, root_status, redirected},
 aasa:{served, valid_json, applinks_app_ids:[], has_components, all_excluded},
 entitlement_domains:[], handler:{handles_browsing_web, routes_to_specific_screen},
 fallback:{unmatched_opens_web}, measurement:{ul_taps_event, runbook_notes_cdn_timing},
 aasa_content_type, aasa_size_kb}
"""
import json, sys

def check(d):
    fails, warns = [], []
    lc = d.get("live_check") or {}
    if not lc.get("recorded"):
        fails.append("UL-0 no live check of the AASA URLs recorded (a link layer that is never fetched live is assumed, not measured)")
    if lc.get("redirected"):
        fails.append("UL-1 AASA is served with a redirect (Apple: host with https, valid certificate, and no redirects)")
    a = d.get("aasa") or {}
    if lc.get("wellknown_status") != 200:
        fails.append(f"UL-1 /.well-known/apple-app-site-association returns {lc.get('wellknown_status')!r}, not 200 (file must exist, extensionless, in .well-known)")
    if not a.get("served") or not a.get("valid_json"):
        fails.append("UL-1 AASA is not served as valid JSON (an HTML 404 page is not an association file)")
    ids = a.get("applinks_app_ids") or []
    exp = d.get("expected_app_id")
    if exp and exp not in ids:
        fails.append(f"UL-2 expected appID {exp!r} is not in AASA applinks appIDs {ids!r} (format <TeamID>.<BundleID>)")
    if not ids:
        fails.append("UL-2 AASA lists no applinks appIDs (universal links have no app to open)")
    if not a.get("has_components"):
        fails.append("UL-2 AASA has no components array (path matching is undefined; details/components define which URLs open the app)")
    if a.get("all_excluded"):
        fails.append("UL-2 every component is exclude:true (the file opts every URL out of universal links)")
    ent = d.get("entitlement_domains") or []
    dom = d.get("domain")
    want = f"applinks:{dom}"
    if want not in ent:
        fails.append(f"UL-3 entitlement lacks {want!r} (Associated Domains Entitlement must list applinks:<FQDN>; entries present: {ent!r})")
    for e in ent:
        body = e.split(":", 1)[-1].split("?")[0]
        if "/" in body or body != body.strip():
            fails.append(f"UL-3 entitlement entry {e!r} contains a path or trailing slash (FQDN only, no path/query/trailing slash)")
    if ids and want not in ent:
        fails.append("UL-4 pairing broken: AASA lists appIDs but the app has no matching Associated Domains Entitlement (Apple: apps in the file must have a matching entitlement)")
    h = d.get("handler") or {}
    if not h.get("handles_browsing_web"):
        fails.append("UL-5 app does not handle browsing-web user activities (no onContinueUserActivity / continue-user-activity path: a tapped universal link has nowhere to land)")
    if h.get("handles_browsing_web") and not h.get("routes_to_specific_screen"):
        fails.append("UL-5 handler opens the app but does not route to the specific screen/content the URL names (universal link as app-launcher only)")
    fb = d.get("fallback") or {}
    if not fb.get("unmatched_opens_web"):
        warns.append("UL-6 unmatched-path fallback to the website is not recorded (non-matching URLs should keep working as web links)")
    m = d.get("measurement") or {}
    if not m.get("ul_taps_event"):
        fails.append("UL-6 universal-link arrivals are not measured (no event for UL-opened sessions: the surface cannot be told apart from organic opens)")
    if not m.get("runbook_notes_cdn_timing"):
        warns.append("UL-6 runbook does not note Apple CDN timing (CDN fetches within 24h; devices re-check about weekly — a same-day 'it does not work' read is premature)")
    if a.get("served") and d.get("aasa_content_type") not in (None, "application/json"):
        warns.append(f"UL-1 content-type is {d.get('aasa_content_type')!r} (third-party guidance expects application/json; not stated on the Apple page read, warning only)")
    if d.get("aasa_size_kb") is not None and d["aasa_size_kb"] > 128:
        warns.append("UL-1 AASA exceeds 128KB (third-party guidance figure; not stated on the Apple page read, warning only)")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for f in fails: print("FAIL", f)
    for w in warns: print("WARN", w)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)} app={d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
