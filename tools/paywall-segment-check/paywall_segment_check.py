#!/usr/bin/env python3
"""paywall-segment-check: deterministic gate for the PAYWALL SEGMENT
OFFERS surface (how the offer differs by user state inside the paywall
itself - a direct-purchase annual beside a trial option on the
onboarding paywall, one onboarding-matched testimonial instead of
aggregate social proof, and a no-trial in-app paywall for users who
declined onboarding and kept using the app - is decided, not uniform).
Stdlib only, offline.
Canonical sources (read in full 2026-11-19):
- GTM Sauce #28 (Buttondown archive of App Masters, 2026-11-17)
  https://buttondown.com/candyblocks/archive/sauce-28-parloa/
  (88 lines read in full): three B2C subscription tactics from the
  2026-11-17 App Masters episode. (1) Offer the yearly plan without a
  free trial next to the trial option: a client copied Shotsy's
  paywall - a yearly plan with no trial beside a free-trial option;
  people sign up for the yearly plan without a trial, and direct
  subscriptions reach Meta's ad optimizer faster than trial
  conversions. One client's report, no figures. (2) Show one
  testimonial on the paywall, matched to the user: the host's own app
  shows ONE testimonial instead of rating or member counts; men see a
  man's testimonial, women a woman's, based on onboarding answers.
  One testimonial "tends to work a little bit better" than big
  numbers; no figures. (3) Drop the free trial on the in-app paywall
  for already active users: users who declined the onboarding paywall
  and kept using the app saw an in-app paywall with no trial; trial
  starts fell but the developer made $4,000 more in the no-trial
  segment. This is the only tactic of the three with a figure.
- Kiko case study (secondary corroboration, agency self-report,
  client anonymised, read in full 2026-11-19)
  https://www.kikogrowth.com/case-studies/ai-creative-full-growth-system/
  : onboarding and paywall changes shipped only after a 50/50 test
  lifted subscriptions per sign-up by 10 percent or more; the paywall
  was shown after the first value moment with the user's remaining
  credits. Used here only for the ship-threshold rule, not for its
  MRR figures ($180K to $640K is the agency's own reporting).
Evidence discipline: tactics (1) and (2) carry NO figures in the
source and are recorded as weak evidence - test candidates behind a
ship threshold, never as proven lifts. Tactic (3) carries one
figure ($4,000, one older case, no segment size) and is recorded as
single-case evidence.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PO-0 the paywall-segment-offer surface is not recorded as a decided surface - every user state gets the same offer by habit, not by decision")
    if not dec.get("owner_recorded"): f.append("PO-0 no owner is recorded for segment offers (dual offer, matched testimonial, in-app segment) - a segment that underperforms has no accountable reader")
    if not dec.get("paywall_surfaces_inventoried"): f.append("PO-0 the paywall surfaces are not inventoried as separate surfaces (onboarding paywall, in-app paywall, second offer after close, win-back) - segment rules written for one surface leak silently onto the others")
    dual=d.get("dual_offer") or {}
    if not dual.get("no_trial_annual_beside_trial_option"): f.append("PO-1 the onboarding paywall does not offer a direct-purchase annual beside a trial option (the Shotsy form copied by the App Masters client) - users ready to pay outright must enter a trial they did not ask for, and the source reports people do choose the no-trial yearly when it exists (one client, no figures - weak evidence, test candidate)")
    if not dual.get("direct_option_is_a_plan_not_a_toggle"): f.append("PO-1 the trial choice is implemented as a switch on one plan instead of distinct plans - trial toggles are the form Apple rejects under guideline 3.1.2 since mid-January 2026 (RevenueCat reporting in the paywall-2026 spec), so the dual offer must be two plan cards, never a toggle")
    if not dual.get("trial_terms_equally_clear_on_both"): f.append("PO-1 the two options are not equally legible (price, trial length and what happens when the trial ends stated on both) - a direct option that wins only because the trial option is confusing is a dark pattern, not a segment offer")
    tes=d.get("testimonial") or {}
    if not tes.get("single_testimonial_on_paywall"): f.append("PO-2 the paywall does not carry a single testimonial (the App Masters host's own app replaced rating and member counts with ONE testimonial, reported as working a little better than big numbers - no figures, weak evidence) - aggregate counts are the untested default left in place")
    if not tes.get("matched_to_onboarding_answers"): f.append("PO-2 the testimonial is not matched to the user's onboarding answers (in the source, men see a man's testimonial and women a woman's, chosen from onboarding answers) - an unmatched testimonial is generic social proof wearing a segment label")
    if not tes.get("testimonial_is_real_and_consented"): f.append("PO-2 the testimonial's reality is not guaranteed (a real user's own words, with consent, replaceable when withdrawn) - an invented or composited testimonial is a lie under the company's no-lying rule and an App Store risk, and it voids the tactic it was meant to copy")
    seg=d.get("inapp_segment") or {}
    if not seg.get("declined_and_active_segment_defined"): f.append("PO-3 the in-app segment is not defined (users who declined the onboarding paywall AND kept using the app, with the activity threshold recorded) - without the definition the no-trial offer cannot be aimed, and new users who never saw value are the ones most likely to receive it")
    if not seg.get("inapp_paywall_has_no_trial"): f.append("PO-3 the in-app paywall for the declined-and-active segment still offers a trial (the App Masters case removed it: these users already sampled the product by using it, trial starts fell and the segment made $4,000 more - one older case, no segment size, single-case evidence)")
    if not seg.get("no_trial_offer_not_shown_to_new_users"): f.append("PO-3 the no-trial offer is not fenced to the segment (a first-session user has not sampled value yet) - removing the trial at the moment of least knowledge converts the segment tactic into a blanket hard sell")
    mea=d.get("measurement") or {}
    if not mea.get("judged_on_revenue_not_trial_starts"): f.append("PO-4 segment offers are not judged on revenue (the source case is explicit: trial starts FELL while revenue rose $4,000) - a segment read on trial starts kills the winning form for doing exactly what it was designed to do")
    if not mea.get("ship_threshold_recorded"): f.append("PO-4 no ship threshold is recorded before testing (the Kiko program shipped onboarding and paywall changes only after a 50/50 test lifted subscriptions per sign-up by 10 percent or more) - weak-evidence tactics without a threshold ship on anecdote and stay on anecdote")
    if not mea.get("per_segment_revenue_read_separately"): f.append("PO-4 revenue is not read per segment (onboarding dual offer, matched-testimonial viewers, declined-and-active in-app) - blended paywall numbers hide which segment carries the result and which one is being taxed")
    grd=d.get("guardrails") or {}
    if not grd.get("no_fake_scarcity_or_false_terms"): f.append("PO-5 scarcity or terms on a segment offer are not guaranteed real (no false one-time claims, no trial terms that differ from billing) - a segment offer is a price presentation, and a false term on it is a lie at the exact moment of payment")
    if not grd.get("gross_profit_checked_per_segment"): f.append("PO-5 gross profit is not checked per segment (revenue minus store fee and serving cost, per the company's gross-profit rule) - a no-trial segment can raise revenue while raising refunds, and revenue alone would call that a win")
    if not grd.get("evidence_strength_recorded"): f.append("PO-5 the evidence strength behind each tactic is not recorded with the tactic (tactics 1 and 2: no figures in the source; tactic 3: one $4,000 case) - unlabelled weak evidence gets quoted downstream as a proven lift, which is how anecdotes become pricing policy")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
