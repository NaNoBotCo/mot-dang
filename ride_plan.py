#!/usr/bin/env python3
"""Plan a ride that obeys the standing rules, or refuse and say which rule.

WHY THIS EXISTS
---------------
`ride_rules.py` can test a route. `importers/routing.py` can find one. This is
the piece between them: it routes a ride on the offline graph in `ride` mode,
tests the result against the rules, and will not hand back a route that breaks
one. A planner that returned a broken route with a warning attached would be
worse than no planner, because the warning is read once and the route is
followed for two hours.

WHAT IT PRODUCES
----------------
A plan carries three things a dash view needs and cannot work out for itself:

  * **the line** — the road actually travelled, from `Graph.route`, end pieces
    cut in rather than left to a straight stub.
  * **the cues** — where the road you are on changes name, in both languages,
    with the turn worked out from the bearing either side of the junction. The
    names come from `data/streets.json`, which is the catalogue's own street
    tier and already carries Thai and English for all 977 of them.
  * **the verdict** — the ride rules, applied. `ok` false means refused.

WHAT IT DOES NOT DO
-------------------
It does not search the catalogue. `--place` is a plain substring match against
the built index and is deliberately NOT the site's forgiving search, which
lives in build.py and has its own tests; a second implementation of that would
be a second thing to keep right. Give it coordinates when you know them.

It does not re-route. A ride is planned before it is ridden, which is also what
the graph supports: `data/road_graph.json` covers the city core only — about
18.757–18.825 N, 98.953–99.017 E — so a stop outside that box gets no route at
all, and says so rather than routing to the edge of the box and stopping.

USE
---
    python3 ride_plan.py --stop 18.7963,98.9888 --stop 18.7878,98.9933
    python3 ride_plan.py --place "เชียงยืน" --place "ท่าแพ" --name morning-loop
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import ride_rules  # noqa: E402
import routing     # noqa: E402

# How near a named street a point has to be before the cue claims that name.
# The street tier uses 30 m to bind a PLACE to a road; a rider is on the road
# itself, so this is tighter — a wrong road name in a turn cue is worse than
# no name, because it is followed.
NAME_CAP_M = 22.0

# Below this the road is the same road bending, not a turn.
STRAIGHT_DEG = 25.0
UTURN_DEG = 150.0

TURN_TH = {"left": "เลี้ยวซ้าย", "right": "เลี้ยวขวา",
           "straight": "ตรงไป", "uturn": "กลับรถ"}
TURN_EN = {"left": "left", "right": "right",
           "straight": "straight on", "uturn": "turn back"}


def turn_of(delta):
    if abs(delta) >= UTURN_DEG:
        return "uturn"
    if abs(delta) < STRAIGHT_DEG:
        return "straight"
    return "right" if delta > 0 else "left"


class Streets:
    """Named streets, indexed for a nearest-name lookup along a line."""

    CELL = 0.005

    def __init__(self, streets):
        self.parts = []
        self.grid = {}
        for s in streets:
            name_th, name_en = s.get("name"), s.get("nameEn")
            if not (name_th or name_en):
                continue
            for line in (s.get("geom") or []):
                if len(line) < 2:
                    continue
                idx = len(self.parts)
                self.parts.append((line, name_th, name_en, s.get("slug")))
                for k in range(len(line) - 1):
                    a, b = line[k], line[k + 1]
                    for cy in range(int(min(a[0], b[0]) / self.CELL),
                                    int(max(a[0], b[0]) / self.CELL) + 1):
                        for cx in range(int(min(a[1], b[1]) / self.CELL),
                                        int(max(a[1], b[1]) / self.CELL) + 1):
                            self.grid.setdefault((cy, cx), []).append((idx, k))

    @classmethod
    def load(cls, path=None):
        p = Path(path) if path else (ROOT / "data" / "streets.json")
        if not p.exists():
            return None
        return cls(json.loads(p.read_text())["streets"])

    def nearest(self, p, cap_m=NAME_CAP_M):
        """The named street a point is on, or None when nothing is near enough."""
        best = None
        cy0, cx0 = int(p[0] / self.CELL), int(p[1] / self.CELL)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for (i, k) in self.grid.get((cy0 + dy, cx0 + dx), ()):
                    line = self.parts[i][0]
                    d = ride_rules._dist_to_segment_m(p, line[k], line[k + 1])
                    if best is None or d < best[0]:
                        best = (d, i)
        if best is None or best[0] > cap_m:
            return None
        _, name_th, name_en, slug = self.parts[best[1]]
        return {"th": name_th, "en": name_en, "slug": slug,
                "off_m": round(best[0], 1)}


def cues_for(line, streets):
    """Where the road changes name, which way you turn, and how far in.

    A cue is emitted only where the NAME changes, not at every junction: a
    rider on one road through six crossroads wants one instruction, not six.
    """
    if streets is None or len(line) < 2:
        return []
    run = 0.0
    marks = []
    for i, p in enumerate(line):
        if i:
            run += ride_rules.hav(line[i - 1], p)
        got = streets.nearest(p)
        marks.append((run, got["th"] if got else None,
                      got["en"] if got else None, got["slug"] if got else None))

    cues = []
    last_slug = None
    for i, (run, th, en, slug) in enumerate(marks):
        if slug is None or slug == last_slug:
            continue
        if last_slug is None:
            turn = "straight"
            delta = 0.0
        else:
            back = max(0, i - 3)
            fwd = min(len(line) - 1, i + 3)
            if back == i or fwd == i:
                turn, delta = "straight", 0.0
            else:
                b1 = ride_rules.bearing(line[back], line[i])
                b2 = ride_rules.bearing(line[i], line[fwd])
                delta = (b2 - b1 + 540.0) % 360.0 - 180.0
                turn = turn_of(delta)
        cues.append({
            "at_m": round(run, 1),
            "point": [round(line[i][0], 6), round(line[i][1], 6)],
            "turn": turn, "delta_deg": round(delta, 1),
            "street_th": th, "street_en": en, "street_slug": slug,
            "say_th": f"{TURN_TH[turn]} เข้า{th}" if th else TURN_TH[turn],
            "say_en": (f"{TURN_EN[turn]} onto {en}" if en
                       else TURN_EN[turn]),
        })
        last_slug = slug
    return cues


def plan(stops, mode="ride", graph=None, rules=None, streets=None):
    """Route through the stops in order and test the result.

    Returns a plan whose `ok` is false when a rule was broken or a leg could
    not be routed. A refused plan still carries everything worked out so far,
    because "no" without the reason sends a rider back to guessing.
    """
    graph = graph or routing.Graph.load()
    rules = rules or ride_rules.Rules.load()
    if graph is None or rules is None:
        return {"ok": False, "error": "no road graph or no moat geometry on disk"}
    if len(stops) < 2:
        return {"ok": False, "error": "a ride needs at least two stops"}
    if streets is None:
        streets = Streets.load()

    outside = [i for i, s in enumerate(stops) if not graph.contains((s[0], s[1]))]
    if outside:
        return {"ok": False,
                "error": "stop outside the road graph",
                "stops_outside": outside,
                "why_th": "จุดหยุดอยู่นอกขอบเขตกราฟถนน",
                "why_en": ("data/road_graph.json covers the city core only, so "
                           "this stop cannot be routed at all — better than a "
                           "route that stops at the edge of the box"),
                "graph_area": graph.area}

    legs, line, total = [], [], 0.0
    for i in range(len(stops) - 1):
        a, b = (stops[i][0], stops[i][1]), (stops[i + 1][0], stops[i + 1][1])
        r = graph.route(a, b, mode)
        if r is None:
            return {"ok": False, "error": "no route for a leg",
                    "leg": i, "from": list(a), "to": list(b),
                    "why_en": "no way through for this mode — oneway can do this"}
        legs.append({"from": list(a), "to": list(b), "m": round(r["m"], 1),
                     "points": len(r["path"]), "same_edge": r["same_edge"]})
        total += r["m"]
        graph._join(line, r["path"])

    report = rules.check_ride(stops=stops, line=line)
    return {
        "ok": bool(report["ok"]),
        "mode": mode,
        "metres": round(total, 1),
        "km": round(total / 1000.0, 2),
        "stops": [[s[0], s[1]] for s in stops],
        "legs": legs,
        "line": [[round(p[0], 6), round(p[1], 6)] for p in line],
        "cues": cues_for(line, streets),
        "rules": report,
        "named_from": "data/streets.json" if streets else None,
    }


def ring_corridor(graph, rules, corridor_m=70.0):
    """Which graph edges count as "round the moat".

    An edge is in if EVERY point of it is within the corridor, not merely its
    midpoint. Testing the middle alone lets in a long road that happens to
    cross the ring on its way somewhere else, and one of those is all it takes
    for the search to find a diagonal again.
    """
    keep = set()
    for i, pts in enumerate(graph.geom):
        if all(rules.ring_offset(p) <= corridor_m for p in pts):
            keep.add(i)
    return keep


# A lap that covers less of the circle than this, or loses more than this share
# of its hops, did not go round — it fragmented, and reporting its distance as
# a lap distance would be reporting a number for a ride nobody can take.
LAP_MIN_TURN_DEG = 300.0
LAP_MAX_SKIP_SHARE = 0.20


def _lap_once(rules, graph, streets, allow, spacing_m, start, mode, reverse):
    way = rules.ring_waypoints(spacing_m=spacing_m, start=start)
    if reverse:
        way = [way[0]] + way[1:][::-1]
    way.append(way[0])   # close the lap

    line, total, skipped = [], 0.0, 0
    for i in range(len(way) - 1):
        r = graph.route(way[i], way[i + 1], mode, allow=allow)
        if r is None:
            # One unreachable hop is not fatal — the next waypoint is a little
            # further round and the corridor is narrow, so stepping over a gap
            # costs a little accuracy and keeps the ring. Counted and reported,
            # never hidden, and too many of them fails the lap outright.
            skipped += 1
            continue
        total += r["m"]
        graph._join(line, r["path"])

    hops = len(way) - 1
    if not line:
        return None
    _, turn = rules.clockwise(line)
    complete = (abs(turn) >= LAP_MIN_TURN_DEG
                and skipped <= hops * LAP_MAX_SKIP_SHARE)
    return {"line": line, "metres": total, "hops": hops, "skipped": skipped,
            "turn_deg": turn, "complete": complete,
            "crossings": len(rules.crossings_of(line)),
            "cues": cues_for(line, streets)}


def plan_lap(rules=None, graph=None, streets=None, spacing_m=140.0,
             corridor_m=60.0, start=None, mode="ride", direction="clockwise"):
    """A lap of the moat that stays on the ring instead of cutting the middle.

    HOW THE SHAPE IS HELD. Two things together, and neither is enough alone.
    Waypoints every `spacing_m` round the ring mean no diagonal between
    neighbours is shorter than the ring itself. The corridor means the search
    cannot take one even if it were. Given only the four แจ่ง corners the router
    did exactly what it was asked and returned 8.86 km across a 5.98 km
    perimeter, weaving through the old city — that is the failure this fixes.

    WHAT THE ROAD SAYS ABOUT เวียนขวา. Asked for clockwise, the graph cannot
    deliver it: 28 of 40 hops have no legal route and the line manages 232° of
    the circle. Anticlockwise comes back at 6.07 km against that 5.98 km
    perimeter, a complete circuit, and no water crossed. The one-way system
    round the moat runs the other way from the rule.

    So `direction` defaults to clockwise, which is the rule, and a lap that
    cannot be ridden is REFUSED rather than quietly reversed — with the
    anticlockwise lap that does work reported beside it as `alternative`, so
    the choice is visible and hers. Silently substituting the opposite
    direction would have her ride เวียนซ้าย believing she had asked for the
    other thing.

    The ring waypoints are shape, never stops: the ring necessarily passes
    through the southwest and the quarter rule is strict about stops. The only
    stop is where the lap begins and ends.
    """
    graph = graph or routing.Graph.load()
    rules = rules or ride_rules.Rules.load()
    if graph is None or rules is None:
        return {"ok": False, "error": "no road graph or no moat geometry on disk"}
    if streets is None:
        streets = Streets.load()

    if start is None:
        gate = [c for c in rules.gates(ok=True) if c["quadrant"] == "N"]
        start = (gate[0]["lat"], gate[0]["lng"]) if gate else tuple(rules.poly[0])

    keep = ring_corridor(graph, rules, corridor_m)
    if len(keep) < 40:
        return {"ok": False,
                "error": "the ring corridor holds almost no road",
                "corridor_m": corridor_m, "edges": len(keep),
                "why_en": "widen corridor_m, or the graph does not cover the moat"}
    allow = keep.__contains__

    want_ccw = direction == "anticlockwise"
    got = _lap_once(rules, graph, streets, allow, spacing_m, start, mode, want_ccw)
    other = _lap_once(rules, graph, streets, allow, spacing_m, start, mode,
                      not want_ccw)

    perimeter_km = round(sum(
        ride_rules.hav(rules.poly[i], rules.poly[(i + 1) % len(rules.poly)])
        for i in range(len(rules.poly))) / 1000.0, 2)

    def summary(d, label):
        if d is None:
            return None
        return {"direction": label, "km": round(d["metres"] / 1000.0, 2),
                "complete": d["complete"], "turn_deg": d["turn_deg"],
                "hops_skipped": d["skipped"], "hops": d["hops"],
                "moat_crossings": d["crossings"]}

    other_label = "clockwise" if want_ccw else "anticlockwise"

    if got is None or not got["complete"]:
        out = {
            "ok": False, "rideable": False,
            "kind": "lap", "mode": mode, "direction": direction,
            "error": f"a {direction} lap of the ring is not rideable",
            "why_th": ("ถนนรอบคูเมืองเป็นทางเดินรถทางเดียวสวนทางกับกฎเวียนขวา"),
            "why_en": ("the one-way system round the moat runs against this "
                       "direction, so the lap fragments rather than going "
                       "round — it is refused instead of being quietly "
                       "reversed"),
            "perimeter_km": perimeter_km,
            "attempt": summary(got, direction),
            "alternative": summary(other, other_label),
            "corridor_m": corridor_m, "corridor_edges": len(keep),
        }
        return out

    report = rules.check_ride(stops=[start], line=got["line"], lap=True)
    # `rideable` and `ok` are different questions and both matter here. The
    # anticlockwise lap goes round perfectly well and still breaks เวียนขวา, so
    # collapsing the two would either hide a working route or pretend a rule was
    # kept. Only `ok` gates what can be baked into the app.
    return {
        "ok": bool(report["ok"]),
        "rideable": True,
        "kind": "lap", "mode": mode, "direction": direction,
        "metres": round(got["metres"], 1),
        "km": round(got["metres"] / 1000.0, 2),
        "perimeter_km": perimeter_km,
        "turn_deg": got["turn_deg"],
        "stops": [list(start)],
        "waypoints": got["hops"],
        "hops_skipped": got["skipped"],
        "corridor_m": corridor_m, "corridor_edges": len(keep),
        "moat_crossings": got["crossings"],
        "line": [[round(p[0], 6), round(p[1], 6)] for p in got["line"]],
        "cues": got["cues"],
        "rules": report,
        "alternative": summary(other, other_label),
        "named_from": "data/streets.json" if streets else None,
    }


def find_place(term, limit=6):
    """A plain substring match, not the site's forgiving search."""
    for cand in ("docs/data/places.json", "data/places.json"):
        p = ROOT / cand
        if p.exists():
            break
    else:
        return []
    recs = json.loads(p.read_text())
    if isinstance(recs, dict):
        recs = recs.get("places") or recs.get("items") or []
    t = term.lower()
    out = []
    for r in recs:
        lat, lng = r.get("lat"), r.get("lng") or r.get("lon")
        if lat is None or lng is None:
            continue
        blob = " ".join(str(r.get(k, "")) for k in ("name", "nameTh", "nameEn"))
        if t in blob.lower():
            out.append({"name": blob.strip()[:70], "lat": lat, "lng": lng})
            if len(out) >= limit:
                break
    return out


