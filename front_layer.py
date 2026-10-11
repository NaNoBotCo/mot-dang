#!/usr/bin/env python3
"""The front page (Nan, 2026-09-30: "Replace current homepage with this new design
version + calendar enrichment. We'll refine more later on").

    now    — the live city, /sites/city-live/?embed=1
    sky    — the view west from Tha Phae Gate, drawn this minute, with the
             forecast in plain view: the next 24 hours of rain, three days, the air
    near   — Nan's field photos, nearest to the reader first
    soon   — the calendar: events ranked by nearness, completeness, what this
             reader has opened before (kept in their own browser) and what readers
             opened in the last 30 days (the map beacon's `open` rows, key ev:…)
    sites  — minisites with a picture from inside each
    drawer — search, every shelf, the rest

The page is a template (assets/front/index.html) and one script
(assets/front/front.js); everything it shows is baked here into docs/front/
and docs/sites/city-live/data/, or read live from docs/data/*.json.

home_next.py keeps rendering, to /home-classic.html, so the way back is
home_next_page() in build.py returning home_next.render() again.

Standalone:  python3 front_layer.py [--docs DIR] [--no-thumbs] [--no-interest]
"""
import collections
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
import datetime as dt
from pathlib import Path

import doodles_layer
import thaitime

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets" / "front"
THUMB_CACHE = ROOT / "cache" / "front_thumbs"
INTEREST = ROOT / "data" / "event_interest.json"
Q = 10000


def _j(p):
    return json.load(open(p))


