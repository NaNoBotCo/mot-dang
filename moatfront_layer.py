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

Nan, 2026-10-11, later: "declutter the pins around the moat ... leaving mainly the well-known
ones, spirit houses, big trees and shrines, and business listings that include either great
details or a picture." So a place stays when it is a wat, sight or museum, a park or market
by name, a spirit house, shrine or big tree (reach 120 m, approximate points allowed, as her
own photos place them), or a business with a photo or four of phone, web, hours, LINE,
facets, schedule. Order: landmarks and the sacred first, then photos, then details.

Nan, 2026-10-12, of a Loi Kroh place page: "Need a lot more of roadside places labeled along
loi kroh road in chang klan. Similar to the moat." "And chang klan road." "Garden restaurant,
Alice's restaurant, Darling Bar not visible here. Lots of massage places and shops." So every
published place within 30 m of Loi Kroh or Chang Klan Road (their lines in
data/front_roads.json, from OpenStreetMap) goes in too, without the moat's declutter, after the
moat's own, the sacred and photos first.

Nan, the same night: "Similarly, give wararot, nimman, santhitam areas some love." So every
published place inside AREAS goes in the same way.

Then: "that's too many places. Please apply some kind of reasonable person filter." Off the
moat, a place without the moat's tier stays when it is somewhere a visitor goes (VISIT), has a
Latin name, and lists one of phone, web, hours, LINE on the two roads, two in the areas, where
it is also the best known such place in its 35 m square.

    rows: [id, lat, lng, thai name, latin name, page path, first category, photo 0/1, antRank,
           RTGS reading of a Thai-only name (build.name_roman) or "",
           tier: 0 landmark or sacred, 1 photo, 2 well described, 3 the rest]

Nan, the same night: "Don't show all places at every zoom level pls." The tier is for that:
map.js moatFront() lets in more tiers as the view closes in.

    python3 moatfront_layer.py          writes it from docs/api/v1/index.json
    python3 moatfront_layer.py roads    rewrites data/front_roads.json from cache/roads/
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAND = ROOT / "assets" / "sites" / "city-live" / "data" / "land.json"
ROADS = ROOT / "data" / "front_roads.json"
ROAD_NAMES = re.compile(r"^(ถนน)?(ลอยเคราะห์|ช้างคลาน)\s*$")
REACH_ROAD = 30
AREAS = {                                        # (south, north, west, east)
    "warorot": (18.7878, 18.7935, 98.9960, 99.0030),     # Tha Phae Rd to Chang Moi, to the Ping
    "nimman": (18.7940, 18.8030, 98.9630, 98.9725),      # Suthep Rd to Huay Kaew, Maya, the sois
    "santitham": (18.7990, 18.8095, 98.9745, 98.9885),
}
BOX = (18.776, 18.800, 98.974, 98.998)          # map.js CFG.moat
REACH = 60                                       # metres from the water's edge
REACH_SACRED = 120
KNOWN = {"sights", "wat", "museums-galleries"}
SACRED = {"spirit-house", "shrine", "big-tree"}
BY_NAME = re.compile(r"park|market|gate|สวน|ตลาด|กาด|ประตู", re.I)
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


def _subs(r):
    s = r.get("sub") or []
    return s if isinstance(s, list) else [s]


def tier(r, en, th):
    """0 landmark or sacred, 1 photo, 2 well described, None left off"""
    if SACRED & set(_subs(r)) or any(k in r["id"] for k in SACRED):
        return 0
    cats = set(r.get("cat") or [])
    if cats & KNOWN or (cats & {"parks", "market"} and BY_NAME.search(en + " " + th)):
        return 0
    has = set(r.get("has") or [])
    if "photo" in has:
        return 1
    if sum(k in has for k in ("phone", "web", "hours", "line")) + ("facets" in r) + ("sched" in r) >= 4:
        return 2
    return None


def pick(places, land, roman=lambda r: ""):
    edges = moat_edges(land)
    if not edges:
        return []
    kx = 110574 * math.cos(math.radians(18.79))
    pad = REACH_SACRED / 110574 * 1.2
    rows = []
    for r in places:
        la, ln = r.get("lat"), r.get("lng")
        if la is None or ln is None or r.get("province") != "cm":
            continue
        if not (BOX[0] - pad < la < BOX[1] + pad and BOX[2] - pad < ln < BOX[3] + pad):
            continue
        name, en = (r.get("name") or "").strip(), (r.get("nameEn") or "").strip()
        if THIN.search(" " + en + " " + name + " "):
            continue
        th = name if THAI.search(name) else (r.get("nameTh") or "")
        if not en and not THAI.search(name):
            en = name
        t = tier(r, en, th)
        if t is None:
            continue
        sacred = t == 0 and bool(SACRED & set(_subs(r)) or any(k in r["id"] for k in SACRED))
        if r.get("geoPrecision") not in (("exact", "block", "approx") if sacred else ("exact", "block")):
            continue
        if min(_dist((la, ln), a, b, kx) for a, b in edges) > (REACH_SACRED if sacred else REACH):
            continue
        rows.append([r["id"], round(la, 6), round(ln, 6), th, en,
                     "/%s/p/%s.html" % (r["province"], r["slug"]),
                     (r.get("cat") or [""])[0], 1 if "photo" in (r.get("has") or []) else 0,
                     r.get("antRank") or 0, "" if en else roman(r), t])
    rows.sort(key=lambda x: (x[10], -x[8]))
    return rows


