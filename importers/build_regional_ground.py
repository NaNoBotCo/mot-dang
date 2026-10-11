#!/usr/bin/env python3
"""The ground under the regional maps: provinces, borders, rivers, main roads.

cm-cr.pmtiles covers Chiang Mai and Chiang Rai and nothing else, so the three
maps whose frame is wider than the two provinces drew their pins on blank
paper: the hot springs of seventeen provinces (/namphuron.html), the shrines of
both provinces (/san.html) and the indigo map that reaches Xieng Khouang in
Laos (/hom.html). This writes one small file those maps draw from at build
time, in their own projection, as inline SVG.

Sources, each cached under cache/naturalearth/ and fetched with curl (the
system Python's LibreSSL fails TLS to these hosts):

  Natural Earth 1:10m (public domain) — admin-1 provinces, admin-0 borders,
      the Mekong, Salween, Ou, Ngum and Ca, main roads.
  OpenStreetMap (ODbL), via Overpass — the Nan, Ping, Wang, Yom, Kok, Ing and
      Moei rivers. Natural Earth's 1:10m rivers stop short of the Nan, which is
      the river the indigo map is about.
  OSRM car profile on routing.openstreetmap.de (OSM data, ODbL) — the road
      from Chiang Mai to Ban Thung Hong, the one route on these maps a reader
      can ride.

    python3 importers/build_regional_ground.py            # uses the cache
    python3 importers/build_regional_ground.py --refetch  # re-downloads

Writes data/regional_ground.json. Coordinates are [lat, lng], 3 dp (~100 m),
Douglas-Peucker thinned, clipped to BOX.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "naturalearth"
OUT = ROOT / "data" / "regional_ground.json"

# South, West, North, East. The widest regional frame on the site is the
# indigo map (Chiang Mai to Xieng Khouang); the hot-spring map reaches Uthai
# Thani at 15.3 N.
BOX = (14.5, 96.8, 21.3, 104.3)

NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
NE_FILES = ("ne_10m_admin_1_states_provinces", "ne_10m_admin_0_countries",
            "ne_10m_rivers_lake_centerlines", "ne_10m_roads")
# Natural Earth's own Ping and Yom are coarser than OSM's and would draw twice.
NE_RIVERS = {"Mekong", "Lancang", "Salween", "Nu", "Ou", "Ngun", "Ca"}
OVERPASS = "https://overpass-api.de/api/interpreter"
OSM_RIVERS_Q = ('[out:json][timeout:300];rel["waterway"="river"]'
                '["name"~"^แม่น้ำ(น่าน|ปิง|วัง|ยม|กก|อิง|เมย)$"]'
                '(14.8,97.0,21.0,104.0);out geom;')
OSRM = "https://routing.openstreetmap.de/routed-car/route/v1/driving/"
ROUTES = [
    {"key": "cm-thunghong", "th": "เชียงใหม่ → บ้านทุ่งโฮ้ง แพร่",
     "en": "Chiang Mai → Ban Thung Hong, Phrae",
     "from": (18.7883, 98.9853), "to": (18.17404, 100.16574)},
]

TH_EN = {"แม่น้ำวัง": "Wang"}
# Natural Earth's name_local is wrong on these four: TH-36 and TH-38 carry a
# neighbour's name, TH-67 and TH-71 the capital district's. Checked against
# ISO 3166-2:TH.
TH_FIX = {"TH-36": "ชัยภูมิ", "TH-38": "บึงกาฬ", "TH-67": "เพชรบูรณ์", "TH-71": "กาญจนบุรี"}

TOL = {"province": 0.006, "country": 0.006, "river": 0.004, "road": 0.004,
       "route": 0.002}


def curl(url, dest, data=None):
    cmd = ["curl", "-sSfL", "-m", "400", "-A", "mot-dang map build (motdang.net)",
           "-o", str(dest)]
    if data:
        cmd += ["--data-urlencode", "data=" + data]
    cmd.append(url)
    subprocess.run(cmd, check=True)


def fetch(refetch):
    CACHE.mkdir(parents=True, exist_ok=True)
    for n in NE_FILES:
        p = CACHE / (n + ".geojson")
        if refetch or not p.exists():
            print("fetching", n)
            curl(NE + n + ".geojson", p)
    p = CACHE / "osm_rivers.json"
    if refetch or not p.exists():
        print("fetching OSM rivers")
        curl(OVERPASS, p, OSM_RIVERS_Q)
    for r in ROUTES:
        p = CACHE / ("osrm_%s.json" % r["key"])
        if refetch or not p.exists():
            (a, b), (c, d) = r["from"], r["to"]
            print("routing", r["key"])
            curl(OSRM + "%s,%s;%s,%s?overview=full&geometries=geojson" % (b, a, d, c), p)


# ---------------------------------------------------------------- geometry

def _perp(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return ((x - (x1 + t * dx)) ** 2 + (y - (y1 + t * dy)) ** 2) ** 0.5


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        far, d = -1, tol
        for k in range(i + 1, j):
            dk = _perp(pts[k], pts[i], pts[j])
            if dk > d:
                far, d = k, dk
        if far > 0:
            keep[far] = True
            stack.append((i, far))
            stack.append((far, j))
    return [p for p, k in zip(pts, keep) if k]


def inside(lat, lng, m=0.0):
    s, w, n, e = BOX
    return s - m <= lat <= n + m and w - m <= lng <= e + m


def clip_runs(lnglat):
    """Split a line into the runs that fall inside BOX (one vertex of margin,
    so a line leaving the frame still reaches its edge)."""
    runs, cur = [], []
    pts = [(c[1], c[0]) for c in lnglat]
    for i, (la, ln) in enumerate(pts):
        near = inside(la, ln) or \
            (i > 0 and inside(*pts[i - 1])) or \
            (i + 1 < len(pts) and inside(*pts[i + 1]))
        if near:
            cur.append((la, ln))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def thin(run, tol):
    s = simplify(run, tol)
    return [[round(a, 3), round(b, 3)] for a, b in s]


def lines_of(geom):
    t = geom["type"]
    c = geom["coordinates"]
    if t == "LineString":
        return [c]
    if t == "MultiLineString":
        return c
    if t == "Polygon":
        return c[:1]
    if t == "MultiPolygon":
        return [poly[0] for poly in c]
    return []


# ------------------------------------------------------------------ layers

def provinces():
    gj = json.loads((CACHE / "ne_10m_admin_1_states_provinces.geojson").read_text())
    out = []
    for f in gj["features"]:
        p, g = f["properties"], f["geometry"]
        if not g:
            continue
        rings = []
        for ring in lines_of(g):
            if not any(inside(c[1], c[0], 0.3) for c in ring):
                continue
            s = thin([(c[1], c[0]) for c in ring], TOL["province"])
            if len(s) > 3:
                rings.append(s)
        if not rings:
            continue
        iso = p.get("iso_3166_2") or ""
        local = TH_FIX.get(iso) or p.get("name_local") or ""
        if local.startswith("จังหวัด"):
            local = local[len("จังหวัด"):]
        out.append({"iso": iso, "country": p.get("adm0_a3") or "",
                    "en": p.get("name_en") or p.get("name") or "",
                    "th": local if p.get("adm0_a3") == "THA" else "",
                    "rings": rings})
    out.sort(key=lambda x: x["iso"])
    return out


def countries():
    gj = json.loads((CACHE / "ne_10m_admin_0_countries.geojson").read_text())
    out = []
    for f in gj["features"]:
        p, g = f["properties"], f["geometry"]
        rings = []
        for ring in lines_of(g):
            for run in clip_runs(ring):
                rings.append(thin(run, TOL["country"]))
        if rings:
            out.append({"a3": p.get("ADM0_A3") or "", "en": p.get("NAME_EN") or p.get("NAME"),
                        "lines": rings})
    return out


def rivers():
    out = []
    gj = json.loads((CACHE / "ne_10m_rivers_lake_centerlines.geojson").read_text())
    for f in gj["features"]:
        p, g = f["properties"], f["geometry"]
        if not g or p.get("name") not in NE_RIVERS:
            continue
        runs = [thin(r, TOL["river"]) for ln in lines_of(g) for r in clip_runs(ln)]
        if runs:
            en = {"Lancang": "Mekong", "Nu": "Salween", "Ngun": "Ngum"}.get(p["name"], p["name"])
            out.append({"en": en, "th": {"Mekong": "แม่น้ำโขง", "Salween": "แม่น้ำสาละวิน"}.get(en, ""),
                        "rank": int(p.get("scalerank") or 9), "src": "ne", "lines": runs})
    osm = json.loads((CACHE / "osm_rivers.json").read_text())
    for e in osm.get("elements", []):
        t = e.get("tags") or {}
        runs = []
        for m in e.get("members", []):
            geo = m.get("geometry") or []
            if m.get("type") != "way" or m.get("role") not in ("main_stream", "", None) or len(geo) < 2:
                continue
            for r in clip_runs([[q["lon"], q["lat"]] for q in geo]):
                runs.append(thin(r, TOL["river"]))
        if runs:
            th = t.get("name") or ""
            en = (t.get("name:en") or "").replace(" River", "") or TH_EN.get(th, th)
            out.append({"en": en, "th": th,
                        "rank": 6, "src": "osm", "id": e["id"], "lines": runs})
    # Merge same-named rivers from both sources into one entry each.
    merged = {}
    for r in out:
        k = r["en"]
        if k in merged:
            merged[k]["lines"] += r["lines"]
        else:
            merged[k] = r
    return list(merged.values())


def roads():
    gj = json.loads((CACHE / "ne_10m_roads.geojson").read_text())
    out = []
    for f in gj["features"]:
        p, g = f["properties"], f["geometry"]
        if not g:
            continue
        runs = [thin(r, TOL["road"]) for ln in lines_of(g) for r in clip_runs(ln)]
        if runs:
            out.append({"rank": int(p.get("scalerank") or 10), "lines": runs})
    return out


def routes():
    out = []
    for r in ROUTES:
        d = json.loads((CACHE / ("osrm_%s.json" % r["key"])).read_text())
        if d.get("code") != "Ok" or not d.get("routes"):
            continue
        best = d["routes"][0]
        line = thin([(c[1], c[0]) for c in best["geometry"]["coordinates"]], TOL["route"])
        out.append({"key": r["key"], "th": r["th"], "en": r["en"],
                    "km": round(best["distance"] / 1000), "h": round(best["duration"] / 3600, 1),
                    "profile": "car", "line": line})
    return out


def main():
    fetch("--refetch" in sys.argv)
    doc = {
        "_readme": "Regional ground for the drawn maps wider than cm-cr.pmtiles. "
                   "Written by importers/build_regional_ground.py; read by regional_ground.py.",
        "box": list(BOX),
        "coords": "[lat, lng], 3 dp, Douglas-Peucker thinned",
        "credits": [
            {"what": "provinces, borders, Mekong/Salween/Ou/Ngum/Ca, main roads",
             "who": "Natural Earth 1:10m", "licence": "public domain",
             "url": "https://www.naturalearthdata.com/"},
            {"what": "Nan, Ping, Wang, Yom, Kok, Ing, Moei rivers; the road route",
             "who": "OpenStreetMap contributors (Overpass; OSRM car profile at "
                    "routing.openstreetmap.de)", "licence": "ODbL",
             "url": "https://www.openstreetmap.org/copyright"},
        ],
        "provinces": provinces(),
        "countries": countries(),
        "rivers": rivers(),
        "roads": roads(),
        "routes": routes(),
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    print("wrote %s — %d KB · %d provinces · %d border runs · %d rivers · %d roads · %d routes"
          % (OUT.relative_to(ROOT), OUT.stat().st_size // 1024, len(doc["provinces"]),
             sum(len(c["lines"]) for c in doc["countries"]), len(doc["rivers"]),
             len(doc["roads"]), len(doc["routes"])))


if __name__ == "__main__":
    main()
