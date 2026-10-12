#!/usr/bin/env python3
"""The big map on the front page: her own pins, drawn.

Two layers, each in the container that suits it.

  1  the places — 88,901 of them. As SVG that is half a megabyte of circles, so
     the density is rendered once to a PNG at the shared projection (light and
     dark), the same trade mhs-loop's terrain.py makes.
  2  the districts — 43 amphoe polygons, as SVG over the picture, because they
     carry a name, a record count and a link into the live map.

    python3 mapart.py          # writes img/map-dots-{light,dark}.png, reports sizes
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
MD = pathlib.Path.home() / "Developer/claude code projects/mot-dang"
W = 1400
PAD = 10

# Two provinces, one ground truth for both: the boundary set's own bbox.
BOUND = json.loads((MD / "data/admin_boundaries.json").read_text())
AMPHOE = [f for f in BOUND["levels"]["amphoe"]["features"]
          if f["properties"].get("province") in ("cm", "cr")]   # the art is the north pair

CITY = [("เชียงใหม่", "Chiang Mai", 18.7883, 98.9853, "cm"),
        ("เชียงราย", "Chiang Rai", 19.9105, 99.8406, "cr")]


def _rings(g):
    c = g["coordinates"]
    return c if g["type"] == "Polygon" else [r for p in c for r in p]


def bbox():
    xs, ys = [], []
    for f in AMPHOE:
        for r in _rings(f["geometry"]):
            for x, y in r:
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


class Proj:
    """Equirectangular with x scaled by cos(mean latitude) — geo.py's projection,
    which is under a percent out over a box this size."""

    def __init__(self, width=W, pad=PAD):
        self.w, self.s, self.e, self.n = bbox()
        self.kx = math.cos(math.radians((self.s + self.n) / 2))
        self.pad = pad
        self.scale = (width - 2 * pad) / ((self.e - self.w) * self.kx)
        self.width = width
        self.height = (self.n - self.s) * self.scale + 2 * pad

    def xy(self, lon, lat):
        return (self.pad + (lon - self.w) * self.kx * self.scale,
                self.pad + (self.n - lat) * self.scale)


def shelf_files():
    d = MD / "docs/data"
    return sorted(p for p in d.glob("c[mr]-*.geojson") if "-tag-" not in p.name)


def points():
    """Every pin on the site, with its shelf and province."""
    for p in shelf_files():
        pv, key = p.name[:2], p.name[3:-8]
        for ft in json.loads(p.read_text())["features"]:
            x, y = ft["geometry"]["coordinates"]
            yield pv, key, x, y


# ---------------------------------------------------------------- the picture

def render_dots(pj, pts, out, ink, glow, gamma=0.62):
    """Density, accumulated then toned. A dot is a 3x3 kernel so a single place is
    visible at this scale and a market street turns solid."""
    from PIL import Image
    Wd, H = int(pj.width), int(pj.height)
    acc = [0.0] * (Wd * H)
    K = ((0, 0, 1.0), (-1, 0, .42), (1, 0, .42), (0, -1, .42), (0, 1, .42),
         (-1, -1, .16), (1, -1, .16), (-1, 1, .16), (1, 1, .16))
    n = 0
    for x, y in pts:
        px, py = pj.xy(x, y)
        ix, iy = int(px), int(py)
        if not (1 <= ix < Wd - 1 and 1 <= iy < H - 1):
            continue
        n += 1
        for dx, dy, wt in K:
            acc[(iy + dy) * Wd + ix + dx] += wt
    img = Image.new("RGBA", (Wd, H), (0, 0, 0, 0))
    px = img.load()
    for i, v in enumerate(acc):
        if v <= 0:
            continue
        a = 1.0 - math.exp(-v * 1.25)          # saturating, so a dense street reads
        t = min(1.0, (v / 6.0) ** gamma)        # and shifts colour as it saturates
        c = tuple(round(ink[k] + (glow[k] - ink[k]) * t) for k in range(3))
        px[i % Wd, i // Wd] = c + (round(255 * min(1.0, a ** .85)),)
    # 48 colours instead of truecolour: the picture is one hue fading to another, and
    # the palette takes it from 248 kB to 70 with nothing visible lost. Rural
    # connections carry this page too.
    img.quantize(colors=48, method=Image.FASTOCTREE).save(out, optimize=True)
    return n, out.stat().st_size


# ---------------------------------------------------------------- the shapes

def simplify(ring, tol):
    """Douglas-Peucker, in projected units. Keeps a district's shape at the width
    it is drawn at and drops the points that land on top of each other."""
    if len(ring) < 3:
        return ring
    keep = [0, len(ring) - 1]
    stack = [(0, len(ring) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        (ax, ay), (bx, by) = ring[a], ring[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        far, fd = None, tol
        for i in range(a + 1, b):
            x, y = ring[i]
            # a closed ring starts and ends on the same point, and the distance to a
            # zero-length segment is the distance to the point itself — without this
            # the first split finds nothing and every district collapses to a line.
            d = (math.hypot(x - ax, y - ay) if L < 1e-9
                 else abs(dy * x - dx * y + bx * ay - by * ax) / L)
            if d > fd:
                far, fd = i, d
        if far:
            keep.append(far)
            stack += [(a, far), (far, b)]
    return [ring[i] for i in sorted(set(keep))]


def amphoe_paths(pj, counts, tol=1.1):
    out = []
    for f in AMPHOE:
        pr = f["properties"]
        d = []
        for r in _rings(f["geometry"]):
            pts = [pj.xy(x, y) for x, y in r]
            pts = simplify(pts, tol)
            seg, last = [], None
            for x, y in pts:
                xy = (round(x), round(y))
                if xy == last:
                    continue
                seg.append(f"{'M' if not seg else 'L'}{xy[0]} {xy[1]}")
                last = xy
            if len(seg) > 2:
                d.append("".join(seg) + "Z")
        if d:
            out.append((pr, "".join(d)))
    return out


def count_by_amphoe(pj):
    """Records per district, by point-in-polygon against the same shapes that are
    drawn. Bounding boxes first, so this is one pass over 88,901 pins."""
    prepared = []
    for f in AMPHOE:
        rings = _rings(f["geometry"])
        xs = [p[0] for r in rings for p in r]
        ys = [p[1] for r in rings for p in r]
        prepared.append((f["properties"], (min(xs), min(ys), max(xs), max(ys)), rings))
    counts = {p[0]["pcode"]: 0 for p in prepared}
    for _pv, _k, x, y in points():
        for pr, (x0, y0, x1, y1), rings in prepared:
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            inside = False
            for r in rings:
                c, j = False, len(r) - 1
                for i in range(len(r)):
                    xi, yi = r[i]
                    xj, yj = r[j]
                    if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
                        c = not c
                    j = i
                inside ^= c
            if inside:
                counts[pr["pcode"]] += 1
                break
    return counts


if __name__ == "__main__":
    pj = Proj()
    print(f"canvas {int(pj.width)}x{int(pj.height)}")
    pts = [(x, y) for _pv, _k, x, y in points()]
    print("points", len(pts))
    out_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "img"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, ink, glow in (("light", (0xC8, 0x54, 0x2B), (0xE0, 0x32, 0x2B)),
                            ("dark", (0x8A, 0x63, 0x2A), (0xFF, 0xC2, 0x3D))):
        n, size = render_dots(pj, pts, out_dir / f"map-dots-{name}.png", ink, glow)
        print(f"  {name}: {n} drawn, {size/1024:.0f} kB")
    c = count_by_amphoe(pj)
    print("districts", len(c), "counted", sum(c.values()))
    json.dump(c, open(HERE / "amphoe_counts.json", "w"))
    paths = amphoe_paths(pj, c)
    print("path bytes", sum(len(d) for _p, d in paths))
