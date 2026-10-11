#!/usr/bin/env python3
"""road_router.py answers road distance, and it is never shorter than the crow.

    python3 tests/test_road_router.py

The invariants a router must keep, checked against the real graph:
  1. road distance >= straight-line, always (a road cannot beat a line)
  2. a point outside the graph's area returns None (the crow is the caller's job)
  3. the moat U-turn is present: somewhere a scooter's road is far longer than a
     walker's, because oneway binds one and not the other
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from road_router import RoadRouter, _hav_m  # noqa: E402

FAIL = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


def rand_point(area, rng):
    return (rng.uniform(area["s"], area["n"]), rng.uniform(area["w"], area["e"]))


def main():
    r = RoadRouter.load()
    print(f"graph: {len(r.nodes):,} nodes, {len(r._raw_edges):,} edges, "
          f"area {r.area['s']:.3f},{r.area['w']:.3f} → {r.area['n']:.3f},{r.area['e']:.3f}")

    print("1 · road distance is never shorter than the crow")
    rng = random.Random(18790)
    tested = 0
    worst = 0.0
    for _ in range(400):
        a = rand_point(r.area, rng)
        b = rand_point(r.area, rng)
        d = r.route_m(a, b, mode="ride")
        if d is None:
            continue
        crow = _hav_m(a[0], a[1], b[0], b[1])
        tested += 1
        # a metre of floating slack; the snap legs make road >= crow exact
        if d + 1.0 < crow:
            worst = max(worst, crow - d)
            FAIL.append("road shorter than crow")
    check(f"road >= crow on {tested} routable pairs", not worst, f"worst deficit {worst:.1f} m")

    print("2 · a point outside the area is not routed")
    outside = (13.7563, 100.5018)                       # Bangkok
    inside = ((r.area["s"] + r.area["n"]) / 2, (r.area["w"] + r.area["e"]) / 2)
    check("outside → None", r.route_m(inside, outside, mode="ride") is None)

    print("3 · the moat U-turn: a scooter's road can dwarf a walker's")
    rng = random.Random(7)
    best = None                                          # (ratio, foot, ride, crow)
    for _ in range(600):
        a = rand_point(r.area, rng)
        b = rand_point(r.area, rng)
        f = r.route_m(a, b, mode="foot")
        rd = r.route_m(a, b, mode="ride")
        if not f or not rd or f < 40:
            continue
        ratio = rd / f
        if best is None or ratio > best[0]:
            best = (ratio, f, rd, _hav_m(a[0], a[1], b[0], b[1]))
    if best:
        print(f"        worst case: foot {best[1]:.0f} m · ride {best[2]:.0f} m · "
              f"crow {best[3]:.0f} m · ride/foot {best[0]:.1f}×")
    check("ride can exceed foot by a wide margin (oneway)", bool(best) and best[0] > 2.0,
          "no pair found where ride >> foot" if not (best and best[0] > 2.0) else "")

    print("4 · a real hop routes (two graph nodes ~1 km apart by crow)")
    # Nodes, not hand-typed coords: a landmark point can sit >250 m from any
    # junction and fail to snap, which is a coordinate accident, not a routing
    # one. Take node 0 and the node closest to 1 km from it, and route between
    # them — proving the walk connects a genuine pair.
    a_la, a_ln = r.nodes[0]
    tgt = min(range(1, len(r.nodes)),
              key=lambda i: abs(_hav_m(a_la, a_ln, r.nodes[i][0], r.nodes[i][1]) - 1000))
    b_la, b_ln = r.nodes[tgt]
    crow = _hav_m(a_la, a_ln, b_la, b_ln)
    d = r.route_m((a_la, a_ln), (b_la, b_ln), mode="ride")
    check("routes and road >= crow", d is not None and d >= crow - 1.0,
          f"road {d:.0f} m vs crow {crow:.0f} m" if d else "None")

    print()
    if FAIL:
        print(f"{len(set(FAIL))} failed:")
        for x in sorted(set(FAIL)):
            print("  -", x)
        return 1
    print("road_router: all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
