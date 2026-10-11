"""The front page as it would publish: live motdang.net with this folder's index.html (its style block,
its <main>, its script tags) and assets/front/*.js, and front/*.json from a local bake when one is given.

    python3 tools/front_preview.py [bake_dir] [port]     # bake_dir holds front/events.json, front/when.json …

A scratch bake: mkdir -p DIR/front; python3 -c "import pathlib,front_layer as F; d=pathlib.Path('DIR');
F.bake_events(d,F._index(F.DOCS),{}); F.bake_when(d)". Default port 8768.
"""
import http.server
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets/front"
BAKE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8768
LIVE = "https://motdang.net"
CACHE = {}


def fetch(path):
    if path in CACHE:
        return CACHE[path]
    req = urllib.request.Request(LIVE + path, headers={"User-Agent": "Mozilla/5.0 preview"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out = (r.status, r.headers.get("Content-Type", "application/octet-stream"), r.read())
    except urllib.error.HTTPError as e:
        out = (e.code, e.headers.get("Content-Type", "text/plain"), e.read())
    if out[0] == 200 and not path.startswith("/api") and not path.endswith(".json"):
        CACHE[path] = out
    return out


def front_html():
    html = fetch("/")[2].decode("utf-8")
    local = (ASSETS / "index.html").read_text(encoding="utf-8")
    # the style block up to the language CSS the build fills in; live's own language CSS after it
    lstyle = re.search(r"<style>(.*?)</style>", local, re.S).group(1).partition("{{LANG_CSS}}")[0]
    m = re.search(r"<style>(.*?)</style>", html, re.S)
    anchor = 'html[data-contrast="more"] #veil{display:none}'
    tail = m.group(1).split(anchor, 1)[1] if anchor in m.group(1) else ""
    html = html[:m.start(1)] + lstyle.rstrip() + "\n" + tail + html[m.end(1):]
    # the stage, and the front's script tags, from the local page
    for pat in (r'<section id="stage".*?</section>', r'(?:<script src="/(?:front/[^"]+|feedback\.js)" defer></script>\s*)+'):
        lm, hm = re.search(pat, local, re.S), re.search(pat, html, re.S)
        if lm and hm and "{{" not in lm.group(0):
            html = html[:hm.start()] + lm.group(0) + html[hm.end():]
    # sections the local page has dropped (#fc and #tiles went into the calendar, 2026-10-11)
    for sid in re.findall(r'<section id="([a-z0-9-]+)"', html):
        if f'<section id="{sid}"' not in local:
            html = re.sub(rf'<section id="{sid}".*?</section>', "", html, count=1, flags=re.S)
    return html.encode("utf-8")


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        bare = self.path.split("?")[0]
        try:
            if bare in ("/", "/index.html"):
                body, ct, st = front_html(), "text/html; charset=utf-8", 200
            elif bare.startswith("/front/") and bare.endswith(".js") and (ASSETS / bare[7:]).exists():
                body, ct, st = (ASSETS / bare[7:]).read_bytes(), "application/javascript; charset=utf-8", 200
            elif bare == "/feedback.js":
                body, ct, st = (ROOT / "assets/feedback.js").read_bytes(), "application/javascript; charset=utf-8", 200
            elif BAKE and bare.startswith("/front/") and (BAKE / bare[1:]).exists():
                body, ct, st = (BAKE / bare[1:]).read_bytes(), "application/json", 200
            elif bare.startswith("/fonts/mali"):
                body, ct, st = (ROOT / "assets/fonts" / bare[7:]).read_bytes(), "font/woff2", 200
            else:
                st, ct, body = fetch(self.path)
        except Exception as e:  # noqa: BLE001
            st, ct, body = 502, "text/plain", str(e).encode()
        self.send_response(st)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("front preview on http://127.0.0.1:%d" % PORT, "· bake:", BAKE or "live")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
