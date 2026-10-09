#!/usr/bin/env python3
"""ไหว้พระ ๙ วัด — the wat rounds, ordered on the road graph and drawn on it.

Replaces `build_merit.py`, which this file is descended from and disagrees with
on three things a reader can see:

  1. **WHICH PLACES ARE WATS.** The catalogue's `wat` lens is wider than the
     word: it holds ศาล shrines, a Hindu เทวาลัย, a Chinese joss house, a
     Christian hall, a museum, a tea house, an apron shop, a cemetery, and
     buildings that stand INSIDE a wat (วิหารลายคำ is a viharn in วัดพระสิงห์;
     อุโบสถ ๑๐๐ ปี is one at วัดแสนฝาง). Nine of those on a round of nine wats
     is a wrong answer in somebody's afternoon: five were on the published
     rounds, including เทพมณเฑียร, a Hindu temple. A stop here has to be named
     as a wat — วัด or Wat at the head of its own name — and nothing else
     qualifies a place.

  2. **WHERE THEY ARE.** 55 records in the box come from the ONAB temple
     register, which places a wat at its tambon rather than at its gate: 37 of
     them sit on one point off Chotana Road, and they are wats in อ.แม่อาย and
     อ.ฝาง, 100 km away. `geoPrecision: approx` cannot be walked to and is not
     routed. OVT records are exact but placed loosely — its วัดดวงดี is a
     kilometre from the วัดดวงดี on Ratchadamnoen, its วัดบ่อสร้าง is 45 m from
     วัดผาบ่อง and 10 km from Bo Sang — so stops are taken from OSM, whose
     polygons are also what the road graph was cut from. What the other sources
     hold that OSM does not is counted in the payload, not walked to.

  3. **THE ORDER, AND THE LINE.** Nine stops is small enough to solve exactly —
     Held-Karp costs 41k operations — so the round is the shortest closed walk
     and not a 2-opt approximation of it. And every leg carries the line it is
     actually walked along, from `Graph.route`, so the map draws streets. The
     old map drew the stops joined by straight lines, which crossed blocks,
     buildings and the moat; the caption admitted it, which is not the same as
     it being right.

Same shape of output as before, plus per-leg lines and metres:

    python3 importers/build_wats.py            # writes data/wats.json
    python3 importers/build_wats.py --n 3      # cap how many rounds

Reads data/road_graph.json + data/canonical/cm.json. Stdlib only, Python 3.9.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
sys.path.insert(0, str(ROOT))
from routing import Graph, hav          # noqa: E402
import translit                        # noqa: E402

OUT = ROOT / "data" / "wats.json"

NINE = 9

# The four แจ่ง corners, the same records build.py reads, so the two agree on
# where the walls are.
MOAT_CORNER_IDS = {
    "ne": "cm-osm-way-263459882",
    "se": "cm-osm-way-791602197",
    "sw": "cm-osm-way-317516851",
    "nw": "cm-osm-way-317516852",
}

# Honorifics and locatives that ride on a wat's full name and not on the name
# anybody says: วัดเจดีย์หลวงวรวิหาร and Wat Chedi Luang are one wat.
NAME_TAILS_TH = ("วรมหาวิหาร", "ราชวรวิหาร", "วรวิหาร", "พระอารามหลวง",
                 "อารามหลวง", "จังหวัดเชียงใหม่", "จังหวัด", "เชียงใหม่")
NAME_TAILS_LAT = ("varavihara", "worawihan", "chiangmai", "chiang mai")

# Romanisation varies by hand and by sign. Folded to a consonant skeleton the
# variants agree: Wat Jed Yod and วัดเจ็ดยอด (Wat Chet Yot) both reduce to
# wctyt. Blunt on purpose, and only ever trusted with the distance test below.
_DIGRAPHS = (("ph", "p"), ("th", "t"), ("kh", "k"), ("ch", "c"), ("sh", "s"))
_LETTERS = (("j", "c"), ("g", "k"), ("b", "p"), ("d", "t"), ("v", "w"), ("z", "s"))

SAME_PLACE_M = 320

FOOT_LEG_M = 1200
FOOT_ROUND_M = 7000
# A round somebody would actually ride for merit in one afternoon. Past this the
# greedy grouping is only sweeping up the wats nobody's round reached — the ninth
# stop of a 28 km circuit across the whole city is a list, not a round, and one
# of them had a leg the one-way network could not ride at all. Those wats keep
# their pages and their neighbours; they do not get a made-up round.
RIDE_ROUND_M = 15000
SPREAD_M = 1500


def names_of(r):
    return [n for n in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if n]


def is_wat(r):
    """Named as a wat, at the head of its own name.

    `วัด` anywhere in the string is not the test: มูลนิธิวัดศรีโสดา is a
    foundation, ศูนย์เรียนรู้…วัดเมืองสาตร a learning centre, สุสานวัดช้างเคี่ยน
    a cemetery, and เจดีย์ (ร้าง) วัดฟ่อนสร้อย a ruined chedi inside one.
    """
    return any(re.match(r"^\s*(วัด|Wat\b)", n.strip(), re.I) for n in names_of(r))


def skeleton(name):
    """One key per wat name, blind to script, spelling and tone marks."""
    s = re.sub(r"[（(][^）)]*[）)]", "", name or "")
    s = re.split(r"[-–—]", s)[0]
    for t in NAME_TAILS_TH:
        s = s.replace(t, "")
    if re.search(r"[฀-๿]", s):
        s = translit.reading(s)
    s = s.lower()
    for t in NAME_TAILS_LAT:
        s = s.replace(t, "")
    s = re.sub(r"[^a-z]", "", s)
    for a, b in _DIGRAPHS:
        s = s.replace(a, b)
    for a, b in _LETTERS:
        s = s.replace(a, b)
    # Whatever h survives the digraphs is decorative: Singh and Sing, Chomphu
    # and Chompu, Umong and Umongh are the same wat on different signs.
    s = s.replace("h", "")
    s = re.sub(r"[aeiou]", "", s)
    return re.sub(r"(.)\1+", r"\1", s)


def keys_of(r):
    return {k for k in (skeleton(n) for n in names_of(r)) if len(k) >= 4}


def same_wat(a, b):
    """One wat mapped twice: the keys agree AND the ground agrees.

    Exact keys only. A key that merely STARTS with another was tried and folded
    วัดทรายมูล (พม่า) into วัดทรายมูลเมือง — two wats, 136 m and a Burmese
    lineage apart — so a shorter name is no longer taken for the same name.
    """
    if hav((a["lat"], a["lng"]), (b["lat"], b["lng"])) > SAME_PLACE_M:
        return False
    return bool(keys_of(a) & keys_of(b))


def moat_ring(by_id):
    pts = [by_id.get(MOAT_CORNER_IDS[k]) for k in ("nw", "ne", "se", "sw")]
    if not all(p and p.get("lat") is not None for p in pts):
        return None
    return [(p["lat"], p["lng"]) for p in pts]


def inside(poly, p):
    """Ray casting. The moat is out of square, and its bounding box would put
    Suan Dok Gate on the wrong side of its own water."""
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


def bearing_name(centre, poly, spread=0.0):
    """Where this round sits, said the way somebody here would say it.

    A round whose stops are spread wider than the walls is not "in the walls"
    because its average happens to land there: round 8 runs from Ku Tao in the
    north to Wat Yang Kuang in the south and its centroid sits on Ratchadamnoen.
    """
    if spread > SPREAD_M:
        return ("รอบเมือง", "around the city")
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
    copies drift, and the drift would be a wrong image against somebody's birth
    day."""
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


