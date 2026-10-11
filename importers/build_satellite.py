#!/usr/bin/env python3
"""ดาวเทียม — the photograph of the ground, bound the way the basemap was bound.

WHY THIS EXISTS
---------------
The vector basemap knows every road in two provinces and draws none of the
land between them. A reader looking for a shelter off a soi, a field, a
reservoir, or the shape of a village nobody has traced yet is asking a
question the drawn map cannot answer. A satellite layer answers it.

It lands under the same rules as the other two archives: one .pmtiles file in
our own bucket, fetched in ranges by the reader's browser, served same-origin
by publish/worker.js, no API key, no third-party host, nobody's logs but ours.
`satellite_layer.py` is the display half. This importer is the only network
step; the build itself stays offline, exactly as CLAUDE.md requires.

WHAT IT FETCHES, AND UNDER WHAT LICENCE
---------------------------------------
Sentinel-2 L2A, the European Space Agency's Copernicus programme, from the
AWS Open Data bucket `sentinel-cogs` (us-west-2), which answers anonymous
HTTP — no account, no key, no signature. Scenes are found through the STAC
API at https://earth-search.aws.element84.com/v1 (Element 84's public index
of that bucket).

    Licence: CC-BY-SA 3.0 IGO.
    Attribution: "Contains modified Copernicus Sentinel data <years>,
                  processed by ESA — CC BY-SA 3.0 IGO"

SHARE-ALIKE IS THE WHOLE POINT AND IT IS NOT A PROBLEM HERE. The obligation
is on the imagery and on anything adapted from it: the mosaic in this archive
is an adaptation, so the archive itself carries the licence in its PMTiles
metadata, `satellite_layer.py` prints the credit wherever the imagery shows,
and the credit is drawn into the pixels of the "send this view" picture the
way the ODbL credit already is. That is the compliance, in full, and it is
the same shape the site already keeps for OpenStreetMap. It does not reach
the directory's own records: a photograph under the pins is not a database
adapted from the photograph.

Nothing else needs saying. The site does not announce its licences as virtues;
it prints them because they are conditions.

WHAT IT PICKS, AND WHY THE MONTHS MATTER
----------------------------------------
Northern Thailand has a burning season. Roughly February to April the basin
fills with smoke from crop residue and forest fire, and a Sentinel-2 scene
taken then is a grey haze over a city nobody can see — the cloud-cover figure
in the metadata does not catch it, because haze is not cloud. November to
January is the clear window, after the rains and before the burning. So the
search window defaults to 1 November – 31 January.

Two metadata numbers do the picking and BOTH are needed:

  eo:cloud_cover                what everybody filters on;
  s2:nodata_pixel_percentage    what nobody filters on, and the trap.

Measured 2026-09-08 over this fence: S2B_47QMA_20251202_0_L2A reports
0.000023% cloud and is 56.2% NOTHING — a swath edge, half the granule black.
Ranking on cloud alone picks it, and the mosaic gets a hole the size of a
province. So the rank is: reject anything below the square's own coverage
floor, then lowest cloud, then newest.

A single scene per MGRS square still leaves gaps — measured over this fence,
one-per-square covers 97.2% of it, the shortfall along the southern edge
where the granules stop. So each square keeps a STACK of candidates in rank
order and a pixel falls through to the next scene when the one above it has
no data there. Different scenes are different days, so a stack can show a
seam; the seam is at a granule edge and it is a photograph of two mornings,
which is what a mosaic is. `data/satellite_scenes.json` records every scene
in every stack, with its date and its cloud figure, and the page prints them.

WHAT IT WRITES
--------------
assets/tiles/cm-cr-satellite.pmtiles — PMTiles v3, raster, JPEG tiles.
Written by the stdlib writer below, which borrows build_terrain's directory
serializer and Hilbert index rather than keeping a second copy of either, and
is proven against map_ground's reader — the site's own PMTiles half — before
it is moved into place. docs/tiles is symlinked by build.py; the archive
stays out of git like the other two (same .gitignore rule, same reason).

    python3 importers/build_satellite.py --maxzoom 13
    python3 importers/build_satellite.py --maxzoom 14      # four times the file

data/satellite_scenes.json — the read date, the licence, the fence, and every
scene id with its cloud and nodata figures. What the page prints, and what
makes the mosaic re-buildable by somebody who is not this script.

WHAT IS ACTUALLY INSTALLED ON THIS MACHINE, AND WHAT IS NOT
------------------------------------------------------------
Checked 2026-09-08 with `which` and an import probe:

    present   pmtiles (Protomaps CLI, /opt/homebrew/bin), Pillow 11.1.0,
              python3 3.9.6, curl
    ABSENT    rio, rio-cogeo, rio-rgbify, rasterio, gdal (gdal_translate,
              gdalbuildvrt, gdalwarp), numpy, boto3, tippecanoe, aws

So the usual recipe — `gdalbuildvrt` a mosaic, `gdalwarp` to EPSG:3857,
`gdal2tiles` or `rio` to tiles, `pmtiles convert` — CANNOT RUN HERE, and this
importer does not need it. Everything below is stdlib plus Pillow:

  · a COG is a TIFF whose tiles are individually addressable, so the header
    and the tile offsets come back in one 64 KB ranged read and each tile is
    one more ranged read. The tiles are DEFLATE with a horizontal predictor:
    zlib.decompress, then undo the differencing. That is the whole reader.
  · the overview levels inside the same file ARE the lower zooms — level 1 is
    20 m/px, level 2 is 40 m/px — so a z13 tile costs a quarter of the bytes
    a z14 tile costs, read from a smaller picture rather than downsampled.
  · UTM to WGS84 is the Snyder transverse-Mercator series, thirty lines, and
    checked against a known point: ประตูท่าแพ (18.7876 N, 98.9931 E) comes
    out at 499272.9 E, 2077326.1 N in zone 47N, which is the published value
    to the metre.
  · a 256-px web-Mercator tile is small enough that the UTM-to-Mercator warp
    over it is affine to well under a pixel, so the resample is one
    Image.transform in Pillow's C rather than 65,536 Python trig calls.

IF YOU WOULD RATHER USE THE GDAL LANE, this is what it needs — none of it is
required by this script, and none of it is installed:

    brew install gdal                       # gdal_translate, gdalwarp, gdalbuildvrt
    pip3 install rasterio rio-cogeo         # rio, the COG profile
    pip3 install rio-tiler                  # tiling
    brew install go-pmtiles                 # the `pmtiles` CLI (ALREADY PRESENT)

and the shape of it would be: gdalbuildvrt over the TCI COGs → gdalwarp to
EPSG:3857 → gdal2tiles.py -z 7-14 → an mbtiles → `pmtiles convert`. It is
faster than this script and it pulls whole scenes: about 2 GB down for the
twenty granules, against the tens of megabytes the ranged reader touches.

WHAT IT CANNOT SHOW
-------------------
10 m per pixel. A z14 tile at this latitude is 9.03 m per pixel, so the
archive is at its own grain there and MapLibre overzooms past it — the same
trade the basemap makes past z15 and the terrain past z12. At 10 m a house is
a pixel. The old city's rooftops, a soi's shophouses, a temple's roofline and
anything you would recognise a doorway by are BELOW the grain and are not
there. What is there: the moat, the Ping, fields, roofs in bulk, forest
against cleared ground, reservoirs, the shape of a village. The toggle in
satellite_layer.py says so in both languages, because a satellite button that
does not say its resolution promises Google's picture and delivers ESA's.

Resumable: every COG tile lands in cache/satellite/ before it is used and is
never fetched twice; every rendered map tile lands in cache/satellite/tiles/
so an interrupted run resumes. The archive is bound only when every tile in
the plan is on disk.
"""
import argparse
import importlib.util
import io
import json
import math
import random
import statistics
import struct
import sys
import time
import zlib
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "satellite"
TILE_CACHE = CACHE / "tiles"
OUT = ROOT / "assets" / "tiles" / "cm-cr-satellite.pmtiles"
SCENES = ROOT / "data" / "satellite_scenes.json"

