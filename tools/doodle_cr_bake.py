#!/usr/bin/env python3
"""The ground under the Chiang Rai doodle map (docs/sites/doodle-chiang-rai/data/).

Nan, 2026-10-03: "Can you make one of these for Chiang Rai?" — from the city to Mae Sai,
the Golden Triangle and Chiang Khong, with the far banks of the Sai and the Mekong.
The Chiang Mai doodle map borrows The City, Live's ground; Chiang Rai's reaches past it,
so this bakes the same files (land.json, roads.json, roadnames.json, labels.json, in the
same encoding) straight from the basemap archive on disk, assets/tiles/cm-cr.pmtiles.

    python3 tools/doodle_cr_bake.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import map_ground  # noqa: E402

OUT = ROOT / "docs" / "sites" / "doodle-chiang-rai" / "data"
REGION = (19.70, 99.66, 20.48, 100.46)            # S, W, N, E
TOWNS = {                                         # where the lanes are drawn too
    "chiang-rai": (19.86, 99.78, 19.96, 99.90),
    "mae-sai": (20.40, 99.85, 20.45, 99.91),
    "chiang-saen": (20.25, 100.06, 20.37, 100.11),
    "chiang-khong": (20.23, 100.38, 20.29, 100.43),
    "mae-salong": (20.15, 99.60, 20.18, 99.64),
}
E5 = 100000
CLASS = {"motorway": "major", "trunk": "major", "primary": "major", "secondary": "major",
         "motorway_link": "major", "trunk_link": "major", "primary_link": "major", "secondary_link": "major",
         "tertiary": "mid", "tertiary_link": "mid", "unclassified": "mid",
         "residential": "minor", "living_street": "minor", "pedestrian": "minor"}
POLY = {"park": "park", "garden": "park", "golf_course": "park", "zoo": "park", "nature_reserve": "park",
        "university": "campus", "college": "campus", "aerodrome": "air"}
POI = {"peak": "peak", "water": "water", "park": "park", "national_park": "wood", "aerodrome": "air", "attraction": "sight"}
# the towns and the far banks, lettered large
PLACES = [
    ("town", "เมืองเชียงราย", "Chiang Rai", 19.9105, 99.8406),
    ("town", "แม่สาย", "Mae Sai", 20.4290, 99.8830),
    ("town", "เชียงแสน", "Chiang Saen", 20.2760, 100.0850),
    ("town", "เชียงของ", "Chiang Khong", 20.2610, 100.4060),
    ("town", "แม่จัน", "Mae Chan", 20.1440, 99.8530),
    ("town", "สบรวก", "Sop Ruak", 20.3540, 100.0830),
    ("town", "ท่าขี้เหล็ก", "Tachileik", 20.4480, 99.8800),
    ("town", "ห้วยทราย", "Huay Xai", 20.2760, 100.4180),
    ("town", "ต้นผึ้ง", "Ton Pheung", 20.3700, 100.1050),
    ("country", "เมียนมา", "MYANMAR", 20.4650, 99.9900),
    ("country", "ลาว", "LAOS", 20.4300, 100.2400),
    ("country", "ไทย", "THAILAND", 20.1000, 100.1500),
]


def dp(pts, eps):
    """Douglas–Peucker on integer points."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1
    i, dmax = 0, -1
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + x1 * y0 - y1 * x0) / n
        if d > dmax:
            i, dmax = k, d
    if dmax <= eps:
        return [pts[0], pts[-1]]
    return dp(pts[:i + 1], eps)[:-1] + dp(pts[i:], eps)


def enc(pts):
    e = list(pts[0])
    for (a, b), (c, d) in zip(pts, pts[1:]):
        e += [c - a, d - b]
    return e


def q(r):
    return [(round(lat * E5), round(lng * E5)) for lng, lat in r]


def area_m2(r):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]):
        a += x0 * y1 - x1 * y0
    return abs(a) / 2 * 111320 ** 2 * math.cos(math.radians(20))


