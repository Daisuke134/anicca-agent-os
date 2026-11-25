#!/usr/bin/env python3
"""multiseat-check: deterministic gate for Apple MULTISEAT / GROUP subscription
purchasing (organizations buying seats in volume via Apple Business / School
Manager, and group purchases where one buyer invites others). Stdlib only,
offline, free.
Sources (read in full 2026-11-23):
- Apple Developer News "Offer your subscriptions to businesses and schools"
  (2026-10-22) https://developer.apple.com/news/
  Multiseat purchasing live for organizations/educational institutions:
  seats bought through a single Apple IAP, assigned/managed with existing
  device management tools, seats can be added/removed at any time. Enabled
  BY DEFAULT in App Store Connect unless previously adjusted; availability
  spans Apple Business, Apple School Manager, and the App Store, changeable
  at any time. Group purchases: from November 2026 configure/test in a
  Sandbox Apple Account; this winter group purchases go live on the App
  Store (buy multiple seats, invite others to access).
- Apple Developer Program License Agreement update (2026-10-13, same page):
  Schedule 2/3 sections added for Group Purchases and for Volume Purchasing
  to Apple Business / School Manager organizations.
Boundary: family-check owns Family Sharing; crosspromo-check owns in-house
cross-promotion; this gate owns ONLY the multiseat/group channel decision,
its sandbox readiness, and seat entitlement handling.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
CHECKS = [
 ("MS-0","inventory_recorded","no inventory of which of the 6 apps' subscriptions are multiseat-eligible is recorded (eligibility is a per-subscription state in ASC; unrecorded = unknown)"),
 ("MS-0","default_status_verified","the enabled-by-default status was never verified per app (default-on is Apple's state, not a house decision; a previously adjusted setting would silently differ)"),
 ("MS-0","channel_owner_recorded","no single owner is recorded for the multiseat/group channel (a default-on channel with no owner is a channel nobody runs)"),
 ("MS-1","channel_availability_decided","availability per channel (App Store / Apple Business / Apple School Manager) was never deliberately decided per app (leaving the default is not a decision; some apps may not fit org buyers)"),
 ("MS-1","agreement_terms_acknowledged","the Oct 2026 license-agreement sections for Group Purchases / Volume Purchasing are not recorded as reviewed (the channel operates under terms nobody here has read)"),
 ("MS-1","per_app_fit_assessed","no per-app fit assessment exists (a behavior-intervention app for a school/team differs from a fashion app for a business; one blanket state fits neither)"),
 ("MS-2","sandbox_group_configured","group purchases were not configured in a Sandbox Apple Account (Apple opened sandbox configuration in November 2026 precisely so the winter launch is not the first test)"),
 ("MS-2","sandbox_group_tested","the group purchase flow (buy seats -> invite -> invitee accesses) was never sandbox-tested end to end before the winter App Store launch"),
 ("MS-2","entitlement_handles_assigned_seats","the app's entitlement handling for assigned/invited seats is not verified (a seat assigned by an org admin or a group invite must unlock the same subscription state; unverified = invitees may hit the paywall)"),
 ("MS-3","seat_lifecycle_handled","seat add/remove lifecycle is not handled or recorded (orgs can add/remove seats at any time; removal must end access cleanly without breaking the remaining seats)"),
 ("MS-3","individual_purchase_unchanged","enabling multiseat must not change the individual purchase path -- not verified (the default-on channel must be additive, never a regression to the main funnel)"),
 ("MS-3","no_org_access_to_personal_content","it is not verified/recorded that a seat buyer (org admin / group organizer) gets NO access to a member's personal in-app content (behavior data is private; a seat is a license, not a window)"),
 ("MS-4","org_buyer_value_copy_exists","no value copy exists for the org/school buyer surface (discovery happens in Apple Business / School Manager; consumer copy does not speak to a buyer purchasing for a team/class)"),
 ("MS-4","group_buyer_path_recorded","the group-purchase buyer path (one buyer, multiple seats, invite others) is not recorded as a distribution surface (winter launch makes it a consumer surface, not only B2B)"),
 ("MS-4","per_seat_economics_recorded","per-seat economics are not recorded (a seat sale is subscription revenue through a different buyer; without per-seat price/margin on record the channel cannot be judged on gross profit)"),
 ("MS-5","measurement_separates_multiseat","multiseat/group revenue is not separated in measurement (blending it into consumer MRR hides whether the channel works and inflates the consumer funnel read)"),
 ("MS-5","support_path_for_seat_issues","no support path is recorded for seat assignment/invite failures (the buyer is an admin, not the end user; consumer support scripts do not cover a seat that never arrived)"),
 ("MS-5","periodic_channel_review","the channel is not on a periodic review (default-on states drift when ASC settings or app fit change; only a review catches a channel that was on but broken)"),
]
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = json.load(open(path)) if path != "-" else json.load(sys.stdin)
    fails = [f"{g} {k}: {msg}" for g, k, msg in CHECKS if not data.get(k)]
    if fails:
        print(f"FAIL {len(fails)}/{len(CHECKS)}")
        for f in fails: print(" -", f)
        return 1
    print(f"PASS {len(CHECKS)}/{len(CHECKS)}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
