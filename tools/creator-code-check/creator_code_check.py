#!/usr/bin/env python3
"""creator-code-check: deterministic gate for the CREATOR OFFER-CODE
surface (whether creator/affiliate distribution on iOS runs on offer
codes -- the only code path since Apple retired IAP promo codes on
2026-03-26 -- with one custom code per creator, store-verified
attribution, and a decided leak response). Stdlib only, offline, free.
Sources (read 2026-11-23):
- DEV/Sabr "Apple retired in-app purchase promo codes: what to do now
  for creator programs" http://dev.to/sabrsystems/apple-retired-in-app-purchase-promo-codes-what-to-do-now-for-creator-programs-12c0
  From 2026-03-26 no new IAP promo codes; offer codes cover all IAP
  types; redemption confirms offerType + offerIdentifier in the
  transaction and offer_code in RevenueCat webhooks (store-verified,
  no IDFA/ATT); custom code per creator (<=64 chars, alnum, cannot be
  edited after creation); redemption URL
  https://apps.apple.com/redeem?ctx=offercodes&id={id}&code={code}
  opens the App Store directly inside TikTok/IG browsers and installs;
  1M codes/quarter shared; one redemption per customer per offer;
  one-time codes expire <=6 months, custom codes may run open-ended.
- Sitara "Promo codes vs tracking links for app influencers"
  https://joinsitara.com/guides/promo-codes-vs-tracking-links
  Pay creators on their own code's verified sales; code counts are a
  floor not the full effect (read with other data); give a reason to
  use the code; creator says+shows code in video/caption/pinned
  comment; link prefills the code; short sayable codes; leak response
  is keep / pause / retire+new code, decided case by case after
  talking to the creator first; commission follows the payments after
  a trial the code started.
Boundary: offercode-check (2026-11-16) owns the redemption surface
(offer decision, in-app sheet, reception/sync). This gate owns the
creator-program layer on top of it: migration, per-creator codes,
distribution form, attribution reading, leak ops.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

CHECKS = [
 ("CC-0","promo_dependency_inventoried","no inventory of where creator/press distribution still depends on retired IAP promo codes (Apple stopped new IAP promo codes 2026-03-26; a spreadsheet-era program silently dies)"),
 ("CC-0","migrated_to_offer_codes","creator distribution is not migrated to offer codes, the only remaining code path covering all IAP types"),
 ("CC-0","offer_per_promoted_subscription","no offer exists per promoted subscription (every code needs an offer: a discount or a free period, with its cost modelled)"),
 ("CC-1","custom_code_per_creator","creators share one generic code or none (a custom code per creator is what makes per-creator credit possible)"),
 ("CC-1","code_validated_before_creation","codes are not validated before creation (custom codes cannot be edited afterwards; a typo'd code is permanent)"),
 ("CC-1","code_short_and_sayable","codes are not short and easy to read aloud (a code a creator cannot say in a video will not be typed)"),
 ("CC-1","redemption_limit_with_headroom","no redemption limit set with headroom / reissue plan (a code that silently caps out mid-campaign credits nobody)"),
 ("CC-2","redemption_link_prefills_code","creator links do not prefill the code via the apps.apple.com/redeem?ctx=offercodes form (plain universal links break in TikTok/IG browsers and force typing)"),
 ("CC-2","code_said_shown_caption_pinned","creators are not briefed to say and show the code in the video, caption and a pinned comment"),
 ("CC-2","incentive_to_use_code","the code carries no incentive (discount or longer trial) -- without a reason, viewers skip it and attribution is lost"),
 ("CC-3","store_verified_attribution_read","sales are not credited from the store-verified signal (transaction offerIdentifier / RevenueCat offer_code) but from probabilistic link guesses"),
 ("CC-3","code_count_read_as_floor","code counts are read as the creator's full effect (they are a floor: viewers who forget the code are real but uncredited; read with brand/search lift)"),
 ("CC-3","commission_on_following_payments","commission is not defined on the payments that follow a trial the code started"),
 ("CC-4","leak_response_decided","no leak response is decided (keep / pause / retire + new code, case by case, talking to the creator first) -- an undecided leak becomes either panic or silent margin loss"),
 ("CC-4","no_bulk_untracked_codes","bulk untracked codes are generated beyond campaign size (they land on coupon sites and give subscriptions to unintended audiences)"),
 ("CC-4","expiry_and_activation_tracked","code expiry / activation lag is not tracked (one-time codes die within 6 months; codes can take up to an hour to activate)"),
]

def check(d):
    fails=[]
    for gate,key,msg in CHECKS:
        if not d.get(key):
            fails.append(f"{gate} {key}: {msg}")
    return fails

if __name__=="__main__":
    d=json.load(open(sys.argv[1]))
    f=check(d)
    for x in f: print("FAIL",x)
    print(f"{'PASS' if not f else 'FAIL'} {len(CHECKS)-len(f)}/{len(CHECKS)}")
    sys.exit(0 if not f else 1)
