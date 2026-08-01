#!/usr/bin/env python3
"""The moat ring, which is now a landmark and no longer a distance rule.

An earlier version of the planner special-cased the moat: it tested each leg
against this ring and priced a crossing round the nearest gate. That guessed
878 m for a leg the real road network puts at 571 m on foot, so the special
case is gone and routing does the work — see tests/test_routing.py, which is
where the interesting behaviour lives now.

What survives is the drawing. The ring is the square everybody in Chiang Mai
navigates by, so plan.html still sketches it for orientation, and it still has
to be the actual moat rather than a hand-typed box 372 m out of place.

Run: python3 tests/test_moat_geometry.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

FAILED = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def km(a, b):
    R = 6371
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def inside(poly, p):
    hit = False
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if (a[0] > p[0]) != (b[0] > p[0]):
            x = a[1] + (p[0] - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
            if p[1] < x:
                hit = not hit
    return hit


print("moat ring (drawn for orientation)")
poly = build.MOAT_POLY
check("ring derived from the catalogue's four แจ่ง", bool(poly) and len(poly) == 4,
      f"{len(poly) if poly else 0} points")
if not poly:
    sys.exit(1)

side = km(poly[0], poly[1])
check("north side between 1.0 and 2.0 km", 1.0 < side < 2.0, f"{side:.2f} km")

# The hand-typed square this replaced had its west edge 372 m too far west,
# which put Suan Dok Gate outside its own moat.
west = (poly[0][1] + poly[3][1]) / 2
check("west edge is where the corner pins say, not the old literal",
      abs(west - 98.97903) < 0.0005, f"{west:.5f}")

geo_page = (build.DOCS / "plan.html").read_text()
geo = json.loads(geo_page.split('id="plan-geo">')[1].split("</script>")[0])
check("plan.html ships the ring", len(geo.get("poly", [])) == 4)
check("plan.html no longer ships gate crossings as a routing input",
      "crossings" not in geo,
      "routing replaced the special case")

# Inside/outside still has to be right, because the ring being wrong would show
# up as a moat drawn through the wrong buildings.
cm = {r["id"]: r for r in json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())}
for pid, want_in, label in [
    ("cm-osm-node-2466299697", False, "City Nail Chiangmai, west bank"),
    ("cm-osm-node-2649612347", False, "Karinthip Village, east bank"),
    ("cm-osm-node-1619287900", True, "คลินิกทันตกรรมมุขไม้, in the old city"),
    ("cm-osm-node-7295643885", True, "Backstreet Barber Shop, in the old city"),
]:
    r = cm.get(pid)
    if not r:
        check(f"{label} present", False, pid)
        continue
    check(f"{label} reads as {'inside' if want_in else 'outside'}",
          inside(poly, (r["lat"], r["lng"])) is want_in)

print()
if FAILED:
    print(f"{len(FAILED)} failed:")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("all moat ring checks pass")
