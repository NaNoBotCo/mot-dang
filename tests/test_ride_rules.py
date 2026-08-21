#!/usr/bin/env python3
"""The standing directional rules for a ride, tested against real pins.

The interesting cases are the two that nearly collide. The moat's own southwest
corner and Suan Prung sit eleven metres apart in distance from the moat centre,
on nearly the same bearing, and one of them is the lap while the other is the
thing the rule exists for. Any version of these rules that separates them by
radius alone is wrong, and the test below is what says so.

Everything here uses the catalogue's own coordinates. A rule tested against
typed-in geometry proves only that the typing was consistent.

Run: python3 tests/test_ride_rules.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build          # noqa: E402
import ride_rules     # noqa: E402

FAILED = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def gate(rules, en):
    for c in rules.crossings:
        if c["en"] == en:
            return (c["lat"], c["lng"])
    return None


def main():
    rules = ride_rules.Rules.load()
    if rules is None:
        print("no moat geometry on disk — cannot test")
        return 1

    print("geometry comes from the catalogue")
    ctr = (sum(p[0] for p in build.MOAT_POLY) / 4.0,
           sum(p[1] for p in build.MOAT_POLY) / 4.0)
    check("centre is the centroid of build.MOAT_POLY",
          abs(rules.centre[0] - ctr[0]) < 1e-9 and abs(rules.centre[1] - ctr[1]) < 1e-9,
          f"{rules.centre[0]:.6f}, {rules.centre[1]:.6f}")
    check("all nine crossings resolved", len(rules.crossings) == 9,
          f"{len(rules.crossings)} found")
    check("every crossing carries both names",
          all(c["th"] and c["en"] for c in rules.crossings))

    print("\nwhich gates the prose allows, derived not typed")
    lap = [c["en"] for c in rules.lap_clockwise()]
    off = [c["en"] for c in rules.gates(ok=False)]
    check("lap uses Chang Phueak, Thapae, Suan Dok",
          lap == ["Chang Phueak Gate", "Thapae Gate", "Suan Dok Gate"], " → ".join(lap))
    check("Saen Pung is off the route", "Saen Pung Gate" in off)
    check("Chiang Mai Gate is off the route", "Chiang Mai Gate" in off)
    check("lap gates come round clockwise",
          [c["bearing"] for c in rules.lap_clockwise()]
          == sorted(c["bearing"] for c in rules.lap_clockwise()),
          str([c["bearing"] for c in rules.lap_clockwise()]))

    print("\nthe two that nearly collide")
    sw_corner = tuple(rules.poly[3])
    suan_prung = (18.7807397, 98.9791533)
    d_corner = ride_rules.hav(rules.centre, sw_corner)
    d_prung = ride_rules.hav(rules.centre, suan_prung)
    check("both sit in the southwest arc",
          rules.in_southwest(sw_corner) and rules.in_southwest(suan_prung),
          f"corner {ride_rules.bearing(rules.centre, sw_corner):.1f}°, "
          f"Suan Prung {ride_rules.bearing(rules.centre, suan_prung):.1f}°")
    check("no radius separates them", abs(d_corner - d_prung) < 40.0,
          f"{d_corner:.1f} m vs {d_prung:.1f} m — {abs(d_corner - d_prung):.1f} m apart")
    check("the ring corridor does separate them",
          rules.on_moat_ring(sw_corner) and not rules.on_moat_ring(suan_prung),
          f"corner {rules.ring_offset(sw_corner):.1f} m, "
          f"Suan Prung {rules.ring_offset(suan_prung):.1f} m off the ring")
    check("Suan Prung fails as a stop",
          not rules.check_ride(stops=[suan_prung])["ok"])

    print("\na clockwise lap of the ring is accepted")
    ring_lap = rules.poly + [rules.poly[0]]
    rep = rules.check_ride(line=ring_lap)
    check("ring lap passes", rep["ok"],
          rep["first_finding"]["why_en"] if rep["first_finding"] else "")
    check("ring lap raises no transit notice",
          not any(f["rule"] == "transit" for f in rep["findings"]))

    print("\nthe same lap ridden backwards is refused")
    rep = rules.check_ride(line=list(reversed(ring_lap)))
    check("anticlockwise lap fails", not rep["ok"])
    check("and says why", any(f["rule"] == "turning" for f in rep["findings"]),
          rep["first_finding"]["why_en"] if rep["first_finding"] else "")

    print("\ncrossing at the wrong gate is refused — and a near miss is not")
    sp = gate(rules, "Saen Pung Gate")
    # A crossing is a change of side, not proximity. Riding the ring passes
    # within metres of the south gates without going through either, and
    # calling that a crossing would make her standing lap unplannable.
    # Far enough either side to clear the ring band. RING_BAND_M treats
    # anything within 40 m of the ring as on it rather than on a side, which is
    # what stops the inner moat road reading as a crossing every time it curves
    # over the chord line.
    inside = (sp[0] + 0.0006, sp[1] + 0.0006)
    outside = (sp[0] - 0.0006, sp[1] - 0.0006)
    check("the test pair really does straddle the moat",
          rules.inside_moat(inside) and not rules.inside_moat(outside))
    check("and both ends clear the ring band",
          rules.ring_offset(inside) > ride_rules.RING_BAND_M
          and rules.ring_offset(outside) > ride_rules.RING_BAND_M,
          f"{rules.ring_offset(inside):.0f} m in, {rules.ring_offset(outside):.0f} m out")
    rep = rules.check_ride(line=[inside, outside])
    check("a line through Saen Pung fails", not rep["ok"])
    check("the finding names the gate",
          any(f.get("gate_en") == "Saen Pung Gate" for f in rep["findings"]))
    along = [inside, (sp[0] + 0.0007, sp[1] + 0.0007), (sp[0] + 0.0008, sp[1] + 0.0008)]
    check("but riding past it on the same side does not",
          not any(f["rule"] == "gate" for f in rules.check_line(along)),
          "proximity alone is not a crossing")
    # The cost of the band, stated rather than left to be discovered: a move
    # that begins or ends inside it is not yet a crossing. A real route carries
    # on past the ring and registers a moment later; a route that stops within
    # 40 m of the water does not register at all.
    near = [(sp[0] + 0.0002, sp[1] + 0.0002), (sp[0] - 0.0002, sp[1] - 0.0002)]
    check("the band's cost is a short blind spot at the water's edge",
          len(rules.crossings_of(near)) == 0,
          "a hop that starts and ends inside the band is not yet a crossing")

    print("\ninside and outside are the right way round")
    check("the moat centre is inside", rules.inside_moat(rules.centre))
    check("Doi Kham is outside", not rules.inside_moat((18.7592698, 98.9191573)))
    check("Wat Chiang Yuen is outside the north wall",
          not rules.inside_moat((18.7963246, 98.9887797)))

    print("\nthe clockwise lap her rules prescribe is plannable")
    lap_gates = [(c["lat"], c["lng"]) for c in rules.crossings if c["kind"] == "corner"]
    lap = lap_gates + [lap_gates[0]]
    rep = rules.check_ride(line=lap)
    check("a lap round the four corners is accepted", rep["ok"],
          rep["first_finding"]["why_en"] if rep["first_finding"] else "")

    print("\ngoing out southwest is refused")
    doi_kham = (18.7592698, 98.9191573)
    check("Doi Kham fails as a stop", not rules.check_ride(stops=[doi_kham])["ok"])
    rep = rules.check_ride(line=[(18.7884, 98.9860), (18.7700, 98.9500), doi_kham])
    check("a line out to Doi Kham raises the transit notice",
          any(f["rule"] == "transit" for f in rep["findings"]))

    print("\ngoing somewhere auspicious is accepted")
    chiang_yuen = (18.7963246, 98.9887797)
    rep = rules.check_ride(stops=[chiang_yuen],
                           line=[gate(rules, "Chang Phueak Gate"), chiang_yuen])
    check("Wat Chiang Yuen out through Chang Phueak passes", rep["ok"],
          rep["first_finding"]["why_en"] if rep["first_finding"] else "")

    print("\nthe range limit is recorded, not glossed over")
    doc = rules.as_document()
    check("the emitted record states the graph's reach",
          "road_graph.json" in doc["range"]["en"])
    graph_area = None
    gp = ROOT / "data" / "road_graph.json"
    if gp.exists():
        import json
        graph_area = json.loads(gp.read_text())["area"]
    if graph_area:
        outside = not (graph_area["w"] < doi_kham[1] < graph_area["e"])
        check("Doi Kham really is outside the road graph", outside,
              f"lng {doi_kham[1]} vs w {graph_area['w']}")

    print("\nthe unenforced leads stay unenforced")
    check("no corridor claims a source",
          all(c["source"] is None for c in doc["unverified"]["corridors"]))

    print()
    if FAILED:
        print(f"{len(FAILED)} failed: " + "; ".join(FAILED))
        return 1
    print("all ride rules ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
