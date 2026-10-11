#!/usr/bin/env python3
"""The counts llms.txt prints, checked against the files they describe.

Run as a script: python3 tests/test_llms_counts.py  (skips on an unbuilt site)

Why: numbers written into llms.txt by hand drift from the data. On 2026-09-25
it said 431 mapped toilets while data/toilets.json held 537, and quoted the
plan demo as 526 m on foot / 762 m by scooter while plan.html, reading
assets/plan-demo.json, said 560 m / 817 m. build.py now interpolates those;
this reads the BUILT file, so a new hand-typed count that drifts is caught
here rather than by a reader.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  — %s" % (detail,)))


def num(s):
    return int(s.replace(",", ""))


def main():
    f = DOCS / "llms.txt"
    if not f.exists():
        print("skip: docs/llms.txt not built")
        return 0
    txt = f.read_text()

    demo = json.loads((ROOT / "assets" / "plan-demo.json").read_text())
    m = re.search(r"one leg is ([\d,]+) m as the crow flies,\s+([\d,]+) m on foot and ([\d,]+) m on a scooter", txt)
    check("plan demo numbers match assets/plan-demo.json",
          m and (num(m[1]), num(m[2]), num(m[3])) == (demo["crowM"], demo["footM"], demo["rideM"]),
          m and m.groups())

    tv = json.loads((DOCS / "data" / "toilets.json").read_text())["verified"]
    m = re.search(r"\(amenity=toilets\)\.\s+([\d,]+) of them", txt)
    check("mapped toilet count matches data/toilets.json", m and num(m[1]) == len(tv),
          (m and m[1], len(tv)))
    priced = sum(1 for r in tv if len(r) > 5 and r[5])
    m = re.search(r"of ([\d,]+) mapped toilets, ([\d,]+)\s+record what they charge", txt)
    check("priced toilet count matches data/toilets.json",
          m and (num(m[1]), num(m[2])) == (len(tv), priced), (m and m.groups(), len(tv), priced))

    k = json.loads((DOCS / "data" / "katha.json").read_text())
    m = re.search(r"These\s+five and ([\d,]+) more passages", txt)
    check("katha 'five and N more' matches data/katha.json", m and num(m[1]) + 5 == k["n"],
          (m and m[1], k["n"]))
    m = re.search(r"katha\.json \(([\d,]+) passages", txt)
    check("katha passage count matches", m and num(m[1]) == k["n"], (m and m[1], k["n"]))

    p = json.loads((DOCS / "data" / "psalms.json").read_text())
    m = re.search(r"in ([\d,]+) windows of two or three verses", txt)
    check("psalm window count matches data/psalms.json", m and num(m[1]) == p["n"], (m and m[1], p["n"]))

    b = DOCS / "data" / "bus_routes.json"
    if b.exists():
        routes = json.loads(b.read_text())["routes"]
        m = re.search(r"([\d,]+) Chiang Mai bus routes", txt)
        check("bus route count matches data/bus_routes.json", m and num(m[1]) == len(routes),
              (m and m[1], len(routes)))

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