# The fence is cm-cr.pmtiles' own extract box, the same three-and-a-bit
# degrees build_terrain fences its z12 to. Kept as a literal here for the
# same reason it is a literal there: four numbers nobody should have to
# import a module to read.
FENCE = (97.3, 17.0, 100.6, 20.5)          # W, S, E, N

# The floor is map_shell.MIN_ZOOM rounded down. Below z7 the camera cannot
# go, so a tile there would be bytes nobody can ask for.
MIN_Z = 7
MAX_Z_DEFAULT = 13

STAC = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"
UA = "motdang-satellite/1 (+https://motdang.net)"

# November to January. See the docstring: February to April is the burning
# season and haze does not show up in eo:cloud_cover. Two seasons are searched
# so a square with a bad November has a December to fall back on.
SEASONS = 2
SEASON_START = (11, 1)
SEASON_END = (1, 31)

CLOUD_MAX = 12.0        # per candidate, before ranking
STACK = 3               # scenes kept per MGRS square, in rank order
COVERAGE_SLACK = 2.0    # a candidate more than this far above its square's
                        # own nodata floor is a different, smaller footprint

LICENCE = "CC BY-SA 3.0 IGO"
ATTRIBUTION = ("Contains modified Copernicus Sentinel data, "
               "processed by ESA — CC BY-SA 3.0 IGO")
SOURCE_URL = "https://registry.opendata.aws/sentinel-2-l2a-cogs/"

JPEG_QUALITY = 80       # measured against 70/85 on real tiles; see --measure

# map_ground is the reading half of PMTiles on this site and build_terrain is
# the writing half. Borrowing both keeps one copy of each (the audit files'
# one-copy rule) and makes the parity gate below an argument rather than a
# hope: this writer is correct because the site's own reader says so.
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


map_ground = _load("map_ground_sat", ROOT / "map_ground.py")
build_terrain = _load("build_terrain_sat", ROOT / "importers" / "build_terrain.py")
zxy_to_tileid = map_ground.zxy_to_tileid
_directory = build_terrain._directory
_tileid_to_zxy = build_terrain._tileid_to_zxy


# --------------------------------------------------------------- the network
_NET = {"bytes": 0, "requests": 0}


def _fetch(url, rng=None, timeout=90, tries=3):
    """One HTTP GET, optionally ranged. Every byte this script pulls comes
    through here so the run can say what it cost."""
    last = None
    for attempt in range(tries):
        try:
            h = {"User-Agent": UA}
            if rng:
                h["Range"] = "bytes=%d-%d" % rng
            resp = urlopen(Request(url, headers=h), timeout=timeout)
            blob = resp.read()
            _NET["bytes"] += len(blob)
            _NET["requests"] += 1
            return blob
        except Exception as err:                # noqa: BLE001 — retried, then raised
            last = err
            time.sleep(1 + 2 * attempt)
    raise IOError("%s (%s)" % (url, last))


# ------------------------------------------------- transverse Mercator, UTM
# Snyder / USGS Professional Paper 1395. Forward only: every pixel this
# script places starts as a lat/lng in web Mercator and needs the UTM
# easting/northing to index the source raster.
_A = 6378137.0
_F = 1 / 298.257223563
_E2 = _F * (2 - _F)
_EP2 = _E2 / (1 - _E2)
_K0 = 0.9996


def utm_forward(lat, lng, zone):
    """(easting, northing) in metres, WGS84, northern hemisphere."""
    lam0 = math.radians(zone * 6 - 183)
    p = math.radians(lat)
    l = math.radians(lng)
    sp = math.sin(p)
    N = _A / math.sqrt(1 - _E2 * sp * sp)
    T = math.tan(p) ** 2
    C = _EP2 * math.cos(p) ** 2
    Aa = math.cos(p) * (l - lam0)
    e2 = _E2
    M = _A * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * p
              - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * p)
              + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * p)
              - (35 * e2 ** 3 / 3072) * math.sin(6 * p))
    x = _K0 * N * (Aa + (1 - T + C) * Aa ** 3 / 6
                   + (5 - 18 * T + T * T + 72 * C - 58 * _EP2) * Aa ** 5 / 120) + 500000.0
    y = _K0 * (M + N * math.tan(p) * (Aa ** 2 / 2
               + (5 - T + 9 * C + 4 * C * C) * Aa ** 4 / 24
               + (61 - 58 * T + T * T + 600 * C - 330 * _EP2) * Aa ** 6 / 720))
    return x, y