def _dump(obj, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def _index(docs):
    for p in (docs / "api/v1/index.json", DOCS / "api/v1/index.json"):
        if p.exists():
            return _j(p)
    raise FileNotFoundError("api/v1/index.json")


# ---------------------------------------------------------------- the live map's layers

# the kinds a reader can switch on over the city map (Nan, 2026-10-02: "turn on dots in
# categories that interest you (e.g. spirit houses, hotels)"); the first ten keep the ids
# the map already knew, so a lamps.json from before reads the same
GROUPS = ["food", "cafe", "night", "market", "care", "shop", "wat", "stay", "health", "other",
          "shrine", "sights", "transport", "repair", "school", "sport"]
CAT_GROUP = {
    "food": "food", "market": "market", "whats-on": "night", "hotel": "stay",
    "beauty": "care", "massage": "care", "tattoo": "care",
    "essentials": "shop", "shopping": "shop", "cannabis": "shop", "pets": "shop",
    "repair": "repair", "home-services": "repair",
    "wat": "wat", "sights": "sights", "museums-galleries": "sights", "parks": "sights", "chang": "sights",
    "medical": "health", "transport": "transport", "school": "school", "cooking": "school",
    "sport": "sport", "muaythai": "sport",
}
_SHRINE = re.compile(r"ศาลพระภูมิ|ศาลเจ้า|ศาลเจ้าที่|หอเจ้าที่|spirit house|shrine", re.I)
CONF = ["field", "official", "register", "curated", "crawled", "third-party"]


def _group(r):
    cats, subs = r.get("cat") or [], set(r.get("sub") or [])
    if "shrine" in subs or _SHRINE.search((r.get("name") or "") + " " + (r.get("nameEn") or "")):
        return "shrine"
    if subs & {"cafe", "coffee", "coffee-shop", "bakery"}:
        return "cafe"
    if subs & {"bar", "pub", "nightclub", "live-music", "beer"}:
        return "night"
    return CAT_GROUP.get(cats[0] if cats else "", "other")


def bake_map(docs, ix):
    """lamps.json first paint; specks.json 22 m grid; names.json on first tap;
    roads, rivers and TomTom hexes. The page is /sites/city-live/."""
    out = docs / "sites/city-live/data"
    rows = [r for r in ix["places"] if r.get("lat") is not None]
    base = (round(min(r["lat"] for r in rows) - 0.001, 4), round(min(r["lng"] for r in rows) - 0.001, 4))
    q = lambda v, b: round((v - b) * Q)
    lampr = sorted([r for r in rows if r.get("sched") is not None], key=lambda r: -(r.get("antRank") or 0))
    speck = [r for r in rows if r.get("sched") is None]
    flat = []
    for r in lampr:
        flat += [q(r["lat"], base[0]), q(r["lng"], base[1]), GROUPS.index(_group(r)), r["sched"]]
    conf = collections.Counter(r["confidence"] for r in rows)
    _dump({"generated": ix["generated"], "count_all": ix["count"], "count": len(rows), "lamps": len(lampr),
           "base": base, "q": Q, "groups": GROUPS, "conf": CONF,
           "conf_counts": {k: conf.get(k, 0) for k in CONF}, "schedules": ix["schedules"], "p": flat},
          out / "lamps.json")
    pts = sorted({(q(r["lat"], base[0]) // 2, q(r["lng"], base[1]) // 2) for r in speck})
    dl = [pts[0][0]] + [pts[i][0] - pts[i - 1][0] for i in range(1, len(pts))]
    dg = [pts[i][1] - (pts[i - 1][1] if i and pts[i][0] == pts[i - 1][0] else 0) for i in range(len(pts))]
    _dump({"base": base, "q": Q // 2, "n": len(speck), "lat": dl, "lng": dg}, out / "specks.json")
    _dump([_nm(r) for r in lampr], out / "names.json")
    _kinds(out, rows, base, q)
    _labels(out)
    if not (out / "roads.json").exists() or not (out / "ground.json").exists():
        _roads_ground(out)
    if not (out / "roadnames.json").exists():
        _roadnames(out)
    if not (out / "land.json").exists():
        _land(out)
    _read_land_roads(out)
    return len(lampr), len(speck)


# ---------------------------------------------------------------- one name, both scripts
# Nan, 2026-10-03: "we should be actively transliterating place names in motdang.net so
# our maps show up well in both languages." The map names a place in the reader's one
# language, so a place whose name is written in one script only went unnamed in the other. Each name row now carries, as its fourth field,
# the name read in the script it lacks: translit.reading() (RTGS) for a Thai-only name,
# thaiscript.reading() for a Latin-only one. A reading, beside the name: city.js draws it
# where the name is missing and the tap card labels it อ่านว่า / reads.
_THAI = re.compile(r"[\u0e00-\u0e7f]")


def _reading(th, en=""):
    """The name read in the script it lacks, or ''."""
    import translit
    import thaiscript
    th, en = th or "", en or ""
    has_latin = (en and not _THAI.search(en)) or (th and not _THAI.search(th))
    has_thai = _THAI.search(th) or _THAI.search(en)
    if has_latin and has_thai:
        return ""
    if has_thai:
        t = th if _THAI.search(th) else en
        latin = re.sub(r"\s+", " ", re.sub(r"[\u0e00-\u0e7f]+|[\[\(][^\]\)]*[\]\)]", " ", t)).strip(" -–·,|/")
        if len(re.findall(r"[A-Za-z]{2,}", latin)) >= 2:
            return latin                  # a mixed name's own Latin half: Colab Cowork & Cafe
        if t.startswith("ถนน"):
            rest = translit.title(t[3:].strip())
            return rest + " Road" if rest else ""
        return translit.reading(t)
    return thaiscript.reading(th or en)


def _nm(r):
    row = [r["name"], r.get("nameEn") or "", r["province"] + "/p/" + r["slug"]]
    rd = _reading(row[0], row[1])
    return row + [rd] if rd else row


def _read_land_roads(out):
    """The same for land.json's names (enr / thr) and roadnames.json (row[4]), which are baked rarely."""
    p = out / "land.json"
    if p.exists():
        d = _j(p)
        for r in d.get("labels", []):
            r.pop("enr", None)
            r.pop("thr", None)
            rd = _reading(r.get("th") or "", r.get("en") or "")
            if rd:
                r["thr" if _THAI.search(rd) else "enr"] = rd
        _dump(d, p)
    p = out / "roadnames.json"
    if p.exists():
        d = _j(p)
        for row in d.get("roads", []):
            del row[4:]
            if not row[1] or _THAI.search(row[1]):
                rd = _reading(row[0])
                if rd:
                    row.append(rd)
        _dump(d, p)


# ---------------------------------------------------------------- the land under the lamps
# Nan, 2026-10-03: the hero map "looks weak. Not descriptive enough. Not enough landmarks.
# Not enough callouts and orientation. Moat should be blue. There should be green areas
# for parks. More map looking." So the map gets the ground a printed map has: water as
# water (the moat a blue ring), parks green, the forested hills a softer green, the
# airport and the campuses tinted, the relief of the mountains shaded, road numbers in
# shields and the named lakes, parks and peaks. All of it from the two archives already
# on disk (assets/tiles/cm-cr.pmtiles, cm-cr-terrain.pmtiles); baked once, when missing.
#
# Shapes the eye reads at a glance (water, parks, campuses, the airport) travel as
# polygons in land.json, so they stay sharp as the map closes in. The forest and the
# relief are soft by nature and would cost megabytes as polygons, so each frame gets
# one small picture of them: ground-<frame>.png, red = how forested, green = relief
# (128 flat, darker in shadow, lighter facing the light from the north-west).
LAND_FRAMES = {               # S, W, N, E; zoom of the vector tiles; zoom of the relief; picture width
    "cm": ((18.52, 98.72, 19.08, 99.28), 13, 12, 1000),
    "cr": ((19.72, 99.62, 20.10, 100.04), 13, 12, 900),
    "north": ((16.9, 97.4, 20.6, 100.9), 9, 9, 1000),
}
_POLY = {"park": "park", "garden": "park", "golf_course": "park", "zoo": "park", "pitch": "park",
         "village_green": "park", "recreation_ground": "park", "playground": "park", "cemetery": "park",
         "university": "campus", "college": "campus", "hospital": "campus", "school": "campus",
         "aerodrome": "air"}
_WOOD = {"wood", "forest", "scrub", "nature_reserve", "grassland", "meadow"}
_LABEL_POI = {"peak": "peak", "water": "water", "park": "park", "zoo": "park", "national_park": "wood",
              "aerodrome": "air", "attraction": "sight"}


def _land(out):
    """land.json + ground-<frame>.png: see the note above LAND_FRAMES."""
    import map_ground
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    g = map_ground.Ground()
    if not g.available:
        return 0
    E5, CO = 100000, math.cos(math.radians(19))
    feats = {"water": [], "park": [], "campus": [], "air": []}
    runways, labels, seen, ground, wide_water = [], [], set(), {}, []

    def enc(pts):
        e = list(pts[0])
        for (a, b), (c, d) in zip(pts, pts[1:]):
            e += [c - a, d - b]
        return e

    def enc_ring(r, eps):
        pts = [(round(lat * E5), round(lng * E5)) for lng, lat in r]
        if len(pts) > 3:                  # a closed ring: simplify its two halves
            h = len(pts) // 2
            pts = _dp(pts[:h + 1], eps)[:-1] + _dp(pts[h:] + [pts[0]], eps)[:-1]
        return enc(pts) if len(pts) >= 3 else None

    def area_m2(r):
        a = 0.0
        for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]):
            a += x0 * y1 - x1 * y0
        return abs(a) / 2 * 111320 ** 2 * CO

    for frame, (bbox, z, zr, width) in LAND_FRAMES.items():
        wide = frame == "north"
        s, w, n, e = bbox
        d = g.fetch(bbox, z, ("water", "landuse", "landcover", "roads", "pois"))
        # the forest, painted 3x and shrunk so its edges are soft
        hgt = round(width * (n - s) / ((e - w) * CO))
        ss = 3
        wood = Image.new("L", (width * ss, hgt * ss), 0)
        wd = ImageDraw.Draw(wood)
        sx, sy = width * ss / (e - w), hgt * ss / (n - s)
        for p, gt, rings in d.get("landuse", []) + d.get("landcover", []):
            if gt != 3:
                continue
            k = p.get("kind")
            if k in _WOOD or (k in ("forest", "grassland", "scrub") and "kind_detail" not in p):
                for i, r in enumerate(rings):
                    if len(r) < 3:
                        continue
                    pts = [((lng - w) * sx, (n - lat) * sy) for lng, lat in r]
                    hole = i and map_ground._area([(x, y) for x, y in pts]) < 0
                    wd.polygon(pts, fill=0 if hole else 255)
        wood = wood.resize((width, hgt), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.4))
        relief = _relief(bbox, zr, width, hgt)
        gimg = np.zeros((hgt, width, 3), dtype=np.uint8)
        gimg[..., 0] = np.asarray(wood)
        gimg[..., 1] = relief
        name = "ground-" + frame + ".jpg"
        Image.fromarray(gimg, "RGB").save(out / name, "JPEG", quality=55, subsampling=0, optimize=True)
        ground[frame] = {"src": name, "bbox": [s, w, n, e]}

        eps, floor = (25, 2e6) if wide else (4, 2500)
        for src, p, gt, rings in [("water", *x) for x in d.get("water", [])] + \
                                 [("land", *x) for x in d.get("landuse", [])]:
            if gt != 3:
                continue
            k = p.get("kind")
            cls = ("water" if k in ("water", "river", "canal", "lake", "reservoir") else None) if src == "water" \
                else _POLY.get(k)
            if not cls or (wide and cls != "water"):
                continue
            # the town itself in full; the hills and fields keep only what reads from afar
            core = any(abs(r[0][1] - (s + n) / 2) < 0.09 and abs(r[0][0] - (w + e) / 2) < 0.09 for r in rings if r)
            # the moat is many narrow pieces, each a few hundred square metres
            least = (300 if cls == "water" else floor) if core else floor * 12
            rings = [r for r in rings if len(r) >= 3]
            if wide or not core:
                if max((area_m2(r) for r in rings), default=0) < least:
                    continue
            else:
                rings = [r for r in rings if area_m2(r) >= least]
                if not rings:
                    continue
            er = [x for x in (enc_ring(r, eps if core else eps * 2.5) for r in rings) if x]
            if not er or (cls, tuple(er[0][:4])) in seen:
                continue
            seen.add((cls, tuple(er[0][:4])))
            (wide_water if wide else feats[cls]).append(er)
        if not wide:
            for p, gt, rs in d.get("roads", []):
                if p.get("kind") == "aeroway" and p.get("kind_detail") == "runway" and gt == 2:
                    runways += [enc([(round(lat * E5), round(lng * E5)) for lng, lat in r]) for r in rs if len(r) > 1]
        for p, gt, rs in d.get("pois", []):
            cls = _LABEL_POI.get(p.get("kind"))
            if not cls or not p.get("name") or not rs or not rs[0] or (p["name"], cls) in seen:
                continue
            seen.add((p["name"], cls))
            lng, lat = rs[0][0]
            labels.append({"k": cls, "th": p["name"], "en": p.get("name:en") or "", "lat": round(lat, 5),
                           "lng": round(lng, 5), "z": p.get("min_zoom", 14),
                           **({"ele": p["elevation"]} if p.get("elevation") else {})})
    # the wide frame's lakes are drawn only when far out

    # shields: each numbered highway, a point every ~1.2 km along it; tier 0 every fourth
    import glob
    nodes, ways = {}, {}
    for f in sorted(glob.glob(str(ROOT / "cache/roads/*.json")) + glob.glob(str(ROOT / "cache/roads/wide/*.json"))):
        for el in _j(f).get("elements", []):
            if el["type"] == "node":
                nodes[el["id"]] = (el["lat"], el["lon"])
            elif el["type"] == "way":
                ways[el["id"]] = el
    shields, placed = [], collections.defaultdict(list)
    for wy in sorted(ways.values(), key=lambda x: x["id"]):
        t = wy.get("tags", {})
        ref = (t.get("ref") or "").split(";")[0].strip()
        if not re.fullmatch(r"\d{1,4}", ref) or t.get("highway") not in ("motorway", "trunk", "primary", "secondary"):
            continue
        pts = [nodes[i] for i in wy["nodes"] if i in nodes]
        run = 0.0
        for (a, b), (c, dd) in zip(pts, pts[1:]):
            run += math.hypot(c - a, (dd - b) * CO) * 111.32
            if run < 0.6:
                continue
            run = 0.0
            if any(math.hypot(c - x, (dd - y) * CO) * 111.32 < 1.2 for x, y in placed[ref]):
                continue
            placed[ref].append((c, dd))
            shields.append([ref, round(c, 5), round(dd, 5), 0 if len(placed[ref]) % 4 == 1 else 1])

    for cls, hw, p, pts in _pm_roads():
        ref = (p.get("ref") or "").split(";")[0].strip()
        if cls != "major" or not re.fullmatch(r"\d{1,4}", ref):
            continue
        run = 0.0
        for (a, b), (c, dd) in zip(pts, pts[1:]):
            run += math.hypot(c - a, (dd - b) * CO) / E5 * 111.32
            if run < 0.6:
                continue
            run = 0.0
            la, ln = c / E5, dd / E5
            if any(math.hypot(la - x, (ln - y) * CO) * 111.32 < 1.2 for x, y in placed[ref]):
                continue
            placed[ref].append((la, ln))
            shields.append([ref, round(la, 5), round(ln, 5), 0 if len(placed[ref]) % 4 == 1 else 1])

    _dump({"scale": E5, "source": "OpenStreetMap contributors (ODbL) via Protomaps; relief SRTM via Mapzen terrain tiles",
           "feats": feats, "wide": {"water": wide_water}, "runways": runways, "labels": labels,
           "shields": shields, "ground": ground}, out / "land.json")
    return sum(len(v) for v in feats.values())


def _relief(bbox, z, width, hgt):
    """The relief of bbox as a width x hgt array: 128 flat, darker on slopes turned away
    from a light in the north-west, lighter on slopes facing it."""
    import io
    import numpy as np
    from PIL import Image
    import map_ground
    arc = map_ground._Archive(ROOT / "assets/tiles/cm-cr-terrain.pmtiles")
    s, w, n, e = bbox
    x0, y0 = map_ground.lnglat_to_tile(w, n, z)
    x1, y1 = map_ground.lnglat_to_tile(e, s, z)
    tiles, T = {}, 256
    for tx in range(int(x0), int(x1) + 1):
        for ty in range(int(y0), int(y1) + 1):
            b = arc.tile(z, tx, ty)
            if b:
                a = np.asarray(Image.open(io.BytesIO(b)).convert("RGB"), dtype=np.float64)
                T = a.shape[0]
                tiles[(tx, ty)] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    dem = np.zeros(((int(y1) - int(y0) + 1) * T, (int(x1) - int(x0) + 1) * T))
    for (tx, ty), a in tiles.items():
        dem[(ty - int(y0)) * T:(ty - int(y0) + 1) * T, (tx - int(x0)) * T:(tx - int(x0) + 1) * T] = a
    mpp = 40075016.7 * math.cos(math.radians((s + n) / 2)) / (T * 2 ** z)
    gy, gx = np.gradient(dem, mpp)
    slope = np.arctan(2.0 * np.hypot(gx, gy))
    aspect = np.arctan2(gy, -gx)
    az, alt = math.radians(315), math.radians(45)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - math.pi / 2 - aspect)
    dv = (hs - math.sin(alt)) * 260
    rel = np.clip(128 + np.sign(dv) * np.maximum(np.abs(dv) - 5, 0), 0, 255)     # the plain's SRTM grain, dropped
    # sample at the frame's plate-carrée pixels (the live map's projection)
    lats = np.linspace(n, s, hgt)
    lngs = np.linspace(w, e, width)
    ty_ = (1 - np.log(np.tan(np.radians(lats)) + 1 / np.cos(np.radians(lats))) / math.pi) / 2 * 2 ** z
    tx_ = (lngs + 180) / 360 * 2 ** z
    iy = np.clip(((ty_ - int(y0)) * T).astype(int), 0, dem.shape[0] - 1)
    ix = np.clip(((tx_ - int(x0)) * T).astype(int), 0, dem.shape[1] - 1)
    return rel[np.ix_(iy, ix)].astype(np.uint8)


def _dp(pts, eps):
    """Douglas-Peucker on integer 1e-5 degree points."""
    if len(pts) < 3:
        return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    L = (dx * dx + dy * dy) ** 0.5 or 1
    best, bi = -1, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / L
        if d > best:
            best, bi = d, i
    return [pts[0], pts[-1]] if best <= eps else _dp(pts[: bi + 1], eps)[:-1] + _dp(pts[bi:], eps)


# Chiang Rai's own road crawl on disk is a few tiles, so its roads come from the
# basemap archive (the same OpenStreetMap ways, cut into tiles); her ask 2026-10-03
CR_ROADS_BOX = (19.78, 99.70, 20.04, 99.97)
_PM_CLASS = {"motorway": "major", "trunk": "major", "primary": "major", "secondary": "major",
             "motorway_link": "major", "trunk_link": "major", "primary_link": "major", "secondary_link": "major",
             "tertiary": "mid", "tertiary_link": "mid", "unclassified": "mid", "pedestrian": "mid",
             "residential": "minor", "living_street": "minor"}


def _pm_roads(bbox=CR_ROADS_BOX, z=14):
    """[(cls, osm highway, props, [(lat5, lng5), ...]), ...] from assets/tiles/cm-cr.pmtiles."""
    import map_ground
    g = map_ground.Ground()
    if not g.available:
        return []
    out, seen = [], set()
    for p, gt, rs in g.fetch(bbox, z, ("roads",)).get("roads", []):
        cls = _PM_CLASS.get(p.get("kind_detail"))
        if gt != 2 or not cls:
            continue
        for r in rs:
            pts = [(round(lat * 1e5), round(lng * 1e5)) for lng, lat in r]
            key = (pts[0], pts[-1]) if len(pts) > 1 else None
            if key and key not in seen:
                seen.add(key)
                out.append((cls, p.get("kind_detail"), p, pts))
    return out



def _roadnames(out):
    """roadnames.json: the named main and middle roads, for the map's tool view
    (Nan, 2026-10-02: once a reader plays with the map it becomes a tool)."""
    import glob
    MAJOR = {"motorway", "trunk", "primary", "secondary"}
    MID = {"tertiary", "unclassified"}
    nodes, ways = {}, {}
    for f in sorted(glob.glob(str(ROOT / "cache/roads/*.json")) + glob.glob(str(ROOT / "cache/roads/wide/*.json"))):
        for e in _j(f).get("elements", []):
            if e["type"] == "node":
                nodes[e["id"]] = (round(e["lat"] * 1e5), round(e["lon"] * 1e5))
            elif e["type"] == "way":
                ways[e["id"]] = e
    rows = []
    for w in ways.values():
        t = w.get("tags", {})
        hw, th = t.get("highway"), t.get("name")
        if not th or hw not in MAJOR | MID:
            continue
        pts = [nodes[n] for n in w["nodes"] if n in nodes]
        if len(pts) < 2:
            continue
        L = sum(((c - a) ** 2 + (d - b) ** 2) ** 0.5 for (a, b), (c, d) in zip(pts, pts[1:]))
        if L < 120:                       # about 120 m: too short to carry a name
            continue
        pts = _dp(pts, 3)                 # ~3 m: long straight stretches carry the label
        enc = list(pts[0])
        for (a, b), (c, d) in zip(pts, pts[1:]):
            enc += [c - a, d - b]
        rows.append([th, t.get("name:en") or "", 1 if hw in MAJOR else 2, enc])
    for cls, hw, p, pts in _pm_roads():
        if cls == "minor" or not p.get("name") or len(pts) < 2:
            continue
        pts = _dp(pts, 3)
        enc = list(pts[0])
        for (a, b), (c, d) in zip(pts, pts[1:]):
            enc += [c - a, d - b]
        rows.append([p["name"], p.get("name:en") or "", 1 if cls == "major" else 2, enc])
    rows.sort(key=lambda r: r[2])
    _dump({"scale": 100000, "source": "OpenStreetMap contributors, ODbL", "roads": rows}, out / "roadnames.json")

def _kinds(out, rows, base, q):
    """k/<kind>.json: every place of one kind, most important first, read when a reader
    switches that kind on; kinds.json: how many each holds."""
    by = collections.defaultdict(list)
    for r in rows:
        by[_group(r)].append(r)
    kd = out / "k"
    kd.mkdir(parents=True, exist_ok=True)
    for f in kd.glob("*.json"):
        if f.stem not in by:
            f.unlink()
    for k, rs in by.items():
        rs.sort(key=lambda r: -(r.get("antRank") or 0))
        flat = []
        for r in rs:
            flat += [q(r["lat"], base[0]), q(r["lng"], base[1]), r["sched"] if r.get("sched") is not None else -1]
        _dump({"base": base, "q": Q, "p": flat,
               "names": [_nm(r) for r in rs]}, kd / (k + ".json"))
    _dump({"kinds": [{"id": k, "n": len(by[k])} for k in GROUPS if by.get(k)]}, out / "kinds.json")


# the names drawn on the map, by rank: lower shows from further out
_KIND_RANK = {"airport": 1, "mall": 2, "market": 2, "university": 2, "gate": 3, "temple": 3, "craft-village": 3,
              "hospital": 4, "monument": 4, "park": 4, "bridge": 4, "terminal": 4, "waterfall": 4, "corner": 6}


def _labels(out):
    """labels.json: the ย่าน of zones.json and the landmarks of docs/data/landmarks.json,
    for the city map's names (Nan, 2026-10-02: "place names should be visible")."""
    rows = []
    z = _j(ROOT / "data/curated/zones.json")["cm"]
    for b in z["boxes"]:
        rows.append({"k": "zone", "r": 0, "th": b["th"].split("-")[0], "en": re.sub(r"\s*\(.*?\)", "", b["en"]).split(" & ")[0],
                     "lat": round(sum(b["lat"]) / 2, 5), "lng": round(sum(b["lng"]) / 2, 5)})
    for c in z.get("circles", []):
        rows.append({"k": "town", "r": 1, "th": c["th"].split("-")[0], "en": c["en"].split(",")[0].split(" & ")[0],
                     "lat": c["lat"], "lng": c["lng"]})
    lm = DOCS / "data/landmarks.json"
    if not lm.exists():
        lm = ROOT / "docs/data/landmarks.json"
    for prov, xs in (_j(lm) if lm.exists() else {}).items():
        for x in xs:
            r = 1 if x["key"] in ("wat-doi-suthep", "warorot", "night-bazaar") else _KIND_RANK.get(x["kind"], 5)
            rows.append({"k": x["kind"], "r": r, "th": re.sub(r"\s*\(.*?\)", "", x["th"]),
                         "en": re.sub(r"\s*\(.*?\)", "", x["en"]), "lat": round(x["lat"], 5), "lng": round(x["lng"], 5)})
    rows.sort(key=lambda r: r["r"])
    _dump(rows, out / "labels.json")
    return len(rows)


def _roads_ground(out):
    """Roads, rivers and traffic change rarely; baked when missing."""
    import glob
    MAJOR = {"motorway", "trunk", "primary", "secondary", "motorway_link", "trunk_link", "primary_link", "secondary_link"}
    MID = {"tertiary", "tertiary_link", "unclassified", "pedestrian"}
    MINOR = {"residential", "living_street"}

    def dp(pts, eps):
        if len(pts) < 3:
            return pts
        (ax, ay), (bx, by) = pts[0], pts[-1]
        dx, dy = bx - ax, by - ay
        L = (dx * dx + dy * dy) ** 0.5 or 1
        best, bi = -1, 0
        for i in range(1, len(pts) - 1):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / L
            if d > best:
                best, bi = d, i
        return [pts[0], pts[-1]] if best <= eps else dp(pts[: bi + 1], eps)[:-1] + dp(pts[bi:], eps)

    nodes, ways = {}, {}
    for f in sorted(glob.glob(str(ROOT / "cache/roads/*.json")) + glob.glob(str(ROOT / "cache/roads/wide/*.json"))):
        for e in _j(f).get("elements", []):
            if e["type"] == "node":
                nodes[e["id"]] = (round(e["lat"] * 1e5), round(e["lon"] * 1e5))
            elif e["type"] == "way":
                ways[e["id"]] = e
    R = {"major": [], "mid": [], "minor": []}
    for w in ways.values():
        hw = w["tags"].get("highway")
        cls = "major" if hw in MAJOR else "mid" if hw in MID else "minor" if hw in MINOR else None
        pts = [nodes[n] for n in w["nodes"] if n in nodes] if cls else []
        if len(pts) < 2:
            continue
        pts = dp(pts, 5 if cls == "minor" else 2.5)
        enc = list(pts[0])
        for (a, b), (c, d) in zip(pts, pts[1:]):
            enc += [c - a, d - b]
        R[cls].append(enc)
    for cls, hw, p, pts in _pm_roads():
        if len(pts) < 2:
            continue
        pts = dp(pts, 5 if cls == "minor" else 2.5)
        enc = list(pts[0])
        for (a, b), (c, d) in zip(pts, pts[1:]):
            enc += [c - a, d - b]
        R[cls].append(enc)
    _dump({"scale": 100000, "source": "OpenStreetMap contributors, ODbL", **R}, out / "roads.json")
    g = _j(ROOT / "data/regional_ground.json")
    rivers = [{"en": r["en"], "th": r.get("th", ""), "lines": r["lines"]} for r in g["rivers"]
              if r["en"] in ("Ping", "Kok", "Mekong", "Ing", "Wang", "Nan", "Yom", "Salween", "Moei")]
    provinces = [{"rings": [[[round(a, 2), round(b, 2)] for a, b in ring] for ring in p["rings"]]}
                 for p in g["provinces"] if p.get("iso", "").startswith("TH")]
    _dump({"rivers": rivers, "provinces": provinces, "credits": g["credits"]}, out / "ground.json")
    t = _j(ROOT / "data/traffic.json")["city"]
    _dump({"source": t["source"], "hex": [[h["am"], h["pm"], [[round(y, 4), round(x, 4)] for x, y in h["ring"]]]
                                          for h in t["hex"] if max(h["am"], h["pm"]) >= 30]}, out / "traffic.json")


# ---------------------------------------------------------------- near

def _latin_t(p):
    """The English caption, with any Thai left in it read out by RTGS: "The soap house sign: เฮือนสบู่ คุณกวี"
    -> "... Hueansabu Khunkwi". No English title at all -> the Thai caption's reading."""
    import translit
    t = p.get("title") or translit.reading(p.get("description_th") or "")
    return re.sub(r"[\u0e00-\u0e7f]+(?:\s+[\u0e00-\u0e7f]+)*", lambda m: translit.reading(m.group(0)), t)


def bake_near(docs, ix, thumbs=True):
    from PIL import Image
    out = docs / "front"
    THUMB_CACHE.mkdir(parents=True, exist_ok=True)
    page = {r["id"]: r["province"] + "/p/" + r["slug"] + ".html" for r in ix["places"]}
    ph = _j(ROOT / "docs/field/data/photos.json" if (ROOT / "docs/field/data/photos.json").exists()
            else docs / "field/data/photos.json")["photos"]
    fdir = docs / "field" if (docs / "field/photos").exists() else ROOT / "docs/field"
    rows, made = [], 0
    for p in ph:
        if p.get("lat") is None or p.get("quality") == 1:
            continue
        src, th = fdir / p["file"], THUMB_CACHE / (p["slug"] + ".webp")
        if thumbs and not th.exists() and src.exists():
            im = Image.open(src).convert("RGB")
            im.thumbnail((640, 640))
            im.save(th, "WEBP", quality=58, method=5)
            made += 1
        if not th.exists():
            continue
        r = {"s": p["slug"], "la": round(p["lat"], 5), "lo": round(p["lng"], 5), "t": _latin_t(p),
             "th": p.get("description_th") or "", "q": p.get("quality") or 0, "k": p.get("subject") or "",
             "img": "field/" + p["file"], "w": p.get("width"), "h": p.get("height")}
        if p.get("placeId") in page:
            r["u"] = page[p["placeId"]]
        rows.append(r)
    hero = ROOT / "docs/site/hero/index.json"
    for h in (_j(hero) if hero.exists() else []):
        if h.get("la") is not None:
            rows.append({"s": h["slug"], "la": h["la"], "lo": h["lo"], "t": h["slug"].replace("-", " "), "th": "",
                         "q": 3, "k": "hero", "pool": h.get("pool"), "img": "site/hero/" + h["slug"] + ".webp",
                         "thumb": "site/hero/" + h["slug"] + ".webp", "w": h["w"], "h": h["h"]})
    _dump({"credit": "NaN Peacock, CC BY 4.0 (field photos)", "photos": rows}, out / "near.json")
    shutil.copytree(THUMB_CACHE, out / "thumbs", dirs_exist_ok=True)
    return len(rows), made


# ---------------------------------------------------------------- minisites and the drawer

def _og(docs, href):
    if href.startswith("http"):
        return None
    last = href.rstrip("/").split("/")[-1]
    p = docs / (href.rstrip("/") + ("/index.html" if href.endswith("/") or "." not in last else ""))
    if not p.exists():
        return None
    m = re.search(r'og:image" content="([^"]+)', p.read_text(errors="ignore"))
    u = m.group(1).replace("https://motdang.net/", "") if m else None
    return None if not u or u.split("?")[0] == "card.png" else u


def _inner_picture(docs, href):
    """The biggest photograph inside the minisite — a picture, not its share card."""
    from PIL import Image
    if href.startswith("http"):
        return None
    d = docs / href.rstrip("/")
    if not d.is_dir():
        return None
    best = None
    for f in list(d.glob("*.jpg")) + list(d.glob("img/*.jpg")) + list(d.glob("assets/*.jpg")) + list(d.glob("photos/*.jpg")):
        if "card" in f.name.lower() or f.name.lower().startswith(("og", "poster", "icon")):
            continue
        try:
            w, h = Image.open(f).size
        except Exception:
            continue
        if w >= 900 and w >= h * 0.9 and (best is None or f.stat().st_size > best[0]):
            best = (f.stat().st_size, f)
    if best is None and (d / "index.html").exists():
        for src in re.findall(r'<img[^>]+src="([^"]+\.(?:jpg|jpeg|webp))"', (d / "index.html").read_text(errors="ignore")):
            f = (docs / src.lstrip("/")) if src.startswith("/") else (d / src)
            if f.exists() and "card" not in f.name:
                try:
                    w, _ = Image.open(f).size
                except Exception:
                    continue
                if w >= 700 and (best is None or f.stat().st_size > best[0]):
                    best = (f.stat().st_size, f)
    return str(best[1].resolve().relative_to(docs.resolve())) if best else None


def bake_sites(docs):
    reg = _j(ROOT / "data/curated/sites.json")
    cards = list(reg["cards"])
    for cj in (ROOT / "assets/sites").glob("*/card.json"):
        c = _j(cj)
        c.setdefault("href", "sites/%s/" % cj.parent.name)
        c.setdefault("id", cj.parent.name)
        if not any(x["id"] == c["id"] for x in cards):
            cards.append(c)
    import sites_layer
    pics, plain = [], []
    for c in cards:
        if c["id"] == "city-live":
            continue
        when = sites_layer.timing(c)
        if when == "out":
            continue
        if c.get("picture"):  # a file in assets/front/pics/ chosen for the tile, credit in picture_by
            (docs / "front/pics").mkdir(parents=True, exist_ok=True)
            shutil.copy(ASSETS / "pics" / c["picture"], docs / "front/pics" / c["picture"])
            img = pic = "front/pics/" + c["picture"]
        else:
            img = _og(docs, c["href"])
            pic = _inner_picture(docs, c["href"]) if img else None
        row = {"id": c["id"], "href": c["href"], "th": c["th"], "en": c["en"], "lth": c.get("line_th", ""),
               "len": c.get("line_en", ""), "d": c.get("shipped"), "img": pic or img,
               "card": not pic and bool(re.search(r"(card|/og/)", img or "")),
               "now": when == "now", "u": c.get("until"), "on": c.get("on"), "by": c.get("picture_by")}
        (pics if img else plain).append(row)
    # what is on now leads, soonest to end first; then the newest
    pics.sort(key=lambda r: r["d"] or "", reverse=True)
    pics.sort(key=lambda r: (not r["now"], r["u"] or "9999"))
    _dump(pics, docs / "front/sites.json")
    cats = _j(ROOT / "data/categories.json")["categories"]
    _dump({"shelves": [{"k": c["key"], "th": c["th"], "en": c["en"]} for c in cats], "more": plain},
          docs / "front/drawer.json")
    t = _j(ROOT / "data/terrain_profile.json")
    _dump({k: t[k] for k in ("lat", "lon_a", "lon_b", "step", "tick", "ele", "read")}, docs / "front/ridge.json")
    return len(pics), len(plain)


# ---------------------------------------------------------------- the calendar

CATS = [  # key, th, en, words — checked in order; the first two catch what the later ones would misfile
    ("art", "ศิลปะ", "Art & film", r"exhibit|gallery|museum|film|cinema|screening|นิทรรศการ"),
    ("social", "พบปะ", "Meet people", r"comedy|stand-?up|quiz|trivia"),
    ("music", "ดนตรี", "Music", r"music|jazz|band\b|concert|live |dj\b|sing|song|acoustic|open mic|karaoke|choir|guitar|ดนตรี|เพลง"),
    ("dance", "เต้นรำ", "Dance", r"salsa|bachata|danc|tango|swing|latin|zouk|kizomba|ballroom|เต้น"),
    ("wellness", "ใจและกาย", "Wellness", r"yoga|meditat|sound bath|breath|qigong|tai chi|reiki|holistic|healing|pilates|mindful|โยคะ|สมาธิ"),
    ("sport", "กีฬา", "Sport", r"\brun\b|running|crossfit|fitness|workout|bootcamp|hik|cycling|padel|tennis|football|futsal|climb|muay|boxing|golf|swim|กีฬา|วิ่ง"),
    ("art", "ศิลปะ", "Art & film", r"exhibit|\bart\b|arts\b|gallery|painting|drawing|photograph|film|cinema|screening|theat|craft|นิทรรศการ|ศิลปะ"),
    ("learn", "เรียนรู้", "Learning", r"workshop|class|course|lecture|talk|lesson|seminar|language|learning|study|เวิร์กช็อป|เรียน"),
    ("food", "กินดื่ม", "Food & drink", r"brunch|dinner|lunch|food|wine|beer|tasting|cooking|bbq|buffet|cocktail|coffee|อาหาร"),
    ("market", "ตลาด", "Markets", r"market|bazaar|\bfair\b|flea|ตลาด|กาด"),
    ("social", "พบปะ", "Meet people", r"meetup|social|quiz|trivia|board game|bridge|chess|networking|expat|club|mixer|games? night|party"),
    ("faith", "วัดและศรัทธา", "Faith", r"temple|\bwat\b|buddhis|dhamma|church|mass\b|prayer|ceremony|วัด|ทำบุญ"),
    ("family", "ครอบครัว", "Family", r"kids|children|family|เด็ก"),
]
OTHER = ("other", "อื่น ๆ", "Other")
AREAS = [  # th, en, lat, lng — the reader's own words for a part of town
    ("เมืองเก่า", "Old City", 18.7883, 98.9853), ("นิมมาน", "Nimman", 18.7996, 98.9675),
    ("ท่าแพ", "Tha Phae", 18.7877, 98.9931), ("ไนท์บาซาร์", "Night Bazaar", 18.7856, 99.0003),
    ("ริมปิง", "Riverside", 18.7935, 99.0045), ("วัวลาย", "Wua Lai", 18.7795, 98.9855),
    ("สันติธรรม", "Santitham", 18.8035, 98.9812), ("ช้างคลาน", "Chang Khlan", 18.7745, 99.0005),
    ("มช.", "CMU", 18.8030, 98.9530), ("ช้างเผือก", "Chang Phueak", 18.8085, 98.9855),
    ("หางดง", "Hang Dong", 18.6890, 98.9250), ("สันกำแพง", "San Kamphaeng", 18.7450, 99.1200),
    ("แม่ริม", "Mae Rim", 18.9150, 98.9450), ("สันทราย", "San Sai", 18.8500, 99.0400),
    ("สารภี", "Saraphi", 18.7100, 99.0400), ("ดอยสะเก็ด", "Doi Saket", 18.8700, 99.1400),
    ("ฟ้าฮ่าม", "Fa Ham", 18.8160, 99.0080), ("หนองหอย", "Nong Hoi", 18.7630, 99.0120),
    ("เชียงราย", "Chiang Rai", 19.9105, 99.8406),
]


def _norm(s):
    s = (s or "").lower()
    s = re.sub(r"\b(chiang ?mai|cnx|cm|the|restaurant|cafe|café|bar|hotel|resort)\b", " ", s)
    return re.sub(r"[^0-9a-z฀-๿]+", "", s)


VENUE_ALIASES = ROOT / "data" / "curated" / "venue_aliases.json"
_VSTOP = {"the", "and", "of", "at", "in", "a", "an", "by", "for", "restaurant", "cafe", "café", "bar",
          "hotel", "resort", "chiang", "mai", "chiangmai", "cnx", "cm"}
# words a venue string or a place name may carry beyond the other without naming a different place
_VEXTRA = {"studio", "spa", "campus", "center", "centre", "university", "international", "school", "club",
           "education", "national"}
_RAI = re.compile(r"\brai\b|เชียงราย")


def _vkey(s):
    """The key venue_aliases.json is written in (build.py's _vnorm)."""
    s = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in (s or "").lower())
    return " ".join(s.split())


def _vtoks(s):
    """Latin words of a name that identify it; Thai has no spaces to split on."""
    s = (s or "").lower().replace("&", " and ")
    return frozenset(t for t in re.findall(r"[^\W_]+", s) if t not in _VSTOP and not re.search(r"[฀-๿]", t))


def _venue_forms(v):
    """The venue string as the calendar's sources write it, then the parts that may name the place
    on their own: before an address comma, before or after ' at ', before ' - ', outside brackets.
    A part counts only when it has two words and 7 letters once 'Chiang Mai' and the like are cut, so 'Yoga at Wat Suan Dok' never
    offers the place called 'Yoga'."""
    s = re.sub(r"\*+", "", v or "")
    s = re.sub(r"^\s*venue\s*:\s*", "", s, flags=re.I).replace("@", " at ")
    s = re.split(r"[  \r\n]", s.strip())[0].strip()
    forms, seen = [s], {s}
    bare = re.sub(r"\([^)]*\)", " ", s)
    parts = [bare]
    for b in (s, bare):
        parts += [b.split(",")[0]] + re.split(r"\s+at\s+|\s+[-–|]\s+", b, flags=re.I)
    for part in parts:
        part = " ".join(part.split()).strip(" ,.-–|")
        if part and part not in seen and len(part.split()) >= 2 and len(_norm(part)) >= 7:
            seen.add(part)
            forms.append(part)
    return forms


def venue_finder(places, aliases=None):
    """venue(name, city) -> the place record an event's venue string names, or None.
    A wrong pin is worse than none, so every step but the first is strict:
      1 the hand-kept alias (data/curated/venue_aliases.json, the table build.py's match_venue reads);
      2 the whole normalised name; 3 a prefix of 7+ letters; 4 the same on the parts of the string
      (address tail, ' at ' halves); 5 a word-set match: all of the place's words are in the venue's
      (2+ words, 8+ letters), or all of the venue's words are in the place's (3+ words), the words
      over being few and plain (studio, campus, center...), and only onto a place with a real pin; two such places over 400 m apart = no match.
    A Chiang Rai place is offered only when the venue says Rai or the row's city is cr."""
    if aliases is None:
        try:
            aliases = _j(VENUE_ALIASES).get("aliases", {})
        except (OSError, ValueError):
            aliases = {}
    by_id = {r["id"]: r for r in places}
    names = collections.defaultdict(list)
    sets = []                                   # (word set, place) for the word-set step
    post = collections.defaultdict(list)
    for r in places:
        if r.get("lat") is None:
            continue
        for nm in {r.get("name"), r.get("nameEn")}:
            k = _norm(nm)
            if len(k) >= 4:
                names[k].append(r)
            ws = _vtoks(nm)
            if len(ws) >= 2 and r.get("geoPrecision") in ("exact", "block"):
                sets.append((ws, r))
                for t in ws:
                    post[t].append(len(sets) - 1)
    keys = sorted(names, key=len, reverse=True)

    def pick(hit, rai):
        hit = [r for r in hit if (r["province"] == "cr") == rai] or None
        return max(hit, key=lambda r: (r.get("antRank") or 0)) if hit else None

    def by_alias(s):
        a = aliases.get(_vkey(s))
        r = by_id.get(a.get("place_id")) if isinstance(a, dict) else by_id.get(a) if a else None
        # a place pinned only to its district centre is not a pin the alias may add
        return r if r and r.get("lat") is not None and r.get("geoPrecision") in ("exact", "block") else None

    def by_words(s, rai):
        ws = _vtoks(s)
        if len(ws) < 2:
            return None
        cand = {}
        for t in ws:
            for i in post.get(t, ()):
                cand[i] = cand.get(i, 0) + 1
        best = []
        for i in cand:
            pw, r = sets[i]
            if (r["province"] == "cr") != rai:
                continue
            if pw <= ws:                      # the place's words all sit in the venue's string
                more, ok = ws - pw, len("".join(pw)) >= 8
            elif ws < pw:                     # the venue's words all sit in the place's name
                more, ok = pw - ws, len(ws) >= 3
            else:
                continue
            if ok and len(more) <= 2 and more <= _VEXTRA:
                best.append((len(more), -(r.get("antRank") or 0), r))
        if not best:
            return None
        near = [b for b in best if b[0] == min(x[0] for x in best)]
        if any(_km(near[0][2]["lat"], near[0][2]["lng"], b[2]["lat"], b[2]["lng"]) > 0.4 for b in near[1:]):
            return None
        return min(near, key=lambda b: b[1])[2]

    def venue(v, city=""):
        rai = bool(_RAI.search((v or "").lower())) or city == "cr"
        forms = _venue_forms(v)
        r = by_alias(forms[0])
        if r:
            return r
        k = _norm(forms[0])
        if len(k) < 4:
            return None
        hit = names.get(k)
        if not hit and len(k) >= 7:
            near = [r for kk in keys if len(kk) >= 7 and (kk.startswith(k) or k.startswith(kk)) for r in names[kk]
                    if (r["province"] == "cr") == rai]
            if near and all(_km(near[0]["lat"], near[0]["lng"], r["lat"], r["lng"]) <= 0.4 for r in near):
                hit = near
        r = pick(hit, rai) if hit else None
        if r:
            return r
        for f in forms[1:]:
            r = by_alias(f) or (pick(names[_norm(f)], rai) if names.get(_norm(f)) else None)
            if r:
                return r
        for f in forms:
            r = by_words(f, rai)
            if r:
                return r
        return None

    return venue


def _km(a, b, c, d):
    return math.hypot((c - a) * 111.32, (d - b) * 111.32 * math.cos(math.radians(a)))


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:80] or "x"


