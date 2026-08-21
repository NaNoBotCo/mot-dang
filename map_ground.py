#!/usr/bin/env python3
"""map_ground.py — the ground under every drawn map, for the pictures Python makes.

WHY THIS EXISTS
---------------
map_shell.py put a basemap under the maps the *browser* draws: it mounts
MapLibre over the SVG in the same box, at the same centre, from our own
cm-cr.pmtiles. That fixed every live map on the site and left a whole second
family of maps untouched — the ones Python draws with Pillow and saves as a
file: the plan GIFs, the share cards, the posters, the handouts. Those are
still pins on a cream rectangle, and they are the pictures that travel: a share
card is what LINE and Facebook show, and it is the only map most people who
meet this site will ever look at.

A browser can fetch a .pmtiles over HTTP ranges. Pillow cannot. So this module
is the reading half of map_shell, in Python and off the disk: a PMTiles v3
reader, a Mapbox-Vector-Tile decoder, and a painter that lays the same ground
in the same palette as data/basemap_style.json.

THE ONE DESIGN DECISION WORTH ARGUING WITH
------------------------------------------
This does not stitch pre-rendered tile images and reproject them under the
drawing. It decodes the vector tiles to lng/lat and hands the geometry back so
the *caller's own projector* draws it. That costs a little speed and buys the
thing that matters: the ground and the pins are projected by one function, so
they cannot drift apart by a pixel, and each picture keeps the framing it
already chose. A picture that is 4 px out is worse than no basemap, because it
is wrong in a way that looks deliberate.

USE
---
    import map_ground
    g = map_ground.Ground()                 # falls back to nothing if no file
    if g.available:
        g.paint(im, xy, bbox, width_px=W)   # xy = the caller's (lat,lng)->(x,y)

`available` False is a supported state, exactly as in map_shell: the caller
keeps the plain paper it always had. Nothing here ever raises on a missing or
truncated archive.

    python3 map_ground.py                   # self-check + a sample PNG

Reads assets/tiles/cm-cr.pmtiles (the same file publish/deploy.py pushes to
R2). Nothing here touches the network.
"""

import collections
import gzip
import io
import json
import math
import os
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TILES = ROOT / "assets" / "tiles" / "cm-cr.pmtiles"

# ---------------------------------------------------------------- the palette
# Lifted from data/basemap_style.json so the drawn pictures and the live maps
# are the same map. Read at import from the file when it is there, so changing
# the site's ground colour changes both at once; the literals are the fallback
# and are kept in sync by tests/test_ground.py.
PALETTE = {
    "paper":      (251, 246, 236),      # #FBF6EC
    "green":      (192, 210, 163),      # #C0D2A3
    "built":      (230, 213, 180),      # #E6D5B4
    "water":      (143, 174, 201),      # #8FAEC9
    "water_line": (97, 139, 178),      # #618BB2
    "building":   (212, 188, 144),      # #D4BC90
    "casing":     (179, 144, 88),      # #B39058
    "minor":      (255, 253, 248),      # #FFFDF8
    "major":      (255, 252, 244),      # #FFFCF4
    "highway":    (232, 184, 102),      # #E8B866
}


# The night ground. Two pictures on this site are deliberately dark — the
# toilets constellation and the nitnoy lamp map — because a map of what is lit
# right now has to read as night. They were dark rectangles with dots on them,
# which is the same "pins on paper" problem in a different colour, so they get
# the same city underneath in a palette that lets a lamp be the brightest thing
# in the frame. Nothing here is inverted from the day palette; every value is
# picked so that #f6b73c lamp light sits at least four steps above the ground.
PALETTE_NIGHT = {
    "paper":      (13, 20, 32),
    "green":      (18, 30, 30),
    "built":      (20, 27, 40),
    # Water has to read AS water at night. The first pass had this three steps
    # off the paper colour, which made the Ping a thin line and the moat —
    # a body of water 1.6 km on a side — completely invisible.
    "water":      (19, 42, 70),
    "water_line": (44, 74, 112),
    "building":   (21, 30, 45),
    "casing":     (25, 36, 53),
    "minor":      (35, 48, 68),
    "major":      (45, 60, 84),
    "highway":    (58, 74, 100),
}


def _hex(s, default):
    s = (s or "").lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return default
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return default


def _area(pts):
    """Shoelace, in screen coordinates (y down). Positive is an exterior ring
    in MVT's winding, negative is a hole."""
    a = 0.0
    for i in range(len(pts) - 1):
        a += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
    a += pts[-1][0] * pts[0][1] - pts[0][0] * pts[-1][1]
    return a / 2.0


