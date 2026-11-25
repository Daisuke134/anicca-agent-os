#!/usr/bin/env python3
"""accessibility-check: judge App Store Accessibility Nutrition Labels state.
Stdlib only, offline.
Sources read in full 2026-11-14:
 - Apple, Overview of Accessibility Nutrition Labels (App Store Connect Help):
   9 features (VoiceOver, Voice Control, Larger Text, Dark Interface,
   Differentiate Without Color Alone, Sufficient Contrast, Reduced Motion,
   Captions, Audio Descriptions). A label may be claimed only if users can
   complete ALL common tasks with that feature (common tasks = primary
   functionality + first launch + login + purchase + settings). Labels are
   voluntary to start, required over time; if you provide nothing, the
   product-page section still appears saying you have not indicated support.
   Declared features make an app more relevant in searches naming them.
   Responses are per device; keep them accurate and up to date; an
   accessibility URL may be provided. Misleading labels violate Guideline 2.3.
   https://developer.apple.com/help/app-store-connect/manage-app-accessibility/overview-of-accessibility-nutrition-labels
 - Winner I am (874656917) live US product page, read 2026-11-14: a
   "Supported Features" section declares 7 of 9: VoiceOver, Voice Control,
   Larger Text, Dark Interface, Differentiate Without Color Alone,
   Sufficient Contrast, Reduced Motion. Captions and Audio Descriptions
   are NOT claimed.
 - Anicca source read 2026-11-14 (canonical checkout Daisuke134/anicca,
   apps/mobile/anicca-ios, 119 Swift files): accessibilityLabel occurrences
   = 1; accessibilityAddTraits/accessibilityAction = 0; fixed-size fonts
   .font(.system(size:)) = 146 vs semantic text styles = 16;
   accessibilityReduceMotion = 0; accessibilityDifferentiateWithoutColor /
   colorSchemeContrast = 0; legibilityWeight = 0; preferredColorScheme = 0.
   Anicca live US product page, read 2026-11-14: no Supported Features
   section at all (nothing declared).
"""
import json, sys
fails=[]; warns=[]
def fail(g,m): fails.append(f"[{g}] {m}")
def warn(g,m): warns.append(f"[{g}] {m}")
NINE=("voiceover","voice_control","larger_text","dark_interface",
      "differentiate_without_color","sufficient_contrast","reduced_motion",
      "captions","audio_descriptions")
def main(path):
    s=json.load(open(path))
    if not s.get("recorded"): fail("A11Y-0","accessibility state not recorded (unmeasured)")
    rec=s.get("record") or {}
    for k in ("common_tasks_listed","per_device_matrix","declared_labels_read_from_asc","accessibility_url_recorded"):
        if rec.get(k) is not True: fail("A11Y-0",f"record.{k} is not true (Apple: list common tasks, evaluate per device, read your own declarations)")
    declared=set(s.get("declared_labels") or [])
    evidence=s.get("evidence") or {}
    for lab in sorted(declared):
        if lab not in NINE: fail("A11Y-6",f"declared label {lab} is not one of Apple's 9 features")
        if evidence.get(lab) is not True: fail("A11Y-6",f"label {lab} declared without common-task audit evidence (Guideline 2.3: misleading metadata)")
    vo=s.get("voiceover") or {}
    if vo.get("all_interactive_elements_labelled") is not True: fail("A11Y-1","not all interactive elements carry accessibility labels (VoiceOver cannot name them)")
    if vo.get("traits_and_actions_present") is not True: fail("A11Y-1","no accessibility traits/actions in code (custom elements stay inert for VoiceOver/Voice Control)")
    if vo.get("all_common_tasks_completable") is not True: fail("A11Y-1","common tasks not verified completable with VoiceOver alone (Apple's claim bar)")
    if "voiceover" in declared and vo.get("all_common_tasks_completable") is not True: fail("A11Y-1","VoiceOver declared but common-task completion unverified")
    lt=s.get("larger_text") or {}
    if (lt.get("fixed_size_font_count") or 0) > (lt.get("semantic_font_count") or 0): fail("A11Y-2","fixed-size fonts outnumber semantic/Dynamic Type fonts: text cannot scale with the system setting")
    if lt.get("tested_at_200_percent") is not True: fail("A11Y-2","layout not tested at 200% text size (Apple's Larger Text bar)")
    if "larger_text" in declared and lt.get("tested_at_200_percent") is not True: fail("A11Y-2","Larger Text declared but 200% test missing")
    vis=s.get("visual") or {}
    if vis.get("dark_interface_supported") is not True: fail("A11Y-3","dark interface not supported/recorded (winner declares Dark Interface)")
    if vis.get("differentiate_without_color") is not True: fail("A11Y-3","key information may rely on color alone: no Differentiate Without Color Alone support recorded")
    if vis.get("contrast_verified") is not True: fail("A11Y-3","sufficient contrast not verified by measurement (claiming or omitting both need the audit)")
    rm=s.get("reduced_motion") or {}
    if rm.get("respects_reduce_motion_setting") is not True: fail("A11Y-4","animations do not respond to the system Reduce Motion setting (0 code references)")
    cap=s.get("media") or {}
    if cap.get("captions_status_recorded") is not True: fail("A11Y-5","captions status of audio/video content not recorded")
    if "captions" in declared and cap.get("timed_text_available") is not True: fail("A11Y-5","Captions declared but no time-synchronized text exists (misleading)")
    if "audio_descriptions" in declared and cap.get("audio_descriptions_available") is not True: fail("A11Y-5","Audio Descriptions declared but none exist (misleading)")
    if not declared: fail("A11Y-6","no labels declared at all: product page shows no Supported Features section while the winner declares 7 of 9 (undeclared section still displays as 'not indicated' on device)")
    cur=s.get("currency") or {}
    if cur.get("reaudit_each_release") is not True: fail("A11Y-7","labels not re-audited per release (Apple: keep responses accurate and up to date)")
    if cur.get("accessibility_url_provided") is not True: warn("A11Y-7","no accessibility URL provided (Apple offers it so users can learn support details and known gaps)")
    for w_ in warns: print("WARN",w_)
    for f in fails: print("FAIL",f)
    print(f"RESULT {'PASS' if not fails else 'FAIL'} fails={len(fails)} warns={len(warns)}")
    return 0 if not fails else 1
if __name__=="__main__": sys.exit(main(sys.argv[1]))
