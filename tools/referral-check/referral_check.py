#!/usr/bin/env python3
"""referral-check: deterministic gate for subscription-app referral programs.
Stdlib only, offline, free. Sources (read in full 2026-11-13):
- RevenueCat, How to build a referral program for your app (updated 2026-09-11):
  reward BOTH referrer and referee; rewards integral to product, hard to game;
  completion event far enough down funnel that repeating it is painful;
  CTA baked into product experience, not hidden in settings, not feeling like an ad;
  start with an MVP; manual reward claiming prevents abuse; referral can be
  20-30% of acquisition mix (Andrew Chen, via RevenueCat).
  https://www.revenuecat.com/blog/growth/how-to-build-a-referral-program-for-mobile-apps
- Insert Affiliate, How Duolingo, Calm and Strava Built Referral Loops (2026-10-10):
  sharing feels natural / built into product; shared content has standalone value
  for recipients before install; rewards dual-sided; sharing recurs, not once.
  https://insertaffiliate.com/blog/duolingo-calm-strava-referral-loops-scale/
- Prior in-house spec affirmation-referral-loop-spec-2026-11-05 (Adapty, full read):
  K-Factor = invites per user x invite->activation; reward on activation, not install.

Extension R-7..R-10 (added 2026-11-21, sources read in full that day):
- Rami / Action Potential, The Referral System Hiding in App Store Connect
  (published 2026-04-20; Alma's shipped implementation, ~1 week, ~800 lines
  backend + ~200 iOS, no third-party SDK): one-time offer codes are a
  PRE-GENERATED POOL, not a per-user generation request (ASC API generation
  is asynchronous; a share tap must never wait on it -- pool row goes
  available -> pending (stamped with referrer, returned <100ms) -> used /
  expired; a scheduled job refills below a threshold, daily not weekly).
  Redemption is detected on TWO idempotent paths because each alone is
  unreliable: (1) RevenueCat INITIAL_PURCHASE webhook carrying offer_code,
  matched against pending rows; (2) the iOS .offerCodeRedemption completion
  calling a confirm endpoint. One referral_completions row per
  (referrer, referee) pair; either path arriving first wins. The webhook's
  shared-secret auth header MUST be validated (an unvalidated webhook lets
  anyone forge a referral and grant themselves premium). Self-referral is
  rejected at redemption (referrer_id == referee_id). ONE entitlement
  identifier everywhere (a week-long bug granted `premium` on one path and
  `alma_premium_promo` on the other; only one unlocked the UX). Reward is a
  promotional entitlement grant (30 days per referral, stackable at Alma);
  the same pool also serves influencer batches and win-back codes.
  https://www.actionpotential.co/p/the-referral-system-hiding-in-app
- Ar.Bhavesh Panse, K-factor math that isn't fantasy (updated 2026-11-17):
  k = i x c where i counts sends that ACTUALLY LEFT the app (not share-button
  taps; screenshots / dark shares undercount, which is survivable -- inflating
  is not) and c counts ACTIVATED users (not installs). The window is part of
  the number: a k with no stated window is fiction. k > 1 is a timestamp,
  not a property -- re-measure on a boring cohort in a boring month. Honest
  sub-1 k discounts paid CAC: effective CAC = paid CAC x (1 - k) (e.g. $2.00
  at k=0.3 -> $1.40). Invites and shared outputs are DIFFERENT loops with
  different conversion rates; tag them separately, never blend.
  https://www.arbhaveshpanse.com/playbooks/product-led-growth/k-factor-math
- Appalize, App Growth Loops (published 2026-03-17, updated 2026-11-21):
  K bands: >1 exponential (rare), 0.3-0.7 strong, <0.1 not meaningful.
  Loop cycle time (sign-up -> referred sign-up) target <14 days; a 60-day
  loop grows slowly however good its K. Loop efficiency = product of the
  step conversion rates; read K by cohort and each step separately.
  https://www.appalize.com/blog/app-marketing/app-growth-loops-building-viral-and-sustainable-growth-engines

Exit 0 = PASS, 1 = FAIL, 2 = PARTIAL (no fails but R-7..R-10 sections absent
-> unknown; absence is recorded, never counted as a pass). Warnings do not fail.
Input JSON: {app, referral_program_implemented, reward:{...}, ask:{...},
 completion:{...}, attribution:{...}, fraud:{...}, measurement:{...},
 k_honesty:{i_counts, c_counts, window_days, invites_shares_tagged_separately,
 k_gt1_treated_as_timestamp},
 cycle:{cycle_time_measured, cycle_time_days, loop_efficiency_measured, k_by_cohort},
 pool:{model, statuses:[...], refill_scheduled, refill_threshold_defined,
 detection_paths:[...], webhook_auth_validated, single_entitlement_id,
 self_referral_rejected_at_redemption},
 economics:{effective_cac_formula, referral_cost_per_activation_tracked}}
"""
import json, sys

