#!/usr/bin/env python3
"""controls-check: deterministic gate for iOS 18 Controls
(Control Center / Lock Screen / Action button).
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- Apple WWDC24, Extend your app's controls across the system
  https://developer.apple.com/videos/play/wwdc2024/10157/
  Controls extend app functionality into Control Center, the Lock Screen
  and the Action button via WidgetKit. Two types: buttons perform discrete
  actions (which can include launching the app); toggles change a boolean
  state. A control uses an App Intent to perform its action; a toggle's
  intent is a SetValueIntent. State lives in a shared group container the
  app also reads. Reloads happen on three events: the action is performed
  (finish all updates before perform() returns), the app requests a reload
  via ControlCenter.reloadControls(ofKind:), and a push notification
  invalidates the control. previewValue is predetermined, very quick, and
  corresponds to the off state. displayName must be specific to what the
  control does (the app name is only the default); value text should use
  the domain's words, not the default on/off; an Action button hint starts
  with a verb.
- Emrld Labs, Interactive Widgets and App Intents (full read)
  https://emrldlabs.com/blog/interactive-widgets-app-intents-home-screen-ios-18/
  perform() runs in the widget extension, not the app; the App Group shared
  container is the wire between them and skipping it is why first attempts
  silently fail (the tap works, nothing happens). Write the action once;
  the surfaces (widget, Control Center, Lock Screen, Action button) are
  wrappers over the same capability. First control: one tap, idempotent,
  result obvious at a glance.
- The Swift Dev, Keep an iOS 18 Control Center Toggle in Sync (full read)
  https://www.theswift.dev/posts/control-center-widgetkit-toggle/
  One source of truth: the intent writes it, the value provider reads it,
  the app writes the same place and calls reloadControls(ofKind:) after
  writing; the kind string must match everywhere; gate app-side reload
  calls with #available(iOS 18.0, *) when deployment targets are older.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, core_actions:[]},
 definition:{defined, in_widget_bundle, kind_unique_and_shared,
   control_type, type_matches_real_capability, display_name_specific,
   description_accurate, symbol_meaningful, value_text_truthful},
 action:{intent_is_setvalue_for_toggle, perform_does_real_work,
   perform_persists_before_return},
 state:{provider_reads_real_shared_state, provider_hardcoded,
   preview_is_off_state_and_fast, shared_store_same_for_app_and_extension},
 sync:{app_side_reload_on_change, server_state_involved,
   remote_push_reload_if_server_state},
 availability_privacy:{ios18_gating_correct, fallback_decision_recorded,
   no_sensitive_content, lockscreen_auth_considered},
 measurement:{event_defined, event_fired, per_kind, joinable_to_completion}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("CT-0 controls are not inventoried (which core actions deserve a Control Center / Lock Screen / Action button entry, and what control exists today, are nowhere recorded; an unrecorded system surface cannot be audited)")
    if not (inv.get("core_actions") or []):
        fails.append("CT-0 no core action is named for a control (the app has obvious one-tap actions -- hear today's affirmation, check today's habit -- yet none is named; Apple: controls are quick access to an app's actions, Emrld: pick the most boring one-tap idempotent action first)")
    dfn = d.get("definition") or {}
    defined = bool(dfn.get("defined"))
    if not defined:
        fails.append("CT-1 no control is defined at all (no ControlWidget in the widget extension; the app offers nothing to Control Center, the Lock Screen control slots, or the Action button -- three free system surfaces since iOS 18)")
    else:
        if not dfn.get("in_widget_bundle"):
            fails.append("CT-1 a control type exists but is not added to the WidgetBundle (an unbundled ControlWidget never reaches the controls gallery; Apple adds the control beside the existing widgets in the same bundle)")
        if not dfn.get("kind_unique_and_shared"):
            fails.append("CT-1 the control kind is not a unique identifier shared by every call site (Apple/The Swift Dev: the kind string has to match everywhere -- definition, reload calls, push configuration; a kind referenced only inside its own file cannot be reloaded or invalidated)")
        if not dfn.get("type_matches_real_capability"):
            fails.append("CT-1 the control's type/subject does not match a real capability of the app (buttons are for a discrete action the app actually has, toggles for a boolean state it actually owns; a control for a capability the app does not have is a template, not an entry point)")
        if not dfn.get("display_name_specific"):
            fails.append("CT-1 the displayName is not specific to what the control does (Apple: the app name is only the default -- choose a displayName specific to the action, or people cannot tell the control apart in the gallery)")
        if not dfn.get("description_accurate"):
            fails.append("CT-1 the control description is missing or does not accurately describe this app's control (the description is shown when the control is configured; template or placeholder text there is a false promise at the exact moment of adoption)")
        if not dfn.get("symbol_meaningful"):
            fails.append("CT-1 the symbol does not meaningfully stand for the action (at the small Control Center size and on the Lock Screen only the symbol is shown; a symbol that does not read as the action fails at the only size that matters)")
        if not dfn.get("value_text_truthful"):
            fails.append("CT-1 the value/state text is not truthful domain language (Apple: replace the default on/off with the words people use for the state, and the text must reflect real state -- state text over a hardcoded or empty action claims a state the app does not have)")
    act = d.get("action") or {}
    if defined:
        if dfn.get("control_type") == "toggle" and not act.get("intent_is_setvalue_for_toggle"):
            fails.append("CT-2 a toggle control's intent is not a SetValueIntent (Apple/Emrld: ControlWidgetToggle hands the intent the desired boolean, so it requires a SetValueIntent whose value is the requested state)")
        if not act.get("perform_does_real_work"):
            fails.append("CT-2 the control intent's perform() does no real work (an empty or comment-only perform() means the tap animates and nothing happens -- the exact silent failure Emrld documents; the control is decoration, not an action)")
        if not act.get("perform_persists_before_return"):
            fails.append("CT-2 perform() does not persist the new state to the shared store before returning (Apple: finish all updates before perform() returns, because the system reloads the control at that moment and will re-read whatever is -- or is not -- stored)")
    else:
        fails.append("CT-2 no control action exists at all (no App Intent performs anything from Control Center, the Lock Screen, or the Action button)")
    st = d.get("state") or {}
    if defined:
        if not st.get("provider_reads_real_shared_state"):
            fails.append("CT-3 the value provider does not read the real shared state (the provider is the control's only window on truth; if it does not read the App Group / shared store the app writes, the control displays a fiction)")
        if st.get("provider_hardcoded"):
            fails.append("CT-3 the value provider returns a hardcoded value (a constant state is a lying control: it shows the same state forever, on every device, regardless of what the user did)")
        if not st.get("preview_is_off_state_and_fast"):
            fails.append("CT-3 previewValue is not a predetermined, fast, off-state value (Apple: the preview is shown in the gallery, Lock Screen customization and Action button settings before the control is added; it must return very quickly and correspond to the off state)")
        if not st.get("shared_store_same_for_app_and_extension"):
            fails.append("CT-3 the app and the widget extension do not share one store for this state (Emrld: perform() runs in the extension process with its own sandbox; two copies of the value is why taps silently do nothing -- the App Group container is the wire, not a nicety)")
    sy = d.get("sync") or {}
    if defined:
        if not sy.get("app_side_reload_on_change"):
            fails.append("CT-4 the app never asks the system to reload the control when it changes the same state in-app (Apple/The Swift Dev: write the source of truth first, then ControlCenter.shared.reloadControls(ofKind:); without it the control stays stale until some unrelated reload)")
        if sy.get("server_state_involved") and not sy.get("remote_push_reload_if_server_state"):
            fails.append("CT-4 the control reflects server state but no push handler invalidates it (Apple: the third reload event is a push notification invalidating the control; without it, a change made on another device never reaches this device's control)")
    ap = d.get("availability_privacy") or {}
    if not ap.get("ios18_gating_correct"):
        fails.append("CT-5 the iOS 18 availability gating is missing or wrong (controls are iOS 18+; the control and any app-side reload calls need @available / #available gating when deployment targets include iOS 15-17, or the build breaks for the targets it claims to support)")
    if not ap.get("fallback_decision_recorded"):
        fails.append("CT-5 no recorded decision covers pre-iOS 18 users (deployment targets below 18 exist, so 'controls for 18+, what instead for everyone else' must be a decision, not an accident)")
    if defined and not ap.get("no_sensitive_content"):
        fails.append("CT-5 the control can surface sensitive content on the Lock Screen (Lock Screen controls are reachable without unlocking; personal affirmation text or habit state shown there is a disclosure, not a feature)")
    if defined and not ap.get("lockscreen_auth_considered"):
        fails.append("CT-5 what the control may do from the Lock Screen / Action button without authentication was never considered (these surfaces run before unlock; which actions are safe there -- and which must open the app instead -- is a design decision that must exist)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("CT-6 the control arrival/action event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'controls bring nobody' forever)")
    if not ms.get("event_defined"):
        fails.append("CT-6 no control action/arrival event exists at all (the system reports nothing back, so without the app's own event this free surface's contribution is unknowable in principle)")
    if defined and not ms.get("per_kind"):
        fails.append("CT-6 control use is not measured per control kind (with more than one possible control, an aggregate count cannot say which action earns its Lock Screen / Action button slot)")
    if not ms.get("joinable_to_completion"):
        fails.append("CT-6 control actions cannot be joined to downstream completion (session heard / habit checked / purchase), so whether system-surface entry works cannot be judged")
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