def _mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _load_palette():
    p = ROOT / "data" / "basemap_style.json"
    try:
        style = json.loads(p.read_text())
    except (OSError, ValueError):
        return dict(PALETTE)
    out = dict(PALETTE)
    by_id = {l.get("id"): l for l in style.get("layers", [])}

    def paint(lid, key):
        v = (by_id.get(lid) or {}).get("paint", {}).get(key)
        return v if isinstance(v, str) else None
    for lid, key, slot in (
        ("earth", "background-color", "paper"),
        ("landuse-green", "fill-color", "green"),
        ("landuse-built", "fill-color", "built"),
        ("water", "fill-color", "water"),
        ("water-line", "line-color", "water_line"),
        ("buildings", "fill-color", "building"),
        ("roads-casing", "line-color", "casing"),
        ("roads-minor", "line-color", "minor"),
        ("roads-major", "line-color", "major"),
        ("roads-highway", "line-color", "highway"),
    ):
        c = _hex(paint(lid, key), None)
        if c:
            out[slot] = c
    return out


# --------------------------------------------------------------- web mercator
def lnglat_to_tile(lng, lat, z):
    n = 1 << z
    x = (lng + 180.0) / 360.0 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def tile_to_lnglat(x, y, z):
    n = 1 << z
    lng = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lng, lat


def zxy_to_tileid(z, x, y):
    """The Hilbert index PMTiles orders its directories by."""
    acc = 0
    for t in range(z):
        acc += (1 << t) * (1 << t)
    n = 1 << z
    d, s = 0, n >> 1
    tx, ty = x, y
    while s > 0:
        rx = 1 if (tx & s) > 0 else 0
        ry = 1 if (ty & s) > 0 else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                tx, ty = s - 1 - tx, s - 1 - ty
            tx, ty = ty, tx
        s >>= 1
    return acc + d


# ------------------------------------------------------------- protobuf, thin
def _varint(buf, i):
    r, sh = 0, 0
    while True:
        b = buf[i]
        i += 1
        r |= (b & 0x7F) << sh
        if not b & 0x80:
            return r, i
        sh += 7


def _fields(buf, i=0, end=None):
    """Yield (field_number, wire_type, value_or_(start,end))."""
    end = len(buf) if end is None else end
    while i < end:
        key, i = _varint(buf, i)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(buf, i)
            yield fn, wt, v
        elif wt == 1:
            yield fn, wt, buf[i:i + 8]
            i += 8
        elif wt == 2:
            ln, i = _varint(buf, i)
            yield fn, wt, (i, i + ln)
            i += ln
        elif wt == 5:
            yield fn, wt, buf[i:i + 4]
            i += 4
        else:                                   # groups: not in MVT
            raise ValueError("wire type %d" % wt)


def _packed(buf, s, e):
    out, i = [], s
    while i < e:
        v, i = _varint(buf, i)
        out.append(v)
    return out


def _zig(v):
    return (v >> 1) ^ -(v & 1)


