#!/usr/bin/env python3
"""front_layer.venue_finder: which place an event's venue string pins, on made-up places.

A pin comes only from a name that is the place's own. Checked here:

  1. the hand-kept alias (data/curated/venue_aliases.json) leads, and a place with a
     district-centre pin (approx) is never added through it;
  2. spelling: '@', markdown, an address tail, a second line, 'at' halves;
  3. word sets: a place's words inside the venue string, or the venue's inside the place's;
  4. traps stay unmatched: an extra distinctive word, a one-word name, a different
     place of the same kind, two places far apart, Chiang Rai places, 'Kriangkrai' is not Rai.

    python3 tests/test_event_venues.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import front_layer as F  # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


def P(i, name, lat=18.79, lng=98.98, prec="exact", prov="cm", en=None, rank=3):
    return {"id": i, "slug": i, "province": prov, "name": name, "nameEn": en or name, "lat": lat, "lng": lng,
            "geoPrecision": prec, "antRank": rank}


PLACES = [
    P("maa", "maa Yoga & Spa"),
    P("rincome", "Eat at Rincome"),
    P("payap-lll", "Payap University Lifelong Learning Center"),
    P("payap", "Payap University"),
    P("meta", "Meta Mall", 18.82, 99.04),
    P("cm-intl", "Chiang Mai International School"),
    P("dog-think", "Dogaholic Think Park"),
    P("station", "Chiang Mai Railway Station"),
    P("kad", "กาดเกรียงไกร", en="Kad Kriangkrai", prec="approx"),
    P("rai-kad", "Kad Kriangkrai Rai", prov="cr"),
    P("loft-a", "Loft Studio Nimman", 18.80, 98.97),
    P("loft-b", "Loft Studio Hangdong", 18.69, 98.92),
    P("f4t", "F4T", prec="approx"),
    P("denplace", "theDENcnx"),
    P("nopin", "Coco Homestay", prec="needs-pin", lat=None, lng=None),
    P("rai-hotel", "Dusit Rai Lodge", 19.9, 99.8, prov="cr"),
    P("cm-hotel", "Dusit Rai Lodge", 18.8, 98.99),
    P("cmu", "Chiang Mai University"),
    P("cmu-lab", "Chiang Mai University Lab", 18.75, 98.95),
    P("campus", "TNSU, Thailand National Sports University, Chiangmai Campus"),
    P("unique", "Skugga Estate Vineyard"),
]
ALIASES = {
    "the den cnx": {"place_id": "denplace", "why": "x"},
    "f4t": {"place_id": "f4t", "why": "x"},
    "coco restaurant homestay": {"place_id": "nopin", "why": "x"},
    "chiang mai railway station park": {"place_id": "payap", "why": "x"},
}
v = F.venue_finder(PLACES, ALIASES)


def hit(name, want, city=""):
    got = v(name, city)
    check(f"{name!r} -> {want}", (got or {}).get("id") == want, (got or {}).get("id"))


# 1. aliases
hit("The DEN Cnx", "denplace")
hit("F4T", None)                       # approx pin: the alias adds nothing, the name is 3 letters
hit("Coco Restaurant & Homestay", None)  # the record has no coordinates
hit("Chiang Mai Railway Station Park", "payap")  # the alias beats the station prefix

# 2. spelling
hit("Eat@Rincome", "rincome")
hit("**Venue:** Meta Mall", "meta")
hit("Meta Mall, 99 Moo 3, San Sai", "meta")
hit("Meta Mall Second line, ignored", "meta")
hit("Kad Kriangkrai", "kad")           # 'kriangkrai' holds 'rai' and is still Chiang Mai

# 3. word sets
hit("Maa Yoga Studio & Spa", "maa")
hit("Lifelong Learning Payap Center", "payap-lll")
hit("Rimping Meta Mall", None)         # 'rimping' is not a plain extra word
hit("Payap Lifelong Learning Center", "payap-lll")
hit("Chiang Mai University (CMU) - Bench at the gate", "cmu")
hit("TNSU Campus Chiang Mai", None)           # an acronym is not a plain extra word

# 4. traps
hit("Unity Concord International School", None)   # unity, concord name another school
hit("Think Park", None)                           # two words inside a three-word dog cafe
hit("Yoga at Wat Suan Dok", None)                 # a part of one word is not a name
hit("Loft Studio", None)                          # two places 12 km apart
hit("Dusit Rai Lodge", "rai-hotel")               # says Rai
hit("Dusit Rai Lodge", "rai-hotel", city="cr")
hit("Dusit Lodge Chiang Mai", None)
hit("", None)
hit("Cafe", None)

# the alias file itself
aliases = json.loads((ROOT / "data/curated/venue_aliases.json").read_text(encoding="utf-8"))["aliases"]
check("alias keys are in the form the lookup uses", all(k == F._vkey(k) for k in aliases),
      [k for k in aliases if k != F._vkey(k)][:3])
check("alias rows name a place", all(isinstance(a, dict) and a.get("place_id") for a in aliases.values()))

print(f"\n{'FAILED: ' + ', '.join(failures) if failures else 'all passed'}")
sys.exit(1 if failures else 0)
