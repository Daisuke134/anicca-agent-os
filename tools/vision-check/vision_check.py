#!/usr/bin/env python3
"""vision-check: deterministic gate for the VISION surface
(how images are sent to the model - source type, format, size,
resolution and visual-token cost, multi-image handling, quality,
verification of interpretations, coordinate rescaling - is decided,
not left to whatever each call happens to attach).
Stdlib only, offline.
Canonical source (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Vision"
  https://platform.claude.com/docs/en/build-with-claude/vision
  (208 lines read in full): images go in as image content blocks via
  three source types - base64 embedded in the request, a URL
  reference, or a file_id from the Files API (upload once, reference
  many times; use it for repeated images or to avoid encoding
  overhead). Multiple images in one request are analysed jointly;
  label each one (Image 1:, Image 2:) so the prompt and follow-ups
  can refer to them; images from earlier turns stay accessible, so
  follow-ups work without resending them. Request limits: 20 images
  per message on claude.ai, 100 per API request on 200k-context
  models, 600 on other models; max dimensions 8000x8000 px; if a
  request contains more than 20 images a stricter per-image limit
  applies to every image - all image blocks count, including resent
  earlier-turn images, images nested in tool_result content, and (on
  Bedrock / Google managed) PDF document blocks; exceeding it is an
  invalid_request_error naming many-image requests - stay safe by
  resizing every image to at most 3000 px per side or keeping the
  request to 20 or fewer image/document blocks. Max size per image:
  10 MB base64 on the Claude API and Google managed, 5 MB on Bedrock,
  10 MB on claude.ai. Supported formats are JPEG, PNG, GIF and WebP;
  animations are unsupported and only the first frame is used.
  Images are processed in 28x28 px patches (visual tokens): cost is
  ceil(width/28) x ceil(height/28). Each model tier has a max native
  resolution - high-resolution tier (Claude 4.7+): long edge 2576 px,
  4784 visual tokens; standard tier: 1568 px, 1568 visual tokens -
  and larger images are downscaled preserving aspect ratio, except
  screenshots/zoom images returned to the computer use / browser use
  toolsets, which are REJECTED with a validation error when they
  exceed the limits, so resize them in the application before
  returning them; any other image can be made to error instead of
  downscaling via the transformations field
  (oversized_image: "error"). High-resolution images can cost up to
  roughly 3x the visual tokens of standard; downsample before
  sending when the extra fidelity is not needed (computer use,
  screenshot understanding and dense documents do need it); prefer
  resizing before upload to minimise latency and simplify
  coordinate workflows. Quality guidance: images clear, not blurry
  or pixelated; important text legible and not too small, without
  cropping away key context just to enlarge text; resizing may make
  text less legible, so consider pre-resizing/cropping; lossy
  compression (JPEG/WebP) reduces latency but artefacts - especially
  from multiple compression passes - can make text hard to read, so
  confirm settings by inspecting the actual images sent.
  Coordinates: the model returns absolute pixel coordinates relative
  to the image it processed AFTER resizing, so pre-resize or rescale
  so coordinates line up with the original. Limitations: Claude
  cannot name people in images and refuses; it can hallucinate or
  err on low-quality, rotated or very small (under 200 px) images;
  spatial reasoning and coordinates are approximate; counting is
  approximate, especially many small objects; it cannot determine
  whether an image is AI-generated - do not rely on it to detect
  fake images; inappropriate content is not processed; it is not
  designed for complex diagnostic scans (CT/MRI) and its outputs are
  not a substitute for professional advice. Always review and verify
  image interpretations, especially for high-stakes use.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("VI-0 the vision surface is not recorded as a decided surface - which images are sent to the model, in what form and at what fidelity is left to each call site and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("VI-0 no owner is recorded for vision correctness (source choice, resizing, cost, verification of interpretations) - a misread screenshot or a silently downscaled paywall image has no accountable reader")
    if not dec.get("vision_surfaces_inventoried"): f.append("VI-0 there is no inventory of the vision surfaces (winner-vs-own screenshot comparison, app-screen reading, chart/document extraction, user-supplied images) - fidelity and verification cannot be required where the surfaces are indistinguishable")
    src=d.get("sources") or {}
    if not src.get("source_type_chosen_deliberately"): f.append("VI-1 the image source type is not chosen deliberately per surface (base64 embedded, URL reference, or a Files API file_id - upload once and reference many times for images used repeatedly or to avoid re-encoding overhead) - resending base64 for the same winner screenshot on every comparison pays encoding and payload cost for a reference that already exists")
    if not src.get("formats_validated"): f.append("VI-1 image formats are not validated before sending (only JPEG, PNG, GIF and WebP are supported, and animations are unsupported - only the first frame is used) - an animated or unsupported image is silently read as its first frame or fails, and the reading is reported as if the whole image was seen")
    if not src.get("size_and_count_limits_enforced"): f.append("VI-1 per-image size and request count limits are not enforced before sending (8000x8000 px maximum; 10 MB base64 on the Claude API, 5 MB on Bedrock; 100 images per API request on 200k-context models, 600 on others, 20 per message on claude.ai) - the limit is learned from an invalid_request_error in production instead of from the design")
    res=d.get("resolution") or {}
    if not res.get("visual_token_cost_estimated"): f.append("VI-2 the visual-token cost of images is not estimated before sending (ceil(width/28) x ceil(height/28) patches, capped by the model tier - standard 1568 px / 1568 tokens, high-resolution 2576 px / 4784 tokens) - image cost enters the bill uncounted, and a 4K screenshot can cost roughly 3x the same image on a standard-tier model")
    if not res.get("resizing_decided_before_send"): f.append("VI-2 resizing before sending is not decided (downsample when the extra fidelity is not needed to control token cost and latency; keep fidelity for screenshot understanding, dense documents and coordinate work, and prefer pre-resizing to simplify coordinate workflows) - every oversized image is downscaled by the API on the API's terms, and text that was legible in the original may not survive the resize nobody chose")
    if not res.get("oversized_handling_decided"): f.append("VI-2 oversized-image handling is not decided (ordinary images are downscaled silently, but screenshots and zoom images returned to the computer use / browser use toolsets are REJECTED with a validation error over the limit and must be resized in the application before returning them; any other image can be set to error instead of downscaling via the transformations field) - a screenshot pipeline that assumes downscaling breaks exactly where the tool returns its evidence")
    multi=d.get("multi_image") or {}
    if not multi.get("multiple_images_labelled"): f.append("VI-3 multiple images in one request are not each introduced with a short label (Image 1:, Image 2:) so the prompt and follow-up turns can refer to them by name - an unlabelled comparison set makes the model's answer about 'the second image' unverifiable against which file that was")
    if not multi.get("many_image_stricter_limit_handled"): f.append("VI-3 the stricter many-image limit is not handled (above 20 images in one request every image faces a stricter per-image dimension limit, and ALL image blocks count - resent earlier-turn images, images nested in tool_result content, and PDF document blocks on Bedrock / Google managed; stay safe by resizing every image to at most 3000 px per side or keeping the request to 20 or fewer blocks) - a long screenshot-review session crosses the threshold silently and starts failing on images that passed yesterday")
    if not multi.get("prior_turn_images_reused_not_resent"): f.append("VI-3 images from earlier turns are resent instead of reused (the model keeps access to every earlier image, so follow-ups such as 'are these similar to the first two?' work without re-including them) - resending pays the visual tokens again, inflates the many-image count, and can push the request over the stricter limit for no new information")
    qual=d.get("quality") or {}
    if not qual.get("image_quality_checked"): f.append("VI-4 the quality of images sent is not checked (clear, not blurry or pixelated; important text legible and not too small; key visual context not cropped away just to enlarge text) - the model reads what it is given, and a verdict on an illegible screenshot is a verdict on the compression, not on the screen")
    if not qual.get("compression_checked_on_actual_sent_images"): f.append("VI-4 compression is not confirmed on the actual images sent (lossy JPEG/WebP compression reduces latency but artefacts, especially from multiple compression passes, can make text difficult to read) - a pipeline can re-compress a winner screenshot until its caption is unreadable and still report a faithful comparison")
    if not qual.get("interpretations_verified"): f.append("VI-4 image interpretations are not reviewed and verified before they are relied on (hallucination and error are expected on low-quality, rotated or very small images under 200 px; counting is approximate, especially many small objects) - an unverified visual verdict ships with the model's confidence and none of its caveats, which is how a misread screen becomes a shipped decision")
    ops=d.get("operations") or {}
    if not ops.get("coordinates_rescaled_to_original"): f.append("VI-5 returned coordinates are not rescaled to the original image (the model returns absolute pixel coordinates relative to the image it processed AFTER resizing and padding) - a bounding box read against the original screenshot points at the wrong UI element by exactly the resize factor nobody recorded")
    if not ops.get("limits_reverified_on_model_change"): f.append("VI-5 vision limits are not re-verified when models change (the native resolution tier, the visual-token cap and the per-request image count all differ by model - high-resolution support is automatic on 4.7+ models with no opt-in, so the same image silently costs up to 3x more after an upgrade) - a model switch reprices and re-resizes every image surface without any decision being revisited")
    if not ops.get("prohibited_uses_excluded"): f.append("VI-5 prohibited and unreliable uses are not excluded by design (the model cannot name people in images and refuses; it cannot determine whether an image is AI-generated, so it must not be relied on to detect fake or synthetic images; it is not designed to interpret complex diagnostic scans such as CTs or MRIs as a substitute for professional advice) - a surface that asks for any of these gets a refusal or a confident error and reports it as a result")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