def best_cycle(matrix):
    """The shortest closed order through every point, exactly.

    Held–Karp over subsets, start fixed at 0. Nine stops is 2^9·9·9 operations,
    so there is no reason for this to be an approximation: 2-opt lands near the
    best answer and near is visible on the ground as a block walked twice.
    """
    n = len(matrix)
    if n < 3:
        return list(range(n))

    def leg(i, j):
        v = matrix[i][j]
        # Unroutable must not read as free, and must not overflow a comparison.
        return 1e7 if v is None else v

    full = 1 << n
    INF = float("inf")
    cost = [[INF] * n for _ in range(full)]
    back = [[-1] * n for _ in range(full)]
    cost[1][0] = 0.0
    for mask in range(full):
        if not (mask & 1):
            continue
        row = cost[mask]
        for last in range(n):
            c = row[last]
            if c == INF:
                continue
            for nxt in range(1, n):
                if mask & (1 << nxt):
                    continue
                nm = mask | (1 << nxt)
                nc = c + leg(last, nxt)
                if nc < cost[nm][nxt]:
                    cost[nm][nxt] = nc
                    back[nm][nxt] = last
    end, best = None, INF
    for last in range(1, n):
        c = cost[full - 1][last] + leg(last, 0)
        if c < best:
            best, end = c, last
    order, mask, cur = [], full - 1, end
    while cur != -1:
        order.append(cur)
        prev = back[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    return order[::-1]


def rotate_and_face(order, pts, matrix, anchor):
    """Where the round starts, and which way round it goes.

    The cycle is a cycle — every rotation walks the same metres — so the choice
    is a reader's, not the solver's. It starts at the stop nearest the middle of
    the old city, which is where most people begin the day, and it turns the way
    that makes the first leg the shorter of the two.
    """
    ds = [hav(pts[i], anchor) for i in order]
    k = ds.index(min(ds))
    order = order[k:] + order[:k]
    n = len(order)
    fwd = matrix[order[0]][order[1]]
    bwd = matrix[order[0]][order[-1]]
    if bwd is not None and (fwd is None or bwd < fwd):
        order = [order[0]] + order[1:][::-1]
    return order


def leg_lines(g, ordered, pts, mode, allow=None):
    """Every leg of the round as the line it is walked along, with its metres.

    A leg the graph cannot route keeps its place and says so with a null line —
    dropping it would renumber the stops, and drawing it straight is what this
    file exists to stop.
    """
    out = []
    n = len(ordered)
    for i in range(n):
        a, b = pts[ordered[i]], pts[ordered[(i + 1) % n]]
        j = g.route(a, b, mode, allow)
        if j is None:
            out.append({"m": None, "line": None, "snap": [0, 0]})
            continue
        line = [[round(p[0], 5), round(p[1], 5)] for p in j["path"]]
        # Straight duplicates cost bytes on every page that draws them.
        thin = [line[0]]
        for p in line[1:]:
            if p != thin[-1]:
                thin.append(p)
        # The walk in from each pin to the road, which the metres include and
        # the road line does not: a 250 m leg between two wats set back from the
        # street is a quarter walk-in, and a drawing that leaves it out is
        # shorter than the number printed beside it. The page draws it as a stub
        # from the pin, which is what /plan.html has always done.
        out.append({"m": round(j["m"]), "line": thin,
                    "snap": [round(x) for x in j.get("snap_in_m") or [0, 0]]})
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

    records = json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())
    by_id = {r["id"]: r for r in records}
    poly = moat_ring(by_id)

    lensed = [r for r in records
              if "wat" in r.get("cat", []) and r.get("lat") is not None
              and g.contains((r["lat"], r["lng"]))]
    named = [r for r in lensed if is_wat(r)]
    not_named = [r for r in lensed if not is_wat(r)]
    placed = [r for r in named if r.get("geoPrecision") != "approx"]
    approx = [r for r in named if r.get("geoPrecision") == "approx"]
    osm = [r for r in placed if "-osm-" in r["id"]]
    elsewhere = [r for r in placed if "-osm-" not in r["id"]]

    print("in the routable box, under the wat lens: %d" % len(lensed))
    print("  named as a wat:            %d   (%d are not: shrines, halls, "
          "buildings inside a wat)" % (len(named), len(not_named)))
    print("  placed at their own gate:  %d   (%d sit at a tambon centroid)"
          % (len(placed), len(approx)))
    print("  mapped in OSM:             %d   (%d only in another source)"
          % (len(osm), len(elsewhere)))

    # One record per wat. OSM holds วัดพันอ้น twice, as a node and as a way, and
    # a round that calls at the same wat at stop three and stop seven is wrong.
    groups = []
    folded = 0
    for r in osm:
        for grp in groups:
            if any(same_wat(r, q) for q in grp):
                grp.append(r)
                folded += 1
                break
        else:
            groups.append([r])

    def pick(grp):
        # The richest record leads: a polygon over a node, a summary over none.
        return sorted(grp, key=lambda r: (
            -len((r.get("attrs") or {}).get("summary", {}) or {}),
            0 if "-way-" in r["id"] or "-relation-" in r["id"] else 1,
            r["id"]))[0]

    wats = [pick(grp) for grp in groups]
    alsoknown = {pick(grp)["id"]: [q["id"] for q in grp if q is not pick(grp)]
                 for grp in groups if len(grp) > 1}
    print("  one record per wat:        %d   (%d second mappings folded)"
          % (len(wats), folded))

    pts = [(w["lat"], w["lng"]) for w in wats]
    print("routing %d wats, both modes..." % len(pts))
    # Snapped onto the connected city, never onto a courtyard path that joins
    # nothing: Wat Phra Singh, Wat Suan Dok and วัดดวงดี each snapped inside
    # their own compound and were set aside as unreachable — the most visited
    # wat in Chiang Mai was on no round at all.
    on_foot = g.main_component("foot")
    on_ride = g.main_component("ride")
    foot = g.matrix(pts, "foot", on_foot)
    ride = g.matrix(pts, "ride", on_ride)

    # A wat the network cannot reach cannot be put on a walking round. Better
    # to leave it off nine stops than to promise a walk that does not exist.
    reach = [sum(1 for v in foot[i] if v is not None) for i in range(len(pts))]
    keep = [i for i in range(len(pts)) if reach[i] >= NINE]
    set_aside = [wats[i]["id"] for i in range(len(pts)) if i not in keep]
    print("  %d walkable from at least eight others  (%d set aside)"
          % (len(keep), len(set_aside)))

    anchor = None
    if poly:
        anchor = (sum(p[0] for p in poly) / len(poly),
                  sum(p[1] for p in poly) / len(poly))

    # Rounds of nine, tightest first. Each wat is used once, so the rounds are
    # different outings and not nine views of the same eight streets.
    unused = set(keep)
    rounds = []
    while len(unused) >= NINE:
        best = None
        for seed in unused:
            near = sorted((foot[seed][j], j) for j in unused
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
        sub = [[foot[i][j] for j in group] for i in group]
        ordered = [group[i] for i in best_cycle(sub)]
        centre = (sum(pts[i][0] for i in ordered) / NINE,
                  sum(pts[i][1] for i in ordered) / NINE)
        ordered = rotate_and_face(ordered, pts, foot, anchor or centre)

        f_legs = leg_lines(g, ordered, pts, "foot", on_foot)
        r_legs = leg_lines(g, ordered, pts, "ride", on_ride)

        def total(legs):
            if any(x["m"] is None for x in legs):
                return None
            return round(sum(x["m"] for x in legs))

        spread = max(hav(pts[i], centre) for i in ordered)
        th, en = bearing_name(centre, poly, spread)
        # Which way this round is done. Nine wats is walked when the wats are
        # close enough to walk between and ridden when they are not; calling a
        # 16 km circuit with a 3 km leg a walk is the kind of promise a reader
        # pays for in the afternoon. FOOT_LEG_M is a leg somebody will walk in
        # the heat between two wats; FOOT_ROUND_M is an afternoon of it.
        legs_m = [x["m"] for x in f_legs if x["m"] is not None]
        walkable = (len(legs_m) == NINE
                    and max(legs_m) <= FOOT_LEG_M
                    and sum(legs_m) <= FOOT_ROUND_M)
        ride_m = None if any(x["m"] is None for x in r_legs) \
            else round(sum(x["m"] for x in r_legs))
        if not walkable and (ride_m is None or ride_m > RIDE_ROUND_M):
            break
        rounds.append({
            "mode": "foot" if walkable else "ride",
            "th": "ไหว้พระ ๙ วัด %s" % th,
            "en": "Nine wats, %s" % en,
            "area_th": th, "area_en": en,
            "centre": [round(centre[0], 6), round(centre[1], 6)],
            "foot_m": total(f_legs),
            "ride_m": total(r_legs),
            "inside_walls": inside(poly, centre),
            "foot_legs": f_legs,
            "ride_legs": r_legs,
            "stops": [{
                "id": wats[i]["id"],
                "name": wats[i].get("name"),
                # Both, where the record holds both. The page resolves the pair
                # from the catalogue, so the two cannot disagree.
                "nameTh": wats[i].get("nameTh"),
                "nameEn": wats[i].get("nameEn"),
                "province": wats[i]["province"],
                "lat": wats[i]["lat"], "lng": wats[i]["lng"],
                "also": alsoknown.get(wats[i]["id"], []),
            } for i in ordered],
        })
        unused -= set(group)
        if cap and len(rounds) >= cap:
            break

    # The walkable rounds lead, tightest first, then the ones that want a
    # scooter. A reader on foot should not have to read past a 16 km circuit.
    rounds.sort(key=lambda x: (x["mode"] != "foot", x["foot_m"] is None,
                               x["foot_m"] or 0))
    for i, r in enumerate(rounds):
        r["slug"] = "round-%02d" % (i + 1)

    on_a_round = {s["id"] for r in rounds for s in r["stops"]}
    payload = {
        "generated": None,      # stamped by the caller, never by a clock here
        "practice_th": "ไหว้พระ ๙ วัด — ธรรมเนียมที่คนทำกันจริง "
                       "มากที่สุดช่วงปีใหม่และสงกรานต์",
        "practice_en": ("Visiting nine wats in one round is an ordinary "
                        "practice here, done most at New Year and Songkran."),
        "not_a_ranking_th": "ลำดับคือทางเดินที่สั้นที่สุด",
        "not_a_ranking_en": "The order is the shortest way round.",
        # The eight พระประจำวันเกิด, taken from make_fortune's table rather than
        # retyped. Shown as what to look for at any wat — the image for the
        # weekday you were born. Nothing here pairs a wat with a weekday; that
        # pairing is not in the tradition and is not ours to make.
        "birthday_buddhas": birthday_buddhas(),
        "counts": {
            "rounds": len(rounds),
            "wats_used": len(on_a_round),
            "wats_placed": len(wats),
            "under_the_lens": len(lensed),
            "not_named_as_a_wat": len(not_named),
            "at_a_centroid": len(approx),
            "only_in_another_source": len(elsewhere),
            "second_mappings_folded": folded,
            "set_aside_unreachable": len(set_aside),
            "rounds_on_foot": sum(1 for r in rounds if r["mode"] == "foot"),
        },
        "wats": [{
            "id": w["id"],
            "name": w.get("name"),
            "nameTh": w.get("nameTh"),
            "nameEn": w.get("nameEn"),
            "lat": w["lat"], "lng": w["lng"],
            "inside_walls": inside(poly, (w["lat"], w["lng"])),
            "on_a_round": w["id"] in on_a_round,
            "also": alsoknown.get(w["id"], []),
        } for w in sorted(wats, key=lambda x: x.get("name") or "")],
        "set_aside": set_aside,
        "rounds": rounds,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print("\n%d rounds of nine  →  %s  (%.0f kB)"
          % (len(rounds), OUT.relative_to(ROOT), OUT.stat().st_size / 1000.0))
    for r in rounds:
        walk = "—" if r["foot_m"] is None else "%.1f km" % (r["foot_m"] / 1000.0)
        ride = "—" if r["ride_m"] is None else "%.1f km" % (r["ride_m"] / 1000.0)
        print("   %-9s %-26s %-5s walk %-8s ride %-8s"
              % (r["slug"], r["area_th"], r["mode"], walk, ride))
    return 0


if __name__ == "__main__":
    sys.exit(main())
