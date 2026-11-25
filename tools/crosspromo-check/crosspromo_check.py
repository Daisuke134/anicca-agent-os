#!/usr/bin/env python3
"""crosspromo-check: deterministic gate for own-portfolio cross-promotion.
Stdlib only, offline, free. Sources (read in full 2026-11-23):
- Sonar, "App cross-promotion: move users between your apps" (policies checked 2026-09-23)
  https://trysonar.app/blog/app-cross-promotion
  Apple documents cross-promotion by name (provider token separates its installs
  in App Store Connect). Allowed: More-apps row, contextual card, SKOverlay.
  Forbidden shape: App-Store-like collection UI (3.2.2(i)), app that is primarily
  marketing (4.2.2), near-duplicate bundle IDs (4.3(a)), unexpected full-screen
  interstitials / auto-opening listings. Best placement is the moment the user's
  need extends past the current app, after the core action succeeds - never
  during onboarding / before activation. Suppress users who already have the
  target (canOpenURL / package visibility); if installed, deep-link instead.
  Landing is a dedicated CPP / custom listing speaking to the source audience.
  Portfolio keywords are split, never shared: cross-promo, not shared keywords,
  moves users across the overlap. Measure incremental installs with a 10%
  holdout, judge at 30 days together with source-app retention. Net-negative
  when: promoted before activation, paying users sent to a weaker monetization
  model, apps too similar, placement intrusive, audiences do not overlap.
  Rule: if you cannot state in one sentence when a user of A needs B, do not ship.
- ASOWin, "Cross-Promotion Between Apps" https://www.asowin.com/blog/cross-promotion-between-apps/
  Native placements over intrusive ads; explain relevance in the copy; never
  require or incentivize an install to unlock features.
Delimitation: cpp-check owns custom product pages, asa-check owns search ads,
referral-check owns user-to-user referral. This gate owns moving users between
your OWN apps: pair selection, placement timing, suppression, keyword split,
incrementality and cannibalization honesty.
Exit 0 = PASS, 1 = FAIL. Input JSON keys are the check names (booleans).
"""
import json, sys
CHECKS = [
    ("pair_inventory_recorded", "XP-0 no inventory of source->target pairs across the portfolio exists (an unlisted pair is an unmanaged channel; with 6 apps the pair space is 30 directed pairs)"),
    ("one_sentence_need_per_pair", "XP-0 a shipped pair has no one-sentence statement of when a user of the source app needs the target app (if that sentence cannot be written, the placement must not ship)"),
    ("audience_overlap_evidenced", "XP-0 audience overlap for the pair is asserted, not evidenced (shared developer is not shared audience; overlap must come from measured user behaviour or a stated shared job)"),
    ("placement_after_core_action", "XP-1 the placement can appear before activation / during onboarding (a card that pulls a user out of an app they have not learned yet costs day-1 retention; it belongs after the core action succeeds)"),
    ("native_contextual_placement", "XP-1 the placement is an intrusive full-screen interstitial or auto-opening store listing instead of a native contextual card / SKOverlay / more-apps row (unexpected interstitials breach Play ads policy and user trust)"),
    ("frequency_capped", "XP-1 there is no frequency cap on the placement (promoting every app to every user on every session reads as spam and taxes the source app's engagement)"),
    ("already_installed_suppressed", "XP-2 users who already have the target app still see the install placement (the slot is wasted; check installed state and swap to a deep link that opens the sibling app)"),
    ("relevance_explained_in_copy", "XP-2 the card copy does not say why this app is relevant to this user now (a generic banner underperforms a reason; the reason is the one-sentence need from XP-0)"),
    ("dedicated_landing_per_pair", "XP-2 the tap lands on the generic default listing instead of a dedicated CPP / custom listing that speaks to arrivals from the source app (cross-promo traffic still has to convert, and generic screenshots do not carry the context)"),
    ("campaign_token_attribution", "XP-3 installs from cross-promotion are not separated with a campaign + provider token (iOS) or listing parameter (Android) (unseparated installs get credited to organic search and the channel can never be judged)"),
    ("holdout_incrementality_measured", "XP-3 there is no holdout (about 10% of eligible users never see the card) so incremental installs are unknown (raw taps claim users who would have installed the sibling anyway)"),
    ("source_retention_read_with_installs", "XP-3 the 30-day read does not include the source app's retention and engagement alongside installs (a pair that gains installs by hollowing out the source app is net negative)"),
    ("keywords_split_not_shared", "XP-4 sibling apps share head keywords / keyword-field terms (two apps chasing one term split one stream; search feeds each app its own users, cross-promo moves them across the overlap)"),
    ("no_weaker_model_flow_for_payers", "XP-4 paying users of the source can be flowed to a target with a weaker monetization model with no bundle / shared-subscription path (moving a subscriber into a free ad app shrinks revenue per user)"),
    ("no_install_gate_or_incentive", "XP-5 no feature is gated on, and no reward is paid for, installing a sibling app (install-to-unlock and incentivized installs breach store policy and fabricate the install count)"),
    ("no_storefront_mimicry", "XP-5 the placement set does not mimic an app-store collection / top-apps grid of the own catalog (3.2.2(i) / 4.2.2 shape; a recommendation is allowed, a fake storefront is not)"),
    ("no_near_duplicate_pairs", "XP-5 a promoted pair is near-duplicate apps differing mainly in theme or name (4.3(a) risk and self-competition; near-duplicates should be merged, not cross-promoted)"),
    ("outside_equals_inside_crosspromo", "XP-5 store copy or the card promises a sibling experience / integration that does not actually exist in the target app (what is shown outside must exist inside)"),
]
def check(d):
    return [m for k, m in CHECKS if not d.get(k)]
def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails: print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS)-len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
