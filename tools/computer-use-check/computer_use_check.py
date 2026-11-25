#!/usr/bin/env python3
"""computer-use-check: deterministic gate for the Computer Use surface
(how a model drives a real desktop GUI through screenshots and mouse /
keyboard actions - which tasks belong on the desktop at all versus an
API or the browser tool, how the agent loop answers batched member
calls, how coordinates and screenshot sizes are handled, how screenshot
history and its token cost are bounded, and how prompt-injection and
precision limits are fenced - is decided, not left to habit).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Computer use tool"
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
  (596 lines read in full): one {"type": "computer_toolset_20260801"}
  entry in tools gives 17 member tools (screenshot, zoom, left_click,
  type, key, scroll, ...); no beta header; the application runs every
  call in an environment it controls; not available in Claude Managed
  Agents. For webpage-only tasks the browser use tool is the closer
  fit. Security: instructions in webpages or images can override the
  user's instructions (prompt injection); classifiers automatically
  scan tool returns such as screenshots and steer the model to verify
  the instruction really came from the user; opt out only via support;
  inform end users of risks and obtain consent before enabling in own
  products. Loop: respond to stop_reason tool_use by running every
  tool_use block in order, return one tool_result per block matched by
  tool_use_id and echoing "toolset_name": "computer"; only screenshot
  and zoom results need an image. Batch actions run sequentially in
  content order, stop at the first failure; the failed block returns
  is_error with a description and every later block returns is_error
  with exactly "Not executed: an earlier computer action in this turn
  failed."; an unanswered block is rejected with invalid_request_error.
  The loop needs a maximum iteration limit against infinite loops and
  unexpected API cost, and a human confirmation check belongs before
  each block when actions are consequential, because a batch can
  complete a multistep action within one turn. Environment: sandboxed
  (virtual X11 display via Xvfb, Mutter/Tint2, Docker reference
  implementation); Claude never connects directly. Coordinates live in
  the pixel space of the full-display screenshots returned (origin top
  left); zoom does not change that space; downscaled screenshots mean
  scaling coordinates back up (macOS Retina 2x). All 17 members are
  enabled by default including zoom; withhold a member via configs
  rather than leaving it enabled and erroring; dispatch on the pair
  (toolset_name, name). The toolset entry rejects legacy fields name,
  display_width_px, display_height_px, display_number, enable_zoom,
  and cannot be declared alongside a computer_20251124 entry or another
  tool named computer. Screenshots must already fit the model's image
  limits - the API does not downscale and oversized images are
  rejected; use 1024x768 or 1280x720 for general desktop tasks,
  1280x800 or 1366x768 for web apps, avoid above 1920x1080, base64 PNG
  or JPEG. Screenshot history: each screenshot is roughly 1,000-1,800
  input tokens; past 20 images in one request every image is held to a
  stricter per-side limit; keep prompt caching effective with one
  cache_control breakpoint after system prompt and tool definitions
  and up to three more on the last tool_result of recent turns (at most
  one per turn inside a batch); prune old screenshots in batches (keep
  the last three, prune about every 25 turns), not one per turn. Do
  not client-side prune on Fable / Mythos 5.x, Opus 5.5, Sonnet 5.5 or
  Haiku 5.5 - removing an earlier screenshot invalidates every later
  thinking block; instead resize to stay under the stricter limit,
  note tool-result clearing still counts cleared screenshots toward
  request limits, use on-demand compaction, and if pruning is
  unavoidable keep prefix_mismatch_behavior "drop_block" set (on
  Sonnet 5.5 / Haiku 5.5 only with adaptive thinking, otherwise strip
  thinking blocks after the prune point). Pricing: the toolset
  definition adds about 4,500 input tokens per request (about 4,590 on
  Sonnet 5, about 4,520 on other supported models; disabling zoom
  removes about 410), estimable in advance with token counting;
  screenshots are billed as image input. Prompting: specify
  well-defined tasks with explicit steps; prompt the model to take a
  screenshot after each step, state in one sentence what it shows and
  whether the step succeeded, and retry before moving on; end batches
  with a screenshot or attach one to the last result; place instruction
  text before the screenshot image to improve click accuracy; prefer
  keyboard shortcuts for dropdowns and scrollbars; ask about a
  specific region to trigger zoom. Limitations: latency, coordinate
  hallucination, tool-selection mistakes, scrolling reliability (Page
  Down fallback), spreadsheet fine control via mouse down/up and
  modifiers, limited account creation and content generation on social
  platforms; always review and verify actions and logs; no tasks
  requiring perfect precision or sensitive user information without
  human oversight. Data retention: client-side tool - screenshots,
  actions and files are stored in your own environment, not by
  Anthropic; ZDR eligible.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("CU-0 the Computer Use surface is not recorded as a decided surface - which tasks are driven through a real desktop GUI, and which stay on APIs or structured tools, is left to each run and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("CU-0 no owner is recorded for computer-use correctness (loop shape, coordinate handling, injection fences, cost of screenshots) - a loop that clicks blind or leaks screen content has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("CU-0 there is no inventory of GUI-automation surfaces in use (which stacks drive a desktop, a browser or a phone, through which harness, and which of them is an API computer-use deployment) - the surface cannot be required where its own deployment is uncounted")
    en=d.get("enablement") or {}
    if not en.get("toolset_definition_fixed"): f.append("CU-1 the toolset definition shape is not fixed (one entry of type computer_toolset_20260801, no beta header, schema-less; the entry rejects the legacy fields name, display_width_px, display_height_px, display_number and enable_zoom, and cannot be declared in the same request as a computer_20251124 entry or another tool named computer) - the desktop is wired in a shape the API refuses")
    if not en.get("fit_decided"): f.append("CU-1 the fit is not decided (tasks that stay inside webpages belong to the browser use tool, which reads and acts on the page itself and needs no desktop environment; computer use is for desktop applications and cross-application work; the toolset is not available in Claude Managed Agents - evaluated on this workload, not the headline) - a full desktop is spun up for page work an API or browser tool does directly, or page tools are forced onto desktop software they cannot drive")
    if not en.get("members_configured"): f.append("CU-1 the member set is not configured deliberately (all 17 members are enabled by default, including zoom; a member the environment cannot serve is withheld through configs - with defer_loading placed inside configs - rather than left enabled and answered with errors; dispatch is on the pair toolset_name plus name, because a custom tool can share a member's name) - the model plans around actions the environment errors on, or a same-named custom tool is driven as a desktop action")
    lp=d.get("loop") or {}
    if not lp.get("loop_answers_every_block"): f.append("CU-2 the agent loop does not answer every block (iterate over every tool_use block in the response, run each in order in your own environment, and return one tool_result per block matched by tool_use_id and echoing toolset_name computer - image only for screenshot and zoom, a short text such as OK otherwise; a request that leaves any block unanswered is rejected with invalid_request_error) - a loop that reads only the first block fails on its next call")
    if not lp.get("batch_order_and_halt"): f.append("CU-2 batch actions are not run in order with the halt rule (blocks run sequentially in content order because later actions depend on earlier ones; stop at the first failure, return is_error with a description for the failed block, and answer every later block with is_error and exactly the halt text 'Not executed: an earlier computer action in this turn failed.') - a type lands wherever a failed click left focus, and the model replans from a batch it believes ran")
    if not lp.get("iteration_cap_set"): f.append("CU-2 no maximum iteration limit or pre-action confirmation is set (the loop continues until the model stops asking or the cap is reached - the cap is the safeguard against infinite loops and unexpected API cost; where actions are consequential, the human confirmation check happens before each block runs, because a batch can complete a multistep action within a single turn) - a stuck desktop loop bills without bound, or a destructive multistep action completes before anyone sees it")
    ev=d.get("environment") or {}
    if not ev.get("sandboxed_environment"): f.append("CU-3 the computing environment is not sandboxed and isolated (a virtual display and lightweight desktop inside a container or VM the application controls - the reference implementation runs in Docker; the model never connects to the environment directly, the application translates its calls, runs them and returns results) - desktop actions run against a real machine holding real data, with no isolation between the agent and everything else on it")
    if not ev.get("coordinate_space_handled"): f.append("CU-3 the coordinate space is not handled (every coordinate, start_coordinate and region, and what cursor_position reports, is in the pixel space of the full-display screenshots returned, origin top left; a zoom image never changes that space; if screenshots are scaled down before returning, the model's coordinates are scaled back up before being applied - including the macOS Retina 2x device pixel ratio) - clicks land offset by exactly the scale factor nobody recorded")
    if not ev.get("screenshot_sizing"): f.append("CU-3 screenshot sizing is not decided (returned screenshots and zoom images must already fit the model's image limits - the toolset takes no display dimensions and the API does not downscale, so an oversized image is rejected with a validation error; use 1024x768 or 1280x720 for general desktop tasks and 1280x800 or 1366x768 for web applications, avoid resolutions above 1920x1080, encode base64 PNG or JPEG) - the loop dies on its own screenshots, or pays 4K detail the model never receives")
    hi=d.get("history") or {}
    if not hi.get("screenshot_history_managed"): f.append("CU-4 screenshot history is not managed (each screenshot costs roughly 1,000-1,800 input tokens, and once a request carries more than 20 images every image is held to a stricter per-side limit; keep prompt caching effective with one cache_control breakpoint after the system prompt and tool definitions and up to three more on the last tool_result block of the most recent turns - at most one inside any batch turn - and prune old screenshots in batches, keeping the last three and pruning about every 25 turns, never one per turn, because dropping one every turn invalidates the cache prefix every turn) - long loops price themselves out on stale screens, or thrash the cache they depend on")
    if not hi.get("pruning_model_exceptions_known"): f.append("CU-4 the pruning model exceptions are not known (on Fable and Mythos 5.x, Opus 5.5, Sonnet 5.5 and Haiku 5.5, client-side pruning is avoided entirely - removing an earlier screenshot invalidates every later thinking block in that and every later request; instead resize screenshots to stay under the stricter limit, remember that tool-result clearing still counts cleared screenshots toward request limits, and use on-demand compaction before the loop reaches them; if pruning is unavoidable, keep prefix_mismatch_behavior drop_block set from then on - which on Sonnet 5.5 and Haiku 5.5 works only with adaptive thinking, otherwise strip every thinking and redacted_thinking block after the prune point) - a routine history trim silently amputates the model's reasoning on exactly the newest models")
    if not hi.get("overhead_counted"): f.append("CU-4 the fixed overhead is not counted (declaring computer_toolset_20260801 with default members adds about 4,500 input tokens to every request - about 4,590 on Sonnet 5 and about 4,520 on other supported models, with disabling zoom removing about 410 - and screenshots are billed as image input on top; the exact count is in response usage and estimable in advance with the token counting endpoint) - the surface is judged at its per-action price while its per-request rent goes uncounted")
    sa=d.get("safety") or {}
    if not sa.get("injection_defenses"): f.append("CU-5 prompt-injection defenses are not in place (instructions embedded in webpages or images can override the user's instructions; isolate the model from sensitive data and actions, rely on - but do not substitute for - the classifiers that scan tool returns such as screenshots and steer the model to check an instruction really came from the user, treat opting out via support as a decision rather than a default, inform end users of the risks and obtain consent before enabling computer use in your own products, and treat putting login credentials in the prompt as a risk-raising step) - the screen itself becomes an instruction channel from whoever published the page on it")
    if not sa.get("verification_prompting"): f.append("CU-5 per-step verification is not prompted (specify well-defined tasks with explicit steps; prompt the model to take a screenshot after each step, state in one sentence what the screenshot shows and whether the step succeeded, and retry before moving on - the model otherwise acts as if actions succeeded without checking; end each batch with a screenshot or attach one to the last result; place instruction text before the screenshot image for click accuracy; prefer keyboard shortcuts for dropdowns and scrollbars, and ask about a specific region or element to trigger zoom on small text) - the loop reports success it never looked at, which is the failure this company's own five-senses rule exists to catch")
    if not sa.get("limits_and_oversight"): f.append("CU-5 the limits and oversight are not recorded (latency makes the surface wrong for speed-critical interaction; coordinates and tool selection can be hallucinated, scrolling can silently not take effect - Page Down is the fallback - and spreadsheets need fine mouse control; account creation and content generation on social platforms are limited; always review and verify the model's computer-use actions and logs, and never run tasks requiring perfect precision or sensitive user information without human oversight; retention is the application's own - screenshots, actions and files live in your environment, not Anthropic's, and the surface is ZDR eligible) - a known-unreliable hand is given unreviewed run of tasks whose errors nobody priced")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