# --------------------------------------------------------------- PMTiles v3
class _Archive:
    """Just enough PMTiles to pull a tile off local disk by z/x/y."""

    HDR = 127

    def __init__(self, path):
        self.path = Path(path)
        self.fh = open(self.path, "rb")
        h = self.fh.read(self.HDR)
        if len(h) < self.HDR or h[:7] != b"PMTiles" or h[7] != 3:
            raise ValueError("not a PMTiles v3 archive")
        (self.root_off, self.root_len, self.meta_off, self.meta_len,
         self.leaf_off, self.leaf_len, self.data_off, self.data_len) = \
            struct.unpack_from("<8Q", h, 8)
        self.clustered = h[96]
        self.internal_compression = h[97]
        self.tile_compression = h[98]
        self.tile_type = h[99]
        self.min_zoom, self.max_zoom = h[100], h[101]
        w, s, e, n = struct.unpack_from("<4i", h, 102)
        self.bounds = (s / 1e7, w / 1e7, n / 1e7, e / 1e7)   # S,W,N,E
        self._root = self._directory(self.root_off, self.root_len)
        self._leaves = {}

    def close(self):
        try:
            self.fh.close()
        except OSError:
            pass

    def _read(self, off, ln):
        self.fh.seek(off)
        return self.fh.read(ln)

    @staticmethod
    def _decompress(blob, kind):
        if kind in (0, 1) or not blob:
            return blob
        if kind == 2:
            return gzip.decompress(blob)
        if kind == 3:
            try:
                import brotli
            except ImportError:
                raise ValueError("archive is brotli-compressed; pip install brotli")
            return brotli.decompress(blob)
        if kind == 4:
            try:
                import zstandard
            except ImportError:
                raise ValueError("archive is zstd-compressed; pip install zstandard")
            return zstandard.ZstdDecompressor().decompress(blob)
        raise ValueError("unknown compression %d" % kind)

    def _directory(self, off, ln):
        buf = self._decompress(self._read(off, ln), self.internal_compression)
        i = 0
        n, i = _varint(buf, i)
        ids, runs, lens, offs = [0] * n, [0] * n, [0] * n, [0] * n
        last = 0
        for k in range(n):
            d, i = _varint(buf, i)
            last += d
            ids[k] = last
        for k in range(n):
            runs[k], i = _varint(buf, i)
        for k in range(n):
            lens[k], i = _varint(buf, i)
        for k in range(n):
            v, i = _varint(buf, i)
            offs[k] = (offs[k - 1] + lens[k - 1]) if v == 0 and k > 0 else v - 1
        return list(zip(ids, runs, lens, offs))

    @staticmethod
    def _find(entries, tid):
        lo, hi = 0, len(entries) - 1
        found = None
        while lo <= hi:                          # last entry with id <= tid
            mid = (lo + hi) // 2
            if entries[mid][0] <= tid:
                found, lo = entries[mid], mid + 1
            else:
                hi = mid - 1
        if not found:
            return None
        tid_, run, ln, off = found
        if run == 0:
            return ("leaf", off, ln)
        if tid < tid_ + run:
            return ("tile", off, ln)
        return None

    def tile(self, z, x, y):
        """Raw (decompressed) tile bytes, or None."""
        if z > self.max_zoom or z < self.min_zoom:
            return None
        tid = zxy_to_tileid(z, x, y)
        entries = self._root
        for _ in range(4):                       # v3 allows nested leaves
            hit = self._find(entries, tid)
            if hit is None:
                return None
            kind, off, ln = hit
            if kind == "tile":
                return self._decompress(self._read(self.data_off + off, ln),
                                        self.tile_compression)
            key = (off, ln)
            if key not in self._leaves:
                self._leaves[key] = self._directory(self.leaf_off + off, ln)
            entries = self._leaves[key]
        return None


# ------------------------------------------------------------------- the MVT
def decode_tile(blob, z, x, y, want=None):
    """{layer_name: [(props, geom_type, [ring_or_line_of_(lng,lat)]), ...]}.

    Coordinates come out in degrees, so the caller's projector is the only
    projector in the picture.
    """
    out = {}
    if not blob:
        return out
    for fn, wt, val in _fields(blob):
        if fn != 3 or wt != 2:
            continue
        s, e = val
        name, extent, feats = None, 4096, []
        keys, vals = [], []
        raw = []
        for lfn, lwt, lval in _fields(blob, s, e):
            if lfn == 1 and lwt == 2:
                name = blob[lval[0]:lval[1]].decode("utf-8", "replace")
            elif lfn == 5 and lwt == 0:
                extent = lval or 4096
            elif lfn == 3 and lwt == 2:
                keys.append(blob[lval[0]:lval[1]].decode("utf-8", "replace"))
            elif lfn == 4 and lwt == 2:
                vals.append(_value(blob, lval[0], lval[1]))
            elif lfn == 2 and lwt == 2:
                raw.append(lval)
        if not name or (want and name not in want):
            continue
        n = 1 << z
        for fs, fe in raw:
            tags, gtype, geom = [], 0, []
            for ffn, ffwt, ffval in _fields(blob, fs, fe):
                if ffn == 2 and ffwt == 2:
                    tags = _packed(blob, *ffval)
                elif ffn == 3 and ffwt == 0:
                    gtype = ffval
                elif ffn == 4 and ffwt == 2:
                    geom = _packed(blob, *ffval)
            props = {}
            for k in range(0, len(tags) - 1, 2):
                ki, vi = tags[k], tags[k + 1]
                if ki < len(keys) and vi < len(vals):
                    props[keys[ki]] = vals[vi]
            rings = []
            for ring in _geometry(geom):
                pts = []
                for px, py in ring:
                    lng, lat = tile_to_lnglat(x + px / extent, y + py / extent, z)
                    pts.append((lng, lat))
                if pts:
                    rings.append(pts)
            if rings:
                feats.append((props, gtype, rings))
        if feats:
            out.setdefault(name, []).extend(feats)
    return out


def _value(buf, s, e):
    for fn, wt, val in _fields(buf, s, e):
        if fn == 1:
            return buf[val[0]:val[1]].decode("utf-8", "replace")
        if fn == 2:
            return struct.unpack("<f", val)[0]
        if fn == 3:
            return struct.unpack("<d", val)[0]
        if fn in (4, 5):
            return val
        if fn == 6:
            return _zig(val)
        if fn == 7:
            return bool(val)
    return None


