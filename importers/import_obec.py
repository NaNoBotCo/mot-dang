#!/usr/bin/env python3
"""Every government school in both provinces, from the state's own register.

WHY THIS EXISTS. A directory for Chiang Mai and Chiang Rai held FOURTEEN
schools. Not fourteen thousand, fourteen — and every one of them was an
international school, because `crawl_overpass.py` asked for `amenity=school`
only where the name matched `International|นานาชาติ`. One regex, written early
and never revisited, decided that the only schools worth crawling were the ones
a foreigner might attend. The census counts around 800 ordinary schools in OSM
that were never once asked for, and this register names 1,302.

THE SOURCE. รายชื่อโรงเรียนในสังกัดสำนักงานคณะกรรมการการศึกษาขั้นพื้นฐาน (สพฐ.)
— the OBEC school register, served as JSON at
https://opendata.edudev.in.th/v1/OBEC_SCHOOL_007 with no key and no signup,
catalogued on gdcatalog.go.th as `gdpublish-obec-school-007` and sourced from
DMC, the ministry's own per-pupil record system. 29,642 schools nationwide;
713 in Chiang Mai and 589 in Chiang Rai.

WHAT MAKES IT BETTER THAN CITIZENinfo. That file (importers/import_citizeninfo.py)
had no phone number in it at all — checked in CSV, XLSX and ZIP. This one
carries a telephone for 1,147 of 1,302 schools, which is 88% on a site whose
overall contactable figure is around 19%. Contact information is the currency
here; this is the largest single deposit the directory has ever taken.

It also carries what a parent actually asks: which levels the school teaches
(อ.1 through ม.6), how many pupils are enrolled, which education service area
it answers to, and whether it stands on the ดอย.

WHAT IT DOES NOT COVER, and the page must not imply otherwise: private schools
(that is สช., see import_opec.py), universities and colleges, municipal and
อบจ. schools, monastic schools, and every non-formal school — language, muay
thai, cooking, massage, driving. This is the สพฐ. sector and nothing else.

ENROLMENT IS A FACT, NOT A LEAGUE TABLE. `students` is published because a
12-pupil school on a ridge and a 3,000-pupil school in town are different
places and a parent deserves to know which one they are looking at. It is
carried with the register's own date and it is never a sort. The practice
about temples never being ranked against each other applies here with more
force, not less — these are children's schools.

THE PINS, MEASURED. 1,301 of 1,302 rows carry coordinates and the register is
far cleaner than its reputation: Thai mappers on the OSM forum report roughly
6% bad GPS in government sources of this kind, and a check against the
register's own geography finds 5 wrong pins — 0.38%. Two sit in other
provinces entirely (one in Bangkok, one out past Khon Kaen), three sit inside
the right province but tens of kilometres from every other school in their own
district. Those five lose their pin and keep their record; a school does not
stop existing because somebody typed a coordinate wrong.

The test is deliberately two-stage and neither stage is a flat number.
Districts here are enormous — อมก๋อย reaches the Tak border and its schools sit
45 km from their own district median while being exactly where they should be.
A flat 25 km rule would have thrown away 104 highland schools, which are
precisely the schools this directory exists to carry.
"""
import json
import math
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "cache", "obec", "OBEC_SCHOOL_007.json")
REVIEW = os.path.join(ROOT, "cache", "obec_pin_review.txt")

ENDPOINT = "https://opendata.edudev.in.th/v1/OBEC_SCHOOL_007"
DATASET = "https://gdcatalog.go.th/dataset/gdpublish-obec-school-007"
LICENCE = "Open Data Common (gdcatalog.go.th)"
CREDIT = "ทะเบียนโรงเรียน สพฐ. · สำนักงานคณะกรรมการการศึกษาขั้นพื้นฐาน"
# The register publishes an academic year, not a fetch date. Both are carried:
# the year is what the figures describe, the fetch is when we took a copy.
FETCHED = "2026-08-18"

