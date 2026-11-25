#!/usr/bin/env python3
"""Read recent inbound SMS to the team Twilio number from THIS VM.

Route: credentials are fetched at runtime from the single source of truth —
anicca-ops `credentials.json` (twilio entry: phone_number / account_sid /
auth_token) via the GitHub API (`gh api`) — then the Twilio Messages API is
called directly from the VM. No Mac involved. The Mac route
(~/workspace/tools/mac-ssh + ~/.secrets/twilio) remains only as a backup.

Output safety: credential values are never printed, and message bodies are
redacted — any run of 4+ digits (e.g. 2FA codes) is masked as ******.

Usage:
  python3 twilio_sms.py [--limit N]
"""
import argparse, base64, json, re, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

REPO = "Daisuke134/anicca-ops"
JST = timezone(timedelta(hours=9))

def load_twilio_creds():
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/credentials.json"],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit("ERROR: could not fetch credentials.json via gh api")
    blob = json.loads(r.stdout)
    data = json.loads(base64.b64decode(blob["content"]))
    for e in data.get("credentials", []):
        if isinstance(e, dict) and "twilio" in str(e.get("service", "")).lower() \
           and e.get("account_sid") and e.get("auth_token") and e.get("phone_number"):
            return e["account_sid"], e["auth_token"], e["phone_number"]
    sys.exit("ERROR: no complete twilio entry (account_sid/auth_token/phone_number) in vault")

def redact(body: str) -> str:
    body = re.sub(r"\d{4,}", "******", body or "")
    return " ".join(body.split())[:100]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    sid, token, number = load_twilio_creds()
    q = urllib.parse.urlencode({"To": number, "PageSize": args.limit})
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json?{q}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR: Twilio API HTTP {e.code}")
    except Exception as e:
        sys.exit(f"ERROR: Twilio API request failed: {type(e).__name__}")

    msgs = payload.get("messages", [])
    print(f"inbound SMS to team number (latest {len(msgs)}):")
    for m in msgs:
        if m.get("direction") not in ("inbound", "received"):
            continue
        dt = m.get("date_sent") or ""
        try:
            d = datetime.strptime(dt, "%a, %d %b %Y %H:%M:%S %z").astimezone(JST)
            when = d.strftime("%Y-%m-%d %H:%M JST")
        except Exception:
            when = dt
        print(f"- {when} | from {m.get('from','?')} | {redact(m.get('body',''))}")

if __name__ == "__main__":
    main()