def _geometry(cmds):
    """MVT command stream -> list of point runs in tile units."""
    rings, cur = [], []
    i, cx, cy = 0, 0, 0
    while i < len(cmds):
        head = cmds[i]
        i += 1
        cmd, count = head & 0x7, head >> 3
        if cmd == 1:                             # MoveTo
            for _ in range(count):
                if i + 1 >= len(cmds):
                    break
                cx += _zig(cmds[i])
                cy += _zig(cmds[i + 1])
                i += 2
                if cur:
                    rings.append(cur)
                cur = [(cx, cy)]
        elif cmd == 2:                           # LineTo
            for _ in range(count):
                if i + 1 >= len(cmds):
                    break
                cx += _zig(cmds[i])
                cy += _zig(cmds[i + 1])
                i += 2
                cur.append((cx, cy))
        elif cmd == 7:                           # ClosePath
            if cur:
                cur.append(cur[0])
                rings.append(cur)
                cur = []
        else:
            break
    if cur:
        rings.append(cur)
    return rings


# ------------------------------------------------------------------ the paint
GROUND_LAYERS = ("water", "landuse", "landcover", "roads", "buildings")

# How wide each road kind is ON THE GROUND, in metres, with a floor in pixels
# so a road never disappears entirely from a wide frame.
#
# These started as fractions of the picture's width, which is wrong in a way
# that took the moat to expose: a fraction-of-width road is the same thickness
# whether the picture covers 500 m or 5 km, so on a city-wide frame a "major
# road" became forty metres of ink, the two carriageways of the moat road met
# in the middle, and the canal between them — the defining shape of Chiang Mai
# — was painted out. In metres the same road is drawn the width it is, the
# moat has room to be water, and every frame gets the weight its scale earns.
# The floors are what stop a soi vanishing when the frame is a whole province.
ROAD_M = {"highway": (20.0, 2.2), "major_road": (13.0, 1.6),
          "minor_road": (7.0, 1.0), "other": (4.5, 0.8), "path": (3.0, 0.7)}
ROAD_ORDER = ("path", "other", "minor_road", "major_road", "highway")


