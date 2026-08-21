#!/usr/bin/env python3
"""Minimal Chrome DevTools client — evaluate JS in the page on the phone.

stdlib only (no websockets package on this Mac). Speaks just enough RFC 6455
to send one Runtime.evaluate and read the reply.

    python3 cdp.py <ws-url> '<javascript expression>'
"""
import base64, json, os, socket, struct, sys
from urllib.parse import urlparse


def ws_connect(url):
    u = urlparse(url)
    s = socket.create_connection((u.hostname, u.port or 80), timeout=20)
    key = base64.b64encode(os.urandom(16)).decode()
    path = u.path + ("?" + u.query if u.query else "")
    s.sendall(("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
               "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n"
               % (path, u.hostname, u.port or 80, key)).encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            raise RuntimeError("handshake closed")
        buf += chunk
    if b"101" not in buf.split(b"\r\n")[0]:
        raise RuntimeError("handshake failed: %s" % buf.split(b"\r\n")[0])
    return s


def ws_send(s, payload):
    data = payload.encode()
    head = bytearray([0x81])                      # FIN + text
    n = len(data)
    mask = os.urandom(4)
    if n < 126:
        head.append(0x80 | n)
    elif n < 65536:
        head.append(0x80 | 126); head += struct.pack(">H", n)
    else:
        head.append(0x80 | 127); head += struct.pack(">Q", n)
    head += mask
    s.sendall(bytes(head) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def _read(s, n):
    out = b""
    while len(out) < n:
        c = s.recv(n - len(out))
        if not c:
            raise RuntimeError("closed")
        out += c
    return out


def ws_recv(s):
    b1, b2 = _read(s, 2)
    n = b2 & 0x7F
    if n == 126:
        n = struct.unpack(">H", _read(s, 2))[0]
    elif n == 127:
        n = struct.unpack(">Q", _read(s, 8))[0]
    return _read(s, n).decode("utf-8", "replace")


def evaluate(ws_url, expr, timeout=25):
    s = ws_connect(ws_url)
    s.settimeout(timeout)
    ws_send(s, json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
        "expression": expr, "returnByValue": True, "awaitPromise": True}}))
    while True:
        msg = json.loads(ws_recv(s))
        if msg.get("id") == 1:
            s.close()
            r = msg.get("result", {})
            if "exceptionDetails" in r:
                return "EXCEPTION: " + json.dumps(r["exceptionDetails"])[:500]
            return r.get("result", {}).get("value")


if __name__ == "__main__":
    print(evaluate(sys.argv[1], sys.argv[2]))
