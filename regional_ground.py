#!/usr/bin/env python3
"""regional_ground.py — provinces, borders, rivers and main roads under a
drawn regional map, in the caller's own projection.

map_shell puts cm-cr.pmtiles under the maps of the two provinces. A map whose
frame runs past them (the north's hot springs, the indigo road from Laos) has
no tiles to stand on, so it draws this instead: data/regional_ground.json,
written by importers/build_regional_ground.py from Natural Earth and OSM.

    import regional_ground as rg
    g = rg.load()                               # None when the file is absent
    svg += rg.svg(g, xy, W, H)                  # xy = the caller's (lat, lng) -> (x, y)
    x, y = rg.label_point(g, "TH-54", xy)       # a province's own middle

The ground and the pins go through one projector, so they cannot drift apart.
A missing file draws nothing and the map keeps its plain paper.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "regional_ground.json"

# Fixed inks, not tokens: every figure that carries this sits on its own light
# card, in both colour schemes.
CSS = """
.rg-land,.rg-abroad{fill:#f7f1e3;stroke:#c9b895;stroke-width:.8;stroke-linejoin:round}
.rg-abroad{fill:#ece5d6}
.rg-border{fill:none;stroke:#8a7a62;stroke-width:1.6;stroke-dasharray:6 3;stroke-linejoin:round}
.rg-road{fill:none;stroke:#d8b27a;stroke-width:.9;stroke-linejoin:round;stroke-linecap:round}
.rg-road.big{stroke-width:1.5}
.rg-river{fill:none;stroke:#7fa9cc;stroke-width:1.1;stroke-linejoin:round;stroke-linecap:round}
.rg-river.big{stroke-width:2.2}
.rg-provname{font-size:10.5px;fill:#9a8a70;letter-spacing:.02em}
.rg-rivername{font-size:10px;fill:#4f7ca3;font-style:italic}
.rg-provname,.rg-rivername{paint-order:stroke;stroke:#f7f1e3;stroke-width:3px;stroke-linejoin:round}
"""

_cache = {}


def load():
    if "g" not in _cache:
        try:
            _cache["g"] = json.loads(DATA.read_text())
        except (OSError, ValueError):
            _cache["g"] = None
    return _cache["g"]


def _d(pts, xy, W, H, close=False, clip=True):
    """A path's d attribute in whole units, relative after the first point.

    Lines drop their off-frame runs (one vertex of margin kept so a line still
    reaches the edge). Polygons are clamped to the frame plus a margin instead,
    which keeps the fill right inside the frame and costs a few bytes for the
    parts outside it.
    """
    m = 40
    P = [xy(p[0], p[1]) for p in pts]

    def on(q):
        return -m <= q[0] <= W + m and -m <= q[1] <= H + m

    out, last, pen = [], None, False
    for i, q in enumerate(P):
        if not clip:
            q = (min(max(q[0], -m), W + m), min(max(q[1], -m), H + m))
        elif not (on(q) or (i and on(P[i - 1])) or (i + 1 < len(P) and on(P[i + 1]))):
            pen = False
            continue
        r = (round(q[0]), round(q[1]))
        if pen:
            if r == last:
                continue
            out.append("l%d %d" % (r[0] - last[0], r[1] - last[1]))
        else:
            out.append("M%d %d" % r)
        last, pen = r, True
    if close and out:
        out.append("z")
    return "".join(out)


def _bbox_hits(pts, xy, W, H):
    xs, ys = zip(*(xy(p[0], p[1]) for p in pts))
    return max(xs) >= 0 and min(xs) <= W and max(ys) >= 0 and min(ys) <= H


def _area(ring):
    a = 0.0
    for (y1, x1), (y2, x2) in zip(ring, ring[1:] + ring[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def _centroid(ring):
    a = cx = cy = 0.0
    for (y1, x1), (y2, x2) in zip(ring, ring[1:] + ring[:1]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    if not a:
        return ring[0]
    return (cy / (3 * a), cx / (3 * a))


def contains(g, iso, lat, lng):
    """True when (lat, lng) falls inside province `iso` (ray casting over its
    rings). None when the province is not held."""
    prov = next((p for p in (g or {}).get("provinces", []) if p["iso"] == iso), None)
    if not prov:
        return None
    for ring in prov["rings"]:
        inside = False
        for (y1, x1), (y2, x2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > lat) != (y2 > lat) and lng < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                inside = not inside
        if inside:
            return True
    return False


def label_point(g, iso, xy):
    """The middle of a province's largest ring, projected."""
    prov = next((p for p in (g or {}).get("provinces", []) if p["iso"] == iso), None)
    if not prov:
        return None
    ring = max(prov["rings"], key=_area)
    c = _centroid(ring)
    return xy(c[0], c[1])


def thai_name(p):
    n = p.get("th") or ""
    return n[len("จังหวัด"):] if n.startswith("จังหวัด") else n


def svg(g, xy, W, H, *, roads=True, rivers=True, names=True, river_names=(),
        skip_names=(), road_rank=8, avoid=()):
    """The ground as one <g>, drawn before the caller's pins.

    names         label the provinces in frame (Thai inside Thailand, English
                  beyond it), at each province's own middle
    river_names   the rivers to name on the drawing, by English name
    skip_names    ISO codes whose name the caller prints itself
    road_rank     Natural Earth scalerank floor for roads (lower = bigger)
    avoid         (x, y[, half-width]) centres of what the caller draws on top —
                  pins and their labels; a province or river name that would
                  land on one is left off
    """
    if not g:
        return ""
    o = ['<g class="rg" aria-hidden="true">']
    provs = [p for p in g["provinces"]
             if any(_bbox_hits(r, xy, W, H) for r in p["rings"])]
    # Home ground pale, the neighbours a shade darker, so the border reads
    # before any line is drawn; each province's outline rides its own fill.
    for p in provs:
        cls = "rg-land" if p["country"] == "THA" else "rg-abroad"
        d = "".join(_d(r, xy, W, H, close=True, clip=False) for r in p["rings"]
                    if _bbox_hits(r, xy, W, H))
        o.append('<path class="%s" d="%s"/>' % (cls, d))
    if roads:
        for big in (False, True):
            d = "".join(_d(ln, xy, W, H) for r in g["roads"]
                        if (r["rank"] <= 5) == big and r["rank"] <= road_rank
                        for ln in r["lines"])
            if d:
                o.append('<path class="rg-road%s" d="%s"/>' % (" big" if big else "", d))
    if rivers:
        for r in g["rivers"]:
            d = "".join(_d(ln, xy, W, H) for ln in r["lines"])
            if d:
                big = " big" if r["en"] in ("Mekong", "Salween") else ""
                o.append('<path class="rg-river%s" d="%s"><title>%s</title></path>'
                         % (big, d, _esc(" · ".join(x for x in (r.get("th"), r["en"]) if x))))
    for c in g["countries"]:
        d = "".join(_d(ln, xy, W, H) for ln in c["lines"])
        if d:
            o.append('<path class="rg-border" d="%s"/>' % d)
    taken = [(a[0], a[1], a[2] if len(a) > 2 else 12) for a in avoid]

    def free(x, y, half):
        return all(abs(x - ax) > half + aw or abs(y - ay) > 16 for ax, ay, aw in taken)

    if names:
        # Biggest first, so a small province never pushes out a large one.
        for p in sorted(provs, key=lambda p: -max(_area(r) for r in p["rings"])):
            if p["iso"] in skip_names:
                continue
            q = label_point(g, p["iso"], xy)
            if not q or not (30 <= q[0] <= W - 30 and 14 <= q[1] <= H - 10):
                continue
            nm = thai_name(p) if p["country"] == "THA" else p["en"]
            half = len(nm) * 3.2
            if not free(q[0], q[1], half):
                continue
            taken.append((q[0], q[1], half))
            o.append('<text class="rg-provname" x="%.0f" y="%.0f" text-anchor="middle">%s</text>'
                     % (q[0], q[1], _esc(nm)))
    for r in g["rivers"]:
        if r["en"] not in river_names:
            continue
        nm = r.get("th") or r["en"]
        half = len(nm) * 3.0
        pts = [xy(a, b) for ln in r["lines"] for a, b in ln]
        pts = [q for q in pts if 40 <= q[0] <= W - 60 and 20 <= q[1] <= H - 20]
        # From the middle of the drawn run outward, the first spot not taken.
        order = sorted(range(len(pts)), key=lambda i: abs(i - len(pts) // 2))
        for i in order:
            x, y = pts[i][0] + 5 + half, pts[i][1] - 4
            if free(x, y, half):
                taken.append((x, y, half))
                o.append('<text class="rg-rivername" x="%.0f" y="%.0f" text-anchor="middle">%s</text>'
                         % (x, y, _esc(nm)))
                break
    o.append("</g>")
    return "".join(o)


def route_d(g, key, xy, W, H):
    """A road route's path data and its figures, or (None, None)."""
    r = next((x for x in (g or {}).get("routes", []) if x["key"] == key), None)
    if not r:
        return None, None
    return _d(r["line"], xy, W, H, clip=False), r


def credit(g):
    """The one-line credit for the figure's caption."""
    if not g:
        return ""
    return ("Natural Earth (public domain) · © OpenStreetMap contributors (ODbL)")


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))
