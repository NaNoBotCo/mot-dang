"""The places along the moat, for Chiang Mai, Doodled: docs/sites/doodle-map/data/moat_front.json.

Nan, 2026-10-11, of the doodle map's moat: "there should also be road and lots of
named buildings on both sides of the moat", then "Yes, way more please, at every
zoom level. With the moat, every business is a landmark."

The map's other places come from /api/v1/places a view at a time, best known
first and fifty at most, so the banks got whatever the whole view had room for.
This picks every published place whose point is within 60 m of the moat's water
(its pieces in city-live's land.json, inside the doodle map's moat box), from the
API index the build has just written, and the map draws them all, before the
view's own pick.

    rows: [id, lat, lng, thai name, latin name, page path, first category, photo 0/1, antRank,
           RTGS reading of a Thai-only name (build.name_roman) or ""]

    python3 moatfront_layer.py      writes it from docs/api/v1/index.json
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAND = ROOT / "assets" / "sites" / "city-live" / "data" / "land.json"
BOX = (18.776, 18.800, 98.974, 98.998)          # map.js CFG.moat
REACH = 60                                       # metres from the water's edge
THAI = re.compile(r"[฀-๿]")
THIN = re.compile(r" · [\d.,]+ ?(m|km|ม\.|กม\.) ")   # map.js thin(): a name made of a distance


def _dec(e, s):
    out, la, lo = [], 0, 0
    for i in range(0, len(e), 2):
        la, lo = (e[0], e[1]) if i == 0 else (la + e[i], lo + e[i + 1])
        out.append((la / s, lo / s))
    return out


def moat_edges(land):
    edges = []
    for f in land["feats"]["water"]:
        for ring in f:
            a = _dec(ring, land["scale"])
            las, los = [p[0] for p in a], [p[1] for p in a]
            if min(las) > BOX[0] and max(las) < BOX[1] and min(los) > BOX[2] and max(los) < BOX[3]:
                edges += [(a[i - 1], a[i]) for i in range(len(a))]
    return edges


def _dist(p, a, b, kx):
    ax, ay = (a[1] - p[1]) * kx, (a[0] - p[0]) * 110574
    bx, by = (b[1] - p[1]) * kx, (b[0] - p[0]) * 110574
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    u = max(0.0, min(1.0, -(ax * dx + ay * dy) / l2)) if l2 else 0.0
    return math.hypot(ax + u * dx, ay + u * dy)


def pick(places, land, roman=lambda r: ""):
    edges = moat_edges(land)
    if not edges:
        return []
    kx = 110574 * math.cos(math.radians(18.79))
    pad = REACH / 110574 * 1.2
    rows = []
    for r in places:
        la, ln = r.get("lat"), r.get("lng")
        if la is None or ln is None or r.get("province") != "cm":
            continue
        if not (BOX[0] - pad < la < BOX[1] + pad and BOX[2] - pad < ln < BOX[3] + pad):
            continue
        if r.get("geoPrecision") not in ("exact", "block"):
            continue
        name, en = (r.get("name") or "").strip(), (r.get("nameEn") or "").strip()
        if THIN.search(" " + en + " " + name + " "):
            continue
        if min(_dist((la, ln), a, b, kx) for a, b in edges) > REACH:
            continue
        th = name if THAI.search(name) else (r.get("nameTh") or "")
        if not en and not THAI.search(name):
            en = name
        rows.append([r["id"], round(la, 6), round(ln, 6), th, en,
                     "/%s/p/%s.html" % (r["province"], r["slug"]),
                     (r.get("cat") or [""])[0], 1 if "photo" in (r.get("has") or []) else 0,
                     r.get("antRank") or 0, "" if en else roman(r)])
    rows.sort(key=lambda x: -x[8])
    return rows


def write(docs, roman):
    docs = Path(docs)
    index = json.loads((docs / "api" / "v1" / "index.json").read_text())
    rows = pick(index["places"], json.loads(LAND.read_text()), roman)
    out = docs / "sites" / "doodle-map" / "data" / "moat_front.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, separators=(",", ":")))
    return "%d places along the moat" % len(rows)


def emit(g):
    return write(g["DOCS"], g["name_roman"])


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    import build
    print(write(ROOT / "docs", build.name_roman))
