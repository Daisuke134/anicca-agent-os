#!/usr/bin/env python3
"""bg-check: deterministic gate for iOS Background Tasks
(BGTaskScheduler: BGAppRefreshTask / BGProcessingTask).
Stdlib only, offline, free. Sources (full-read 2026-11-15):
- 3N Softs, iOS Background Tasks in Production (2026 guide)
  https://www.3nsofts.com/guides/ios-architecture/background-tasks-production-2026
  Register every identifier in BGTaskSchedulerPermittedIdentifiers or
  registration/submission fails; inside the handler call
  task.setTaskCompleted(success:) or iOS marks the task failed and
  deprioritizes that identifier; for recurring refresh submit the NEXT
  request first, before any fallible async work, so the chain survives
  cancellation/expiration; set expirationHandler and cancel promptly,
  leaving durable state consistent; BGProcessingTask declares
  requiresNetworkConnectivity / requiresExternalPower honestly (they are
  workload requirements, not scheduling tricks); check thermalState for
  expensive nonessential work; register only identifiers the app
  genuinely needs; neither task type is a timer -- the system chooses.
- uynguyen, Best practice: iOS background processing (WWDC19/20 digest)
  https://uynguyen.github.io/2020/09/26/Best-practice-iOS-background-processing-Background-App-Refresh-Task/
  BGAppRefreshTask grants ~30s; always call the completion path or the
  system limits future wakeups; read UIApplication.backgroundRefreshStatus
  (the person can disable Background App Refresh per app); tasks do not
  run before first unlock after reboot.
- Reintech, Handling Background Tasks and Multitasking in iOS Apps
  https://reintech.io/blog/handling-background-tasks-multitasking-ios-apps
  Only declare background modes you actually use -- Apple reviews
  background-mode usage and unused declarations can delay approval.
Exit 0 = PASS, 1 = FAIL. Warnings do not fail.
Input JSON: {app,
 inventory:{recorded, refreshable_work:[], permitted_ids:[]},
 registration:{any_registered, all_permitted_ids_registered,
   registered_before_launch_completes, framework_import_used},
 submission:{any_submitted, resubmits_next_before_work,
   earliest_begin_date_set, submit_errors_handled},
 handler:{does_real_work, set_task_completed_called,
   expiration_handler_set, work_cancelable},
 conditions:{refresh_status_checked, declared_modes_all_used,
   processing_requirements_honest, deployment_covers_base},
 measurement:{event_defined, event_fired, per_identifier,
   joinable_to_outcome}}
"""
import json, sys