GOOD_TRIGGERS = {"after_first_affirmation_complete", "after_premium_win", "after_milestone", "after_first_value_complete"}
BAD_TRIGGERS = {"at_signup", "onboarding_start", "first_session_start", "after_paywall_failure", "on_app_open"}
GOOD_COMPLETION = {"referee_activation", "referee_first_purchase"}
PRODUCT_TYPES = {"premium_days", "premium_time", "credits", "feature_access", "product_value"}
POOL_STATUSES = {"available", "pending", "used", "expired"}
DETECTION_PATHS = {"revenuecat_webhook", "ios_confirm_endpoint"}

def check(d):
    fails, warns, unknowns = [], [], []
    if not d.get("referral_program_implemented"):
        fails.append("R-0 no referral program implemented (a spec without code converts nobody; in-house spec has existed since 2026-11-05)")
    r = d.get("reward") or {}
    rt, ft = r.get("referrer_type"), r.get("referee_type")
    if rt not in PRODUCT_TYPES:
        fails.append(f"R-1 referrer reward type {rt!r} is not product value (both sides must gain product value, e.g. premium days; cash-only invites fraud)")
    if ft not in PRODUCT_TYPES:
        fails.append(f"R-1 referee reward type {ft!r} is not product value (the friend must receive a real gift, not nothing)")
    if not r.get("referrer_cap_days"):
        fails.append("R-1 no referrer reward cap (uncapped premium invites farming; in-house 2026-11-05 spec caps at 30 days)")
    a = d.get("ask") or {}
    trig = a.get("trigger")
    if trig in BAD_TRIGGERS or trig not in GOOD_TRIGGERS:
        fails.append(f"R-2 ask trigger {trig!r} is not after a value moment (never at signup / onboarding start / first session / paywall failure; ask right after the aha / premium win)")
    placements = a.get("placements") or []
    if not placements or placements == ["settings"]:
        fails.append("R-2 referral CTA is hidden in settings only or absent (bake it into the product experience where the value moment happens)")
    if not a.get("share_content_has_standalone_value"):
        fails.append("R-2 shared content has no standalone value for the recipient (Duolingo/Calm/Strava lesson: recipient gets something useful before installing, e.g. the affirmation itself)")
    taps = a.get("share_taps")
    if taps is None or taps > 2:
        fails.append(f"R-2 share flow takes {taps} taps (target <=2 taps to the share sheet)")
    c = d.get("completion") or {}
    if c.get("event") not in GOOD_COMPLETION:
        fails.append(f"R-3 completion event {c.get('event')!r} is too shallow (reward on referee activation or first purchase, never on install / signup alone)")
    if not c.get("idempotent_per_pair"):
        fails.append("R-3 completion is not idempotent per (referrer, referee) pair (double-fire double-pays the reward)")
    at = d.get("attribution") or {}
    if at.get("code_origin") != "server":
        fails.append(f"R-4 code origin {at.get('code_origin')!r} is not server (one code per user, created and stored server-side; never generated in the client)")
    if at.get("code_delivery") == "link_only" or not at.get("code_delivery"):
        fails.append("R-4 attribution relies on a link alone (an iOS link does not survive an App Store install; a typed code the referee enters is the durable path)")
    if not at.get("subscriber_attribute_set_before_purchase"):
        fails.append("R-4 referral code is not set as a subscriber attribute before purchase (without it, purchases and renewals cannot be joined back to the referrer)")
    if not at.get("first_attribution_wins"):
        fails.append("R-4 first attribution does not win (a later code must not steal an already-attributed user)")
    f = d.get("fraud") or {}
    if not ((f.get("hold_days") or 0) >= 7 or f.get("manual_claim")):
        fails.append("R-5 no hold period (>=7 days) and no manual claim step (paying instantly invites self-referral and refund fraud)")
    if not f.get("self_referral_check"):
        fails.append("R-5 no self-referral check (same device / account referring itself must be held, not paid)")
    m = d.get("measurement") or {}
    metrics = set(m.get("metrics") or [])
    for need in ("k_factor", "invite_to_activation", "share_rate"):
        if need not in metrics:
            fails.append(f"R-6 metric {need} is not measured (K-Factor = invites per eligible user x invite->activation; judge activation, not installs)")
    if m.get("denominator") != "eligible":
        fails.append(f"R-6 denominator is {m.get('denominator')!r}, not eligible users (participation is shared / eligible-after-value, not all installs)")
    if not m.get("compares_to_paid_cac"):
        warns.append("R-6 referral CAC is not compared with paid CAC (a referral program must be a better deal than paid acquisition)")

    # ---- R-7..R-10 extension (2026-11-21). Absent section = UNKNOWN, not pass.
    kh = d.get("k_honesty")
    if kh is None:
        unknowns.append("R-7 k_honesty section absent (how K's two inputs are counted is unrecorded; an unrecorded K definition is not a pass)")
    else:
        if kh.get("i_counts") != "sends_left_app":
            fails.append(f"R-7 i counts {kh.get('i_counts')!r}, not sends_left_app (count shares/invites that actually left the app, not share-button taps; undercounting dark shares is survivable, inflating is not)")
        if kh.get("c_counts") != "activated":
            fails.append(f"R-7 c counts {kh.get('c_counts')!r}, not activated (conversion is to a new ACTIVATED user reaching first value, not an install)")
        w = kh.get("window_days")
        if not isinstance(w, (int, float)) or isinstance(w, bool) or w <= 0:
            fails.append(f"R-7 K window is {w!r} (the window is part of the number; a K quoted with no window is fiction -- fix a window, e.g. cohort's first 30 days, and hold it)")
        if not kh.get("invites_shares_tagged_separately"):
            fails.append("R-7 invites and shared outputs are blended into one K (they are different loops with different conversion rates; tag separately or the number hides which loop deserves the next sprint)")
        if not kh.get("k_gt1_treated_as_timestamp"):
            fails.append("R-7 a K above 1 would be read as a property of the product (it is a timestamp of a burst; re-measure on a boring cohort in a boring month before planning on it)")
    cy = d.get("cycle")
    if cy is None:
        unknowns.append("R-8 cycle section absent (loop cycle time and step efficiency are unmeasured; K alone says nothing about speed)")
    else:
        if not cy.get("cycle_time_measured"):
            fails.append("R-8 loop cycle time is not measured (sign-up -> referred sign-up; target <14 days -- a 60-day loop grows slowly at any K)")
        ctd = cy.get("cycle_time_days")
        if isinstance(ctd, (int, float)) and not isinstance(ctd, bool) and ctd > 14:
            warns.append(f"R-8 measured cycle time is {ctd} days, above the <14-day target (shorten the cycle before raising K)")
        if not cy.get("loop_efficiency_measured"):
            fails.append("R-8 loop efficiency (product of the step conversion rates) is not measured (a small gain at any one step compounds through the whole loop; unmeasured steps cannot be improved in order)")
        if not cy.get("k_by_cohort"):
            fails.append("R-8 K is not read by cohort (a single blended K hides whether the loop is improving or decaying)")
    p = d.get("pool")
    if p is None:
        unknowns.append("R-9 pool section absent (whether offer codes are pre-generated as a pool or minted on demand at the share tap is unrecorded)")
    else:
        if p.get("model") != "pre_generated_pool":
            fails.append(f"R-9 code supply model is {p.get('model')!r}, not pre_generated_pool (ASC API generation is asynchronous; minting on the share tap makes the share button a loading spinner and an empty pool a 503 -- pre-generate, assign from the pool in <100ms)")
        missing = POOL_STATUSES - set(p.get("statuses") or [])
        if missing:
            fails.append(f"R-9 pool statuses are missing {sorted(missing)} (the lifecycle is available -> pending (stamped with the referrer) -> used / expired; a missing state is a code that can leak or double-pay)")
        if not p.get("refill_scheduled"):
            fails.append("R-9 no scheduled pool refill (a job watches the available count and refills below a threshold, daily not weekly; Apple latency means an empty pool is a broken referral feature)")
        if not p.get("refill_threshold_defined"):
            fails.append("R-9 no refill threshold is defined (keep it generous; the refill trigger is a count of available rows, not a calendar guess)")
        dm = DETECTION_PATHS - set(p.get("detection_paths") or [])
        if dm:
            fails.append(f"R-9 redemption detection is missing {sorted(dm)} (each path alone is unreliable -- the webhook can arrive late, empty, or never, and the app can be backgrounded before confirming; both paths, idempotent per pair, first arrival wins)")
        if not p.get("webhook_auth_validated"):
            fails.append("R-9 the RevenueCat webhook's shared-secret auth header is not validated (anyone on the internet can forge a successful referral and grant themselves premium)")
        if not p.get("single_entitlement_id"):
            fails.append("R-9 the promotional entitlement identifier is not single and shared by both paths (drift between paths grants an entitlement that unlocks nothing on one of them)")
        if not p.get("self_referral_rejected_at_redemption"):
            fails.append("R-9 self-referral is not rejected at redemption (referrer_id == referee_id must reject at the redemption check itself, not only in later fraud review)")
    e = d.get("economics")
    if e is None:
        unknowns.append("R-10 economics section absent (the referral loop's effect on acquisition cost is unrecorded)")
    else:
        if e.get("effective_cac_formula") != "paid_cac_x_1_minus_k":
            fails.append(f"R-10 effective CAC formula is {e.get('effective_cac_formula')!r}, not paid_cac_x_1_minus_k (an honest sub-1 K discounts every paid channel at once: $2.00 CAC at K=0.3 is $1.40 effective; quoting paid CAC alone overstates acquisition cost)")
        if not e.get("referral_cost_per_activation_tracked"):
            fails.append("R-10 referral cost per ACTIVATED referred user is not tracked (reward cost divided by activations, not by installs or redemptions alone)")
    return fails, warns, unknowns

if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        data = json.load(fh)
    fails, warns, unknowns = check(data)
    for w in warns:
        print(f"WARN {w}")
    for u in unknowns:
        print(f"UNKNOWN {u}")
    for x in fails:
        print(f"FAIL {x}")
    if fails:
        print(f"RESULT FAIL ({len(fails)} fails, {len(warns)} warnings, {len(unknowns)} unknowns)")
        sys.exit(1)
    if unknowns:
        print(f"RESULT PARTIAL (0 fails, {len(warns)} warnings, {len(unknowns)} unknowns)")
        sys.exit(2)
    print(f"RESULT PASS (0 fails, {len(warns)} warnings, 0 unknowns)")
    sys.exit(0)
