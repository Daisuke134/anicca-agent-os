#!/usr/bin/env python3
"""Fast reconstruct of fujibee/agmsg via GitHub API with keep-alive + threads.

Token comes from `gh auth token` (used in-process only, never printed/stored).
Writes with retry (VM writes are intermittently EPERM). Idempotent: files
already present with the correct size are skipped.
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

REPO = "fujibee/agmsg"
DEST = os.path.expanduser("~/workspace/tools/agmsg")
TOP_FILES = {
    "SKILL.md", "VERSION", "package.json", "setup.sh", "install.sh",
    "uninstall.sh", "llms.txt", "openai.yaml", "LICENSE", "README.md",
    ".gitignore", ".gitattributes",
}
PREFIXES = ("scripts/", "bin/", ".claude-plugin/")

TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
assert TOKEN, "no gh token"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agmsg-fetch",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            return json.loads(data)
        except Exception:  # noqa: BLE001
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def write_retry(path, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for attempt in range(8):
        try:
            with open(path, "wb") as f:
                f.write(data)
            if os.path.getsize(path) == len(data):
                return
        except OSError:
            pass
        time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"write failed: {path}")


def fetch_one(b):
    p = b["path"]
    dest = os.path.join(DEST, p)
    if os.path.exists(dest) and os.path.getsize(dest) == b["size"]:
        return (p, "skip")
    blob = api(f"repos/{REPO}/git/blobs/{b['sha']}")
    data = base64.b64decode(blob["content"])
    assert len(data) == b["size"], f"size mismatch {p}"
    write_retry(dest, data)
    return (p, "ok")


def _safe(b):
    try:
        return fetch_one(b)
    except Exception as e:  # noqa: BLE001
        return (b["path"], f"ERR {str(e)[:120]}")


def main():
    tree = api(f"repos/{REPO}/git/trees/main?recursive=1")
    blobs = [t for t in tree["tree"] if t["type"] == "blob"]
    wanted = [b for b in blobs if b["path"] in TOP_FILES or b["path"].startswith(PREFIXES)]
    print(f"total={len(blobs)} wanted={len(wanted)}", flush=True)
    ok = skip = 0
    failed = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for p, st in ex.map(_safe, wanted):
            if st == "ok":
                ok += 1
            elif st == "skip":
                skip += 1
            else:
                failed.append((p, st))
            if (ok + skip) % 50 == 0:
                print(f"progress ok={ok} skip={skip} failed={len(failed)}", flush=True)
    print(f"FINISHED ok={ok} skip={skip} failed={len(failed)}")
    for p, e in failed:
        print(f"FAILED {p}: {e}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
