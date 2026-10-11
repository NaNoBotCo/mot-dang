#!/usr/bin/env python3
"""commons_layer + data/curated/commons_pool.json: every picture shown carries its credit.

    python3 tests/test_commons_layer.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import commons_layer as C  # noqa: E402

H = {"bi": lambda th, en: '<span class="th">%s</span> · <span class="en">%s</span>' % (th, en),
     "esc": lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
     "att": lambda s: (s or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;"),
     "name_bi": lambda r: r.get("name", "")}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)


pool = json.loads((ROOT / "data/curated/commons_pool.json").read_text())["picks"]
for p in pool:
    for k in ("title", "slug", "page", "licence", "artist", "file", "topic", "place"):
        check(p.get(k) not in (None, ""), "%s: no %s" % (p.get("slug"), k))
    check(re.match(r"(?i)^(cc0|pd|public domain|cc[- ]by(-sa)?[- ]\d)", p.get("licence") or ""),
          "%s: licence %r" % (p["slug"], p.get("licence")))
    check(p["slug"].startswith("c-"), "%s: slug outside the pool's namespace" % p["slug"])

C.bind({"cm": [{"id": "t", "name": "Test", "lat": 18.7877, "lng": 98.9931}]}, {"t": "cm/p/test"})
shown = C.picks()
check(len(shown) > 0, "no usable pool picture on disk")
if shown:
    p0 = next((p for p in shown if p.get("lat") is not None), shown[0])
    rec = {"id": "x", "name": "Somewhere", "lat": p0.get("lat", 18.7877), "lng": p0.get("lng", 98.9931)}
    html = C.around(rec, H)
    check("class=\"cpics\"" in html, "around(): nothing drawn beside a pool picture")
    check("class=\"cred\"" in html and "Wikimedia Commons" in html, "around(): no credit line")
    check('loading="lazy"' in html, "around(): images not lazy")
    check(not EMOJI.search(html), "around(): emoji in markup")
    for a in re.findall(r'<a class="shot" href="([^"]+)"', html):
        check(a.startswith(("../../", "https://commons.wikimedia.org/")), "around(): odd link %s" % a)

if fails:
    print("FAIL test_commons_layer:", len(fails))
    for f in fails[:40]:
        print("  ", f)
    sys.exit(1)
print("ok test_commons_layer: %d pool pictures, %d on disk" % (len(pool), len(shown)))
