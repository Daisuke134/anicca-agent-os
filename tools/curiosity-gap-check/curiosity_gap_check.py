#!/usr/bin/env python3
"""curiosity-gap-check: deterministic gate for information-gap (curiosity) design.
Stdlib only, offline, free.
Primary sources (read via browser.search this run, 2026-11-25):
- Loewenstein (1994) Psychol Bull 116(1):75-98, doi:10.1037/0033-2909.116.1.75
  https://psycnet.apa.org:443/doi/10.1037/0033-2909.116.1.75 -- curiosity as
  cognitively induced deprivation from a perceived gap in knowledge. THEORY
  paper: no new data; a hypothesis generator, not an experiment.
- Kang et al. (2009) Psychol Sci 20(8):963-973 -- curiosity highest at
  moderate confidence (half-known), tracked caudate reward activity; people
  spent scarce tokens/waiting time for answers; higher curiosity correlated
  with better recall of surprising answers 1-2 weeks later. Lab trivia,
  correlational within subject.
Boundary: peak-end-check owns episode memory; reactance-check owns freedom
threat; this gate owns only the opened knowledge gap: is it specific,
closable, honestly closed, and measured at closure (not just at open).
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys
def check(d):
    f=[]
    inv=d.get("inventory") or {}
    if not inv.get("gaps_inventoried_per_surface"): f.append("CG-0 open gaps are not inventoried per surface (notification/home/onboarding/content)")
    if not inv.get("gap_is_specific_question"): f.append("CG-0 the gap is not a specific question the user could state (vague teasing is not an information gap)")
    if not inv.get("partial_knowledge_present"): f.append("CG-0 partial knowledge is not established first (Kang: curiosity peaks at moderate confidence / half-known; a gap the user cannot frame does not pull)")
    des=d.get("design") or {}
    if not des.get("gap_opened_before_answer"): f.append("CG-1 no gap is opened before the answer is given (answer-first surfaces get no curiosity pull)")
    if not des.get("answer_exists_and_closable"): f.append("CG-1 the promised answer does not exist yet or has no scheduled closure (an unclosable gap is a broken promise)")
    if not des.get("closure_distance_honest"): f.append("CG-1 the distance to closure is not honestly signalled (Loewenstein: intensity tracks proximity to the answer; fake proximity is clickbait)")
    pro=d.get("prohibitions") or {}
    if pro.get("payoff_unrelated_or_absent"): f.append("CG-2 the payoff is absent or unrelated to the gap that was opened (clickbait form)")
    if pro.get("gap_never_closed"): f.append("CG-2 a gap is left permanently open (deprivation without resolution trains ignoring, not return)")
    if pro.get("fabricated_mystery"): f.append("CG-2 the mystery is fabricated (the 'answer' was invented to manufacture a gap)")
    mea=d.get("measurement") or {}
    if not mea.get("open_and_closure_measured_separately"): f.append("CG-3 opening (tap/open) and closure (answer reached) are not measured separately")
    if not mea.get("post_answer_disappointment_measured"): f.append("CG-3 post-answer disappointment / drop-off is not measured (Loewenstein: satisfaction often disappoints; closure quality is the retention variable)")
    if not mea.get("counts_recorded_not_rates_only"): f.append("CG-3 counts are not recorded (gaps opened, closed, abandoned) -- rates alone hide volume effects")
    cit=d.get("citation") or {}
    if not cit.get("source_numbers_cited_with_design"): f.append("CG-4 source claims are not cited with their design (1994 theory paper vs 2009 lab trivia fMRI/behaviour, correlational)")
    if cit.get("lab_effect_used_as_product_promise"): f.append("CG-4 a lab trivia curiosity effect is used as a product/CTR promise")
    if not cit.get("revenue_chain_recorded"): f.append("CG-4 the revenue chain is not recorded (gap opened -> closure reached -> value delivered -> return/conversion, each measured locally)")
    eth=d.get("ethics") or {}
    if eth.get("paywall_blocks_self_generated_answer"): f.append("CG-5 a paywall blocks the answer to a curiosity gap the product itself manufactured, without that being disclosed before the gap was opened")
    if not eth.get("user_can_ignore_gap_without_penalty"): f.append("CG-5 ignoring an open gap is penalised (streak loss, nagging escalation) -- deprivation pressure, not curiosity")
    if not eth.get("review_cadence_recorded"): f.append("CG-5 no review cadence is recorded for re-auditing open gaps when surfaces change")
    return f
def main():
    d=json.load(open(sys.argv[1])); fails=check(d)
    for x in fails: print("FAIL:",x)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
