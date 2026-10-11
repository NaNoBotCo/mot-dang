#!/usr/bin/env python3
"""Overture is a second witness, and these are the fences that keep it one.

Four properties, each of them a thing that would be invisible in the output if
it broke:

  * IDENTITY IS NAME AND PROXIMITY. Exact name equality across a province has a
    p90 of 21 km — it is routinely two different shops. A match beyond 300 m
    would put one shop's telephone on another's page and nothing on the site
    would look wrong.
  * NOTHING IS OVERWRITTEN. A survey, a register, an owner's claim and a
    curated correction all outrank this, and all of them run later. The fence
    has to be here because by then the value is gone.
  * NOTHING IS GIVEABLE. CDLA-Permissive is not ODbL and 99% of these rows are
    Meta's. provenance.py answers this, and the answer has to stay no.
  * NOTHING IS ADMITTED THAT CANNOT BE FILED. A record with no shelf, no pin or
    a confidence below 0.5 is a row we cannot answer a question with.

    python3 tests/test_overture.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import import_overture as O          # noqa: E402
import provenance as P               # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def row(id="ovt-1", name="ร้านทดสอบ", lat=18.7900, lng=98.9900, cat="massage_therapy",
        phone="+6653000000", website=None, email=None, address=None,
        socials=None, confidence=0.9, province="cm"):
    return {"id": id, "name": name, "lat": lat, "lng": lng, "cat": cat,
            "catAlt": [], "confidence": confidence, "phone": phone,
            "website": website, "email": email, "address": address,
            "socials": socials or [], "brand": None, "dataset": "meta",
            "province": province, "namesCommon": {}, "status": None,
            "locality": None, "postcode": "50200", "region": None,
            "updated": None}


def record(**kw):
    r = {"id": "cm-osm-node-1", "province": "cm", "cat": ["massage"], "sub": [],
         "name": "ร้านทดสอบ", "nameTh": "ร้านทดสอบ", "nameEn": None,
         "lat": 18.7900, "lng": 98.9900, "geoPrecision": "exact",
         "address": None, "phone": None, "website": None, "hours": None,
         "attrs": {}, "featured": False, "landmark": False, "sources": [],
         "confidence": "crawled", "updatedAt": "2026-07-27"}
    r.update(kw)
    return r


def apply(records, rows):
    """apply() against a made-up cache rather than the real one."""
    real_load, real_manifest = O.load, O.manifest
    O.load = lambda province=None: [r for r in rows if province in (None, r["province"])]
    O.manifest = lambda: {"fetched": "2026-09-07", "licence": "CDLA-Permissive-2.0",
                          "release": "test"}
    try:
        return O.apply(records, "cm")
    finally:
        O.load, O.manifest = real_load, real_manifest


print("identity is name AND proximity")
r = record()
enriched, _ = apply([r], [row()])
check("a same-name row 0 m away is the same place", enriched == 1 and r["phone"])
r = record()
# 0.02° of latitude is about 2.2 km — inside the province, far outside a shop.
enriched, _ = apply([r], [row(lat=18.8100)])
check("a same-name row 2.2 km away is NOT", enriched == 0 and not r["phone"],
      f"phone={r['phone']!r}")
r = record(name="ร้าน", nameTh="ร้าน")
enriched, _ = apply([r], [row(name="ร้านลาบลำปางสาขาสอง")])
check("a short name is not matched by containment", enriched == 0,
      "'ร้าน' is the word for shop, not an identity")

print("\nnothing is overwritten")
r = record(phone="053-111-111", website="https://held.example")
apply([r], [row(phone="+6653999999", website="https://overture.example")])
check("a phone already held survives", r["phone"] == "053-111-111", r["phone"])
check("a website already held survives", r["website"] == "https://held.example")
r = record(attrs={"facebook": "https://www.facebook.com/held"})
apply([r], [row(socials=["https://www.facebook.com/overture"])])
check("a facebook page already held survives",
      r["attrs"]["facebook"] == "https://www.facebook.com/held")

print("\na record that gains nothing is left alone")
r = record(phone="053-111-111")
apply([r], [row(phone="+6653999999", website=None, email=None, socials=[])])
check("no source is appended", r["sources"] == [], str(r["sources"]))
check("no provenance is written", not r.get("provenance"))

print("\nan address is an address, not a house number")
r = record()
apply([r], [row(address="1294")])
check("a bare number is refused", r["address"] is None, str(r["address"]))
r = record()
apply([r], [row(address="82 หมู่ 3 ต.สุเทพ อ.เมืองเชียงใหม่ 50200")])
check("a Thai address is taken", bool(r["address"]))

print("\na link to a map of the place is not its website")
r = record()
apply([r], [row(website="https://maps.app.goo.gl/abc123")])
check("a Google Maps share link is dropped", r["website"] is None, str(r["website"]))
r = record()
apply([r], [row(website="https://www.facebook.com/someshop")])
check("a Facebook address lands in attrs.facebook, not website",
      r["website"] is None and r["attrs"].get("facebook"), str(r["attrs"]))
r = record()
apply([r], [row(website="https://lin.ee/abc")])
check("a LINE address lands in attrs.lineUrl", r["attrs"].get("lineUrl"))
r = record()
apply([r], [row(website="https://ruenkaew.example.co.th")])
check("a real domain is kept", r["website"] == "https://ruenkaew.example.co.th")

print("\nnothing from Overture is giveable to OpenStreetMap")
r = record()
apply([r], [row(phone="+6653000000")])
check("the phone it just gave is not giveable", not P.giveable(r, "phone"))
check("nor is it merely waiting on a licence", not P.needs_licence_clearance(r, "phone"))
_, new = apply([], [row(id="ovt-9")])
check("nor is anything on an admitted record",
      new and P.giveable_fields(new[0]) == [], str(new and P.giveable_fields(new[0])))
check("an admitted record's provenance validates",
      new and P.validate(new[0]) == [], str(new and P.validate(new[0])))

print("\nnothing is admitted that cannot be filed")
_, new = apply([], [row(id="a", confidence=0.4)])
check("confidence below 0.5 is refused", new == [])
_, new = apply([], [row(id="b", cat="fortune_teller_that_does_not_exist")])
check("an unmapped category is refused", new == [])
_, new = apply([], [row(id="c", cat=None)])
check("no category at all is refused", new == [])
_, new = apply([], [row(id="d"), row(id="e")])
check("the same name at the same pin is admitted once", len(new) == 1, str(len(new)))
_, new = apply([], [row(id="f")])
check("an admitted record carries its licence",
      new and new[0]["sources"][0]["licence"] == "CDLA-Permissive-2.0")
check("an admitted record is third-party", new and new[0]["confidence"] == "third-party")

print("\na near-miss is handed over, not settled")
r = record(name="Ban Coffee", nameTh=None, nameEn="Ban Coffee", cat=["food"])
_, new = apply([r], [row(id="ovt-near", name="บ้านกาแฟ", cat="cafe",
                         lat=18.79003, lng=98.99003)])
check("a same-shelf row 4 m away under another name is not admitted", new == [],
      f"admitted {len(new)}")
check("it is written down for a person",
      (ROOT / "cache" / "overture_review_cm.txt").exists())
r = record(name="Ban Coffee", nameTh=None, nameEn="Ban Coffee", cat=["food"])
_, new = apply([r], [row(id="ovt-far", name="บ้านกาแฟ", cat="cafe",
                         lat=18.79100, lng=98.99100)])
check("the same row 140 m away IS admitted", len(new) == 1,
      "25 m is a building; a soi is not a duplicate")

print("\nno pin is ever moved or invented")
r = record(lat=None, lng=None, geoPrecision="needs-pin")
enriched, _ = apply([r], [row()])
check("an unpinned record stays unpinned", r["lat"] is None and enriched == 0,
      "measured: even the strictest rule left p90 at 5.5 km, above the ±3 km cap")
r = record(lat=18.7900, lng=98.9900)
apply([r], [row(lat=18.7901, lng=98.9901)])
check("a pinned record keeps its own pin", r["lat"] == 18.7900)

print("\nthe category map")
doc = json.loads((ROOT / "data" / "curated" / "overture_categories.json").read_text())
check("every rule compiles and names a shelf",
      all(r.get("match") and r.get("cat") for r in doc["rules"]))
cats = {r["cat"] for r in doc["rules"]}
canon = json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())
known = {c for r in canon for c in r["cat"]}
check("every shelf it files to already exists", cats <= known, str(sorted(cats - known)))
check("no rule matches an empty category", O.shelf_of({"cat": "", "catAlt": []}) is None)

print("\nrunning it twice says the same thing")
rows = [row(id="x"), row(id="y", name="อีกร้าน", lat=18.8000, lng=98.9800)]
r = record()
e1, n1 = apply([r], rows)
e2, n2 = apply([r], rows)
check("a second pass enriches nothing further", e2 == 0, f"{e1} then {e2}")
check("a second pass admits the same records", len(n1) == len(n2) == 1,
      f"{len(n1)} then {len(n2)}")

print()
if failures:
    print(f"{len(failures)} failure(s): " + "; ".join(failures))
    sys.exit(1)
print("overture: all fences hold")
