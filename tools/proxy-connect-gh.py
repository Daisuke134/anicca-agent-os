#!/usr/bin/env python3
import os, socket, sys, urllib.parse, base64, threading
host, port = sys.argv[1], int(sys.argv[2])
u = urllib.parse.urlparse(os.environ["HTTPS_PROXY"])
s = socket.create_connection((u.hostname, u.port or 3128), timeout=20)
auth = ""
if u.username:
    auth = "Proxy-Authorization: Basic " + base64.b64encode(f"{urllib.parse.unquote(u.username)}:{urllib.parse.unquote(u.password or '')}".encode()).decode() + "\r\n"
s.sendall(f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n{auth}\r\n".encode())
resp = b""
while b"\r\n\r\n" not in resp:
    chunk = s.recv(1024)
    if not chunk: sys.exit(1)
    resp += chunk
if b" 200 " not in resp.split(b"\r\n")[0]:
    sys.stderr.write(resp.decode(errors="replace")); sys.exit(1)
def pump(src, dst, is_sock_src):
    try:
        while True:
            data = src.recv(65536) if is_sock_src else os.read(src, 65536)
            if not data: break
            dst.sendall(data) if is_sock_src is False else os.write(dst, data)
    except Exception: pass
    try:
        s.shutdown(socket.SHUT_WR) if is_sock_src else None
    except Exception: pass
t = threading.Thread(target=pump, args=(s, 1, True), daemon=True); t.start()
try:
    while True:
        data = os.read(0, 65536)
        if not data: break
        s.sendall(data)
except Exception: pass
t.join(timeout=3)