# ------------------------------------------------------------ the COG reader
class Cog:
    """A tiled, DEFLATE-compressed Cloud-Optimized GeoTIFF, read over HTTP
    ranges. Handles what the Sentinel-2 COGs actually are and nothing else:
    little-endian, classic TIFF, chunky planar config, 8-bit RGB (TCI) or
    16-bit single band (B02/B03/B04), horizontal predictor.

    The overview IFDs chained after the full-resolution one are the lower
    zooms. level(0) is 10 m/px; each level after halves it.
    """

    _T_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8, 17: 8, 18: 8}
    _T_FMT = {1: "B", 2: "c", 3: "H", 4: "I", 5: "Q", 11: "f", 12: "d", 16: "Q"}

    def __init__(self, url, header=65536):
        self.url = url
        self.head = self._cached_head(header)
        if self.head[:2] != b"II" or struct.unpack_from("<H", self.head, 2)[0] != 42:
            raise ValueError("not a little-endian classic TIFF: %s" % url)
        self.ifds = []
        off = struct.unpack_from("<I", self.head, 4)[0]
        while off and off + 2 < len(self.head):
            d, off = self._ifd(off)
            self.ifds.append(d)
        if not self.ifds:
            raise ValueError("no IFD in the first %d bytes of %s" % (header, url))
        self._levels = {}
        self._tiles = {}

    def _cached_head(self, n):
        p = CACHE / "hdr" / (_slug(self.url) + ".hdr")
        if p.exists() and p.stat().st_size >= n:
            return p.read_bytes()
        blob = _fetch(self.url, (0, n - 1))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        return blob

    def _ifd(self, off):
        n = struct.unpack_from("<H", self.head, off)[0]
        d = {}
        for i in range(n):
            p = off + 2 + i * 12
            tag, typ, cnt = struct.unpack_from("<HHI", self.head, p)
            d[tag] = (typ, cnt, p + 8)
        return d, struct.unpack_from("<I", self.head, off + 2 + n * 12)[0]

    def _v(self, d, tag, default=None):
        if tag not in d:
            return default
        typ, cnt, p = d[tag]
        sz = self._T_SIZE.get(typ, 1)
        fmt = self._T_FMT.get(typ, "B")
        if cnt * sz <= 4:
            return list(struct.unpack_from("<" + fmt * cnt, self.head, p))
        off = struct.unpack_from("<I", self.head, p)[0]
        end = off + cnt * sz
        if end > len(self.head):
            # A 10,980-px level has 121 tile offsets; they fit. A wider file
            # one day might not, and a silent short read would place tiles at
            # garbage offsets, so this refuses rather than guesses.
            raise ValueError("tag %d runs past the cached header (%d > %d) — "
                             "raise Cog(header=)" % (tag, end, len(self.head)))
        return list(struct.unpack_from("<" + fmt * cnt, self.head, off))

    def level(self, i):
        if i not in self._levels:
            d = self.ifds[i]
            self._levels[i] = {
                "w": self._v(d, 256)[0], "h": self._v(d, 257)[0],
                "tw": self._v(d, 322)[0], "th": self._v(d, 323)[0],
                "bits": self._v(d, 258, [8])[0],
                "spp": self._v(d, 277, [1])[0],
                "comp": self._v(d, 259)[0],
                "pred": self._v(d, 317, [1])[0],
                "offs": self._v(d, 324), "byts": self._v(d, 325),
            }
        return self._levels[i]

    @property
    def n_levels(self):
        return len(self.ifds)

    def _tile_bytes(self, li, ti):
        L = self.level(li)
        off, ln = L["offs"][ti], L["byts"][ti]
        if ln == 0:
            return None
        p = CACHE / "cog" / _slug(self.url) / ("%d_%d.bin" % (li, ti))
        if p.exists() and p.stat().st_size == ln:
            blob = p.read_bytes()
        else:
            blob = _fetch(self.url, (off, off + ln - 1))
            if len(blob) != ln:
                raise IOError("short tile %d/%d: %d of %d bytes"
                              % (li, ti, len(blob), ln))
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_bytes(blob)
            tmp.replace(p)
        if L["comp"] != 8 and L["comp"] != 32946:
            raise ValueError("compression %d is not DEFLATE" % L["comp"])
        raw = zlib.decompress(blob)
        if L["pred"] == 2:
            raw = _unpredict(raw, L["tw"], L["th"], L["spp"], L["bits"])
        return raw

    def tile_image(self, li, ti):
        """One source tile as a Pillow image — 'RGB' for TCI, 'I;16' for a
        raw band. Cached in memory: a warp over one output tile touches the
        same source tile hundreds of times."""
        from PIL import Image
        key = (li, ti)
        if key in self._tiles:
            return self._tiles[key]
        raw = self._tile_bytes(li, ti)
        L = self.level(li)
        if raw is None:
            im = None
        elif L["spp"] == 3:
            im = Image.frombytes("RGB", (L["tw"], L["th"]), raw)
        elif L["bits"] == 16:
            im = Image.frombytes("I;16", (L["tw"], L["th"]), raw)
        else:
            im = Image.frombytes("L", (L["tw"], L["th"]), raw)
        if len(self._tiles) > 12:
            self._tiles.clear()
        self._tiles[key] = im
        return im

    def window(self, li, x0, y0, w, h):
        """A (w x h) image of level li starting at pixel (x0, y0), assembled
        from whatever source tiles it crosses. Out-of-raster is black, which
        is what nodata already is in these products."""
        from PIL import Image
        L = self.level(li)
        mode = "RGB" if L["spp"] == 3 else ("I;16" if L["bits"] == 16 else "L")
        out = Image.new(mode, (w, h))
        ntx = (L["w"] + L["tw"] - 1) // L["tw"]
        tx0, tx1 = x0 // L["tw"], (x0 + w - 1) // L["tw"]
        ty0, ty1 = y0 // L["th"], (y0 + h - 1) // L["th"]
        for ty in range(max(0, ty0), ty1 + 1):
            for tx in range(max(0, tx0), tx1 + 1):
                if tx >= ntx or ty * ntx + tx >= len(L["offs"]):
                    continue
                im = self.tile_image(li, ty * ntx + tx)
                if im is None:
                    continue
                out.paste(im, (tx * L["tw"] - x0, ty * L["th"] - y0))
        return out


