#!/usr/bin/env python3
"""A gift from motdang.net/bequeath is used only the ways its use card ticks.

    python3 tests/test_gifts_gate.py            (the fixture cases, then the built site)

The card for each gift the puller took is data/curated/gifts/<gift>.json
(importers/bequeath_pull.py writes it; the gift's points are in
cache/gifts/<gift>/). A layer that puts a gift on a page declares it:

  docs/data/gift_uses.json   {"uses": [{"gift": "g_…", "use": "<use>",
                                        "page": "<path under docs/>",
                                        "credit": "<name printed, or null>"}]}
  and, on that page, the element carries data-gift="g_…" data-use="<use>".

<use> is one of: maps (roads, paths, places built from the gift) ·
public-points (its points or tracks drawn on a public map) · photos (a photo
on a place page) · raw-reuse (its points in a download others may reuse).

This refuses:
  1. a use the card does not tick (public-points unticked, photos unticked,
     raw-reuse under a maps-only licence);
  2. a gift with no card on disk: withdrawn, sealed, held, or not pulled;
  3. a credit other than the card's, or any name on a no-name card;
  4. a data-gift attribute on a page with no matching declaration;
  5. a curated card carrying data (points, places, photos, home) — those live
     in cache/, which the source archive and git leave out;
  6. a gift's folder or points.json copied into docs/.

Nothing in build.py reads gifts yet; this passes on a site that uses none.
The hook, when one does: after build.py, beside test_publish_gate.py.
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USES = ("maps", "public-points", "photos", "raw-reuse")
GIFT_ATTR = re.compile(r'data-gift="(g_[a-z0-9]+)"(?:[^>]*?data-use="([a-z-]+)")?')
DATA_KEYS = ("points", "places", "photos", "home", "tracks")


def cards(root):
    out = {}
    d = Path(root) / "data" / "curated" / "gifts"
    for p in sorted(d.glob("g_*.json")) if d.exists() else []:
        try:
            out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            out[p.stem] = None
    return out


def permitted(card, use):
    u = card.get("uses") or {}
    if use == "raw-reuse":
        return bool(u.get("raw-reuse")) and card.get("licence") in ("cc-by-4.0", "cc0")
    return bool(u.get(use))


def check(root, docs=None, scan_all=False):
    """Every problem found, as lines. Empty means pass."""
    root = Path(root)
    docs = Path(docs) if docs else root / "docs"
    problems = []
    cs = cards(root)

    for gid, c in cs.items():
        if c is None:
            problems.append("data/curated/gifts/%s.json is not JSON" % gid)
            continue
        for k in DATA_KEYS:
            if k in c:
                problems.append("data/curated/gifts/%s.json carries %r — data lives in cache/gifts/, not in the curated card" % (gid, k))

    manifest = docs / "data" / "gift_uses.json"
    declared = []
    if manifest.exists():
        try:
            declared = json.loads(manifest.read_text(encoding="utf-8")).get("uses") or []
        except ValueError:
            problems.append("docs/data/gift_uses.json is not JSON")
    pages = set()
    for u in declared:
        gid, use, page = u.get("gift"), u.get("use"), u.get("page")
        where = "%s on %s" % (gid, page)
        if use not in USES:
            problems.append("%s: unknown use %r" % (where, use))
            continue
        card = cs.get(gid)
        if not card:
            problems.append("%s: no card on disk (withdrawn, sealed, held or not pulled) — the gift cannot be used" % where)
            continue
        if not permitted(card, use):
            problems.append("%s: the card does not tick %s" % (where, use))
        want = card.get("credit")
        got = u.get("credit")
        if want is None and got:
            problems.append("%s: prints the name %r on a no-name card" % (where, got))
        elif want is not None and got is not None and got != want:
            problems.append("%s: credit %r, the card says %r" % (where, got, want))
        if page:
            pages.add(page)

    ok = {(u.get("gift"), u.get("use"), u.get("page")) for u in declared}
    look = set(pages)
    if scan_all and docs.exists():
        look |= {str(p.relative_to(docs)) for p in docs.rglob("*.html")}
    for page in sorted(look):
        p = docs / page
        if not p.is_file():
            if page in pages:
                problems.append("docs/%s is declared in gift_uses.json and not built" % page)
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in GIFT_ATTR.finditer(text):
            gid, use = m.group(1), m.group(2)
            if (gid, use, page) not in ok:
                problems.append("docs/%s: data-gift=%s data-use=%s is not declared in gift_uses.json" % (page, gid, use))
            elif gid not in cs:
                problems.append("docs/%s: gift %s has no card on disk" % (page, gid))

    if docs.exists():
        for p in docs.rglob("points.json"):
            if '"gift_id"' in p.read_text(encoding="utf-8", errors="replace")[:200]:
                problems.append("docs/%s looks like a gift's points.json" % p.relative_to(docs))
        for gid in cs:
            for p in docs.rglob(gid):
                if p.is_dir():
                    problems.append("docs/%s/ holds a gift's files" % p.relative_to(docs))
    return problems


# ---------------------------------------------------------------- the cases
def card(gid, **over):
    c = {"gift_id": gid, "card": {"id": 1, "version": "bequeath-card/1 2026-09-29", "sha": "x" * 64},
         "state": "open", "uses": {"maps": True, "public-points": False, "photos": True, "raw-reuse": True, "credit": "Ant"},
         "licence": "cc-by-4.0", "credit": "Ant", "blur_m": 500, "home_not_found": False,
         "counts": {"points": 10}, "data": "cache/gifts/%s/points.json" % gid}
    c.update(over)
    return c


class Gate(unittest.TestCase):
    def site(self, gifts=(), uses=None, pages=None):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "data" / "curated" / "gifts").mkdir(parents=True)
        (tmp / "docs" / "data").mkdir(parents=True)
        for c in gifts:
            (tmp / "data" / "curated" / "gifts" / ("%s.json" % c["gift_id"])).write_text(json.dumps(c))
        if uses is not None:
            (tmp / "docs" / "data" / "gift_uses.json").write_text(json.dumps({"uses": uses}))
        for name, html in (pages or {}).items():
            (tmp / "docs" / name).parent.mkdir(parents=True, exist_ok=True)
            (tmp / "docs" / name).write_text(html)
        return tmp

    def test_nothing_used_passes(self):
        self.assertEqual(check(self.site([card("g_aaa111")])), [])

    def test_ticked_use_passes(self):
        s = self.site([card("g_aaa111")], [{"gift": "g_aaa111", "use": "maps", "page": "map.html", "credit": "Ant"}],
                      {"map.html": '<div data-gift="g_aaa111" data-use="maps">road</div>'})
        self.assertEqual(check(s), [])

    def test_public_points_unticked_is_refused(self):
        s = self.site([card("g_aaa111")], [{"gift": "g_aaa111", "use": "public-points", "page": "map.html"}],
                      {"map.html": '<svg data-gift="g_aaa111" data-use="public-points"></svg>'})
        self.assertTrue(any("does not tick public-points" in p for p in check(s)))

    def test_photos_unticked_is_refused(self):
        c = card("g_aaa111", uses={"maps": True, "public-points": False, "photos": False, "raw-reuse": True, "credit": "Ant"})
        s = self.site([c], [{"gift": "g_aaa111", "use": "photos", "page": "cm/p/x.html"}], {"cm/p/x.html": "<p></p>"})
        self.assertTrue(any("does not tick photos" in p for p in check(s)))

    def test_maps_only_licence_refuses_reuse(self):
        c = card("g_aaa111", licence="maps-only", uses={"maps": True, "public-points": True, "photos": True, "raw-reuse": False, "credit": "Ant"})
        s = self.site([c], [{"gift": "g_aaa111", "use": "raw-reuse", "page": "source/gifts.html"}], {"source/gifts.html": "x"})
        self.assertTrue(any("does not tick raw-reuse" in p for p in check(s)))

    def test_withdrawn_or_sealed_gift_has_no_card_and_is_refused(self):
        s = self.site([], [{"gift": "g_gone22", "use": "maps", "page": "map.html"}], {"map.html": "x"})
        self.assertTrue(any("no card on disk" in p for p in check(s)))

    def test_wrong_credit_and_name_on_a_no_name_card(self):
        s = self.site([card("g_aaa111"), card("g_bbb222", credit=None)],
                      [{"gift": "g_aaa111", "use": "maps", "page": "a.html", "credit": "Someone Else"},
                       {"gift": "g_bbb222", "use": "maps", "page": "a.html", "credit": "Their Real Name"}],
                      {"a.html": "x"})
        got = check(s)
        self.assertTrue(any("the card says 'Ant'" in p for p in got))
        self.assertTrue(any("no-name card" in p for p in got))

    def test_undeclared_attribute_is_refused(self):
        s = self.site([card("g_aaa111")], [{"gift": "g_aaa111", "use": "maps", "page": "a.html"}],
                      {"a.html": '<i data-gift="g_aaa111" data-use="public-points"></i>'})
        self.assertTrue(any("not declared" in p for p in check(s)))
        s2 = self.site([card("g_aaa111")], [], {"b.html": '<i data-gift="g_aaa111" data-use="maps"></i>'})
        self.assertEqual(check(s2), [])
        self.assertTrue(any("not declared" in p for p in check(s2, scan_all=True)))

    def test_curated_card_carrying_points_is_refused(self):
        s = self.site([card("g_aaa111", points=[[18.8, 98.95]])])
        self.assertTrue(any("carries 'points'" in p for p in check(s)))

    def test_gift_files_in_docs_are_refused(self):
        s = self.site([card("g_aaa111")], pages={"gifts/g_aaa111/points.json": '{"gift_id":"g_aaa111","points":[]}'})
        got = check(s)
        self.assertTrue(any("points.json" in p for p in got))
        self.assertTrue(any("holds a gift's files" in p for p in got))

    def test_the_puller_output_passes_the_gate(self):
        """bequeath_pull writes a card the gate accepts, and its data stays in cache/."""
        sys.path.insert(0, str(ROOT / "importers"))
        import bequeath_pull as bp
        tmp = Path(tempfile.mkdtemp())
        gpx = ('<gpx><trk><trkseg>'
               + "".join('<trkpt lat="%.5f" lon="98.95"><time>2025-01-10T%02d:00:00Z</time></trkpt>' % (18.8 + i * 1e-5, h)
                         for i, h in enumerate((16, 17, 18)))
               + "".join('<trkpt lat="%.4f" lon="%.4f"><time>2025-01-11T01:%02d:00Z</time></trkpt>' % (18.8 - i * 0.002, 98.95 + i * 0.004, i)
                         for i in range(12))
               + '</trkseg></trk></gpx>').encode()
        m = {"gift_id": "g_test0001", "state": "open", "review": "ok",
             "card": {"id": 3, "version": "v", "sha": "s" * 64, "created_at": "2026-09-29",
                      "choices": {"blur_m": 500, "home": "found", "licence": "maps-only", "credit": "none", "credit_name": None},
                      "uses": {"maps": True, "public-points": False, "photos": False, "raw-reuse": False, "credit": None}},
             "home": None, "files": [{"id": "f1", "key": "raw/g_test0001/f1-walk.gpx", "name": "walk.gpx", "kind": "gpx"}]}
        sealed = dict(m, gift_id="g_sealed01", state="sealed")
        (tmp / "data" / "curated" / "gifts").mkdir(parents=True)
        (tmp / "data" / "curated" / "gifts" / "g_sealed01.json").write_text("{}")
        logs = []
        bp.pull(lambda: iter([m, sealed]), lambda k: gpx if k.endswith("walk.gpx") else None, root=tmp, log=logs.append)
        rec = json.loads((tmp / "data" / "curated" / "gifts" / "g_test0001.json").read_text())
        pts = json.loads((tmp / "cache" / "gifts" / "g_test0001" / "points.json").read_text())["points"]
        self.assertFalse((tmp / "data" / "curated" / "gifts" / "g_sealed01.json").exists(), "a sealed gift is taken out")
        self.assertIsNone(rec["credit"])
        self.assertFalse(rec["home_not_found"])
        self.assertGreater(rec["counts"]["cut_near_home"], 3)
        for lat, lon, _ in pts:
            self.assertGreater(bp.metres(18.8, 98.95, lat, lon), 500, "no point within the blur of home")
        self.assertEqual(check(tmp), [])
        (tmp / "docs" / "data").mkdir(parents=True)
        (tmp / "docs" / "data" / "gift_uses.json").write_text(json.dumps({"uses": [{"gift": "g_test0001", "use": "public-points", "page": "m.html"}]}))
        (tmp / "docs" / "m.html").write_text("x")
        self.assertTrue(any("does not tick public-points" in p for p in check(tmp)))


class Site(unittest.TestCase):
    def test_the_built_site(self):
        problems = check(ROOT)
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main(verbosity=2)
