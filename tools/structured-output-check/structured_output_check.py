#!/usr/bin/env python3
"""structured-output-check: deterministic gate for the STRUCTURED OUTPUTS surface
(strict schema adherence vs JSON mode, schema design within the supported subset,
function calling vs response format, refusal-before-parse, incomplete/error handling,
business-rule validation beyond the schema, incompatible-input path, mistake correction,
schema quality via evals, latency/streaming, CI anti-divergence, model-support recheck,
failure-mode measurement). Stdlib only, offline.
Canonical source (read in full 2026-11-18, OpenAI, "Structured model outputs",
https://platform.openai.com/docs/guides/structured-outputs):
- Structured Outputs constrains completed, non-refusal output to the supplied JSON
  Schema; JSON mode guarantees valid JSON only, never schema adherence. Prefer
  Structured Outputs (strict: true) whenever possible. gpt-4o-2024-08-06 scored 100%
  schema compliance in OpenAI's eval vs <40% for gpt-4-0613 prompting.
- Two forms: function calling (model bridges to tools/data) vs json_schema response
  format (structure the model's reply to the user). Choose by purpose.
- Supported subset only: root must be an object (never anyOf), every field required
  (emulate optional with a null union), additionalProperties: false on every object,
  <=5000 properties, <=10 nesting levels, <=1000 enum values, 120k total schema
  string characters; some string constraints unsupported on fine-tuned models.
- Refusals do not follow the schema: the API returns a refusal field; check it
  BEFORE parsing. Incomplete responses (max_output_tokens) and API errors must be
  handled; a truncated reply is not valid output.
- The schema does not express business rules: the application still validates them.
  With user-generated input the model may hallucinate to fit the schema on unrelated
  input - the prompt must define the incompatible-input path (empty parameters or a
  specific response). Mistakes are fixed via instructions, examples, or splitting
  tasks into simpler subtasks.
- Quality: name keys clearly, give titles/descriptions to important keys, and use
  evals to determine the structure that works best. Prevent schema/type divergence
  with native SDK helpers (Pydantic / Zod) or CI rules that flag edits / generate
  the schema from type definitions. First request with a new schema carries extra
  processing latency; streaming should rely on the SDKs.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("SO-0 the structured-outputs surface is not recorded as a decided surface - which model outputs are machine-consumed, and under what contract, is left to habit")
    if not dec.get("owner_recorded"): f.append("SO-0 no structured-outputs owner is recorded - nobody is named to keep schemas, refusal handling and failure rates honest")
    if not dec.get("canonical_source_recorded"): f.append("SO-0 the canonical source is not recorded (OpenAI Structured Outputs: strict schema adherence, supported subset, refusal-before-parse, business rules beyond the schema) - every caller invents its own output contract")
    sd=d.get("schema_design") or {}
    if not sd.get("strict_mode_used_not_json_mode"): f.append("SO-1 strict Structured Outputs are not used where a schema is needed (JSON mode guarantees valid JSON only, never the fields, types or enums) - downstream code parses hope")
    if not sd.get("schema_from_types_no_divergence"): f.append("SO-1 schemas are not defined from the code's own types via SDK helpers (Pydantic / Zod) - hand-written schemas and data objects drift apart silently")
    if not sd.get("schema_within_supported_subset_and_limits"): f.append("SO-1 schemas are not kept inside the supported subset (root object, never anyOf; every field required with null unions for optional; additionalProperties false; size, nesting and enum limits) - requests fail or guarantees silently lapse")
    con=d.get("consumption") or {}
    if not con.get("form_chosen_function_calling_vs_response_format"): f.append("SO-2 the form is not chosen by purpose (function calling when the model bridges to tools/data, json_schema response format when structuring the reply to the user) - tools and replies share one accidental shape")
    if not con.get("refusal_checked_before_parsing"): f.append("SO-2 refusals are not checked before parsing (a refusal does not follow the schema and arrives as its own field) - safety refusals crash parsers or are consumed as data")
    if not con.get("incomplete_and_errors_handled"): f.append("SO-2 incomplete responses (max_output_tokens truncation) and API errors are not handled as their own cases - a cut-off reply is treated as a complete answer")
    sem=d.get("semantics") or {}
    if not sem.get("business_rules_validated_beyond_schema"): f.append("SO-3 business rules the schema cannot express are not validated in application code (right shape, wrong value passes) - schema adherence is mistaken for correctness")
    if not sem.get("incompatible_input_path_defined"): f.append("SO-3 no incompatible-input path is defined in the prompt (return empty parameters or a specific response when input cannot yield a valid answer) - the model hallucinates values to fit the schema on unrelated input")
    if not sem.get("mistakes_corrected_via_instructions_examples_subtasks"): f.append("SO-3 output mistakes are not corrected by adjusting instructions, adding examples, or splitting the task into simpler subtasks - the same wrong values recur")
    q=d.get("quality") or {}
    if not q.get("keys_named_and_described"): f.append("SO-4 schema keys are not named clearly with titles/descriptions on important keys - the model guesses at field intent the schema author never stated")
    if not q.get("evals_determine_schema_structure"): f.append("SO-4 evals are not used to determine the schema structure that works best - the contract is fixed by first draft, never measured")
    if not q.get("first_request_latency_and_streaming_handled"): f.append("SO-4 first-request schema-processing latency is not accounted for and streaming (when used) is not handled through the SDKs - latency surprises and hand-rolled stream parsing enter the critical path")
    ev=d.get("evolution") or {}
    if not ev.get("schema_changes_ci_flagged_or_generated"): f.append("SO-5 schema changes are not fenced in CI (flag edits to schema or types, or generate one from the other) - divergence is discovered in production, not in review")
    if not ev.get("model_support_reverified_on_change"): f.append("SO-5 model and subset support are not re-verified when the model or schema changes (snapshot support windows, fine-tuned-model constraint gaps) - a model swap silently downgrades the guarantee")
    if not ev.get("failure_modes_measured_and_schema_revised"): f.append("SO-5 refusal, incomplete and wrong-value rates are not measured per schema and fed back into schema/instruction revision - the failure mix is invisible, so the contract never improves")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS")
