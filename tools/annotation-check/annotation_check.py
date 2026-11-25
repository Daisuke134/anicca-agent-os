#!/usr/bin/env python3
"""annotation-check: deterministic gate for the HUMAN ANNOTATION /
LABEL QUALITY surface (who labels LLM outputs, how agreement is
measured, and how disagreements become rubric improvements).
Stdlib only, offline, free.
Canonical source (read in full 2026-11-18, Hamel Husain, AI Evals FAQ,
"How many people should annotate my LLM outputs?", 2025-05-31,
updated 2026-09-01):
https://hamel.dev/blog/posts/evals-faq/how-many-people-should-annotate-my-llm-outputs.html
- For most small to medium-sized companies, appointing a single domain
  expert as a "benevolent dictator" is the most effective approach:
  the definitive voice on quality standards (e.g. a psychologist for
  a mental health chatbot). A single expert eliminates annotation
  conflicts; needing five experts to judge one interaction is a sign
  the product scope might be too broad.
- Larger / multi-domain organisations may need multiple annotators;
  then measure agreement with Cohen's Kappa, which accounts for
  agreement beyond chance. Even then, a single expert is often enough.
- Resolve disagreements by process, not by vote: annotators label the
  same examples independently BEFORE discussing; measure agreement and
  collect the differing cases; in an alignment session ask which part
  of the rubric caused the disagreement and what rule would make the
  next decision clear; update the rubric with a definition, rule or
  example covering the disputed case; relabel affected examples; if
  disagreement persists, a domain expert makes the final decision and
  the reason is recorded.
- Start with a benevolent dictator whenever feasible. Only add
  complexity when absolutely necessary.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("HA-0 human annotation / label quality is not recorded as a decided surface - who labels, and whose label wins, is decided ad hoc per eval and no gold label can be trusted back to a process")
    if not dec.get("owner_recorded"): f.append("HA-0 no single annotation owner (benevolent dictator) is recorded - when labels conflict there is no definitive voice on quality standards")
    if not dec.get("canonical_source_recorded"): f.append("HA-0 the canonical source is not recorded (Hamel Evals FAQ: single domain expert as benevolent dictator by default, Cohen's Kappa when multiple annotators are used) - every labelling effort invents its own rule")
    mod=d.get("annotator_model") or {}
    if not mod.get("single_dictator_default_or_justified_multiple"): f.append("HA-1 the annotator model is not the recorded default (one domain expert as benevolent dictator, multiple annotators only with a recorded multi-domain / multi-culture justification) - labelling is either ownerless or committee-based by accident")
    if not mod.get("annotator_is_domain_expert"): f.append("HA-1 the annotator is not recorded as a domain expert for the product's domain (e.g. a psychologist for a mental-health product) - labels come from whoever is available, not from the judgment the product depends on")
    if not mod.get("scope_breadth_checked"): f.append("HA-1 scope breadth is not checked against annotator need (Hamel: needing five subject-matter experts to judge one interaction signals the product scope is too broad) - an over-broad scope is absorbed as labelling complexity instead of being narrowed")
    ind=d.get("independence") or {}
    if not ind.get("label_independently_before_discussion"): f.append("HA-2 annotators do not label independently before any discussion (or the single-annotator case is not recorded as such) - early discussion anchors labels and measured agreement no longer means independent judgment")
    if not ind.get("same_examples_overlap_for_agreement"): f.append("HA-2 annotators do not label an overlapping set of the same examples - with no shared items, agreement cannot be measured and disagreement cases cannot be collected")
    if not ind.get("labels_recorded_with_rubric_version"): f.append("HA-2 labels are not recorded together with the rubric version that produced them - after a rubric change, old and new labels mix silently and no label set can be reproduced")
    agr=d.get("agreement") or {}
    if not agr.get("agreement_measured_with_kappa"): f.append("HA-3 agreement is not measured with a chance-corrected metric (Cohen's Kappa for two annotators) when more than one annotator labels - raw percent agreement flatters the labels because chance agreement is never subtracted")
    if not agr.get("disagreement_cases_collected"): f.append("HA-3 the cases where labels differ are not collected as a set - disagreements, the highest-value rubric evidence, are resolved informally and lost")
    if not agr.get("agreement_result_recorded_per_round"): f.append("HA-3 the agreement result is not recorded per labelling round - a rubric or annotator change cannot be shown to have improved (or worsened) label consistency")
    res=d.get("resolution") or {}
    if not res.get("alignment_session_identifies_rubric_cause"): f.append("HA-4 disagreements are not worked in an alignment session that asks which part of the rubric caused each disagreement and what rule would make the next decision clear - the same disagreement recurs every round")
    if not res.get("rubric_updated_and_affected_relabeled"): f.append("HA-4 the rubric is not updated with a definition, rule or example covering disputed cases, and affected examples are not relabelled - the label set stays internally inconsistent under the new understanding")
    if not res.get("expert_final_decision_with_reason"): f.append("HA-4 persistent disagreements are not closed by a domain expert's final decision with the reason recorded - unresolved labels are either dropped silently or decided by vote / seniority without a trace")
    evo=d.get("evolution") or {}
    if not evo.get("labels_become_gold_or_eval_cases"): f.append("HA-5 human labels do not become a versioned gold set / eval cases - the most expensive judgment the team produces is spent once and cannot calibrate judges or regression suites afterwards")
    if not evo.get("fresh_traces_relabeled_on_cadence"): f.append("HA-5 labelling is not repeated on fresh traces on a recorded cadence (product, rubric and failure modes drift) - the gold set ages into a picture of a product that no longer exists")
    if not evo.get("complexity_added_only_when_necessary"): f.append("HA-5 annotation complexity is not governed by the recorded rule 'start with a benevolent dictator, add annotators / process only when absolutely necessary' - process grows by accumulation and slows every eval that depends on labels")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
