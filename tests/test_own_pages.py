"""People's own pages (sites.motdang.net) folded into the places they describe.

    python3 tests/test_own_pages.py

Four things, each invisible in the output if it broke:

  * IDENTITY IS NAME AND PROXIMITY. A page is a record only inside MATCH_M of
    its pin and under a name that agrees; a record 200 m off, or a different
    name next door, is not it.
  * NOTHING IS OVERWRITTEN. The page's phone waits in the file when the record
    has one. What is written carries a receipt (provenance.py) and the page.
  * A DEAD FEED CHANGES NOTHING. A failed fetch reads the last good copy; with
    none, the importer leaves the file as it was.
  * A FREE PAGE IS A PROPOSAL. A page with a pin and no record is listed in
    data/curated/own_pages.json and joins the catalogue only where its entry
    says admit.

The feed is tests/fixtures/own_pages_feed.json (invented pages, named
example-...). Nothing here reaches the network.
"""
from __future__ import annotations

import copy
import inspect
import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))
sys.path.insert(0, str(ROOT / "fleetsearch"))

import own_pages as O          # noqa: E402
import ownpage_layer as L      # noqa: E402
import provenance as P         # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "own_pages_feed.json"
FEED = json.loads(FIXTURE.read_text(encoding="utf-8"))
PAGES = {p["name"]: p for p in FEED["pages"]}
LUNG = PAGES["example-baan-lung-mee"]          # pin 18.7885, 98.9870, gold, food
WEAVE = PAGES["example-tha-sai-shop"]          # pin in Chiang Rai city, no record
SEEN = "2026-10-13"


def rec(id="cm-osm-node-1", name="บ้านลุงหมี", name_en="Uncle Bear's Home", lat=18.78835, lng=98.98685, **kw):
    r = {"id": id, "province": "cm", "cat": ["food"], "sub": ["cafe"], "name": name, "nameTh": name,
         "nameEn": name_en, "lat": lat, "lng": lng, "geoPrecision": "exact", "address": None,
         "phone": None, "website": None, "hours": "", "attrs": {}, "sources": [], "confidence": "crawled"}
    r.update(kw)
    return r


def doc_for(records, pages=None, previous=None):
    return O.build(pages or O._pages_of(FEED), records, SEEN, previous)


# ------------------------------------------------------------------ the feed

class _Resp:
    def __init__(self, body, status=200):
        self._b, self.status = body, status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n=-1):
        return self._b


def _with_urlopen(fn, thing):
    real = urllib.request.urlopen
    urllib.request.urlopen = thing
    try:
        return fn()
    finally:
        urllib.request.urlopen = real


def test_a_good_fetch_is_kept_as_the_last_good_copy(tmp):
    cache = tmp / "feed.json"
    body = json.dumps(FEED).encode()
    doc, via = _with_urlopen(lambda: O.fetch_feed(cache, url="https://x/feed.json"), lambda req, timeout=0: _Resp(body))
    assert via == "live" and len(doc["pages"]) == 6, via
    assert json.loads(cache.read_text())["generated"] == FEED["generated"]


def test_a_dead_feed_reads_the_cached_copy_and_none_means_none(tmp):
    cache = tmp / "feed.json"

    def boom(req, timeout=0):
        raise OSError("down")
    doc, via = _with_urlopen(lambda: O.fetch_feed(cache), boom)
    assert doc is None and via == "none", via
    cache.write_text(json.dumps(FEED))
    doc, via = _with_urlopen(lambda: O.fetch_feed(cache), boom)
    assert via == "cache" and len(doc["pages"]) == 6
    doc, via = _with_urlopen(lambda: O.fetch_feed(cache), lambda req, timeout=0: _Resp(b"{not json"))
    assert via == "cache", "a body that is not the feed is a failure, not an answer"
    doc, via = _with_urlopen(lambda: O.fetch_feed(cache), lambda req, timeout=0: _Resp(b"{}", 503))
    assert via == "cache"


def test_the_importer_leaves_the_file_alone_with_no_feed(tmp):
    out = tmp / "own_pages.json"
    out.write_text('{"keep": true}')
    real = urllib.request.urlopen
    urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(OSError("down"))
    try:
        rc = O.main(["--write", "--out", str(out), "--cache", str(tmp / "none.json")])
    finally:
        urllib.request.urlopen = real
    assert rc == 0 and json.loads(out.read_text()) == {"keep": True}


