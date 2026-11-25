#!/usr/bin/env python3
"""MSPW record checker for distribution stock packs.

Make Something People Want wiring (2026-11-14): every pack created for the
distribution stock must carry one line in its stock section:

    - MSPW: 誰＝<who, in what state>／瞬間＝<the moment>／欲しいもの＝<what they want>

Usage:
  mspw_check.py check --file <stock.md> --pack <PACK-ID>
      Exit 0 iff that pack's section contains a complete MSPW line
      (all three fields present and non-empty). Exit 1 otherwise.
  mspw_check.py scan --file <stock.md>
      Lists every READY pack section and whether it has a complete MSPW
      line. Informational only; always exit 0.

Deterministic, stdlib only, no network.
"""
import argparse
import re
import sys

FIELDS = ("誰＝", "瞬間＝", "欲しいもの＝")


def sections(text):
    """Yield (heading_line, body_text) for each ### pack section."""
    parts = re.split(r"(?m)^(### .+)$", text)
    # parts: [pre, heading, body, heading, body, ...]
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i]
        body = parts[i + 1]
        # stop body at next ## section heading
        body = re.split(r"(?m)^## ", body)[0]
        yield heading, body


def mspw_status(body):
    """Return (ok, detail) for a pack section body."""
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("- MSPW:"):
            missing = []
            for f in FIELDS:
                idx = s.find(f)
                if idx < 0:
                    missing.append(f)
                    continue
                rest = s[idx + len(f):]
                value = rest.split("／")[0].strip()
                if not value:
                    missing.append(f + "(empty)")
            if missing:
                return False, "MSPW line present but incomplete: " + ", ".join(missing)
            return True, "complete"
    return False, "no MSPW line"


def pack_id_of(heading):
    m = re.match(r"###\s+([^\s［]+)", heading)
    return m.group(1) if m else None


def find_pack(text, pack_id):
    for heading, body in sections(text):
        if pack_id_of(heading) == pack_id:
            return heading, body
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check", "scan"])
    ap.add_argument("--file", required=True)
    ap.add_argument("--pack")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as fh:
        text = fh.read()

    if args.mode == "check":
        if not args.pack:
            print("check mode requires --pack", file=sys.stderr)
            return 2
        heading, body = find_pack(text, args.pack)
        if heading is None:
            print(f"FAIL {args.pack}: section not found")
            return 1
        ok, detail = mspw_status(body)
        print(("PASS " if ok else "FAIL ") + f"{args.pack}: {detail}")
        return 0 if ok else 1

    # scan
    total = ready = with_mspw = 0
    for heading, body in sections(text):
        total += 1
        if "READY" not in heading:
            continue
        ready += 1
        ok, _ = mspw_status(body)
        pid = pack_id_of(heading) or heading
        if ok:
            with_mspw += 1
        print(f"{'MSPW-OK ' if ok else 'MSPW-MISSING '} {pid}")
    print(f"# sections={total} ready={ready} ready_with_mspw={with_mspw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
