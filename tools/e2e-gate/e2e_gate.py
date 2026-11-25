#!/usr/bin/env python3
"""Anicca E2E gate checker.

Deterministic release gate, same family as publish-verify and the
*-check tools: given an app version + build number, decide whether a
FRESH, PASSING Maestro gate-suite run exists for that exact build.

The evidence is a gate record: a JSON file
    <records-dir>/<version>-<build>.json
produced by assembling the CI run's gate-result.json (written by
apps/mobile/anicca-ios/scripts/run-e2e-gate.sh) with the App Store
Connect build metadata (build id + uploadedDate). Records live in
anicca-ops `files/e2e-gate-records/` (canonical, on GitHub).

Exit 0  — the build is certified: every gate flow passed, the
          living-home words-changed check passed, and the run finished
          after the build was created in ASC and within the freshness
          window.
Exit 1  — anything else. Every failed condition is printed by name.

Freshness rule (documented, deliberate):
  * finished_at >= build_created_at  — the run must postdate the
    build's existence; a run from before the build existed cannot
    certify it.
  * now - finished_at <= --max-age-days (default 30) — a run older
    than the window is stale evidence.
  * finished_at may not be in the future (> 5 min clock skew).

Usage:
  e2e_gate.py --version 1.11.2 --build 841
  e2e_gate.py --version 1.11.2 --build 841 --records-dir DIR
  e2e_gate.py --version 1.11.2 --build 841 --now 2026-11-25T00:00:00Z
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

APP_ID = "ai.anicca.app.ios"
REQUIRED_FLOWS = [
    "01-onboarding-first-words",
    "02-paywall-plans",
    "03-living-home-words",
    "03b-living-home-words-changed",
    "04-poyo-on-home",
    "05-settings-round-trip",
]
REQUIRED_EXTRA_CHECKS = ["living-home-words-changed"]
DEFAULT_RECORDS_DIR = os.path.expanduser(
    "~/workspace/anicca-ops-push/files/e2e-gate-records"
)


def parse_ts(value):
    """Parse an ISO-8601 timestamp to an aware UTC datetime, or None."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_record(record, version, build, now, max_age_days):
    """Return a list of (ok, label, detail) verdicts for one record."""
    out = []

    def verdict(ok, label, detail=""):
        out.append((bool(ok), label, detail))

    verdict(record.get("version") == version, "version matches",
            f"record={record.get('version')!r} want={version!r}")
    verdict(record.get("build") == str(build), "build matches",
            f"record={record.get('build')!r} want={str(build)!r}")
    if record.get("app_id") is not None:
        verdict(record.get("app_id") == APP_ID, "app id matches",
                f"record={record.get('app_id')!r}")

    flows = {f.get("name"): f.get("status") for f in record.get("flows", [])}
    for name in REQUIRED_FLOWS:
        status = flows.get(name)
        verdict(status == "passed", f"flow passed: {name}",
                f"status={status!r}" if status != "passed" else "")

    extras = {c.get("name"): c.get("status")
              for c in record.get("extra_checks", [])}
    for name in REQUIRED_EXTRA_CHECKS:
        status = extras.get(name)
        verdict(status == "passed", f"check passed: {name}",
                f"status={status!r}" if status != "passed" else "")

    build_created = parse_ts(record.get("build_created_at"))
    finished = parse_ts(record.get("finished_at"))
    started = parse_ts(record.get("started_at"))
    verdict(build_created is not None, "build_created_at recorded",
            f"value={record.get('build_created_at')!r}")
    verdict(finished is not None, "finished_at recorded",
            f"value={record.get('finished_at')!r}")
    if build_created is not None and finished is not None:
        verdict(finished >= build_created,
                "run finished after the build was created",
                f"finished={finished.isoformat()} build_created={build_created.isoformat()}")
    if started is not None and finished is not None:
        verdict(started <= finished, "run interval sane",
                f"started={started.isoformat()} finished={finished.isoformat()}")
    if finished is not None:
        age = now - finished
        verdict(age <= timedelta(days=max_age_days),
                f"run is fresh (<= {max_age_days} days old)",
                f"age={age.days}d {age.seconds // 3600}h")
        verdict(finished <= now + timedelta(minutes=5),
                "run is not from the future",
                f"finished={finished.isoformat()} now={now.isoformat()}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Anicca E2E gate checker")
    ap.add_argument("--version", required=True)
    ap.add_argument("--build", required=True)
    ap.add_argument("--records-dir",
                    default=os.environ.get("E2E_GATE_RECORDS_DIR",
                                           DEFAULT_RECORDS_DIR))
    ap.add_argument("--max-age-days", type=int, default=30)
    ap.add_argument("--now", default=None,
                    help="ISO timestamp to use as 'now' (testing)")
    args = ap.parse_args()

    now = parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        print(f"FAIL could not parse --now {args.now!r}")
        return 1

    path = os.path.join(args.records_dir, f"{args.version}-{args.build}.json")
    print(f"e2e-gate: {args.version} ({args.build})")
    print(f"  record: {path}")
    if not os.path.isfile(path):
        print("  FAIL no gate record for this build — no passing "
              "Maestro gate run exists")
        print("VERDICT: FAIL")
        return 1
    try:
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"  FAIL gate record unreadable: {e}")
        print("VERDICT: FAIL")
        return 1

    verdicts = check_record(record, args.version, args.build, now,
                            args.max_age_days)
    failed = 0
    for ok, label, detail in verdicts:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        line = f"  {mark} {label}"
        if detail:
            line += f" ({detail})"
        print(line)
    if failed:
        print(f"VERDICT: FAIL ({failed} check(s) failed)")
        return 1
    print("VERDICT: PASS — build is E2E-certified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
