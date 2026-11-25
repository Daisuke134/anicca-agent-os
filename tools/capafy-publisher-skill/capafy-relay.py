#!/usr/bin/env python3
"""Local relay: forwards Capafy platform API requests via curl.

Reason: Python urllib responses from api.capafy.ai are truncated by the
egress proxy on this VM (large JSON bodies cut at ~32-48KB), while curl
receives them intact. The official Publisher CLI supports overriding the
platform base URL via CAPAFY_PLATFORM_BASE_URL, so point it here; every
request is forwarded byte-for-byte to https://api.capafy.ai via curl.
Headers (including Authorization) are passed to curl via stdin config so
the token never appears in a process argument list.
"""
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "https://api.capafy.ai"
HOP_HEADERS = {"host", "content-length", "connection", "keep-alive", "proxy-connection",
               "transfer-encoding", "te", "trailer", "upgrade"}


class Relay(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("[relay] %s\n" % (fmt % args))

    def _handle(self, method):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        url = UPSTREAM + self.path

        config_lines = [f'url = "{url}"', 'silent', 'show-error', 'max-time = 120']
        for key, value in self.headers.items():
            if key.lower() in HOP_HEADERS:
                continue
            esc = value.replace('\\', '\\\\').replace('"', '\\"')
            config_lines.append(f'header = "{key}: {esc}"')
        if method != "GET":
            config_lines.append(f'request = "{method}"')
        config = "\n".join(config_lines).encode()

        import tempfile
        tmpdir = tempfile.mkdtemp(prefix="capafy-relay-")
        body_path = os.path.join(tmpdir, "req.bin")
        hdr_path = os.path.join(tmpdir, "resp.headers")
        out_path = os.path.join(tmpdir, "resp.body")
        try:
            if body is not None:
                with open(body_path, "wb") as fh:
                    fh.write(body)
                config += f'\ndata-binary = "@{body_path}"'.encode()
            cmd = ["curl", "-K", "-", "-D", hdr_path, "-o", out_path,
                   "-w", "%{http_code}"]
            proc = subprocess.run(cmd, input=config, capture_output=True, timeout=150)
            status = int(proc.stdout.decode().strip())
            with open(out_path, "rb") as fh:
                resp_body = fh.read()
            with open(hdr_path, "rb") as fh:
                hdr_raw = fh.read().decode("iso-8859-1", "replace")
            # The dump may contain a proxy CONNECT block first; the real
            # response headers are the LAST block.
            blocks = [b for b in hdr_raw.split("\r\n\r\n") if b.strip()]
            raw_headers = blocks[-1] if blocks else ""
        except subprocess.TimeoutExpired:
            self._respond(504, b'{"error":"relay upstream timeout"}', "application/json")
            return
        except Exception as exc:
            self._respond(502, ('{"error":"relay failure: %s"}' % exc).encode(),
                          "application/json")
            return
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        content_type = "application/json"
        extra = {}
        for line in raw_headers.split("\r\n")[1:]:
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            kl = k.strip().lower()
            if kl == "content-type":
                content_type = v.strip()
            elif kl in ("x-skill-version-status",):
                extra[k.strip()] = v.strip()
        self._respond(status, resp_body, content_type, extra)

    def _respond(self, status, body, content_type, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def do_PATCH(self):
        self._handle("PATCH")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
    ThreadingHTTPServer(("127.0.0.1", port), Relay).serve_forever()
