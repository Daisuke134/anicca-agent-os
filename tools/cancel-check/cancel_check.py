#!/usr/bin/env python3
"""cancel-check: deterministic gate for Apple Retention Messaging (cancel-screen saves).
Stdlib only, offline, free. Sources (read in full this run / in-house primaries):
- Superwall, "What actually saves subscribers on Apple's cancel screen?" (2026-09-29,
  30 apps, ~73,000 sends, Aug 31-Sep 28 2026): save = no cancel within 24h; median save
  text 20.7% / promo 17.7% / switch-plan 12.9%; in 6 of 8 apps running both, text >=
  discount; concrete loss 21%, lost progress/streak 29% (n=1), goal reminder 14%,
  FOMO 7%, generic "you'll lose access" 6%; switch-plan actual switches only ~1.4%;
  plan medians annual 16.3% / monthly 13.5% / weekly 12.6%; text & promo saves hold at
  7 days (-1.5 to -3 pts), switch-plan loses ~1/3; header 66 chars / body 144 chars;
  default message for EVERY product and locale (locales do not carry over); submit
  early (every message/image passes App Review); one type per product, rotate ~2 weeks.
  https://superwall.com/blog/apple-retention-messaging-benchmarks
- RevenueCat, "Early Apple Retention Messaging benchmarks from 22M messages"
  (309 apps, 21,960,020 messages, Mar-Sep 2026): median save 17%, top 10% >=42%;
  87% of apps show discount/switch yet acceptance is only ~1.1% promo / ~0.6% switch
  -- most saves are non-acceptors who simply do not cancel; save rate is NOT lift
  (no no-message control; cancellation-rate effect unproven vs matched apps);
  discounts must be selective (exclude trials / prior redeemers) or subscribers learn
  to start cancelling for a lower price; judge with renewals + revenue, not save alone.
  https://www.revenuecat.com/blog/growth/apple-retention-messaging-benchmarks
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app, configured_in_asc, review_approved, products_covered, locales_covered,
 first_message_type, offers_added_only_if_beat_text, copy:{header_chars, body_chars,
 angle, names_specific_loss, loss_items_all_exist_in_product, mentions_price_or_discount},
 rotation:{types_per_product_simultaneous, rotation_days}, discount:{blanket_to_all,
 excludes_trials, excludes_prior_redeemers}, measurement:{save_rate_24h_tracked,
 save_rate_7d_hold_tracked, renewal_tracked, split_by_plan, split_by_product_locale,
 primary_metric, reported_as_lift}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    if not d.get("configured_in_asc"):
        fails.append("C-0 no retention message is recorded as configured in App Store Connect (a spec with draft copy is not a message a cancelling subscriber can see; the in-house churn-save spec has existed since 2026-11-05 with no ASC configuration record)")
    if not d.get("review_approved"):
        fails.append("C-0 messages are not recorded as App Review approved (every production message and image passes Apple review and it takes days -- unapproved copy saves nobody)")
    if (d.get("products_covered") or 0) < 1 or (d.get("locales_covered") or 0) < 1:
        fails.append("C-0 coverage is empty: a default message must exist for every product and every locale (locales do not carry over -- en-US does not cover en-GB or ja)")
    if d.get("first_message_type") != "text":
        fails.append(f"C-1 first message type is {d.get('first_message_type')!r}, not text (text median save 20.7% >= promo 17.7%; in 6 of 8 apps running both, text matched or beat the discount -- a discount must earn its place by beating text first)")
    offers = d.get("first_message_type") in ("promo", "switch") or d.get("offers_present")
    if offers and not d.get("offers_added_only_if_beat_text"):
        fails.append("C-1 an offer is present without a recorded measurement that it beat the text message's save rate (discounts do not reliably win; adding one first spends margin on an unproven lever)")
    c = d.get("copy") or {}
    if (c.get("header_chars") or 999) > 66:
        fails.append(f"C-2 header is {c.get('header_chars')!r} chars, over Apple's 66-char limit")
    if (c.get("body_chars") or 999) > 144:
        fails.append(f"C-2 body is {c.get('body_chars')!r} chars, over Apple's 144-char limit")
    if c.get("angle") in ("generic_access", "fomo_new_content", "generic_encouragement"):
        fails.append(f"C-2 copy angle is {c.get('angle')!r} (generic 'you'll lose access' saved 6%, FOMO 7%, generic encouragement fell flat -- only a named, concrete loss reached 21%)")
    if not c.get("names_specific_loss"):
        fails.append("C-2 copy does not name a specific thing the subscriber loses (the top angle names what they built or own: progress, streak, saved content, history)")
    if c.get("names_specific_loss") and not c.get("loss_items_all_exist_in_product"):
        fails.append("C-2 copy names a loss the product does not actually have (naming an unimplemented feature as the loss is a fabricated claim -- the loss must exist before it can be named)")
    if c.get("mentions_price_or_discount"):
        fails.append("C-2 text copy mentions price or a discount (price/discount wording in message text is an App Review rejection reason; discounts belong to the offer object, not the text)")
    r = d.get("rotation") or {}
    if (r.get("types_per_product_simultaneous") or 0) > 1:
        fails.append(f"C-3 {r.get('types_per_product_simultaneous')} message types run simultaneously per product (run one type per product, rotate and compare -- simultaneous types make attribution impossible)")
    if r.get("types_per_product_simultaneous") == 1 and (r.get("rotation_days") or 0) < 14:
        fails.append(f"C-3 rotation window is {r.get('rotation_days')!r} days, under ~14 (Superwall's rotation is a couple of weeks per type before swapping)")
    disc = d.get("discount") or {}
    if disc.get("blanket_to_all"):
        fails.append("C-4 the discount is shown to everyone who opens the cancel screen (RevenueCat: blanket discounts teach subscribers that starting to cancel is an easy way to get a lower price)")
    if d.get("offers_present") and not disc.get("excludes_trials"):
        warns.append("C-4 offer targeting does not exclude free-trial subscribers (RevenueCat's selectivity example; warning only in this gate)")
    if d.get("offers_present") and not disc.get("excludes_prior_redeemers"):
        warns.append("C-4 offer targeting does not exclude subscribers who already redeemed an offer (warning only in this gate)")
    m = d.get("measurement") or {}
    if not m.get("save_rate_24h_tracked"):
        fails.append("C-5 the 24-hour save rate is not tracked (save = did not cancel within 24h of the message; benchmarks: median 17% RevenueCat / 13-21% by type Superwall)")
    if not m.get("save_rate_7d_hold_tracked"):
        fails.append("C-5 the 7-day hold is not tracked (text/promo saves should drop only 1.5-3 points; switch-plan loses ~1/3 in a week -- a 24h-only read cannot tell a save from a delay)")
    if not m.get("renewal_tracked"):
        fails.append("C-5 renewal after the save is not tracked (RevenueCat: track renewals and revenue alongside the save rate to see which message keeps subscribers through their next payment)")
    if not m.get("split_by_plan"):
        fails.append("C-5 save rate is not split by plan (plan medians differ materially: annual 16.3% / monthly 13.5% / weekly 12.6% -- a blended rate hides the hardest segment, weekly)")
    if not m.get("split_by_product_locale"):
        fails.append("C-5 save rate is not split by product and locale (Apple only reports product and locale; an un-split rate cannot be acted on per message)")
    if m.get("primary_metric") == "offer_acceptance":
        fails.append("C-5 offer acceptance is the primary metric (acceptance is ~1.1% promo / ~0.6% switch -- most saves never accept anything; judging by acceptance misreads a working message as a failure)")
    if m.get("reported_as_lift"):
        fails.append("C-5 the save rate is reported as lift (both primaries are explicit: save rate is not lift -- there is no no-message control, and RevenueCat found no measurable cancellation-rate effect vs matched apps)")
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