def test_pages_off_the_pages_host_are_dropped():
    bad = {"pages": [dict(LUNG, url="https://evil.example/x"), dict(LUNG, url="http://sites.motdang.net/x"),
                     dict(LUNG, title=""), "x", dict(LUNG)]}
    assert [p["name"] for p in O._pages_of(bad)] == ["example-baan-lung-mee"]


# ---------------------------------------------------------------- the hours

def test_a_week_becomes_an_osm_string_and_minutes():
    assert O.hours_string(LUNG["hours"]) == "Mo-Fr 08:00-17:00; Sa 09:00-14:00,16:00-19:00"
    assert O.hours_string({"on": True, "always": True}) == "Mo-Su 00:00-24:00"
    assert O.hours_string({"on": False, "week": [[["09:00", "17:00"]]] * 7}) == ""
    assert O.hours_string({"on": True, "tz": "Europe/Lisbon", "week": [[["09:00", "17:00"]]] * 7}) == ""
    assert O.hours_string({"on": True, "tz": "Asia/Bangkok", "week": [[["18:00", "00:00"]]] + [None] * 6}) == "Mo 18:00-24:00"
    assert O.sched_of(LUNG["hours"])[0] == [480, 1020]
    assert O.sched_of({"on": True, "week": [[["22:00", "02:00"]]]}) == [[1320, 1560]]
    # the string is what build_open_lamps.py reads: it must parse to the same minutes
    import build_open_lamps as B
    for h in (LUNG["hours"], WEAVE["hours"], {"on": True, "always": True}):
        assert B.parse_hours(O.hours_string(h)) == O.sched_of(h), h


# ------------------------------------------------------------------ matching

def test_a_page_is_the_record_inside_the_radius_under_a_name_that_agrees():
    d = doc_for([rec()])
    m = d["matched"]
    assert [x["page"] for x in m] == ["example-baan-lung-mee"], m
    assert m[0]["place"] == "cm-osm-node-1" and m[0]["tier"] == "gold" and m[0]["metres"] <= O.MATCH_M


def test_other_names_and_other_places_do_not_match():
    far = rec(lat=18.7885 + 0.0020)                       # about 220 m north
    assert doc_for([far])["matched"] == []
    other = rec(name="ร้านข้าวมันไก่", name_en=None)
    assert doc_for([other])["matched"] == []
    only_generic = rec(name="ร้านกาแฟ", name_en=None)
    assert doc_for([only_generic])["matched"] == [], "a kind of place is not a name"
    pinless = rec(lat=None, lng=None)
    assert doc_for([pinless])["matched"] == []


def test_the_latin_name_matches_a_thai_title_by_its_reading():
    r = rec(name="Baan Lung Mee", name_en="Baan Lung Mee")
    r["nameTh"] = None
    p = dict(LUNG, title="บ้านลุงหมี")                      # the page says it in Thai only
    assert doc_for([r], [p])["matched"], "Thai page, Latin record"
    r2 = rec(name="บ้านลุงหมี", name_en=None)
    p2 = dict(LUNG, title="Baan Lung Mee")
    assert doc_for([r2], [p2])["matched"], "Latin page, Thai record"


def test_the_nearest_of_two_matching_records_wins():
    near, far = rec(id="a", lat=18.78852), rec(id="b", lat=18.78880)
    assert doc_for([far, near])["matched"][0]["place"] == "a"


def test_lacks_names_only_what_the_record_does_not_hold():
    r = rec(phone="+66882531675", attrs={"facebook": "https://www.facebook.com/x"})
    m = doc_for([r])["matched"][0]
    assert "phone" not in m["lacks"] and "facebook" not in m["lacks"], m["lacks"]
    assert {"hours", "line", "web", "instagram", "items", "photos"} <= set(m["lacks"]), m["lacks"]
    assert m["facts"]["phone"] == "081-000-0001", "the page's own phone waits in the file"


