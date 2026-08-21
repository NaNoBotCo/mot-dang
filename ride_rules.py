#!/usr/bin/env python3
"""The standing directional rules for a ride, as geometry instead of memory.

WHY THIS EXISTS
---------------
The rules for a ride out of the old city are written down in prose and applied
by hand: leave through Chang Phueak, lap the moat clockwise with the wall on
your right, close the loop through a north, east or west gate, and keep the
southwest quarter off the route. Prose cannot check a route, and a rider
squinting at a phone at a junction cannot check one either. This module turns
the same rules into predicates, so a planned route is either accepted or told
which rule it broke and where.

WHERE THE GEOMETRY COMES FROM
-----------------------------
Nothing here is typed in. The moat is `build.MOAT_POLY` — the quadrilateral of
the four แจ่ง corners as the catalogue pins them — and the crossings are
`build._moat_crossings()`, the five gates and four corners under the names OSM
carries for them. That matters more than it looks: the hand-typed moat square
those replaced had its west side 372 m out of place, enough to put Suan Dok
Gate on the wrong side of its own moat. A rule tested against bad geometry is
worse than no rule, because it fails while appearing to work.

The centre is the centroid of those four corners, and every direction here is a
bearing from it. Which gates may be used is decided by the quadrant a bearing
falls in, so the permitted set is derived from the catalogue rather than listed
by hand — it comes out as Chang Phueak (N), Thapae (E) and Suan Dok (W), which
is what the prose says, and it would keep saying it if a pin moved.

THE TENSION IN THE RULES, AND HOW IT IS SETTLED
-----------------------------------------------
Read strictly, two rules contradict each other. The moat's own southwest corner
(แจ่งกู่เฮือง) sits at bearing 229° from the centre and Saen Pung Gate at 211°,
both inside the southwest quarter. Completing a clockwise lap from Chiang Mai
Gate round to Suan Dok Gate therefore travels through the quarter, so "lap the
moat" and "keep the southwest off the route" cannot both hold for every metre
ridden.

Trying to settle it with one distance threshold does not work, and the numbers
say so plainly: the moat's southwest corner is 1108 m from the centre and Suan
Prung about 1119 m on nearly the same bearing. Eleven metres apart radially. No
radius tells them apart.

What settles it is reading the prose for what it actually restricts — the gate
you cross at, and where you are going. Riding the ring past its own southwest
corner is the lap. Leaving through Saen Pung, or having somewhere southwest as
a destination, is not. So the rules are applied to two different things:

  * **stops** — every waypoint and the destination. The quarter rule is strict
    here, with no corridor and no exemption. Suan Prung as a destination fails.
  * **the line** — the geometry actually travelled. The gate and turning rules
    apply, plus a softer notice for transit that leaves the ring corridor and
    runs off into the quarter.

That split is why `MOAT_TOL_M` no longer has to be precise. It governs only the
transit notice, and it was measured rather than picked: the crossings a legal
lap must pass in the southwest arc lie 0 m (the corner) and 21.5 m (Saen Pung
Gate) off the corner-to-corner ring, while Suan Prung is 118.1 m off it. Sixty
metres sits clear of both, with the widest offset anywhere on the ring being
Suan Dok Gate at 91.1 m — which is in the west quadrant and constrains nothing
here, and which independently reproduces the ~92 m figure recorded in build.py.

THE RULES
---------
  * **gate** — a crossing happens at a north, east or west gate. Chiang Mai
    Gate is south and Saen Pung southwest; both are off the route.
  * **quarter** — no stop in the southwest quarter, bearing 180°–270°.
  * **turning** — the lap runs clockwise, so bearings accumulate positively.

USE
---
    import ride_rules
    r = ride_rules.Rules.load()
    report = r.check_ride(stops=[(18.7963, 98.9888)], line=lap_points)
    if not report["ok"]:
        print(report["first_finding"]["why_en"])
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# The southwest quarter, as bearings from the moat centre.
SOUTHWEST = (180.0, 270.0)

# Width of the moat-ring transit corridor. Measured, not chosen: the southwest
# crossings a legal lap must pass sit 0 m and 21.5 m off the corner-to-corner
# ring; Suan Prung sits 118.1 m off it. See the module docstring.
MOAT_TOL_M = 60.0

# How near a gate a line has to pass before it counts as crossing there.
GATE_NEAR_M = 60.0

# How wide the "on the ring, neither side" band is. Measured from the street
# tier rather than chosen: the inner moat roads sit 13-22 m off the corner-to-
# corner chords (Bumrung Buri 13.0, Moon Muang 15.7, Sri Poom 21.5) and the
# outer ones 50-62 m (Kotchasarn 50.0, Chang Lo 50.5, Mani Noppharat 61.6).
# Forty metres covers every inner road and reaches no outer one, so following
# the inner ring is on the ring, and swapping to the outer ring is getting
# across the water — which is what it is.
RING_BAND_M = 40.0

# How near its own start a line has to end before it is a lap rather than a
# journey. เวียนขวา is a rule about going ROUND something; a ride from one
# place to another has no direction to be wrong about, and testing it as though
# it did refuses good routes for a reason that does not apply to them.
LAP_CLOSE_M = 150.0

# Which rule leads when several are broken at once. A stop somewhere the ride
# does not go is the substantive breach; the way the line happened to wind is
# the least of it. Sorting these by where they occur instead buries the reason
# a rider actually needs under whichever fired earliest.
RULE_ORDER = {"quarter": 0, "gate": 1, "turning": 2, "transit": 3}

# Quadrant arcs. A gate is named by the one its bearing falls in, so the
# permitted set follows from the catalogue's own pins.
QUADRANTS = (("N", 315.0, 45.0), ("E", 45.0, 135.0),
             ("S", 135.0, 225.0), ("W", 225.0, 315.0))

# The prose says a loop closes through a north, east or west gate.
GATE_QUADRANTS_OK = ("N", "E", "W")

QUADRANT_TH = {"N": "ทิศเหนือ", "E": "ทิศตะวันออก",
               "S": "ทิศใต้", "W": "ทิศตะวันตก"}


def hav(a, b):
    """Metres between two lat/lng pairs."""
    R = 6371000.0
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0]))
         * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def bearing(a, b):
    """Degrees clockwise from north, a to b."""
    dl = math.radians(b[1] - a[1])
    la1, la2 = math.radians(a[0]), math.radians(b[0])
    y = math.sin(dl) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def in_arc(deg, lo, hi):
    """Whether a bearing sits in an arc, wrapping through north when it must."""
    deg %= 360.0
    if lo <= hi:
        return lo <= deg < hi
    return deg >= lo or deg < hi


def quadrant(deg):
    for name, lo, hi in QUADRANTS:
        if in_arc(deg, lo, hi):
            return name
    return "N"


def _dist_to_segment_m(p, a, b):
    """Metres from p to segment ab, on a flat local projection.

    Over one side of the moat the curvature of the earth is not the error that
    matters; agreeing with `importers/routing.py`'s `_to_seg` is.
    """
    kx = math.cos(math.radians(p[0])) * 111320.0
    ky = 110540.0
    px, py = p[1] * kx, p[0] * ky
    ax, ay = a[1] * kx, a[0] * ky
    bx, by = b[1] * kx, b[0] * ky
    dx, dy = bx - ax, by - ay
    span = dx * dx + dy * dy
    if span == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class Rules:
    """The directional rules, resolved against the catalogue's own geometry."""

    def __init__(self, poly, crossings):
        self.poly = [list(p) for p in poly]
        self.centre = (sum(p[0] for p in self.poly) / len(self.poly),
                       sum(p[1] for p in self.poly) / len(self.poly))
        self.crossings = []
        for lat, lng, th, en, kind in crossings:
            b = bearing(self.centre, (lat, lng))
            self.crossings.append({
                "lat": lat, "lng": lng, "th": th, "en": en, "kind": kind,
                "bearing": round(b, 1),
                "metres": round(hav(self.centre, (lat, lng)), 1),
                "ring_offset_m": round(self.ring_offset((lat, lng)), 1),
                "quadrant": quadrant(b),
                "in_southwest": in_arc(b, *SOUTHWEST),
            })
        self.crossings.sort(key=lambda c: c["bearing"])

    @classmethod
    def load(cls):
        """Build from `build.py`'s moat geometry.

        Returns None when it is not there, the same way map_ground reports a
        missing archive: a caller with no geometry keeps the prose it already
        had rather than being handed a rule resolved against a guess.
        """
        import build
        if not build.MOAT_POLY:
            return None
        crossings = build._moat_crossings()
        if not crossings:
            return None
        return cls(build.MOAT_POLY, crossings)

    # ---- geometry --------------------------------------------------------

    def ring_offset(self, p):
        """Metres from a point to the nearest side of the moat ring."""
        n = len(self.poly)
        return min(_dist_to_segment_m(p, self.poly[i], self.poly[(i + 1) % n])
                   for i in range(n))

    def gates(self, ok=True):
        """The gates a crossing may (or may not) use, by quadrant."""
        return [c for c in self.crossings
                if c["kind"] == "gate"
                and ((c["quadrant"] in GATE_QUADRANTS_OK) == bool(ok))]

    def on_moat_ring(self, p, tol_m=MOAT_TOL_M):
        """Whether a point is riding the ring rather than leaving through it."""
        return self.ring_offset(p) <= tol_m

    def inside_moat(self, p):
        """Whether a point is inside the old city. Ray casting on the ring."""
        hit = False
        n = len(self.poly)
        for i in range(n):
            a, b = self.poly[i], self.poly[(i + 1) % n]
            if (a[0] > p[0]) != (b[0] > p[0]):
                x = a[1] + (p[0] - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
                if p[1] < x:
                    hit = not hit
        return hit

    def crossings_of(self, points, near_m=GATE_NEAR_M, band_m=RING_BAND_M):
        """Where a line actually gets across the moat, and at which gate.

        A crossing is a change of side, not a near miss. Testing proximity
        alone refuses the lap itself: riding the ring passes within a few metres
        of Chiang Mai Gate and Saen Pung Gate without going through either.

        THE BAND, AND WHY IT IS NOT OPTIONAL. `self.poly` is the four แจ่ง
        corners joined by straight chords, and the real ring road curves. The
        inner moat road sits only 13-22 m off those chords — Moon Muang 15.7 m,
        Bumrung Buri 13.0 m, Sri Poom 21.5 m — so a route simply following it
        weaves back and forth across the chord line, and a bare side test
        counted every weave as getting across the water. A lap of the ring came
        back reporting twenty-two moat crossings it had not made, and worse, a
        point-to-point ride along Moon Muang could be refused for crossing at a
        gate it only rode past.

        So points within `band_m` of the ring are on the ring and count as
        neither side. A crossing is a move from CLEARLY one side to CLEARLY the
        other, and the band is what tells a road that hugs the moat apart from
        a road that goes over it.

        A crossing at no named gate is reported with `gate: None` rather than as
        a fault — the nine are the ones anyone would name, and build.py says
        plainly they are not every bridge over the water.
        """
        out = []
        gates = [c for c in self.crossings if c["kind"] == "gate"]

        def side(p):
            if self.ring_offset(p) <= band_m:
                return 0                     # on the ring, neither side
            return 1 if self.inside_moat(p) else -1

        last = 0
        last_i = 0
        for i, raw in enumerate(points):
            p = (raw[0], raw[1])
            s = side(p)
            if s == 0:
                continue
            if last != 0 and s != last:
                a = points[last_i]
                mid = ((a[0] + p[0]) / 2.0, (a[1] + p[1]) / 2.0)
                best = None
                for c in gates:
                    d = hav(mid, (c["lat"], c["lng"]))
                    if best is None or d < best[0]:
                        best = (d, c)
                out.append({
                    "index": i, "point": [mid[0], mid[1]],
                    "outbound": last == 1,
                    "gate": best[1] if best and best[0] <= near_m else None,
                    "gate_m": round(best[0], 1) if best else None,
                })
            last, last_i = s, i
        return out

    def in_southwest(self, p):
        """Whether a point sits in the southwest quarter. No exemption — this
        is the strict test, for stops."""
        return in_arc(bearing(self.centre, p), *SOUTHWEST)

    def clockwise(self, points):
        """Whether successive points turn clockwise about the centre.

        Consecutive bearings are compared the short way round, so a lap that
        crosses north does not read as a reversal.
        """
        bs = [bearing(self.centre, p) for p in points]
        turn = 0.0
        for a, b in zip(bs, bs[1:]):
            turn += (b - a + 540.0) % 360.0 - 180.0
        return turn >= 0.0, round(turn, 1)

    # ---- the checks ------------------------------------------------------

    def check_stops(self, stops):
        """The strict rule: no waypoint or destination in the southwest."""
        out = []
        for i, s in enumerate(stops):
            p = (s[0], s[1])
            if self.in_southwest(p):
                out.append({
                    "rule": "quarter", "index": i, "point": [p[0], p[1]],
                    "bearing": round(bearing(self.centre, p), 1),
                    "metres": round(hav(self.centre, p), 1),
                    "ring_offset_m": round(self.ring_offset(p), 1),
                    "why_th": "จุดหยุดนี้อยู่ในทิศตะวันตกเฉียงใต้",
                    "why_en": "this stop lies in the southwest quarter",
                })
        return out

    def is_lap(self, points):
        """Whether a line comes back to where it started."""
        return (len(points) > 2
                and hav((points[0][0], points[0][1]),
                        (points[-1][0], points[-1][1])) <= LAP_CLOSE_M)

    def check_line(self, points, tol_m=MOAT_TOL_M, lap=None):
        """The gate rule, the turning rule where it applies, and a notice for
        transit that leaves the ring and runs off into the quarter.

        `lap` decides whether เวียนขวา is tested at all. Left as None it is
        worked out from the line itself — a route that ends where it began is a
        lap and has a direction to be right or wrong about; one that ends
        somewhere else does not.
        """
        out = []

        seen = set()
        for x in self.crossings_of(points):
            c = x["gate"]
            if not c or c["quadrant"] in GATE_QUADRANTS_OK or c["en"] in seen:
                continue
            seen.add(c["en"])
            out.append({
                "rule": "gate", "index": x["index"], "point": x["point"],
                "gate_th": c["th"], "gate_en": c["en"],
                "quadrant": c["quadrant"],
                "outbound": x["outbound"], "gate_m": x["gate_m"],
                "why_th": f"ข้ามคูเมืองที่{c['th']} ({QUADRANT_TH[c['quadrant']]})",
                "why_en": (f"crosses the moat at {c['en']}, which is "
                           f"{c['quadrant']} — the loop closes north, "
                           f"east or west"),
            })

        for i, p in enumerate(points):
            p = (p[0], p[1])
            if self.in_southwest(p) and not self.on_moat_ring(p, tol_m):
                out.append({
                    "rule": "transit", "notice": True, "index": i,
                    "point": [p[0], p[1]],
                    "bearing": round(bearing(self.centre, p), 1),
                    "ring_offset_m": round(self.ring_offset(p), 1),
                    "why_th": "เส้นทางออกนอกแนวคูเมืองไปทางทิศตะวันตกเฉียงใต้",
                    "why_en": ("the line leaves the moat ring and runs into the "
                               "southwest quarter"),
                })
                break

        if lap is None:
            lap = self.is_lap(points)
        if lap:
            cw, turn = self.clockwise(points)
            if not cw:
                out.append({
                    "rule": "turning", "index": 0, "turn_degrees": turn,
                    "why_th": "เส้นทางเวียนซ้าย ไม่ใช่เวียนขวา",
                    "why_en": "the lap turns anticlockwise; เวียนขวา is clockwise",
                })
        return out

    def check_ride(self, stops=(), line=(), lap=None):
        """Both checks together.

        A notice does not fail a ride; a rule does. Findings are ordered by
        which rule matters, not by where along the route it fired, so the one
        printed first is the one worth acting on.
        """
        findings = (list(self.check_stops(stops))
                    + list(self.check_line(line, lap=lap)))
        findings.sort(key=lambda f: (bool(f.get("notice")),
                                     RULE_ORDER.get(f.get("rule"), 9),
                                     f.get("index", 0)))
        hard = [f for f in findings if not f.get("notice")]
        return {
            "ok": not hard,
            "stops": len(stops),
            "line_points": len(line),
            "findings": findings,
            "first_finding": hard[0] if hard else (findings[0] if findings else None),
            "centre": [round(self.centre[0], 6), round(self.centre[1], 6)],
        }

    def ring_waypoints(self, spacing_m=140.0, start=None):
        """Points round the moat ring, clockwise, for shaping a lap.

        A lap cannot be planned from the four แจ่ง corners alone. Between two
        corners the shortest way is a diagonal through the old city, so the
        router — correctly doing what it was asked — returned a line that
        crossed the water twelve times and ran 8.86 km against a 5.98 km
        perimeter. Waypoints close enough together that no shortcut between
        neighbours is shorter than the ring itself are what make the ring the
        answer.

        These are SHAPING points and not stops. That distinction matters: the
        quarter rule is strict about stops, and the ring necessarily passes
        through the southwest. Pass them as the line's shape, never as `stops`.

        `start` rotates the sequence to begin at the sampled point nearest a
        place — Chang Phueak, normally, since that is the gate she leaves by.
        """
        pts = []
        n = len(self.poly)
        for i in range(n):
            a, b = self.poly[i], self.poly[(i + 1) % n]
            side = hav(a, b)
            steps = max(1, int(side // spacing_m))
            for s in range(steps):
                t = s / float(steps)
                pts.append([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])
        if start is not None and pts:
            k = min(range(len(pts)),
                    key=lambda j: hav(pts[j], (start[0], start[1])))
            pts = pts[k:] + pts[:k]
        return pts

    def lap_clockwise(self):
        """The gates of a clockwise lap, in the order they come round.

        Saen Pung is absent because it is southwest, and Chiang Mai Gate
        because it is south — the rule expresses itself as an omission from the
        chain rather than as a warning after the fact.
        """
        return self.gates(ok=True)

    # ---- the emitted record ----------------------------------------------

    def as_document(self):
        return {
            "note": ("Standing directional rules for a ride, resolved from the "
                     "catalogue's own moat pins. Generated by ride_rules.py — "
                     "edit the module, not this file."),
            "centre": {"lat": round(self.centre[0], 6),
                       "lng": round(self.centre[1], 6),
                       "via": "centroid of the four แจ่ง corners in build.MOAT_POLY"},
            "moat_ring": self.poly,
            "thresholds": {
                "moat_tol_m": MOAT_TOL_M,
                "gate_near_m": GATE_NEAR_M,
                "southwest_arc_degrees": list(SOUTHWEST),
                "gate_quadrants_ok": list(GATE_QUADRANTS_OK),
            },
            "how_the_rules_divide": {
                "th": ("กฎเรื่องทิศใช้กับจุดหยุดและประตูที่ข้าม ไม่ใช้กับทุกเมตรที่ขี่ผ่าน "
                       "แนวคูเมืองถือเป็นทางเวียน"),
                "en": ("The quarter rule is applied strictly to stops, and to which "
                       "gate a crossing uses. It is not applied to every metre "
                       "ridden, because the moat's own southwest corner is 1108 m "
                       "from the centre and Suan Prung about 1119 m on nearly the "
                       "same bearing — eleven metres apart radially, so no radius "
                       "separates them. Riding the ring is the lap; leaving through "
                       "Saen Pung or stopping in the southwest is not. moat_tol_m "
                       "governs only the transit notice."),
                "measured": {
                    "southwest_arc_crossings_off_ring_m": [0.0, 21.5],
                    "suan_prung_off_ring_m": 118.1,
                    "widest_crossing_off_ring_m": 91.1,
                    "widest_crossing": "Suan Dok Gate (W) — reproduces build.py's ~92 m",
                },
            },
            "crossings": self.crossings,
            "lap_clockwise": [{"th": c["th"], "en": c["en"],
                               "quadrant": c["quadrant"], "bearing": c["bearing"]}
                              for c in self.lap_clockwise()],
            "gates_off_route": [{"th": c["th"], "en": c["en"],
                                 "quadrant": c["quadrant"], "bearing": c["bearing"]}
                                for c in self.gates(ok=False)],
            "unverified": {
                "note": ("Named in the prose as sitting in the southwest, but not "
                         "enforced here: no polygon for any of them has a fetched "
                         "source, and the rule governing honours.json and names.json "
                         "applies — a lead waits here and is never rendered as a "
                         "fact. The quarter rule already catches a stop in any of "
                         "them; what is missing is the corridor a route could clip "
                         "without stopping."),
                "corridors": [
                    {"th": "ถนน 1269 หางดง", "en": "1269 Hang Dong road", "source": None},
                    {"th": "ต้นเกว๋น", "en": "Ton Kwen", "source": None},
                    {"th": "จอมทอง", "en": "Chom Thong", "source": None},
                    {"th": "วัดศรีสุพรรณ", "en": "Wat Sri Suphan", "source": None},
                ],
            },
            "range": {
                "th": "กราฟถนนครอบคลุมเฉพาะในเมือง",
                "en": ("data/road_graph.json covers the city core only — about "
                       "18.757–18.825 N, 98.953–99.017 E. Doi Kham at 98.919 E "
                       "falls outside it, so a ride out there cannot be routed "
                       "on the offline graph as it stands. The quarter rule still "
                       "answers for it, because a bearing needs no graph."),
            },
        }


def main():
    rules = Rules.load()
    if rules is None:
        print("no moat geometry on disk — nothing written")
        return 1
    out = ROOT / "data" / "ride_rules.json"
    out.write_text(json.dumps(rules.as_document(), ensure_ascii=False, indent=2) + "\n")
    print(f"centre  {rules.centre[0]:.6f}, {rules.centre[1]:.6f}")
    print("clockwise lap  : " +
          " → ".join(f"{c['en']} ({c['quadrant']})" for c in rules.lap_clockwise()))
    print("off the route  : " +
          ", ".join(f"{c['en']} ({c['quadrant']})" for c in rules.gates(ok=False)))
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
