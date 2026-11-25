#!/usr/bin/env python3
"""ugc-brief-check: deterministic gate for UGC creator briefs for consumer apps.
Stdlib only, offline, free. Sources (read in full 2026-11-21):
- Briefbase, UGC Brief Template https://www.getbriefbase.com/blog/ugc-brief-template-that-actually-works
  (one page, 10 sections; one brief per video; 2-3 hook options, creator picks or writes own;
  structure in seconds is the section most briefs omit; script only lines that must be exact;
  rights agreed in writing before filming; disclosure in the video itself, not only description;
  references 2-3 with one line each; review first cut against the brief)
- Wade, UGC Creator Brief Template for Consumer Apps https://www.wade.so/blog/ugc-creator-brief-template
  (deal before brief: rate/deliverables/length/editing/posting account; paid-ad rights separate;
  recording kit: tested link, demo login with fake safe data, premium access, required state,
  tap-sequence recording, never-show list; one concept, claim the footage can honestly prove;
  3 clean openings around one shared demo; do not present as customer unless true, no fake history;
  unique name/campaign link per concept-creator pair; judge on installs+activation, not views;
  keep winning concept fixed, change one component, record result beside the brief)
- GOAT practice already recorded in cal-ai-creator-volume-spec SS8: 1-page brief,
  product inside the first 15 seconds, attribution and renewal discipline.
Exit 0 = PASS, 1 = FAIL.
"""
import json, sys

