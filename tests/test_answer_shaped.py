#!/usr/bin/env python3
"""Answer-shaped tests: a reader's question, and the records that must answer it.

Every other test here counts shelves. A shelf count says "massage: 302" and
cannot see that the one thing a reader asked for — tok sen, in the old city,
after dinner — was on none of the 302 records. That is the search disease
(notes/search-disease-cure-plan-2026-09-05.txt): the unit of indexing is the
NAME and the unit of demand is the NEED. So this file asks the corpus the
reader's question, in the reader's shape, and fails when the answer is empty.

Phase 0 of the cure ships ONE case, the type case, against the data layer
(canonical records + the moat polygon build.py draws + the same hours grammar
the lamps use). Phase 4 grows it into tests/answers.json, fifty questions,
scored against all three doors (site search, /api/search, the assistant).

    python3 tests/test_answer_shaped.py      # reads data/canonical only
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


# One case = one question a reader actually asked (Nan, 2026-09-04: a tok sen
# shop, old city, finishing at ten at night). Fields:
#   cat/sub      the shelf the answer lives on
#   area         "old-city" = inside the moat ring build.py draws
#   open_past    "HH:MM" — the place must still be open at this time on at
#                least one day, by the lamp grammar (unparseable hours = not
#                open; an honest "closes about 22:00 (observed)" does not count
#                until it is written as hours)
#   min          how many records must survive every filter
CASES = [
    {"q": "toksen in the old city, open past 21:00",
     "province": "cm", "cat": "massage", "sub": "tok-sen",
     "area": "old-city", "open_past": "21:00", "min": 1},
    # Nan, 2026-09-21: searched the live site for kratom and the shelf
    # answered with one shop. It held one in each province while nine shops
    # in the weed.th harvest carried ใบกระท่อม or Kratom on their own sign
    # and were shelved "dispensary" alone — the same shelf-not-source defect
    # the tok-sen case above was written for. No area or hours filter: the
    # question here is only whether the shelf can answer its own name.
    # These floors are what the corpus holds, not what the trade is; the
    # gap between them is in notes/kratom-2026-09-21.txt.
    {"q": "a kratom shop in Chiang Mai",
     "province": "cm", "cat": "cannabis", "sub": "kratom", "min": 5},
    {"q": "a kratom shop in Chiang Rai",
     "province": "cr", "cat": "cannabis", "sub": "kratom", "min": 2},
]


def inside(poly, lat, lng):
    """Ray casting over the moat ring — the same test build.py's map runs."""
    n = len(poly)
    hit = False
    for i in range(n):
        y1, x1 = poly[i]
        y2, x2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            x = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lng < x:
                hit = not hit
    return hit


def open_past(hours, hhmm):
    from build_open_lamps import parse_hours
    if not hours:
        return False
    spans = parse_hours(hours)
    if not spans:
        return False
    h, m = map(int, hhmm.split(":"))
    for day in range(7):
        t = day * 1440 + h * 60 + m
        if any(s <= t < e for s, e in spans):
            return True
    return False


def main():
    import build   # for MOAT_POLY, the ring the site itself draws
    poly = build.MOAT_POLY
    check("build.py knows the moat ring", bool(poly), "MOAT_POLY is empty")
    recs = {}
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if f.exists():
            recs[prov] = json.loads(f.read_text())
    for case in CASES:
        rows = [r for r in recs.get(case["province"], [])
                if case["cat"] in (r.get("cat") or [])
                and case["sub"] in (r.get("sub") or [])]
        n_shelf = len(rows)
        if case.get("area") == "old-city" and poly:
            rows = [r for r in rows if r.get("lat") and r.get("lng")
                    and inside(poly, r["lat"], r["lng"])]
        n_area = len(rows)
        if case.get("open_past"):
            rows = [r for r in rows if open_past(r.get("hours"), case["open_past"])]
        names = [r.get("name") or r["id"] for r in rows]
        check(f'"{case["q"]}" → ≥ {case["min"]} record(s)', len(rows) >= case["min"],
              f"shelf {n_shelf}, in area {n_area}, open past {case.get('open_past')}: {len(rows)}")
        for nm in names:
            print(f"         · {nm}")

    print()
    if failures:
        print(f"{len(failures)} failure(s): {failures}")
        return 1
    print("all answer-shaped checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
