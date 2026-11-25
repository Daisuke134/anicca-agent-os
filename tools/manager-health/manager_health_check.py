#!/usr/bin/env python3
"""Manager production health + generation checker (synthetic monitoring).

Probes the production Manager product service (Railway) every run:
  1. GET  /manager/health          (Bearer MANAGER_SERVICE_TOKEN)
       -> default_backend must be 'manager-v1' and generation_available true.
  2. POST /manager/decisions       (Bearer MANAGER_SERVICE_TOKEN,
       x-manager-subject: monitoring-probe, fresh UUID delivery_id)
       -> backend 'manager-v1', policy_version 'manager-generated-v1',
          0 < assigned_probability <= 1, 2..8 candidates.
          A successful probe also proves the InterventionStore accepted a
          new record (decide() inserts before returning), so a stall in
          store writes shows up here as a failure.
  3. POST /manager/push-decisions  (Bearer MANAGER_SENDER_TOKEN,
       subject 'monitoring-probe')
       -> same generation assertions on decisions[0]. This is the exact
          path the APNs sender job uses in production.

Tokens are read in-process from the shared vault
(~/workspace/anicca-ops/credentials.json, entry `anicca_manager_service`)
and are never printed, logged, or written anywhere.

State machine (state.json next to this script):
  - verdict BAD  and (previous OK or last alert > 6h ago) -> alert
  - verdict OK   and previous BAD                          -> recovery alert
Alerts go to Slack #agents-hq (C0CBLBGSBJN) via /opt/hatch/bin/slack and to
GitHub (Daisuke134/anicca-ops issue, deduped by title) via gh, with a
team-outbox file (contents API) as fallback when gh issue fails.

Usage:
  manager_health_check.py            # normal run
  manager_health_check.py --test-alert   # force a BAD verdict through the
                                         # real alert path (self-test)
Exit code: 0 = OK, 2 = BAD, 3 = checker itself could not run.
"""
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_URL = "https://manager-product-production.up.railway.app"
VAULT = Path.home() / "workspace" / "anicca-ops" / "credentials.json"
HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / "state.json"
HISTORY_PATH = HERE / "history.jsonl"
SLACK_BIN = "/opt/hatch/bin/slack"
SLACK_CHANNEL = "C0CBLBGSBJN"  # #agents-hq
GH_REPO = "Daisuke134/anicca-ops"
ISSUE_TITLE = "[manager-health] Manager engine generation DOWN"
REALERT_SEC = 6 * 3600
REQ_TIMEOUT = 60
JST = timezone(timedelta(hours=9))
PROBE_SUBJECT = "monitoring-probe"


def load_tokens():
    data = json.loads(VAULT.read_text())
    entry = data["anicca_manager_service"]
    return entry["MANAGER_SERVICE_TOKEN"], entry["MANAGER_SENDER_TOKEN"]


def http(method, path, token, body=None, extra_headers=None):
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode())
        except Exception:
            payload = {}
        return e.code, payload
    except Exception as e:  # timeout / DNS / tunnel
        return None, {"transport_error": type(e).__name__}


ATTEMPT_LOG = {}


def http_retry(method, path, token, body=None, extra_headers=None, attempts=3):
    """Retry transport failures (no HTTP response at all) with backoff.

    Root cause of the 2026-11-22..24 alert flapping (Issue #520): this
    monitor runs behind the VM's egress proxy, which sporadically drops
    single connections (URLError / RemoteDisconnected / IncompleteRead).
    Railway's own HTTP logs show the engine answering 200 (health in ~6ms)
    at the very moments the old single-attempt probe recorded http=None,
    and the server process has not restarted since its 2026-11-23 deploy.
    An HTTP status — even an error status — is the engine answering and is
    returned immediately; only a missing response is retried, so a BAD
    verdict now requires every attempt to fail.
    """
    delays = [5, 15]
    status, payload = None, {}
    for i in range(attempts):
        status, payload = http(method, path, token, body=body,
                               extra_headers=extra_headers)
        ATTEMPT_LOG[path] = i + 1
        if status is not None:
            break
        if i < attempts - 1:
            time.sleep(delays[min(i, len(delays) - 1)])
    return status, payload


