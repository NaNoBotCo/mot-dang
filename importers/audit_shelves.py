#!/usr/bin/env python3
"""Audit canonical records for shelf drift and near-duplicates. Zero network.

Two reports, both read-only — this script never edits data. Fixes flow through
the curated files (data/curated/shelves.json, data/curated/merges.json) after
a human look at the report.

1. DRIFT: a place whose NAME claims an identity its shelves do not carry.
   The coworking sweep of 2026-08-07 found Hub 53 (hotel/guesthouse only),
   Heartwork, The Story 106, Peaberry and Brain awake (food/cafe only) all
   carrying "coworking" in their own names while absent from the coworking
   shelf — OSM allows one primary tag, so the crawl files each place once.
   Matching is word-boundary aware: "Code Space" must not read as a spa,
   and a pet clinic on the vet shelf is already where it belongs (the vet
   shelf outranks the medical clinic claim for animal names).

2. DUPES: two records, same normalized name, within DUPE_M metres, different
   ids — usually the same venue crawled as both a node and a way, or by two
   groups. The Social Club carries one record filed hotel and another filed
   coworking. Merge candidates only; merging is a curated decision.

Usage:
  python3 importers/audit_shelves.py            # both reports
  python3 importers/audit_shelves.py --emit     # drift as shelves.json-ready JSON
"""
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUPE_M = 80

# name-pattern -> claim. A claim names the shelf key, the cat it lives under,
# and HOW the shelf matches (data/categories.json is the authority): most match
# {sub}, but medical/dentist and essentials/pharmacy match attrs.facilityType.
# Patterns use (?<![a-z]) / (?![a-z]) as latin word fences; Thai needs none
# (tokens below do not appear inside longer common Thai words in this data).
CLAIMS = [
    (r"(?<![a-z])co-?working(?![a-z])|โคเวิร์[คก]",
     {"key": "coworking", "add_cat": ["business"], "add_sub": ["coworking"]}),
    (r"(?<![a-z])hostel(?![a-z])|โฮสเทล",
     {"key": "hostel", "add_cat": ["hotel"], "add_sub": ["hostel"]}),
    (r"(?<![a-z])(gym|fitness)(?![a-z])|ฟิตเนส",
     {"key": "gym", "add_cat": ["learn"], "add_sub": ["gym"]}),
    (r"(?<![a-z])spa(?![a-z])|(?<!โฮม)สปา",
     {"key": "beauty-spa", "add_cat": ["beauty"], "add_sub": ["beauty-spa"]}),
    (r"(?<![a-z])massage(?![a-z])|ร้านนวด|นวดแผน",
     {"key": "massage", "add_cat": ["massage"], "add_sub": []}),
    (r"(?<![a-z])pharmacy(?![a-z])|ร้าน(ขาย)?ยา(?![ยา-ๆ])|เภสัช|ฟาร์มาซ",  # (?!ย) keeps ร้านยายคำ = grandma's shop
     {"key": "pharmacy", "add_cat": ["essentials"], "add_sub": [],
      "set_attrs": {"facilityType": "pharmacy"}}),
    (r"(?<![a-z])dental|dentist(?![a-z])|ทันตกรรม|ทำฟัน|คลินิกฟัน",
     {"key": "dentist", "add_cat": ["medical"], "add_sub": [],
      "set_attrs": {"facilityType": "dentist"}}),
    (r"(?<![a-z])tailor(?![a-z])|ตัดเย็บ|ร้านตัดผ้า",
     {"key": "tailor", "add_cat": ["shopping"], "add_sub": ["tailor"]}),
    (r"(?<![a-z])laundry(?![a-z])|ซัก(รีด|อบ)",
     {"key": "laundry", "add_cat": ["essentials"], "add_sub": ["laundry"]}),
    (r"(?<![a-z])hotel(?![a-z])|โรงแรม",
     {"key": "hotel-full", "add_cat": ["hotel"], "add_sub": ["hotel-full"]}),
]
# a claim is silenced when the record already sits on any of these shelves —
# the claimed identity is either present or outranked by a truer one.
# A resort named "& Spa" stays a hotel: the spa is a guest amenity, and
# putting resorts on the beauty shelf breaks that shelf's promise.
# A condo tower named "Hotel Style" stays realestate for the same reason.
SILENCERS = {
    "coworking": {"coworking"},
    "hostel": {"hostel"},
    "gym": {"gym", "parks", "playground"},          # public exercise ground is not a gym business
    "beauty-spa": {"beauty-spa", "beauty", "massage", "thai-medicine", "grooming",
                   "hotel", "hotel-full", "guesthouse"},
    "massage": {"massage", "thai-medicine", "beauty-spa", "beauty"},
    "pharmacy": {"pharmacy"},
    "dentist": {"dentist"},
    "tailor": {"tailor"},
    "laundry": {"laundry"},
    "hotel-full": {"hotel-full", "guesthouse", "hostel", "pets", "grooming",
                   "condo", "realestate"},
}
ANIMAL = re.compile(r"pet|vet|animal|cat|dog|สัตว์|แมว|หมา|สุนัข", re.I)


