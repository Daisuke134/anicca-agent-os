# e2e-gate — Anicca's Maestro E2E release gate

A system, not a checklist. Built 2026-11-25 after Anicca 1.11.2 was
submitted to App Store review with CI/unit tests only and no
end-to-end pass. Founder's rule: **no build is submitted for review
without a fresh, passing Maestro gate run for that exact build** —
enforced by machines, not by anyone's memory.

## The pieces

| Piece | Where | What it does |
|---|---|---|
| Gate flows | `Daisuke134/anicca` → `apps/mobile/anicca-ios/maestro/gate/` | Five Maestro flows (tag `e2e-gate`): onboarding → first words; paywall plans; living-home words T0/T1; Poyo on home; settings round-trip |
| Runner | `Daisuke134/anicca` → `apps/mobile/anicca-ios/scripts/run-e2e-gate.sh` | Fresh simulator → build → run flows → prove words change on their own → write `gate-result.json` |
| Workflow | `Daisuke134/anicca` → `.github/workflows/anicca-e2e-gate.yml` | Dispatch with version+build; fails if the built app isn't the requested build; uploads gate evidence |
| Checker | `e2e_gate.py` (here) | Deterministic verdict for a version+build against its gate record. Exit 0 only on a fresh full pass |
| Submit wrapper | `submit_with_gate.sh` (here) | The only sanctioned submission path: runs the checker, refuses to call `asc review submit` on failure |
| Watchdog | `e2e_watchdog.py` (here) + cron `anicca-e2e-gate-watchdog` (30 min) | Auto-dispatches the suite for new VALID builds, lands records, and alerts if any version sits in review without a passing gate |
| Records | anicca-ops `files/e2e-gate-records/<version>-<build>.json` | The canonical evidence the checker reads |
| Alerts | anicca-ops `files/e2e-gate-alerts/` + team-outbox | Watchdog tripwire output |

## Checker contract

```
python3 e2e_gate.py --version 1.11.2 --build 841
```

Exit 0 iff a record exists for that exact version+build AND:
- all six gate flows have status `passed`,
- the `living-home-words-changed` check passed,
- `finished_at >= build_created_at` (the run postdates the ASC build),
- the run is at most `--max-age-days` old (default 30),
- the run is not timestamped in the future.

Fixtures in `fixtures/` cover pass / stale / failed-flow verdicts
(plus the missing-record case). Re-run them any time:

```
python3 e2e_gate.py --version 9.9.9 --build 901 --records-dir fixtures --now 2026-11-25T00:00:00Z   # exit 0
python3 e2e_gate.py --version 9.9.9 --build 902 --records-dir fixtures --now 2026-11-25T00:00:00Z   # exit 1 (stale)
python3 e2e_gate.py --version 9.9.9 --build 903 --records-dir fixtures --now 2026-11-25T00:00:00Z   # exit 1 (flow failed)
```

## Submitting (the only way)

```
./submit_with_gate.sh 1.11.2 841 <ASC_BUILD_ID>
```

## Honest limits

- The gate runs a **simulator build of the identical source commit**
  (same version/build numbers), not the Xcode Cloud device binary
  itself — iOS E2E cannot run the App Store binary. The record pins
  the source commit so the equivalence is auditable.
- Poyo's *expression switching* is not black-box observable (raster
  image, no accessibility value); the gate asserts Poyo's presence on
  the home. Expression mapping is covered by app unit tests.
- Notification attachment rendering is not covered by Maestro; the
  existing notification flows under `maestro/e2e/` remain the
  supplementary lane for that surface.

Reference material: `reference/maestro-testing-skill-SKILL.md`
(limrun-inc/skills@limrun-maestro-testing, 43.8K installs — adopted
as flow-writing reference only; execution here is stock Maestro CLI
on GitHub-hosted macOS runners, per the repo's established pattern).