def time_band(now_jst):
    h = now_jst.hour
    if 5 <= h < 11:
        return "morning"
    if 11 <= h < 17:
        return "day"
    if 17 <= h < 23:
        return "evening"
    return "night"


def check_generation_payload(payload):
    """Validate a decide() result without recording generated text."""
    problems = []
    if payload.get("backend") != "manager-v1":
        problems.append(f"backend={payload.get('backend')!r}")
    if payload.get("policy_version") != "manager-generated-v1":
        problems.append(f"policy_version={payload.get('policy_version')!r}")
    p = payload.get("assigned_probability")
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not (0 < p <= 1):
        problems.append(f"assigned_probability={p!r}")
    cands = payload.get("candidates")
    if not isinstance(cands, list) or not (2 <= len(cands) <= 8):
        problems.append("candidates missing or out of range")
    chosen = payload.get("chosen") or {}
    if chosen.get("kind") != "none" and not (isinstance(chosen.get("text"), str) and 0 < len(chosen["text"]) <= 500):
        problems.append("chosen text missing/oversize")
    # A notification (or home word) must never go out wordless: whenever a
    # decision says send, the chosen candidate must carry real text, and
    # the send flag must agree with the chosen kind.
    if payload.get("send") is True and not (isinstance(chosen.get("text"), str) and chosen["text"].strip()):
        problems.append("send=true but chosen text is empty")
    if payload.get("send") is not None and (payload.get("send") is True) != (chosen.get("kind") != "none"):
        problems.append("send flag disagrees with chosen kind")
    return problems


def run_checks(service_token, sender_token):
    now_jst = datetime.now(JST)
    checks = []

    # NOTE: the service's authenticate() returns the x-manager-subject header
    # value; /manager/health 401s when the header is absent even with a valid
    # service token. Always send the probe subject header.
    status, payload = http_retry("GET", "/manager/health", service_token,
                                 extra_headers={"x-manager-subject": PROBE_SUBJECT})
    problems = []
    if status != 200:
        problems.append(f"http={status}")
        if isinstance(payload, dict) and "transport_error" in payload:
            problems.append(payload["transport_error"])
    else:
        if payload.get("default_backend") != "manager-v1":
            problems.append(f"default_backend={payload.get('default_backend')!r}")
        if payload.get("generation_available") is not True:
            problems.append(f"generation_available={payload.get('generation_available')!r}")
        if "transport_error" in payload:
            problems.append(payload["transport_error"])
    checks.append({"name": "health", "ok": not problems, "http": status,
                   "generator_model": payload.get("generator_model"),
                   "no_response": status is None,
                   "attempts": ATTEMPT_LOG.get("/manager/health"),
                   "problems": problems})

    ctx = {"time_band": time_band(now_jst), "language": "en",
           "desired_state": "calm", "source": "daily_home"}
    # The decisions probe MUST use the app's exact request shape. The app
    # (ModelWordsService.today) always adds a `synthetic_user` context key
    # whose answer_ids is a {axis: [ids]} dict, and it sends its own viewed
    # quote IDs back as legacy_recent_message_ids — catalog IDs are dotted
    # ("growth.calm.2"). On 2026-11-23 the backend's answer-value regex
    # excluded the dot, every returning user's home request got HTTP 422,
    # 1.11.0 rendered zero words, and this probe stayed green for hours
    # because its context carried no synthetic_user at all. A probe that
    # does not reproduce the client's request is not monitoring.
    app_ctx = dict(ctx, synthetic_user={
        "answer_ids": {"desired_state": ["calm"], "pain_points": ["stress"],
                       "legacy_recent_message_ids": ["growth.calm.2"]},
        "answer_version": 4})
    status, payload = http_retry("POST", "/manager/decisions", service_token,
                                 body={"delivery_id": str(uuid.uuid4()), "context": app_ctx},
                                 extra_headers={"x-manager-subject": PROBE_SUBJECT})
    problems = []
    if status != 200:
        problems.append(f"http={status}")
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if isinstance(detail, dict) and detail.get("backend"):
            problems.append(f"error_backend={detail['backend']!r}")
        if isinstance(payload, dict) and "transport_error" in payload:
            problems.append(payload["transport_error"])
    else:
        problems = check_generation_payload(payload)
    checks.append({"name": "decisions", "ok": not problems, "http": status,
                   "no_response": status is None,
                   "attempts": ATTEMPT_LOG.get("/manager/decisions"),
                   "problems": problems})

    push_ctx = dict(ctx, source="notification")
    push_state = {"profile": {}, "recent_reactions": [],
                  "local_day": now_jst.strftime("%Y-%m-%d"),
                  "slot": now_jst.strftime("%H:%M")}
    body = {"decisions": [{"subject": PROBE_SUBJECT,
                           "delivery_id": str(uuid.uuid4()),
                           "context": push_ctx, "push_state": push_state}]}
    status, payload = http_retry("POST", "/manager/push-decisions", sender_token, body=body)
    problems = []
    if status != 200:
        problems.append(f"http={status}")
        if isinstance(payload, dict) and "transport_error" in payload:
            problems.append(payload["transport_error"])
    else:
        results = payload.get("decisions")
        if not isinstance(results, list) or len(results) != 1:
            problems.append("decisions[] missing")
        else:
            problems = check_generation_payload(results[0])
    checks.append({"name": "push-decisions", "ok": not problems, "http": status,
                   "no_response": status is None,
                   "attempts": ATTEMPT_LOG.get("/manager/push-decisions"),
                   "problems": problems})
    return checks


