#!/usr/bin/env python3
"""comedy-taste-check: deterministic gate for the COMEDY TASTE surface
(the founder rule 2026-11-22: comedy taste in EVERYTHING -- notifications,
home words, posts, blog, every surface; Anicca is used on hard days and
laugh-wanting days BECAUSE it is funny; one mascot character speaks).
Stdlib only, offline, free.
Owns comedy coverage/type/generation/measurement. Not notification decision
ownership (notif-model-check NM), not simulate-first order (sim-first-check SI).
Sources (read 2026-11-22):
- Sun et al., ACM CUI '24, "Can a Funny Chatbot Make a Difference?"
  https://ir.cwi.nl/pub/34506/34506.pdf (DOI 10.1145/3640794.3665555):
  RCT, 66 participants, 10 days, 3 arms. AFFILIATIVE humorous style positively
  impacted physical activity over time; USER ENGAGEMENT mediated the effect,
  motivation did NOT. Aggressive / self-defeating humor is divisive or
  draining; affiliative humor (shared human experience) is the safe type.
  Generative LLM humor removes the repetition constraint of canned jokes.
- Choi et al., JMIR Mental Health 2018;5(2):e26 (RCT, n=549 recruited,
  318 in poor ranges): humor-driven feedback did NOT differ from normative
  feedback on immediate clicks to a help resource. Comedy alone does not
  move the immediate action; the clear help/action path must survive.
- Duolingo push practice (secondary summary, The Dock):
  https://thedock.beehiiv.com/p/how-duolingo-used-push-notifications-to-build-a-10b-brand
  one character (Duo) speaks across notifications and social; notifications
  written like a person/character, personalized by user state (missed days,
  streak), humor makes users screenshot and share them (organic UGC).
- House rules (founder, 2026-11-22, primary): comedy taste in everything;
  brand promise "on a hard day / a laugh-wanting day, people use Anicca
  because it is funny"; a mascot is to be decided (one character) and speaks;
  notifications are model-decided and model-worded, push text must fit the
  full banner; founder is the first gate (must make him laugh, ease his
  hard day). Comedy lane rule (2026-11-17): no monk premise in comedy.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    c=d.get("coverage") or {}
    if not c.get("comedy_required_on_every_surface_recorded"): f.append("CT-0 the every-surface comedy requirement is not recorded (an unrecorded taste rule applies only where someone remembers it; notifications, home, posts and blog drift back to generic)")
    if not c.get("surface_inventory_covers_notifications_home_posts_blog"): f.append("CT-0 the surface inventory does not cover notifications, home words, posts and blog (a surface missing from the inventory is a surface with no comedy by construction)")
    if not c.get("single_mascot_character_decided"): f.append("CT-0 no single mascot character is decided (the winner form is ONE character who speaks -- Duolingo's Duo; an undecided mascot means every surface invents its own voice)")
    if not c.get("mascot_voice_defined_and_shared"): f.append("CT-0 the mascot voice is not defined and shared (character, tone and lines must be written once and reused, or each lane writes a different character with the same name)")
    t=d.get("type") or {}
    if not t.get("affiliative_humor_only"): f.append("CT-1 humor type is not restricted to affiliative (the RCT evidence is for affiliative humor -- jokes from shared human experience; other types were not the tested intervention)")
    if not t.get("aggressive_and_self_defeating_humor_banned"): f.append("CT-1 aggressive and self-defeating humor are not banned (both are divisive or emotionally draining, the opposite of easing a hard day)")
    if not t.get("no_monk_premise_in_comedy"): f.append("CT-1 comedy still leans on a monk premise (house rule: comedy starts by forgetting the monk frame -- no monk setup, costume or sermon content)")
    if not t.get("comedy_serves_hard_day_promise"): f.append("CT-1 comedy is not tied to the brand promise (the stated reason people use Anicca on hard days is that it is funny; jokes that do not ease the day are decoration)")
    g=d.get("generation") or {}
    if not g.get("model_generated_not_canned_catalogue"): f.append("CT-2 wording is still a canned catalogue (pre-written lines cannot be personal or fresh; the RCT used generative humor precisely to escape repetition)")
    if not g.get("personalized_from_user_state"): f.append("CT-2 comedy is not personalized from user state (the winner form tailors the character's line to what the user just did -- missed days, streak, answers -- generic jokes land as ads)")
    if not g.get("repetition_guard_same_joke_not_resent"): f.append("CT-2 there is no repetition guard (the same joke resent is the fastest way to train users to ignore the character)")
    if not g.get("push_text_fits_full_banner_length"): f.append("CT-2 push text is not constrained to fit the full banner (a joke cut off mid-line on the lock screen is a broken joke; length is part of the craft)")
    m=d.get("measurement") or {}
    if not m.get("engagement_measured_as_the_mediator"): f.append("CT-3 engagement is not measured as the mediator (in the RCT the path was humor -> engagement -> behavior; opens alone do not show the mechanism)")
    if not m.get("behavior_outcome_measured_not_opens_only"): f.append("CT-3 no behavior outcome is measured (motivation did NOT mediate in the RCT and clicks did not move in the JMIR RCT -- self-reported motivation and raw opens are not evidence comedy worked)")
    if not m.get("comedy_not_credited_without_own_test"): f.append("CT-3 comedy is credited without an own test (JMIR 2018 found no difference vs normative feedback; claiming a comedy lift without a humorous-vs-plain comparison in own data is an unverified claim)")
    if not m.get("founder_first_gate_laugh_test"): f.append("CT-3 the founder first gate is not applied (the first acceptance condition is that it makes the founder laugh and eases his hard day, judged on the real surface, before scale)")
    s=d.get("safety") or {}
    if not s.get("clear_action_path_preserved_despite_humor"): f.append("CT-4 the clear action/help path is not preserved (humor-driven feedback did not beat a plain path on immediate help-seeking; the joke may carry the user TO the action, never replace it)")
    if not s.get("crisis_and_safety_surfaces_gentle_or_exempt"): f.append("CT-4 crisis and safety surfaces are not gentle or exempt (a user in acute distress gets care and a clear path first; comedy taste never outranks safety wording)")
    if not s.get("outside_matches_inside_comedy_exists_in_product"): f.append("CT-4 distribution promises a comedy the product does not contain (what is shown outside must exist inside; funny ads for a humourless app are a lie)")
    l=d.get("loop") or {}
    if not l.get("shareability_checked_screenshots"): f.append("CT-5 shareability is not checked (the winner's humor is screenshot and reposted by users -- free organic UGC; lines nobody would screenshot are not doing distribution work)")
    if not l.get("comedy_samples_reviewed_on_a_loop"): f.append("CT-5 shipped comedy samples are not reviewed on a loop (taste drifts silently; actual sent lines must be re-read and scored, not assumed funny)")
    if not l.get("unfunny_lines_killed_and_recorded"): f.append("CT-5 unfunny lines are not killed and recorded (a line that failed must leave the pool with a record, or it will be resent by the next run)")
    return f
def main():
    d=json.load(open(sys.argv[1]))
    fails=check(d)
    for x in fails: print("FAIL", x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
