#!/usr/bin/env python3
"""The planner: a route that obeys the rules, or a refusal that says which.

`Graph.route` is a THIRD copy of a search that already exists twice, so the
first thing tested here is that it returns the same metres as `Graph.distance`
over real pairs. A line that disagrees with the number printed beside it is the
failure this file exists to catch — the line is what a rider follows and the
number is what they planned around, and they have to describe one journey.

Then the refusals, because a planner is only worth having if it says no. Two of
these are regression guards for real defects found while building it:

  * a point-to-point ride was refused for turning anticlockwise. เวียนขวา is a
    rule about going round something; a ride from one place to another has no
    direction to be wrong about.
  * a ride with a stop in the southwest was refused for the wrong reason,
    because findings were ordered by where they fired rather than by which rule
    matters. The rider was told about the winding and not about the stop.

Run: python3 tests/test_ride_plan.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import ride_plan    # noqa: E402
import ride_rules   # noqa: E402
import routing      # noqa: E402

FAILED = []

CHIANG_YUEN = (18.7963246, 98.9887797)
THAPAE = (18.7877625, 98.9932697)
SUAN_PRUNG = (18.7807397, 98.9791533)
DOI_KHAM = (18.7592698, 98.9191573)


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def main():
    graph = routing.Graph.load()
    rules = ride_rules.Rules.load()
    if graph is None or rules is None:
        print("no road graph or no moat geometry on disk — cannot test")
        return 1
    streets = ride_plan.Streets.load()

    print("the line and the number describe one journey")
    pairs = [(CHIANG_YUEN, THAPAE), (THAPAE, CHIANG_YUEN),
             (CHIANG_YUEN, SUAN_PRUNG), (SUAN_PRUNG, THAPAE)]
    agree = 0
    for mode in ("ride", "foot"):
        for a, b in pairs:
            d = graph.distance(a, b, mode)
            r = graph.route(a, b, mode)
            if d is not None and r is not None and abs(d - r["m"]) < 0.5:
                agree += 1
    check("route() metres match distance() over real pairs", agree == 8,
          f"{agree}/8 agree to under half a metre")

    r = graph.route(CHIANG_YUEN, THAPAE, "ride")
    check("the line starts at the first stop",
          ride_rules.hav(r["path"][0], CHIANG_YUEN) < 60.0,
          f"{ride_rules.hav(r['path'][0], CHIANG_YUEN):.1f} m off")
    check("the line ends at the second stop",
          ride_rules.hav(r["path"][-1], THAPAE) < 60.0,
          f"{ride_rules.hav(r['path'][-1], THAPAE):.1f} m off")
    span = sum(ride_rules.hav(r["path"][i], r["path"][i + 1])
               for i in range(len(r["path"]) - 1))
    check("the drawn line is as long as the journey, not a straight stub",
          abs(span - (r["m"] - sum(r["snap_in_m"]))) < 5.0,
          f"line {span:.1f} m vs journey {r['m'] - sum(r['snap_in_m']):.1f} m")
    check("the line follows a road rather than the crow",
          span > ride_rules.hav(CHIANG_YUEN, THAPAE) * 1.2,
          f"crow {ride_rules.hav(CHIANG_YUEN, THAPAE):.0f} m vs road {span:.0f} m")

    print("\noneway still binds the scooter and not the walker")
    ride = graph.route(CHIANG_YUEN, THAPAE, "ride")
    foot = graph.route(CHIANG_YUEN, THAPAE, "foot")
    check("the scooter's way round is longer", ride["m"] > foot["m"] + 25.0,
          f"ride {ride['m']:.0f} m vs foot {foot['m']:.0f} m")

    print("\na ride that keeps the rules is accepted")
    p = ride_plan.plan([CHIANG_YUEN, THAPAE], graph=graph, rules=rules, streets=streets)
    check("accepted", p["ok"],
          p["rules"]["first_finding"]["why_en"] if not p["ok"] else f"{p['km']} km")
    check("it carries a line", len(p["line"]) > 20, f"{len(p['line'])} points")

    print("\ncues come from the catalogue's own street tier")
    check("there are cues", len(p["cues"]) > 0, f"{len(p['cues'])}")
    check("every cue names a street in both languages",
          all(c["street_th"] and c["street_en"] for c in p["cues"]))
    check("no cue repeats the street before it",
          all(a["street_slug"] != b["street_slug"]
              for a, b in zip(p["cues"], p["cues"][1:])))
    check("cues run forwards along the route",
          [c["at_m"] for c in p["cues"]] == sorted(c["at_m"] for c in p["cues"]))
    check("every turn is one of the four words",
          all(c["turn"] in ("left", "right", "straight", "uturn") for c in p["cues"]))
    check("the spoken form is filled in both languages",
          all(c["say_th"] and c["say_en"] for c in p["cues"]),
          p["cues"][0]["say_en"] if p["cues"] else "")

    print("\na stop in the southwest is refused, and told the right reason")
    p = ride_plan.plan([CHIANG_YUEN, SUAN_PRUNG], graph=graph, rules=rules, streets=streets)
    check("refused", not p["ok"])
    lead = p["rules"]["first_finding"]
    check("the leading finding is the stop, not the winding",
          lead and lead["rule"] == "quarter",
          f"got {lead['rule'] if lead else 'none'} — {lead['why_en'] if lead else ''}")

    print("\nเวียนขวา is only asked of a lap")
    line = [p2 for p2 in graph.route(CHIANG_YUEN, THAPAE, "ride")["path"]]
    check("a point-to-point line is not a lap", not rules.is_lap(line),
          f"ends {ride_rules.hav(line[0], line[-1]):.0f} m from its start")
    check("and so is not tested for turning",
          not any(f["rule"] == "turning" for f in rules.check_line(line)))
    ring = rules.poly + [rules.poly[0]]
    check("a closed ring is a lap", rules.is_lap(ring))
    check("and a backwards one is refused",
          any(f["rule"] == "turning" for f in rules.check_line(list(reversed(ring)))))

    print("\nout of the graph's reach is refused, not fudged")
    p = ride_plan.plan([CHIANG_YUEN, DOI_KHAM], graph=graph, rules=rules, streets=streets)
    check("refused", not p["ok"])
    check("and says it is a range problem",
          p.get("error") == "stop outside the road graph", str(p.get("error")))
    check("naming which stop", p.get("stops_outside") == [1])

    print("\nthe ring band stops a road that hugs the moat reading as crossing it")
    # The inner moat roads sit 13-22 m off the corner-to-corner chords and curve
    # across them repeatedly. Without the band a lap of the ring reported 22
    # water crossings it never made, and a ride along Moon Muang could be
    # refused for crossing at a gate it only rode past.
    ring_line = []
    keep = ride_plan.ring_corridor(graph, rules, 60.0)
    way = rules.ring_waypoints(spacing_m=140.0)
    way = [way[0]] + way[1:][::-1] + [way[0]]
    for i in range(len(way) - 1):
        seg = graph.route(way[i], way[i + 1], "ride", allow=keep.__contains__)
        if seg:
            graph._join(ring_line, seg["path"])
    check("a lap of the ring crosses no water", len(rules.crossings_of(ring_line)) == 0,
          f"{len(rules.crossings_of(ring_line))} crossings")
    check("without the band it would over-count badly",
          len(rules.crossings_of(ring_line, band_m=0.0)) > 5,
          f"{len(rules.crossings_of(ring_line, band_m=0.0))} false crossings at band 0")

    print("\nthe corridor keeps a lap on the ring instead of through the middle")
    p = ride_plan.plan_lap(rules=rules, graph=graph, streets=streets,
                           direction="anticlockwise")
    check("it is rideable", p.get("rideable") is True)
    check("its length is near the perimeter, not half again",
          abs(p["km"] - p["perimeter_km"]) < 0.9,
          f"{p['km']} km vs {p['perimeter_km']} km perimeter")
    check("it goes the whole way round", abs(p["turn_deg"]) >= 300.0,
          f"{p['turn_deg']}°")
    check("it crosses no water", p["moat_crossings"] == 0)
    check("most hops routed", p["hops_skipped"] <= p["waypoints"] * 0.25,
          f"{p['hops_skipped']}/{p['waypoints']} skipped")
    check("but it still reports breaking เวียนขวา", p["ok"] is False,
          "rideable and rule-breaking are different questions")

    print("\nเวียนขวา is refused rather than quietly reversed")
    p = ride_plan.plan_lap(rules=rules, graph=graph, streets=streets,
                           direction="clockwise")
    check("clockwise is refused", p["ok"] is False and p["rideable"] is False)
    check("and named as a direction problem",
          "not rideable" in p.get("error", ""), p.get("error", ""))
    check("the attempt is reported, not hidden",
          p["attempt"]["complete"] is False,
          f"{p['attempt']['turn_deg']}° of the circle, "
          f"{p['attempt']['hops_skipped']}/{p['attempt']['hops']} hops lost")
    check("the working alternative is offered",
          p["alternative"]["complete"] is True
          and p["alternative"]["direction"] == "anticlockwise",
          f"{p['alternative']['km']} km anticlockwise")
    check("no line is returned for a refused lap", "line" not in p,
          "nothing that could be baked by accident")

    print("\nthe planner refuses to guess")
    p = ride_plan.plan([CHIANG_YUEN], graph=graph, rules=rules, streets=streets)
    check("one stop is not a ride", not p["ok"] and "two stops" in p.get("error", ""))

    print()
    if FAILED:
        print(f"{len(FAILED)} failed: " + "; ".join(FAILED))
        return 1
    print("all ride plan checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