def interest(days=30):
    """Human `open` taps on calendar events in the last `days`, from traffic_eye.
    A failed query keeps the last file; counting is never worth a build."""
    try:
        from traffic import sql
        rows = sql("SELECT blob11 k, SUM(_sample_interval * double5) AS n FROM traffic_eye "
                   f"WHERE blob1 = 'motdang.net' AND timestamp > NOW() - INTERVAL '{days}' DAY "
                   "AND blob4 = '/api/map' AND blob9 = 'open' AND blob11 LIKE 'ev:%' AND blob2 = 'human' "
                   "GROUP BY k ORDER BY n DESC LIMIT 500")
        data = {"generated": thaitime.bangkok_today().isoformat(), "days": days,
                "counts": {r["k"][3:]: int(float(r["n"])) for r in rows}}
        _dump(data, INTEREST)
        return data
    except (SystemExit, Exception):
        return _j(INTEREST) if INTEREST.exists() else {"counts": {}}


def bake_events(docs, ix, counts):
    ev = _j(ROOT / "data/events.json")["events"]
    ex = _j(ROOT / "data/curated/event_extras.json")
    extras = ex.get("events", {})
    rows_add = [r for r in ex.get("add", []) if isinstance(r, dict) and r.get("uid") not in {e["uid"] for e in ev}]
    venue = venue_finder(ix["places"])
    # each event's link from importers/event_links.py: the source's own if it answers, else the
    # series' kept link, else the venue's site (rung "venue", shown as the venue's, not the event's).
    # A file older than three days is not trusted to say a source link is dead: the source's stands.
    lkf = ROOT / "data/event_links.json"
    lk = _j(lkf) if lkf.exists() else {}
    fresh = lk.get("generated", "") >= (thaitime.bangkok_today() - dt.timedelta(days=3)).isoformat()
    links = lk.get("links", {}) if fresh else {}
    judged = set(lk.get("judged", [])) if fresh else set()

    today = thaitime.bangkok_today()
    horizon = (today + dt.timedelta(days=56)).isoformat()   # the calendar pages a fortnight at a time
    out, matched = [], 0
    for e in ev + rows_add:
        e = dict(e, **{k: v for k, v in extras.get(e["uid"], {}).items() if v})
        s = e.get("start") or ""
        if not s or s[:10] > horizon or (e.get("end") or s)[:10] < today.isoformat():
            continue
        text = (e.get("title", "") + " " + (e.get("description") or "")).lower()
        cat = next((c for c in CATS if re.search(c[3], text)), OTHER)
        v = venue(e.get("venue_name"), e.get("city") or "")
        got = links.get(e["uid"])
        url = got["url"] if got else ("" if e["uid"] in judged else e.get("url") or "")   # an event harvested after the run keeps its source's link
        row = {"k": _slug(e["title"]), "t": re.sub(r"<[^>]+>", "", e["title"]).strip(), "s": s, "e": e.get("end"), "ad": bool(e.get("all_day")),
               "v": e.get("venue_name") or "", "cost": e.get("cost") or "", "url": url,
               "rec": bool(e.get("recurring")), "src": e.get("source") or "", "c": cat[0],
               # the calendar has two cities; a venue in a neighbouring province (Lamphun's) goes with Chiang Mai
               "city": "cr" if ((v or {}).get("province") or e.get("city")) == "cr" else "cm"}
        if got and (got.get("kind") == "host" or got["rung"] == "venue"):
            row["lk"] = "host"              # the page of whoever runs or hosts it, not of this event
        desc = re.sub(r"\s*·?\s*booking: \S+", "", e.get("description") or "").strip(" ·")
        if desc and not re.match(r"^(every \w+|\d{1,2} \w+ \d{4}) [\d:]*\s*·\s*at ", desc):
            row["d"] = desc[:600]
        if e.get("image"):
            row["img"], row["alt"] = e["image"], e.get("image_alt", "")
        else:
            dd = doodles_layer.fit(e["title"], e.get("venue_name"))
            if dd:
                row["dd"] = dd
        if e.get("page"):
            row["page"] = e["page"]
        if v:
            matched += 1
            row["la"], row["lo"] = round(v["lat"], 5), round(v["lng"], 5)
            row["vu"] = v["province"] + "/p/" + v["slug"] + ".html"
            # The venue's own picture, shown inside the opened card; the card's
            # cover (its image or its doodle) is left as it is.
            try:
                import commons_layer
                vp = commons_layer.place_picture(v["id"])
            except Exception:                    # noqa: BLE001
                vp = None
            if not vp:
                # nothing OF the venue: the nearest picture within 250 m, said so
                try:
                    nb = commons_layer.near(v["lat"], v["lng"], 0.25, 1)
                except Exception:                # noqa: BLE001
                    nb = []
                if nb:
                    p = nb[0][1]
                    vp = {"src": commons_layer._band(p), "link": p.get("page") or "",
                          "by": "%s, %s" % (commons_layer._artist(p.get("artist")), p.get("licence") or "")}
                    row["vpn"] = int(round(nb[0][0] * 1000 / 10.0) * 10) or 10
            if vp:
                row["vp"], row["vpb"], row["vpl"] = vp["src"], vp["by"], vp["link"]
            a = min(AREAS, key=lambda A: _km(v["lat"], v["lng"], A[2], A[3]))
            if _km(v["lat"], v["lng"], a[2], a[3]) < 4:
                row["ath"], row["aen"] = a[0], a[1]
        have = {"time": not row["ad"] and s[11:16] not in ("", "00:00"), "end": bool(row["e"]), "venue": bool(row["v"]),
                "map": "la" in row, "cost": bool(row["cost"]), "link": bool((row["url"] and row.get("lk") != "host") or row.get("page")),
                "about": "d" in row, "picture": "img" in row}
        row["have"] = [k for k, ok in have.items() if ok]
        row["n"] = counts.get(row["k"], 0)
        out.append(row)
    out.sort(key=lambda r: r["s"])
    cats, seen = [], set()
    for c in CATS + [OTHER]:
        if c[0] not in seen:
            seen.add(c[0])
            cats.append({"k": c[0], "th": c[1], "en": c[2]})
    _dump({"generated": today.isoformat(), "cats": cats, "fields": ["time", "end", "venue", "map", "cost", "link", "about", "picture"],
           "events": out}, docs / "front/events.json")
    fest = _j(ROOT / "data/festivals.json")["festivals"]
    fn = {f["id"]: f for f in fest}
    upcoming = sorted([{"id": r["festival_id"], "d0": r["date_start"], "d1": r["date_end"],
                        "th": fn.get(r["festival_id"], {}).get("name_th", r["festival_id"]),
                        "en": fn.get(r["festival_id"], {}).get("name_en", "")}
                       for r in _j(ROOT / "data/festival_calendar.json")["rows"] if r["date_end"] >= today.isoformat()],
                      key=lambda r: r["d0"])[:4]
    _dump({"festivals": upcoming}, docs / "front/soon.json")
    dd = ROOT / "data/curated/doodles.json"
    days = [d for d in (_j(dd)["days"] if dd.exists() else []) if d.get("date", "") >= today.isoformat()]
    days, aired = _doodle_days(days, docs / "front/events.json", today)
    kinds = {k: {"math": v.get("math", "")} for k, v in doodles_layer.kinds().items()}
    _dump({"days": days, "kinds": kinds, "aired": aired}, docs / "front/doodle.json")
    _dump({"aired": _j(AIRED).get("aired", [])}, docs / "front/aired.json")   # /sites/doodles/
    return len(out), matched


