#!/usr/bin/env python3
"""publish-verify: deterministic publication verifier for aniccaai.com pages.

Stdlib only, offline-capable except for the fetches themselves, free.

Why this exists (2026-11-25): the Society Simulation research blog shipped
with 4 figure SVGs that returned HTTP 200 with Content-Length: 0 (empty
files committed to the repo). A status-code-only check reported "all figures
verified HTTP 200" and the founder found the broken images himself on his
phone. The founder's rule: verification is a system (tool + hook), not
vigilance -- "you don't even need to think about it all the time... we just
make it a system." This tool is that system for published pages.

Checks, for the page and for EVERY asset it references (img src / srcset,
og:image, twitter:image, and any linked .svg/.png/.jpg/.jpeg/.webp/.gif):
  1. HTTP status == 200
  2. body bytes > 0            (0-byte body = FAIL, always)
  3. Content-Type consistent with the URL extension
  4. content sniff: SVG body contains "<svg"; PNG starts with the PNG magic
     bytes; JPEG with FFD8FF; GIF with "GIF8"; WebP with RIFF....WEBP;
     HTML contains the expected title string when --title is given.

Exit 0 only if the page and ALL assets pass. Exit 1 otherwise.
Prints a per-asset PASS/FAIL table with byte counts.

Usage:
  publish_verify.py URL [URL ...] [--title "Expected Title"] [--timeout 45]
  publish_verify.py --list-file urls.txt [--title "..."]
"""
import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "anicca-publish-verify/1.0 (+https://aniccaai.com)"

EXT_TYPES = {
    ".svg": ("image/svg+xml",),
    ".png": ("image/png",),
    ".jpg": ("image/jpeg",),
    ".jpeg": ("image/jpeg",),
    ".webp": ("image/webp",),
    ".gif": ("image/gif",),
    ".html": ("text/html",),
    ".htm": ("text/html",),
    "": ("text/html",),  # extensionless page URL
}


def fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for _ in range(2):  # one retry: egress is flaky
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", "") if e.headers else "", e.read() if hasattr(e, "read") else b""
        except Exception as e:  # URLError, timeout, ssl, ...
            last = e
    raise last


def sniff_ok(ext, body):
    """Return (ok, note). Magic/structure check on the actual bytes."""
    if ext == ".svg":
        return (b"<svg" in body[:4096]), "body must contain '<svg'"
    if ext == ".png":
        return body.startswith(b"\x89PNG\r\n\x1a\n"), "PNG magic bytes"
    if ext in (".jpg", ".jpeg"):
        return body.startswith(b"\xff\xd8\xff"), "JPEG magic bytes FFD8FF"
    if ext == ".gif":
        return body.startswith(b"GIF8"), "GIF magic 'GIF8'"
    if ext == ".webp":
        return body[:4] == b"RIFF" and body[8:12] == b"WEBP", "WebP RIFF/WEBP magic"
    return True, "no sniff rule"


def ext_of(url):
    path = urllib.parse.urlparse(url).path.lower()
    for ext in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".html", ".htm"):
        if path.endswith(ext):
            return ext
    return ""


def check_one(url, timeout, title=None, is_page=False):
    """Return (ok, status, nbytes, ctype, reasons[])."""
    reasons = []
    try:
        status, ctype, body = fetch(url, timeout)
    except Exception as e:
        return False, "ERR", 0, "", [f"fetch failed: {type(e).__name__}: {e}"]
    n = len(body)
    ext = ext_of(url)
    if status != 200:
        reasons.append(f"HTTP {status} != 200")
    if n == 0:
        reasons.append("0-byte body (empty file)")
    base_type = (ctype or "").split(";")[0].strip().lower()
    expected = EXT_TYPES.get(ext)
    if expected and base_type and base_type not in expected:
        reasons.append(f"Content-Type '{base_type}' inconsistent with '{ext}' (expected {'/'.join(expected)})")
    if n > 0:
        ok, note = sniff_ok(ext, body)
        if not ok:
            reasons.append(f"content sniff failed: {note}")
    if is_page and title:
        text = body.decode("utf-8", "replace")
        if title not in text:
            reasons.append(f"expected title string not found in HTML: {title!r}")
    return (not reasons), status, n, base_type, reasons


ASSET_PATTERNS = [
    re.compile(r'<img[^>]+src\s*=\s*"([^"]+)"', re.I),
    re.compile(r"<img[^>]+src\s*=\s*'([^']+)'", re.I),
    re.compile(r'<meta[^>]+property\s*=\s*"og:image"[^>]+content\s*=\s*"([^"]+)"', re.I),
    re.compile(r'<meta[^>]+name\s*=\s*"twitter:image"[^>]+content\s*=\s*"([^"]+)"', re.I),
    re.compile(r'(?:src|href)\s*=\s*"([^"]+\.(?:svg|png|jpe?g|webp|gif)(?:\?[^"]*)?)"', re.I),
]


def extract_assets(page_url, html):
    found = []
    seen = set()
    for pat in ASSET_PATTERNS:
        for m in pat.finditer(html):
            u = urllib.parse.urljoin(page_url, m.group(1))
            if u not in seen:
                seen.add(u)
                found.append(u)
    # also srcset first entries
    for m in re.finditer(r'srcset\s*=\s*"([^"]+)"', html, re.I):
        first = m.group(1).split(",")[0].strip().split(" ")[0]
        u = urllib.parse.urljoin(page_url, first)
        if u not in seen:
            seen.add(u)
            found.append(u)
    return found


def main():
    ap = argparse.ArgumentParser(description="Deterministic publication verifier (status + bytes + type + sniff).")
    ap.add_argument("urls", nargs="*", help="page URLs to verify")
    ap.add_argument("--list-file", help="file with one page URL per line")
    ap.add_argument("--title", help="expected title string that each page's HTML must contain")
    ap.add_argument("--timeout", type=float, default=45.0)
    args = ap.parse_args()

    urls = list(args.urls)
    if args.list_file:
        with open(args.list_file) as f:
            urls += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    if not urls:
        ap.error("no URLs given")

    all_ok = True
    for page_url in urls:
        print(f"PAGE {page_url}")
        ok, status, n, ctype, reasons = check_one(page_url, args.timeout, title=args.title, is_page=True)
        verdict = "PASS" if ok else "FAIL"
        print(f"  [{verdict}] page itself            status={status} bytes={n} type={ctype or '-'}"
              + ("" if ok else "  <-- " + "; ".join(reasons)))
        all_ok = all_ok and ok
        if status == 200 and n > 0:
            try:
                _, _, body = fetch(page_url, args.timeout)
                html = body.decode("utf-8", "replace")
            except Exception as e:
                print(f"  [FAIL] could not re-fetch page for asset extraction: {e}")
                all_ok = False
                continue
            assets = extract_assets(page_url, html)
            if not assets:
                print("  (no assets referenced)")
            for a in assets:
                aok, astatus, an, act, areasons = check_one(a, args.timeout)
                averdict = "PASS" if aok else "FAIL"
                print(f"  [{averdict}] {a}  status={astatus} bytes={an} type={act or '-'}"
                      + ("" if aok else "  <-- " + "; ".join(areasons)))
                all_ok = all_ok and aok
        print()
    print("RESULT:", "PASS (all pages and assets verified)" if all_ok else "FAIL (see above)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