def test_the_real_record_beside_the_fixture_page_is_found():
    f = ROOT / "data" / "canonical" / "cm.json"
    if not f.exists():
        return "no data/canonical/cm.json"
    recs = [r for r in json.loads(f.read_text()) if r.get("lat") and abs(r["lat"] - 18.7885) < 0.01 and abs(r["lng"] - 98.987) < 0.01]
    m = doc_for(recs)["matched"]
    assert m and m[0]["place"] == "cm-osm-node-2039957239", m


# -------------------------------------------------------------- the proposals

def test_a_page_with_a_pin_and_no_record_is_proposed_in_its_province():
    d = doc_for([])
    names = {e["page"]: e for e in d["proposed"]}
    assert "example-tha-sai-shop" in names, names
    e = names["example-tha-sai-shop"]
    assert e["province"] == "cr" and e["admit"] is False
    r = e["record"]
    assert r["id"].startswith("cr-own-") and r["cat"] == ["shopping"] and r["geoPrecision"] == "exact"
    s = r["sources"][0]
    assert s["type"] == "own-site" and s["label"] == "own page" and s["ref"] == WEAVE["url"] and s["fetched"] == SEEN
    assert r["attrs"]["ownPage"]["url"] == WEAVE["url"]
    assert r["hours"] == "Mo-Fr 09:00-18:00; Sa 09:00-12:00" and r["phone"] == "081-000-0002"


def test_what_is_not_proposed_and_why():
    d = doc_for([])
    assert "example-bangkok-shop" in d["not_proposed"], "a pin outside the provinces we cover"
    assert "example-night-market" in d["not_proposed"], "an event is not a place"
    assert set(d["unpinned"]) == {"example-plumber-no-pin", "example-overseas-me"}, d["unpinned"]


def test_an_admit_flag_survives_a_new_run():
    first = doc_for([])
    mine = [e for e in first["proposed"] if e["page"] == "example-tha-sai-shop"][0]
    mine["admit"] = True
    again = doc_for([], previous=first)
    assert {e["page"]: e["admit"] for e in again["proposed"]} == {"example-baan-lung-mee": False, "example-tha-sai-shop": True}


# --------------------------------------------------------------------- apply

def _matched_doc(r):
    return doc_for([r])


def test_apply_fills_gaps_and_never_overwrites():
    r = rec(phone="+66882531675", address="ที่อยู่เดิม")
    d = _matched_doc(r)
    filled, new = O.apply([r], "cm", d)
    assert filled == 1 and new == []
    assert r["phone"] == "+66882531675" and r["address"] == "ที่อยู่เดิม", "held values stay"
    assert r["hours"] == "Mo-Fr 08:00-17:00; Sa 09:00-14:00,16:00-19:00"
    a = r["attrs"]
    assert a["lineId"] == "@example-lungmee" and a["instagram"] == "example.lungmee"
    assert a["facebook"].startswith("https://www.facebook.com/")
    assert r["website"] == "https://example.invalid/lungmee"
    assert a["ownMenu"]["items"][0] == {"n": "กาแฟดริป", "p": "65", "note": "เมล็ดจากแม่แจ่ม"} and a["ownMenu"]["currency"] == "THB"
    assert a["ownPhotos"][1]["credit"]["license"] == "CC BY-SA 4.0"
    assert a["ownPage"]["url"] == LUNG["url"] and a["ownPage"]["tier"] == "gold"
    assert "phone" not in a["ownPage"]["filled"] and {"hours", "line", "web", "items"} <= set(a["ownPage"]["filled"])


def test_apply_leaves_receipts():
    r = rec()
    O.apply([r], "cm", _matched_doc(r))
    for field in ("phone", "hours", "address", "website"):
        e = r["provenance"][field]
        assert e == {"source": "own-site:sites.motdang.net", "how": "stated", "at": SEEN}, (field, e)
    src = [s for s in r["sources"] if s["type"] == "own-site"]
    assert len(src) == 1 and src[0]["ref"] == LUNG["url"] and src[0]["fetched"] == SEEN
    assert P.source_class(src[0]) == P.VENUE, "the place's own words, whoever hosts them"


def test_a_value_the_record_had_first_keeps_its_own_receipt():
    r = rec(phone="+66882531675")
    P.stamp(r, "phone", "osm:node", P.STATED, "2026-08-01")
    O.apply([r], "cm", _matched_doc(r))
    assert r["provenance"]["phone"]["source"] == "osm:node"