PROVINCE = {"เชียงใหม่": "cm", "เชียงราย": "cr"}

# A pin outside this is in another province. Bounds are the register's own
# trimmed extent (99.5th percentile, so the two gross errors cannot set them),
# widened south for Chiang Mai because อมก๋อย genuinely reaches past 17.26°N
# and its schools must survive the test that exists to protect them.
BOX = {"cm": (17.10, 20.25, 97.30, 99.65),
       "cr": (18.95, 20.55, 99.15, 100.65)}

# A school that stands far from every other school in its own อำเภอ is a typo,
# but "far" has to be read against how big that district is. The limit is three
# times the district's own 75th-percentile spread, floored at 25 km so a tight
# urban district cannot set an absurdly small one.
DISTRICT_SPREAD_MULT = 3.0
DISTRICT_FLOOR_KM = 25.0

SCHOOL_WORDS = ("โรงเรียน", "ร.ร.", "วิทยาลัย", "มหาวิทยาลัย", "ศูนย์")


def _km(alat, alng, blat, blng):
    dy = (alat - blat) * 110.574
    dx = (alng - blng) * 111.320 * math.cos(math.radians((alat + blat) / 2))
    return math.hypot(dx, dy)


def thai_phone(raw):
    """The register writes a Chiang Mai number four different ways.

    Measured across the 1,147 numbers in these two provinces: 880 arrive as
    nine digits (053222475), 255 as a ten-digit mobile, and a handful as
    0-5324-0062 or 053 247724. Five arrive as EIGHT digits beginning 53 —
    the leading zero dropped somewhere upstream — and those are restored here
    rather than discarded, because 53222475 is unmistakably 053-222475 in a
    file that only holds Chiang Mai and Chiang Rai.

    Everything else is dropped. A wrong number on a school is worse than a
    blank one: it is somebody's house, ringing.
    """
    d = re.sub(r"[^\d]", "", str(raw or ""))
    if not d:
        return None
    # 052/053/054 are the northern landline blocks; 8 digits starting with 5
    # is one of those with the zero lost.
    if len(d) == 8 and d[0] == "5":
        d = "0" + d
    if not d.startswith("0"):
        return None
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    if len(d) == 9:
        return f"02-{d[2:]}" if d.startswith("02") else f"{d[:3]}-{d[3:]}"
    return None


def _name(raw):
    """โรงเรียนบ้านต้นขาม, not บ้านต้นขาม.

    The register stores the bare name, which on a directory page reads as a
    village rather than a school. Every row in this file is officially a
    โรงเรียน and is spoken of that way, so the word is restored where the name
    does not already carry one. The register's exact string is kept in
    attrs.registerName so nothing is lost.
    """
    n = (raw or "").strip()
    if not n:
        return None
    if any(n.startswith(w) for w in SCHOOL_WORDS):
        return n
    return "โรงเรียน" + n


def _address(r):
    """The register splits an address across villageName, moo, subdistrict and
    district, and writes "-" for every part it does not have. villageName is
    itself a composite ("154 4 - เชียงใหม่-แม่ริม" = house number, moo, village,
    road), so it is rebuilt from its own non-empty pieces rather than printed
    raw with its dashes showing."""
    head = " ".join(p for p in str(r.get("villageName") or "").split()
                    if p and p != "-")
    parts = [head]
    moo = str(r.get("moo") or "").strip()
    if moo and moo != "-":
        parts.append(f"หมู่ {moo}")
    for key, prefix in (("subdistrict", "ต."), ("district", "อ."),
                        ("province", "จ.")):
        v = str(r.get(key) or "").strip()
        if v and v != "-":
            parts.append(prefix + v)
    post = str(r.get("postCode") or "").strip()
    if post and post.isdigit():
        parts.append(post)
    out = " ".join(p for p in parts if p).strip()
    return out or None


