#!/usr/bin/env python3
"""tipkit-check: deterministic gate for in-context feature discovery (TipKit, iOS 17+).
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Emrld Labs, "TipKit SwiftUI Tutorial: Feature Discovery Without Walls"
  https://emrldlabs.com/blog/tipkit-feature-discovery-inline-tips-swiftui/
  Onboarding walls teach nothing (no context, tapped through); TipKit's
  WWDC23 framing is "teachable moments": show the tip on the surface the
  feature lives on, after behaviour makes it relevant. Rules decide
  eligibility (parameter = state, event = donated behaviour); options and
  the global displayFrequency decide pacing. Forgetting Tips.configure()
  means tips silently never appear. Invalidate with .actionPerformed the
  moment the feature is used, and cap with MaxDisplayCount -- on iOS 26 a
  popoverTip inside a TabView can re-appear on every tab switch
  (FB20904972), so the cap is also the regression guard. Reserve tips for
  genuinely non-obvious, genuinely valuable features (2-3, not every
  control); TipKit state is on-device and iCloud-synced, no backend.
- Gurgul folio, "TipKit -- rules, pacing, invalidation"
  https://folio.gurgul.pro/swiftui/tipkit.html
  Configure once / rule who / pace when / cap how often / invalidate when
  learned. HIG shape: simple features (<=3 actions), 1-2 sentences,
  actionable; never for tours, promotion, or critical information.
  TipGroup and MaxDisplayDuration need iOS 18; core TipKit needs iOS 17,
  with no official back-deployment to iOS 16 or earlier.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, tips:[{id, feature, surface, presentation}]},
 configure:{called_at_launch, before_any_tip, display_frequency},
 eligibility:{every_tip_has_rule, rule_kinds:[], parameters_assigned_at_real_sites,
              events_donated_at_real_sites},
 content:{all_actionable, all_simple_le3_actions, any_promotional_or_paywall,
          any_critical_info},
 lifecycle:{invalidate_action_performed_wired, every_tip_has_max_display_count,
            ignores_display_frequency_used},
 availability:{min_target_ge17, availability_guard_present, fallback_for_below17_recorded},
 measurement:{tip_event_defined, tip_event_fired, adoption_joinable_exposed_vs_not}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    tips = inv.get("tips") or []
    if not inv.get("recorded"):
        fails.append("TK-0 feature discovery is not inventoried (which features are non-obvious, which surface each tip lives on, and how each is presented are nowhere recorded; an unrecorded discovery layer cannot be audited or fixed in order)")
    if not tips:
        fails.append("TK-0 no tips exist at all (TipKit / TipView / popoverTip hits are zero; every feature past onboarding is undiscoverable in context, so buried-but-valuable features -- widget setup, sharing, habit creation -- depend on the user stumbling onto them)")
    cfg = d.get("configure") or {}
    if not cfg.get("called_at_launch"):
        fails.append("TK-1 Tips.configure() is never called (without it tips silently never appear -- no crash, no warning; a tip layer without configure is a layer that does not exist)")
    elif not cfg.get("before_any_tip"):
        fails.append("TK-1 Tips.configure() is not called before any tip can display (configuration after first presentation leaves the first tips unconfigured)")
    freq = cfg.get("display_frequency")
    if tips and freq == "immediate" and len(tips) > 1:
        fails.append("TK-1 display frequency is .immediate with more than one tip (eligible tips can fire back to back -- the coach-mark carpet bomb the eligibility engine exists to prevent; pace to .daily or slower)")
    if tips and not freq:
        fails.append("TK-1 no display frequency is set in configure (pacing is left to the default instead of being a recorded decision)")
    el = d.get("eligibility") or {}
    if tips:
        if not el.get("every_tip_has_rule"):
            fails.append("TK-2 at least one tip has no eligibility rule (an unconditional tip shows to everyone on first sight, including people who already use the feature and people it cannot benefit -- rules decide WHO, not decoration)")
        kinds = el.get("rule_kinds") or []
        if "parameter" in kinds and not el.get("parameters_assigned_at_real_sites"):
            fails.append("TK-2 parameter rules exist but their @Parameter values are never assigned at real sites (a parameter nobody flips keeps the rule false forever; the tip can never become eligible)")
        if "event" in kinds and not el.get("events_donated_at_real_sites"):
            fails.append("TK-2 event rules exist but donate() is never called at the real moment (an unfed Tips.Event stays at count zero and the rule never passes; the event is a counter the app is responsible for feeding)")
        if not kinds:
            fails.append("TK-2 no rule kinds are recorded (parameter vs event is the core design split -- state vs behaviour over time -- and an unrecorded split cannot be reviewed)")
    ct = d.get("content") or {}
    if tips:
        if not ct.get("all_actionable"):
            fails.append("TK-3 at least one tip is not actionable (HIG: a tip teaches one simple, actionable thing in 1-2 sentences; a non-actionable tip is an announcement wearing a tip's clothes)")
        if not ct.get("all_simple_le3_actions"):
            fails.append("TK-3 at least one tip teaches a feature needing more than 3 actions (complex flows belong in onboarding or help, not in a transient tip that can be missed)")
        if ct.get("any_promotional_or_paywall"):
            fails.append("TK-3 a tip is promotional / paywall content (HIG forbids promotion in tips; a sales message inside the discovery layer teaches users to dismiss every future tip unread)")
        if ct.get("any_critical_info"):
            fails.append("TK-3 a tip carries critical information (a tip can be missed or capped away; critical information must live in the flow itself, never only in a tip)")
    lc = d.get("lifecycle") or {}
    if tips:
        if not lc.get("invalidate_action_performed_wired"):
            fails.append("TK-4 invalidate(reason: .actionPerformed) is not wired at the feature-use site (a tip that keeps reappearing after the user found the feature is worse than no tip; retire on the action, not just on the close)")
        if not lc.get("every_tip_has_max_display_count"):
            fails.append("TK-4 at least one tip has no MaxDisplayCount (there is no default cap, and on iOS 26 a popoverTip inside a TabView can re-appear on every tab switch, FB20904972 -- the cap is both the budget and the regression guard)")
        if lc.get("ignores_display_frequency_used"):
            warns.append("TK-4 a tip uses IgnoresDisplayFrequency (reserved for critical tips, and tips must never be critical -- warning only, but the justification must be recorded)")
    av = d.get("availability") or {}
    if not av.get("min_target_ge17") and not (av.get("availability_guard_present") and av.get("fallback_for_below17_recorded")):
        fails.append("TK-5 the deployment target goes below iOS 17 with no availability guard and no recorded fallback (TipKit has no official back-deployment; below-17 users would get either a crash path or a silently absent discovery layer, and neither is a recorded decision)")
    ms = d.get("measurement") or {}
    if ms.get("tip_event_defined") and not ms.get("tip_event_fired"):
        fails.append("TK-6 the tip-lifecycle event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'no tips shown' forever)")
    if not ms.get("tip_event_defined"):
        fails.append("TK-6 no tip-lifecycle event exists at all (TipKit keeps its state on-device and reports nothing to the app's analytics; without the app's own shown / closed / action events, discovery cannot be counted)")
    if not ms.get("adoption_joinable_exposed_vs_not"):
        fails.append("TK-6 tip exposure cannot be joined to feature adoption (exposed vs not-exposed), so whether a tip caused the feature's use -- the only reason the layer exists -- is unmeasurable in principle")
    return fails, warns

def main():
    d = json.load(open(sys.argv[1]))
    fails, warns = check(d)
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print(f"{'PASS' if not fails else 'FAIL'}: {len(fails)} fail(s), {len(warns)} warning(s) -- {d.get('app')}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
