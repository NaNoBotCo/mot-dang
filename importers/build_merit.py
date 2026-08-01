#!/usr/bin/env python3
"""ไหว้พระ ๙ วัด — nine-temple routes, generated from the catalogue.

Visiting nine temples in one round is a real and ordinary practice here, done
most at ปีใหม่ and สงกรานต์. People already do it; what they do not have is a
walkable order for the temples nearest them. The catalogue holds 104 temples
inside the routable box and a road graph that knows the one-way sois, so the
order can simply be worked out.

**A route is an order of walking. It is not a ranking, and must never read as
one.** No temple here is placed above another; the sequence is the shortest way
round and nothing else, and `/merit.html` says so in those words. Royal grade is
shown where the Sangha has assigned one, because the Sangha assigned it — never
as this project's opinion, and never as a reason one temple leads a route.

What the generator does:

  1. Take the temples inside the road graph's box, deduplicated by name — OSM
     holds วัดพันอ้น twice, as a node and as a way, and a route that visits the
     same temple at stop three and stop seven is simply wrong.
  2. Drop any that the road network cannot actually reach. A handful snap into
     footpath fragments inside their own compound with no way out; a route
     promising to walk there would be a lie told in metres.
  3. Grow disjoint groups of nine, densest first, so each route is compact and
     no temple appears on two routes.
  4. Order each group by real network distance, and bake the walk and the ride
     separately — they differ, which is the point of having the graph.

    python3 importers/build_merit.py        # writes data/merit.json
    python3 importers/build_merit.py --n 6  # cap how many routes

Reads data/road_graph.json + data/canonical/*.json. Written for stdlib Python
3.9, like everything else here.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from routing import Graph, hav, order_loop          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "merit.json"

NINE = 9

# The four แจ่ง corners, same records build.py reads, so the two agree on where
# the walls are. A route is named by where it sits relative to them.
MOAT_CORNER_IDS = {
    "ne": "cm-osm-way-263459882",
    "se": "cm-osm-way-791602197",
    "sw": "cm-osm-way-317516851",
    "nw": "cm-osm-way-317516852",
}


def norm_name(s):
    """One key per temple. Strips the วัด prefix, spaces and punctuation, so
    'วัดพันอ้น' and 'วัด พันอ้น' are recognised as the same place."""
    s = (s or "").strip()
    s = re.sub(r"^(วัด|Wat)\s*", "", s, flags=re.IGNORECASE)
    return re.sub(r"[\s\-–—_.]+", "", s).lower()


def moat_ring(by_id):
    pts = [by_id.get(MOAT_CORNER_IDS[k]) for k in ("nw", "ne", "se", "sw")]
    if not all(p and p.get("lat") is not None for p in pts):
        return None
    return [(p["lat"], p["lng"]) for p in pts]


def inside(poly, p):
    """Ray casting. The moat is slightly out of square, and using its bounding
    box instead would put Suan Dok Gate on the wrong side of its own water."""
    if not poly:
        return False
    x, y = p[1], p[0]
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        yi, xi = poly[i]
        yj, xj = poly[j]
        if (xi > x) != (xj > x):
            ty = (yj - yi) * (x - xi) / ((xj - xi) or 1e-12) + yi
            if y < ty:
                hit = not hit
        j = i
    return hit


def bearing_name(centre, poly):
    """Where this round sits, said the way somebody here would say it."""
    if inside(poly, centre):
        return ("ในเวียง", "inside the walls")
    if not poly:
        return ("รอบเมือง", "around the city")
    mlat = sum(p[0] for p in poly) / len(poly)
    mlng = sum(p[1] for p in poly) / len(poly)
    dlat, dlng = centre[0] - mlat, (centre[1] - mlng) * math.cos(math.radians(mlat))
    if abs(dlat) >= abs(dlng):
        return ("นอกเวียงด้านเหนือ", "north of the walls") if dlat > 0 \
            else ("นอกเวียงด้านใต้", "south of the walls")
    return ("นอกเวียงด้านตะวันออก", "east of the walls") if dlng > 0 \
        else ("นอกเวียงด้านตะวันตก", "west of the walls")


def birthday_buddhas():
    """The eight, from make_fortune's own table. Imported, never retyped — two
    copies of a list like this drift, and the drift would be a wrong image
    against somebody's birth day."""
    try:
        import make_fortune
    except Exception:
        return []
    out = []
    for d in make_fortune.THAI_DAYS:
        out.append({k: d[k] for k in
                    ("th", "en", "colour_th", "colour_en", "hex",
                     "buddha_th", "buddha_en")})
    w = make_fortune.WEDNESDAY_NIGHT
    out.append({k: w[k] for k in
                ("th", "en", "colour_th", "colour_en", "hex",
                 "buddha_th", "buddha_en")})
    return out