class Ground:
    """The basemap, as pixels or as geometry, for the pictures Python makes.

    Ground() is cheap and safe: no file, no archive, or a broken one just gives
    you .available == False and every caller keeps its paper.
    """

    TILE_CACHE = 900          # decoded tiles held; see .tile()

    def __init__(self, path=None, palette=None, night=False):
        self.path = Path(path or os.environ.get("MD_TILES") or TILES)
        self.night = night
        if night:
            self.palette = dict(PALETTE_NIGHT)
        else:
            self.palette = dict(PALETTE)
            self.palette.update(_load_palette())
        if palette:
            self.palette.update(palette)
        self.archive = None
        self.error = None
        self._tiles = collections.OrderedDict()
        try:
            if self.path.exists() and self.path.stat().st_size > 1000:
                self.archive = _Archive(self.path)
        except (OSError, ValueError, struct.error) as exc:
            self.error = str(exc)


    @property
    def available(self):
        return self.archive is not None

    # -- reading ------------------------------------------------------------
    def zoom_for(self, bbox, width_px, tile_px=512):
        """The zoom whose tiles carry about as much detail as the picture can
        show. Protomaps generalises per zoom, so asking for one zoom too low
        loses the sois and one too high just costs time."""
        s, w, n, e = bbox
        span = max(abs(e - w), 1e-6)
        z = math.log2(width_px / tile_px * 360.0 / span)
        lo = self.archive.min_zoom if self.archive else 0
        hi = self.archive.max_zoom if self.archive else 15
        return max(lo, min(hi, int(round(z))))

    def tile(self, z, x, y, want):
        """One decoded tile, kept.

        THE CACHE IS WHAT MAKES TWELVE THOUSAND MAPS POSSIBLE. Decoding a
        vector tile costs 30–100 ms, and a place page needs one to four of
        them; done fresh for every place that is 27 minutes of build for a
        site that builds in two. Cached by tile rather than by bounding box —
        the old cache was keyed on the box, which meant two shops on the same
        soi shared nothing — neighbouring places reuse the same four tiles and
        the cost collapses to the geometry work.

        Bounded, because a decoded z15 tile is a few hundred kilobytes and
        both provinces would not fit in memory. Least-recently-used goes
        first; at 900 the working set of a whole build stays resident.
        """
        key = (z, x, y, want)
        hit = self._tiles.get(key)
        if hit is not None:
            self._tiles.move_to_end(key)
            return hit
        try:
            blob = self.archive.tile(z, x, y)
        except (OSError, ValueError, zlib.error, struct.error):
            blob = None
        got = {}
        if blob:
            try:
                got = decode_tile(blob, z, x, y, want)
            except (ValueError, IndexError, struct.error):
                got = {}
        self._tiles[key] = got
        if len(self._tiles) > self.TILE_CACHE:
            self._tiles.popitem(last=False)
        return got

    def fetch(self, bbox, zoom, want=GROUND_LAYERS):
        """Every feature of `want` touching bbox, in degrees."""
        if not self.available:
            return {}
        s, w, n, e = bbox
        x0, y0 = lnglat_to_tile(w, n, zoom)
        x1, y1 = lnglat_to_tile(e, s, zoom)
        out = {}
        lim = 1 << zoom
        for tx in range(max(0, int(x0)), min(lim - 1, int(x1)) + 1):
            for ty in range(max(0, int(y0)), min(lim - 1, int(y1)) + 1):
                for k, v in self.tile(zoom, tx, ty, want).items():
                    out.setdefault(k, []).extend(v)
        return out

    # -- painting -----------------------------------------------------------
    def paint(self, im, xy, bbox, width_px=None, zoom=None, scale=1.0,
              buildings=True, water=True, fade=1.0, contrast=1.0):
        """Lay the ground into `im` under the caller's own projector.

        xy      (lat, lng) -> (x, y), the exact function the caller draws pins
                with. Nothing here reprojects anything.
        bbox    (S, W, N, E) in degrees — what the picture covers.
        scale   multiply road widths (supersampled canvases pass SS).
        fade    0..1 blend towards paper, for when the ground must stay quiet
                behind heavy overlay.
        contrast
                >1 darkens the road casing and the water edge. The live style
                is tuned for a screen-sized map with room to breathe; the same
                colours in a 500 px card go to porridge, because the casing is
                doing all the work of drawing the street and there is no longer
                a pixel of it. Nothing else is touched — the fills stay exactly
                the site's, so a card and the live map are still one map.
        Returns True if anything was drawn.
        """
        if not self.available:
            return False
        from PIL import Image, ImageDraw

        W = width_px or im.size[0]
        z = zoom if zoom is not None else self.zoom_for(bbox, W)
        want = tuple(l for l in GROUND_LAYERS
                     if (l != "buildings" or buildings) and (l != "water" or water))
        data = self.fetch(bbox, z, want)
        if not data:
            return False

        layer = Image.new("RGB", im.size, self.palette["paper"])
        d = ImageDraw.Draw(layer)
        P = dict(self.palette)
        if contrast > 1.0:
            # Day darkens the casing; night lifts it. Both are the same move —
            # push the street edge further from the ground it sits on.
            t = min(1.0, (contrast - 1.0))
            P["casing"] = _mix(P["casing"], (72, 96, 136) if self.night
                               else (150, 132, 105), t)
            P["water_line"] = _mix(P["water_line"], (86, 118, 165), t)

        W_px, H_px = im.size

        def poly(rings, colour):
            """One polygon feature, holes and all.

            Filling every ring of a feature separately is the obvious way and
            it is wrong in exactly one place that matters: the moat. A moat is
            a ring — an outer square with an inner square cut out of it — and
            drawing both rings solid fills the entire old city with water,
            which then gets papered over by the buildings drawn on top and
            reads as a faint blue smear instead of as the most recognisable
            shape in Chiang Mai. Same bug, quieter, on every lake with an
            island and every park with a car park in the middle.

            MVT orders exterior rings clockwise and their holes anti-clockwise,
            so the sign of the shoelace area says which is which. Multi-ring
            features are composed through a mask cropped to the feature; single
            -ring ones — which is nearly all of them, every building on the
            map — keep the fast path.
            """
            if len(rings) == 1:
                if len(rings[0]) >= 3:
                    d.polygon([xy((lat, lng)) for lng, lat in rings[0]], fill=colour)
                return
            shot = [[xy((lat, lng)) for lng, lat in r] for r in rings if len(r) >= 3]
            if not shot:
                return
            xs = [p[0] for r in shot for p in r]
            ys = [p[1] for r in shot for p in r]
            x0, y0 = max(0, int(min(xs)) - 1), max(0, int(min(ys)) - 1)
            x1, y1 = min(W_px, int(max(xs)) + 2), min(H_px, int(max(ys)) + 2)
            if x1 <= x0 or y1 <= y0:
                return
            areas = [_area(r) for r in shot]
            outer = max(range(len(shot)), key=lambda i: abs(areas[i]))
            mask = Image.new("1", (x1 - x0, y1 - y0), 0)
            md = ImageDraw.Draw(mask)
            for i, r in enumerate(shot):
                # If nothing claims to be an exterior ring, the biggest one is.
                hole = areas[i] < 0 and not (i == outer and max(areas) <= 0)
                md.polygon([(p[0] - x0, p[1] - y0) for p in r], fill=0 if hole else 1)
            layer.paste(colour, (x0, y0), mask)

        for props, gt, rings in data.get("landcover", []):
            if gt == 3:
                kind = props.get("kind")
                poly(rings, P["green"] if kind in ("forest", "grassland", "scrub")
                     else P["built"])
        for props, gt, rings in data.get("landuse", []):
            if gt != 3:
                continue
            kind = props.get("kind")
            if kind in ("park", "forest", "garden", "recreation_ground", "pitch",
                        "cemetery", "grass", "nature_reserve", "wood"):
                poly(rings, P["green"])
            elif kind in ("school", "university", "hospital", "industrial",
                          "commercial", "retail", "military", "aerodrome"):
                poly(rings, P["built"])
        if water:
            for props, gt, rings in data.get("water", []):
                if gt == 3:
                    poly(rings, P["water"])
            wl = max(1, int(round(W * 0.0035 * scale)))
            for props, gt, rings in data.get("water", []):
                if gt == 2 and props.get("kind") in ("river", "stream", "canal"):
                    for r in rings:
                        if len(r) > 1:
                            d.line([xy((lat, lng)) for lng, lat in r],
                                   fill=P["water_line"], width=wl, joint="curve")
        if buildings:
            for props, gt, rings in data.get("buildings", []):
                if gt == 3:
                    poly(rings, P["building"])

        roads = [f for f in data.get("roads", []) if f[1] == 2]
        if roads:
            # Metres per pixel, from what the frame actually covers.
            bs, bw, bn, be = bbox
            mpp = ((be - bw) * 111320.0
                   * math.cos(math.radians((bn + bs) / 2))) / max(1, W)

            def width_of(kind, extra):
                metres, floor = ROAD_M.get(kind, ROAD_M["other"])
                px = max(metres / mpp, floor)
                return max(1, int(round(px * scale + extra)))

            casing = max(1, int(round(1.1 * scale)))
            for pass_ in ("casing", "fill"):
                for kind in ROAD_ORDER:
                    if pass_ == "casing" and kind in ("path", "other"):
                        continue
                    colour = (P["casing"] if pass_ == "casing" else
                              P["highway"] if kind == "highway" else
                              P["major"] if kind == "major_road" else P["minor"])
                    wpx = width_of(kind, casing * 2 if pass_ == "casing" else 0)
                    for props, gt, rings in roads:
                        k = props.get("kind") or "other"
                        if k != kind:
                            continue
                        for r in rings:
                            if len(r) > 1:
                                d.line([xy((lat, lng)) for lng, lat in r],
                                       fill=colour, width=wpx, joint="curve")

        if fade < 1.0:
            paper = Image.new("RGB", im.size, self.palette["paper"])
            layer = Image.blend(paper, layer, max(0.0, min(1.0, fade)))
        im.paste(layer, (0, 0))
        return True


    # -- a finished picture -------------------------------------------------
    def picture(self, center, size, span_m=700, buildings=True, fade=1.0,
                credit=True, scale=True, contrast=1.6):
        """A standalone ground image around a point — for the cards, which are
        HTML and cannot call paint() on their own canvas.

        center   (lat, lng)
        size     (w, h) pixels
        span_m   how many metres the SHORT side covers. 700 m is a
                 neighbourhood: you can see which soi it is on and still see
                 the landmark you would navigate by.
        Returns a PIL image, or None when there is no archive.
        """
        if not self.available:
            return None
        from PIL import Image

        w, h = size
        lat, lng = center
        short = min(w, h)
        dlat = (span_m / 111320.0) * (h / short)
        dlng = (span_m / (111320.0 * math.cos(math.radians(lat)))) * (w / short)
        bbox = (lat - dlat / 2, lng - dlng / 2, lat + dlat / 2, lng + dlng / 2)
        s, wl, n, e = bbox

        def xy(p):
            return ((p[1] - wl) / (e - wl) * w, (n - p[0]) / (n - s) * h)

        im = Image.new("RGB", (w, h), self.palette["paper"])
        z = self.zoom_for(bbox, w, 256)
        if not self.paint(im, xy, bbox, width_px=max(w, h), zoom=z,
                          buildings=buildings, fade=fade, contrast=contrast):
            return None
        px_per_km = w / (dlng * math.cos(math.radians(lat)) * 111.32)
        if scale:
            scale_bar(im, px_per_km, dark=self.night)
        if credit:
            credit_mark(im, dark=self.night)
        return im


