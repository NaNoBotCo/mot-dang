"""The fleet search's crawler and wiring.

    python3 tests/test_fleetsearch.py

The extractor is run over pages written here, so nothing depends on a build;
the MATCH strings the JS planner emits (node tests/test_fleetsearch.js --dump)
are executed against the local twin when it exists, so a string that parses in
node and breaks in SQLite is still caught. The Worker and wrangler wiring is
read as text: the route, the binding, the parameter list.
"""
from __future__ import annotations

import inspect
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fleetsearch"))
import crawl  # noqa: E402

TWIN = ROOT / "cache" / "fleetsearch" / "fleet.sqlite"
PAGE = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">
<title>ตอกเส้นบ้านพ่อครูดาว · Tok Sen Kru Dao — มดแดง</title>
<meta name="description" content="นวดตอกเส้น ล้านนา เปิด 10:00–22:00">
<link rel="canonical" href="{canon}">
<style>.x{{color:red}}</style><script>var a="hidden words";</script>
</head><body><header><nav>chrome words</nav></header>
<main><h1>ตอกเส้นบ้านพ่อครูดาว</h1><p>ถนนนิมมานเหมินท์ เชียงใหม่ · Nimman Road, Chiang Mai.</p>
<svg><text>svg words</text></svg></main>
<footer>footer words</footer></body></html>"""


def site(tmp_path, canon="https://motdang.net/cm/p/kru-dao.html"):
    root = tmp_path / "docs"
    (root / "cm" / "p").mkdir(parents=True)
    (root / "cm" / "p" / "kru-dao.html").write_text(PAGE.format(canon=canon), encoding="utf-8")
    (root / "index.html").write_text(PAGE.format(canon="https://elsewhere.example/"), encoding="utf-8")
    (root / "hidden.html").write_text(
        PAGE.format(canon="x").replace("<title>", '<meta name="robots" content="noindex"><title>'), encoding="utf-8")
    (root / "blank.html").write_text("<html><head><title></title></head><body>x</body></html>", encoding="utf-8")
    (root / "404.html").write_text(PAGE.format(canon="x"), encoding="utf-8")
    return root


def test_extract_reads_title_abstract_and_text(tmp_path):
    root = site(tmp_path)
    row = crawl.extract(root / "cm" / "p" / "kru-dao.html", "motdang", "https://motdang.net/", root, {})
    assert row["url"] == "https://motdang.net/cm/p/kru-dao.html"
    assert row["title"].startswith("ตอกเส้นบ้านพ่อครูดาว")
    assert row["abstract"] == "นวดตอกเส้น ล้านนา เปิด 10:00–22:00"
    assert row["site"] == "motdang" and row["host"] == "motdang.net"
    for hidden in ("hidden words", "svg words", "chrome words", "footer words", "color:red"):
        assert hidden not in row["body_s"]
    assert "Nimman Road" in row["body_s"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["lastmod"])


def test_thai_is_spaced_by_the_dictionary(tmp_path):
    root = site(tmp_path)
    row = crawl.extract(root / "cm" / "p" / "kru-dao.html", "motdang", "https://motdang.net/", root, {})
    assert "ตอกเส้น " in row["title_s"]          # one dictionary word, then a space
    assert "เชียงใหม่" in row["body_s"]
    assert " " in crawl.tokenise("ร้านกาแฟนิมมาน")


def test_index_html_is_the_directory_and_a_foreign_canonical_loses(tmp_path):
    root = site(tmp_path)
    row = crawl.extract(root / "index.html", "motdang", "https://motdang.net/", root, {})
    assert row["url"] == "https://motdang.net/"


def test_own_canonical_wins(tmp_path):
    root = site(tmp_path, canon="https://motdang.net/cm/p/kru-dao-canonical.html")
    row = crawl.extract(root / "cm" / "p" / "kru-dao.html", "motdang", "https://motdang.net/", root, {})
    assert row["url"].endswith("kru-dao-canonical.html")


def test_noindex_untitled_and_404_are_skipped(tmp_path):
    root = site(tmp_path)
    assert crawl.extract(root / "hidden.html", "motdang", "https://motdang.net/", root, {}) is None
    assert crawl.extract(root / "blank.html", "motdang", "https://motdang.net/", root, {}) is None
    assert "404.html" not in {p.name for p in crawl.walk(root)}


def test_sitemap_lastmod_beats_mtime(tmp_path):
    root = site(tmp_path)
    (root / "sitemap.xml").write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url>'
        "<loc>https://motdang.net/cm/p/kru-dao.html</loc><lastmod>2025-01-02T03:04:05Z</lastmod>"
        "</url></urlset>", encoding="utf-8")
    lm = crawl.sitemap_lastmods(root)
    row = crawl.extract(root / "cm" / "p" / "kru-dao.html", "motdang", "https://motdang.net/", root, lm)
    assert row["lastmod"] == "2025-01-02"


PLACE = """<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">
<title>Wawee Coffee — กาแฟ-คาเฟ่ เชียงใหม่ · มดแดง Mot Dang</title>
<meta name="description" content="Wawee Coffee · กาแฟ-คาเฟ่">
<meta property="og:image" content="https://motdang.net/card.png">
<script type="application/ld+json">{"@type": "Restaurant", "name": "Wawee Coffee", "geo": {"@type": "GeoCoordinates", "latitude": 18.8000906, "longitude": 99.0183907}}</script>
<script type="application/ld+json">{"@type": "BreadcrumbList", "itemListElement": [
 {"@type": "ListItem", "position": 1, "name": "หน้าแรก", "item": "https://motdang.net/"},
 {"@type": "ListItem", "position": 2, "name": "เชียงใหม่", "item": "https://motdang.net/cm/index.html"},
 {"@type": "ListItem", "position": 3, "name": "ร้านอาหาร-ของกิน", "item": "https://motdang.net/cm/food/index.html"},
 {"@type": "ListItem", "position": 4, "name": "Wawee Coffee", "item": "https://motdang.net/cm/p/wawee.html"}]}</script>
