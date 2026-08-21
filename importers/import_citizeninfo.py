#!/usr/bin/env python3
"""Government health facilities, with real coordinates, from open government data.

WHY THIS EXISTS. The medical shelf had never been crawled — no clinic, doctors,
hospital, dentist or pharmacy selector existed in crawl_overpass.py, and no
classify() rule for any of them. Chiang Mai's 233 records had all arrived from
the cm-womens-health import, which is a women's-health slice and not a medical
directory. CHIANG RAI HAD THREE RECORDS FOR A WHOLE PROVINCE. This file alone
takes Chiang Rai from 3 to 228.

THE SOURCE. ข้อมูลพิกัดสถานพยาบาลของรัฐจากระบบ CITIZENinfo, published by
สำนักงานพัฒนารัฐบาลดิจิทัล (DGA) on data.go.th under **Creative Commons
Attribution**. 10,715 rows nationwide; 524 of them are in Chiang Mai and Chiang
Rai and every single one carries a latitude and a longitude. That is the whole
point: these are surveyed government pins, not addresses we had to guess at.

The credit is a licence condition, not a courtesy, so it travels on every
record's `sources` entry and is named in data/sources.json.

WHAT IS IN IT, measured before this was written: 477 โรงพยาบาลส่งเสริมสุขภาพ
ตำบล (รพ.สต. — the subdistrict health-promoting hospitals that are the whole
backbone of rural care here, and which no other directory of this province
lists) and 47 โรงพยาบาล. Nothing else; there is no third kind to handle.

WHAT IS NOT IN IT. Private clinics. This is the state sector only — the OSM
`medical` crawl group covers the private half. สสจ.เชียงราย's own open figure
puts Chiang Rai at 628 clinics of all types (2564), so between this and the
crawl the shelf is still short of the ground, and the page should say so rather
than imply completeness.

DATED. The file is stamped 2020-03-14 by its publisher and that date rides on
every record. A รพ.สต. does not move, but it can close, and a six-year-old
pin presented as current is a claim we have not earned.
"""
import csv
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "cache", "citizeninfo", "health.csv")
# The publisher's own stamp, carried in the filename they serve it under.
PUBLISHED = "2020-03-14"
LICENCE = "CC-BY (data.go.th)"
CREDIT = "ระบบ CITIZENinfo · สำนักงานพัฒนารัฐบาลดิจิทัล (DGA)"
DATASET = ("https://data.go.th/dataset/"
           "00170665-bda1-4f4a-ad7c-52dac7abc7a5")

PROVINCE = {"เชียงใหม่": "cm", "เชียงราย": "cr"}


def _text():
    raw = open(SRC, "rb").read()
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _province(address):
    """Which province, read from the จ./จังหวัด marker rather than from any
    mention of the word. An address in Chiang Rai can name Chiang Mai in a road
    name — ถ.เชียงราย-เชียงใหม่ runs between them — and filing a place by the
    first province word it happens to contain is how a clinic ends up in the
    wrong one."""
    m = re.findall(r"(?:จ\.|จังหวัด)\s*(เชียงใหม่|เชียงราย)", address or "")
    if m:
        return PROVINCE[m[-1]]
    return None


def _kind(name):
    """(facilityType, sub). Measured: the file holds exactly two kinds."""
    if "โรงพยาบาลส่งเสริมสุขภาพตำบล" in name or "สถานีอนามัย" in name:
        return "health-station", "health-station"
    if "โรงพยาบาล" in name:
        return "hospital", "hospital"
    return "clinic", "clinic"


def _clean(name, province):
    """Drop the trailing province tag the register appends to its own names.

    "โรงพยาบาลดอยเต่า จังหวัดเชียงใหม่" is the register's full official string;
    on a page that already says which province it is in, the tail is noise.
    Only an exact trailing match is removed — nothing is reworded, and a name
    that carries the province in the middle keeps it.
    """
    th = "เชียงใหม่" if province == "cm" else "เชียงราย"
    for tail in (f" จังหวัด{th}", f" จ.{th}", f" {th}"):
        if name.endswith(tail):
            return name[: -len(tail)].strip()
    return name.strip()


def records():
    if not os.path.exists(SRC):
        print(f"missing {SRC} — see the module docstring for the dataset URL")
        return []
    rows = list(csv.reader(io.StringIO(_text())))
    if not rows:
        return []
    H = {h: i for i, h in enumerate(rows[0])}
    need = ("รหัสหน่วยงาน", "หน่วยงาน", "ที่อยู่จุดบริการ", "ละติจูด", "ลองติจูด")
    missing = [k for k in need if k not in H]
    if missing:
        print(f"citizeninfo: header changed, missing {missing} — not importing")
        return []

    out, seen, skipped = [], set(), 0
    for r in rows[1:]:
        if len(r) <= max(H[k] for k in need):
            continue
        addr = r[H["ที่อยู่จุดบริการ"]].strip()
        prov = _province(addr)
        if prov is None:
            continue
        name = r[H["หน่วยงาน"]].strip()
        code = r[H["รหัสหน่วยงาน"]].strip()
        try:
            lat = float(r[H["ละติจูด"]])
            lng = float(r[H["ลองติจูด"]])
        except (ValueError, TypeError):
            skipped += 1
            continue
        # A pin outside the two provinces is a bad row, not a discovery.
        if not (17.0 < lat < 21.0 and 97.5 < lng < 100.8):
            skipped += 1
            continue
        if not name or not code or code in seen:
            continue
        seen.add(code)
        ftype, sub = _kind(name)
        out.append({
            "id": f"{prov}-moph-{code}",
            "province": prov, "cat": ["medical"], "sub": [sub],
            "name": _clean(name, prov), "nameTh": None, "nameEn": None,
            "lat": lat, "lng": lng, "geoPrecision": "exact",
            "address": addr or None, "phone": None, "website": None,
            "hours": None,
            "attrs": {"facilityType": ftype, "mophCode": code,
                      "sector": "state"},
            "featured": False, "landmark": False,
            "sources": [{"type": "opendata", "ref": DATASET,
                         "fetched": PUBLISHED, "via": "CITIZENinfo (DGA)",
                         "licence": LICENCE, "credit": CREDIT}],
            "confidence": "official", "updatedAt": PUBLISHED,
        })
    if skipped:
        print(f"citizeninfo: {skipped} row(s) skipped (bad or out-of-area coordinates)")
    return out


if __name__ == "__main__":
    import collections
    recs = records()
    print(f"citizeninfo: {len(recs)} facilities")
    print("  by province:", dict(collections.Counter(r["province"] for r in recs)))
    print("  by kind:", dict(collections.Counter(r["sub"][0] for r in recs)))
    if "--sample" in sys.argv:
        for r in recs[:8]:
            print(f"   {r['province']}  {r['name'][:46]:46} {r['lat']:.4f},{r['lng']:.4f}")