def main():
    g = map_ground.Ground()
    if not g.available:
        sys.exit("no basemap archive")
    OUT.mkdir(parents=True, exist_ok=True)
    roads = {"major": [], "mid": [], "minor": []}
    names, feats, labels, runways = [], {"water": [], "park": [], "campus": [], "air": []}, [], []
    rivers = []                                   # [width in metres, encoded line]: the polygons arrive cut at tile edges
    seen = set()

    def take_roads(d, allow_minor):
        for p, gt, rs in d.get("roads", []):
            if gt != 2:
                continue
            if p.get("kind") == "aeroway" and p.get("kind_detail") == "runway":
                runways.extend(enc(q(r)) for r in rs if len(r) > 1)
                continue
            cls = CLASS.get(p.get("kind_detail"))
            if not cls or (cls == "minor" and not allow_minor):
                continue
            for r in rs:
                pts = dp(q(r), 3 if cls != "minor" else 4)
                key = (cls, pts[0], pts[-1])
                if len(pts) < 2 or key in seen:
                    continue
                seen.add(key)
                roads[cls].append(enc(pts))
                if cls != "minor" and p.get("name") and len(pts) >= 2:
                    L = sum(math.hypot(c - a, d - b) for (a, b), (c, d) in zip(pts, pts[1:]))
                    if L > 150:
                        names.append([p["name"], p.get("name:en") or "", 1 if cls == "major" else 2, enc(pts)])

    def take_polys(d, floor):
        for src in ("water", "landuse"):
            for p, gt, rings in d.get(src, []):
                if gt != 3:
                    continue
                k = p.get("kind")
                cls = ("water" if k in ("water", "river", "canal", "lake", "reservoir", "riverbank") else None) if src == "water" else POLY.get(k)
                if not cls:
                    continue
                rings = [r for r in rings if len(r) >= 3 and area_m2(r) >= (floor if cls != "water" else floor / 4)]
                er = []
                for r in rings:
                    pts = q(r)
                    if len(pts) > 3:
                        h = len(pts) // 2
                        pts = dp(pts[:h + 1], 4)[:-1] + dp(pts[h:] + [pts[0]], 4)[:-1]
                    if len(pts) >= 3:
                        er.append(enc(pts))
                if er and (cls, tuple(er[0][:4])) not in seen:
                    seen.add((cls, tuple(er[0][:4])))
                    feats[cls].append(er)

    WIDE = {"mekong": 420, "mekong river": 420, "kok river": 110, "mae nam kok": 110, "ruak river": 45, "mae sai river": 40,
            "sai river": 40, "kham river": 30, "mae nam kham": 30, "nam mae chan": 25, "mae lao river": 30, "ing river": 40}

    def take_rivers(d):
        for p, gt, rs in d.get("water", []):
            if gt != 2 or p.get("kind") not in ("river", "canal"):
                continue
            nm = (p.get("name:en") or p.get("name") or "").lower()
            wdt = WIDE.get(nm, 14 if p.get("kind") == "river" else 6)
            for r in rs:
                pts = dp(q(r), 4)
                key = ("riv", pts[0], pts[-1])
                if len(pts) >= 2 and key not in seen:
                    seen.add(key); rivers.append([wdt, enc(pts)])

    def take_pois(d):
        for p, gt, rs in d.get("pois", []):
            cls = POI.get(p.get("kind"))
            if not cls or not p.get("name") or not rs or not rs[0] or (p["name"], cls) in seen:
                continue
            seen.add((p["name"], cls))
            lng, lat = rs[0][0]
            labels.append({"k": cls, "th": p["name"], "en": p.get("name:en") or "", "lat": round(lat, 5), "lng": round(lng, 5),
                           **({"ele": p["elevation"]} if p.get("elevation") else {})})

    # the whole region in tiles of about 0.2°, the main roads and the big water
    s, w, n, e = REGION
    la = s
    while la < n:
        ln = w
        while ln < e:
            box = (la, ln, min(n, la + 0.2), min(e, ln + 0.2))
            d = g.fetch(box, 12, ("roads", "water", "landuse", "pois"))
            take_roads(d, False); take_polys(d, 2e5); take_pois(d); take_rivers(d)
            ln += 0.2
        la += 0.2
    # the towns, closer: the middle roads, the lanes, the small water and parks
    for t, box in TOWNS.items():
        d = g.fetch(box, 14, ("roads", "water", "landuse", "pois"))
        take_roads(d, True); take_polys(d, 3000); take_pois(d)
        print(t, {k: len(v) for k, v in roads.items()})

    dump = lambda obj, f: (OUT / f).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    src = "OpenStreetMap contributors (ODbL), via the Protomaps basemap archive"
    dump({"scale": E5, "source": src, **roads}, "roads.json")
    dump({"scale": E5, "source": src, "roads": sorted(names, key=lambda r: r[2])}, "roadnames.json")
    dump({"scale": E5, "source": src, "feats": feats, "wide": {"water": []}, "rivers": rivers, "runways": runways, "labels": labels,
          "shields": [], "ground": {}}, "land.json")
    dump([{"k": k, "th": th, "en": en, "lat": la_, "lng": ln_} for k, th, en, la_, ln_ in PLACES], "labels.json")
    for f in ("roads.json", "roadnames.json", "land.json", "labels.json"):
        print(f, (OUT / f).stat().st_size)


if __name__ == "__main__":
    main()