# --------------------------------------------------------------- annotations
# Both of these are conditions of use rather than decoration: the credit is
# ODbL's, and a map with no scale on it is a picture of a place rather than a
# statement about it. Every surface that paints ground calls both.
FONTS = ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
         "/System/Library/Fonts/Thonburi.ttc",
         "/System/Library/Fonts/Supplemental/Arial.ttf"]
INK_SOFT = (111, 99, 83)


def font(size):
    from PIL import ImageFont
    for p in FONTS:
        try:
            return ImageFont.truetype(p, int(size))
        except OSError:
            continue
    return ImageFont.load_default()


def credit_mark(im, corner="br", scale=1.0, dark=False, inset=0):
    """© OpenStreetMap, on the picture itself.

    On the page the attribution control carries this. A card or a gif has no
    page around it — it gets reposted bare — so the credit is drawn into the
    pixels, which is the only form of it that survives a screenshot.
    """
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    W, H = im.size
    f = font(max(9, min(W, H) * 0.026) * scale)
    text = "© OpenStreetMap"
    bb = d.textbbox((0, 0), text, font=f)
    pad = max(3, int(min(W, H) * 0.008))
    cw, ch = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    # `inset` is for panels with rounded corners: a credit flush into a
    # radiused corner gets its last two letters clipped, and a clipped licence
    # notice is not a licence notice.
    x = W - cw - inset if "r" in corner else inset
    y = H - ch - inset if "b" in corner else inset
    d.rectangle([x, y, x + cw, y + ch], fill=(16, 24, 38) if dark else (252, 249, 242))
    d.text((x + pad - bb[0], y + pad - bb[1]), text, font=f,
           fill=(126, 142, 166) if dark else INK_SOFT)


