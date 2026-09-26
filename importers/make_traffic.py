#!/usr/bin/env python3
"""Bake /traffic.html's data: where the roads jam, and at what hour.

Two sources, each doing the one thing it measures:

  กรมทางหลวง (DOH), Open Government Data of Thailand, attribution —
    * the AADT road lines from DOH's own GeoServer (onemap-layers.doh.go.th),
      every counted highway section in both provinces with its geometry and
      its vehicles a day by class. Motorcycles are class 2 and stay a column
      of their own, the way DOH prints them.
    * the congestion grade (ดัชนีการจราจรติดขัด, level A–F) per control
      section: peak-hour volume against the road's capacity, DOH's figure.
      The 2568 file's province column does not match its rows (route 108
      section 101 "เชียงใหม่ - ปากทางท่าลี่" is filed under อุดรธานี), so the
      join is on route + control section and the province column is unread.

  TomTom Traffic Index 2025, Chiang Mai city page — the hour. Congestion in
    the city centre and the metro area for each weekday hour (7 × 24), by
    month, and the H3 cells where the morning and evening jams sit. It is the
    only measured hour-by-hour figure for Chiang Mai on this disk; DOH
    publishes none, and the OTP's hourly camera counts are Bangkok. TomTom
    reserves its rights on the page; the figures are credited on every
    surface that prints them.

H3 cells arrive as ids. Turning an id into a hexagon needs the `h3` package
(pip install h3), used here only; the site reads plain coordinates. Without
it, a run keeps the hexagons already on disk for every id it already knows.

    python3 importers/make_traffic.py            # fetch, cache, bake
    python3 importers/make_traffic.py --offline  # rebuild from cache/traffic/
"""
import csv
import html
import io
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import ingest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "traffic.json"
CACHE = ROOT / "cache" / "traffic"
UA = "mot-dang-directory/1.0 (+https://motdang.net; traffic page)"

WFS = "https://onemap-layers.doh.go.th/geoserver/wfs"
# Chiang Mai and Chiang Rai with a margin; the DOH district decides membership.
BBOX = (97.3, 17.2, 100.7, 20.5)
DISTRICTS = ("ขท.เชียงใหม่", "ขท.เชียงราย")
INDEX_CSV = ("https://opendata.doh.go.th/dataset/0d6e8dab-74d6-4d1d-8046-f114721ad56d/"
             "resource/2a21b177-fd21-4f29-88d6-682905c173cc/download/index_route.csv")
INDEX_PAGE = "https://opendata.doh.go.th/dataset/index-traffic-route"
TOMTOM = "https://www.tomtom.com/traffic-index/city/chiang-mai/"

# DOH's thirteen classes, read against the aadt-68.csv columns row by row
# (route 1141 km 7: 96,450 cars, 26,366 motorcycles, total 121,403).
CLASS_MOTO = 2
CLASS_MOTOR = range(3, 13)      # cars, vans, buses, trucks: DOH's "รวม"
CLASS_HEAVY = range(5, 13)      # buses and trucks, DOH's "ยานยนต์หนัก"


def get(url, name, offline, binary=False):
    """Fetch once, keep the bytes in cache/traffic/, read the cache offline."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / name
    if not offline:
        # opendata.doh.go.th serves a chain Python 3.9's LibreSSL rejects;
        # the same bytes come over curl -k. Public data, read-only.
        ctx = ssl._create_unverified_context() if "doh.go.th" in url else None
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
            p.write_bytes(r.read())
    if not p.exists():
        raise SystemExit(f"{p} missing — run without --offline first")
    return p.read_bytes() if binary else p.read_text(encoding="utf-8-sig")


def latest_layer(offline):
    caps = get(WFS + "?service=WFS&version=2.0.0&request=GetCapabilities",
               "capabilities.xml", offline)
    years = [int(y) for y in re.findall(r"dohonemap:hgds_aadt_line_(\d{4})<", caps)]
    if not years:
        raise SystemExit("DOH capabilities list no hgds_aadt_line layer")
    return max(years)


def simplify(pts, tol=0.00018):
    """Douglas–Peucker in degrees; 0.00018° is about 19 m here, under a
    lane's width at the zoom the page opens on."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    dd = dx * dx + dy * dy or 1e-18
    worst, wi = 0.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / dd))
        ex, ey = x1 + t * dx - px, y1 + t * dy - py
        e = ex * ex + ey * ey
        if e > worst:
            worst, wi = e, i
    if worst <= tol * tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:wi + 1], tol)[:-1] + simplify(pts[wi:], tol)


