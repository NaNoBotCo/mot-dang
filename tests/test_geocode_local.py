#!/usr/bin/env python3
"""The gazetteer must not be confidently wrong, and a sign's spelling must reach it.

Two defects measured on 2026-09-07 (WO-73), each pinned here so it stays fixed:

  1. ถนนโชตนา in อ.ฝาง was matched to the Chiang Mai city stub of a road that
     runs 128 km north, and declared ±280 m — half the length of the fragment
     we HOLD, not of the road. The worst five of every --validate run were
     that one failure. A street nobody else in the address vouches for (no
     tambon centroid, no postcode centroid within reach) now answers at
     ±3,000 m or more, which is above the publish cap: not published, rather
     than published wrong.

  2. streets.json spells Thapae Road and Huaykaew Road; addresses say
     Tha Phae Rd and Huay Kaew Rd. A space-blind index (2026-09-05) caught
     Wualai; the aspirate and the closing y/w are RULES (geocode_local._sign),
     and the residue the rules cannot reach is a hand-written row in
     data/curated/street_aliases.json — never a fuzzy matcher.

    python3 tests/test_geocode_local.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))

import geocode_local as G  # noqa: E402

FAIL = []


def check(cond, why):
    if not cond:
        FAIL.append(why)


g = G.Gazetteer()


def locate(addr, prov="cm"):
    return g.locate(addr, prov)


# 1. an unwitnessed street is never a confident answer -----------------------
for addr in ("239 ถนนโชตนา ต.เวียง อ.ฝาง เชียงใหม่ 50110",
             "ถนนโชตนา อ.ฝาง",
             "Chotana Road, Fang"):
    r = locate(addr)
    check(r is None or r["precision"] != "street" or r["uncertainty_m"] >= 3000,
          f"{addr!r}: a street with no witness answered {r}")

# ...but a witnessed one keeps its real uncertainty
r = locate("24/1 Moon Muang Rd Lane 6, Tambon Si Phum, Amphoe Mueang Chiang Mai, 50200")
check(r and r["precision"] == "street" and r["uncertainty_m"] < 3000,
      f"Moon Muang with tambon and postcode should be a street pin, got {r}")

# 2. the sign's spelling reaches the road -----------------------------------
SAME = [
    ("12 Tha Phae Rd, Si Phum, Chiang Mai 50200", "12 Thapae Road, Si Phum, Chiang Mai 50200"),
    ("Wualai Rd, Hai Ya, Chiang Mai 50100", "Wua Lai Road, Hai Ya, Chiang Mai 50100"),
    ("Huay Kaew Rd, Suthep, Chiang Mai 50200", "Huai Kaeo Road, Suthep, Chiang Mai 50200"),
    ("Chang Klan Road, Chang Khlan, Chiang Mai 50100", "Changklan Rd, Chang Khlan, Chiang Mai 50100"),
    ("Nimmanhaemin Rd, Suthep, Chiang Mai 50200", "3 ถนนนิมมานเหมินท์ ตำบลสุเทพ อำเภอเมืองเชียงใหม่ 50200"),
]
for a, b in SAME:
    ra, rb = locate(a), locate(b)
    check(ra and rb and ra["precision"] == "street" and rb["precision"] == "street"
          and ra.get("street_slug") == rb.get("street_slug"),
          f"{a!r} and {b!r} should land on one road: {ra and ra.get('matched')} / {rb and rb.get('matched')}")

# a district word in front of a name makes it a district, not a road
r = locate("ถนนโชตนา ต.ช้างเผือก อ.เมืองเชียงใหม่ 50300")
check(r and "chotana" in (r.get("street_slug") or ""),
      f"ต.ช้างเผือก is a tambon here, not Changpuak Road: {r}")
# ...and the named อำเภอ is a witness: a road outside it is the wrong road
r = locate("30 ม.4 ถ.โชตนา หมู่ 4 ต.เวียง อ.ฝาง จ.เชียงใหม่ 50110")
check(r and r["precision"] != "street", f"Fang's Chotana is not the city's: {r}")

# the tambon's name is also a road's name: the longer road name still wins
r = locate("Huay Kaew Rd, Suthep, Chiang Mai 50200")
check(r and "huaykaew" in (r.get("street_slug") or ""),
      f"Huay Kaew must not be answered by Suthep Road: {r}")

# 3. the sign rule itself
check(G._sign(G._norm("tha phae road")) == G._sign(G._norm("thapae road")) == "tapae",
      "aspirate and space fold to one key")
check(G._sign("huay kaew") == G._sign("huai kaeo"), "closing y/w fold to i/o")
check(G._sign("นิมมาน") == "", "Thai keys are not sign-folded")

if FAIL:
    print("FAIL —", len(FAIL), "problem(s):")
    for f in FAIL:
        print("  *", f)
    sys.exit(1)
print("OK — gazetteer: unwitnessed streets stay unpublished, sign spellings resolve")
