#!/usr/bin/env python3
"""Deferred deep link Gate checker (DDL-0..DDL-7). Stdlib only, deterministic, offline.
Sources (full-read 2026-11-14):
- AppsFlyer glossary, Deferred Deep Linking https://www.appsflyer.com/glossary/deferred-deep-linking/
  Path A installed -> direct to intended screen. Path B not installed -> store the
  intended destination, redirect to store, on first open retrieve it and land on
  the specific content. "The user arrives where the link intended, attributed and
  4x more likely to convert" (vendor claim, linked from the glossary -- not a
  house measurement). Best practices: personalize the destination (general
  post-install screens waste intent), branded recognizable domain, always test
  on both platforms in both install states, connect every link to attribution.
- Airbridge, Deferred Deeplink for Onboarding (2026-06-10, updated 2026-11-05)
  https://www.airbridge.io/en/blog/deferred-deeplink-for-onboarding
  Install erases context by default; generic home kills momentum; >82% of trial
  starts happen on Day 0 and ~44.5% of purchases land on Day 0 (RevenueCat
  State of Subscription Apps, cited there -- secondary). Map every promise to a
  specific destination, carry campaign context into session 1, pre-fill / skip
  redundant questions, shorten path to first action (no forced signup wall /
  permission / tutorial blocking the promised screen), measure the funnel by
  channel and creative, test the not-installed case on a clean device.
House facts: house attribution today is ASC campaign links only
(hidden_files/attribution-links-2026-11-11.md): pt not yet obtained, Campaign
values all empty on 2026-11-11 measurement, links land on the store listing,
no in-app destination is carried through install.
"""
import json, sys

def check(d):
    fails, warns = [], []
    # DDL-0 inventory: every external link mapped promise -> destination
    if d.get("link_inventory_recorded") is not True:
        fails.append("DDL-0: no recorded inventory of external links (bio / posts / referral / web / QR / email) with the promise each link makes")
    if d.get("promise_to_destination_map_recorded") is not True:
        fails.append("DDL-0: no promise-to-destination map (Airbridge: start with the ads/posts, write the exact promise, map each to a specific in-app destination; an unmapped promise has the gap built in)")
    # DDL-1 specific destination, not generic home
    if d.get("destination_type") == "generic_home":
        fails.append("DDL-1: links land on the generic home screen after install (AppsFlyer: general post-install screens waste the intent; Airbridge: generic home is where installs die)")
    elif d.get("destination_type") != "specific_screen":
        fails.append("DDL-1: destination is not recorded as a specific in-app screen/content (deep_link_value per link is required)")
    if d.get("deep_link_value_per_link") is not True:
        fails.append("DDL-1: no deep_link_value carried per link (only a store-listing / campaign link is not a deferred deep link)")
    # DDL-2 context carried + attribution connected
    if d.get("context_carried_through_install") is not True:
        fails.append("DDL-2: click context (channel / creative / offer / referral) is not carried through the install (the store detour erases it by default)")
    if d.get("connected_to_attribution") is not True:
        fails.append("DDL-2: deferred links are not connected to the attribution stack (AppsFlyer: a link not tied to attribution is a missed measurement opportunity)")
    if d.get("campaign_attribution_values_empty") is True:
        fails.append("DDL-2: campaign attribution is recorded as empty in practice (links exist on paper but no campaign values are flowing)")
    # DDL-3 tested both platforms, both install states, clean device
    if d.get("tested_installed_and_not_installed") is not True:
        fails.append("DDL-3: links are not tested in both install states (AppsFlyer: always test installed and not installed; Airbridge: teams test on installed devices, see it work, and ship -- the deferred path is the not-installed case)")
    if d.get("tested_ios_and_android") is not True:
        fails.append("DDL-3: links are not tested on both iOS and Android (routing differs per platform: Universal Links vs App Links)")
    if d.get("tested_on_clean_device") is not True:
        fails.append("DDL-3: the not-installed path is not tested on a clean device")
    # DDL-4 first-open routing via first-launch conversion data, once
    if d.get("first_open_routing") == "app_open_attribution_only":
        fails.append("DDL-4: first-open routing relies only on the re-engagement callback (first installs arrive via first-launch conversion data; the re-engagement callback alone misses first-install routing)")
    elif d.get("first_open_routing") != "first_launch_conversion_data":
        fails.append("DDL-4: first-open routing mechanism is not recorded as first-launch conversion data restoring the stored destination on first open")
    if d.get("destination_replayed_on_later_opens") is True:
        fails.append("DDL-4: the deferred destination is replayed on later opens (it is a first-open restore, not a permanent redirect)")
    # DDL-5 fallback, branded domain, no dead end
    fb = d.get("fallback_when_no_match")
    if fb == "dead_end_or_blank":
        fails.append("DDL-5: a failed/expired match dead-ends (blank / crash / broken page) -- a sensible fallback is required")
    elif fb != "sensible_fallback_with_attribution":
        fails.append("DDL-5: no recorded sensible fallback (onboarding/home with attribution preserved, or a clean web fallback) for no-match / expired links")
    if d.get("branded_link_domain") is not True:
        warns.append("DDL-5: link domain is not a branded, recognizable domain (AppsFlyer: obscure/generic domains reduce click-through and trust)")
    if d.get("claims_100_percent_match") is True:
        fails.append("DDL-5: matching is claimed at 100% (post-ATT matching is partly probabilistic; an honest design records match rate instead of claiming perfection)")
    # DDL-6 friction after landing + carried intent used
    if d.get("promised_screen_blocked_by_wall") is True:
        fails.append("DDL-6: the promised screen sits behind a forced signup wall / permission prompt / tutorial before value (Airbridge: the link gets the user to the right room; a locked room reintroduces the friction)")
    if d.get("carried_intent_used_in_onboarding") is not True:
        fails.append("DDL-6: carried intent is not used in onboarding (pre-fill the goal, skip redundant questions, show the promised offer on the paywall -- otherwise context is restored and then thrown away)")
    if d.get("paywall_offer_matches_promise") is not True:
        fails.append("DDL-6: the paywall after landing does not show the offer/content the link promised (promise and first screen must tell the same story)")
    # DDL-7 measurement by channel/creative, promised-screen denominator
    if d.get("funnel_measured_by_channel_creative") is not True:
        fails.append("DDL-7: the funnel is not measured by channel and creative (click -> install -> promised screen reached -> first action -> trial/purchase; averages across all installs cannot show which links work)")
    if d.get("promised_screen_reached_recorded") is not True:
        fails.append("DDL-7: 'promised screen reached' is not recorded as a funnel step (installs alone are the vanity end of this funnel; Day 0 is where >82% of trial starts happen, per RevenueCat cited by Airbridge)")
    if d.get("match_rate_recorded") is not True:
        warns.append("DDL-7: deferred match rate is not recorded (without it, a low restore rate is invisible and read as low intent)")
    return fails, warns

def main():
    if len(sys.argv) != 2:
        print("usage: deferred_link_check.py <fixture.json>"); return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    fails, warns = check(d)
    for w in warns: print(f"WARN: {w}")
    for x in fails: print(f"FAIL: {x}")
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
