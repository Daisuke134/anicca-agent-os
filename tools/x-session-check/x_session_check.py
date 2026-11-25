#!/usr/bin/env python3
import json
import re
import sys
import gzip
import zlib
from html.parser import HTMLParser
from http.cookiejar import CookieJar, Cookie
from urllib import request as urlrequest
from urllib.parse import urlsplit

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

INVALID = "handle: unknown\nname: unknown\nsession: invalid"

HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")


def domain_matches(domain):
    if not isinstance(domain, str):
        return False
    d = domain.lstrip(".").lower()
    return d == "x.com" or d.endswith(".x.com")


def load_cookies(path):
    with open(path, "r", encoding="utf-8") as fh:
        state = json.load(fh)
    if not isinstance(state, dict):
        raise ValueError("bad state")
    cookies = state.get("cookies")
    if not isinstance(cookies, list):
        raise ValueError("bad state")
    return cookies


def build_jar(raw_cookies):
    jar = CookieJar()
    for c in raw_cookies:
        if not isinstance(c, dict):
            continue
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain")
        if not isinstance(name, str) or not isinstance(value, str):
            continue
        if not domain_matches(domain):
            continue
        path = c.get("path") if isinstance(c.get("path"), str) else "/"
        secure = bool(c.get("secure", True))
        d = domain.lstrip(".").lower()
        jar.set_cookie(
            Cookie(
                version=0,
                name=name,
                value=value,
                port=None,
                port_specified=False,
                domain=d,
                domain_specified=True,
                domain_initial_dot=d.startswith("."),
                path=path or "/",
                path_specified=True,
                secure=secure,
                expires=None,
                discard=False,
                comment=None,
                comment_url=None,
                rest={},
            )
        )
    return jar


def ct0_from_jar(jar):
    for c in jar:
        if c.name == "ct0" and c.value:
            return c.value
    return None


def cookie_header_for(jar):
    pairs = []
    for c in jar:
        if domain_matches(c.domain):
            pairs.append("%s=%s" % (c.name, c.value))
    return "; ".join(pairs)


def decode_body(resp):
    data = resp.read()
    enc = (resp.headers.get("Content-Encoding") or "").lower()
    if "gzip" in enc:
        data = gzip.decompress(data)
    elif "deflate" in enc:
        try:
            data = zlib.decompress(data)
        except zlib.error:
            data = zlib.decompress(data, -zlib.MAX_WBITS)
    return data


def make_opener(jar):
    return urlrequest.build_opener(
        urlrequest.HTTPCookieProcessor(jar),
        urlrequest.HTTPRedirectHandler(),
    )


def fetch(opener, url, headers):
    req = urlrequest.Request(url, headers=headers, method="GET")
    return opener.open(req, timeout=20)


def normalize_text(parts):
    return " ".join("".join(parts).split())


class PageParser(HTMLParser):
    """Collect anchor offsets, span text and image alt text from the SSR page."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self._html_len = len(html)
        self._line_starts = [0]
        pos = html.find("\n")
        while pos != -1:
            self._line_starts.append(pos + 1)
            pos = html.find("\n", pos + 1)
        self.spans = []
        self.images = []
        self._open_spans = []

    def _pos(self):
        line, col = self.getpos()
        if 1 <= line <= len(self._line_starts):
            return self._line_starts[line - 1] + col
        return self._html_len

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            attributes = dict(attrs)
            record = {
                "start": self._pos(),
                "end": self._pos(),
                "class": attributes.get("class") or "",
                "parts": [],
            }
            self.spans.append(record)
            self._open_spans.append(record)
        elif tag == "img":
            attributes = dict(attrs)
            self.images.append(
                {"start": self._pos(), "alt": attributes.get("alt") or ""}
            )

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "span":
            self.handle_endtag(tag)

    def handle_data(self, data):
        for record in self._open_spans:
            record["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "span" and self._open_spans:
            record = self._open_spans.pop()
            record["end"] = self._pos()

    def close(self):
        super().close()
        while self._open_spans:
            self._open_spans.pop()["end"] = self._html_len


def extract_identity(html):
    parser = PageParser(html)
    parser.feed(html)
    parser.close()

    for record in parser.spans:
        record["text"] = normalize_text(record["parts"])

    lowered = html.lower()

    def href_present(handle):
        return ('href="/%s"' % handle.lower()) in lowered

    handle = None
    anchor = None

    for record in parser.spans:
        if "text-secondary" not in record["class"]:
            continue
        text = record["text"]
        if not text.startswith("@"):
            continue
        candidate = text[1:]
        if HANDLE_RE.match(candidate) and href_present(candidate):
            handle = candidate
            anchor = record
            break

    if handle is None:
        for image in parser.images:
            alt = image["alt"].strip()
            if not alt.startswith("@"):
                continue
            candidate = alt[1:]
            if HANDLE_RE.match(candidate) and href_present(candidate):
                handle = candidate
                anchor = image
                break

    if handle is None:
        return None

    name = None
    window_start = anchor["start"] - 800
    best = None
    for record in parser.spans:
        if record is anchor:
            continue
        if record["start"] < window_start:
            continue
        if record["start"] >= anchor["start"]:
            continue
        if record["end"] > anchor["start"]:
            continue
        text = record["text"]
        if not text or text.startswith("@"):
            continue
        if best is None or record["end"] > best["end"]:
            best = record

    if best is not None:
        name = best["text"]

    if not name:
        return None
    return handle, name


def main(argv):
    if len(argv) != 2:
        sys.stdout.write(INVALID + "\n")
        return 1

    try:
        raw_cookies = load_cookies(argv[1])
        jar = build_jar(raw_cookies)
    except Exception:
        sys.stdout.write(INVALID + "\n")
        return 1

    opener = make_opener(jar)

    # Step 1: fetch a fresh ct0 from server Set-Cookie headers when possible.
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Cookie": cookie_header_for(jar),
        }
        with fetch(opener, "https://x.com/", headers) as resp:
            try:
                decode_body(resp)
            except Exception:
                pass
    except Exception:
        pass

    # Step 2: fetch the home page and read the account from the SSR HTML.
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Cookie": cookie_header_for(jar),
        }
        with fetch(opener, "https://x.com/home", headers) as resp:
            if resp.status != 200:
                raise ValueError("status")
            final_path = urlsplit(resp.geturl()).path
            if final_path.rstrip("/") != "/home":
                raise ValueError("redirect")
            body = decode_body(resp)
        identity = extract_identity(body.decode("utf-8", "replace"))
        if identity is None:
            raise ValueError("identity")
        screen_name, name = identity
    except Exception:
        sys.stdout.write(INVALID + "\n")
        return 1

    sys.stdout.write(
        "handle: @%s\nname: %s\nsession: valid\n" % (screen_name, name)
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception:
        sys.stdout.write(INVALID + "\n")
        sys.exit(1)
