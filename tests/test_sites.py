#!/usr/bin/env python3
"""The register (data/curated/sites.json, sites_layer.py). Plain script:

    python3 tests/test_sites.py
"""
import datetime
import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sites_layer  # noqa: E402

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


reg = sites_layer.load()
gkeys = {g["key"] for g in reg["groups"]}
sprite = (ROOT / "docs" / "icons.svg")
icons = set(re.findall(r'id="(i-[a-z0-9-]+)"', sprite.read_text())) if sprite.exists() else set()
need = ("id", "href", "th", "en", "line_th", "line_en", "icon", "group", "where", "served")
seen = set()
for c in reg["cards"]:
    for k in need:
        check(c.get(k) not in (None, ""), f"card {c.get('id')}: no {k}")
    check(c["href"] not in seen, f"card {c['id']}: href twice")
    seen.add(c["href"])
    check(c.get("group") in gkeys, f"card {c['id']}: group {c.get('group')} not in groups")
    check(c.get("where") in ("cm", "cr", "both"), f"card {c['id']}: where")
    check(c.get("served") in ("docs", "worker", "external"), f"card {c['id']}: served")
    check(c["href"].startswith("http") == (c.get("served") == "external"),
          f"card {c['id']}: external href and served disagree")
    if c.get("shipped"):
        datetime.date.fromisoformat(c["shipped"])
    if icons:
        check(c.get("icon") in icons, f"card {c['id']}: icon {c.get('icon')} not in the sprite")
for h, g in reg["pages"]:
    check(g in gkeys, f"page {h}: group {g}")
    check(h not in seen, f"page {h}: also a card")

# best(): six, no repeats, each lane gets a turn
six = sites_layer.best(6)
check(len(six) == 6, "best(6) is not six")
check(len({c["href"] for c in six}) == 6, "best(6) repeats a card")
newest = max((c for c in reg["cards"] if c.get("shipped")), key=lambda c: c["shipped"])
check(newest["shipped"] == six[0]["shipped"] or any(c.get("fav") for c in reg["cards"]),
      "the newest card is not first when there are no picks")

# the gate, against a scratch docs/
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    for c in reg["cards"]:
        if c["served"] == "docs" and c["href"].endswith("/"):
            (d / c["href"]).mkdir(parents=True, exist_ok=True)
            (d / c["href"] / "index.html").write_text("<h1>x</h1>")
    check(sites_layer.unregistered(d) == [], "a carded tree fails the gate")
    (d / "new-thing").mkdir()
    (d / "new-thing" / "index.html").write_text("<h1>x</h1>")
    (d / "sites" / "new-shop").mkdir(parents=True)
    (d / "sites" / "new-shop" / "index.html").write_text("<h1>x</h1>")
    (d / "stray.html").write_text("<h1>x</h1>")
    miss = sites_layer.unregistered(d)
    check(miss == ["new-thing/", "stray.html", "sites/new-shop/"], f"gate missed: {miss}")
    msg = sites_layer.refusal(miss)
    check("fix yourself and return recombobulated" in msg, "refusal lost its message")
    check("sites/new-shop/" in msg, "refusal does not name the path")

    # a card.json inside the site folder counts as its card
    (d / "sites" / "new-shop" / "card.json").write_text(json.dumps(
        {"th": "ร้าน", "en": "Shop", "line_th": "ก", "line_en": "a", "icon": "i-shop",
         "group": "biz", "where": "cm", "shipped": "2026-09-28"}))
    sites_layer._REG = None
    sites_layer.load(d)
    check("sites/new-shop/" not in sites_layer.unregistered(d), "card.json was not read")
    sites_layer._REG = None

# search rows carry every card, absolute
rows = sites_layer.search_rows(ROOT / "docs")["sites"]
check(all(r["u"].startswith("http") for r in rows), "a search row is not absolute")
check(len(rows) >= len(reg["cards"]), "search rows lost cards")

print("register: %d cards, %d pages, %d search rows" % (len(reg["cards"]), len(reg["pages"]), len(rows)))
for f in FAILS:
    print("  FAIL", f)
print("PASS" if not FAILS else "FAIL")
sys.exit(1 if FAILS else 0)