def slack_send(text):
    payload = {"channel_id": SLACK_CHANNEL, "message": text}
    proc = subprocess.run(
        [SLACK_BIN, "call-tool", "--name", "slack_send_message",
         "--arguments-json", json.dumps(payload)],
        capture_output=True, text=True, timeout=120)
    out = (proc.stdout or "").strip()
    ok = proc.returncode == 0
    if ok:
        try:
            parsed = json.loads(out)
            result = parsed.get("result", {})
            if result.get("isError"):
                ok = False
        except Exception:
            pass
    return ok, out[-400:]


def gh_issue_alert(body_text, recovery=False):
    """Comment on the open manager-health issue or create it. Returns (ok, info)."""
    title = ISSUE_TITLE if not recovery else ISSUE_TITLE + " — RECOVERED"
    try:
        proc = subprocess.run(
            ["gh", "issue", "list", "--repo", GH_REPO, "--state", "open",
             "--search", "manager-health in:title", "--json", "number,title",
             "--limit", "10"],
            capture_output=True, text=True, timeout=90)
        issues = json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout else []
    except Exception:
        issues = []
    open_nums = [i["number"] for i in issues if i.get("title", "").startswith("[manager-health]")]
    try:
        if open_nums:
            n = open_nums[0]
            proc = subprocess.run(
                ["gh", "issue", "comment", str(n), "--repo", GH_REPO, "--body", body_text],
                capture_output=True, text=True, timeout=90)
            if proc.returncode != 0:
                return False, f"comment on issue #{n} failed"
            if recovery:
                subprocess.run(
                    ["gh", "issue", "close", str(n), "--repo", GH_REPO],
                    capture_output=True, text=True, timeout=90)
                return True, f"commented + closed issue #{n}"
            return True, f"commented issue #{n}"
        proc = subprocess.run(
            ["gh", "issue", "create", "--repo", GH_REPO, "--title", title,
             "--body", body_text],
            capture_output=True, text=True, timeout=90)
        url = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
        return proc.returncode == 0, f"created {url}"
    except Exception as e:
        return False, f"gh error {type(e).__name__}"


def team_outbox_fallback(body_text, stamp):
    """Last-resort GitHub landing: a team-outbox file via the contents API."""
    path = f"team-outbox/muse/to-all-{stamp}-manager-health-alert.md"
    content = body_text
    proc = subprocess.run(
        ["gh", "api", "-X", "PUT", f"repos/{GH_REPO}/contents/{path}",
         "-f", "message=monitor: manager-health alert (fallback landing)",
         "-f", f"content={__import__('base64').b64encode(content.encode()).decode()}"],
        capture_output=True, text=True, timeout=90)
    return proc.returncode == 0, path


