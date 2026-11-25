#!/usr/bin/env python3
"""Anicca E2E gate watchdog + trigger (runs on a cron tick).

Job A — TRIGGER. For the latest VALID App Store Connect build of each
version that has no gate record yet, dispatch the `anicca-e2e-gate`
GitHub workflow once. When the dispatched run completes, download its
gate-result.json artifact and land the assembled gate record in
anicca-ops `files/e2e-gate-records/`. Failed-flow manifests land too:
failed evidence is still evidence (the checker will fail that build).

Job B — WATCHDOG. For every app version in a review state
(WAITING_FOR_REVIEW / IN_REVIEW / PENDING_DEVELOPER_RELEASE), run the
gate checker against its attached build. If it does not pass and no
alert exists yet, land an alert in anicca-ops
`files/e2e-gate-alerts/` plus a team-outbox note and push. This is the
mechanical tripwire for exactly the 2026-11-25 failure: a version
sitting in review with no E2E behind it.

Fixture mode (--fixtures DIR) replaces asc/gh/git with canned data so
the logic is testable deterministically:
  builds.json   [{version, build, build_id, uploadedDate, processingState}]
  versions.json [{version, state, build}]
  runs.json     [{version, build, conclusion, manifest}]  (optional)
Writes go under --ops-dir (same relative layout as anicca-ops);
dispatches are recorded as marker files, and a runs.json entry for a
dispatched build is treated as its completed workflow run.

Live mode uses: ~/workspace/tools/asc, gh (authenticated), and the
anicca-ops push clone (fetch + rebase before push, never force).
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

APP_ID = "6755129214"
REPO = "Daisuke134/anicca"
WORKFLOW = "anicca-e2e-gate.yml"
REVIEW_STATES = {"WAITING_FOR_REVIEW", "IN_REVIEW",
                 "PENDING_DEVELOPER_RELEASE"}
DISPATCH_WINDOW_DAYS = 14
MAX_DISPATCH_ATTEMPTS = 3
RETRY_AFTER_HOURS = 24

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "e2e_gate", os.path.join(HERE, "e2e_gate.py"))
e2e_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e_gate)


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- ASC
def asc_json(args):
    asc = os.environ.get("ASC_BIN", os.path.expanduser("~/workspace/tools/asc"))
    p = run([asc] + args + ["--output", "json"])
    if p.returncode != 0:
        raise RuntimeError(f"asc {' '.join(args)} failed: {p.stderr.strip()[:300]}")
    return json.loads(p.stdout)


def live_builds():
    """Latest VALID builds: [{version, build, build_id, uploadedDate}]."""
    data = asc_json(["builds", "list", "--app", APP_ID]).get("data", [])
    out = []
    for b in data[:30]:
        attrs = b.get("attributes", {})
        if attrs.get("processingState") != "VALID":
            continue
        info = asc_json(["builds", "info", "--build-id", b["id"]])
        version = None
        for inc in info.get("included", []):
            if inc.get("type") == "preReleaseVersions":
                version = inc.get("attributes", {}).get("version")
        if version:
            out.append({
                "version": version,
                "build": attrs.get("version"),
                "build_id": b["id"],
                "uploadedDate": attrs.get("uploadedDate"),
                "processingState": "VALID",
            })
    return out


def live_versions():
    """Versions in review states: [{version, state, build}]."""
    data = asc_json(["versions", "list", "--app", APP_ID,
                     "--platform", "IOS"]).get("data", [])
    out = []
    for v in data:
        attrs = v.get("attributes", {})
        state = attrs.get("appStoreState")
        if state not in REVIEW_STATES:
            continue
        build = None
        view = asc_json(["versions", "view", "--version-id", v["id"],
                         "--include-build"])
        for inc in view.get("included", []):
            if inc.get("type") == "builds":
                build = inc.get("attributes", {}).get("version")
        out.append({"version": attrs.get("versionString"),
                    "state": state, "build": build})
    return out


# ------------------------------------------------------------------ GH
def gh_dispatch(version, build):
    p = run(["gh", "workflow", "run", WORKFLOW, "--repo", REPO,
             "--ref", "main", "-f", f"version={version}",
             "-f", f"build={build}"])
    if p.returncode != 0:
        raise RuntimeError(f"gh workflow run failed: {p.stderr.strip()[:300]}")


def gh_find_run(dispatched_at):
    """Newest completed gate run created at/after dispatched_at."""
    p = run(["gh", "run", "list", "--repo", REPO, "--workflow", WORKFLOW,
             "--limit", "30", "--json",
             "databaseId,status,conclusion,createdAt,url"])
    if p.returncode != 0:
        return None
    for r in json.loads(p.stdout):
        created = e2e_gate.parse_ts(r.get("createdAt"))
        if (r.get("status") == "completed" and created
                and created >= dispatched_at - timedelta(minutes=5)):
            return r
    return None


def gh_download_manifest(run_id):
    with tempfile.TemporaryDirectory() as tmp:
        p = run(["gh", "run", "download", str(run_id), "--repo", REPO,
                 "--dir", tmp])
        if p.returncode != 0:
            return None
        for root, _dirs, files in os.walk(tmp):
            if "gate-result.json" in files:
                with open(os.path.join(root, "gate-result.json"),
                          encoding="utf-8") as f:
                    return json.load(f)
    return None


# ----------------------------------------------------------------- OPS
class Ops:
    """anicca-ops layout: records, alerts, team-outbox. In live mode
    this is the push clone and changes are committed + pushed."""

    def __init__(self, root, live):
        self.root = root
        self.live = live
        self.records = os.path.join(root, "files", "e2e-gate-records")
        self.alerts = os.path.join(root, "files", "e2e-gate-alerts")
        self.outbox = os.path.join(root, "team-outbox", "muse")
        for d in (self.records, self.alerts, self.outbox):
            os.makedirs(d, exist_ok=True)
        self.dirty = False

    def record_path(self, version, build):
        return os.path.join(self.records, f"{version}-{build}.json")

    def marker_path(self, version, build):
        return os.path.join(self.records, f"{version}-{build}.dispatch.json")

    def has_record(self, version, build):
        return os.path.isfile(self.record_path(version, build))

    def read_record(self, version, build):
        try:
            with open(self.record_path(version, build), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def write_json(self, path, obj):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        self.dirty = True

    def write_text(self, path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        self.dirty = True

    def remove(self, path):
        if os.path.isfile(path):
            os.remove(path)
            self.dirty = True

    def sync_in(self):
        if self.live:
            run(["git", "-C", self.root, "fetch", "origin"], check=False)
            run(["git", "-C", self.root, "rebase", "origin/main"], check=False)

    def sync_out(self, message):
        if not (self.live and self.dirty):
            return
        run(["git", "-C", self.root, "add", "files/e2e-gate-records",
             "files/e2e-gate-alerts", "team-outbox/muse"], check=False)
        c = run(["git", "-C", self.root, "commit", "-m", message])
        if c.returncode != 0:
            print(f"watchdog: nothing to commit ({c.stdout.strip()[:120]})")
            return
        p = run(["git", "-C", self.root, "push", "origin", "main"])
        if p.returncode != 0:
            print(f"watchdog: PUSH FAILED: {p.stderr.strip()[:300]}")
            raise SystemExit(1)
        print(f"watchdog: pushed ({message})")


# -------------------------------------------------------------- LOGIC
def latest_builds_per_version(builds, now):
    by_version = {}
    for b in builds:
        up = e2e_gate.parse_ts(b.get("uploadedDate"))
        if up is None or now - up > timedelta(days=DISPATCH_WINDOW_DAYS):
            continue
        cur = by_version.get(b["version"])
        if cur is None or up > e2e_gate.parse_ts(cur["uploadedDate"]):
            by_version[b["version"]] = b
    return by_version


def assemble_record(manifest, build_info):
    rec = dict(manifest)
    rec["build_id"] = build_info["build_id"]
    uploaded = e2e_gate.parse_ts(build_info.get("uploadedDate"))
    rec["build_created_at"] = iso(uploaded) if uploaded else None
    return rec


def job_trigger(ops, builds, now, dispatch_fn, find_run_fn,
                download_fn, fixture_runs=None):
    actions = []
    for version, b in sorted(latest_builds_per_version(builds, now).items()):
        build = str(b["build"])
        if ops.has_record(version, build):
            continue
        marker_file = ops.marker_path(version, build)
        marker = None
        if os.path.isfile(marker_file):
            with open(marker_file, encoding="utf-8") as f:
                marker = json.load(f)
        if marker is None:
            dispatch_fn(version, build)
            ops.write_json(marker_file, {
                "version": version, "build": build,
                "build_id": b["build_id"],
                "build_created_at": b.get("uploadedDate"),
                "dispatched_at": iso(now), "attempts": 1,
            })
            actions.append(f"dispatched gate workflow for {version} ({build})")
            continue
        # A dispatch is outstanding: look for its completed run.
        dispatched_at = e2e_gate.parse_ts(marker["dispatched_at"])
        manifest = None
        if fixture_runs is not None:
            for r in fixture_runs:
                if (str(r.get("version")) == version
                        and str(r.get("build")) == build):
                    manifest = r.get("manifest")
                    break
        else:
            found = find_run_fn(dispatched_at)
            if found:
                manifest = download_fn(found["databaseId"])
        if manifest:
            ops.write_json(ops.record_path(version, build),
                           assemble_record(manifest, b))
            ops.remove(marker_file)
            actions.append(
                f"landed gate record for {version} ({build}) "
                f"from completed workflow run")
        elif (now - dispatched_at > timedelta(hours=RETRY_AFTER_HOURS)
              and marker.get("attempts", 1) < MAX_DISPATCH_ATTEMPTS):
            dispatch_fn(version, build)
            marker["attempts"] = marker.get("attempts", 1) + 1
            marker["dispatched_at"] = iso(now)
            ops.write_json(marker_file, marker)
            actions.append(
                f"re-dispatched gate workflow for {version} ({build}) "
                f"(attempt {marker['attempts']}, previous run left no manifest)")
    return actions


def job_watchdog(ops, versions, now):
    actions = []
    for v in versions:
        version, build, state = v["version"], v.get("build"), v["state"]
        if not build:
            continue
        build = str(build)
        record = ops.read_record(version, build)
        if record is None:
            verdicts = [(False, "gate record exists",
                         "no record — build was never E2E-certified")]
        else:
            verdicts = e2e_gate.check_record(record, version, build, now, 30)
        failed = [x for x in verdicts if not x[0]]
        if not failed:
            print(f"watchdog: OK {version} ({build}) in {state} — gate passes")
            continue
        alert_file = os.path.join(ops.alerts, f"{version}-{build}.md")
        if os.path.isfile(alert_file):
            print(f"watchdog: {version} ({build}) in {state} — gate FAILS, "
                  "alert already on file")
            continue
        lines = [
            f"# E2E GATE ALERT — {version} (build {build}) is in {state} "
            "without a passing E2E gate",
            "",
            f"- Detected: {iso(now)}",
            f"- App Store state: {state}",
            f"- Version: {version} / build: {build}",
            "",
            "Gate verdicts:",
        ]
        for ok, label, detail in verdicts:
            lines.append(f"- {'PASS' if ok else 'FAIL'} {label}"
                         + (f" ({detail})" if detail else ""))
        lines += [
            "",
            "This is the exact failure of 2026-11-25 (1.11.2 submitted "
            "with CI/unit tests only). Do not let this version proceed: "
            "run the gate suite (workflow `anicca-e2e-gate.yml`), land "
            "a passing record, or withdraw the version from review.",
        ]
        ops.write_text(alert_file, "\n".join(lines) + "\n")
        note = os.path.join(
            ops.outbox,
            f"to-all-{now.strftime('%Y-%m-%d')}-e2e-gate-alert-{version}-{build}.md")
        ops.write_text(note, "\n".join(lines) + "\n")
        actions.append(
            f"ALERT landed: {version} ({build}) in {state} without passing E2E gate")
    return actions


def main() -> int:
    ap = argparse.ArgumentParser(description="Anicca E2E gate watchdog")
    ap.add_argument("--fixtures", default=None,
                    help="fixture dir (builds.json/versions.json/runs.json)")
    ap.add_argument("--ops-dir",
                    default=os.path.expanduser("~/workspace/anicca-ops-push"))
    ap.add_argument("--now", default=None)
    args = ap.parse_args()
    now = e2e_gate.parse_ts(args.now) if args.now else now_utc()
    live = args.fixtures is None
    ops = Ops(args.ops_dir, live)
    ops.sync_in()

    fixture_runs = None
    if live:
        builds = live_builds()
        versions = live_versions()
        dispatch_fn, find_run_fn, download_fn = (
            gh_dispatch, gh_find_run, gh_download_manifest)
    else:
        with open(os.path.join(args.fixtures, "builds.json"),
                  encoding="utf-8") as f:
            builds = json.load(f)
        with open(os.path.join(args.fixtures, "versions.json"),
                  encoding="utf-8") as f:
            versions = [v for v in json.load(f)
                        if v.get("state") in REVIEW_STATES]
        runs_path = os.path.join(args.fixtures, "runs.json")
        fixture_runs = []
        if os.path.isfile(runs_path):
            with open(runs_path, encoding="utf-8") as f:
                fixture_runs = json.load(f)

        def dispatch_fn(version, build):
            print(f"watchdog[fixture]: would dispatch {WORKFLOW} "
                  f"for {version} ({build})")

        find_run_fn = download_fn = None

    actions = job_trigger(ops, builds, now, dispatch_fn, find_run_fn,
                          download_fn, fixture_runs)
    actions += job_watchdog(ops, versions, now)
    for a in actions:
        print(f"watchdog: {a}")
    if not actions:
        print("watchdog: no actions (all builds certified or in flight, "
              "no version in review without a gate)")
    ops.sync_out("e2e-gate watchdog: "
                 + ("; ".join(actions) if actions else "state sync"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
