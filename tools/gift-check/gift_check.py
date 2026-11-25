#!/usr/bin/env python3
"""gift-check: gate for GIFTED SUBSCRIPTION / gift-led acquisition - a satisfied
subscriber buys a term for a non-subscriber, the ask is attached to a detected
trigger (not buried in a menu), the recipient needs no account until claim, and
the claim screen converts the recipient into a customer. Stdlib only, offline,
free. Exit 0=PASS, 1=FAIL.
Sources (read in full 2026-11-24):
- freeCodeCamp, "How to Design Gifting Features People Actually Use: Evidence
  from 58 Apps" https://www.freecodecamp.org/news/how-to-design-gifting-features-people-actually-use-evidence-from-58-apps/
  49/58 apps have an end-to-end send flow across 9 scenarios. Stored-value gift
  cards (22 apps) are the ONLY scenario with no trigger - the wish must arrive
  before the app does; the other 8 manufacture the reason (occasion catalogue
  19, checkout upsell 12, subscription seeding 9, referral-as-giving 7...).
  Subscription seeding: an existing subscriber buys a term for a non-subscriber
  = "an acquisition channel wearing a bow" (Thrive Market, Discord, Telegram,
  Headway, Lovi); entry points sit in Settings, on the paywall, or on a
  recipient profile; Thrive Market pays the sender $30 store credit (a decided
  CAC). Telegram discounts the gift by term (10% off 3 months, 45% off a year).
  Six recurring send-flow problems: recipient may have no account (take email/
  phone, create the account at claim - requiring an account before sending
  turns gifting into loyalty, not acquisition); sender must confirm permission
  before a message goes to a non-user (TCPA; store consent copy VERSION +
  timestamp, not a bare boolean); sender can't guess -> hand the choice to the
  recipient (2-3 options); one personalisation rung above a plain card;
  scheduled delivery stored as date+timezone (recipient's), capped window;
  sender previews the recipient's exact view, contents/identity are separate
  secrets (Hide My Name). Claim screen: finish opening the gift BEFORE the
  account ask; the account request does the converting ("the recipient pays
  for the gift with an account, and pays willingly"); a stubbed claim screen
  loses the customer. Sender needs a sent/received view or unopened gifts are
  never chased. Engineering: claim must be idempotent (double-tap = double
  credit without a conditional write); expiry is per gift kind (purchased
  stored value is a legal object - US CARD Act generally bars expiry <5y);
  expired and refunded are separate records/states.
- Apple App Review Guidelines 3.1.1 (via StoreRules summary, checked against
  official text): apps may enable gifting of IAP-eligible items; such gifts
  may only be refunded to the original purchaser and may not be exchanged;
  digital gift cards/certificates redeemable for digital goods may only be
  sold via IAP. Apple Support: free apps/items cannot be gifted via the store
  Gift button, gifts stay within the sender's country/region.
Separation: referral-check owns two-sided referral rewards; family-check owns
Family Sharing eligibility; offercode-check owns offer codes; crosspromo-check
owns cross-app promotion. This gate owns only the paid gift of a term to a
(second, possibly account-less) person and its claim conversion.
NOT adopted: auto-renewing the gift onto the RECIPIENT's payment method by
default (Thrive Market's anniversary charge on the recipient is recorded as
the source's fact, not our form - the giftee must opt in themselves, in plain
language, before any charge); platform-issued "unclaimed gifts" badge bait.
"""
import json, sys
CHECKS=[
 ("gift_surface_recorded","GF-0 no gifted-subscription / gift-term surface is recorded per app (without a recorded surface there is no sender flow, claim flow or read)"),
 ("gift_item_is_iap_eligible_and_sold_via_iap","GF-0 the gift is not an IAP-eligible item sold via in-app purchase (digital gift cards/certificates for digital goods may only be sold via IAP - Guideline 3.1.1; refunds go only to the original purchaser, gifts may not be exchanged)"),
 ("gift_has_detected_trigger_not_menu_only","GF-0 the gift entry has no detected trigger and sits only in an account/settings menu (stored value with no trigger is the one scenario where demand must arrive before the app does - 58-app study; subscription seeding triggers on being a satisfied subscriber)"),
 ("sender_segment_is_satisfied_subscribers","GF-1 the sender segment is not satisfied/tenured subscribers (subscription seeding's trigger is a subscriber who stayed long enough to recommend; asking brand-new or churning users to gift inverts the evidence)"),
 ("gift_entry_on_paywall_or_profile","GF-1 no gift entry point exists on the paywall or a recipient/profile surface (Discord/Telegram/Headway place it in Settings, on the paywall, or on a recipient's profile - at least the paywall/profile placements must exist, not Settings alone)"),
 ("gift_terms_offer_term_discount_ladder","GF-1 gift terms do not offer a term ladder with the longest term cheapest per month (Telegram: 10% off 3 months, 45% off a year - the sender who commits furthest pays least per month; a single flat term leaves that lever unused)"),
 ("recipient_needs_no_account_until_claim","GF-2 sending requires the recipient to already have an account (take a bare email/phone and create the person at claim; requiring an account first makes gifting a loyalty feature, not acquisition - Thrive Market/Blank Street/Uber Eats)"),
 ("sender_confirms_recipient_permission_versioned","GF-2 the sender does not confirm recipient permission before a message goes to a non-user, or consent is stored as a bare boolean (TCPA: store the consent copy VERSION + timestamp; a stored true proves nothing about what was agreed)"),
 ("recipient_choice_when_sender_cant_guess","GF-2 the sender is forced to guess the exact product/term with no way to hand the choice to the recipient (Grab/Uber Eats hand the choice forward - 2-3 options or recipient-chosen timing - because a sender who cannot guess abandons halfway)"),
 ("one_personalisation_rung_and_sender_preview","GF-2 the gift has no personalisation rung above a plain amount, or the sender cannot preview the recipient's exact view before payment (a bare amount reads thoughtless; the preview - Grab's 'One Last Check' - reassures a sender buying an experience they will never see; contents and sender identity are separate secrets)"),
 ("scheduled_delivery_date_timezone_capped","GF-2 scheduled delivery is not supported, or is stored as a frozen instant instead of date + recipient timezone with a capped window (senders act when they remember, rarely on the date; Revolut resolves 08:00 in the recipient's timezone at send time; Urban Outfitters caps at 90 days)"),
 ("claim_opens_gift_before_account_ask","GF-3 the claim flow asks for an account before the recipient finishes opening the gift (order matters: open first, then the account request does the converting; a stubbed or account-first claim loses the customer the sender already paid for)"),
 ("claim_is_idempotent_single_credit","GF-3 claim is not a single conditional write / idempotent (two taps on a slow connection both find the gift unclaimed and both pay out - the money leaves with no error in the logs)"),
 ("giftee_renewal_is_explicit_optin_not_default","GF-3 the gift auto-renews onto the recipient's payment method by default or without a plain-language opt-in (a gift that silently becomes the recipient's recurring charge converts a present into a billing surprise; the giftee chooses, in words, before any charge)"),
 ("expiry_per_kind_and_refund_separate_state","GF-4 expiry is one number across all gift kinds, or expired and refunded are the same record (purchased stored value is a legal object - US CARD Act generally bars expiry within 5 years; owing a refund and having sent it are different facts)"),
 ("sender_sent_received_tracking_view","GF-4 the sender has no sent/received (My Gifts) view after payment (Uber Eats/Satispay give the sender somewhere to check; every flow that leaves the sender alone after payment loses the chase that gets gifts claimed)"),
 ("gift_read_as_acquisition_funnel","GF-5 gifting is not read as an acquisition funnel (sent -> delivered -> claimed -> giftee self-paying conversion, with sender-paid CAC compared to other channels; Thrive Market decided $30 credit beats its alternatives - without the read there is no such decision)"),
 ("unclaimed_gifts_have_sender_chase_path","GF-5 unclaimed/undelivered gifts have no defined path (sender reminder from the tracking view, expiry handling, refund-to-purchaser per 3.1.1; an unclaimed gift silently kept is revenue booked on a customer never acquired)"),
]
def main(p):
    s=json.load(open(p)); fails=[m for k,m in CHECKS if s.get(k) is not True]
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} pass={len(CHECKS)-len(fails)}/{len(CHECKS)} fails={len(fails)}")
    return 0 if not fails else 1
if __name__=="__main__":
    if len(sys.argv)!=2: print("usage: gift_check.py <state.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
