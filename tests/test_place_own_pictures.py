#!/usr/bin/env python3
"""place_own_pictures: a cluster of her photos with no record near it becomes a
record, and a photo inside a market lands on the market and one stall."""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importers"))
import place_own_pictures as po  # noqa: E402


def fake(recs):
    c = po.Catalogue.__new__(po.Catalogue)
    c.recs = recs
    c.by_id = {r["id"]: r for r in recs}
    c.grid = collections.defaultdict(list)
    for r in recs:
        c.grid[c.key(r["lat"], r["lng"])].append(r)
    c.members = collections.defaultdict(list)
    for r in recs:
        inside = (r.get("attrs") or {}).get("insideOfId")
        if inside:
            c.members[inside].append(r["id"])
    return c


def pic(slug, lat, lng, topic, title="", day="2026-10-01"):
    return {"slug": slug, "lat": lat, "lng": lng, "topic": topic, "title": title,
            "description": title, "date": day}


def test_cluster_becomes_record():
    cat = fake([{"id": "cm-osm-node-1", "name": "Wat Far", "nameEn": "Wat Far",
                 "lat": 18.8000, "lng": 99.0000, "cat": ["wat"]}])
    group = [pic("a%d" % i, 18.8020 + i * 0.00005, 99.0000, ["market"]) for i in range(5)]
    cl = [g for d, g in po.clusters(group) if len(g) >= po.MIN_CLUSTER]
    assert len(cl) == 1 and len(cl[0]) == 5
    assert not cat.near(18.8021, 99.0000, po.CLEAR_M)
    pv, rec = po.provisional_record(cat, "2026-10-01", cl[0])
    assert pv == "cm" and rec["id"].startswith("cm-own-20261001-")
    assert rec["attrs"]["provisionalName"] is True
    assert rec["nameEn"] == "Market near Wat Far", rec["nameEn"]
    assert rec["cat"] == ["market"]


def test_street_view_is_not_a_place():
    assert not po.place_like(pic("s", 18.8, 99.0, ["city", "transport"]))


def test_market_photo_lands_on_market():
    mk = {"id": "cm-osm-node-9", "name": "Antique Market", "lat": 18.8, "lng": 99.0, "cat": ["shopping"]}
    st = {"id": "cm-curated-stall", "name": "Stall", "lat": 18.8, "lng": 99.0, "cat": ["shopping"],
          "attrs": {"insideOfId": "cm-osm-node-9"}}
    cat = fake([mk, st])
    r, d = po.by_container(cat, pic("m", 18.80005, 99.0, ["market"], "Trays of amulets"))
    assert r["id"] == "cm-osm-node-9"


def test_weak_word_does_not_name_a_stall():
    st = {"id": "cm-curated-tk", "name": "TK-AMULET 65", "nameEn": "TK-AMULET 65",
          "lat": 18.8, "lng": 99.0, "cat": ["shopping"]}
    r, d = po.by_name(fake([st]), pic("x", 18.8001, 99.0, ["market"], "The long aisle of the amulet market"))
    assert r is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