def road_lines():
    """the roads' OpenStreetMap ways from the road tiles: [[[lat, lng], ...], ...]"""
    ways = {}
    for f in sorted((ROOT / "cache" / "roads").glob("*.json")):
        els = json.loads(f.read_text())["elements"]
        nodes = {e["id"]: (e["lat"], e["lon"]) for e in els if e["type"] == "node"}
        for e in els:
            if e["type"] == "way" and ROAD_NAMES.match(e["tags"].get("name", "")) and e["id"] not in ways:
                pts = [nodes.get(i) for i in e["nodes"]]
                if all(pts):
                    ways[e["id"]] = [[round(a, 7), round(b, 7)] for a, b in pts]
    return list(ways.values())


VISIT = {"food", "massage", "shopping", "hotel", "tattoo", "market", "parks", "whats-on", "muaythai"}
SPACING = 35                                     # metres between plain places in an area


def _inside(la, ln):
    return any(s < la < n and w < ln < e for s, n, w, e in AREAS.values())


def pick_roads(places, lines, have, roman=lambda r: ""):
    """the roads' places and the areas' places"""
    edges = [(tuple(w[i - 1]), tuple(w[i])) for w in lines for i in range(1, len(w))]
    kx = 110574 * math.cos(math.radians(18.79))
    las = [p[0] for e in edges for p in e] + [b[i] for b in AREAS.values() for i in (0, 1)]
    los = [p[1] for e in edges for p in e] + [b[i] for b in AREAS.values() for i in (2, 3)]
    pad = REACH_SACRED / 110574 * 1.2
    rows = []
    for r in places:
        la, ln = r.get("lat"), r.get("lng")
        if la is None or ln is None or r.get("province") != "cm" or r["id"] in have:
            continue
        if not (min(las) - pad < la < max(las) + pad and min(los) - pad < ln < max(los) + pad):
            continue
        name, en = (r.get("name") or "").strip(), (r.get("nameEn") or "").strip()
        if THIN.search(" " + en + " " + name + " "):
            continue
        th = name if THAI.search(name) else (r.get("nameTh") or "")
        if not en and not THAI.search(name):
            en = name
        t = tier(r, en, th)
        area = _inside(la, ln)
        if t is None:
            has = set(r.get("has") or [])
            if (r.get("cat") or [""])[0] not in VISIT or not en or \
                    sum(k in has for k in ("phone", "web", "hours", "line")) < (2 if area else 1):
                continue
        sacred = t == 0 and bool(SACRED & set(_subs(r)) or any(k in r["id"] for k in SACRED))
        if r.get("geoPrecision") not in (("exact", "block", "approx") if sacred else ("exact", "block")):
            continue
        if not area and (not edges or min(_dist((la, ln), a, b, kx) for a, b in edges)
                                    > (REACH_SACRED if sacred else REACH_ROAD)):
            continue
        rows.append([r["id"], round(la, 6), round(ln, 6), th, en,
                     "/%s/p/%s.html" % (r["province"], r["slug"]),
                     (r.get("cat") or [""])[0], 1 if "photo" in (r.get("has") or []) else 0,
                     r.get("antRank") or 0, "" if en else roman(r), 3 if t is None else t])
    rows.sort(key=lambda x: (x[10], -x[8]))
    taken, kept = set(), []
    for x in rows:
        if x[10] == 3 and _inside(x[1], x[2]):
            cell = (int(x[1] * 110574 / SPACING), int(x[2] * 104700 / SPACING))
            if cell in taken:
                continue
            taken.add(cell)
        kept.append(x)
    return kept


def write(docs, roman):
    docs = Path(docs)
    index = json.loads((docs / "api" / "v1" / "index.json").read_text())
    rows = pick(index["places"], json.loads(LAND.read_text()), roman)
    n = len(rows)
    lines = json.loads(ROADS.read_text()) if ROADS.exists() else []
    rows += pick_roads(index["places"], lines, {x[0] for x in rows}, roman)
    out = docs / "sites" / "doodle-map" / "data" / "moat_front.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, separators=(",", ":")))
    return "%d places along the moat, %d along Loi Kroh and Chang Klan and in Warorot, Nimman, Santitham" % (n, len(rows) - n)


def emit(g):
    return write(g["DOCS"], g["name_roman"])


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    if sys.argv[1:] == ["roads"]:
        lines = road_lines()
        ROADS.write_text(json.dumps(lines, separators=(",", ":")))
        print("%d ways" % len(lines))
    else:
        import build
        print(write(ROOT / "docs", build.name_roman))
