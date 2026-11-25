#!/usr/bin/env python3
"""age-rating-check: deterministic gate for the APP STORE AGE RATING QUESTIONNAIRE surface.
Stdlib only, offline, free. This is NOT the Declared Age Range API surface
(that is age-range-check); this gate owns the App Store Connect age rating
questionnaire itself: the answers, the calculated rating, overrides, and
regional variants.
Sources (read in full 2026-11-22):
- Apple Developer News, "Updated age ratings in App Store Connect" (2025-07-24)
  https://developer.apple.com/news/?id=ks775ehf
  The system adds 13+, 16+, 18+ to 4+ and 9+; ratings for all apps were
  automatically updated; a new REQUIRED question set covers in-app controls,
  capabilities, medical or wellness topics, and violent themes; responses were
  due per app by January 31, 2026 to avoid an interruption when submitting
  updates; a higher rating may be set when the app's own policy requires a
  higher minimum age; developers must consider how ALL features, including AI
  assistants and chatbot functionality, impact the frequency of sensitive
  content; COPPA/GDPR and all local laws still apply.
- Newly, "App Store Age Rating: Tiers, Questions and Overrides (2026)"
  (Apple's values-and-definitions table read in full)
  https://newly.app/how-to/app-store-age-rating
  The rating is CALCULATED, never chosen: content descriptors are answered
  none / infrequent / frequent, controls and capabilities are present-or-not,
  and the highest tier any answer reaches wins. Override is upward only and
  is mandatory when the EULA/terms minimum age exceeds the calculated tier.
  Graphic sexual content and prolonged graphic/sadistic realistic violence
  are Unrated at any frequency (cannot be published on the App Store).
  Capability traps: unrestricted web access = 16+, social media = 13+,
  health/wellness topics = 9+ (presence), medical/treatment information =
  13+ infrequent / 16+ frequent, loot boxes = 9+, real-money gambling = 18+.
  Made for Kids is selectable only at calculated 4+ or 9+ and cannot be
  changed once App Review approves the app. Regional variants: Australia
  (social media and loot boxes display 16+, any simulated gambling R 18+),
  Brazil (AL-A18), Korea (All/12+/15+/19+, GRAC number for frequent simulated
  gambling, locked once approved), Vietnam (00+/12+/16+/18+). Guideline
  2.3.6: answer honestly -- a mis-rated app can trigger a regulator inquiry.
  Guideline 2.3.8: icon, screenshots and previews must adhere to 4+ whatever
  the app's own rating. Google Play uses the separate IARC questionnaire;
  the two must stay consistent with each other and with the binary.
  Social media capability questions were added 2026-07-09 and responses are
  required from September 2026 for new apps and updates (per Apple News as
  summarised by Newly/app369, read 2026-11-22).
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    comp=d.get("completeness") or {}
    if not comp.get("new_questions_answered_per_app"): f.append("AQ-0 the 2025 required question set (in-app controls / capabilities / medical or wellness / violent themes) is not answered for every app (the January 31, 2026 date has passed, so an unanswered app is interrupted at its next update submission -- the automatically converted rating is not an answer)")
    if not comp.get("social_media_question_answered"): f.append("AQ-0 the social media capability questions (added 2026-07-09, required from September 2026) are not answered (a feed-like surface answered under the old questionnaire alone no longer submits)")
    if not comp.get("answers_recorded_per_app_not_shared"): f.append("AQ-0 answers are not recorded per app (the questionnaire is per app in App Information; one app's answers never carry to another, and an unrecorded answer cannot be re-verified)")
    if not comp.get("reanswer_trigger_on_content_or_feature_change"): f.append("AQ-0 no re-answer trigger exists for content/feature changes (adding chat, a web view, UGC or a new content type changes the correct answers; a questionnaire answered once in 2025 silently rots)")
    hon=d.get("honesty_scope") or {}
    if not hon.get("answers_from_shipped_app_incl_sdks_webviews_ads"): f.append("AQ-1 answers are not derived from the shipped app including SDKs, web views and ads (the questionnaire asks what the app does, not what the marketing page says; a third-party SDK's content is the app's content)")
    if not hon.get("ai_assistant_frequency_considered"): f.append("AQ-1 the frequency impact of AI assistant / chatbot functionality is not considered (Apple's notice names this explicitly: an LLM that can produce profanity, medical or mature content changes the frequency answers, unless its output is restricted and that restriction is tested)")
    if not hon.get("frequency_vs_presence_kinds_distinguished"): f.append("AQ-1 the two question kinds are not distinguished (content descriptors take none/infrequent/frequent; in-app controls and capabilities are present-or-not -- answering a capability as a frequency, or a descriptor as a checkbox, misstates both)")
    if not hon.get("honesty_236_acknowledged"): f.append("AQ-1 Guideline 2.3.6 honesty is not acknowledged as the standard (answers drive parental controls; a mis-rated app can surprise customers or trigger an inquiry from government regulators -- 'lower is better for conversion' is a false declaration)")
    calc=d.get("calculation") or {}
    if not calc.get("calculated_rating_read_not_chosen"): f.append("AQ-2 the rating is treated as chosen rather than calculated (Apple generates it from the answers; the only developer-set values are the answers themselves and an upward override)")
    if not calc.get("highest_answer_wins_understood"): f.append("AQ-2 the highest-answer-wins rule is not applied in planning (one 16+ answer makes a 16+ app however clean the rest is; feature decisions are rating decisions)")
    if not calc.get("unrated_descriptors_verified_absent"): f.append("AQ-2 absence of the two Unrated descriptors is not verified (graphic sexual content and prolonged graphic or sadistic realistic violence are Unrated at ANY frequency and cannot be published on the App Store at all)")
    trap=d.get("capability_traps") or {}
    if not trap.get("unrestricted_web_access_flagged"): f.append("AQ-3 unrestricted web access is not flagged wherever it exists (any in-app browser or web view that can navigate to any page = 16+ on its own, even in an otherwise 4+ app)")
    if not trap.get("social_media_flagged_if_feed"): f.append("AQ-3 social media is not flagged if the app has a public feed / social surface (social media = 13+, including when disabled for users under 13; calling it 'community content' does not change the capability)")
    if not trap.get("wellness_vs_medical_distinguished"): f.append("AQ-3 health/wellness topics and medical/treatment information are not distinguished (wellness topics -- calorie tracking, dieting or exercise advice -- are a 9+ presence item; medical or treatment information is a frequency item at 13+ infrequent / 16+ frequent; a wellness app that drifts into treatment guidance crosses two tiers)")
    ovr=d.get("override_kids_regions") or {}
    if not ovr.get("override_upward_only_matches_min_age_policy"): f.append("AQ-4 the override rule is not recorded (override is upward only, there is no downward override; and when the app's own policy/EULA minimum age exceeds the calculated rating, overriding up to match is mandatory, not optional)")
    if not ovr.get("made_for_kids_irreversibility_understood"): f.append("AQ-4 Made for Kids is not treated as an irreversible commitment (selectable only at calculated 4+ or 9+, it cannot be changed once App Review approves the app, and all later updates must follow the Kids category guidelines)")
    if not ovr.get("regional_variants_checked"): f.append("AQ-4 regional rating variants are not checked (the same answers display differently in Australia, Brazil, Korea and Vietnam -- e.g. AU shows social media and loot boxes at 16+ and any simulated gambling at R 18+; KR frequent simulated gambling needs a GRAC number locked once approved)")
    if not ovr.get("store_assets_4plus_238"): f.append("AQ-4 Guideline 2.3.8 is not checked (the icon, screenshots and previews must adhere to a 4+ rating whatever the app itself is rated -- an 18+ app still needs store assets a child could see)")
    chg=d.get("change_management") or {}
    if not chg.get("rating_change_treated_as_significant_change"): f.append("AQ-5 a rating change is not treated as a significant change (in regulated regions a change in the app's age rating itself triggers parental-consent / adult-notification duties -- silently shipping a re-rate is a compliance event, not a metadata edit)")
    if not chg.get("play_iarc_consistency_checked"): f.append("AQ-5 consistency with the Google Play IARC questionnaire is not checked where the app ships on Play (two questionnaires, one binary: authorities can change a Play rating after review, and answers that contradict the App Store answers misrepresent the same content twice)")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
