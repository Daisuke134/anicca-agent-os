#!/usr/bin/env python3
"""ProxyCommand helper: CONNECT through the runtime egress proxy on the
Tailscale port (3130) so SSH can reach tailnet addresses (100.64.0.0/10).
Proxy URL (with auth) is read from HTTPS_PROXY; only its port is changed.
Credentials are never printed. Uses raw fds to avoid buffered-IO shutdown
races with the stdin pump thread.
"""
import base64
import os
import socket
import sys
import threading
import urllib.parse


def main() -> int:
    host, port = sys.argv[1], int(sys.argv[2])
    u = urllib.parse.urlparse(os.environ["HTTPS_PROXY"])
    s = socket.create_connection((u.hostname, 3130), timeout=25)
    auth = ""
    if u.username:
        cred = "%s:%s" % (
            urllib.parse.unquote(u.username),
            urllib.parse.unquote(u.password or ""),
        )
        auth = "Proxy-Authorization: Basic %s\r\n" % base64.b64encode(
            cred.encode()
        ).decode()
    s.sendall(
        (
            "CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n%s\r\n"
            % (host, port, host, port, auth)
        ).encode()
    )
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            return 1
        buf += chunk
    head, rest = buf.split(b"\r\n\r\n", 1)
    status_line = head.split(b"\r\n")[0].decode(errors="replace")
    if " 200" not in status_line:
        os.write(2, ("CONNECT failed: %s\n" % status_line).encode())
        return 1
    if rest:
        os.write(1, rest)

    def pump_in() -> None:
        try:
            while True:
                data = os.read(0, 65536)
                if not data:
                    try:
                        s.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                    return
                s.sendall(data)
        except OSError:
            pass

    threading.Thread(target=pump_in, daemon=True).start()
    try:
        while True:
            data = s.recv(65536)
            if not data:
                break
            os.write(1, data)
    except OSError:
        pass
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
