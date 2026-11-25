#!/usr/bin/env python3
"""embedded-virality-check: deterministic gate for embedded virality (product outputs
that reach non-users in normal use), as distinct from referral programs and share prompts.
Stdlib only, offline, free. Sources (read in full 2026-11-23):
- Signal, "Referral Loops Are Dead. Embedded Virality Is What Actually Works Now."
  https://www.readsignal.io/article/referral-loops-dead-embedded-virality-works
  Referral participation 11% (2018) -> 3% (2026), link->signup 18% -> 4%, referred
  90-day retention vs organic +12% -> -2% (the quality signal has inverted; figures
  are the article's own table, treated as vendor/secondary data). Embedded virality =
  use product -> product creates an output -> output reaches non-users in normal
  workflow -> non-user experiences value -> signs up to create their own. Three
  components: output artifact, non-user exposure, motivation bridge (intrinsic, no
  incentive). Metrics: exposure rate; impression-to-signup 1-3% average / 3-7%
  strong / 7%+ exceptional; organic K = artifacts/user/month x non-user exposures
  per artifact x impression-to-signup (Calendly 0.48, Figma 0.31, Loom 0.18).
  Design: shareable by default, no login for viewers, brand the output (tasteful,
  not removable on free), viewer experience is the demo, CTA after value is felt.
- GTM Wiki, "Referral and Viral Flow - the Loop Pipeline"
  https://gtm-wiki-nu.vercel.app/docs/flows/referral-and-viral
  Growth compounds on cycle count, not volume; pay on conversion, never on the
  share; decision gate = second-person reason + retention holds + attribution
  exists; a coefficient that holds across two cohorts on a repeat cycle is a loop,
  a single strong week is a campaign; fix retention before asking for referrals.
Delimitation: referral-check owns the incentivised referral program (offer-code
pool, reward mechanics); share-check owns the in-app share prompt for content.
This gate owns the output-artifact -> non-user exposure -> signup chain and its
measurement. Exit 0 = PASS, 1 = FAIL.
Input JSON keys are the check names themselves (booleans).
"""
import json, sys

CHECKS = [
    # EV-0 decision and artifact inventory
    ("output_artifact_named", "EV-0 the product's output artifact is not named (a document, card, video, page or link the product itself creates; a marketing message or a 'refer a friend' screen is not an output artifact)"),
    ("artifact_created_in_core_workflow", "EV-0 the artifact is not created inside the core workflow (embedded virality is a byproduct of normal use; a bolt-on growth feature is a referral program, not this loop)"),
    ("second_person_reason_recorded", "EV-0 no second-person reason is recorded (why would a recipient want this artifact, and why would they want their own; without it the decision gate fails)"),
    ("retention_holds_before_loop", "EV-0 retention does not hold yet, or was never checked (fix retention before building any loop on top; a one-and-done product offers one share chance, a daily product offers many)"),
    # EV-1 exposure
    ("artifact_reaches_nonusers_by_default", "EV-1 artifacts do not reach non-users by default in normal use (if the output stays inside the user's account, exposure is structurally zero)"),
    ("viewer_needs_no_login", "EV-1 a viewer must log in or install before experiencing the artifact (the exposure is the demo; a login wall collapses the motivation bridge)"),
    ("sharing_is_default_and_low_friction", "EV-1 sharing the artifact is not the default, low-friction path (public link / one-click; every extra step is drop-off the loop pays for)"),
    ("exposure_rate_tracked", "EV-1 exposure rate is not tracked (share of artifacts that reach at least one non-user; without it the chain's first link is invisible)"),
    # EV-2 viewer experience and bridge
    ("artifact_carries_brand", "EV-2 the artifact carries no tasteful brand attribution (the awareness layer: a small logo/link naming the product that made it; unbranded exposure converts nobody)"),
    ("viewer_experience_is_the_demo", "EV-2 the viewer's experience of the artifact is not itself a firsthand product demo (the non-user must experience the value in context, not read a claim about it)"),
    ("cta_after_value_moment", "EV-2 the signup CTA is not placed after the value moment (after they watched / read / used it; a CTA before demonstrated value converts on incentive, not motivation)"),
    ("bridge_is_intrinsic_not_incentivised", "EV-2 the bridge depends on a cash/credit incentive (2026 referred users retain worse than organic, -2% at 90 days in the source's table; incentive signups are the inverted quality signal)"),
    # EV-3 measurement
    ("impression_to_signup_tracked", "EV-3 impression-to-signup is not tracked (of non-users who interact with the output, the share who sign up; benchmarks 1-3% average, 3-7% strong, 7%+ exceptional)"),
    ("organic_k_computed_from_chain", "EV-3 organic K is not computed from the chain (artifacts per user per month x non-user exposures per artifact x impression-to-signup; an invites-based K describes a different loop)"),
    ("embedded_k_separated_from_referral_and_paid", "EV-3 embedded K is blended with referral-program or paid acquisition (the three loops have different conversion and retention; blended, none of them can be read)"),
    ("cycle_time_tracked", "EV-3 cycle time is not tracked (days from one cohort's exposure to the next cohort's; growth compounds on cycle count, not volume -- a 30-day cycle compounds 12 times a year, a 90-day cycle 4)"),
    # EV-4 honesty and quality
    ("referred_retention_measured_not_assumed", "EV-4 the retention of users arriving through artifacts is not compared with organic (the old assumption 'referred retain better' inverted by 2026; measure it, never assert it)"),
    ("loop_read_per_cohort_two_cohorts", "EV-4 the loop is not read per cohort across at least two cohorts before scaling (a single strong week is a campaign; a coefficient that holds on a repeat cycle is a loop)"),
    ("artifact_has_standalone_recipient_value", "EV-4 the artifact has no standalone value for the recipient before signup (the recipient must get something real from the output itself; an artifact that is only an ad produces exposure without motivation)"),
    # EV-5 own rules
    ("rewards_if_any_paid_on_conversion_only", "EV-5 a reward, if any exists alongside, is paid on the share/send rather than on a qualified conversion (paying for forwarded links buys accounts that do not stay)"),
    ("outside_equals_inside_for_artifact", "EV-5 what the artifact shows a non-user is not what the app actually contains (an output that promises words or experiences the product does not have is a lie under the house rule, and it poisons the bridge)"),
]

def check(d):
    return [msg for key, msg in CHECKS if not d.get(key)]

def main():
    d = json.load(open(sys.argv[1]))
    fails = check(d)
    for f in fails:
        print("FAIL", f)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(CHECKS) - len(fails)}/{len(CHECKS)} checks passed, {len(fails)} fails)")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
