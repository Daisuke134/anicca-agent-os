#!/usr/bin/env python3
"""appclip-check: deterministic gate for iOS App Clips.
Stdlib only, offline, free. Sources (search-read 2026-11-15, Apple-documentation
summaries at newly.app/guides/app-clips and /app-thinning-and-size-limits,
which cite the Apple pages named below; plus Apple HIG guidance as quoted there):
- Apple, "Choosing the right functionality for your App Clip" / App Clip
  documentation: an App Clip is a small part of the app usable WITHOUT
  installing the full app; it must accomplish a real task and provide real
  value -- Apple warns against using App Clips solely for marketing/advertising.
- Invocations: physical (App Clip Code, QR code, NFC tag), location-based
  Siri Suggestions, Maps link, Smart App Banner on a website in Safari,
  Messages link, plain link in email / on a web page.
- An invocation URL on your own domain requires domain ownership proof via
  the apple-app-site-association file in /.well-known/ (the same associated-
  domains mechanism Universal Links use), plus the appclips service in the
  Associated Domains entitlement. One default experience; advanced
  experiences are keyed to URLs, most specific prefix wins.
- Size (App Store Connect Help, "Maximum build file sizes"): the cap is the
  UNCOMPRESSED App Clip main bundle AFTER app thinning: 10 MB if iOS 15 or
  earlier is supported, 15 MB for iOS 16, 100 MB ONLY if the clip requires
  iOS 17+, supports DIGITAL invocations only (no App Clip Code / QR / NFC),
  and is used where a reliable connection is likely.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 decision:{clip_shipped, not_shipping_reason_recorded},
 clip:{target_exists, core_task, marketing_only, handles_invocation_url,
       routes_to_specific_content, offers_full_app, shared_app_group,
       sign_in_with_apple_if_auth},
 association:{aasa_wellknown_status, aasa_has_appclips, entitlement_appclips},
 invocation:{types:[digital|physical|...], smart_app_banner_or_link},
 size:{thinned_uncompressed_mb, min_ios, recorded},
 measurement:{invocation_source_tracked, clip_completion_tracked,
              clip_to_install_tracked}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    dec = d.get("decision") or {}
    clip = d.get("clip") or {}
    shipped = bool(dec.get("clip_shipped") or clip.get("target_exists"))
    # AC-0 decision: absence is allowed only as a recorded decision
    if not shipped and not dec.get("not_shipping_reason_recorded"):
        fails.append("AC-0 no App Clip is shipped and no recorded decision explains the absence (an unrecorded absence is an unconsidered surface, not a choice)")
        # Remaining gates describe the shipped state; report them as fails too
        # only where the input explicitly claims a state. Keep AC-0 as the
        # single fail for a pure absence so the count stays honest.
        return fails, warns
    if not shipped:
        return fails, warns  # recorded decision not to ship: gate passes
    # AC-1 real task, not marketing
    if not clip.get("target_exists"):
        fails.append("AC-1 decision says shipped but no App Clip target exists in the project")
    if not clip.get("core_task"):
        fails.append("AC-1 the clip performs no named core task (Apple: a clip accomplishes a real task; a taskless clip is a brochure)")
    if clip.get("marketing_only"):
        fails.append("AC-1 the clip is marketing/advertising only (Apple explicitly warns against App Clips used solely to advertise services or products)")
    # AC-2 association (own-domain invocations need AASA appclips + entitlement)
    assoc = d.get("association") or {}
    if assoc.get("aasa_wellknown_status") != 200:
        fails.append(f"AC-2 /.well-known/apple-app-site-association returns {assoc.get('aasa_wellknown_status')!r}, not 200 (own-domain clip invocation URLs require the association file; without it the clip cannot be invoked from your own links)")
    if not assoc.get("aasa_has_appclips"):
        fails.append("AC-2 AASA has no appclips entry (the association must name the clip, not only the full app)")
    if not assoc.get("entitlement_appclips"):
        fails.append("AC-2 entitlement carries no appclips:<domain> associated-domains entry (AASA and entitlement must pair, as with Universal Links)")
    # AC-3 invocation + routing
    inv = d.get("invocation") or {}
    types = inv.get("types") or []
    if not types:
        fails.append("AC-3 no invocation type is configured (a clip nobody can invoke -- code, link, banner, Maps, Messages -- does not exist as a surface)")
    if not inv.get("smart_app_banner_or_link"):
        warns.append("AC-3 no digital invocation (Smart App Banner / web link) recorded; physical-only clips cannot be reached from the web surfaces the team already publishes (warning only)")
    if not clip.get("handles_invocation_url"):
        fails.append("AC-3 the clip does not handle its invocation URL (the URL is the experience selector; ignoring it lands every invocation on the same generic screen)")
    if not clip.get("routes_to_specific_content"):
        fails.append("AC-3 invocation does not route to the specific content the link promised (outside and inside must be the same experience)")
    # AC-4 size discipline
    size = d.get("size") or {}
    mb = size.get("thinned_uncompressed_mb")
    min_ios = size.get("min_ios") or 0
    physical = "physical" in types
    if not size.get("recorded") or mb is None:
        fails.append("AC-4 thinned uncompressed clip size is not recorded (the size cap is the format's defining constraint; an unmeasured clip is an unshippable clip)")
    else:
        if physical or min_ios < 17:
            cap = 15 if min_ios >= 16 else 10
            if mb > cap:
                fails.append(f"AC-4 clip is {mb} MB but the cap is {cap} MB (physical invocations or min iOS {min_ios} exclude the 100 MB tier, which is digital-only and iOS 17+ only)")
        elif mb > 100:
            fails.append(f"AC-4 clip is {mb} MB, above even the 100 MB digital-only iOS 17+ cap")
    # AC-5 full-app handoff
    if not clip.get("offers_full_app"):
        fails.append("AC-5 the clip offers no path to the full app (the clip is an entry, not a dead end; its job includes handing the user to the full experience)")
    if not clip.get("shared_app_group"):
        fails.append("AC-5 clip and full app share no app group (state created in the clip -- e.g. the first completed session -- is lost at install, breaking the promised continuity)")
    # AC-6 measurement
    ms = d.get("measurement") or {}
    if not ms.get("invocation_source_tracked"):
        fails.append("AC-6 invocation source is not tracked (codes, banners, Maps and Messages convert differently; a blended count cannot steer placement)")
    if not ms.get("clip_completion_tracked"):
        fails.append("AC-6 clip task completion is not tracked (invocations without completions measure curiosity, not value delivered)")
    if not ms.get("clip_to_install_tracked"):
        fails.append("AC-6 clip-to-install conversion is not tracked separately (the clip's whole economic claim is install conversion without an install barrier)")
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