def lines_of(geom):
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return geom["coordinates"]
    return []


def km(s):
    m = re.match(r"\s*(\d+)\+(\d+)", s or "")
    return int(m.group(1)) + int(m.group(2)) / 1000 if m else None


def roads(offline):
    year_be = latest_layer(offline)
    q = urllib.parse.urlencode({
        "service": "WFS", "version": "1.0.0", "request": "GetFeature",
        "outputFormat": "application/json", "srsName": "EPSG:4326",
        "typeName": f"dohonemap:hgds_aadt_line_{year_be}",
        "bbox": ",".join(map(str, BBOX)) + ",EPSG:4326"})
    fc = json.loads(get(WFS + "?" + q, f"aadt_line_{year_be}.json", offline))

    grades, grade_year = index_grades(offline)
    out = []
    for f in fc["features"]:
        p = f["properties"]
        if not (p.get("district_name") or "").startswith(DISTRICTS):
            continue
        cls = {i: int(p.get(f"vehcat_{i}_total") or 0) for i in range(1, 14)}
        motor = sum(cls[i] for i in CLASS_MOTOR)
        if not motor:
            continue
        route = str(int(p["highway_code"]))
        section = str(int(p["road_code"]))
        parts = []
        for ln in lines_of(f["geometry"]):
            s = simplify([(round(x, 5), round(y, 5)) for x, y in ln])
            if len(s) >= 2:
                parts.append([[x, y] for x, y in s])
        if not parts:
            continue
        g = grades.get((route, section))
        out.append({
            "route": route, "section": section,
            "name": (p.get("road_name") or "").strip(),
            "km": [p.get("km_start"), p.get("km_end")],
            "motor": motor, "moto": cls[CLASS_MOTO],
            "heavy": round(100 * sum(cls[i] for i in CLASS_HEAVY) / motor, 1),
            "station": p.get("station_type") or "",
            "year": p.get("traffic_year"),
            "district": p.get("district_name"),
            "grade": g["grade"] if g else None,
            "density": g["density"] if g else None,
            "grade_km": g["km"] if g else None,
            "lines": parts,
        })
    out.sort(key=lambda r: -r["motor"])
    return out, {"layer": f"hgds_aadt_line_{year_be}", "year_be": year_be,
                 "grade_year_be": grade_year}


def index_grades(offline):
    """(route, section) -> the section's grade in DOH's latest year. Where a
    section was surveyed at two km posts, the worse grade stands: the page
    says what the road does at its busiest hour."""
    text = get(INDEX_CSV, "index_route.csv", offline)
    rows = list(csv.DictReader(io.StringIO(text)))
    year = max(int(r["ปี"]) for r in rows if r["ปี"].isdigit())
    best = {}
    for r in rows:
        if r["ปี"] != str(year):
            continue
        key = (str(int(r["หมายเลขทางหลวง"])), str(int(r["ตอนควบคุม"])))
        g = (r.get("level_capacity_ratio") or "").strip().upper()
        if g not in "ABCDEF" or not g:
            continue
        try:
            dens = float(r["ความหนาแน่น"])
        except ValueError:
            dens = None
        if key not in best or g > best[key]["grade"]:
            best[key] = {"grade": g, "density": dens, "km": r["กม.สำรวจ"]}
    return best, year


def _astro(v):
    """Astro's island props are [type, value] pairs all the way down."""
    if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int):
        t, x = v
        if t == 0:
            return {k: _astro(y) for k, y in x.items()} if isinstance(x, dict) else x
        if t == 1:
            return [_astro(y) for y in x]
        return x
    if isinstance(v, dict):
        return {k: _astro(y) for k, y in v.items()}
    if isinstance(v, list):
        return [_astro(y) for y in v]
    return v


DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]


def week(rows):
    """168 {time: 'FRIDAY-17', c, v, fv} -> [day Mon=0][hour] = [c, v, fv]."""
    grid = [[None] * 24 for _ in DAYS]
    for r in rows:
        d, h = r["time"].rsplit("-", 1)
        grid[DAYS.index(d)][int(h)] = [r["c"], r["v"], r["fv"]]
    if any(x is None for row in grid for x in row):
        raise SystemExit("TomTom week grid has holes")
    return grid