AIRED = ROOT / "data/curated/doodle_aired.json"


def _doodle_days(days, events, today, ahead=2):
    """The band's doodle fixed for today and the next days (tools/doodler_pick.mjs), a curated
    row winning its day; today's goes on the aired list, so it returns only at a higher version
    (Nan, 2026-10-02: reused "only after significant editing to make it more baller than last
    time"). Returns the days and the aired map {'set' or 'set:variant': version}."""
    led = _j(AIRED).get("aired", []) if AIRED.exists() else []
    want = [(today + dt.timedelta(days=i)).isoformat() for i in range(ahead + 1)]
    have = {d["date"] for d in days}
    try:
        r = subprocess.run(["node", str(ROOT / "tools/doodler_pick.mjs"), str(events), str(AIRED)] + want,
                           capture_output=True, text=True, timeout=60, check=True)
        planned = [p for p in json.loads(r.stdout) if p.get("set") and p["date"] not in have]
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        print("doodle plan skipped:", e)
        planned = []
    days = sorted(days + planned, key=lambda d: d["date"])
    for d in days:
        if d["date"] <= today.isoformat() and not any(x["date"] == d["date"] for x in led):
            for o in d.get("opts") or [d]:   # each of the day's choices airs to some reader
                led.append({"date": d["date"], "k": o.get("k", ""), "set": o.get("set") or ("latin" if d.get("kind") == "latin-night" else d.get("kind", "")),
                            "variant": o.get("variant", ""), "version": o.get("version", 1)})
    # each row keeps the event it was drawn for, so /sites/doodles/ can draw it again after the event leaves the calendar
    evs = {}
    for e in (_j(events).get("events", []) if Path(events).exists() else []):
        evs.setdefault(e["k"], []).append(e)
    for x in led:
        if "t" not in x and evs.get(x["k"]):
            e = min(evs[x["k"]], key=lambda e: abs(dt.date.fromisoformat(e["s"][:10]) - dt.date.fromisoformat(x["date"])))
            x.update({k: e[k] for k in ("t", "s", "v", "la", "lo") if e.get(k) not in (None, "")})
    AIRED.write_text(json.dumps({"about": "Doodles the front band has shown, one row a day; a doodle returns only at a higher version.",
                                 "aired": sorted(led, key=lambda x: x["date"])}, ensure_ascii=False, indent=1))
    aired = {}
    for x in led:
        key = x["set"] + (":" + x["variant"] if x.get("variant") else "")
        aired[key] = max(aired.get(key, 0), x.get("version", 1))
    return days, aired