def scale_bar(im, px_per_km, scale=1.0, bilingual=True, dark=False):
    """A bar of a round number of metres, bottom left."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    W, H = im.size
    metres, bar = 100, 0
    for metres in (5000, 2000, 1000, 500, 300, 200, 100, 50):
        bar = px_per_km * metres / 1000.0
        if bar < W * 0.30:
            break
    if bar < W * 0.05:
        return
    ink = (126, 142, 166) if dark else INK_SOFT
    f = font(max(9, min(W, H) * 0.026) * scale)
    x0 = int(W * 0.035)
    y0 = H - int(min(W, H) * 0.045)
    lw = max(2, int(min(W, H) * 0.004))
    d.line([(x0, y0), (x0 + bar, y0)], fill=ink, width=lw)
    for x in (x0, x0 + bar):
        d.line([(x, y0 - lw * 2.5), (x, y0 + lw * 2.5)], fill=ink, width=lw)
    label = ("%d ม. / m" % metres) if metres < 1000 else ("%g กม. / km" % (metres / 1000))
    d.text((x0, y0 - lw * 4), label if bilingual else str(metres), font=f,
           fill=ink, anchor="ls")


# ------------------------------------------------------- geometry, for the SVG
# The picture-making half of this module hands geometry to Pillow. These four
# hand it to an SVG instead — the drawn map baked into a page, which is what
# prints, what a reader with scripting off keeps, and what fills the box before
# a tile has arrived. Everything here exists to make that drawing small: a
# place page carries its own map, and there are twelve thousand of them.


def simplify(pts, eps):
    """Douglas–Peucker, iterative so a long river cannot blow the stack."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        den = math.hypot(dx, dy) or 1e-9
        far, fd = -1, eps
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + bx * ay - by * ax) / den
            if d > fd:
                far, fd = i, d
        if far > 0:
            keep[far] = True
            stack.append((a, far))
            stack.append((far, b))
    return [p for p, k in zip(pts, keep) if k]


def clip_poly(pts, box):
    """Sutherland–Hodgman against the frame.

    The whole file-size problem is features that reach far outside the picture:
    tiles are 1.2 km across and a place map is 500 m, so an unclipped farmland
    polygon is two kilometres of coordinates nobody will ever see. Clipping
    took the drawn map from 12 KB to 4.
    """
    lo_x, lo_y, hi_x, hi_y = box

    def inside(p, edge):
        return (p[0] >= lo_x if edge == 0 else p[0] <= hi_x if edge == 1 else
                p[1] >= lo_y if edge == 2 else p[1] <= hi_y)

    def cross(a, b, edge):
        ax, ay = a
        bx, by = b
        if edge in (0, 1):
            x = lo_x if edge == 0 else hi_x
            t = (x - ax) / ((bx - ax) or 1e-9)
            return (x, ay + t * (by - ay))
        y = lo_y if edge == 2 else hi_y
        t = (y - ay) / ((by - ay) or 1e-9)
        return (ax + t * (bx - ax), y)

    out = pts
    for edge in range(4):
        if not out:
            return []
        src, out = out, []
        prev = src[-1]
        for cur in src:
            ci, pi = inside(cur, edge), inside(prev, edge)
            if ci:
                if not pi:
                    out.append(cross(prev, cur, edge))
                out.append(cur)
            elif pi:
                out.append(cross(prev, cur, edge))
            prev = cur
    return out