</head><body><main><h1>Wawee Coffee</h1>
<div class="whatson"><h2>What is on here</h2><ul><li><b>Nomad Dinner</b>
<a class="evcal small" href="data:text/calendar;base64,{ics}" download="x.ics">🗓</a></li></ul>
</main></body></html>"""
ICS = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART;TZID=Asia/Bangkok:20260912T190000\r\n"
       "RRULE:FREQ=WEEKLY;BYDAY=SA\r\nSUMMARY:Nomad Dinner\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")


def place_site(tmp_path, twin):
    import base64
    root = tmp_path / "docs"
    (root / "cm" / "p").mkdir(parents=True)
    (root / "photos").mkdir()
    (root / "photos" / "w.jpg").write_bytes(b"x")
    page = PLACE.replace("{ics}", base64.b64encode(ICS.encode()).decode())
    (root / "cm" / "p" / "wawee.html").write_text(page, encoding="utf-8")
    (root / "cm" / "p" / "wawee.json").write_text(json.dumps(twin, ensure_ascii=False), encoding="utf-8")
    return root


def test_a_place_row_carries_its_crumbs_ways_events_and_picture(tmp_path):
    root = place_site(tmp_path, {
        "sub": ["cafe"], "cat": ["food"],
        "channels": [{"kind": "web"}, {"kind": "phone"}, {"kind": "line"}],
        "facets": {"wifi": "field", "toilethere": "field"},
        "sched": [[480, 1080]],
        "photo": {"url": "https://motdang.net/photos/w.jpg", "author": "Nan", "license": "CC BY 4.0"}})
    row = crawl.extract(root / "cm" / "p" / "wawee.html", "motdang", "https://motdang.net/", root, {})
    assert row["kind"] == "place"
    assert [c[0] for c in row["crumbs"]] == ["เชียงใหม่", "ร้านอาหาร-ของกิน"]      # no front page, no self
    assert row["crumbs"][0][2] == "Chiang Mai"
    rich = row["rich"]
    assert rich["ways"] == ["phone", "line", "web"]                              # the place page's order
    assert rich["toilet"] == ["r", "มีห้องน้ำ", "toilet"]
    assert [f[0] for f in rich["fac"]] == ["wifi", "toilethere"]
    assert rich["sched"] == [[480, 1080]]
    assert rich["ev"] == [{"d": "2026-09-12", "w": [5], "t": "Nomad Dinner"}]
    assert row["img"] == "file:" + str((root / "photos" / "w.jpg").resolve())
    assert rich["credit"] == "Nan · CC BY 4.0"


def toilets_fixture():
    """A Toilets with the live model's `stated` table, and a minisite of two
    rows: a wat anyone may walk into (a strong tier) and a café (customers)."""
    t = crawl.Toilets.__new__(crawl.Toilets)
    model = json.loads((ROOT / "data" / "toilets.json").read_text(encoding="utf-8"))
    t.stated, t.reports = model.get("stated") or {}, {}
    wat = {"key": "wat", "access": "public", "strength": "strong"}
    cafe = {"key": "sitdown", "access": "customer", "strength": "medium"}
    t.tiers = [wat, cafe]
    t.baked_said = False
    t.by_id = {"cm-wat": (wat, "", None), "cm-cafe": (cafe, "", None), "cm-shut": (wat, "toiletnone", None)}
    t.grid = {}
    t._put(t.grid, 18.80000, 99.00000, ("วัดเกต", "cm-wat", "place"))
    t._put(t.grid, 18.80100, 99.00000, ("ห้องน้ำสาธารณะ", "", "mapped"))
    return t


def test_toilets_follow_the_minisite_and_nans_word():
    t = toilets_fixture()
    assert t.of({"id": "cm-shut", "cat": ["wat"], "name": "วัดหนึ่ง"}, {}) is None       # somebody stood there
    assert t.of({"id": "x"}, {"toiletfee5": "field"}) == ["r", "ห้องน้ำ 5 บาท", "toilet, 5 baht"]
    assert t.of({"id": "cm-cafe", "sub": ["cafe"]}, {}) is None                        # customers only: not said
    said = lambda rec: (t.of(rec, {}) or [None])[0]                                    # noqa: E731
    # Nan, 2026-09-23
    assert said({"id": "a", "sub": ["fuel"], "name": "PTT Station", "attrs": {"brand": "PTT"}}) == "s"
    assert said({"id": "b", "sub": ["fuel"], "name": "ปั๊ม", "attrs": {"brand": "ป.ต.ท."}}) == "s"
    assert said({"id": "c", "sub": ["fuel"], "name": "PT Max", "attrs": {"brand": "PT"}}) is None
    assert said({"id": "d", "cat": ["wat"], "name": "วัดเจดีย์หลวง"}) == "s"
    assert said({"id": "e", "cat": ["wat"], "name": "Wat Phaya Chomphu"}) == "s"
    assert said({"id": "f", "cat": ["wat"], "name": "วัดร้างสันป่าตึง"}) is None
    assert said({"id": "g", "cat": ["wat"], "sub": ["shrine"], "name": "ศาลเจ้า"}) is None
    assert said({"id": "h", "cat": ["market"], "name": "กาดหลวง"}) == "s"
    assert said({"id": "i", "sub": ["hotel-full"], "name": "Big", "attrs": {"stars": "5"}}) == "s"
    assert said({"id": "j", "sub": ["hotel-full"], "name": "Small guesthouse"}) is None
    assert said({"id": "k", "sub": ["mall"], "name": "Central Festival"}) == "s"
    assert said({"id": "l", "sub": ["wholesale"], "name": "Makro (แม็คโคร)"}) == "s"
    assert said({"id": "m", "sub": ["fresh"], "name": "บิ๊กซี บ้านดู่"}) == "s"
    assert said({"id": "n", "sub": ["convenience"], "name": "มินิบิ๊กซี สาขาชลประทาน"}) is None
    assert said({"id": "o", "sub": ["pharmacy"], "name": "วัตสันฟาร์มาซี สาขา บิ๊กซี"}) is None
    assert said({"id": "q", "sub": ["cafe"], "name": "Big Coffee"}) is None             # a word boundary
    assert said({"id": "r", "sub": ["photo"], "name": "BIG Camera"}) is None
    assert said({"id": "s", "sub": ["mall"], "name": "Big C-บิ๊กซีหางดงแม่เหียะ"}) == "s"
    # once the minisite bakes its own match, that is the one used
    t.baked_said, t.by_id["cm-said"] = True, (None, "", {"key": "wat", "th": "มีห้องน้ำ ตามเวลาเปิด", "en": "x"})
    assert t.of({"id": "cm-said"}, {}) == ["s", "มีห้องน้ำ ตามเวลาเปิด", "x"]
    assert t.of({"id": "zz", "sub": ["mall"], "name": "Central"}, {}) is None          # baked says nothing: nothing
    t.baked_said = False
    assert said({"id": "cm-osm-node-2300400256", "name": "The Garden Restaurant & Guest House"}) == "s"
    assert t.of({"id": "cm-wat", "cat": ["temple-ish"]}, {}) == ["h", "ปกติมีห้องน้ำ", "usually a toilet"]
    # the nearest one, from an exact pin only
    rec = {"id": "p", "lat": 18.8005, "lng": 99.0, "geoPrecision": "exact"}
    assert t.near(rec) == ["n", "วัดเกต", 60]
    assert t.near({**rec, "geoPrecision": "tambon"}) is None
    assert t.near({**rec, "lat": 18.80001}) == ["n", "ห้องน้ำสาธารณะ", 110]         # 1 m off the wat: a centroid, not a neighbour
    assert t.near({**rec, "lat": 18.9}) is None


def test_a_toilet_nobody_reports_is_left_unsaid(tmp_path):
    root2 = place_site(tmp_path / "b", {"sub": ["fuel"], "facets": {"toiletnone": "field"}})
    row2 = crawl.extract(root2 / "cm" / "p" / "wawee.html", "motdang", "https://motdang.net/", root2, {})
    assert "toilet" not in row2["rich"]                                         # somebody looked: none


def test_a_share_card_is_not_a_picture(tmp_path):
    root = place_site(tmp_path, {"sub": ["cafe"]})
    row = crawl.extract(root / "cm" / "p" / "wawee.html", "motdang", "https://motdang.net/", root, {})
    assert row["img"] == ""                                                     # og:image is card.png
    for u in ("https://x.org/cards/place__a.jpg", "/og/shelf-cm.png", "/logo/motdang.svg", "og.jpg"):
        assert crawl.RE_NOT_PICTURE.search(u), u
    assert not crawl.RE_NOT_PICTURE.search("/muay-thai/images/te-chiang/kick.jpg")


def test_images_resolve_three_ways(tmp_path):
    root = tmp_path / "docs"
    (root / "images" / "a").mkdir(parents=True)
    (root / "images" / "a" / "p.jpg").write_bytes(b"x")
    (root / "place" / "b").mkdir(parents=True)
    page = root / "place" / "b" / "index.html"
    base = "https://nanobotco.github.io/basque-tables/"
    want = "file:" + str((root / "images" / "a" / "p.jpg").resolve())
    assert crawl.resolve_img("/basque-tables/images/a/p.jpg", page, root, base) == want
    assert crawl.resolve_img("../../images/a/p.jpg", page, root, base) == want
    assert crawl.resolve_img(base + "images/a/p.jpg", page, root, base) == want
    assert crawl.resolve_img("https://iiif.example/x/full/1200,/0/default.jpg", page, root, base).startswith("https://iiif")
    assert crawl.resolve_img("../../../../etc/passwd", page, root, base) == ""  # never outside the build


def test_the_cell_keeps_its_pin_in_the_middle_half():
    sys.path.insert(0, str(ROOT / "fleetsearch"))
    import thumbs  # noqa: E402
    import random
    rnd = random.Random(4)
    for _ in range(2000):
        _, _, fx, fy = thumbs.cell_of(rnd.uniform(17.5, 20.3), rnd.uniform(97.5, 100.5))
        assert 0.25 <= fx < 0.75 and 0.25 <= fy < 0.75, (fx, fy)
    assert thumbs.cell_of(18.8000906, 99.0183907)[:2] == (50793, 29281)      # the JS test's cell
    assert thumbs.remote_small("https://iiif-content.crossasia.org/xasia/dlntm+1+1_2/full/1200,/0/default.jpg") \
        == "https://iiif-content.crossasia.org/xasia/dlntm+1+1_2/full/!300,300/0/default.jpg"
    assert thumbs.remote_small("https://upload.wikimedia.org/wikipedia/commons/a/ab/Wat_X.jpg") \
        == "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Wat_X.jpg/330px-Wat_X.jpg"
    assert thumbs.remote_small("https://elsewhere.example/a.jpg") == ""


def test_events_to_come_and_the_flags_a_row_is_filtered_on():
    sys.path.insert(0, str(ROOT / "fleetsearch"))
    import load  # noqa: E402
    ev = [{"d": "2026-09-12", "w": [5]}, {"d": "2026-09-01"}, {"d": "2026-10-02", "t": "x"},
          {"d": "2026-01-03", "w": [0], "u": "2026-02-01"}]
    keep, nxt, last = load.upcoming(ev, "2026-09-23")
    assert nxt == "2026-09-26" and last == load.FOREVER
    assert [e["d"] for e in keep] == ["2026-09-12", "2026-10-02"]
    scheds = {}
    r = {"kind": "place", "img": "file:/x.jpg", "lat": 18.8000906, "lon": 99.0183907,
         "crumbs": [["เชียงใหม่", "u", "Chiang Mai"], ["ร้าน", "v", ""]],
         "rich": {"ways": ["phone"], "toilet": ["h", "ปกติมีห้องน้ำ", "usually a toilet"], "ev": ev,
                  "sched": [[0, 60]], "credit": "c"}}
    d = load.derive(r, {"file:/x.jpg": "abc"}, {"50793_29281"}, scheds, "2026-09-23")
    H = load.HAS
    assert d["has"] == H["photo"] | H["map"] | H["contact"] | H["toilet"] | H["events"] | H["hours"]
    assert d["thumb"] == "p/abc" and d["sk"] == 0 and d["sec"] == "เชียงใหม่ › ร้าน"
    assert d["evn"] == "2026-09-26" and "sched" not in d["rich"] and d["rich"]["credit"] == "c"
    d2 = load.derive({**r, "img": ""}, {}, {"50793_29281"}, scheds, "2026-09-23")
    assert d2["thumb"] == "g/50793_29281" and "credit" not in d2["rich"]        # no picture, the map
    assert load.derive({**r, "rich": {"sched": [[0, 60]]}}, {}, set(), scheds, "2026-09-23")["sk"] == 0
    near = load.derive({**r, "rich": {"toilet": ["n", "วัด", 120]}}, {}, set(), scheds, "2026-09-23")
    assert not near["has"] & H["toilet"]                                          # one nearby is not its own


def test_every_roster_site_has_a_build():
    missing = [s for s, rel, _ in crawl.SITES if not (crawl.PROJECTS / rel).is_dir()]
    assert not missing, missing


def test_the_site_list_comes_from_the_roster():
    nobuild = []
    got = {s: (root, base) for s, root, base in crawl.sites(nobuild)}
    roster = {s["id"] for s in crawl.roster()}
    assert set(got) | {s for s, _ in nobuild} >= roster
    for sid in ("lersi", "birds-chiang-mai", "golden-gate", "tham-luang", "warp-and-weft"):
        assert sid in got, sid
        assert got[sid][1] == f"https://nanobotco.github.io/{sid}/"
    # a site served inside another site's build is read from that folder
    assert got["muay-thai"][0] == (crawl.PROJECTS / "mot-dang" / "docs" / "muay-thai").resolve()
    # and the parent's walk leaves it out, so no page is read twice
    root = got["motdang"][0]
    inner = [r for r, _ in got.values() if r != root and root in r.parents]
    assert got["muay-thai"][0] in inner


def test_walk_leaves_out_a_folder_another_site_owns(tmp_path):
    root = site(tmp_path)
    assert any("cm" in p.parts for p in crawl.walk(root))
    assert not any("cm" in p.parts for p in crawl.walk(root, [root / "cm"]))


CHROME = """<html><head><title>Wat Ket — วัด เชียงใหม่ · มดแดง Mot Dang</title></head><body><main>
<h1>Wat Ket</h1><p>Riverside temple.</p>
<a class="grabride" href="x"><span class="bi">Ride here · Grab</span></a>
<div class="adbox"><span class="adlabel">sponsor</span><div><div>Garden Restaurant</div></div>
<a class="adsell" href="a">advertise here</a></div>
<section class="cpics"><h2>Around here</h2><div class="row"><a class="shot">Khua Lek</a></div></section>
<p class="anthill"><a href="h">What the bots say — รังมด</a></p>
<div class="share">Share LINE</div><p>Open daily.</p>
<dd><a href="../../map.html#16/18/99/pin=x">มดแดง · Mot Dang</a> · <a href="https://osm.org">OpenStreetMap</a></dd>
<p class="anthill">never closed <b>kept words</b>
</main><footer class="bare"><div class="footsos"><a class="sos" href="tel:1669">1669</a></div></footer></body></html>"""


def test_chrome_leaves_the_index():
    text = crawl.page_text(CHROME)
    for gone in ("Ride here", "Grab", "Garden Restaurant", "advertise", "Around here", "Khua Lek",
                 "รังมด", "Share", "1669", "Mot Dang"):
        assert gone not in text, gone
    for kept in ("Wat Ket", "Riverside temple.", "Open daily.", "OpenStreetMap", "kept words"):
        assert kept in text, kept


def test_the_site_name_leaves_the_matched_title(tmp_path):
    b = ["Mot Dang", "มดแดง"]
    assert crawl.brand_suffix("Wawee — กาแฟ เชียงใหม่ · มดแดง Mot Dang", b) == ("Wawee — กาแฟ เชียงใหม่", "มดแดง Mot Dang")
    assert crawl.brand_suffix("Gardeners — มดแดง", b) == ("Gardeners", "มดแดง")
    assert crawl.brand_suffix("มดแดง Mot Dang", b) == ("มดแดง Mot Dang", "")
    assert crawl.brand_suffix("Red Ant Café · Mot Dang Road", b)[0] == "Red Ant Café · Mot Dang Road"
    root = tmp_path / "docs"
    (root / "cm" / "p").mkdir(parents=True)
    (root / "cm" / "p" / "w.html").write_text(CHROME, encoding="utf-8")
    row = crawl.extract(root / "cm" / "p" / "w.html", "motdang", "https://motdang.net/", root, {})
    assert row["title"] == "Wat Ket — วัด เชียงใหม่ · มดแดง Mot Dang"       # shown whole
    assert "Mot Dang" not in row["title_s"] and "แดง" not in row["title_s"]   # matched without it


def test_stubs_rolls_and_untitled(tmp_path):
    root = tmp_path / "docs"
    (root / "cm" / "p").mkdir(parents=True)
    (root / "moved.html").write_text('<!doctype html><title>Moved to wichaa.net</title>'
                                     '<meta http-equiv="refresh" content="0; url=https://wichaa.net/x/">', encoding="utf-8")
    (root / "m.html").write_text("<!doctype html><meta charset=utf-8><title>Untitled (Atanatiya sut)</title>"
                                 "<meta http-equiv=refresh content=\"0; url=/m/a/\"><meta name=robots content=\"noindex,follow\">"
                                 "<p>Moved to x</p>", encoding="utf-8")
    roll = PAGE.format(canon="https://motdang.net/all.html").replace(
        "<title>", '<meta name="robots" content="index,follow"><meta name="robots" content="noindex,follow"><title>')
    (root / "all.html").write_text(roll, encoding="utf-8")
    (root / "cm" / "p" / "thin.html").write_text(roll.replace("all.html", "cm/p/thin.html"), encoding="utf-8")
    (root / "ms.html").write_text("<!doctype html><html><head><title>Untitled (Khun cao kao yang) — wichaa</title></head>"
                                  "<body><h1>Untitled (Khun cao kao yang)</h1><p class=th>ไม่ปรากฎ (คุณเจ้าเก้าอย่าง)</p>"
                                  "<p>A folio.</p></body></html>", encoding="utf-8")
    (root / "bare.html").write_text("<!doctype html><html><head><title>Untitled — wichaa</title></head>"
                                    "<body><h1>Untitled</h1></body></html>", encoding="utf-8")
    ex = lambda n: crawl.extract(root / n, "motdang", "https://motdang.net/", root, {})  # noqa: E731
    assert ex("moved.html") is None and ex("m.html") is None
    assert ex("all.html") is None                           # a complete roll repeats its shelf
    assert ex("cm/p/thin.html") is not None                 # a place's one page stays
    assert ex("ms.html")["title"] == "Khun cao kao yang · คุณเจ้าเก้าอย่าง — wichaa"
    assert ex("bare.html") is None


def test_one_row_per_address(tmp_path):
    rows = [
        {"url": "https://motdang.net/ghost/stops/", "title": "Every stop — Ghost", "kb": 30},
        {"url": "https://motdang.net/ghost/stops/", "_own": "https://motdang.net/ghost/stops/doi-kham.html",
         "title": "Doi Kham — Ghost", "kb": 25},
        {"url": "https://motdang.net/", "title": "มดแดง Mot Dang — เชียงใหม่ · เชียงราย ตอนนี้", "kb": 200},
        {"url": "https://motdang.net/", "_own": "https://motdang.net/home-classic.html",
         "title": "มดแดง Mot Dang — เชียงใหม่ · เชียงราย", "kb": 260},
        {"url": "https://motdang.net/home-help/", "title": "Home help (extra)", "kb": 12},
    ]
    rows.insert(0, {"url": "https://motdang.net/home-help/", "title": "Home help", "kb": 20})
    src, dst = tmp_path / "raw.jsonl", tmp_path / "out.jsonl"
    src.write_text("".join(json.dumps({**r, "url_s": ""}, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    crawl.dedupe(src, dst)
    out = [json.loads(x) for x in dst.read_text(encoding="utf-8").splitlines()]
    urls = [r["url"] for r in out]
    assert len(urls) == len(set(urls)), urls
    assert "https://motdang.net/ghost/stops/doi-kham.html" in urls      # a stop of its own lands on the stop
    assert "https://motdang.net/home-classic.html" not in urls          # a copy of the front page is dropped
    assert [r["title"] for r in out if r["url"].endswith("home-help/")] == ["Home help"]
    assert not any("_own" in r for r in out)


def test_worker_owns_find_and_the_header_box():
    src = (ROOT / "publish" / "worker.js").read_text(encoding="utf-8")
    assert 'import { fleetSearch } from "./fleetsearch.js"' in src
    assert "if (fleetOwns(url))" in src
    m = re.search(r'FLEET_PARAMS = new Set\(\[(.*?)\]\)', src, re.S)
    params = set(re.findall(r'"(\w+)"', m.group(1)))
    assert params == {"q", "adv", "lucky", "p", "n", "site", "from", "to", "fmt",
                      "sort", "in", "since", "near", "kind", "sec", "has"}
    # every parameter the page renders into a link must be one the Worker owns,
    # or that link lands on the old static page instead of the search
    js = (ROOT / "publish" / "fleetsearch.js").read_text(encoding="utf-8")
    emitted = set(re.findall(r'searchParams\.(?:set|delete)\("(\w+)"', js))
    emitted |= set(re.findall(r'<(?:input|select|textarea)[^>]*?\bname="(\w+)"', js))
    keep = js.split("function keep(st)")[1].split("\n}")[0]               # the hidden fields
    emitted |= set(re.findall(r'(\w+):', keep))
    emitted |= set(re.findall(r'sel\("(\w+)"', js))                        # the boolean form's dropdowns
    assert emitted <= params, emitted - params
    # the header box on every page posts to search.html?q=, so that address must be owned
    assert 'p !== "/search.html"' in src


def test_the_loader_writes_the_narrow_twin():
    src = (ROOT / "fleetsearch" / "load.py").read_text(encoding="utf-8")
    assert "CREATE TABLE keys{sfx}(id INTEGER PRIMARY KEY" in src
    assert "INSERT OR REPLACE INTO keys{sfx}(id,site,host,lastmod,title,lat,lon,kind,sec,has,sk,evn,evu,score,evc)" in src
    # the bits the loader writes are the bits the page reads
    js_has = re.search(r"const HAS = \{([^}]*)\}", (ROOT / "publish" / "fleetsearch.js").read_text(encoding="utf-8")).group(1)
    sys.path.insert(0, str(ROOT / "fleetsearch"))
    import load  # noqa: E402
    assert {k: int(v) for k, v in re.findall(r"(\w+): (\d+)", js_has)} == load.HAS
    # a chunk retried after a partial import must land where the first attempt did
    for t in ("pages", "keys", "fts", "meta"):
        assert f"INSERT OR REPLACE INTO {t}{{sfx}}" in src, t
    # a swap that renamed only some of them would leave the index half old
    js = (ROOT / "publish" / "fleetsearch.js").read_text(encoding="utf-8")
    for t in ("pages", "keys", "fts", "meta"):
        assert f'"{t}"' in src.split("def swap_sql")[1].split("def wrangler")[0], t
    assert "JOIN keys" in js and "JOIN pages q" not in js


def test_wrangler_binds_the_index():
    toml = (ROOT / "publish" / "wrangler.toml").read_text(encoding="utf-8")
    assert 'binding = "SEARCH"' in toml and 'database_name = "motdang-search"' in toml
    js = (ROOT / "publish" / "fleetsearch.js").read_text(encoding="utf-8")
    assert "env.SEARCH" in js


def test_every_planned_match_runs_in_sqlite():
    if not TWIN.exists():
        return "no local twin; python3 fleetsearch/load.py --sql --local"
    out = subprocess.run(["node", str(ROOT / "tests" / "test_fleetsearch.js"), "--dump"],
                         capture_output=True, text=True, cwd=ROOT)
    # The verdict is the output, not the exit code: node 24 sometimes takes a
    # SIGSEGV tearing down this process AFTER printing everything, and an exit
    # code that is occasionally -11 after a clean run would make this suite
    # lie in both directions.
    assert "all passed" in out.stdout, (out.returncode, out.stdout[-600:], out.stderr[-300:])
    assert "DUMP " in out.stdout, (out.returncode, out.stdout[-600:])
    dump = json.loads(out.stdout.split("DUMP ", 1)[1].splitlines()[0])
    con = sqlite3.connect(f"file:{TWIN}?mode=ro", uri=True)
    broken = []
    for q, matches in dump.items():
        for m in matches:
            try:
                con.execute("SELECT count(*) FROM fts WHERE fts MATCH ?", (m,)).fetchone()
            except sqlite3.OperationalError as e:
                broken.append(f"{q!r} → {m!r}: {e}")
    assert not broken, "\n".join(broken)


def test_twin_holds_the_roster_and_the_rank_weights():
    if not TWIN.exists():
        return "no local twin"
    con = sqlite3.connect(f"file:{TWIN}?mode=ro", uri=True)
    sites = {r[0] for r in con.execute("SELECT DISTINCT site FROM pages")}
    # every roster site with a build, less one whose pages are all stubs
    # (hand-poke: each page now says "Moved to wichaa.net")
    tally = json.loads((ROOT / "cache" / "fleetsearch" / "crawl.json").read_text(encoding="utf-8"))["sites"]
    want = {s for s, _, _ in crawl.sites() if tally.get(s, {}).get("pages")}
    assert sites == want, sites ^ want
    rank = con.execute("SELECT v FROM fts_config WHERE k='rank'").fetchone()[0]
    assert rank == "bm25(8.0, 1.0, 2.0, 0.0)"
    # the narrow twin the sorts and facets read, one row per page
    a, = con.execute("SELECT count(*) FROM keys").fetchone()
    b, = con.execute("SELECT count(*) FROM pages").fetchone()
    assert a == b, (a, b)
    orphan, = con.execute("SELECT count(*) FROM pages p LEFT JOIN keys k ON k.id=p.id"
                          " WHERE k.id IS NULL").fetchone()
    assert orphan == 0, orphan
    drift, = con.execute("SELECT count(*) FROM pages p JOIN keys k ON k.id=p.id"
                         " WHERE k.title <> p.title").fetchone()
    assert drift == 0, drift
    ddl = con.execute("SELECT sql FROM sqlite_master WHERE name='fts'").fetchone()[0]
    assert "categories 'L* N* Co Mn Mc'" in ddl, "Thai marks would be split off their letters"
    whole, = con.execute("SELECT count(*) FROM fts WHERE fts MATCH '\"ก๋วยเตี๋ยว\"'").fetchone()
    shred, = con.execute("SELECT count(*) FROM fts WHERE fts MATCH '\"ก วยเต ยว\"'").fetchone()
    assert whole > 0 and shred == 0, (whole, shred)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            with tempfile.TemporaryDirectory() as d:
                skip = fn(Path(d)) if inspect.signature(fn).parameters else fn()
            print(f"  {'skip' if skip else 'ok  '} {name}" + (f" — {skip}" if skip else ""))
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}\n       {e!r}")
    print("all passed" if not failures else f"{failures} FAILED")
    sys.exit(1 if failures else 0)