# ---------------------------------------------------------------- AHEAD: the months past the fortnight

def bake_ahead(docs, today=None):
    """The stage's Ahead strip (Nan, 2026-10-02: "show 14 days, but do something snazzy to
    encourage planning further out … also planning to bug out for smoke season"). Picks and
    words in data/curated/ahead.json; lunar dates from festival_calendar.json; the smoke from
    the Smoky Season's satellite fire climatology (FIRMS 2003–2024, per day of year)."""
    today = today or thaitime.bangkok_today()
    cur = _j(ROOT / "data/curated/ahead.json")
    cal = _j(ROOT / "data/festival_calendar.json")["rows"]
    m = today.month - 1 + cur.get("months", 7) + 1
    to = dt.date(today.year + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)

    def nth_weekend(y, mo, n):
        d = dt.date(y, mo, 1)
        d += dt.timedelta(days=(5 - d.weekday()) % 7)
        d += dt.timedelta(days=7 * (n - 1))
        return d, d + dt.timedelta(days=1)

    items = []
    for p in cur["picks"]:
        d0 = d1 = None
        usual = False
        rows = sorted((r for r in cal if r["festival_id"] == p["id"] and r["date_end"] >= today.isoformat()),
                      key=lambda r: r["date_start"])
        if rows:
            d0, d1 = dt.date.fromisoformat(rows[0]["date_start"]), dt.date.fromisoformat(rows[0]["date_end"])
        else:
            for y in (today.year, today.year + 1):
                if p.get("d"):
                    a, b = (dt.date(y, int(x[:2]), int(x[3:])) for x in p["d"])
                elif p.get("rule"):
                    a, b = nth_weekend(y, p["rule"][2], p["rule"][0])
                    usual = True
                else:
                    fe = next(f for f in _j(ROOT / "data/festivals.json")["festivals"] if f["id"] == p["id"])
                    a = b = dt.date(y, fe["months"][0], fe["day"])
                if b >= today:
                    d0, d1 = a, b
                    break
        if not d0 or d0 > to:
            continue
        items.append({"id": p["id"], "kind": p["kind"], "th": p["th"], "en": p["en"], "lth": p["line_th"],
                      "len": p["line_en"], "d0": d0.isoformat(), "d1": d1.isoformat(), "usual": usual,
                      "page": "festivals/%s.html" % p["id"]})
    out = {"from": today.isoformat(), "to": to.isoformat(), "items": sorted(items, key=lambda r: r["d0"])}
    try:
        clim = _j(ROOT / "assets/sites/smoky-season/data/fires.json")["clim"]
    except (OSError, KeyError, ValueError):
        clim = None
    if clim:
        top, sm = max(clim), cur["smoke"]
        n = (to - today).days + 1
        out["haze"] = [round(clim[min((today + dt.timedelta(days=i)).timetuple().tm_yday, 365) - 1] / top, 2) for i in range(n)]
        hot = [i + 1 for i, v in enumerate(clim) if v >= sm.get("cut", 0.25) * top]
        y = today.year if dt.date(today.year, 1, 1) + dt.timedelta(days=hot[-1] - 1) >= today else today.year + 1
        s0 = dt.date(y, 1, 1) + dt.timedelta(days=hot[0] - 1)
        s1 = dt.date(y, 1, 1) + dt.timedelta(days=hot[-1] - 1)
        pk = dt.date(y, 1, 1) + dt.timedelta(days=clim.index(top))
        out["smoke"] = {"kind": "smoke", "th": sm["th"], "en": sm["en"], "lth": sm["line_th"], "len": sm["line_en"],
                        "d0": s0.isoformat(), "d1": s1.isoformat(), "peak": pk.isoformat(), "page": sm["page"]}
    out["plan"] = _plan()
    _dump(out, docs / "front/ahead.json")
    return len(items)