def _slug(url):
    """A filesystem name for a URL. The scene id and the band are the part
    that matters and they are already unique; the hash keeps two scenes with
    the same band from colliding if a path ever repeats."""
    tail = url.rstrip("/").split("/")[-1]
    return "%s-%08x" % (tail.replace(".", "_"),
                        zlib.crc32(url.encode("utf-8")) & 0xFFFFFFFF)


def _unpredict(raw, tw, th, spp, bits):
    """Undo TIFF horizontal differencing (predictor 2), in place on a bytearray.

    Two widths, because these files use both: TCI is 8-bit x 3 samples, a raw
    band is 16-bit x 1. Getting the sample width wrong does not error — it
    produces a picture that is subtly, beautifully wrong, which is why the
    16-bit branch reads and writes whole words rather than bytes.
    """
    out = bytearray(raw)
    if bits == 8:
        row = tw * spp
        for r in range(th):
            b = r * row
            for c in range(spp, row):
                out[b + c] = (out[b + c] + out[b + c - spp]) & 0xFF
        return bytes(out)
    if bits == 16:
        row = tw * spp
        for r in range(th):
            b = r * row * 2
            vals = list(struct.unpack_from("<%dH" % row, out, b))
            for c in range(spp, row):
                vals[c] = (vals[c] + vals[c - spp]) & 0xFFFF
            struct.pack_into("<%dH" % row, out, b, *vals)
        return bytes(out)
    raise ValueError("predictor 2 with %d bits per sample is not handled" % bits)


# ------------------------------------------------------------- scene finding
def _windows(today=None):
    """The dry-season windows to search, newest first."""
    d = today or date.today()
    out = []
    # The season that ENDS in year Y runs Nov (Y-1) to Jan Y. Before the end
    # of January the current season is still open, so the newest COMPLETE
    # window is the one that ended this year either way.
    end_year = d.year
    for i in range(SEASONS):
        y = end_year - i
        a = "%04d-%02d-%02dT00:00:00Z" % (y - 1, SEASON_START[0], SEASON_START[1])
        b = "%04d-%02d-%02dT23:59:59Z" % (y, SEASON_END[0], SEASON_END[1])
        out.append(a + "/" + b)
    return out


def search(windows=None, cloud_max=CLOUD_MAX, limit_pages=6):
    """Every Sentinel-2 L2A scene over the fence in the dry-season windows.

    The STAC API is queried by bbox and by eo:cloud_cover; the nodata figure
    is not queryable, so it is read off each result and used in the ranking.
    """
    feats, seen = [], set()
    for win in (windows or _windows()):
        body = {"collections": [COLLECTION], "bbox": list(FENCE),
                "datetime": win,
                "query": {"eo:cloud_cover": {"lt": cloud_max}},
                "limit": 100}
        url, payload, page = STAC, body, 0
        while page < limit_pages:
            blob = _post(url, payload)
            d = json.loads(blob)
            for f in d.get("features", []):
                if f["id"] not in seen:
                    seen.add(f["id"])
                    feats.append(f)
            nxt = [l for l in d.get("links", []) if l.get("rel") == "next"]
            if not nxt:
                break
            url = nxt[0]["href"]
            payload = nxt[0].get("body") or body
            page += 1
    return feats


def _post(url, body):
    data = json.dumps(body).encode("utf-8")
    last = None
    for attempt in range(3):
        try:
            req = Request(url, data=data,
                          headers={"Content-Type": "application/json",
                                   "User-Agent": UA})
            blob = urlopen(req, timeout=90).read()
            _NET["bytes"] += len(blob)
            _NET["requests"] += 1
            return blob
        except Exception as err:                # noqa: BLE001
            last = err
            time.sleep(1 + 2 * attempt)
    raise IOError("STAC %s (%s)" % (url, last))


def _overlaps_fence(bbox):
    return not (bbox[2] < FENCE[0] or bbox[0] > FENCE[2]
                or bbox[3] < FENCE[1] or bbox[1] > FENCE[3])


def rank(feats, stack=STACK):
    """Per MGRS square, the scenes to read in order.

    The ranking, and the reason for each step:

      1. drop anything whose footprint misses the fence entirely;
      2. find the square's own nodata FLOOR — the best coverage any date
         achieves there. A square clipped by the granule grid has a floor
         well above zero and no date will ever beat it, so the floor is the
         yardstick, not zero;
      3. keep only candidates within COVERAGE_SLACK of that floor. A
         candidate far above it is a different, smaller footprint — the
         swath-edge sliver that reports 0% cloud because there is nothing
         there to be cloudy;
      4. among those, lowest cloud, then newest.
    """
    by = {}
    for f in feats:
        if not _overlaps_fence(f.get("bbox") or [0, 0, 0, 0]):
            continue
        by.setdefault(f["properties"]["grid:code"], []).append(f)
    out = []
    for code in sorted(by):
        fs = by[code]
        floor = min(_nodata(f) for f in fs)
        same = [f for f in fs if _nodata(f) <= floor + COVERAGE_SLACK]
        same.sort(key=lambda f: (f["properties"]["eo:cloud_cover"],
                                 -_datenum(f)))
        out.append({"square": code, "floor": round(floor, 3),
                    "candidates": len(fs),
                    "scenes": [_scene(f) for f in same[:stack]]})
    return out


