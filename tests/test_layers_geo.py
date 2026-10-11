#!/usr/bin/env python3
"""layers_geo.py draws four things that were already on disk. This checks it
draws them where they actually are.

    python3 tests/test_layers_geo.py      # 154 checks, ~9 s, reads data/ only
                                          # and never runs a build

Three kinds of check, and the first two are the ones that catch real damage:

  · THE AXIS SWAP. streets.json stores [lat, lng] and GeoJSON wants
    [lng, lat]. Swapped, every soi lands at 98.9° N 18.7° E, in the Barents
    Sea, and every renderer draws it without complaint. So every coordinate
    of every feature is fenced to 97.3–100.6 E and 17.0–20.5 N, the two
    provinces plus room.

  · THE REFUSAL. data/road_graph.json covers the old city plus about 2 km.
    Outside it walk_bands() must raise, not fall back to a circle. Checked
    from Bangkok, from Chiang Rai, and from just past each of the four walls
    of the box — a fence that only fails 700 km away is not a fence.

  · THE COUNTS. Fixed numbers, so a silent change in an input is noticed
    here rather than on the map. Every number below was measured on
    2026-09-08 from the files in data/.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import layers_geo as L  # noqa: E402

# The two provinces plus room. Chiang Mai and Chiang Rai together run roughly
# 17.1–20.5 N, 97.35–100.5 E; anything outside this fence is a bug, not a
# place.
FENCE_W, FENCE_E = 97.3, 100.6
FENCE_S, FENCE_N = 17.0, 20.5

# Measured 2026-09-08. Each is a count from the file named, not a target.
N_SOIS = 534            # data/streets.json: entries carrying `geom`
N_SOIS_MULTI = 89       # of those, in more than one part
N_SOIS_SOI = 317        # of those, sois rather than roads
N_ZONE_BOX = 10         # data/curated/zones.json cm.boxes
N_ZONE_CIRCLE = 10      # cm.circles
N_LANDMARKS = 68        # data/curated/landmarks.json, resolved through bearings
N_SEEDS = 9             # 5 gates + 4 moat corners, all inside the graph box
N_GRAPH_NODES = 9767
N_GRAPH_EDGES = 12280

FAILED = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def coords(geom):
    """Every [lng, lat] pair in any geometry, however nested."""
    t = geom["type"]
    c = geom["coordinates"]
    if t == "Point":
        return [c]
    if t in ("LineString", "MultiPoint"):
        return list(c)
    if t in ("MultiLineString", "Polygon"):
        return [p for part in c for p in part]
    if t == "MultiPolygon":
        return [p for poly in c for ring in poly for p in ring]
    raise AssertionError("unhandled geometry " + t)


def fence(label, fc):
    """No NaN, no infinity, five decimals, and inside the two provinces."""
    bad_num = bad_fence = bad_prec = 0
    n = 0
    for f in fc["features"]:
        for lng, lat in coords(f["geometry"]):
            n += 1
            if not (isinstance(lng, float) or isinstance(lng, int)) \
               or not (isinstance(lat, float) or isinstance(lat, int)) \
               or math.isnan(lng) or math.isnan(lat) \
               or math.isinf(lng) or math.isinf(lat):
                bad_num += 1
                continue
            if not (FENCE_W <= lng <= FENCE_E and FENCE_S <= lat <= FENCE_N):
                bad_fence += 1
            if round(lng, L.PREC) != lng or round(lat, L.PREC) != lat:
                bad_prec += 1
    check(f"{label}: {n:,} coordinates, none NaN or infinite", bad_num == 0, str(bad_num))
    check(f"{label}: every coordinate inside 97.3–100.6 E / 17.0–20.5 N",
          bad_fence == 0, f"{bad_fence} outside")
    check(f"{label}: every coordinate rounded to {L.PREC} decimals",
          bad_prec == 0, f"{bad_prec} longer")
    return n


def valid_geojson(label, fc):
    check(f"{label}: is a FeatureCollection", fc.get("type") == "FeatureCollection")
    check(f"{label}: names its source on disk", bool(fc.get("source")))
    bad = [f for f in fc["features"]
           if f.get("type") != "Feature" or not f.get("geometry")
           or not isinstance(f.get("properties"), dict)]
    check(f"{label}: every feature has a geometry and properties", not bad, str(len(bad)))
    # It must survive the trip it will actually make: json.dumps with Thai
    # kept as Thai, then back.
    s = json.dumps(fc, ensure_ascii=False)
    check(f"{label}: round-trips through JSON with Thai unescaped",
          json.loads(s) == fc and "\\u0e" not in s)


# --------------------------------------------------------------------- sois --

def test_sois():
    print("sois — data/streets.json")
    fc = L.sois()
    valid_geojson("sois", fc)
    check(f"sois: {N_SOIS} ways carry geometry", len(fc["features"]) == N_SOIS,
          str(len(fc["features"])))
    multi = [f for f in fc["features"] if f["geometry"]["type"] == "MultiLineString"]
    single = [f for f in fc["features"] if f["geometry"]["type"] == "LineString"]
    check(f"sois: {N_SOIS_MULTI} come in more than one part", len(multi) == N_SOIS_MULTI,
          str(len(multi)))
    check("sois: every geometry is a LineString or a MultiLineString",
          len(multi) + len(single) == len(fc["features"]))
    # A line of one point is not a line. GeoJSON says two minimum, and a
    # renderer given one draws nothing and says nothing.
    short = [f for f in fc["features"]
             for part in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "LineString"
                          else f["geometry"]["coordinates"])
             if len(part) < 2]
    check("sois: no line with fewer than 2 points", not short, str(len(short)))
    dup = [f for f in fc["features"]
           for part in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "LineString"
                        else f["geometry"]["coordinates"])
           for i in range(len(part) - 1) if part[i] == part[i + 1]]
    check("sois: no zero-length segment left by rounding", not dup, str(len(dup)))
    n = fence("sois", fc)
    check("sois: 8,000+ points, so the geometry is really there", n > 8000, f"{n:,}")

    props = [f["properties"] for f in fc["features"]]
    check("sois: every feature has a slug and a name",
          all(p.get("slug") and p.get("name") for p in props))
    check("sois: slugs are unique", len({p["slug"] for p in props}) == len(props))
    check(f"sois: {N_SOIS_SOI} of them are sois",
          sum(1 for p in props if p["soi"]) == N_SOIS_SOI,
          str(sum(1 for p in props if p["soi"])))
    check("sois: `soi` is a boolean, and the number rides beside it as soiNo",
          all(isinstance(p["soi"], bool) for p in props)
          and all(p.get("soiNo") for p in props if p["soi"]))
    check("sois: `places` is an int on every feature, never a list",
          all(isinstance(p["places"], int) for p in props))
    # 6,227 places are attached to named ways in streets.json; the ways with
    # geometry hold all of them, because only CM has geometry and only CM has
    # places attached. If that stops being true the layer is dropping joins.
    doc = json.loads((ROOT / "data" / "streets.json").read_text())
    placed = doc["counts"]["placed"]
    check(f"sois: the counts add to streets.json's own placed total ({placed:,})",
          sum(p["places"] for p in props) == placed,
          str(sum(p["places"] for p in props)))
    check("sois: every one carries a length", all(p["length"] for p in props))
    # Thai is the name and nameEn is optional. 527 of the 534 names carry
    # Thai; the other 7 are what OSM had — "147 Avenue Shopping", "Chinatown",
    # and one way literally named "one way". They are passed through as they
    # are: a Latin-only name is a fact about the source, not something for a
    # layer to correct on the way past.
    thai = [p for p in props if any("\u0e01" <= ch <= "\u0e5b" for ch in p["name"])]
    check("sois: 527 of the 534 names carry Thai, and none is empty",
          len(thai) == 527 and all(p["name"].strip() for p in props), str(len(thai)))
    return fc


# -------------------------------------------------------------------- zones --

def test_zones():
    print("zones — data/curated/zones.json")
    fc = L.zones()
    valid_geojson("zones", fc)
    boxes = [f for f in fc["features"] if f["properties"]["shape"] == "box"]
    circles = [f for f in fc["features"] if f["properties"]["shape"] == "circle"]
    check(f"zones: {N_ZONE_BOX} boxes", len(boxes) == N_ZONE_BOX, str(len(boxes)))
    check(f"zones: {N_ZONE_CIRCLE} circles", len(circles) == N_ZONE_CIRCLE, str(len(circles)))
    fence("zones", fc)
    check("zones: every ring closes (first point == last)",
          all(f["geometry"]["coordinates"][0][0] == f["geometry"]["coordinates"][0][-1]
              for f in fc["features"]))
    check("zones: every ring has at least 4 points",
          all(len(f["geometry"]["coordinates"][0]) >= 4 for f in fc["features"]))
    check(f"zones: a circle is a {L.CIRCLE_SIDES}-gon",
          all(len(f["geometry"]["coordinates"][0]) == L.CIRCLE_SIDES + 1 for f in circles))
    check("zones: keys unique",
          len({f["properties"]["key"] for f in fc["features"]}) == len(fc["features"]))
    check("zones: every zone carries its Thai and its English",
          all(f["properties"]["th"] and f["properties"]["en"] for f in fc["features"]))
    # First match wins, boxes before circles: the order IS the classifier, and
    # a layer that renumbers it disagrees with the shelf it is explaining.
    order = [f["properties"]["order"] for f in fc["features"]]
    check("zones: order is 0..19 in file order, boxes first",
          order == list(range(len(fc["features"])))
          and all(f["properties"]["shape"] == "box" for f in fc["features"][:N_ZONE_BOX]))

    # A box must contain its own named anchors, which is the rule
    # importers/audit_zones.py enforces on the source. Checked here against
    # the drawn ring rather than the numbers, so a bad ring is caught too.
    src = json.loads((ROOT / "data" / "curated" / "zones.json").read_text())["cm"]
    by_key = {b["key"]: b for b in src["boxes"]}
    bad = []
    for f in boxes:
        b = by_key[f["properties"]["key"]]
        ring = f["geometry"]["coordinates"][0]
        lngs = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        if not (math.isclose(min(lngs), b["lng"][0], abs_tol=1e-5)
                and math.isclose(max(lngs), b["lng"][1], abs_tol=1e-5)
                and math.isclose(min(lats), b["lat"][0], abs_tol=1e-5)
                and math.isclose(max(lats), b["lat"][1], abs_tol=1e-5)):
            bad.append(b["key"])
    check("zones: every box ring is exactly its bounds on disk", not bad, str(bad))

    # A circle's drawn radius must be the radius claimed. mae-taeng is 45 km
    # and chomthong 60 km; a degree/radian slip would show up as kilometres.
    bad = []
    for f in circles:
        p = f["properties"]
        ring = f["geometry"]["coordinates"][0]
        want = p["r_km"] * 1000
        for lng, lat in ring[:-1]:
            got = L._metres(p["lat"], p["lng"], lat, lng)
            if abs(got - want) > want * 0.01:      # 1% of the claimed radius
                bad.append((p["key"], round(got), want))
                break
    check("zones: every circle's drawn radius is within 1% of its r_km",
          not bad, str(bad[:3]))
    return fc


# ---------------------------------------------------------------- landmarks --

def test_landmarks():
    print("landmarks — data/curated/landmarks.json via bearings_layer")
    fc = L.landmarks()
    valid_geojson("landmarks", fc)
    check(f"landmarks: {N_LANDMARKS} resolved", len(fc["features"]) == N_LANDMARKS,
          str(len(fc["features"])))
    check("landmarks: none unresolved", fc["unresolved"] == 0, str(fc["unresolved"]))
    fence("landmarks", fc)
    check("landmarks: every geometry is a Point",
          all(f["geometry"]["type"] == "Point" for f in fc["features"]))
    check("landmarks: keys unique",
          len({f["properties"]["key"] for f in fc["features"]}) == len(fc["features"]))
    props = [f["properties"] for f in fc["features"]]
    check("landmarks: every one carries kind, th, en and a reach",
          all(p.get("kind") and p.get("th") and p.get("en") and p.get("reach_m")
              for p in props))
    check("landmarks: every one names a record or an OSM element",
          all(p.get("id") or p.get("osm") for p in props))
    # A CM landmark pinned in Chiang Rai would put every bearing 150 km out
    # and still look like a map. Same check the bearings test makes, on the
    # drawn coordinate rather than the register.
    bad = []
    for f in fc["features"]:
        lng, lat = f["geometry"]["coordinates"]
        p = f["properties"]
        if p["province"] == "cm" and not (17.8 <= lat <= 20.2 and 98.0 <= lng <= 99.6):
            bad.append(p["key"])
        if p["province"] == "cr" and not (19.2 <= lat <= 20.5 and 99.3 <= lng <= 100.6):
            bad.append(p["key"])
    check("landmarks: each pin is in its own province's box", not bad, str(bad))
    # Tha Phae Gate is the origin every CM bearing measures from. If it moves,
    # every bearing on the site moves with it.
    tp = next(f for f in fc["features"] if f["properties"]["key"] == "tha-phae-gate")
    lng, lat = tp["geometry"]["coordinates"]
    check("landmarks: Tha Phae Gate is within 50 m of 18.78776, 98.99327",
          L._metres(lat, lng, 18.7877625, 98.9932697) < 50,
          f"{lat},{lng}")
    check("landmarks: Tha Phae Gate is CM's origin", tp["properties"]["origin"] is True)
    return fc


# -------------------------------------------------------------- walk bands --

def test_graph():
    print("road graph — data/road_graph.json")
    G = L.graph()
    check(f"graph: {N_GRAPH_NODES:,} junctions", len(G["nodes"]) == N_GRAPH_NODES,
          str(len(G["nodes"])))
    check(f"graph: {N_GRAPH_EDGES:,} edges", len(G["edges"]) == N_GRAPH_EDGES,
          str(len(G["edges"])))
    check("graph: one rebuilt polyline per edge", len(G["geom"]) == len(G["edges"]))
    # The delta decode is the part that fails silently: get the first pair
    # wrong and the bend lands in the Gulf of Thailand while the road still
    # draws. So every point of every rebuilt polyline is fenced to the box.
    a = G["area"]
    bad = 0
    n = 0
    for pts in G["geom"]:
        for lat, lng in pts:
            n += 1
            if not (a["s"] - 1e-4 <= lat <= a["n"] + 1e-4
                    and a["w"] - 1e-4 <= lng <= a["e"] + 1e-4):
                bad += 1
    check(f"graph: all {n:,} rebuilt points inside the crawled box", bad == 0, str(bad))
    check("graph: every polyline starts at one junction and ends at the other",
          all(G["geom"][i][0] == G["nodes"][e[0]] and G["geom"][i][-1] == G["nodes"][e[1]]
              for i, e in enumerate(G["edges"])))
    # 4.6 km/h is build.py's MODES.foot.kmh. Duplicated constants drift; this
    # is the check that says so. build.py is a 20,000-line import, so it is
    # read as text rather than imported.
    src = (ROOT / "build.py").read_text()
    check("graph: the foot speed matches build.py's planner (4.6 km/h)",
          f"foot:{{kmh:{L.WALK_KMH}" in src.replace(" ", ""),
          "not found in build.py")


def test_refusal():
    print("the refusal — outside the graph there is no band, and no circle")
    a = L.graph()["area"]
    outside = [
        ("Bangkok", 13.7563, 100.5018),
        ("Chiang Rai clock tower", 19.9105, 99.8406),
        ("Doi Suthep temple", 18.8048, 98.9217),
        ("just north of the box", a["n"] + 0.001, (a["w"] + a["e"]) / 2),
        ("just south of the box", a["s"] - 0.001, (a["w"] + a["e"]) / 2),
        ("just east of the box", (a["s"] + a["n"]) / 2, a["e"] + 0.001),
        ("just west of the box", (a["s"] + a["n"]) / 2, a["w"] - 0.001),
    ]
    for label, lat, lng in outside:
        try:
            L.walk_bands(lat, lng)
            check(f"refuses at {label}", False, "returned a band")
        except L.OutsideGraph as exc:
            # The refusal has to SAY SO — a bare exception in a log is not the
            # sentence a reader or the next session needs.
            msg = str(exc)
            check(f"refuses at {label}", True, msg.split(" — ")[0])
            if label == "Bangkok":
                check("the refusal names the box it covers",
                      "18.7567" in msg and "99.0170" in msg and "No band drawn" in msg,
                      msg)
    check("in_graph() agrees with the refusal",
          all(not L.in_graph(lat, lng) for _, lat, lng in outside))
    check("in_graph() says yes at Tha Phae Gate", L.in_graph(18.7877625, 98.9932697))


def test_bands():
    print("walk bands — 5/10/15 minutes on foot")
    got, missing = L.seeds()
    check(f"seeds: all {N_SEEDS} points of the wall are inside the box",
          len(got) == N_SEEDS and not missing, str(missing))
    check("seeds: 5 gates and 4 moat corners",
          sum(1 for s in got if s["kind"] == "gate") == 5
          and sum(1 for s in got if s["kind"] == "corner") == 4)

    # From the SEED coordinate, not the register's, because the seed is what
    # ships: seeds() carries the landmark pin already rounded to 5 decimals,
    # and 1.1 m of origin is worth an edge or two at the far rim of a band.
    # Testing the unrounded pin would check a file nobody downloads.
    tp = next(s for s in got if s["key"] == "tha-phae-gate")
    fc = L.walk_bands(tp["lat"], tp["lng"])
    valid_geojson("bands", fc)
    fence("bands", fc)
    check("bands: three rings", len(fc["features"]) == 3)
    check("bands: every geometry is a MultiLineString",
          all(f["geometry"]["type"] == "MultiLineString" for f in fc["features"]))
    bands = {f["properties"]["minutes"]: f for f in fc["features"]}
    check("bands: 5, 10 and 15 minutes", sorted(bands) == [5, 10, 15])
    check("bands: widest first in the file",
          [f["properties"]["minutes"] for f in fc["features"]] == [15, 10, 5])
    check("bands: budgets are 383, 767 and 1150 m at 4.6 km/h",
          [bands[m]["properties"]["budget_m"] for m in (5, 10, 15)] == [383, 767, 1150],
          str([bands[m]["properties"]["budget_m"] for m in (5, 10, 15)]))
    check("bands: fromMin chains 0 → 5 → 10",
          [bands[m]["properties"]["fromMin"] for m in (5, 10, 15)] == [0, 5, 10])

    # The rings are disjoint: an edge drawn in two of them is the cumulative
    # bug this layer was restructured to avoid, and it triples the file.
    seen = set()
    dup = 0
    for m in (5, 10, 15):
        for line in bands[m]["geometry"]["coordinates"]:
            k = tuple(tuple(p) for p in line)
            if k in seen:
                dup += 1
            seen.add(k)
    check("bands: no line appears in two rings", dup == 0, str(dup))

    # A 5-minute walk is not 15 minutes of street. If the rings ever come out
    # equal the Dijkstra has stopped costing anything.
    e5, e10, e15 = (bands[m]["properties"]["edges"] for m in (5, 10, 15))
    check("bands: each ring adds edges (282 / 529 / 927)",
          (e5, e10, e15) == (282, 529, 927), f"{e5}/{e10}/{e15}")
    check("bands: Tha Phae Gate reaches 282 edges in the first 5 minutes",
          e5 == 282, str(e5))
    check("bands: 1,738 edges and 70,177 m of street inside 15 minutes",
          e5 + e10 + e15 == 1738
          and abs(sum(bands[m]["properties"]["street_m"] for m in (5, 10, 15)) - 70177) < 5,
          str(e5 + e10 + e15))

    # THE SHAPE IS NOT A CIRCLE, and this is the check that proves it rather
    # than asserting it: the straight-line budget for 15 minutes is 1,150 m,
    # so a circle would fill that disc. Count how much of the disc the band
    # actually reaches, in 16 sectors.
    lat0, lng0 = tp["lat"], tp["lng"]
    sectors = set()
    far = 0
    for f in fc["features"]:
        for line in f["geometry"]["coordinates"]:
            for lng, lat in line:
                d = L._metres(lat0, lng0, lat, lng)
                if d > 1150:
                    far += 1
                sectors.add(int((math.degrees(math.atan2(lng - lng0, lat - lat0)) + 360) % 360 // 22.5))
    check("bands: no drawn point further than the straight-line budget",
          far == 0, f"{far} points beyond 1,150 m")
    check("bands: the walk reaches into every one of the 16 compass sectors",
          len(sectors) == 16, str(sorted(sectors)))

    index, per = L.wall_bands()
    check(f"wall bands: {N_SEEDS} seeds in the index", len(index["features"]) == N_SEEDS)
    check("wall bands: one ring file per seed, three rings each",
          len(per) == N_SEEDS and all(len(v["features"]) == 3 for v in per.values()))
    check("wall bands: every index point names its file",
          all(f["properties"]["file"] == L.band_file(f["properties"]["seed"])
              for f in index["features"]))
    fence("wall band index", index)
    for k, v in per.items():
        valid_geojson(f"wall bands/{k}", v)
    # The nine are not nine copies of one answer: the wall is 1.6 km across
    # and the network is not the same on both sides of it.
    fives = {k: v["features"][-1]["properties"]["edges"] for k, v in per.items()}
    check("wall bands: the nine seeds give nine different 5-minute reaches",
          len(set(fives.values())) >= 8, str(sorted(fives.values())))


# --------------------------------------------------------------------- emit --

def test_emit():
    print("emit — what lands in docs/data/")
    import tempfile
    d = Path(tempfile.mkdtemp())
    status = L.emit({"DOCS": d})
    print("   ", status)
    files = sorted(p.name for p in (d / "data").iterdir())
    want = ["landmarks.geojson", "sois.geojson", "walk-bands.geojson", "zones.geojson"]
    check("emit: writes the four named layers", all(w in files for w in want), str(files))
    check(f"emit: writes one ring file per seed ({N_SEEDS})",
          sum(1 for f in files if f.startswith("walk-bands-")) == N_SEEDS)
    check("emit: says what it wrote", "sois 534" in status and "landmarks 68" in status,
          status)
    check("emit: skips nothing on this disk", "SKIPPED" not in status, status)
    for name in files:
        blob = (d / "data" / name).read_text()
        check(f"emit: {name} parses as JSON and keeps Thai as Thai",
              json.loads(blob)["type"] == "FeatureCollection" and "\\u0e" not in blob)
    # Weight is a live constraint here (test_page_weight.py, the index split).
    # The four files a map loads before anybody taps anything.
    base = sum((d / "data" / n).stat().st_size for n in want)
    check("emit: the always-loaded four are under 512 kB",
          base < 512 * 1024, f"{base / 1024:.1f} kB")
    # sois.geojson is the biggest at 368 kB — 8,494 points is what 534 real
    # streets cost, and there is nothing to trim that is not geometry. The
    # bound is there to notice growth, not to promise a number.
    biggest = max(files, key=lambda n: (d / "data" / n).stat().st_size)
    size = (d / "data" / biggest).stat().st_size
    check("emit: the biggest file is sois.geojson, under 400 kB",
          biggest == "sois.geojson" and size < 400 * 1024,
          f"{biggest} {size / 1024:.1f} kB")
    # 4 layers + 9 seed files. Nothing else, and nothing outside the scratch
    # DOCS it was handed: emit() writes through g["DOCS"] and nowhere else.
    check(f"emit: exactly {4 + N_SEEDS} files, all under the scratch DOCS",
          len(files) == 4 + N_SEEDS
          and sorted(p.name for p in d.iterdir()) == ["data"], str(len(files)))


def main():
    test_sois()
    test_zones()
    test_landmarks()
    test_graph()
    test_refusal()
    test_bands()
    test_emit()
    print()
    if FAILED:
        print(f"{len(FAILED)} FAILED:")
        for f in FAILED:
            print("  -", f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