GUIDE_REGISTER = "https://esvcs.dot.go.th/e-service/LicenseInformationPage"


def _plan():
    """The Plan ahead cards' buttons (Nan, 2026-10-11). Find a room: the paid booking link per city, from the
    md-plan-room-<city> slots in data/curated/affiliate.json (affiliate-slots/slots.json; url null until the link
    exists). Find a guide: motdang.net Co.'s helpers from data/curated/guides.json when it has any
    ({"helpers": [{"city", "en", "th", "url", "price"}]}), then the Department of Tourism's licence register."""
    aff = _j(ROOT / "data/curated/affiliate.json") if (ROOT / "data/curated/affiliate.json").exists() else {"slots": {}}
    room = {}
    for c in ("cm", "cr"):
        s = aff["slots"].get("md-plan-room-" + c) or {}
        if s.get("url"):
            room[c] = {"url": s["url"], "en": s.get("en") or s.get("brand", ""), "th": s.get("th") or s.get("brand", "")}
    g = ROOT / "data/curated/guides.json"
    helpers = [h for h in (_j(g).get("helpers", []) if g.exists() else []) if h.get("url") and h.get("en")]
    return {"room": room, "paid": {"en": aff.get("label_en", ""), "th": aff.get("label_th", "")},
            "guide": {"register": GUIDE_REGISTER, "helpers": helpers}}