def main():
    cap = None
    if "--n" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--n") + 1])

    g = Graph.load()
    if g is None:
        print("no data/road_graph.json — run crawl_roads.py then "
              "build_road_graph.py first", file=sys.stderr)
        return 1

    records = []
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / ("%s.json" % prov)
        if f.exists():
            records += json.loads(f.read_text())
    by_id = {r["id"]: r for r in records}
    poly = moat_ring(by_id)

    # Temples inside the box, one record per temple.
    seen, wats = {}, []
    dupes = 0
    for r in records:
        if "wat" not in r.get("cat", []) or r.get("lat") is None:
            continue
        if not g.contains((r["lat"], r["lng"])):
            continue
        k = norm_name(r.get("name"))
        if not k:
            continue
        if k in seen:
            dupes += 1
            continue
        seen[k] = True
        wats.append(r)
    print("temples inside the routable box: %d  (%d duplicate names folded)"
          % (len(wats), dupes))

    pts = [(w["lat"], w["lng"]) for w in wats]
    print("routing %d temples, both modes..." % len(pts))
    foot = g.matrix(pts, "foot")
    ride = g.matrix(pts, "ride")

    # A temple the network cannot reach cannot be put on a walking route. Better
    # to leave it off nine stops than to promise a walk that does not exist.
    reach = [sum(1 for v in foot[i] if v is not None) for i in range(len(pts))]
    keep = [i for i in range(len(pts)) if reach[i] >= NINE]
    dropped = len(pts) - len(keep)
    print("  %d reachable on foot from at least eight others  (%d set aside)"
          % (len(keep), dropped))

    # Grow rounds of nine, tightest first. Each temple is used once, so the
    # rounds are genuinely different outings rather than nine views of the same
    # eight streets.
    unused = set(keep)
    routes = []
    while len(unused) >= NINE:
        best = None
        for seed in unused:
            near = sorted(
                (foot[seed][j], j) for j in unused
                if j != seed and foot[seed][j] is not None)
            if len(near) < NINE - 1:
                continue
            group = [seed] + [j for _, j in near[:NINE - 1]]
            span = near[NINE - 2][0]
            if best is None or span < best[0]:
                best = (span, group)
        if best is None:
            break
        group = best[1]
        sub_foot = [[foot[i][j] for j in group] for i in group]
        order = order_loop(sub_foot)
        ordered = [group[i] for i in order]

        def total(matrix):
            t = 0.0
            for i in range(len(ordered)):
                v = matrix[ordered[i]][ordered[(i + 1) % len(ordered)]]
                if v is None:
                    return None
                t += v
            return t

        f_m, r_m = total(foot), total(ride)
        centre = (sum(pts[i][0] for i in ordered) / NINE,
                  sum(pts[i][1] for i in ordered) / NINE)
        th, en = bearing_name(centre, poly)
        routes.append({
            "th": "ไหว้พระ ๙ วัด %s" % th,
            "en": "Nine temples, %s" % en,
            "area_th": th, "area_en": en,
            "centre": [round(centre[0], 6), round(centre[1], 6)],
            "foot_m": None if f_m is None else round(f_m),
            "ride_m": None if r_m is None else round(r_m),
            "inside_walls": inside(poly, centre),
            "stops": [{
                "id": wats[i]["id"],
                "name": wats[i].get("name"),
                "nameEn": wats[i].get("nameEn"),
                "province": wats[i]["province"],
                "lat": wats[i]["lat"], "lng": wats[i]["lng"],
            } for i in ordered],
        })
        unused -= set(group)
        if cap and len(routes) >= cap:
            break

    # Tightest walk first — the easiest round to actually do leads.
    routes.sort(key=lambda x: (x["foot_m"] is None, x["foot_m"] or 0))
    for i, r in enumerate(routes):
        r["slug"] = "nine-%02d" % (i + 1)

    payload = {
        "generated": None,      # stamped by the caller, never by a clock here
        "practice_th": "ไหว้พระ ๙ วัด — ธรรมเนียมที่คนทำกันจริง มากที่สุดช่วงปีใหม่และสงกรานต์",
        "practice_en": ("Visiting nine temples in one round is an ordinary "
                        "practice here, done most at New Year and Songkran."),
        "not_a_ranking_th": "ลำดับคือทางเดินที่สั้นที่สุด ไม่ใช่การจัดอันดับวัด",
        "not_a_ranking_en": ("The order is the shortest way round. It is not a "
                             "ranking of temples, and nothing here places one "
                             "temple above another."),
        # The eight พระประจำวันเกิด, taken from make_fortune's table rather than
        # retyped, so the merit page and the fortune tile can never drift apart.
        # These are shown as WHAT TO LOOK FOR at any temple — the image for the
        # weekday you were born. Nothing here says a temple belongs to a
        # weekday; that pairing is not in the tradition and is not ours to make.
        "birthday_buddhas": birthday_buddhas(),
        "counts": {"routes": len(routes), "temples_used": len(routes) * NINE,
                   "temples_in_box": len(pts), "set_aside": dropped,
                   "duplicates_folded": dupes},
        "routes": routes,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print("\n%d rounds of nine  →  %s" % (len(routes), OUT.relative_to(ROOT)))
    for r in routes:
        walk = "—" if r["foot_m"] is None else "%.1f km" % (r["foot_m"] / 1000.0)
        ride = "—" if r["ride_m"] is None else "%.1f km" % (r["ride_m"] / 1000.0)
        print("   %-9s %-26s walk %-8s ride %-8s" % (r["slug"], r["area_th"], walk, ride))
    return 0


if __name__ == "__main__":
    sys.exit(main())