def norm(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


def load():
    out = []
    for prov in ("cm", "cr"):
        out += json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text())
    return out


def fullname(p):
    return " ".join(str(p.get(k) or "") for k in ("name", "nameTh", "nameEn"))


def drift(places):
    rows = []
    for p in places:
        nm = fullname(p)
        low = nm.lower()
        ftype = (p.get("attrs") or {}).get("facilityType")
        shelves = set(norm(p.get("cat")) + norm(p.get("sub")) + ([ftype] if ftype else []))
        for pat, claim in CLAIMS:
            if not re.search(pat, low):
                continue
            if shelves & SILENCERS[claim["key"]]:
                continue
            if claim["key"] in ("dentist", "massage", "beauty-spa", "hotel-full") and ANIMAL.search(low):
                continue  # pet grooming/vet dentistry/pet hotels stay with the animals
            row = {"id": p["id"], "name": p.get("name"), "add_cat": claim["add_cat"],
                   "add_sub": claim["add_sub"], "now": sorted(s for s in shelves if s)}
            if claim.get("set_attrs"):
                row["set_attrs"] = claim["set_attrs"]
                if ftype:
                    row["overwrites"] = {"facilityType": ftype}
            rows.append(row)
    return rows


def dupe_key(name):
    s = unicodedata.normalize("NFC", name or "").lower()
    s = re.sub(r"[^a-z0-9ก-๙]+", "", s)
    return s


def haversine(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371000 * 2 * math.asin(math.sqrt(h))


def dupes(places):
    by_name = {}
    for p in places:
        if not (p.get("lat") and p.get("lng")):
            continue
        k = dupe_key(p.get("name"))
        if len(k) >= 6:  # short names ("401", "ร้านนวด") collide by accident
            by_name.setdefault((p["province"], k), []).append(p)
    pairs = []
    for group in by_name.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                d = haversine(a, b)
                if d <= DUPE_M:
                    pairs.append((round(d), a, b))
    return sorted(pairs, key=lambda t: t[0])


def main():
    places = load()
    rows = drift(places)
    if "--emit" in sys.argv:
        out = {}
        for r in rows:
            claimed = (r["add_sub"] or [r.get("set_attrs", {}).get("facilityType", r["add_cat"][0])])[0]
            e = {"note": f"{r['name']} — name claims {claimed}; was {'/'.join(r['now'])}",
                 "add_cat": r["add_cat"], "add_sub": r["add_sub"],
                 "source": f"osm name: {r['name']}", "fetched": ""}
            if r.get("set_attrs"):
                e["set_attrs"] = r["set_attrs"]
            out[r["id"]] = e
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    print(f"DRIFT — {len(rows)} name-vs-shelf candidates")
    for r in rows:
        claimed = (r["add_sub"] or [r.get("set_attrs", {}).get("facilityType", r["add_cat"][0])])[0]
        ow = f"  OVERWRITES {r['overwrites']}" if r.get("overwrites") else ""
        print(f"  {claimed:10} {str(r['name'])[:44]:46} now: {'/'.join(r['now'])}  [{r['id']}]{ow}")
    pairs = dupes(places)
    print(f"\nDUPES — {len(pairs)} same-name pairs within {DUPE_M} m")
    for d, a, b in pairs:
        print(f"  {d:3}m  {str(a.get('name'))[:40]:42} {a['id']} {'/'.join(sorted(set(norm(a.get('cat')))))}"
              f"  <>  {b['id']} {'/'.join(sorted(set(norm(b.get('cat')))))}")


if __name__ == "__main__":
    main()
