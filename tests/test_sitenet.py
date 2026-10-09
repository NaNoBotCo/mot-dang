#!/usr/bin/env python3
"""The Mot Dang net (sitenet_layer.py, data/curated/sitenet.json). Plain script:

    python3 tests/test_sitenet.py
"""
import json
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sitenet_layer  # noqa: E402
import sites_layer  # noqa: E402

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


net = sitenet_layer.load()
for k in ("th", "en", "lede_th", "lede_en", "machines", "places"):
    check(net.get(k), "sitenet.json: missing %s" % k)
hrefs = [j["href"] for j in net["machines"]["jewels"]]
check(len(hrefs) == len(set(hrefs)), "sitenet.json: a machine file listed twice")
for j in net["machines"]["jewels"]:
    for k in ("href", "th", "en", "line_th", "line_en"):
        check(j.get(k), "sitenet.json: %s lacks %s" % (j.get("href"), k))

with tempfile.TemporaryDirectory() as t:
    docs = pathlib.Path(t)
    (docs / "field").mkdir()
    (docs / "field" / "index.html").write_text("<html><body><main><h1>x</h1></main></body></html>")
    (docs / "colophon.html").write_text("<html><body><p>no main</p></body></html>")
    (docs / "sites").mkdir()
    (docs / "sites" / "index.html").write_text("<html><body><main></main></body></html>")
    sites_layer._REG = None
    sitenet_layer._FOUND.clear()
    n, off = sitenet_layer.inject(docs)
    check(n == 3, "inject: wrote %d pages, expected 3" % n)
    f = (docs / "field" / "index.html").read_text()
    check(f.count("<!--sitenet-->") == 1, "field: one net block")
    check(f.index("<!--sitenet-->") < f.index("</main>"), "field: net sits inside <main>")
    check(re.search(r'<li class="here"><b>.*?Field', f), "field: marked as here")
    check('href="../colophon.html"' in f, "field: sibling linked one level up")
    check('href="../llms.txt"' in f, "field: machine files linked")
    c = (docs / "colophon.html").read_text()
    check(c.index("<!--sitenet-->") < c.index("</body>"), "colophon: falls back to </body>")
    check('href="field/"' in c, "colophon: sibling linked from the root")
    s = (docs / "sites" / "index.html").read_text()
    check('class="here"' not in s, "/sites/: no page marked here")
    sitenet_layer.inject(docs)
    check((docs / "field" / "index.html").read_text() == f, "inject: a second run changes nothing")
    for cid in off:
        card = next(x for x in sites_layer.cards() if x["id"] == cid)
        check(card.get("served") != "docs" or not (docs / card["href"]).exists(),
              "off list: %s has a page" % cid)
    j = sitenet_layer.net_json(docs)
    check(all(x["url"].startswith("http") for s_ in j["strands"] for x in s_["jewels"]),
          "net.json: every jewel carries an absolute url")
    json.dumps(j)
    sites_layer._REG = None

if FAILS:
    print("sitenet: FAIL")
    for m in FAILS:
        print("  -", m)
    sys.exit(1)
print("sitenet: ok")
