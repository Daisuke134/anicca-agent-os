#!/usr/bin/env python3
"""files-check: deterministic gate for the Files API surface
(how files are uploaded once and referenced by file_id - block-type
mapping, size/storage/filename validation, workspace trust, expiration,
pagination and silent-omission reconciliation, the downloadable
distinction, generated-output capture, free operations vs token billing,
and the beta-header migration / audit trail - is decided, not left to
whatever each call happens to attach).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Files API"
  https://platform.claude.com/docs/en/build-with-claude/files
  (289 lines read in full): create-once, use-many-times - upload to
  Anthropic storage, receive a file_id, reference it in Messages
  requests instead of re-uploading; download files created by skills
  or the code execution tool; manage with list / retrieve / delete.
  Block mapping: PDF and text/plain -> document, images
  (jpeg/png/gif/webp) -> image, datasets/others -> container_upload
  for code execution. Unsupported document types (.docx/.xlsx) are
  converted to plain text and included directly; .csv/.md may be read
  inline or uploaded as text/plain. Limits: 500 MB per file, 1 TB
  total per organization, about 500 requests/minute; all Files
  operations are free, file content in Messages is billed as input
  tokens. Lifecycle: files are scoped to their workspace - never
  accept file IDs from untrusted sources; files cannot be modified or
  renamed (upload new + delete old); files persist until deleted or
  expires_at; deletion is unrecoverable. Expiration is set once at
  upload via expires_in_seconds (3,600 to 7,776,000 = 1 hour to 90
  days) and cannot be changed; after expiry content download is 404,
  Messages references fail before inference, metadata stays readable
  up to 30 days and expired files still appear in lists (filter by
  expires_at). List is paginated (limit 20 default, max 1,000,
  next_page -> page, newest first, SDK auto-pagination) or takes up
  to 100 ids[] in one request - ids[] cannot combine with page/limit,
  always returns a single page, and silently omits IDs that do not
  resolve, so compare returned vs requested IDs. Uploaded files have
  downloadable=false and cannot be downloaded (400); only files
  created by skills / code execution can, via the file_id in the
  bash_code_execution_tool_result block; generated media carry signed
  C2PA Content Credentials. Errors: 404 not found, 400 type/block
  mismatch, 400 not downloadable, 400 exceeds context window, 400
  invalid file name (1-255 chars, no < > : " | ? * backslash slash or
  control chars 0-31), 413 file too large, 400 storage limit.
  Migration: the API is out of beta - no files-api-2025-04-14 header
  needed; removing it switches list shape to {data, next_page},
  cursors to page / ids[], expires_at always present, Content-Type
  optional; use the stable SDK namespace (client.files). Audit: the
  Compliance API Activity Feed records upload / content download /
  delete only when enabled beforehand (list and metadata reads are
  not recorded); on Claude Platform on AWS use CloudTrail instead.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("FL-0 the Files API surface is not recorded as a decided surface - which files are uploaded once and referenced by file_id, under what lifecycle and at what trust, is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("FL-0 no owner is recorded for file correctness (upload, referencing, expiration, deletion, trust) - an expired reference failing in production or an orphaned 1 TB store has no accountable reader")
    if not dec.get("file_surfaces_inventoried"): f.append("FL-0 there is no inventory of the file surfaces (repeated papers and screenshots, datasets for code execution, generated outputs to download) - the create-once saving cannot be required where the surfaces are indistinguishable")
    ref=d.get("referencing") or {}
    if not ref.get("create_once_reference_decided"): f.append("FL-1 create-once, use-many-times is not decided per surface (upload once, keep the file_id, reference it in Messages instead of re-uploading content with every request) - the same paper or screenshot is re-encoded and re-sent on every read, paying payload and encoding cost for a reference that could exist")
    if not ref.get("block_type_matched"): f.append("FL-1 the content block type is not matched to the file type (PDF and text/plain -> document, images -> image, datasets and other analysis files -> container_upload for the code execution tool) - a type/block mismatch is a 400 learned in production instead of a mapping fixed in the design")
    if not ref.get("unsupported_formats_converted"): f.append("FL-1 unsupported document formats are not routed (for example .docx and .xlsx are converted to plain text and included directly in the message; .csv and .md are read inline or uploaded explicitly as text/plain) - an unsupported file is sent as-is and fails, or its contents are reported as if seen")
    val=d.get("validation") or {}
    if not val.get("size_storage_limits_validated"): f.append("FL-2 file size and storage limits are not validated before upload (500 MB per file -> 413, 1 TB total per organization -> 400, and a referenced file must still fit the context window -> 400) - the limit is learned from a failed upload or a failed Messages request instead of from the design")
    if not val.get("filename_validated"): f.append("FL-2 file names are not validated before upload (1-255 characters, none of < > : \" | ? * backslash slash or Unicode control characters 0-31 -> 400) - a generated or user-supplied name fails the upload for a reason a pre-check would have caught")
    if not val.get("billing_and_rate_understood"): f.append("FL-2 the billing shape is not accounted (all Files operations - upload, download, list, metadata, delete - are free; file content used in Messages is priced as input tokens; file calls are rate-limited to about 500 requests per minute) - storage looks free while the repeated reads it enables are the actual bill, and bulk jobs hit an unplanned rate ceiling")
    life=d.get("lifecycle") or {}
    if not life.get("workspace_trust_enforced"): f.append("FL-3 workspace scoping and file-ID trust are not enforced (files are scoped to the workspace that uploaded them and any request in that workspace can reference them; file IDs from untrusted sources are never accepted) - a foreign or injected file_id silently becomes evidence inside a trusted request")
    if not life.get("expiration_decided"): f.append("FL-3 expiration is not decided at upload (expires_in_seconds between 3,600 and 7,776,000 - 1 hour to 90 days - is set once and cannot be changed; after expires_at, content download returns 404, a Messages reference fails before inference, metadata stays readable up to 30 days, and expired files still appear in list responses so callers filter by expires_at) - a reference dies mid-workflow with no warning, or files meant to be temporary persist forever by default")
    if not life.get("immutability_deletion_handled"): f.append("FL-3 immutability and deletion are not handled (files cannot be modified or renamed after upload - change means upload a new file and delete the old one; deleted files cannot be recovered, and may persist briefly in already-active Messages calls) - a stale file keeps being referenced as if it were the current version, and a mistaken delete has no recovery path in the design")
    ops=d.get("operations") or {}
    if not ops.get("pagination_handled"): f.append("FL-4 list pagination is not handled (each request returns up to limit files - 20 by default, at most 1,000 - newest first, following next_page as the page parameter, or via the SDK auto-pagination helpers) - an inventory or cleanup job silently sees only the first page and reports the rest as absent")
    if not ops.get("ids_omission_reconciled"): f.append("FL-4 bulk ID checks are not reconciled (up to 100 ids[] in one request, never combined with page or limit, always a single page - and an ID that does not resolve is left out of data without an error, so returned IDs must be compared against requested IDs) - a missing file is read as present because the check that should have caught it returned no error")
    if not ops.get("downloadable_distinguished"): f.append("FL-4 the downloadable distinction is not enforced (files you upload have downloadable=false and downloading one is a 400; only files created by skills or the code execution tool can be downloaded) - a pipeline waits on a download that can never succeed, or treats an uploaded original as retrievable when it is not")
    gov=d.get("governance") or {}
    if not gov.get("generated_outputs_captured"): f.append("FL-5 generated outputs are not captured by contract (the file_id of a file created by a skill or the code execution tool appears in the bash_code_execution_tool_result block of the creating response, and generated image/video/audio files carry signed C2PA Content Credentials to verify on download) - a generated chart or dataset is lost with the response that made it, and downloaded media is trusted without its credential")
    if not gov.get("beta_header_migrated"): f.append("FL-5 the beta migration is not decided (the Files API is out of beta and needs no files-api-2025-04-14 header; keeping the header keeps the beta response shapes - removing it switches list to {data, next_page}, cursors to page / ids[], makes expires_at always present and Content-Type optional, and the stable SDK namespace client.files is the default) - an integration pinned to beta shapes breaks silently the day the header or SDK namespace changes")
    if not gov.get("audit_logging_enabled"): f.append("FL-5 the audit trail is not enabled before it is relied on (with the Compliance API enabled, the Activity Feed records uploads, content downloads and deletions - list and metadata reads are not recorded - and operations that occur while it is off are never recorded and cannot be recovered; on Claude Platform on AWS, audit with CloudTrail data events instead) - the file history the team expects to reconstruct later was never written")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
