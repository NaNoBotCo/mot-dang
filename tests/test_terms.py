#!/usr/bin/env python3
"""The gloss layer, and the language toggle it was built to feed.

THREE KINDS OF CHECK, because they fail for different reasons.

FIXED CASES pin the glosses that are administrative fact rather than
judgement: ม.1 is Grade 7 and not Grade 1, สพป. is a primary service area and
สพม. a secondary one, ได้รับ is granted. A wrong one of these is a wrong fact
on a page, not a clumsy phrase.

REFUSALS pin the silence. terms.gloss() returns "" when any Thai word in a
value is unknown, and that is the whole reason it can be trusted: a value
half-glossed reads as if the site understood it. A change that makes it
guess would pass every other check here.

THE CORPUS FLOOR asks the question Nan actually asked — how much of what the
pages print is now readable by someone without Thai — and holds it where it
stands. It samples data/canonical, so it drifts as records arrive; a floor,
not a target.

    python3 tests/test_terms.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import terms as T  # noqa: E402
import translit  # noqa: E402

FAIL = []
THAI = re.compile(r"[฀-๿]")


def check(got, want, why):
    if got != want:
        FAIL.append(f"{why}\n     got  {got!r}\n     want {want!r}")


_LEX = {}
_p = os.path.join(ROOT, "data", "trade_lexicon.json")
if os.path.exists(_p):
    _LEX = (json.load(open(_p, encoding="utf-8")).get("areas") or {})


def read(w):
    e = _LEX.get(w) or {}
    if e.get("reading") and not e.get("suspect"):
        return e["reading"]
    return (translit.reading(w) or "").strip()


# ---------------------------------------------------------------------------
# 1. Facts, not phrasing
# ---------------------------------------------------------------------------
FIXED = [
    ("มหานิกาย", "sect", "Maha Nikaya, the larger monastic order"),
    ("ธรรมยุต", "sect", "Thammayut, the reform monastic order"),
    ("วัดราษฎร์", "watRank", "a people's temple, not a royal one"),
    ("พระอารามหลวง", "watRank", "a royal temple"),
    ("ได้รับ", "wisung", "granted"),
    ("ไม่ได้รับ", "wisung", "not granted"),
    # ป.N is Grade N; ม.N is Grade N+6. A school teaching อ.2–ม.3 teaches to
    # Grade 9, and printing "Grade 3" would send a parent to the wrong school.
    ("อ.2–ป.6", "levels", "Kindergarten 2 – Grade 6"),
    ("อ.2–ม.3", "levels", "Kindergarten 2 – Grade 9"),
    ("ม.1–ม.6", "levels", "Grade 7 – Grade 12"),
    ("ป.1–ป.6", "levels", "Grade 1 – Grade 6"),
    ("อนุบาล-ประถม", "levels", "kindergarten – primary"),
    ("บุคคลธรรมดา", "licensee", "a private individual"),
    ("มูลนิธิ", "licensee", "a foundation"),
    ("ปางช้าง", "kind", "an elephant camp"),
]
for th, field, want in FIXED:
    check(T.gloss(th, field), want, f"gloss({th!r}, {field!r})")

# สพป. vs สพม. is the difference between a primary and a secondary school,
# and the province in the middle is a NAME: read, never translated.
check(T.edu_area("สพป.เชียงราย เขต 2", read),
      "Chiang Rai Primary Education Service Area 2", "edu_area primary + area number")
check(T.edu_area("สพม.เชียงใหม่", read),
      "Chiang Mai Secondary Education Service Area", "edu_area secondary, no number")

# ---------------------------------------------------------------------------
# 2. What it refuses to say
# ---------------------------------------------------------------------------
REFUSE = [
    # A word nobody has glossed takes the whole value down with it, rather
    # than printing "residential unit · ??? · balcony area".
    ("ห้องชุดพักอาศัย/คำที่ยังไม่มีใครแปล", "registerUses"),
    # A field with no table at all says nothing.
    ("มหานิกาย", "fieldThatDoesNotExist"),
    # A name is not a term. Nothing here may translate one.
    ("วัดพระสิงห์", "sect"),
    ("", "levels"),
]
for v, field in REFUSE:
    got = T.gloss(v, field)
    if got:
        FAIL.append(f"gloss({v!r}, {field!r}) should have refused, said {got!r}")

# The tail is READ, never translated, and only where a head word was known.
check(T.gloss("ลานจอดรถ มหาวิทยาลัยเชียงใหม่", "nameBase", read_tail=read),
      "parking yard Chiang Mai University", "head glossed, tail read")
if T.gloss("ลานจอดรถ มหาวิทยาลัยเชียงใหม่", "nameBase"):
    FAIL.append("a tail was read without a romaniser being passed")

# ---------------------------------------------------------------------------
# 3. The address, decomposed
# ---------------------------------------------------------------------------
check(T.address("ตำบลหนองบัว อำเภอไชยปราการ จังหวัดเชียงใหม่", read),
      [("Tambon", "Nong Bua"), ("Amphoe", "Chai Prakan"), ("Changwat", "Chiang Mai")],
      "three units, each cut at the next prefix")
# A comma ends a unit: "ต.วัดเกต, เมือง" must not invent a Tambon Wat Ket Mueang.
check(T.address("ถ.แก้วนวรัฐ ต.วัดเกต, เมือง, 50000", read)[-1],
      ("Tambon", "Wat Ket"), "a comma ends the unit")
# An address that labels nothing gets nothing, rather than a run-on reading.
check(T.address("ตรงข้ามตลาด 100 เมตร", read), [], "no labelled unit, no reading")
# The postcode is not part of the province's name.
for _lbl, _nm in T.address("อ.พาน จ.เชียงราย 57280", read):
    if re.search(r"\d", _nm):
        FAIL.append(f"a postcode rode into a name: {_nm!r}")

# ---------------------------------------------------------------------------
# 4. The agencies, whole-string only
# ---------------------------------------------------------------------------
check(T.agency("กรมธนารักษ์"), "The Treasury Department", "agency by its own English")
if T.agency("กรมธนารักษ์แห่งหนึ่ง"):
    FAIL.append("agency() matched a prefix; it must match whole strings only")

# ---------------------------------------------------------------------------
# 5. The corpus floor — how much of what the pages print is now readable
# ---------------------------------------------------------------------------
FIELD_FLOOR = {"sect": 1.0, "watRank": 1.0, "wisung": 1.0, "levels": 1.0,
               "licensee": 0.98, "officialType": 0.9}
ADDRESS_FLOOR = 0.90

recs = []
for pv in ("cm", "cr"):
    p = os.path.join(ROOT, "data", "canonical", f"{pv}.json")
    if os.path.exists(p):
        recs += json.load(open(p, encoding="utf-8"))

if recs:
    seen = {f: [0, 0] for f in FIELD_FLOOR}
    addr = [0, 0]
    for r in recs:
        a = r.get("attrs") or {}
        for f in FIELD_FLOOR:
            v = a.get(f)
            if isinstance(v, str) and THAI.search(v):
                seen[f][1] += 1
                if T.gloss(v, f):
                    seen[f][0] += 1
        ad = r.get("address") or ""
        if THAI.search(ad) and not re.search(r"[A-Za-z]{2,}", ad):
            addr[1] += 1
            if T.address(ad, read):
                addr[0] += 1
    for f, floor in FIELD_FLOOR.items():
        hit, tot = seen[f]
        if not tot:
            continue
        share = hit / tot
        print(f"  {f:14} {hit:6,}/{tot:6,} glossed = {share:6.1%}")
        if share < floor:
            FAIL.append(f"{f} gloss coverage fell to {share:.1%} (floor {floor:.0%})")
    if addr[1]:
        share = addr[0] / addr[1]
        print(f"  {'address':14} {addr[0]:6,}/{addr[1]:6,} decomposed = {share:6.1%}")
        if share < ADDRESS_FLOOR:
            FAIL.append(f"address decomposition fell to {share:.1%} "
                        f"(floor {ADDRESS_FLOOR:.0%})")
else:
    print("  corpus floor: skipped — data/canonical not built")

# ---------------------------------------------------------------------------
if FAIL:
    print(f"\nFAIL — {len(FAIL)} problem(s):\n")
    for f in FAIL:
        print("  *", f)
    sys.exit(1)
print(f"OK — {len(FIXED) + len(REFUSE) + 10} checks")