# ---------------------------------------------------------------- the whole bake, and the page

# ---------------------------------------------------------------- WHEN: every dated thing, one bake

AHEAD_DAYS = 214        # plan ahead runs to about seven months (when.js AHEAD_DAYS)


def bake_when(docs, today=None):
    """docs/front/when.json (calendar design, D): the front page's dated things in one file. Events
    are events.json's rows as they stand (same `k`, so kept lists and shared #ev= links hold) with
    kind "ev"; festivals take their dates from festivals_layer.occurrence() (announced, then the
    rule) and from data/festival_calendar.json only where that gives none; wan phra and the full and
    new moons come from data/sky.json. Run after bake_events."""
    import festivals_layer
    today = today or thaitime.bangkok_today()
    horizon = today + dt.timedelta(days=AHEAD_DAYS)
    items = [dict(e, kind="ev") for e in _j(docs / "front/events.json")["events"]]
    ann = festivals_layer.announced_dates()
    cal = sorted(_j(ROOT / "data/festival_calendar.json")["rows"], key=lambda r: r["date_start"])
    for f in _j(ROOT / "data/festivals.json")["festivals"]:
        occ = festivals_layer.occurrence(f, ann.get(f["id"]), today)
        if occ:
            d0, d1, by = occ
        else:
            row = next((r for r in cal if r["festival_id"] == f["id"] and r["date_end"] >= today.isoformat()), None)
            if not row:
                continue
            d0, d1, by = dt.date.fromisoformat(row["date_start"]), dt.date.fromisoformat(row["date_end"]), "calendar"
        if d1 < today or d0 > horizon:
            continue
        items.append({"kind": "fest", "id": f["id"], "th": f.get("name_th", f["id"]), "en": f.get("name_en", ""),
                      "d0": d0.isoformat(), "d1": d1.isoformat(), "by": by, "prov": f.get("province") or "",
                      "page": "festivals/%s.html" % f["id"]})
    sky = _j(ROOT / "data/sky.json").get("days", {})
    for d in sorted(sky):
        m = sky[d].get("moon") or {}
        if not today.isoformat() <= d <= horizon.isoformat():
            continue
        if m.get("wan_phra") or m.get("phase_en") in ("Full moon", "New moon"):
            items.append({"kind": "sky", "d": d, "wan": bool(m.get("wan_phra")), "th": m.get("phase_th", ""),
                          "en": m.get("phase_en", ""), "lth": m.get("thai_label_th", ""), "len": m.get("thai_label_en", "")})
    _dump({"built": dt.datetime.now(thaitime.BKK).isoformat(timespec="seconds"), "today": today.isoformat(),
           "items": items}, docs / "front/when.json")
    return len(items)