def check(d):
    fails = []
    if not d.get("brief_per_video_recorded"):
        fails.append("UB-0 no per-video brief is recorded with concept/creator/batch (one campaign brief forwarded to everyone is not a brief)")
    if not d.get("product_one_sentence_in_customer_words"):
        fails.append("UB-0 the brief does not state the product in one sentence in customer words (founder story/brand values are not a product line)")
    deal = d.get("deal") or {}
    if not deal.get("rate_stated_before_filming"):
        fails.append("UB-1 rate is not stated before filming")
    if not deal.get("deliverables_length_editing_posting_account_stated"):
        fails.append("UB-1 deliverable count, length, editing responsibility, or posting account is missing from the deal (production vs distribution are different sales)")
    if deal.get("paid_ad_rights_buried_in_organic_rate"):
        fails.append("UB-1 paid advertising rights are buried inside the organic rate (Spark/partnership usage is a separate agreement)")
    kit = d.get("recording_kit") or {}
    if not kit.get("tested_download_link_supplied"):
        fails.append("UB-2 no tested download link is supplied in the recording kit")
    if not kit.get("demo_login_fake_safe_data"):
        fails.append("UB-2 no demo login with fake, safe-to-publish data (creators must never record real personal data)")
    if not kit.get("premium_and_required_state_prepared"):
        fails.append("UB-2 premium access / required permission and onboarding state is not prepared for the assigned feature")
    if not kit.get("tap_sequence_recording_supplied"):
        fails.append("UB-2 no screen recording of the intended tap sequence is supplied (the creator cannot improvise the app flow)")
    if not d.get("one_concept_one_message"):
        fails.append("UB-3 the brief carries more than one concept/message (three benefits are three videos or hook variations, not one crowded video)")
    if not d.get("claim_demonstrable_in_footage"):
        fails.append("UB-3 the claim is broader than what the footage can honestly prove (one task / one result, not the whole product)")
    hk = d.get("hooks") or {}
    if (hk.get("hook_options_count") or 0) < 2:
        fails.append("UB-4 fewer than 2 hook options are given (hooks are where creators freeze or fall back on generic openers)")
    if not hk.get("openings_recorded_as_separate_clips"):
        fails.append("UB-4 openings are not recorded as separate clean clips around one shared demo (hooks cannot be tested without reshooting)")
    if hk.get("full_word_for_word_script"):
        fails.append("UB-4 the whole video is scripted word-for-word (it comes back sounding read; script only claims and the CTA exactly)")
    st = d.get("structure") or {}
    if not st.get("timed_structure_in_seconds"):
        fails.append("UB-5 no timed structure in seconds (0-3 hook / problem / app sequence / result / CTA) - the section most briefs omit")
    if not st.get("demo_follows_supplied_sequence"):
        fails.append("UB-5 the demo does not follow the supplied app sequence")
    if not st.get("single_cta_at_end"):
        fails.append("UB-5 there is not a single assigned call to action in the final seconds")
    ms = d.get("must_show_do_not") or {}
    if not ms.get("must_show_say_separated_from_preferences"):
        fails.append("UB-6 must-show/must-say items are not separated from preferences (required proof shot and approved claim wording must be explicit)")
    if not ms.get("do_not_list_present"):
        fails.append("UB-6 no do-not list (unsupported claims, competitors, past mistakes) - a short do-not list prevents reshoots a brand book cannot)")
    if not ms.get("never_show_private_or_internal"):
        fails.append("UB-6 the never-show list does not cover private data and internal screens")
    if ms.get("fake_personal_history_or_false_customer_pose"):
        fails.append("UB-6 the brief asks for a fake personal history or presents a non-customer as a customer (an unsupportable claim)")
    sp = d.get("specs") or {}
    if not sp.get("count_length_format_stated"):
        fails.append("UB-7 deliverable count, length range, or 9:16 vertical format is not stated ('a TikTok' is not a spec)")
    if not sp.get("raw_vs_edited_and_captions_stated"):
        fails.append("UB-7 raw vs edited, hook variations, or caption handling is not stated")
    if not sp.get("file_naming_and_caption_delivery_stated"):
        fails.append("UB-7 file naming or caption-text delivery is not stated (batches become uncomparable and unfindable)")
    rt = d.get("rights_disclosure") or {}
    if not rt.get("organic_usage_where_and_duration_in_writing"):
        fails.append("UB-8 organic usage (where it runs, for how long) is not agreed in writing before filming")
    if not rt.get("disclosure_in_video_when_creator_posts"):
        fails.append("UB-8 disclosure is not required inside the video itself when the creator posts to their own account (description-only is not enough)")
    if not rt.get("ai_generated_content_confirmed_and_labelled"):
        fails.append("UB-8 AI-generated face/voice/scene is not confirmed in delivery and labelled where the platform requires it")
    tl = d.get("timeline") or {}
    if not tl.get("first_cut_date_and_revision_rounds_defined"):
        fails.append("UB-9 first-cut date or the number/definition of revision rounds is undefined (one consolidated factual round is the app default)")
    if not tl.get("fee_and_pay_timing_stated"):
        fails.append("UB-9 fee or pay timing is not stated")
    if not tl.get("written_confirmation_before_filming"):
        fails.append("UB-9 the creator has not confirmed brief, fee, deadline, and rights in writing before filming")
    mm = d.get("measurement") or {}
    if not mm.get("unique_name_or_link_per_concept_creator"):
        fails.append("UB-10 no unique name/campaign link per concept-creator pair (attribution cannot be reconstructed later)")
    if not mm.get("judged_on_installs_and_activation"):
        fails.append("UB-10 results are judged on views alone (the decision metric is installs and activation)")
    if not mm.get("winner_fixed_one_component_changed_result_recorded"):
        fails.append("UB-10 the winning concept is not kept fixed with one component changed and the result recorded beside the brief")
    if not d.get("references_with_takeaway_lines"):
        fails.append("UB-10 fewer than 2 reference videos with a one-line takeaway each (a reference does more than a paragraph of adjectives)")
    return fails

def main():
    with open(sys.argv[1]) as f:
        d = json.load(f)
    fails = check(d)
    print(f"{d.get('app','?')}: fails={len(fails)}")
    for x in fails:
        print(" FAIL", x)
    print("PASS" if not fails else "FAIL")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
