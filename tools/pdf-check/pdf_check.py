#!/usr/bin/env python3
"""pdf-check: deterministic gate for the PDF / document-input surface
(how PDFs are sent to the model - source type, request limits, per-page
text+visual token cost, placement, page referencing, quality, caching,
batch scale and vision-shared limitations - is decided, not left to
whatever each call happens to attach).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "PDF support"
  https://platform.claude.com/docs/en/build-with-claude/pdf-support
  (159 lines read in full): PDFs are sent in a document content block
  via three source types - URL reference, base64 embedded in the
  request, or a file_id from the Files API (use Files API for large
  PDFs or repeated use, to keep payloads small and avoid encoding
  overhead). Requirements: max request size 128 MB on the first-party
  API (entire payload, including other content), max 600 pages per
  request (100 when context window is under 1M tokens), standard PDF
  only - no passwords / encryption. All active models support it.
  How it works: each page is converted to an image and its text is
  extracted alongside; the model analyses both, so charts/diagrams are
  readable as visual content. Cost: no extra PDF fee; text typically
  1,500-3,000 tokens per page by density, plus each page image at most
  1,568 visual tokens (page images are fitted to the Standard
  resolution tier on every model); use token counting to estimate a
  specific PDF. Best practices: place PDFs before text, use standard
  fonts, clear legible text, rotate pages upright, refer to pages by
  logical (PDF viewer) page numbers, split large PDFs into chunks
  when needed, enable prompt caching for repeated analysis. Scale:
  combine with prompt caching for repeated queries and with the
  Message Batches API for high-volume asynchronous processing; tools
  can extract specific information for use as tool inputs. Because
  PDF support relies on vision, it shares vision limitations.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("PD-0 the PDF surface is not recorded as a decided surface - which documents are sent to the model, in what form and at what cost is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("PD-0 no owner is recorded for PDF correctness (source choice, limits, cost, verification of extracted claims) - a misread chart or an over-limit request has no accountable reader")
    if not dec.get("pdf_surfaces_inventoried"): f.append("PD-0 there is no inventory of the PDF surfaces (paper reading, report/chart extraction, legal/contract reading, user-supplied documents) - cost and verification cannot be required where the surfaces are indistinguishable")
    src=d.get("sources") or {}
    if not src.get("source_type_chosen_deliberately"): f.append("PD-1 the PDF source type is not chosen deliberately per surface (URL reference, base64 embedded, or Files API file_id - upload once for large PDFs or repeated use to keep payloads small and avoid re-encoding overhead) - resending base64 for the same paper on every read pays payload and encoding cost for a reference that already exists")
    if not src.get("requirements_validated"): f.append("PD-1 PDF requirements are not validated before sending (128 MB maximum for the entire request payload on the first-party API including other content; 600 pages per request, 100 when the context window is under 1M tokens; standard PDF only) - the limit is learned from a failed request in production instead of from the design")
    if not src.get("encrypted_excluded"): f.append("PD-1 password-protected / encrypted PDFs are not excluded or routed before sending (only standard, unencrypted PDFs are supported) - a locked document fails or is silently unread and its contents are reported as if seen")
    cost=d.get("cost") or {}
    if not cost.get("token_cost_estimated"): f.append("PD-2 the token cost of a PDF is not estimated before sending with token counting (typically 1,500-3,000 text tokens per page by density plus at most 1,568 visual tokens per page image) - a 100-page report enters the bill as an unknown, and cost per successful task cannot be computed for document work")
    if not cost.get("page_image_tier_accounted"): f.append("PD-2 the per-page image cost is not accounted as fitted to the Standard resolution tier on every model (at most 1,568 visual tokens per page, no additional PDF fee) - page-image cost is either double-counted at high-resolution rates or omitted entirely")
    if not cost.get("splitting_decided"): f.append("PD-2 splitting large PDFs into chunks is not decided (split when needed instead of sending the whole document) - a long document crowds out the question, the evidence and the answer in one window, and the pages that mattered are diluted by the pages that did not")
    place=d.get("placement") or {}
    if not place.get("pdf_before_text"): f.append("PD-3 PDFs are not placed before the text in requests (documents first, then the instruction/question) - the model reads the question before the evidence it is about, against the documented best practice")
    if not place.get("logical_page_numbers_used"): f.append("PD-3 prompts do not refer to pages by their logical page numbers (the numbers shown in the PDF viewer) - a claim cited to 'page 12' cannot be checked when the prompt and the viewer count pages differently")
    if not place.get("caching_for_repeated_analysis"): f.append("PD-3 prompt caching is not used for repeated analysis of the same PDF (cache the document so repeated queries do not re-pay full processing) - every follow-up question about the same paper re-buys the whole document")
    qual=d.get("quality") or {}
    if not qual.get("fonts_and_legibility_checked"): f.append("PD-4 standard fonts and clear, legible text are not checked before relying on a reading (non-standard fonts and illegible text degrade extraction) - a verdict on a garbled extraction is a verdict on the font, not on the document")
    if not qual.get("orientation_upright"): f.append("PD-4 pages are not rotated to proper upright orientation before sending - rotated pages are a known source of vision error, and a sideways table is read as evidence anyway")
    if not qual.get("interpretations_verified"): f.append("PD-4 PDF interpretations are not reviewed and verified before they are relied on (PDF support relies on vision, so its limitations apply - charts, tables and diagrams are read from page images and can be misread) - an unverified extracted number ships with the model's confidence and none of its caveats")
    ops=d.get("operations") or {}
    if not ops.get("batch_decided_for_high_volume"): f.append("PD-5 high-volume PDF processing is not decided through the Message Batches API (asynchronous batch processing for many documents in one request, with progress checked and results retrieved at completion) - volume document work runs synchronously at interactive cost and latency by default")
    if not ops.get("tool_extraction_decided"): f.append("PD-5 tool-based extraction is not decided (tools can extract specific information from documents for use as tool inputs, instead of free-text answers for structured needs) - structured data pulled from PDFs is parsed out of prose by hand where a tool contract was available")
    if not ops.get("limits_reverified_on_model_change"): f.append("PD-5 PDF limits are not re-verified when models or context windows change (the page cap is 600, but 100 when the context window is under 1M tokens, and request-size limits vary by platform) - a model switch silently halves the page budget and the first long document learns it by failing")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