def _kind(r):
    """Which shelf. The register's own schoolType is the authority — nothing
    here is guessed from a name."""
    t = (r.get("schoolType") or "").strip()
    if t == "ศึกษาพิเศษ":
        return "special"
    if t == "ศึกษาสงเคราะห์":
        return "welfare"
    return "government"


def _levels(r):
    """อ.2–ป.6 as the register states it. '0' means the register does not say,
    and is carried as nothing rather than as a level."""
    lo = str(r.get("classMinLevel") or "").strip()
    hi = str(r.get("classMaxLevel") or "").strip()
    lo = lo if lo and lo != "0" else None
    hi = hi if hi and hi != "0" else None
    if lo and hi:
        return f"{lo}–{hi}" if lo != hi else lo
    return lo or hi


def _attrs(r, kind):
    a = {
        "facilityType": kind,
        "obecCode": str(r.get("moeCode") or "").strip() or None,
        "sector": "state",
        "eduArea": (r.get("areaName") or "").strip() or None,
        "levels": _levels(r),
        "schoolSector": "obec",
    }
    students = r.get("students")
    if isinstance(students, int):
        a["students"] = students
    rooms = r.get("room")
    if isinstance(rooms, int) and rooms:
        a["classrooms"] = rooms
    size = (r.get("schoolSize") or "").strip()
    if size:
        # "ขนาด2_121-200" — the band is the useful half.
        a["sizeBand"] = size.split("_", 1)[-1] if "_" in size else size
    # 424 of 1,302 stand on the ดอย. These are the schools no other directory
    # of either province carries, and the register says so itself.
    if (r.get("highArea") or "").strip() == "พื้นที่สูง":
        a["highland"] = True
    geo = (r.get("geoLocation") or "").strip()
    if "ชายแดน" in geo:
        a["borderland"] = True
    if (r.get("expandOp") or "").strip() == "ใช่":
        # โรงเรียนขยายโอกาส — a primary school that added lower secondary so the
        # village's children do not have to travel to finish it.
        a["expandOpportunity"] = True
    if (r.get("branch") or "").strip() == "ใช่":
        a["branchSchool"] = True
    a["registerName"] = (r.get("schoolName") or "").strip() or None
    return {k: v for k, v in a.items() if v not in (None, "")}