def _when_or_none(docs):
    """when.json is new and nothing reads it yet: a failure in it is printed, and the build goes on."""
    try:
        return bake_when(docs)
    except Exception as x:  # noqa: BLE001
        print("  ⚠️  front: when.json not baked —", repr(x))
        return 0


def bake_fires(docs):
    """docs/front/fires.json: the week's satellite fire counts (data/firms.json, the Smoky Season's feed),
    per day for the whole box and for each province. The doodle draws a flame per fire in the reader's."""
    src = ROOT / "data" / "firms.json"
    if not src.exists():
        return 0
    f = _j(src)
    out = {k: f[k] for k in ("source", "updated", "days", "per_day", "prov") if k in f}
    (docs / "front").mkdir(parents=True, exist_ok=True)
    (docs / "front" / "fires.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return sum(f.get("per_day", []))


AIRPORTS_CSV = ROOT / "cache" / "ourairports.csv"   # OurAirports, public domain: davidmegginson.github.io/ourairports-data


def bake_flights(docs):
    """docs/front/flights.json for the flights tile: every route in data/flights.json with its airport's
    position (OurAirports), plus the airlines' names. Counts stay the file's own (arrivals a month)."""
    import csv
    src = ROOT / "data" / "flights.json"
    if not src.exists() or not AIRPORTS_CSV.exists():
        return 0
    f = _j(src)
    want = {r["iata"] for r in f["routes"]} | set(f["airports"])
    board = ROOT / "data" / "flightboard.json"           # today's board may name an airport the timetable does not
    if board.exists():
        for x in _j(board).get("flights", []):
            want |= {x.get("dep_iata"), x.get("arr_iata")}
    at = {}
    with AIRPORTS_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["iata_code"] in want and row["type"] in ("large_airport", "medium_airport", "small_airport"):
                at.setdefault(row["iata_code"], [round(float(row["latitude_deg"]), 4), round(float(row["longitude_deg"]), 4)])
    routes = [{k: r[k] for k in ("airport", "iata", "th", "en", "country_th", "country_en", "dom", "per_month", "airlines", "season",
                                       "block_min", "per_week", "start", "end", "status") if k in r}
              | {"ll": at[r["iata"]]} for r in f["routes"] if r["iata"] in at]
    out = {"as_of": f["as_of"], "airports": {k: v | {"ll": at[k]} for k, v in f["airports"].items() if k in at},
           "ll": {k: v for k, v in at.items()},
           "airlines": f["airlines"], "routes": routes}
    (docs / "front").mkdir(parents=True, exist_ok=True)
    (docs / "front" / "flights.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return len(routes)


def bake_roads(docs):
    """docs/front/roads.json for the roads tile: the Department of Highways' counted sections around Chiang
    Mai (data/traffic.json, AADT lines), each with its vehicles a day, motorcycles a day and grade."""
    src = ROOT / "data" / "traffic.json"
    if not src.exists():
        return 0
    t = _j(src)
    roads = [{"route": r["route"], "name": r["name"], "motor": r["motor"], "moto": r["moto"], "heavy": r["heavy"],
              "grade": r.get("grade"), "year": r.get("year"),
              "lines": [[[round(x, 4), round(y, 4)] for x, y in ln] for ln in r["lines"]]}
             for r in t["roads"] if r.get("lines")]
    c = t["city"]["center"]                       # TomTom 2025, central Chiang Mai: congestion % by weekday (Mon = 0) and hour
    tt = {"week": [[h[0] for h in day] for day in c["week"]], "month": c["month"], "year_c": c["year_c"],
          "source": t["city"]["source"]}
    out = {"year_be": t["roads_meta"]["year_be"], "sources": t["roads_meta"]["sources"][:1], "roads": roads, "tomtom": tt}
    (docs / "front").mkdir(parents=True, exist_ok=True)
    (docs / "front" / "roads.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return len(roads)


def bake(docs=None, thumbs=True, ask=True):
    docs = Path(docs or DOCS)
    ix = _index(docs)
    counts = (interest() if ask else (_j(INTEREST) if INTEREST.exists() else {})).get("counts", {})
    parts = {"map": bake_map(docs, ix), "near": bake_near(docs, ix, thumbs), "sites": bake_sites(docs),
             "events": bake_events(docs, ix, counts), "when": _when_or_none(docs), "ahead": bake_ahead(docs), "fires": bake_fires(docs),
             "flights": bake_flights(docs), "roads": bake_roads(docs)}
    shutil.copy(ASSETS / "when.js", docs / "front/when.js")
    shutil.copy(ASSETS / "tiles.js", docs / "front/tiles.js")
    shutil.copy(ASSETS / "front.js", docs / "front/front.js")
    shutil.copy(ASSETS / "wx.js", docs / "front/wx.js")
    shutil.copy(ASSETS / "lunation.js", docs / "front/lunation.js")
    doodles_layer.copy(docs)
    return ("front: %d lamps, %d specks · %d near photos (%d new thumbs) · %d minisites with pictures · "
            "%d events, %d at a known venue · %d with reader interest") % (
        *parts["map"], *parts["near"], parts["sites"][0], *parts["events"], len(counts))


def render(home_ld="", lang_head="", lang_css="", lang_switch="", lang_js="", built=""):
    t = (ASSETS / "index.html").read_text()
    # the rest of the site's ant (build.py LOGO_MARK, the same file) and its faces (assets/fonts/_faces.css)
    logo = (ROOT / "assets/logo/motdang-mark.svg").read_text().replace(
        '<svg ', '<svg class="logoant" aria-hidden="true" focusable="false" ', 1).replace(' role="img" aria-label="มดแดง Mot Dang"', '')
    faces = ROOT / "assets/fonts/_faces.css"
    faces = faces.read_text().strip().replace("url(fonts/", "url(/fonts/") if faces.exists() else ""
    for k, v in {"LOGO": logo, "FACES": faces, "HOME_LD": home_ld, "LANG_HEAD": lang_head, "LANG_CSS": lang_css, "LANG_SWITCH": lang_switch,
                 "LANG_JS": lang_js, "BUILT": html.escape(built)}.items():
        t = t.replace("{{%s}}" % k, v)
    return stamp(t)


def stamp(t):
    """Each front-page script's own hash in its address. sw.js answers a script from its cache first, so an
    unstamped address hands a returning phone yesterday's script beside today's page (Nan's phone, 2026-10-03:
    the doodle and tiles blank until a second visit). One page carries these; the rest of the site does not."""
    for js in ("skyline.js", "doodler.js", "doodles.js", "when.js", "tiles.js", "wx.js", "lunation.js", "front.js"):
        f = ASSETS / js
        if f.exists():
            v = hashlib.md5(f.read_bytes()).hexdigest()[:8]
            t = re.sub(r'src="/front/%s(\?v=[0-9a-f]+)?"' % re.escape(js), 'src="/front/%s?v=%s"' % (js, v), t)
    return t


if __name__ == "__main__":
    args = sys.argv[1:]
    d = Path(args[args.index("--docs") + 1]) if "--docs" in args else DOCS
    print(bake(d, thumbs="--no-thumbs" not in args, ask="--no-interest" not in args))