def _nodata(f):
    return float(f["properties"].get("s2:nodata_pixel_percentage", 100.0))


def _datenum(f):
    return int(f["properties"]["datetime"][:10].replace("-", ""))


def _scene(f):
    a = f["assets"]
    v = a["visual"]
    return {
        "id": f["id"],
        "date": f["properties"]["datetime"][:10],
        "cloud": round(float(f["properties"]["eo:cloud_cover"]), 4),
        "nodata": round(_nodata(f), 3),
        "zone": int(f["properties"]["mgrs:utm_zone"]),
        "tci": v["href"],
        "red": a["red"]["href"], "green": a["green"]["href"],
        "blue": a["blue"]["href"],
        "transform": v["proj:transform"], "shape": v["proj:shape"],
        "bbox": f["bbox"],
    }


def coverage(plan, step=0.02):
    """What share of the fence the picked footprints actually cover, on a
    grid. A number, not a hope: one-per-square measured 97.2% here, and the
    stack is what closes it."""
    boxes = [s["bbox"] for sq in plan for s in sq["scenes"]]
    hit = miss = 0
    y = FENCE[1] + step / 2
    while y < FENCE[3]:
        x = FENCE[0] + step / 2
        while x < FENCE[2]:
            if any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes):
                hit += 1
            else:
                miss += 1
            x += step
        y += step
    return hit / (hit + miss) if (hit + miss) else 0.0


# ---------------------------------------------------------------- the mosaic
def _tile_range(z, box):
    """Inclusive tile x/y ranges covering box at z. No margin: the fence IS
    the coverage, and a tile outside it is a tile the camera cannot reach."""
    w, s, e, n = box

    def tx(lon):
        return int((lon + 180.0) / 360.0 * (1 << z))

    def ty(lat):
        r = math.radians(lat)
        return int((1.0 - math.asinh(math.tan(r)) / math.pi) / 2.0 * (1 << z))
    lim = (1 << z) - 1
    return (max(0, tx(w)), min(lim, tx(e)), max(0, ty(n)), min(lim, ty(s)))


def plan_tiles(max_z, min_z=MIN_Z):
    tiles = []
    for z in range(min_z, max_z + 1):
        x0, x1, y0, y1 = _tile_range(z, FENCE)
        tiles += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    return tiles


def _tile_lonlat(z, x, y):
    n = 1 << z
    w = x / n * 360.0 - 180.0
    e = (x + 1) / n * 360.0 - 180.0
    ytop = math.pi * (1 - 2 * y / n)
    ybot = math.pi * (1 - 2 * (y + 1) / n)
    return w, e, ytop, ybot


def _level_for(z, n_levels):
    """Which COG overview answers zoom z.

    Level 0 is 10 m/px; level k is 10 * 2^k. Zoom z at this latitude is
    156543.034 * cos(19°) / 2^z metres per pixel — 9.03 m at z14, 18.07 at
    z13, 36.14 at z12. Take the finest level that is not finer than the
    zoom needs, so a low zoom reads a small picture instead of throwing away
    fifteen sixteenths of a big one.
    """
    mpp = 156543.03392 * math.cos(math.radians(19.0)) / (1 << z)
    k = int(math.floor(math.log(max(mpp, 10.0) / 10.0, 2)))
    return max(0, min(k, n_levels - 1))


class Mosaic:
    """The stack of scenes, opened lazily, asked in rank order."""

    def __init__(self, plan, band="tci"):
        self.plan = plan
        self.band = band
        self._cogs = {}

    def open(self, scene):
        key = (scene["id"], self.band)
        if key not in self._cogs:
            url = scene["tci"] if self.band == "tci" else scene[self.band]
            self._cogs[key] = Cog(url)
        return self._cogs[key]

    def candidates(self, w, e, s, n):
        """Every scene whose footprint touches this box, in rank order,
        squares nearest the box first."""
        out = []
        for sq in self.plan:
            for sc in sq["scenes"]:
                b = sc["bbox"]
                if b[2] < w or b[0] > e or b[3] < s or b[1] > n:
                    continue
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                d = (cx - (w + e) / 2) ** 2 + (cy - (s + n) / 2) ** 2
                out.append((d, sc))
        out.sort(key=lambda t: t[0])
        return [sc for _, sc in out]

    def render(self, z, x, y, size=256):
        """One web-Mercator tile, or None when no scene has pixels there.

        THE WARP IS AFFINE ON PURPOSE. Over one 256-px tile — 2.3 km at z14,
        18 km at z11 — the difference between web Mercator and UTM is a
        smooth rotation and scale, and fitting it from the four corners is
        accurate to well under a pixel. That lets Pillow's C do the
        resampling. The alternative, inverse-projecting all 65,536 pixels in
        Python, was measured at about six seconds a tile: a day and a half
        for the z13 archive, six days for z14.
        """
        from PIL import Image
        w, e, ytop, ybot = _tile_lonlat(z, x, y)

        best = None
        for sc in self.candidates(w, e,
                                  math.degrees(math.atan(math.sinh(ybot))),
                                  math.degrees(math.atan(math.sinh(ytop)))):
            cog = self.open(sc)
            li = _level_for(z, cog.n_levels)
            L = cog.level(li)
            tr = sc["transform"]
            ox, oy, res = tr[2], tr[5], tr[0] * (1 << li)
            zone = sc["zone"]

            # Four corners, output pixel -> source pixel.
            pts = []
            for (px, py) in ((0, 0), (size, 0), (0, size)):
                lo = w + (e - w) * px / size
                yy = ytop + (ybot - ytop) * py / size
                la = math.degrees(math.atan(math.sinh(yy)))
                ux, uy = utm_forward(la, lo, zone)
                pts.append(((ux - ox) / res, (oy - uy) / res))
            (ax, ay), (bx, by), (cx, cy) = pts
            # Image.transform AFFINE maps output (i, j) -> source
            #   (a*i + b*j + c, d*i + e*j + f)
            a = (bx - ax) / size
            b = (cx - ax) / size
            c = ax
            d = (by - ay) / size
            ee = (cy - ay) / size
            f = ay

            xs = [ax, bx, cx, ax + (bx - ax) + (cx - ax)]
            ys = [ay, by, cy, ay + (by - ay) + (cy - ay)]
            x0, y0 = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
            x1, y1 = int(math.ceil(max(xs))) + 2, int(math.ceil(max(ys))) + 2
            if x1 < 0 or y1 < 0 or x0 > L["w"] or y0 > L["h"]:
                continue
            src = cog.window(li, x0, y0, x1 - x0, y1 - y0)
            im = src.transform((size, size), Image.AFFINE,
                               (a, b, c - x0, d, ee, f - y0),
                               resample=Image.BILINEAR)
            if im.mode != "RGB":
                im = im.convert("RGB")
            filled = _filled(im)
            if filled >= 0.999:
                return im
            if best is None:
                best = im
            else:
                best = _fill_holes(best, im)
                if _filled(best) >= 0.999:
                    return best
        return best


