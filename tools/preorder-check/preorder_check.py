#!/usr/bin/env python3
"""preorder-check: deterministic gate for the APP STORE PRE-ORDER surface
(using pre-orders / regional pre-orders as a launch-velocity and demand-test
instrument, not as a hype announcement). Stdlib only, offline, free.
Sources (read 2026-11-23):
- Apple App Store Connect Help "Publish for pre-order"
  https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/publish-for-pre-order
  Eligible where app not yet released; approved build required first;
  new app release date 2-180 days out; once released in a territory a
  pre-order can never be re-run there; paid customers charged on release
  at the LOWER of accepted pre-order price or release price; on release
  customers are notified and the app auto-downloads; IAPs not eligible
  for pre-order but can be set up during the window.
- PricePush "App Store Pre-Order: How It Works for Developers"
  https://pricepush.app/glossary/app-store-pre-order
  Pre-order price is set per storefront and is a ceiling for that
  customer; opening pre-orders publishes prices in every country, so a
  raw currency conversion commits international users to too-high prices.
- Skill Leaderboard summary of rshankras/pre-orders (secondary summary)
  Regional pre-order for an existing app: up to 365 days out, one-shot
  per territory; CPP and PPO can run during pre-order so launch day lands
  on an already-tested page; pre-orders count toward day-one downloads;
  name / primary category cannot change after pre-order starts; price
  increases require 7-day notice to pre-order customers.
Boundary: phased-release-check / featuring-check own release rollout and
featuring nominations; cpp-check / ppo-check own page tests themselves.
This gate owns the pre-order window decision, its pricing commitment,
page honesty during the window, and day-one conversion reading.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
CHECKS = [
 ("PO-0","launch_pipeline_inventoried","no inventory of upcoming launches / new territories where a pre-order could run (the instrument is never considered)"),
 ("PO-0","territory_oneshot_acknowledged","one-shot rule not recorded (once released in a territory, pre-order there is gone forever; spending it casually wastes it)"),
 ("PO-0","approved_build_before_preorder","no approved-build-first plan (Apple requires an approved version before pre-order can open; a bare placeholder cannot pass review)"),
 ("PO-1","window_within_limits","window not checked against limits (new app 2-180 days; existing app new territory up to 365 days from first publication)"),
 ("PO-1","date_is_real_and_build_ready","release date is not tied to a real, build-ready plan (a slipped fake date burns the one-shot and the waiting users)"),
 ("PO-1","cpp_ppo_run_during_window","CPP / PPO tests are not run during the pre-order window (launch day then lands on an untested page)"),
 ("PO-2","per_storefront_prices_localized","per-storefront prices are raw currency conversions, not localized (opening pre-orders commits prices in every country at once)"),
 ("PO-2","lower_of_two_price_modelled","lower-of-two rule not modelled (paid pre-order customers pay min(accepted price, release price); the pre-order price is a ceiling)"),
 ("PO-2","price_increase_notice_plan","no 7-day notice plan for price increases to pre-order customers"),
 ("PO-3","page_matches_shipped_app","pre-order page promises do not match what will ship (screenshots selling an unrealized vision violate outside=inside; sell only what ships)"),
 ("PO-3","name_category_lock_acknowledged","name / primary category lock after pre-order start is not acknowledged in the launch plan"),
 ("PO-3","search_browse_visibility_used","search/browse visibility during the window is not used (the page is live and indexable; silence wastes free ASO runway)"),
 ("PO-4","preorder_count_tracked","pre-order count is not tracked over time (it is the only in-store measure of genuine install intent before launch)"),
 ("PO-4","dayone_velocity_plan","no day-one plan for the auto-download velocity spike (charts, featuring and first-review handling on the day pre-orders convert)"),
 ("PO-4","preorder_to_activation_read","success is read as downloads only (pre-order auto-downloads must be read through to first open / activation / trial, or the spike is vanity)"),
 ("PO-5","date_change_early_release_procedure","no procedure for moving the date or releasing early (changes propagate within ~24h; an unplanned slip strands waiting users)"),
 ("PO-5","iap_ready_during_window","IAPs / subscriptions are not set up and approved during the window (they cannot be pre-ordered, but launch day monetization must be ready)"),
 ("PO-5","regional_preorder_evaluated_for_existing","regional pre-order is not evaluated for existing apps entering new storefronts (the main remaining use for already-shipped apps)"),
]
def check(d):
    return [f"{g} {k}: {m}" for g,k,m in CHECKS if not d.get(k)]
if __name__=="__main__":
    d=json.load(open(sys.argv[1])); f=check(d)
    for x in f: print("FAIL",x)
    print(f"{'PASS' if not f else 'FAIL'} {len(CHECKS)-len(f)}/{len(CHECKS)}")
    sys.exit(0 if not f else 1)