def main():
    test_alert = "--test-alert" in sys.argv
    now = datetime.now(timezone.utc)
    now_jst = now.astimezone(JST)
    stamp = now_jst.strftime("%Y-%m-%d-%H%M")

    try:
        service_token, sender_token = load_tokens()
    except Exception as e:
        print(f"CHECKER_ERROR vault read failed: {type(e).__name__}")
        return 3

    if test_alert:
        checks = [{"name": "self-test", "ok": False, "http": None,
                   "problems": ["SIMULATED anomaly for alert-path verification"]}]
    else:
        checks = run_checks(service_token, sender_token)
    verdict_ok = all(c["ok"] for c in checks)

    state = {}
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text())
        except Exception:
            state = {}
    prev_status = state.get("status")
    last_alert_at = state.get("last_alert_at", 0)

    should_alert = False
    recovery = False
    if not verdict_ok:
        if prev_status != "bad" or (time.time() - last_alert_at) > REALERT_SEC or test_alert:
            should_alert = True
    else:
        if prev_status == "bad":
            should_alert = True
            recovery = True

    summary_lines = [f"{c['name']}: {'OK' if c['ok'] else 'FAIL'}"
                     + (f" ({'; '.join(c['problems'])})" if c['problems'] else "")
                     for c in checks]
    # A failure where every failed check got no HTTP response at all (after
    # retries) is a transport/path failure: the engine never answered, so
    # its state is unconfirmed — do not report it as an engine failure.
    failed_checks = [c for c in checks if not c["ok"]]
    failure_kind = None
    if failed_checks:
        failure_kind = ("transport" if all(c.get("no_response") for c in failed_checks)
                        else "engine")
    record = {"ts": now.isoformat(), "verdict": "ok" if verdict_ok else "bad",
              "failure_kind": failure_kind,
              "test_alert": test_alert, "checks": checks, "alerted": False}
    alert_results = {}

    if should_alert:
        head = ("[TEST] Manager monitoring self-test — simulated anomaly. "
                "This is a drill to verify the alert path, not a real incident."
                if test_alert else
                ("Manager engine RECOVERED — generation checks pass again."
                 if recovery else
                 ("Manager engine UNREACHABLE from the monitoring path — no HTTP "
                  "response after retries. Engine state is unconfirmed: past flaps "
                  "of this shape were egress-proxy drops, not engine downtime "
                  "(Issue #520)."
                  if failure_kind == "transport" else
                  "Manager engine generation is DOWN — production is serving prepared words / failing.")))
        body = (f"{head}\n\nTime: {now_jst.strftime('%Y-%m-%d %H:%M JST')}\n"
                f"Target: {BASE_URL}\nChecks:\n- " + "\n- ".join(summary_lines) +
                "\n\nOwner: engine repair lane (Issue #520). Monitoring: anicca monitoring loop "
                "(manager_health_check.py, every 30 min).")
        ok_slack, info_slack = slack_send(body)
        alert_results["slack"] = {"ok": ok_slack, "info": info_slack}
        ok_gh, info_gh = gh_issue_alert(body, recovery=recovery)
        if not ok_gh:
            ok_fb, fb_path = team_outbox_fallback(body, stamp)
            alert_results["github"] = {"ok": ok_fb, "info": f"fallback file {fb_path}" if ok_fb else info_gh}
        else:
            alert_results["github"] = {"ok": ok_gh, "info": info_gh}
        record["alerted"] = True
        record["alert_results"] = alert_results
        if not recovery:
            state["last_alert_at"] = time.time()

    state["status"] = "ok" if verdict_ok else "bad"
    state["updated_at"] = now.isoformat()
    # Atomic state write (temp file + os.replace): the old direct write
    # crashed mid-write on 2026-11-24 (PermissionError) and left state.json
    # at 0 bytes, erasing the previous verdict. A state/history write
    # failure must never kill the checker or mask the verdict.
    import os
    try:
        tmp_path = STATE_PATH.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(state, indent=2))
        os.replace(tmp_path, STATE_PATH)
    except Exception as e:
        print(f"STATE_WRITE_ERROR {type(e).__name__}")
    try:
        with HISTORY_PATH.open("a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"HISTORY_WRITE_ERROR {type(e).__name__}")

    print(f"MANAGER_HEALTH {'OK' if verdict_ok else 'BAD'} | " + " | ".join(summary_lines))
    if alert_results:
        print("ALERTS " + json.dumps(alert_results))
    return 0 if verdict_ok else 2


if __name__ == "__main__":
    sys.exit(main())