def _filled(im):
    """Share of pixels that are not nodata. Nodata in these products is
    exactly black, and real ground at 10 m almost never is: a shadowed
    reservoir at midday reads 8–20, not 0."""
    n = im.width * im.height
    black = im.histogram()
    # An RGB histogram is three 256-bins; a pixel is nodata only when all
    # three are 0, which the extrema cannot tell us, so count the darkest
    # bin of the darkest band as the ceiling on how many that could be.
    return 1.0 - min(black[0], black[256], black[512]) / float(n)


def _fill_holes(base, other):
    """Paste `other` wherever `base` has nothing. The mask is base's own
    darkness: a pixel that is 0 in all three bands."""
    from PIL import Image, ImageChops
    r, g, b = base.split()
    lum = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mask = lum.point(lambda v: 255 if v == 0 else 0)
    out = base.copy()
    out.paste(other, (0, 0), mask)
    return out


# ----------------------------------------------------- rendering the archive
def _tile_path(z, x, y):
    return TILE_CACHE / str(z) / str(x) / ("%d.jpg" % y)


def _save(p, im, quality):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=False)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(p)


def render_max(mos, max_z, quality=JPEG_QUALITY, report=200):
    """The BOTTOM of the pyramid, warped from the source. Only this zoom is.

    WHY ONLY THIS ONE. The warp fits an affine from a tile's three corners,
    which is exact to well under a pixel over the 2.3 km a z14 tile covers
    and over the 4.6 km a z13 one covers. It is NOT exact over the 313 km a
    z7 tile covers: UTM and web Mercator diverge over that distance by
    kilometres, and a z7 tile fitted that way would be a picture of the right
    country in slightly the wrong shape. Worse, no single Sentinel granule
    fills a z7 tile, so the tile would be a quilt of sixty separately-wrong
    affines meeting at visible steps.

    So the low zooms are FOLDED from this one, below — which is what every
    tiler does, is exact by construction, is free, and gives the pyramid the
    smooth downsampling a reader zooming out expects.
    """
    x0, x1, y0, y1 = _tile_range(max_z, FENCE)
    tiles = [(max_z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    done = {"cached": 0, "made": 0, "empty": 0}
    t0 = time.time()
    for i, (z, x, y) in enumerate(tiles, 1):
        p = _tile_path(z, x, y)
        if p.exists():
            done["cached"] += 1
        else:
            im = mos.render(z, x, y)
            if im is None:
                done["empty"] += 1
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"")          # a recorded absence, not a retry
                continue
            _save(p, im, quality)
            done["made"] += 1
        if i % report == 0 or i == len(tiles):
            el = time.time() - t0
            print("  %6d/%d  cached %d made %d empty %d  %.0f MB pulled  %.1f min"
                  % (i, len(tiles), done["cached"], done["made"], done["empty"],
                     _NET["bytes"] / 1e6, el / 60), flush=True)
    return done


def fold(max_z, min_z=MIN_Z, quality=JPEG_QUALITY):
    """Every zoom above the bottom, each built from its four children.

    A tile with no children at all is left absent rather than written black:
    absence is how this archive says "no photograph here", and the layer
    reads it that way.
    """
    from PIL import Image
    made = {}
    for z in range(max_z - 1, min_z - 1, -1):
        x0, x1, y0, y1 = _tile_range(z, FENCE)
        n = 0
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                p = _tile_path(z, x, y)
                if p.exists():
                    continue
                quad = Image.new("RGB", (512, 512))
                any_child = False
                for dx in (0, 1):
                    for dy in (0, 1):
                        cp = _tile_path(z + 1, x * 2 + dx, y * 2 + dy)
                        if not cp.exists() or cp.stat().st_size == 0:
                            continue
                        quad.paste(Image.open(cp).convert("RGB"),
                                   (dx * 256, dy * 256))
                        any_child = True
                p.parent.mkdir(parents=True, exist_ok=True)
                if not any_child:
                    p.write_bytes(b"")
                    continue
                _save(p, quad.resize((256, 256), Image.LANCZOS), quality)
                n += 1
        made[z] = n
        print("  folded z%d: %d tiles" % (z, n), flush=True)
    return made


# ------------------------------------------------ PMTiles v3, writing half
def bind(tiles, out_path, max_z, meta_extra=None):
    """Bind the cached JPEG tiles into one archive.

    The directory serializer and the Hilbert index are build_terrain's — one
    copy of each on this machine, and the format is therefore correct in the
    same way its archive is. What differs is the header: tile type 3 (JPEG)
    rather than 2, and no tile compression, because JPEG carries its own.
    """
    recs = []
    for z, x, y in tiles:
        p = _tile_path(z, x, y)
        if not p.exists():
            raise SystemExit("refusing to bind: %d/%d/%d was never rendered"
                             % (z, x, y))
        if p.stat().st_size == 0:
            continue                    # a recorded empty tile is simply absent
        recs.append((zxy_to_tileid(z, x, y), p))
    if not recs:
        raise SystemExit("refusing to bind: nothing rendered")
    recs.sort()

    entries, blobs, off = [], [], 0
    for tid, p in recs:
        blob = p.read_bytes()
        entries.append((tid, 1, len(blob), off))
        blobs.append(blob)
        off += len(blob)

    LEAF = 512
    leaf_blobs, root_entries, leaf_off = [], [], 0
    for i in range(0, len(entries), LEAF):
        chunk = entries[i:i + LEAF]
        blob = _directory(chunk)
        root_entries.append((chunk[0][0], 0, len(blob), leaf_off))
        leaf_blobs.append(blob)
        leaf_off += len(blob)
    root = _directory(root_entries)

    md = {
        "name": "cm-cr-satellite",
        "description": "Sentinel-2 L2A true colour over the Chiang Mai + "
                       "Chiang Rai frame. Bound by importers/build_satellite.py.",
        "attribution": ATTRIBUTION,
        "license": LICENCE,
        "source": SOURCE_URL,
        "read": date.today().isoformat(),
    }
    md.update(meta_extra or {})
    meta = _gzip(json.dumps(md, ensure_ascii=False,
                            separators=(",", ":")).encode("utf-8"))

    HDR = 127
    root_off = HDR
    meta_off = root_off + len(root)
    leaf_sec = meta_off + len(meta)
    data_off = leaf_sec + leaf_off

    w, s, e, n = FENCE
    head = bytearray(HDR)
    head[0:7] = b"PMTiles"
    head[7] = 3
    struct.pack_into("<8Q", head, 8,
                     root_off, len(root), meta_off, len(meta),
                     leaf_sec, leaf_off, data_off, off)
    struct.pack_into("<3Q", head, 72, len(recs), len(entries), len(entries))
    head[96] = 1        # clustered: data is in tileid order
    head[97] = 2        # internal compression: gzip
    head[98] = 1        # tile compression: none — JPEG carries its own
    head[99] = 3        # tile type: jpeg
    head[100] = MIN_Z
    head[101] = max_z
    struct.pack_into("<4i", head, 102, int(w * 1e7), int(s * 1e7),
                     int(e * 1e7), int(n * 1e7))
    head[118] = 13
    struct.pack_into("<2i", head, 119,
                     int((w + e) / 2 * 1e7), int((s + n) / 2 * 1e7))

    tmp = out_path.with_name("." + out_path.name + ".tmp")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "wb") as fh:
        fh.write(bytes(head))
        fh.write(root)
        fh.write(meta)
        for blob in leaf_blobs:
            fh.write(blob)
        for blob in blobs:
            fh.write(blob)

    # The parity gate: the site's own reader, on the file just written.
    arc = map_ground._Archive(tmp)
    sample = recs[:: max(1, len(recs) // 40)] + [recs[0], recs[-1]]
    for tid, p in sample:
        z, x, y = _tileid_to_zxy(tid)
        if arc.tile(z, x, y) != p.read_bytes():
            arc.close()
            tmp.unlink()
            raise SystemExit("parity failed at %d/%d/%d — archive not shipped"
                             % (z, x, y))
    arc.close()
    tmp.replace(out_path)
    return {"tiles": len(recs), "bytes": out_path.stat().st_size,
            "leaves": len(leaf_blobs)}


def _gzip(payload):
    import gzip as _g
    return _g.compress(payload, mtime=0)


# -------------------------------------------------------------- measurement
def measure(mos, max_z, n=16, quality=JPEG_QUALITY, seed=9):
    """What the archive would weigh, measured on real tiles and multiplied out.

    Two samples, both real, and the second is the one that matters most:

      · n random tiles at max_z, warped from the source. Random over the
        WHOLE fence, not over four pretty places — the fence is mostly forest
        and paddy, and a city-weighted mean overstates the archive by half.
      · n // 2 random tiles at max_z - 1, built by actually folding their
        four children, which is how the real build makes them.

    Everything at z ≤ max_z - 2 is folded the same way from the level below,
    so it is estimated at the folded mean. That assumption is worth naming
    and worth almost nothing: z7–z11 is 610 tiles of the 8,704 in a maxzoom-13
    archive and of the 34,223 in a maxzoom-14 one — under 2% either way.
    """
    from PIL import Image
    at_max, folded = [], []

    def rand_tiles(z, want):
        """A generator PER ZOOM, seeded by the zoom.

        One shared generator was a real and quiet mistake: randint over
        x 6310–6385 at z13 and over x 12620–12770 at z14 consumes the same
        underlying draws, so the z14 sample came out as almost exactly the
        CHILDREN of the z13 sample — every source tile already cached, zero
        network, and two "independent" measurements that were one. Reseeding
        per zoom is the whole cure.
        """
        rnd = random.Random(seed * 1000 + z)
        x0, x1, y0, y1 = _tile_range(z, FENCE)
        seen = set()
        while len(seen) < min(want, (x1 - x0 + 1) * (y1 - y0 + 1)):
            seen.add((rnd.randint(x0, x1), rnd.randint(y0, y1)))
        return sorted(seen)

    def jpeg_bytes(im):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True)
        return len(buf.getvalue())

    for x, y in rand_tiles(max_z, n):
        im = mos.render(max_z, x, y)
        if im is not None:
            at_max.append(jpeg_bytes(im))
    for x, y in rand_tiles(max_z - 1, max(2, n // 2)):
        quad, any_child = Image.new("RGB", (512, 512)), False
        for dx in (0, 1):
            for dy in (0, 1):
                child = mos.render(max_z, x * 2 + dx, y * 2 + dy)
                if child is not None:
                    quad.paste(child, (dx * 256, dy * 256))
                    any_child = True
        if any_child:
            folded.append(jpeg_bytes(quad.resize((256, 256), Image.LANCZOS)))
    return at_max, folded


def totals(at_max, folded, max_z):
    """Per-zoom counts x measured means, added up. The arithmetic is returned
    row by row so anybody can check it rather than trust the total."""
    m_max = statistics.mean(at_max) if at_max else 0.0
    m_fold = statistics.mean(folded) if folded else m_max
    lines, total = [], 0.0
    for z in range(MIN_Z, max_z + 1):
        x0, x1, y0, y1 = _tile_range(z, FENCE)
        count = (x1 - x0 + 1) * (y1 - y0 + 1)
        if z == max_z:
            m, how = m_max, "measured, warped from source"
        elif z == max_z - 1:
            m, how = m_fold, "measured, folded from four children"
        else:
            m, how = m_fold, "folded — estimated at the folded mean"
        total += count * m
        lines.append((z, count, m, count * m, how))
    return total, lines


# ----------------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--maxzoom", type=int, default=MAX_Z_DEFAULT,
                    help="13 (default, ~18 m/px) or 14 (native 10 m/px)")
    ap.add_argument("--dry", action="store_true",
                    help="print the plan's tile count and leave the network alone")
    ap.add_argument("--scenes", action="store_true",
                    help="search and rank only; write data/satellite_scenes.json")
    ap.add_argument("--measure", type=int, metavar="N", default=0,
                    help="render N random tiles per zoom and report the size "
                         "the whole archive would be")
    ap.add_argument("--quality", type=int, default=JPEG_QUALITY)
    ap.add_argument("--band", default="tci", choices=("tci", "red", "green", "blue"),
                    help="tci is ESA's own B04/B03/B02 composite, 8-bit, and "
                         "is what the archive ships; the single bands are here "
                         "for looking at one at a time")
    ap.add_argument("--no-fetch", action="store_true",
                    help="bind from the tile cache only")
    args = ap.parse_args()

    tiles = plan_tiles(args.maxzoom)
    by_z = {}
    for z, _x, _y in tiles:
        by_z[z] = by_z.get(z, 0) + 1
    print("plan: %d tiles z%d–z%d  (%s)"
          % (len(tiles), MIN_Z, args.maxzoom,
             ", ".join("z%d:%d" % (z, by_z[z]) for z in sorted(by_z))))
    if args.dry:
        return

    for d in (CACHE, TILE_CACHE, CACHE / "cog", CACHE / "hdr"):
        d.mkdir(parents=True, exist_ok=True)

    if SCENES.exists() and args.no_fetch:
        doc = json.loads(SCENES.read_text())
        plan = doc["squares"]
    else:
        print("searching STAC …", flush=True)
        feats = search()
        plan = rank(feats)
        cov = coverage(plan)
        doc = {
            "read": date.today().isoformat(),
            "source": {"name": "Sentinel-2 L2A (ESA / Copernicus) on AWS Open Data",
                       "url": SOURCE_URL, "stac": STAC},
            "licence": LICENCE,
            "attribution": ATTRIBUTION,
            "fence": list(FENCE),
            "window": _windows(),
            "resolution_m": 10,
            "native_zoom": 14,
            "coverage_of_fence": round(cov, 4),
            "squares": plan,
        }
        SCENES.write_text(json.dumps(doc, ensure_ascii=False, indent=1))
        print("scenes: %d squares, %d scenes, %.1f%% of the fence covered"
              % (len(plan), sum(len(s["scenes"]) for s in plan), cov * 100))
        for sq in plan:
            s = sq["scenes"][0]
            print("  %-12s %-26s %s  cloud %6.3f%%  nodata %6.2f%%  (+%d in stack)"
                  % (sq["square"], s["id"], s["date"], s["cloud"], s["nodata"],
                     len(sq["scenes"]) - 1))
    if args.scenes:
        print("network: %d bytes in %d requests" % (_NET["bytes"], _NET["requests"]))
        return

    mos = Mosaic(plan, band=args.band)

    if args.measure:
        print("measuring: %d random z%d tiles from source, %d folded z%d tiles …"
              % (args.measure, args.maxzoom, max(2, args.measure // 2),
                 args.maxzoom - 1), flush=True)
        at_max, folded = measure(mos, args.maxzoom, n=args.measure,
                                 quality=args.quality)
        print("  z%d  n=%d  mean %.0f B  median %.0f B  min %d  max %d"
              % (args.maxzoom, len(at_max), statistics.mean(at_max),
                 statistics.median(at_max), min(at_max), max(at_max)))
        if folded:
            print("  z%d  n=%d  mean %.0f B  median %.0f B"
                  % (args.maxzoom - 1, len(folded), statistics.mean(folded),
                     statistics.median(folded)))
        total, lines = totals(at_max, folded, args.maxzoom)
        print("\n  z    tiles     mean B    subtotal   how")
        for z, count, m, sub, how in lines:
            print("  %-4d %-9d %-9.0f %7.1f MB  %s"
                  % (z, count, m, sub / 1e6, how))
        print("  ---- maxzoom %d: %d tiles, %.1f MB (JPEG q%d)"
              % (args.maxzoom, sum(l[1] for l in lines), total / 1e6,
                 args.quality))
        print("network: %.1f MB in %d requests"
              % (_NET["bytes"] / 1e6, _NET["requests"]))
        return

    if not args.no_fetch:
        print("rendering the z%d floor from source …" % args.maxzoom, flush=True)
        print("render:", render_max(mos, args.maxzoom, quality=args.quality))
        print("folding z%d–z%d from it …" % (MIN_Z, args.maxzoom - 1), flush=True)
        fold(args.maxzoom, quality=args.quality)
    print("bind:", bind(tiles, OUT, args.maxzoom,
                        {"maxzoom": args.maxzoom,
                         "scenes": [s["id"] for sq in plan for s in sq["scenes"]]}))
    print("network: %.1f MB in %d requests"
          % (_NET["bytes"] / 1e6, _NET["requests"]))
    print("\nNow add the satellite block to data/basemap.json (the block is in "
          "notes/maps-grow-2026-09-08.txt §10) and run publish/deploy.py --tiles.")


if __name__ == "__main__":
    main()