def check(d):
    fails, warns = [], []
    inv = d.get("inventory") or {}
    if not inv.get("recorded"):
        fails.append("BG-0 background-task state is not inventoried (which work should refresh while the app is closed, which identifiers are permitted, and what is registered today are nowhere recorded; an unrecorded scheduler cannot be audited)")
    if not (inv.get("refreshable_work") or []):
        fails.append("BG-0 no refreshable work is named (a background task needs a real job -- e.g. fetch the next nudges, refresh widget data, sync offerings; naming none means the surface has nothing to do even if registered)")
    if not (inv.get("permitted_ids") or []):
        fails.append("BG-0 no BGTaskSchedulerPermittedIdentifiers are declared in Info.plist (3N Softs: the identifier must appear there or registration/submission fails -- a declared identifier list is the contract the code must fulfil)")
    reg = d.get("registration") or {}
    any_reg = bool(reg.get("any_registered"))
    if not any_reg:
        fails.append("BG-1 no task identifier is registered at all (BGTaskScheduler.shared.register is never called; permitted identifiers in Info.plist plus an unused `import BackgroundTasks` start nothing -- the system can never launch what was never registered, so every declared identifier is a dead promise)")
    else:
        if not reg.get("all_permitted_ids_registered"):
            fails.append("BG-1 not every permitted identifier is registered (an identifier declared in Info.plist with no matching register() call can never run; either register it or remove the declaration -- a half-wired pair is exactly the failure 3N Softs lists first)")
        if not reg.get("registered_before_launch_completes"):
            fails.append("BG-1 registration does not happen before application launch completes (Apple's contract: register in didFinishLaunching; registering later races the system's launch-for-task path and the handler can be missed)")
        if not reg.get("framework_import_used"):
            warns.append("BG-1 BackgroundTasks is imported but the import's symbols are unused in the registering file (dead import -- harmless, but it is the fossil of an unfinished wiring)")
    sub = d.get("submission") or {}
    if any_reg:
        if not sub.get("any_submitted"):
            fails.append("BG-2 no task request is ever submitted (registration alone schedules nothing; without BGTaskScheduler.shared.submit of a BGAppRefreshTaskRequest/BGProcessingTaskRequest the system has no request to honour)")
        else:
            if not sub.get("resubmits_next_before_work"):
                fails.append("BG-2 the handler does not submit the next request before starting its work (3N Softs' first killer mistake: submit next first, before any fallible async work -- if the task is cancelled or expires mid-work, an unsubmitted chain ends forever after one run)")
            if not sub.get("earliest_begin_date_set"):
                fails.append("BG-2 requests carry no earliestBeginDate (the date is only a lower bound, never a promise -- but without it the request is eligible immediately and the cadence intent -- e.g. not before the next nudge window -- is nowhere expressed)")
            if not sub.get("submit_errors_handled"):
                fails.append("BG-2 submit errors are not handled at the call site (submit throws when the identifier is unregistered or called outside the lifecycle; an unhandled throw turns a scheduling bug into a crash or a silent no-op)")
    else:
        fails.append("BG-2 no submission exists at all (no request chain exists to break or keep -- recurring background refresh is absent, not merely fragile)")
    han = d.get("handler") or {}
    if any_reg:
        if not han.get("does_real_work"):
            fails.append("BG-3 the handler does no real work (a handler that returns without fetching/syncing the named refreshable work is a launch the system granted and the app wasted; the system learns the launches are worthless)")
        if not han.get("set_task_completed_called"):
            fails.append("BG-3 setTaskCompleted(success:) is never called (3N Softs: skip it and iOS marks the task failed and deprioritizes future scheduling for that identifier -- the app trains the system to stop waking it)")
        if not han.get("expiration_handler_set"):
            fails.append("BG-3 no expirationHandler is set (when the system reclaims the window, work must stop promptly and leave durable state consistent; without the handler the process is killed mid-write)")
        if not han.get("work_cancelable"):
            fails.append("BG-3 the handler's work is not cancelable (expiration can only be honoured if the underlying operation can actually stop; fire-and-forget tasks ignore the system's one signal)")
    else:
        fails.append("BG-3 no handler exists at all (nothing runs when the system would have granted a window -- for a proactive app this means content only ever refreshes while the person is already looking at it)")
    con = d.get("conditions") or {}
    if not con.get("refresh_status_checked"):
        fails.append("BG-4 UIApplication.backgroundRefreshStatus is never read (the person can disable Background App Refresh for this app in Settings; an app that never reads the status cannot distinguish 'system deprioritized us' from 'the person opted out', and cannot ask honestly)")
    if not con.get("declared_modes_all_used"):
        fails.append("BG-4 a declared UIBackgroundModes entry has no living implementation (Reintech/Apple review practice: declare only modes you actually use -- a 'processing' mode with zero processing tasks is an unused declaration that invites review questions and promises the system a capability that does not exist)")
    if any_reg and not con.get("processing_requirements_honest"):
        fails.append("BG-4 processing-task requirements are not set honestly (requiresNetworkConnectivity/requiresExternalPower are workload requirements, not scheduling tricks; setting external power on light work needlessly narrows eligibility, omitting it on heavy work burns battery)")
    if not con.get("deployment_covers_base"):
        fails.append("BG-4 deployment targets do not cover the BackgroundTasks base (BGTaskScheduler is iOS 13+; a target below that with no availability decision is an accident, not a gate)")
    ms = d.get("measurement") or {}
    if ms.get("event_defined") and not ms.get("event_fired"):
        fails.append("BG-5 the background-task event is defined but fired from 0 call sites (a defined-but-unfired event reads as 'background refresh never happens' forever, indistinguishable from the truth)")
    if not ms.get("event_defined"):
        fails.append("BG-5 no background-task run/completion event exists at all (the system reports scheduling decisions only via device logs; without the app's own event, whether refresh ever ran -- and whether it succeeded -- is unknowable in principle)")
    if any_reg and not ms.get("per_identifier"):
        fails.append("BG-5 runs are not measured per identifier (refresh and nudge-fetch have different jobs and different failure costs; an aggregate count cannot say which chain is alive)")
    if not ms.get("joinable_to_outcome"):
        fails.append("BG-5 background runs cannot be joined to their outcome (next-open content freshness, widget showing today's words, nudge delivered on time), so whether background work earns its battery cannot be judged")
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
