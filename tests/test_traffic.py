#!/usr/bin/env python3
"""/traffic.html holds its sum and its sources.

  THE SUM IS THE DOCSTRING'S. forecast() is week × month ÷ year, and minutes
      are 10 × (1 + c/100). Friday 17:00 in the 2025 figures is the week's
      worst hour; if a refactor moves that, the page is printing something
      other than what its Sources section says.
  A ROAD CARRIES DOH'S OWN FIGURES. A count, a class-2 motorcycle column
      kept apart, and a grade that is one of DOH's six letters or none.
  THE CELLS ARE ONE SHAPE. The page draws every H3 cell from one template;
      that is only sound while every ring sits within a few metres of it.
  NO EMOJI IN WHAT THE PAGE EMITS. The site's own i-* icons only.

    python3 tests/test_traffic.py
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import traffic_layer as T  # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


p = ROOT / "data" / "traffic.json"
if not p.exists():
    check("data/traffic.json is here", False, "run importers/make_traffic.py")
else:
    doc = json.loads(p.read_text(encoding="utf-8"))
    city = doc["city"]
    c = city["center"]

    print("the sum")
    raw = c["week"][4][17][0]
    got = T.forecast(city, 4, 17, 8)
    want = raw * c["month"][8] / c["year_c"]
    check("congestion = week × month ÷ year", abs(got[0] - want) < 1e-9, (got[0], want))
    check("minutes = 10 × (1 + c/100)", abs(got[1] - 10 * (1 + want / 100)) < 1e-9)
    worst = max(((d, h) for d in range(7) for h in range(24)), key=lambda x: c["week"][x[0]][x[1]][0])
    check("the worst weekday hour is still Friday 17:00", worst == (4, 17), worst)
    check("every week cell is filled",
          all(len(row) == 24 and all(len(x) == 3 for x in row) for row in c["week"])
          and len(c["week"]) == 7)

    print("the roads")
    roads = doc["roads"]
    check("the DOH layer is not hollow", len(roads) >= 100, len(roads))
    check("every road carries a count and a motorcycle column",
          all(r["motor"] > 0 and isinstance(r["moto"], int) for r in roads))
    check("grades are DOH's six letters or none",
          all(r["grade"] in (None, "A", "B", "C", "D", "E", "F") for r in roads))
    check("both provinces are present",
          any(r["district"].startswith("ขท.เชียงใหม่") for r in roads)
          and any(r["district"].startswith("ขท.เชียงราย") for r in roads))
    m1141 = [r for r in roads if r["route"] == "1141"]
    check("route 1141 reads DOH's 2568 count (121,403)",
          any(r["motor"] == 121403 and r["moto"] == 26366 for r in m1141),
          [(r["motor"], r["moto"]) for r in m1141])

    print("the cells")
    hx = city["hex"]
    check("the TomTom cells are not hollow", len(hx) >= 1000, len(hx))
    t = hx[0]["ring"]
    cx0, cy0 = sum(q[0] for q in t) / 6, sum(q[1] for q in t) / 6
    worst_m = 0
    for h in hx:
        cx, cy = sum(q[0] for q in h["ring"]) / 6, sum(q[1] for q in h["ring"]) / 6
        for a, b in zip(h["ring"], t):
            worst_m = max(worst_m, math.hypot((a[0] - cx - (b[0] - cx0)) * 105000,
                                              (a[1] - cy - (b[1] - cy0)) * 111000))
    check("every cell is within 5 m of the template shape", worst_m < 5, round(worst_m, 1))

    print("what the page emits")
    emoji = re.compile("[\U0001F300-\U0001FAFF☀-⛿✀-➿]")
    check("no emoji in traffic.js", not emoji.search(T.JS), emoji.findall(T.JS)[:5])
    check("no emoji in the layer's markup",
          not emoji.search(Path(T.__file__).read_text(encoding="utf-8")))
    check("the JS placeholders are the ones emit() fills",
          T.JS.count("__GRADES__") == 1 and T.JS.count("__BANDS__") == 1)

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("\nall traffic checks pass")