def records():
    if not os.path.exists(SRC):
        print(f"obec: missing {SRC} — fetch {ENDPOINT} into it "
              f"(23 MB, no key needed)")
        return []
    try:
        rows = json.load(open(SRC, encoding="utf-8"))
    except Exception as exc:                       # noqa: BLE001
        print(f"obec: cannot read {SRC} ({exc}) — not importing")
        return []
    if not isinstance(rows, list) or not rows:
        print("obec: register is empty or not a list — not importing")
        return []
    if "moeCode" not in rows[0] or "schoolName" not in rows[0]:
        print("obec: shape changed (no moeCode/schoolName) — not importing")
        return []

    ours = [r for r in rows if (r.get("province") or "").strip() in PROVINCE]

    # --- pin validation, stage one: is it even in the right province ---
    def coords(r):
        try:
            lat = float(r["latitude"])
            lng = float(r["longitude"])
        except (KeyError, TypeError, ValueError):
            return None
        return (lat, lng)

    bad = {}
    placed = []
    for r in ours:
        c = coords(r)
        if c is None:
            bad[id(r)] = "no coordinates in the register"
            continue
        prov = PROVINCE[(r.get("province") or "").strip()]
        lo_lat, hi_lat, lo_lng, hi_lng = BOX[prov]
        if not (lo_lat <= c[0] <= hi_lat and lo_lng <= c[1] <= hi_lng):
            bad[id(r)] = f"pin {c[0]:.4f},{c[1]:.4f} is outside the province"
            continue
        placed.append((r, c))

    # --- stage two: is it near the other schools of its own district ---
    by_district = {}
    for r, c in placed:
        by_district.setdefault(
            (r.get("province"), r.get("district")), []).append((r, c))
    for key, group in by_district.items():
        if len(group) < 5:
            continue                      # too few to say anything about
        mlat = statistics.median(c[0] for _, c in group)
        mlng = statistics.median(c[1] for _, c in group)
        spread = sorted(_km(c[0], c[1], mlat, mlng) for _, c in group)
        p75 = spread[int(len(spread) * 0.75)]
        limit = max(DISTRICT_FLOOR_KM, p75 * DISTRICT_SPREAD_MULT)
        for r, c in group:
            d = _km(c[0], c[1], mlat, mlng)
            if d > limit:
                bad[id(r)] = (f"pin {c[0]:.4f},{c[1]:.4f} is {d:.0f} km from "
                              f"the other schools of อ.{key[1]} "
                              f"(limit {limit:.0f} km)")

    out, seen, review = [], set(), []
    for r in ours:
        code = str(r.get("moeCode") or "").strip()
        name = _name(r.get("schoolName"))
        if not code or not name or code in seen:
            continue
        seen.add(code)
        prov = PROVINCE[(r.get("province") or "").strip()]
        kind = _kind(r)
        why = bad.get(id(r))
        c = None if why else coords(r)
        if why:
            review.append(f"{prov}  {name}  (อ.{r.get('district')})  — {why}")
        rec = {
            "id": f"{prov}-obec-{code}",
            "province": prov,
            "cat": ["school"],
            "sub": [kind],
            "name": name,
            "nameTh": name, "nameEn": None,
            "lat": c[0] if c else None,
            "lng": c[1] if c else None,
            # A school whose pin we refused still deserves to be found. The
            # gazetteer (geocode_local.py) can place it from its address, and
            # /pins.html already exists to walk the rest onto the map.
            "geoPrecision": "exact" if c else "needs-pin",
            "address": _address(r),
            "phone": thai_phone(r.get("telephone")),
            "website": None,
            "hours": None,
            "attrs": _attrs(r, kind),
            "featured": False,
            "landmark": False,
            "sources": [{"type": "opendata", "ref": DATASET,
                         "endpoint": ENDPOINT, "fetched": FETCHED,
                         "via": "ทะเบียนโรงเรียน สพฐ. (OBEC)",
                         "licence": LICENCE, "credit": CREDIT}],
            "confidence": "official",
            "updatedAt": FETCHED,
        }
        out.append(rec)

    if review:
        with open(REVIEW, "w", encoding="utf-8") as fh:
            fh.write("Schools whose register pin was refused.\n"
                     "The record is kept and published; only the coordinate is\n"
                     "dropped, and geocode_local.py may place it from its\n"
                     "address. Walk one and it can be pinned for good.\n\n")
            fh.write("\n".join(review) + "\n")
        print(f"obec: {len(review)} pin(s) refused — see {REVIEW}")
    return out


if __name__ == "__main__":
    import collections
    recs = records()
    print(f"obec: {len(recs)} schools")
    print("  by province:", dict(collections.Counter(r["province"] for r in recs)))
    print("  by kind:", dict(collections.Counter(r["sub"][0] for r in recs)))
    print("  with a phone:",
          sum(1 for r in recs if r["phone"]), f"of {len(recs)}")
    print("  pinned:", sum(1 for r in recs if r["lat"]),
          "| awaiting a pin:", sum(1 for r in recs if not r["lat"]))
    print("  on the ดอย:", sum(1 for r in recs if r["attrs"].get("highland")))
    print("  ขยายโอกาส:",
          sum(1 for r in recs if r["attrs"].get("expandOpportunity")))
    if "--sample" in sys.argv:
        for r in recs[:10]:
            print(f"   {r['province']}  {r['name'][:34]:34} "
                  f"{r['attrs'].get('levels','—'):11} {r['phone'] or '—':14} "
                  f"{r['attrs'].get('eduArea','—')}")