def test_apply_twice_says_the_same_thing():
    r = rec()
    d = _matched_doc(r)
    O.apply([r], "cm", d)
    snap = copy.deepcopy(r)
    filled, _ = O.apply([r], "cm", d)
    assert filled == 0 and r == snap, "a second pass writes nothing"
    again = doc_for([r])["matched"][0]
    assert "phone" in again["lacks"] and "hours" in again["lacks"], "what we wrote ourselves still counts as lacking"


def test_a_website_that_is_a_facebook_page_files_as_facebook():
    r = rec()
    p = dict(LUNG, web="https://www.facebook.com/lungmee.shop", facebook="")
    O.apply([r], "cm", doc_for([r], [p]))
    assert r["website"] is None and r["attrs"]["facebook"] == "https://www.facebook.com/lungmee.shop"


def test_only_an_admitted_proposal_joins_and_only_in_its_province():
    d = doc_for([])
    assert O.apply([], "cr", d) == (0, [])
    [e for e in d["proposed"] if e["page"] == "example-tha-sai-shop"][0]["admit"] = True
    assert O.apply([], "cm", d)[1] == [], "wrong province"
    filled, new = O.apply([], "cr", d)
    assert filled == 0 and len(new) == 1
    r = new[0]
    assert r["provenance"]["name"]["source"] == "own-site:sites.motdang.net" and r["provenance"]["lat"]["how"] == "stated"
    assert O.apply([r], "cr", d)[1] == [], "already held, not admitted twice"
    assert all("provenance" not in e["record"] for e in d["proposed"]), "the document itself is not written through"


def test_apply_with_no_file_does_nothing():
    assert O.apply([rec()], "cm", {}) == (0, [])


# ------------------------------------------------------------------ the layer

def _bi(th, en):
    return f"<bi>{th}|{en}</bi>"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _icon(name, size=16):
    return f"<svg {name}/>"


def _mark(label, th, en):
    return f"<mark>{label}|{th}|{en}</mark>"


def test_the_button_goes_to_the_page_and_only_where_there_is_one():
    r = rec()
    O.apply([r], "cm", _matched_doc(r))
    h = L.pill_html(r, _bi, _esc, _esc, _icon)
    assert 'href="https://sites.motdang.net/example-baan-lung-mee"' in h and "เว็บของร้าน" in h and "Their own page" in h
    assert "i-shop" in h and "<svg" in h
    assert L.pill_html(rec(), _bi, _esc, _esc, _icon) == ""
    bad = rec(attrs={"ownPage": {"url": "https://evil.example/x"}})
    assert L.pill_html(bad, _bi, _esc, _esc, _icon) == "", "an address off the host is not drawn"


def test_the_menu_row_lists_items_with_prices_and_its_source():
    r = rec()
    O.apply([r], "cm", _matched_doc(r))
    h = L.menu_row(r, _bi, _esc, _esc, _mark)
    assert "กาแฟดริป" in h and "฿65" in h and "เมล็ดจากแม่แจ่ม" in h
    assert "จากหน้าของร้านเอง อ่านเมื่อ 2026-10-13" in h and "from their own page, read 2026-10-13" in h
    assert L.menu_row(rec(), _bi, _esc, _esc, _mark) == ""


def test_menu_text_is_escaped_and_long_menus_link_to_the_page():
    items = [{"n": f"<b>{i}</b>", "p": "10"} for i in range(15)]
    r = rec(attrs={"ownPage": {"url": LUNG["url"], "seen": SEEN},
                   "ownMenu": {"items": items, "currency": "EUR", "seen": SEEN}})
    h = L.menu_row(r, _bi, _esc, _esc, _mark)
    assert "<b>" not in h and "&lt;b&gt;0&lt;/b&gt;" in h and "EUR 10" in h
    assert "อีก 3 รายการ" in h and LUNG["url"] in h


# ---------------------------------------------------------- the search index