def clip_line(pts, box):
    """The runs of a polyline that touch the frame.

    Each run keeps one point beyond the edge, so a road still runs off the
    picture rather than stopping short of it — a street that ends in mid-air
    two pixels inside the border reads as missing data.
    """
    lo_x, lo_y, hi_x, hi_y = box
    runs, cur = [], []
    for i, p in enumerate(pts):
        if lo_x <= p[0] <= hi_x and lo_y <= p[1] <= hi_y:
            if not cur and i:
                cur.append(pts[i - 1])
            cur.append(p)
        elif cur:
            cur.append(p)
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def path_d(pts, close=False):
    """Path data, relative and at integer precision.

    On a 640-unit viewBox covering half a kilometre, one unit is 80 cm: the
    rounding is invisible and the string is half the length of absolute
    decimals. Repeated points collapse, which is most of what simplification
    leaves behind.
    """
    if len(pts) < 2:
        return ""
    px, py = int(round(pts[0][0])), int(round(pts[0][1]))
    body = []
    for x, y in pts[1:]:
        xi, yi = int(round(x)), int(round(y))
        if xi == px and yi == py:
            continue
        body.append("%d %d" % (xi - px, yi - py))
        px, py = xi, yi
    if not body:
        return ""
    return "M%d %dl%s%s" % (int(round(pts[0][0])), int(round(pts[0][1])),
                            ",".join(body), "Z" if close else "")


def data_uri(im, fmt="PNG"):
    """For the cards, which are HTML rendered by a headless Chrome: a file://
    page loading a file:// image is a fight with Chrome's rules that nobody
    needs to have, and the picture is 100 KB."""
    import base64
    buf = io.BytesIO()
    im.save(buf, fmt, optimize=True)
    return "data:image/%s;base64,%s" % (fmt.lower(),
                                        base64.b64encode(buf.getvalue()).decode())


_SHARED = {}


def shared(night=False):
    """One archive per palette per process — the file is 116 MB and the
    directories are worth keeping warm across the dozens of cards a build
    draws."""
    if night not in _SHARED:
        _SHARED[night] = Ground(night=night)
    return _SHARED[night]


def bbox_of(points, pad=0.15, square=False):
    """(S, W, N, E) around (lat, lng) points, padded, optionally squared off in
    projected proportion so a square canvas is not a sheared map."""
    lats = [p[0] for p in points]
    lngs = [p[1] for p in points]
    s, n, w, e = min(lats), max(lats), min(lngs), max(lngs)
    dlat = max((n - s) * pad, 0.0008)
    dlng = max((e - w) * pad, 0.0008)
    s, n, w, e = s - dlat, n + dlat, w - dlng, e + dlng
    if square:
        kx = math.cos(math.radians((n + s) / 2))
        span_lng, span_lat = (e - w) * kx, n - s
        if span_lng > span_lat:
            g = (span_lng - span_lat) / 2
            n, s = n + g, s - g
        else:
            g = (span_lat - span_lng) / 2 / kx
            e, w = e + g, w - g
    return (s, w, n, e)


def _selfcheck():
    g = Ground()
    if not g.available:
        print("no archive at %s — every caller keeps its paper (%s)"
              % (g.path, g.error or "file missing"))
        return 1
    a = g.archive
    print("archive : %s (%.0f MB)" % (a.path.name, a.path.stat().st_size / 1e6))
    print("zooms   : %d..%d   bounds S,W,N,E = %s" %
          (a.min_zoom, a.max_zoom, ", ".join("%.3f" % v for v in a.bounds)))
    # Tha Phae Gate, a 1.2 km box.
    lat, lng = 18.7876, 98.9931
    bbox = (lat - 0.006, lng - 0.006, lat + 0.006, lng + 0.006)
    z = g.zoom_for(bbox, 560)
    data = g.fetch(bbox, z)
    print("z%-3d    : %s" % (z, "  ".join("%s=%d" % (k, len(v))
                                          for k, v in sorted(data.items()))))
    kinds = {}
    for props, gt, rings in data.get("roads", []):
        kinds[props.get("kind")] = kinds.get(props.get("kind"), 0) + 1
    print("roads   : %s" % kinds)

    from PIL import Image
    W = 560
    im = Image.new("RGB", (W, W), g.palette["paper"])
    s, w, n, e = bbox

    def xy(p):
        return ((p[1] - w) / (e - w) * W, (n - p[0]) / (n - s) * W)
    ok = g.paint(im, xy, bbox, width_px=W)
    out = ROOT / "assets" / "_ground-selfcheck.png"
    im.save(out)
    print("painted : %s -> %s" % (ok, out.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(_selfcheck())