def main():
    ap = argparse.ArgumentParser(description="Plan a ride that obeys the standing rules.")
    ap.add_argument("--stop", action="append", default=[], metavar="LAT,LNG")
    ap.add_argument("--place", action="append", default=[], metavar="TEXT")
    ap.add_argument("--lap", action="store_true",
                    help="a lap of the moat rather than a journey")
    ap.add_argument("--direction", default="clockwise",
                    choices=("clockwise", "anticlockwise"))
    ap.add_argument("--mode", default="ride", choices=("ride", "foot"))
    ap.add_argument("--name", default="ride")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.lap:
        p = plan_lap(mode=args.mode, direction=args.direction)
        if not p.get("rideable"):
            print(f"refused: {p.get('error')}")
            if p.get("why_en"):
                print("  " + p["why_en"])
            if p.get("attempt"):
                a = p["attempt"]
                print(f"  attempted {a['direction']}: {a['turn_deg']}° of the "
                      f"circle, {a['hops_skipped']}/{a['hops']} hops lost")
            if p.get("alternative") and p["alternative"]["complete"]:
                b = p["alternative"]
                print(f"  what does work: {b['direction']}, {b['km']} km — "
                      f"ask for it with --direction {b['direction']}")
            return 1
        print(f"{p['km']} km {p['direction']} lap "
              f"(perimeter {p['perimeter_km']} km), turn {p['turn_deg']}°, "
              f"{p['moat_crossings']} water crossings, "
              f"{p['hops_skipped']}/{p['waypoints']} hops skipped, "
              f"{len(p['cues'])} cues")
        if not p["ok"]:
            f = p["rules"]["first_finding"]
            print("\nRIDEABLE BUT AGAINST A STANDING RULE — "
                  + (f["why_en"] if f else ""))
            print("  It is not written out as accepted. To use it anyway, bake "
                  "it with:\n    python3 dash/build_data.py --ride NAME "
                  "--waive turning")
        out = Path(args.out) if args.out else (ROOT / "data" / "rides"
                                              / f"{args.name}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n")
        print(f"\nwrote {out.relative_to(ROOT)}")
        return 0

    stops = []
    for s in args.stop:
        lat, lng = (float(x) for x in s.split(","))
        stops.append((lat, lng))
    for term in args.place:
        hits = find_place(term)
        if not hits:
            print(f"no place matched {term!r}")
            return 1
        print(f"{term!r} → {hits[0]['name']}")
        stops.append((hits[0]["lat"], hits[0]["lng"]))

    p = plan(stops, mode=args.mode)
    if p.get("error"):
        print("refused:", p["error"])
        if p.get("why_en"):
            print("  " + p["why_en"])
        return 1

    print(f"{p['km']} km, {len(p['legs'])} leg(s), {len(p['line'])} points, "
          f"{len(p['cues'])} cue(s)")
    for c in p["cues"][:12]:
        print(f"  {c['at_m']:8.0f} m  {c['say_en']}")
    if len(p["cues"]) > 12:
        print(f"  … {len(p['cues']) - 12} more")

    if not p["ok"]:
        f = p["rules"]["first_finding"]
        print("\nREFUSED — " + (f["why_en"] if f else "a rule was broken"))
        return 1

    notices = [f for f in p["rules"]["findings"] if f.get("notice")]
    for n in notices:
        print("  notice: " + n["why_en"])

    out = Path(args.out) if args.out else (ROOT / "data" / "rides" / f"{args.name}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n")
    print(f"\naccepted — wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
