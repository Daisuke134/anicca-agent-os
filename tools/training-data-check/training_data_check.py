#!/usr/bin/env python3
"""training-data-check: deterministic gate for the TRAINING DATA CURATION
surface (post-training / fine-tuning datasets built from own sources:
logs, conversations, traces, expert answers). Stdlib only, offline, free.
Canonical source (read 2026-11-17):
- Sandeep Belgavi, "Training Data Curation Pipeline, in depth"
  https://www.aicassindra.com/blogs/slm/training_data_curation.html
  A fine-tuning dataset is a build artefact, not a folder of cleaned
  files. Guarantees: one canonical schema the chat template accepts;
  every record legal to train on, no personal data or secrets;
  near-identical prompts do not dominate; every assistant turn worth
  imitating; no evaluation prompt or paraphrase in training. Pipeline
  is deterministic and explainable: content-addressed record ids, a
  manifest per stage (kept ids + code/parameter hash), an append-only
  drop ledger (a stage suddenly dropping 40% of one source is a bug or
  an upstream format change). Stages: (1) normalise through the
  trainer's real template, reject records not ending in an assistant
  turn or exceeding the token budget, rendered text must round-trip;
  (2) layered privacy/secrets detection, typed placeholders numbered
  consistently, drop when the sensitive content is the point, licence
  basis recorded per source; (3) deduplicate prompts not just records:
  cluster on the user side (MinHash/LSH), keep 2-3 best per cluster,
  record cluster id on every kept record; (4) label quality cheapest
  first: rules, executable checks, model judge with a written rubric
  (store the score; rubric/judge/threshold versioned in the manifest),
  stratified human audit of a few hundred judged records per release;
  (5) coverage: taxonomy tags, caps and floors per bucket, under-filled
  buckets become data requests not 10x upsampling; (6) leak-free
  splits: split by cluster hash (never random), decontaminate against
  every reported evaluation set (long n-grams; cluster with eval
  prompts for small high-stakes sets), freeze the evaluation split.
  Curation decisions are experiments: change one thing, fine-tune the
  same base/recipe, compare on the frozen split, log both manifest
  hashes, scores and the decision.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("TD-0 the training-data curation surface is not recorded as a decided surface - datasets are assembled ad hoc per run and no release can be compared to another")
    if not dec.get("owner_recorded"): f.append("TD-0 no single owner is recorded for training data curation - when a run disappoints, nobody owns the data cause (the source: when a fine-tuned small model disappoints, the data is a more common cause than the learning rate)")
    if not dec.get("canonical_source_recorded"): f.append("TD-0 the canonical source is not recorded (Belgavi curation pipeline) - every run invents its own cleaning steps")
    pipe=d.get("pipeline") or {}
    if not pipe.get("canonical_schema_and_content_addressed_ids"): f.append("TD-1 records are not in one canonical schema with content-addressed ids - exact duplicates do not collapse automatically and splits/drop decisions keyed on row numbers shift when a source changes")
    if not pipe.get("deterministic_stages_with_manifests"): f.append("TD-1 stages are not deterministic pure functions writing manifests (kept ids + code/parameter hash) - the same inputs do not reproduce the same dataset, so a curation change cannot be measured")
    if not pipe.get("drop_ledger_with_reasons"): f.append("TD-1 there is no append-only drop ledger (id, stage, reason, source) - no dropped record can be explained, and a stage silently dropping 40% of one source is never noticed")
    norm=d.get("normalise_privacy") or {}
    if not norm.get("normalised_through_real_template"): f.append("TD-2 records are not normalised through the trainer's real chat template with round-trip check, assistant-turn ending and token-budget fit - templates silently drop system turns and right-truncation removes the answer, the only part that carries loss")
    if not norm.get("layered_privacy_and_secrets_with_placeholders"): f.append("TD-2 privacy/secrets screening is not layered (patterns, named entities, secrets scanner) with consistent typed placeholders and drop-when-sensitive-is-the-point - a fine-tuned model can repeat real names, emails, account ids and tokens it was trained on")
    if not norm.get("licence_basis_per_source"): f.append("TD-2 no licence / training-use basis is recorded per source - records without a basis belong in the drop ledger, not in a release")
    ded=d.get("dedup_quality") or {}
    if not ded.get("prompt_level_near_dedup_clustering"): f.append("TD-3 deduplication is exact-only or record-level, not prompt-level near-duplicate clustering on the user side - the same question asked thousands of times dominates the mix and wastes training steps on one behaviour")
    if not ded.get("keep_policy_and_cluster_id_recorded"): f.append("TD-3 there is no keep policy (2-3 best members per cluster) and no cluster id recorded on kept records - either variety is destroyed or dominance remains, and the split stage has nothing to split by")
    if not ded.get("label_quality_checks_with_scores"): f.append("TD-3 label (assistant-turn) quality is not checked cheapest-first (rules, executable checks, rubric-scored model judge with the score stored and rubric/judge/threshold versioned) - macros, escalations and wrong answers are trained as behaviour worth imitating")
    cov=d.get("coverage_splits") or {}
    if not cov.get("human_audit_of_judge_per_release"): f.append("TD-4 the judge is never audited by humans on a stratified sample per release - judges drift with prompt changes and favour long confident replies, so release comparisons measure judge drift, not data")
    if not cov.get("coverage_taxonomy_caps_floors"): f.append("TD-4 records are not tagged with a taxonomy and balanced with caps and floors per bucket - the mix reflects what happened to be collected, one intent holds a third of the data, and under-filled buckets get upsampled into verbatim memorisation instead of becoming data requests")
    if not cov.get("cluster_level_split_no_random"): f.append("TD-4 splits are random or row-level instead of by cluster hash - near-duplicates sit on both sides and the evaluation score measures memorisation")
    evo=d.get("decontamination_evolution") or {}
    if not evo.get("decontaminated_against_all_eval_sets"): f.append("TD-5 training data is not decontaminated against every evaluation set that gets reported (long n-gram index; cluster-level drop for small high-stakes sets) - benchmark prompts or paraphrases in training make the reported score mean nothing")
    if not evo.get("frozen_eval_split"): f.append("TD-5 the evaluation split is not frozen and versioned - if it changes between releases, scores stop being comparable and new material must go into a new versioned set")
    if not evo.get("one_change_ablation_log"): f.append("TD-5 curation decisions are not tested as one-change ablations (same base, same recipe, previous release vs one change, frozen split, both manifest hashes, scores and decision logged) - thresholds that look reasonable stay unmeasured guesses")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