def tomtom(offline):
    page = get(TOMTOM, "tomtom-chiang-mai.html", offline)
    head = None
    for props in re.findall(r'<astro-island[^>]*component-url="[^"]*CityMapHeader[^"]*"'
                            r'[^>]*props="([^"]*)"', page):
        head = _astro(json.loads(html.unescape(props)))
    if not head or "traffic" not in head:
        raise SystemExit("TomTom page carried no CityMapHeader island")
    t = head["traffic"]
    out = {}
    for area in ("center", "metro"):
        a = t[area]["all"]
        out[area] = {
            "week": week(a["weekHour"]),
            "month": [m["c"] for m in a["monthly"]],
            "year_c": a["base"]["c"], "year_v": a["base"]["v"], "year_fv": a["base"]["fv"],
            "am": {"hour": a["am"]["time"], "c": a["am"]["c"]},
            "pm": {"hour": a["pm"]["time"], "c": a["pm"]["c"]},
            "worst_day": a["worstDay"]["time"],
        }
    tiles = {}
    for key, name in (("congestionTiles", "all"), ("amCongestionTiles", "am"),
                      ("pmCongestionTiles", "pm")):
        for c in head.get(key) or []:
            tiles.setdefault(c["hex"], {})[name] = c["count"]
    return out, tiles, head.get("cityConfig", {}).get("timezone")


def hexes(tiles):
    """id -> ring. h3 when installed; else the rings the last run baked."""
    old = {}
    if OUT.exists():
        try:
            for h in json.loads(OUT.read_text())["city"]["hex"]:
                old[h["id"]] = h["ring"]
        except (ValueError, KeyError):
            pass
    try:
        import h3
    except ImportError:
        h3 = None
    rows, missing = [], 0
    for hid, s in sorted(tiles.items()):
        if h3:
            ring = [[round(lng, 5), round(lat, 5)] for lat, lng in h3.cell_to_boundary(hid)]
        else:
            ring = old.get(hid)
        if not ring:
            missing += 1
            continue
        rows.append({"id": hid, "all": s.get("all", 0), "am": s.get("am", 0),
                     "pm": s.get("pm", 0), "ring": ring})
    if missing:
        print(f"   {missing} H3 cells have no hexagon — pip install h3 and run again")
    return rows


def main():
    offline = "--offline" in sys.argv
    ok, failed = [], []
    try:
        road_rows, road_meta = roads(offline)
        ok.append("doh")
    except Exception as e:           # recorded by ingest, never swallowed
        road_rows, road_meta = [], {}
        failed.append(("doh", str(e)[:200]))
    try:
        city, tiles, tz = tomtom(offline)
        hex_rows = hexes(tiles)
        ok.append("tomtom")
    except Exception as e:
        city, hex_rows, tz = {}, [], None
        failed.append(("tomtom", str(e)[:200]))
    if failed:
        # Half a picture is a wrong picture: one source down keeps yesterday's file.
        return ingest.refuse(OUT, "; ".join(f"{a}: {b}" for a, b in failed), ok, failed)

    grades = {}
    for r in road_rows:
        grades[r["grade"] or "?"] = grades.get(r["grade"] or "?", 0) + 1
    doc = {
        "generated": date.today().isoformat(),
        "roads": road_rows,
        "roads_meta": dict(road_meta, grades=grades, sources=[
            {"th": "กรมทางหลวง ปริมาณจราจรเฉลี่ยต่อวัน (AADT) แผนที่สายทาง",
             "en": "Department of Highways, AADT road lines",
             "url": "https://onemap-layers.doh.go.th/geoserver/web/",
             "licence": "Open Government Data of Thailand — attribution"},
            {"th": "กรมทางหลวง ดัชนีการจราจรติดขัดตามสายทาง",
             "en": "Department of Highways, congestion index by route",
             "url": INDEX_PAGE,
             "licence": "Open Government Data of Thailand — attribution"}]),
        "city": {
            "name_th": "เชียงใหม่", "name_en": "Chiang Mai", "tz": tz,
            "year": 2025,
            "center": city["center"], "metro": city["metro"],
            "hex": hex_rows,
            "source": {"th": "TomTom Traffic Index 2025 หน้าเมืองเชียงใหม่",
                       "en": "TomTom Traffic Index 2025, Chiang Mai city page",
                       "url": TOMTOM, "licence": "© TomTom"},
        },
    }
    return ingest.write(OUT, doc, count=len(road_rows) + len(hex_rows),
                        min_rows=200, sources_ok=ok)


if __name__ == "__main__":
    main()
