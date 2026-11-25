#!/usr/bin/env python3
"""streaming-check: deterministic gate for the STREAMING surface
(responses delivered incrementally over SSE - transport, event and delta
handling, latency measurement, mid-stream recovery, operations - is
decided, not left to whatever the route happens to do).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Streaming messages"
  https://platform.claude.com/docs/en/build-with-claude/streaming
  (181 lines read in full): set "stream": true to receive the response
  incrementally as server-sent events. The Python and TypeScript SDKs
  offer streaming helpers (Python sync and async), the PHP SDK streams
  through createStream(), and the official SDKs are the recommended
  route - they handle streaming, accumulation and reconnection. When
  the complete Message is what is needed, the SDK can stream internally
  and return it via the accumulation helper (get_final_message()),
  identical to messages.create(); this is especially useful at large
  max_tokens values, where the SDK requires streaming to avoid HTTP
  timeouts. Event flow: message_start (a Message with empty content)
  -> per content block: content_block_start, any number of
  content_block_delta events, content_block_stop (the block index maps
  to its index in the final content array) -> one or more message_delta
  events -> message_stop. Ping events may appear anywhere. Error events
  can arrive mid-stream (an overloaded_error corresponds to HTTP 529 in
  a non-streaming context). Under the versioning policy new event types
  may be added, so unknown event types must be handled gracefully. Some
  blocks arrive whole with no deltas: redacted_thinking blocks, server
  tool results such as web_search_tool_result, and the fallback block
  at each model boundary of a server-side fallback. Delta types:
  text_delta; input_json_delta (partial JSON strings for a tool_use
  block's input - accumulate the strings and parse at
  content_block_stop, or use the SDK helpers that expose the parsed
  input incrementally; by default the API buffers each complete key and
  value, so delays between events are normal while the model works);
  thinking_delta, with a signature_delta sent just before
  content_block_stop to verify the thinking block's integrity (with
  display "omitted" the thinking delta carries an empty string and no
  thinking text streams). Error recovery: capture the partial response,
  build a continuation request and resume streaming - for Claude 4.5
  and earlier the partial response becomes the beginning of a new
  assistant message; for Claude 4.6 and later, step 2 changes: add a
  user message containing the partial response and an instruction to
  continue from where it left off. Tool use and thinking blocks cannot
  be partially recovered; resume from the most recent text block. On
  completion, handle each stop_reason value. Streaming is available on
  the Messages API for all models. The page's own next steps separate
  the surfaces: stream tool input JSON without server-side buffering
  for lower latency, and process large volumes asynchronously (batch)
  when real-time responses are not needed.
Secondary (flagged, not in the official page as fetched): the usage
token counts carried by message_delta events are cumulative (docs
mirror, read via search results 2026-11-19); fine-grained tool
streaming is switched per tool (eager_input_streaming) and can deliver
invalid or partial JSON that the caller must tolerate (AWS Bedrock
documentation of the same Anthropic capability, read via search
results 2026-11-19).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("ST-0 the streaming surface is not recorded as a decided surface - which responses arrive incrementally and which arrive whole is left to route defaults and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("ST-0 no owner is recorded for streaming correctness (event handling, latency, recovery) - a stream that stalls, drops deltas or dies mid-answer has no accountable reader")
    if not dec.get("streaming_surfaces_inventoried"): f.append("ST-0 there is no inventory of the surfaces that need streaming (user-facing delivery where first-token latency is felt, long generations, agent loops) - streaming cannot be required where the surfaces are indistinguishable from batch work")
    tr=d.get("transport") or {}
    if not tr.get("sdk_used_not_handrolled_sse"): f.append("ST-1 streaming is hand-rolled over raw SSE instead of the official SDKs - the SDKs handle streaming, accumulation and reconnection, and a hand parser re-implements exactly the parts that break silently (event ordering, accumulation, reconnects)")
    if not tr.get("streaming_used_where_required"): f.append("ST-1 streaming is not used where it is required (large max_tokens and long generations, where the SDK requires streaming to avoid HTTP timeouts; and get_final_message() when the complete Message is the deliverable) - a long non-streaming request learns about its timeout from the failure, not from the design")
    if not tr.get("event_contract_handled"): f.append("ST-1 the event contract is not handled in full (message_start -> content_block_start/delta/stop per block -> message_delta -> message_stop, ping events interspersed, error events mid-stream, and unknown event types tolerated because the versioning policy may add them) - a consumer that only understands text deltas breaks on the first ping, error or new event type it meets")
    dl=d.get("deltas") or {}
    if not dl.get("partial_json_accumulated_and_parsed_at_block_stop"): f.append("ST-2 tool_use input deltas are not accumulated as partial JSON strings and parsed at content_block_stop (the final input is always an object; the deltas are strings, and the API buffers each complete key and value by default, so gaps between events are normal) - parsing a partial delta as JSON, or treating a gap as a hang, corrupts tool calls that were merely still arriving")
    if not dl.get("whole_blocks_and_fallback_blocks_handled"): f.append("ST-2 blocks that arrive whole are not handled (redacted_thinking, server tool results such as web_search_tool_result, and the fallback block at each model boundary of a server-side fallback carry no deltas) - a delta-only consumer drops exactly the blocks that carry redactions, server results and model-boundary evidence")
    if not dl.get("thinking_deltas_and_signature_handled"): f.append("ST-2 thinking streaming is not handled (thinking_delta events, the signature_delta just before content_block_stop that verifies the block's integrity, and display omitted - an empty thinking delta plus one signature delta and no text) - dropping the signature, or reading an omitted block as an empty thought, corrupts the thinking record the next turn depends on")
    lat=d.get("latency") or {}
    if not lat.get("first_token_latency_measured"): f.append("ST-3 first-token latency is not measured (time to message_start and to the first text delta, recorded per surface) - streaming exists to change what the user feels first, and an unmeasured stream can be slower to first token than the whole non-streaming answer it replaced")
    if not lat.get("final_message_accumulated_and_retained"): f.append("ST-3 the complete final Message is not accumulated and retained (via the SDK accumulation helper or an equivalent event fold, stored with its stop_reason and usage) - without the accumulated message there is no ground truth to bill, trace or resume from, only a scroll of deltas")
    if not lat.get("stop_reasons_handled_on_completion"): f.append("ST-3 stop_reason values are not each handled once a stream completes (end_turn, max_tokens, stop_sequence, tool_use and refusals take different next steps) - a truncated or refused stream read as a finished answer ships a partial intervention as if it were whole")
    rec=d.get("recovery") or {}
    if not rec.get("partial_response_captured"): f.append("ST-4 the partial response is not captured as it streams (every block retained up to the interruption) - recovery from where the stream stopped is impossible if the part that already arrived was never saved, and the whole response is re-processed at full price")
    if not rec.get("continuation_form_matches_model_generation"): f.append("ST-4 the continuation form does not match the model generation (Claude 4.5 and earlier: the partial response opens a new assistant message; Claude 4.6 and later: a user message carries the partial response plus an instruction to continue - and tool use and thinking blocks cannot be partially recovered, so resumption starts from the most recent text block) - the wrong form restarts, repeats or silently loses the middle of the answer")
    if not rec.get("midstream_error_events_handled"): f.append("ST-4 mid-stream error events are not handled as their own case (an overloaded_error inside the stream is not an HTTP 529 before it; a failure before the first event is a retryable HTTP error, a failure after it ends the stream) - treating both the same either retries a half-delivered answer from zero or abandons one that was recoverable")
    ops=d.get("operations") or {}
    if not ops.get("fine_grained_tool_streaming_decided"): f.append("ST-5 fine-grained tool streaming is undecided (streaming tool input JSON without server-side buffering lowers the latency to first parameter bytes, is set per tool, and can deliver invalid or partial JSON the caller must tolerate) - leaving it to chance either pays buffering latency on every tool call or accepts unvalidated JSON without a decision")
    if not ops.get("non_streaming_surfaces_explicitly_decided"): f.append("ST-5 the non-streaming surfaces are not explicitly decided (work that does not need a real-time response belongs on the asynchronous batch surface, and short whole answers can stay non-streaming) - streaming everything pays connection and handling complexity on work nobody watches arrive")
    if not ops.get("streaming_reverified_on_model_or_sdk_change"): f.append("ST-5 streaming handling is not re-verified when models or SDKs change (new event types arrive under the versioning policy, beta headers change what message_start carries, fallback blocks appear at model boundaries, and the recovery form itself changed at the 4.6 generation) - a consumer verified once silently ages out of the protocol it consumes")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
