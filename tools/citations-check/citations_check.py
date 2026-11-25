#!/usr/bin/env python3
"""citations-check: deterministic gate for the GROUNDED CITATIONS surface
(answers generated from source documents carry structured, verifiable
citations back to the exact passages relied on).
Stdlib only, offline.
Canonical source (read in full 2026-11-18):
- Anthropic Claude Platform Docs "Citations"
  https://platform.claude.com/docs/en/build-with-claude/citations
  (184 lines read in full): citations are enabled per document with
  citations.enabled=true and must be enabled on ALL or NONE of the
  documents in a request; all active models support citations; only
  text citations (no image citations). Documents are chunked to define
  citation granularity: PDFs and plain text are sentence-chunked,
  custom content documents use the supplied blocks as-is. Citation
  locations: PDF = page range (1-indexed), plain text = character
  range (0-indexed, exclusive end), custom content = block index range
  (0-indexed, exclusive end); document indices are 0-indexed across all
  documents in the request. Only a document's source content is
  citable; title and context are passed to the model but never cited.
  Scanned PDFs with no extractable text are not citable. cited_text
  does not count toward output tokens, nor toward input tokens when
  passed back in later turns; enabling citations slightly increases
  input tokens (system prompt + chunking). Citations compose with
  prompt caching, token counting and batch processing: cache the
  source documents with cache_control on the document blocks (the
  generated citation blocks themselves cannot be cached). For
  structured extraction, prompt for one line per field and parse the
  lines attaching each block's citations; prompts that ask for only
  JSON can return few or no citations; the API does not guarantee a
  value or a citation for any field, so check each one. In streaming,
  citations arrive as citations_delta deltas inside content_block_delta
  events, one citation at a time.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CI-0 the grounded-citations surface is not recorded as a decided surface - which answers must be verifiable against sources is left to habit and prose source labels, not a decision")
    if not dec.get("owner_recorded"): f.append("CI-0 no owner is recorded for citation correctness (coverage, mapping, overstated claims) - an answer with a wrong or missing citation has no accountable reader")
    if not dec.get("grounded_surfaces_inventoried"): f.append("CI-0 there is no inventory of the surfaces that answer from documents or records (research answers, eval judgements, user-facing explanations) - citations cannot be required where the surfaces are indistinguishable")
    en=d.get("enablement") or {}
    if not en.get("citations_enabled_on_all_documents"): f.append("CI-1 citations are not enabled on all documents of a request - the API requires all-or-none per request, so partial enablement errors or silently drops grounding on the unenclosed documents")
    if not en.get("document_type_chosen_per_source"): f.append("CI-1 the document type is not chosen per source (plain text / PDF / custom content) - the type fixes both chunking and the citation location format (character range, page range, block range), so an unchosen type makes locations uninterpretable")
    if not en.get("granularity_chosen_deliberately"): f.append("CI-1 citation granularity is not chosen deliberately (sentence chunking for plain text and PDFs versus caller-supplied blocks for custom content) - granularity decides whether a citation points at a sentence or at a whole supplied chunk")
    cor=d.get("correctness") or {}
    if not cor.get("title_and_context_not_treated_as_citable"): f.append("CI-2 title and context are treated as citable evidence - they are passed to the model but are never part of the citable source content, so a citation can never support a claim that rests on them")
    if not cor.get("non_citable_content_excluded"): f.append("CI-2 non-citable content is not excluded upstream (scanned PDFs with no extractable text layer, images inside PDFs) - such content can be answered from but never cited, which manufactures unverifiable claims")
    if not cor.get("structured_output_conflict_handled"): f.append("CI-2 the conflict with structured output is not handled - prompts that demand only JSON can return few or no citations; grounded extraction needs the one-line-per-field pattern with citations parsed and attached in code, or a separate formatting pass")
    pre=d.get("preservation") or {}
    if not pre.get("response_blocks_preserved_not_flattened"): f.append("CI-3 response text blocks and their citation objects are not preserved - flattening the answer into one string destroys the claim-to-passage mapping the feature exists to produce")
    if not pre.get("document_identity_mapped_by_application"): f.append("CI-3 returned document indices are not mapped by the application to the exact source records and versions supplied in that request - a citation that cannot be resolved to a fixed source version silently points at rewritten material, and model-invented URLs are not a substitute")
    if not pre.get("cited_text_token_economics_accounted"): f.append("CI-3 the token economics are not accounted for (enabling citations slightly raises input tokens; cited_text is free in output and free again when passed back) - budgets drawn without this misprice grounded answers in both directions")
    ver=d.get("verification") or {}
    if not ver.get("citation_coverage_checked"): f.append("CI-4 citation coverage is not checked per claim or extracted field - the API does not guarantee a value or a citation, so an unchecked answer can carry unsupported claims wearing a cited format")
    if not ver.get("absent_or_conflicting_evidence_handled"): f.append("CI-4 absent or conflicting evidence is not handled by rule (state that the supplied material does not establish the answer instead of filling the gap) - grounded answering fails exactly where the sources run out")
    if not ver.get("citation_quality_evaluated"): f.append("CI-4 citation quality is not evaluated on the team's own corpus (a cited passage can still be overstated by the surrounding claim) - presence of citations is not accuracy, and unmeasured grounding is a label, not evidence")
    ops=d.get("operations") or {}
    if not ops.get("caching_applied_to_source_documents"): f.append("CI-5 prompt caching is not applied to the source documents (cache_control on the document blocks) - the citation blocks cannot be cached, so re-sending the same corpus at full input price is the avoidable default")
    if not ops.get("streaming_citations_delta_handled"): f.append("CI-5 streaming citation delivery is not handled (citations_delta inside content_block_delta, one citation at a time) - a streaming surface that ignores the delta type drops citations between the API and the reader")
    if not ops.get("citation_events_logged_with_source_version"): f.append("CI-5 citation events are not logged with the source document identity and version - a challenged answer cannot be re-verified later against the material it actually relied on")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
