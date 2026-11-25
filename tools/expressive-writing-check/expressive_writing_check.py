#!/usr/bin/env python3
"""expressive-writing-check: deterministic gate. Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Pennebaker & Beall (1986) J Abnorm Psychol 95(3):274-281 -- 46 students, 15 min x 4 consecutive days, deepest thoughts/feelings about most traumatic experience vs trivial topics; fewer health-centre visits after.
- Frattaroli (2006) Psychol Bull 132(6):823-865, DOI 10.1037/0033-2909.132.6.823 -- 146 randomized studies, average r=.075 (approx d=0.15), small.
- Counterweight: Mogk et al. (2006) -- RCT-only (30 pooled): no significant somatic/psychological effects. Short-term distress increase after writing is expected in the paradigm.
- Protocol (Cambridge APT review of Pennebaker paradigm): 15-20 min, 3-5 occasions, confidential, no feedback, write continuously, thoughts AND feelings not facts alone.
Boundary: expressive writing owns ONLY private, time-boxed writing about a specific upsetting experience (thoughts+feelings). NOT gratitude lists (gratitude-check), BPS future writing (best-possible-self-check), generic journaling/mood tracking, or forgiveness work (forgiveness-check). Privacy is a design condition: writing read/shared/trained-on by default breaks the tested paradigm.
Exit 0=PASS, 1=FAIL."""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("expressive_writing_surfaces_inventoried"): f.append("EW-0 expressive-writing surfaces are not inventoried per app (any prompt inviting writing about an upsetting experience)")
    if not inv.get("expressive_writing_defined_as_private_timeboxed_thoughts_and_feelings_about_specific_upsetting_experience_distinct_from_journaling_gratitude_bps"): f.append("EW-0 expressive writing is not defined as private time-boxed writing of deepest thoughts AND feelings about a specific upsetting experience, distinct from generic journaling, gratitude lists and best-possible-self writing")
    if not inv.get("distress_and_privacy_risks_audited"): f.append("EW-0 surfaces have not been audited for short-term distress increase and privacy exposure (both are known paradigm features, Pennebaker & Beall 1986; Frattaroli 2006)")
    des=d.get("design") or {}
    if not des.get("dose_15_to_20_min_3_to_4_sessions_recorded"): f.append("EW-1 dose is not the tested dose (15-20 min, 3-4 sessions, recorded; a 2-minute free-write prompt is not the tested intervention)")
    if not des.get("continuous_writing_no_grammar_concern_and_may_stop"): f.append("EW-1 continuous writing without grammar/style concern, with an explicit right to stop, is not specified (protocol: keep writing until time is up, confidentiality assured, stopping permitted)")
    if not des.get("writing_private_by_default_not_read_shared_or_trained_on"): f.append("EW-1 writing is not private by default (the paradigm assures complete confidentiality and gives no feedback; reading, sharing, social posting or training on the text by default changes the intervention and inhibits disclosure)")
    pro=d.get("prohibitions") or {}
    if pro.get("distress_presented_as_proof_it_works_or_required"): f.append("EW-2 short-term distress is presented as proof it works or as required suffering (distress after writing is a common transient, unrelated to later benefit in reviews; it is never the goal)")
    if pro.get("expressive_writing_paywalled_or_upsold_at_disclosure_moment"): f.append("EW-2 the writing sessions themselves are paywalled or an upsell is placed at the disclosure moment (inserting payment into private disclosure changes the intervention)")
    if pro.get("forced_daily_streak_or_public_sharing_required"): f.append("EW-2 a forced daily streak or public/social sharing is required (the tested protocol is 3-4 sessions then stop and reassess, private; indefinite daily trauma writing is untested)")
    mea=d.get("measurement") or {}
    if not mea.get("outcomes_measured_at_followup_not_immediately_only"): f.append("EW-3 outcomes are not measured at a follow-up window (benefits in the paradigm appear over weeks-months, e.g. health-centre visits after; immediate post-writing mood is expected to worsen and cannot be the success read)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("EW-3 counts are not recorded (prompt shown, session started, minutes written, sessions completed, stopped early) -- rates alone hide whether the dose ever happened")
    if not mea.get("immediate_distress_and_later_outcomes_measured_separately"): f.append("EW-3 immediate distress and later outcomes are not measured separately (pooling them cancels the paradigm's known time course)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("EW-4 source claims are not cited with their design (Frattaroli 2006: 146 randomized studies, r=.075 approx d=0.15; Pennebaker & Beall 1986: N=46, 15 min x 4 days)")
    if cit.get("effect_claimed_as_large_cure_or_trauma_treatment"): f.append("EW-4 the effect is claimed as large, a cure, or trauma treatment (honest claim: small average benefit, r=.075, and an RCT-only meta-analysis Mogk 2006 found no significant effects -- uncertainty must be stated)")
    if not cit.get("revenue_chain_recorded"): f.append("EW-4 the revenue chain is not recorded (voluntary private protocol offered -> full dose completed -> later outcomes/return measured locally; no chain may be asserted from the meta-analysis alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("EW-5 a clinical claim is made (treats PTSD/depression) -- the evidence is a small average effect in mostly non-clinical samples; this is not a treatment")
    if not eth.get("protocol_available_to_free_users"): f.append("EW-5 the expressive-writing protocol is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("EW-5 no review cadence is recorded for re-auditing expressive-writing surfaces")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
