#!/usr/bin/env python3
"""availability-check: deterministic gate for the APP STORE AVAILABILITY & PRE-ORDER surface.
Stdlib only, offline, free. Owns Pricing and Availability: territory selection and the
pre-order clock. Not ASO/metadata (metadata-check), not featuring (featuring), not CPP.
Sources (read in full 2026-11-22):
- Apple ASC Help, "Publish for pre-order"
  https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/publish-for-pre-order
  Pre-order only where the app has not yet been released; free and paid apps on all platforms
  are eligible; IAPs and app bundles are NOT eligible (promoted IAPs stay hidden until release).
  First release: date 2-180 days out. Existing app in a new territory: 2-365 days out. A date
  edit must stay within 180 (first) / 365 (new territory) days OF THE PRE-ORDER'S INITIAL
  PUBLICATION in that territory, and is impossible once the date has passed there. Once released
  in a territory, pre-order there is never possible again. The pre-order publishes only after
  App Review approval + Release This Version, and may take up to 24h to appear to all users.
  Display: <180 days shows the full date, beyond shows month/year only. Paid: charged at release
  at the LOWER of the accepted pre-order price and the release-day price. At release customers
  are notified and the app auto-downloads; they receive the latest released version. Removing a
  pre-order: customers get nothing and are not charged, and republishing after the original
  release date has passed is impossible. New App Store territories are added automatically
  unless availability is managed otherwise.
- ShotCanvas, "How pre-orders and pre-registration actually work" (2026-10-24)
  https://www.shotcanvas.app/blog/pre-orders
  The 180 days are a fixed budget from day one (publish 150 days out = 30 days of slip room).
  Apple does NOT contact pre-order customers when the date changes or the pre-order is removed;
  tell them yourself and keep the date out of uneditable marketing. App Analytics shows
  pre-orders by date/region/source; Sales and Trends adds cancellations. Play pre-registration
  is a separate 90-day, non-extendable clock.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision_record") or {}
    if not dec.get("availability_decision_recorded_per_app"): f.append("AV-0 the availability/pre-order decision is not recorded per app (which territories are live, which are pre-order, which are excluded -- and why -- is currently an unrecorded default)")
    if not dec.get("territory_list_read_from_asc_not_assumed"): f.append("AV-0 the territory list was not read from App Store Connect (assuming 'available everywhere' hides territories excluded long ago and territories never enabled)")
    if not dec.get("new_territory_auto_add_preference_recorded"): f.append("AV-0 the new-territory auto-add behaviour is not recorded (Apple makes the app available in new App Store countries automatically unless availability is edited -- a launch in a market nobody chose is a decision made by default)")
    if not dec.get("released_territory_preorder_irreversibility_understood"): f.append("AV-0 the irreversibility is not understood (once an app is released for download in a territory it can NEVER be offered for pre-order there again -- releasing early to 'test' a market permanently spends that market's pre-order)")
    win=d.get("window_eligibility") or {}
    if not win.get("preorder_only_in_unreleased_territories"): f.append("AV-1 pre-order is not restricted to unreleased territories (eligibility is per country/region where the app has not yet been released; a live territory cannot be re-pre-ordered)")
    if not win.get("iap_and_bundles_excluded_understood"): f.append("AV-1 the IAP/bundle exclusion is not understood (In-App Purchases and app bundles are not eligible for pre-order, and promoted IAPs do not display on the product page until release -- a launch plan that sells the IAP during pre-order sells something invisible)")
    if not win.get("first_release_window_2_to_180_checked"): f.append("AV-1 the first-release window is not checked (release date must be 2-180 days in the future for a first publication)")
    if not win.get("new_territory_window_2_to_365_checked"): f.append("AV-1 the new-territory window is not checked (an app already on sale somewhere gets 2-365 days for a new territory -- using the 180-day first-release limit, or exceeding 365, both misplan the expansion)")
    clk=d.get("clock_and_slack") or {}
    if not clk.get("window_counted_from_initial_publication"): f.append("AV-2 the window is counted from today instead of from the pre-order's initial publication in that territory (the 180/365 days are a fixed budget that started on publication day; a date edit that looks 'within 180 days of now' can already be impossible)")
    if not clk.get("slip_slack_planned_not_maxed"): f.append("AV-2 no slip slack is planned (publishing at the maximum date leaves almost no room to move: 150 days out = 30 days of total slip room for the life of that pre-order)")
    if not clk.get("date_change_customer_notice_owned"): f.append("AV-2 customer notice on a date change/removal is not owned by us (Apple does not contact pre-order customers when the date changes or the pre-order is removed -- silence from us is the only message they get)")
    if not clk.get("date_kept_out_of_uneditable_marketing"): f.append("AV-2 the exact release date appears in marketing that cannot be edited (if the date may move, uneditable creative carrying it becomes a false promise; Apple's own guidance is to leave it out)")
    rev=d.get("review_and_display") or {}
    if not rev.get("preorder_live_only_after_review_and_manual_release"): f.append("AV-3 the go-live sequence is not recorded (a first pre-order appears only after App Review approval AND Release This Version on a Pending Developer Release version -- setting up availability alone publishes nothing)")
    if not rev.get("visibility_24h_verified_before_traffic"): f.append("AV-3 traffic is sent before live visibility is verified per territory (publication is immediate but can take up to 24 hours to appear to all users -- an announcement in hour one can land on a page that is not there yet)")
    if not rev.get("expected_date_display_rule_understood"): f.append("AV-3 the Expected-date display rule is not understood (under 180 days the full date shows; beyond, only month and year -- a 300-day new-territory pre-order cannot promise customers a specific day on the page)")
    if not rev.get("paid_lower_of_two_prices_understood"): f.append("AV-3 the paid pre-order pricing rule is not understood (customers are charged at release the LOWER of the price they accepted and the release-day price -- raising the price during pre-order earns nothing from existing orders, and a cut is safe to run)")
    rel=d.get("release_and_removal") or {}
    if not rel.get("release_day_notify_autodownload_expected"): f.append("AV-4 release-day fulfilment is not planned for (customers are notified and the app auto-downloads to the ordering device -- support, servers and the first-run experience must be ready on that morning, not that week)")
    if not rel.get("customers_get_latest_released_version"): f.append("AV-4 version handling during pre-order is not recorded (customers receive the latest version released for distribution; submitting fixes during the window is expected, and the bare first build is not what ships)")
    if not rel.get("removal_consequences_understood"): f.append("AV-4 removal consequences are not understood (removing a pre-order means customers receive nothing and are not charged, and after the original release date passes the app cannot be republished as a pre-order -- removal is not a pause button)")
    mea=d.get("measurement_and_use") or {}
    if not mea.get("preorder_analytics_and_cancellations_read"): f.append("AV-5 pre-order measurement is not read (App Analytics breaks pre-orders down by date, region and source; Sales and Trends adds cancellations -- gross orders without cancellations overstate launch day)")
    if not mea.get("preorders_not_counted_as_installs"): f.append("AV-5 pre-orders are counted as installs/downloads (they are intent that converts on release day, minus cancellations; banking them early inflates the funnel and the launch forecast)")
    if not mea.get("play_preregistration_clock_separate"): f.append("AV-5 the Google Play clock is not kept separate where the app ships on Android (Play pre-registration is 90 days per country, non-extendable, and missing it ends the campaign everywhere -- it is not Apple's 180/365-day window)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
