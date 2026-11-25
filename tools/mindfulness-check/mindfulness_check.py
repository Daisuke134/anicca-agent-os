#!/usr/bin/env python3
"""mindfulness-check: deterministic gate. Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Keng, Smoski & Robins (2011) Clin Psychol Rev 31:1041-1056, DOI 10.1016/j.cpr.2011.04.006 -- narrative review: mindfulness = present-moment, nonjudgmental attention; correlational + multi-week intervention (MBSR/MBCT) + lab induction evidence kept separate.
- Gal et al. (2021) mindfulness meditation apps meta-analysis -- 34 RCTs, N=7566; post-test stress g=0.46, anxiety g=0.28, depression g=0.33, psychological well-being g=0.29; distress g=0.10 n.s., general well-being g=0.14 n.s.; uncertain risk of bias, heterogeneity.
- Linardon et al. (2023) Clin Psychol Rev 107:102370 -- 43 RCTs; depression g=0.24 (N=5852), anxiety g=0.28 (N=6082) vs controls; vs active therapeutic comparisons g=-0.15 / g=0.10, n.s. (few studies).
- Sommers-Spijkerman et al. / JMIR Ment Health 2021 online MBI meta-analysis -- 97 RCTs, 125 comparisons; depression g=0.34, stress g=0.44, mindfulness g=0.40, anxiety g=0.26; inactive controls yielded larger effects; trim-and-fill adjusted mindfulness effect g=-0.04.
Boundary: mindfulness owns ONLY present-moment nonjudgmental attention practice (anchor, noticing wandering, gentle return), distinct from relaxation/sleep, thought suppression/empty-mind, acceptance+values action (acceptance-check), and savoring (savoring-check). Evidence is mostly multi-week programs or app programs over weeks vs mostly inactive controls; a single prompt is not that dose.
Exit 0=PASS, 1=FAIL."""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("mindfulness_surfaces_inventoried"): f.append("MF-0 mindfulness surfaces are not inventoried per app (any prompt/session that asks a user to attend to the present moment, breath, body or sounds)")
    if not inv.get("mindfulness_defined_as_present_moment_nonjudgmental_attention_distinct_from_relaxation_suppression_empty_mind"): f.append("MF-0 mindfulness is not defined as present-moment nonjudgmental attention, distinct from relaxation, sleep, thought suppression and emptying the mind")
    if not inv.get("evidence_scope_and_control_caveat_audited"): f.append("MF-0 evidence scope/control caveat is not audited (effects are from multi-week/app programs vs mostly inactive controls; vs active therapeutic comparisons effects were n.s. in Linardon 2023; trim-and-fill mindfulness g=-0.04 in JMIR 2021)")
    des=d.get("design") or {}
    if not des.get("anchor_and_gentle_return_instruction_present"): f.append("MF-1 no anchor + gentle-return instruction (choose an anchor, notice wandering without judgment, return -- wandering is the rep, not a failure)")
    if not des.get("dose_and_repetition_recorded_not_single_prompt_claim"): f.append("MF-1 dose/repetition is not recorded (session length, sessions per week, program length -- a single prompt must not be presented as the tested dose)")
    if not des.get("user_can_stop_and_alternative_anchor_offered"): f.append("MF-1 user cannot stop / no alternative offered (eyes-open, sound or movement anchor and a stop path; breath/body focus is not safe or comfortable for everyone)")
    pro=d.get("prohibitions") or {}
    if pro.get("relaxation_or_empty_mind_counted_as_mindfulness"): f.append("MF-2 relaxation, sleepiness or an empty mind is counted as mindfulness (calm is a possible by-product, not the practice or its measure)")
    if pro.get("mind_wandering_or_noncompletion_shamed_or_scored_as_failure"): f.append("MF-2 mind-wandering or non-completion is shamed or scored as failure (noticing wandering is the mechanism; scoring it as failure teaches suppression)")
    if pro.get("distress_moment_used_to_paywall_the_practice"): f.append("MF-2 the moment of distress is used to paywall the practice (the user is asked to pay to continue attending -- core practice must precede any paywall)")
    mea=d.get("measurement") or {}
    if not mea.get("counts_recorded_not_rates_only"): f.append("MF-3 counts are not recorded (sessions offered, started, completed, stopped early, anchor used) -- rates alone hide whether any practice happened")
    if not mea.get("attention_measured_separately_from_calm_only"): f.append("MF-3 attention/practice is not measured separately from calm-only self-report (record practice completion and a follow-up functioning/stress read; 'felt calmer' alone does not show mindfulness was practised)")
    if not mea.get("outcomes_measured_at_followup_separately_from_immediate_calm"): f.append("MF-3 outcomes are not measured at a follow-up window separately from immediate post-session calm (trial effects are post-program and follow-up reads, not a 1-minute afterglow)")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("MF-4 source claims are not cited with their design (Gal 2021: 34 RCTs N=7566 stress g=0.46 depression g=0.33; Linardon 2023: 43 RCTs depression g=0.24 anxiety g=0.28, vs active comparisons n.s.)")
    if cit.get("effect_claimed_as_cure_or_single_prompt_equivalent_to_program"): f.append("MF-4 the effect is claimed as a cure, or a single prompt/session is claimed equivalent to a multi-week mindfulness program (no such evidence)")
    if not cit.get("revenue_chain_recorded"): f.append("MF-4 the revenue chain is not recorded (practice offered -> actually practised with counts -> follow-up stress/functioning read locally -> retention read; no chain may be asserted from the meta-analyses alone)")
    eth=d.get("ethics") or {}
    if eth.get("clinical_claim_made"): f.append("MF-5 a clinical claim is made (treats/cures anxiety/depression) -- this is program-trial evidence, not an app claim")
    if not eth.get("core_mindfulness_available_to_free_users"): f.append("MF-5 core mindfulness practice is not available to free users")
    if not eth.get("review_cadence_recorded"): f.append("MF-5 no review cadence is recorded for re-auditing mindfulness surfaces")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