def test_the_crawl_makes_a_row_for_each_page_with_its_words_pin_and_picture():
    import crawl
    rows = crawl.own_rows(fetch=False, fixture=str(FIXTURE))
    by = {r["url"].rsplit("/", 1)[1]: r for r in rows}
    assert len(rows) == 6 and {r["site"] for r in rows} == {"sites"} and {r["host"] for r in rows} == {"sites.motdang.net"}
    r = by["example-baan-lung-mee"]
    assert r["lat"] == 18.7885 and r["lon"] == 98.987 and r["kind"] == "place"
    assert r["img"] == LUNG["cover"] and r["abstract"] == LUNG["tagline"]
    assert "ขนมปัง" in r["body_s"] and "65" in r["body_s"] and "ซอยข้าง" in r["body_s"], "items and address are searchable"
    assert "ร้านอาหาร" in r["body_s"] and "restaurant" in r["body_s"], "the kind in both languages"
    assert r["rich"]["ways"] == ["phone", "line", "facebook", "instagram", "web"] and r["rich"]["sched"][0] == [480, 1020]
    assert r["crumbs"] == [["ร้านอาหาร", None, "Food"]]
    assert by["example-plumber-no-pin"]["lat"] is None and by["example-overseas-me"]["lat"] is None
    ev = by["example-night-market"]
    assert ev["kind"] == "page" and ev["rich"]["ev"][0]["d"] == "2026-10-20"
    assert "sched" not in by["example-overseas-me"]["rich"]


def test_the_row_loads_the_way_every_other_row_does():
    import crawl
    import load
    row = [r for r in crawl.own_rows(fetch=False, fixture=str(FIXTURE)) if r["url"].endswith("lung-mee")][0]
    d = load.derive(row, {}, set(), {}, "2026-10-13")
    assert d["has"] & load.HAS["contact"] and d["has"] & load.HAS["hours"] and d["sk"] is not None
    ev = [r for r in crawl.own_rows(fetch=False, fixture=str(FIXTURE)) if r["url"].endswith("night-market")][0]
    assert load.derive(ev, {}, set(), {}, "2026-10-13")["evn"] == "2026-10-20"


def test_a_dead_feed_falls_back_to_the_cached_copy_in_cache_fleetsearch(tmp):
    import crawl
    old = crawl.OWN_FEED_CACHE
    crawl.OWN_FEED_CACHE = tmp / "own_pages_feed.json"
    try:
        assert crawl.own_rows(fetch=False) == [], "no feed, no cache, no rows"
        crawl.OWN_FEED_CACHE.write_text(FIXTURE.read_text())
        rows = _with_urlopen(lambda: crawl.own_rows(fetch=True), lambda req, timeout=0: (_ for _ in ()).throw(OSError("down")))
        assert len(rows) == 6
        assert len(crawl.own_rows(fetch=False)) == 6
    finally:
        crawl.OWN_FEED_CACHE = old


def test_the_page_makers_pictures_are_fetched_as_they_are():
    import thumbs
    u = "https://sites.motdang.net/img/abc.webp"
    assert thumbs.remote_small(u) == u
    assert thumbs.remote_small("https://example.com/a.jpg") == ""


# -------------------------------------------------------------------- wiring

def _text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_everything_is_wired_where_the_neighbours_are():
    b = _text("build.py")
    assert "import ownpage_layer" in b and "ownpage_layer.pill_html(r, bi, att, esc, svg_icon)" in b
    assert "ownpage_layer.menu_row(r, bi, esc, att, mark)" in b and '"ownpage_layer.py"' in b
    ia = _text("importers/import_all.py")
    assert ia.index("own_pages.apply(final, prov)") < ia.index("import_overture.apply(final, prov)"), "its own words first"
    assert "importers/own_pages.py --write" in _text("importers/standing_walk.sh")
    fj = _text("publish/fleetsearch.js")
    assert 'from "./ownfind.js"' in fj and "ownPagesSoon(env, qm, st.pin)" in fj
    assert "own_pages.py" in _text("fleetsearch/README.md")
    cr = _text("fleetsearch/crawl.py")
    assert "own_rows(fetch=not a.no_fetch" in cr


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            with tempfile.TemporaryDirectory() as d:
                skip = fn(Path(d)) if inspect.signature(fn).parameters else fn()
            print(f"  {'skip' if skip else 'ok  '} {name}" + (f" - {skip}" if skip else ""))
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}\n       {e!r}")
    print("all passed" if not failures else f"{failures} FAILED")
    sys.exit(1 if failures else 0)
