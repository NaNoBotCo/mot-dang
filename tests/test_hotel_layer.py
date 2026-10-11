#!/usr/bin/env python3
"""hotel_layer: the Stay block on lodging pages.

1 · an unknown amenity renders nothing, never "no"
2 · an empty booking_links.json renders no paid link; a filled one renders
    rel="sponsored nofollow noopener" under the paid-link label
3 · a website found not answering puts phone + LINE above it
4 · the old city: the moat ring from the four แจ่ง corners on record
    (build.MOAT_CORNER_IDS) holds Wat Phra Singh, not One Nimman, and Tha
    Phae Gate sits on its edge

    python3 tests/test_hotel_layer.py
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import hotel_layer as H  # noqa: E402

FAIL = []


def check(ok, what):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok:
        FAIL.append(what)


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def att(s):
    return esc(s).replace('"', "&quot;")


def bi(th, en):
    return f'<span class="th">{esc(th)}</span><span class="en"> · {esc(en)}</span>'


h = {"bi": bi, "esc": esc, "att": att, "icon": lambda n, s=18: f'<svg data-i="{n}"></svg>',
     "name_bi": lambda r: esc(r.get("name")), "href": lambda rid: "cm/p/" + rid,
     "reach": lambda r: [{"kind": "phone", "text": r.get("phone"), "href": "tel:" + r.get("phone")},
                         {"kind": "line", "text": "@stay", "href": "https://line.me/R/ti/p/~stay"}],
     "fmt_tel": lambda s: s, "tel_href": lambda s: "tel:" + s, "reading": lambda s: ""}

tmp = Path(tempfile.mkdtemp())
H.AMENITIES = tmp / "amen.json"
H.BOOKING = tmp / "booking.json"
H.SITECHECK = tmp / "batch.tsv"
H.AMENITIES.write_text(json.dumps({
    "h1": {"pool": {"value": "unknown", "source": "own-site", "url": "https://h1.example/"},
           "bar": {"value": None, "source": "osm", "url": "https://www.openstreetmap.org/node/1"},
           "food": {"value": "no", "source": "own-name", "url": None},
           "shuttle": {}},
    "h2": {"pool": {"value": "yes", "evidence": "Swimming Pool", "source": "own-site",
                    "url": "https://h2.example/facilities/", "fetched": "2026-10-04"},
           "shuttle": {"value": "yes", "cost": "free", "source": "own-site",
                       "url": "https://h2.example/", "fetched": "2026-10-04"}}}))
H.BOOKING.write_text(json.dumps({"_note": "", "search": [], "places": {}}))
H.SITECHECK.write_text("host\tids\tnames\tcat\tstatus\tfinal_host\tmoved\n"
                       "h1.example\th1\tOne\t['hotel']\t0\th1.example\t\n"
                       "h2.example\th2\tTwo\t['hotel']\t200\th2.example\t\n"
                       "h3.example\th3\tThree\t['hotel']\t403\th3.example\t\n")

recs = [{"id": i, "name": i.upper(), "cat": ["hotel"], "sub": ["hotel-full"], "province": "cm",
         "phone": "053-000-000", "website": f"https://{i}.example/", "lat": None, "lng": None,
         "geoPrecision": "needs-pin", "attrs": {}} for i in ("h1", "h2", "h3")]
g = {"norm_url": lambda u: u, "url_kind": lambda u: None}
H.prepare(g, {"cm": recs}, net=None, h=h, log=lambda *a: None)
page = {r["id"]: H.block(r, h) for r in recs}
NO = re.compile(r"ไม่มี|>\s*· no\s*<|: <b>[^<]*no", re.I)

print("1 · unknown is not no")
check(not NO.search(page["h1"]), "h1: unknown / empty / unsourced amenities print no 'no'")
check("สระว่ายน้ำ" not in page["h1"] and "Pool" not in page["h1"], "h1: unknown pool is left off")
check("Pool" in page["h2"] and "the hotel's site, 2026-10-04" in page["h2"], "h2: stated pool shows with its source")
check("ฟรี" in page["h2"] and "free" in page["h2"], "h2: free shuttle says free")
check(H.amenity({"pool": {"value": "no", "source": "own-name"}}, "pool") is None,
      "a 'no' without a page or tag behind it is dropped")

print("2 · booking links")
check("sponsored" not in "".join(page.values()), "empty booking_links.json: no paid link anywhere")
check("Paid links" not in "".join(page.values()), "empty booking_links.json: no paid-link label")
H.BOOKING.write_text(json.dumps({"search": [{"name": "Agoda", "url": "https://example.test/s?q={q}"}],
                                 "places": {"h2": [{"name": "Booking.com", "url": "https://example.test/h2"}]}}))
H.prepare(g, {"cm": recs}, net=None, h=h, log=lambda *a: None)
b2 = H.block(recs[1], h)
check(b2.count('rel="sponsored nofollow noopener"') == 2, "filled file: place link + search link, both sponsored")
check("Paid links: Mot Dang earns a fee if you book." in b2
      and "ลิงก์มีค่าตอบแทน: มดแดงได้ค่าแนะนำเมื่อคุณจองผ่านลิงก์นี้" in b2, "filled file: label in both languages")
check(b2.index("h2.example") < b2.index("sponsored"), "the hotel's own site comes before paid links")
check("q=H2%20Chiang%20Mai" in b2, "search template takes the name and city")

print("3 · a site not answering")
b1 = H.block(recs[0], h)
check("not answering on" in b1, "h1: website marked not answering, with the date")
check('href="https://h1.example/"' not in b1, "h1: the dead site is not linked")
check(b1.index("053-000-000") < b1.index("h1.example") and b1.index("@stay") < b1.index("h1.example"),
      "h1: phone and LINE stand above the website")
check("not answering" not in H.block(recs[2], h) and 'href="https://h3.example/"' in H.block(recs[2], h),
      "h3: a 403 (a robot turned away) stays linked")
check("not answering" not in b2 and "053-000-000" not in b2, "h2: a live site keeps its place, no phone added")

print("4 · old city")
cm = {r["id"]: r for r in json.loads((ROOT / "data/canonical/cm.json").read_text())}
corners = {"ne": "cm-osm-way-263459882", "se": "cm-osm-way-791602197",
           "sw": "cm-osm-way-317516851", "nw": "cm-osm-way-317516852"}   # build.MOAT_CORNER_IDS
ring = [[cm[corners[k]]["lat"], cm[corners[k]]["lng"]] for k in ("nw", "ne", "se", "sw")]
singh = cm["cm-osm-way-93414647"]
nimman = cm["cm-osm-way-627946317"]
gate = cm["cm-osm-node-1017379824"]
check(H.point_in_poly(singh["lat"], singh["lng"], ring), "Wat Phra Singh is inside")
check(not H.point_in_poly(nimman["lat"], nimman["lng"], ring), "One Nimman is outside")


def seg_m(lat, lng, a, b):
    kx = 111320 * 0.946                       # cos(18.8°)
    px, py = (lng - a[1]) * kx, (lat - a[0]) * 110574
    bx, by = (b[1] - a[1]) * kx, (b[0] - a[0]) * 110574
    t = max(0.0, min(1.0, (px * bx + py * by) / ((bx * bx + by * by) or 1)))
    return ((px - t * bx) ** 2 + (py - t * by) ** 2) ** 0.5


edge = min(seg_m(gate["lat"], gate["lng"], a, b) for a, b in zip(ring, ring[1:] + ring[:1]))
check(edge < 120, f"Tha Phae Gate stands on the moat's edge ({edge:.0f} m from the ring)")
check(H.point_in_poly(gate["lat"], gate["lng"] - 0.0015, ring), "150 m west of Tha Phae Gate is inside")
check(not H.point_in_poly(gate["lat"], gate["lng"] + 0.0015, ring), "150 m east of Tha Phae Gate is outside")

if FAIL:
    print(f"FAIL test_hotel_layer: {len(FAIL)}")
    sys.exit(1)
print("ok test_hotel_layer")
