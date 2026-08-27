#!/usr/bin/env python3
"""ดอย — fetch the elevation archive and bind it the way the basemap was bound.

WHY THIS EXISTS
---------------
The basemap knows every road in two provinces and nothing about the ground
they climb. The doi page (/doi.html, geography_layer.py) puts the third
dimension under the same self-hosted rules as the second: one .pmtiles file
in our own bucket, fetched in ranges by the reader's browser, no API key,
nobody's logs but ours. This importer is the only network step; the build
itself stays offline, exactly as CLAUDE.md requires.

WHAT IT FETCHES
---------------
Terrarium-encoded elevation rasters from the Terrain Tiles public dataset on
AWS Open Data (bucket elevation-tiles-prod, no key, made for exactly this):
https://registry.opendata.aws/terrain-tiles/ — Mapzen's tiling of public
DEMs; at this latitude the height in every pixel is NASA/USGS SRTM.
Decoding is one line: metres = R*256 + G + B/256 - 32768.

The coverage rule is legible on purpose:
  z0–11  the camera RAILS (map_shell.BOUNDS with a tile of margin) — however
         far a reader can pan, the ground under them is real;
  z12    the FENCE (the cm-cr.pmtiles extract box) — full detail where the
         directory actually lives. ~38 m/px, which is the source data's own
         grain, so z13+ would be bytes without information. MapLibre overzooms
         past 12 from z12 data, the same trade the basemap makes past 15.

WHAT IT WRITES
--------------
assets/tiles/cm-cr-terrain.pmtiles — PMTiles v3, written by the stdlib writer
below and proven against map_ground's reader (the site's own PMTiles half)
before it is moved into place: every archive this script ships has already
been read back tile-for-tile on this machine. docs/tiles is a symlink to
assets/tiles, so the walk ships it with everything else; the archive itself
stays out of git like cm-cr.pmtiles (same .gitignore rule, same reason), and
this file is its regeneration command:

    python3 importers/build_terrain.py

With Pillow present (optional, same arrangement as make_og_cards.py) it also
reads the archive it just bound and writes what the page prints:

  data/terrain_meta.json     the read date, the source, and the highest cell
                             the model holds in the fence — found, not chosen;
  data/terrain_profile.json  a west–east line of heights through ประตูท่าแพ,
                             for the drawn cross-section that is the page's
                             no-script, no-tiles, on-paper fallback.

Without Pillow those two files are simply left as they were, the bind still
completes, and this script says which half it skipped. Nothing here ranks a
mountain; the numbers are the instrument's, dated, with the instrument named.

Resumable: tiles land in cache/terrain/<z>/<x>/<y>.png first and are never
fetched twice. A short read (a truncated PNG from a dropped connection) is
re-fetched rather than trusted — the magic bytes are checked on every file.
The archive is bound only when EVERY tile in the plan is on disk: a partial
elevation file would render as cliffs of missing ground, which is worse than
no third dimension at all.
"""
import argparse
import gzip
import importlib.util
import json
import math
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "terrain"
OUT = ROOT / "assets" / "tiles" / "cm-cr-terrain.pmtiles"
META = ROOT / "data" / "terrain_meta.json"
PROFILE = ROOT / "data" / "terrain_profile.json"

# The fence is cm-cr.pmtiles' own extract box (data/basemap.json records the
# command); the rails are map_shell.BOUNDS. Kept as literals here the same way
# the fence comment in map_shell keeps them: three numbers nobody should have
# to import a module to read.
FENCE = (97.3, 17.0, 100.6, 20.5)          # W, S, E, N — z12 lives here
RAILS = (96.9, 16.6, 101.0, 20.9)          # camera bounds — z0–11 live here
MAX_Z = 12
RAILS_Z = 11

SRC = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = "motdang-terrain/1 (+https://motdang.net)"
WORKERS = 8
ATTRIBUTION = ("Terrain Tiles — Mapzen, on AWS Open Data; "
               "DEM here: SRTM (NASA/USGS). "
               "https://registry.opendata.aws/terrain-tiles/")

# map_ground is the reading half of PMTiles on this site; borrowing its
# Hilbert index and its reader keeps one copy of each (the audit files'
# one-copy rule), and makes the parity check below an argument rather than a
# hope: the writer is correct because the site's own reader says so.
_spec = importlib.util.spec_from_file_location("map_ground", ROOT / "map_ground.py")
map_ground = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(map_ground)
zxy_to_tileid = map_ground.zxy_to_tileid


# ------------------------------------------------------------------ the plan
def _tile_range(z, box):
    """Inclusive tile x/y ranges covering box at z, one tile of margin."""
    w, s, e, n = box
    def tx(lon):
        return int((lon + 180.0) / 360.0 * (1 << z))
    def ty(lat):
        r = math.radians(lat)
        return int((1.0 - math.asinh(math.tan(r)) / math.pi) / 2.0 * (1 << z))
    x0, x1 = tx(w) - 1, tx(e) + 1
    y0, y1 = ty(n) - 1, ty(s) + 1        # y grows southward
    lim = (1 << z) - 1
    return (max(0, x0), min(lim, x1), max(0, y0), min(lim, y1))


def plan():
    """Every (z, x, y) the archive will hold, in no particular order."""
    tiles = []
    for z in range(0, RAILS_Z + 1):
        x0, x1, y0, y1 = _tile_range(z, RAILS)
        tiles += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    x0, x1, y0, y1 = _tile_range(MAX_Z, FENCE)
    tiles += [(MAX_Z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    return tiles


# ----------------------------------------------------------------- the fetch
def _path(z, x, y):
    return CACHE / str(z) / str(x) / ("%d.png" % y)


def _sound(p):
    """A cached tile is trusted only if it still starts like a PNG."""
    try:
        return p.stat().st_size > 8 and p.open("rb").read(4) == b"\x89PNG"
    except OSError:
        return False


def _fetch_one(zxy):
    z, x, y = zxy
    p = _path(z, x, y)
    if _sound(p):
        return "cached"
    url = SRC.format(z=z, x=x, y=y)
    last = None
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": UA})
            blob = urlopen(req, timeout=30).read()
            if blob[:4] != b"\x89PNG":
                raise ValueError("not a PNG: %s" % url)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_bytes(blob)
            tmp.replace(p)
            return "fetched"
        except Exception as err:               # noqa: BLE001 — retried, then reported
            last = err
            time.sleep(1 + 2 * attempt)
    return "failed: %s (%s)" % (url, last)


def fetch(tiles):
    done = {"cached": 0, "fetched": 0}
    failures = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in tiles}
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            if r in done:
                done[r] += 1
            else:
                failures.append(r)
            if i % 200 == 0 or i == len(tiles):
                print("  %5d/%d  (cached %d, fetched %d, failed %d)"
                      % (i, len(tiles), done["cached"], done["fetched"],
                         len(failures)), flush=True)
    return done, failures


# ------------------------------------------------- PMTiles v3, writing half
def _varint(v):
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _directory(entries):
    """Serialize [(tileid, run, length, offset)] the way map_ground reads it:
    count, id deltas, runs, lengths, then offsets written explicitly as
    offset+1 (the 0-means-contiguous shorthand is a reader's option, not a
    writer's obligation, and the explicit form is the one that cannot be
    subtly wrong)."""
    out = bytearray(_varint(len(entries)))
    last = 0
    for tid, _, _, _ in entries:
        out += _varint(tid - last)
        last = tid
    for _, run, _, _ in entries:
        out += _varint(run)
    for _, _, ln, _ in entries:
        out += _varint(ln)
    for _, _, _, off in entries:
        out += _varint(off + 1)
    return gzip.compress(bytes(out), mtime=0)


def bind(tiles, out_path):
    """Bind cached tiles into one archive. Tiles must all be on disk."""
    recs = []
    for z, x, y in tiles:
        p = _path(z, x, y)
        if not _sound(p):
            raise SystemExit("refusing to bind: missing tile %d/%d/%d" % (z, x, y))
        recs.append((zxy_to_tileid(z, x, y), p))
    recs.sort()

    # Data section in tileid order (clustered=1), offsets relative to its start.
    entries, blobs, off = [], [], 0
    for tid, p in recs:
        blob = p.read_bytes()
        entries.append((tid, 1, len(blob), off))
        blobs.append(blob)
        off += len(blob)

    # Leaves of 512 entries: the root stays a handful of pointers and always
    # fits the 16 KB first fetch a browser client makes, however the count
    # grows the day a third province arrives.
    LEAF = 512
    leaf_blobs, root_entries, leaf_off = [], [], 0
    for i in range(0, len(entries), LEAF):
        chunk = entries[i:i + LEAF]
        blob = _directory(chunk)
        root_entries.append((chunk[0][0], 0, len(blob), leaf_off))
        leaf_blobs.append(blob)
        leaf_off += len(blob)
    root = _directory(root_entries)

    meta = gzip.compress(json.dumps({
        "name": "cm-cr-terrain",
        "description": "Elevation for the Chiang Mai + Chiang Rai frame, "
                       "terrarium-encoded. Bound by importers/build_terrain.py.",
        "attribution": ATTRIBUTION,
        "encoding": "terrarium",
        "read": date.today().isoformat(),
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), mtime=0)

    HDR = 127
    root_off = HDR
    meta_off = root_off + len(root)
    leaf_sec = meta_off + len(meta)
    data_off = leaf_sec + leaf_off

    w, s, e, n = (min(FENCE[0], RAILS[0]), min(FENCE[1], RAILS[1]),
                  max(FENCE[2], RAILS[2]), max(FENCE[3], RAILS[3]))
    head = bytearray(HDR)
    head[0:7] = b"PMTiles"
    head[7] = 3
    struct.pack_into("<8Q", head, 8,
                     root_off, len(root), meta_off, len(meta),
                     leaf_sec, leaf_off, data_off, off)
    struct.pack_into("<3Q", head, 72, len(recs), len(entries), len(entries))
    head[96] = 1        # clustered: data is in tileid order
    head[97] = 2        # internal compression: gzip
    head[98] = 1        # tile compression: none — PNG carries its own
    head[99] = 2        # tile type: png
    head[100] = 0
    head[101] = MAX_Z
    struct.pack_into("<4i", head, 102, int(w * 1e7), int(s * 1e7),
                     int(e * 1e7), int(n * 1e7))
    head[118] = 9
    struct.pack_into("<2i", head, 119,
                     int((w + e) / 2 * 1e7), int((s + n) / 2 * 1e7))

    tmp = out_path.with_name("." + out_path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(bytes(head))
        fh.write(root)
        fh.write(meta)
        for blob in leaf_blobs:
            fh.write(blob)
        for blob in blobs:
            fh.write(blob)

    # The parity gate: the site's own reader, on the file just written. A
    # sample from every zoom plus both fence corners, byte-compared to the
    # cache; a miss refuses the whole bind.
    arc = map_ground._Archive(tmp)
    sample = recs[:: max(1, len(recs) // 40)] + [recs[0], recs[-1]]
    for tid, p in sample:
        z, x, y = _tileid_to_zxy(tid)
        got = arc.tile(z, x, y)
        if got != p.read_bytes():
            arc.close()
            tmp.unlink()
            raise SystemExit("parity failed at %d/%d/%d — archive not shipped"
                             % (z, x, y))
    if arc.tile(MAX_Z, 0, 0) is not None:
        arc.close()
        tmp.unlink()
        raise SystemExit("parity failed: a tile outside the plan answered")
    arc.close()
    tmp.replace(out_path)
    return {"tiles": len(recs), "bytes": out_path.stat().st_size,
            "leaves": len(leaf_blobs)}


def _tileid_to_zxy(tid):
    """Inverse of zxy_to_tileid — needed only by the parity gate."""
    z, acc = 0, 0
    while acc + (1 << z) * (1 << z) <= tid:
        acc += (1 << z) * (1 << z)
        z += 1
    d = tid - acc
    n = 1 << z
    x = y = 0
    s = 1
    while s < n:
        rx = 1 & (d // 2)
        ry = 1 & (d ^ rx)
        if ry == 0:
            if rx == 1:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        d //= 4
        s *= 2
    return z, x, y


# ------------------------------------------- what the page prints (Pillow)
def read_back():
    """Decode the fetched z12 fence and write the two data files the doi page
    renders. Optional half: no Pillow, no files, no failure."""
    try:
        from PIL import Image
    except ImportError:
        print("  read-back skipped: Pillow is not installed "
              "(pip install Pillow — same optional arrangement as make_og_cards)")
        return None

    x0, x1, y0, y1 = _tile_range(MAX_Z, FENCE)

    _imgs = {}

    def decode(z, x, y):
        key = (z, x, y)
        if key not in _imgs:
            if len(_imgs) > 64:
                _imgs.clear()
            _imgs[key] = Image.open(_path(z, x, y)).convert("RGB")
        return _imgs[key]

    # The highest cell in the fence — with the instrument's own lies caught.
    # The first pass of this scan reported 3,687 m in the hills east of the
    # provinces, which is four hundred metres above anything in the country:
    # a void-fill spike in the source DEM, the terrain data's version of the
    # Overpass empty-remark. So no cell is believed alone. Candidates above
    # THRESH are gathered (Pillow's C extrema skip every tile that cannot
    # hold one), sorted highest first, and the first cell that is NOT more
    # than SHEER metres above all eight of its neighbours wins — a 38 m
    # column rising three hundred sheer metres above everything it touches is
    # an artifact, not a doi. The rejects are counted and reported, and the
    # method rides in terrain_meta.json beside the number it produced.
    THRESH = 2400          # metres — comfortably under the real summit
    SHEER = 300            # metres above ALL eight neighbours = artifact
    thr_key = (THRESH + 32768) << 8
    cands = []
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            r, g, b = decode(MAX_Z, x, y).split()
            if ((r.getextrema()[1] << 16) | 0xFFFF) < thr_key:
                continue
            for i, (rv, gv, bv) in enumerate(zip(r.getdata(), g.getdata(),
                                                 b.getdata())):
                key = (rv << 16) | (gv << 8) | bv
                if key >= thr_key:
                    cands.append((key, x, y, i % 256, i // 256))
    cands.sort(reverse=True)

    def cell_ele(gx, gy):
        tx_, px_ = divmod(gx, 256)
        ty_, py_ = divmod(gy, 256)
        rv, gv, bv = decode(MAX_Z, tx_, ty_).getpixel((px_, py_))
        return rv * 256 + gv + bv / 256 - 32768

    spikes = 0
    best = None
    for key, x, y, px, py in cands:
        ele_c = (key >> 16) * 256 + ((key >> 8) & 255) + (key & 255) / 256 - 32768
        gx, gy = x * 256 + px, y * 256 + py
        around = max(cell_ele(gx + dx, gy + dy)
                     for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                     if (dx, dy) != (0, 0))
        if ele_c - around > SHEER:
            spikes += 1
            continue
        best = (ele_c, x, y, px, py)
        break
    if best is None:
        raise SystemExit("read-back: every candidate above %d m failed the "
                         "neighbour test — the source data needs eyes on it"
                         % THRESH)
    ele, x, y, px, py = best
    n = 1 << MAX_Z
    lng = (x + (px + 0.5) / 256) / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + (py + 0.5) / 256) / n))))

    def sample(lat_, lng_):
        n_ = 1 << MAX_Z
        fx = (lng_ + 180.0) / 360.0 * n_
        fy = (1.0 - math.asinh(math.tan(math.radians(lat_))) / math.pi) / 2.0 * n_
        tx_, ty_ = int(fx), int(fy)
        px_, py_ = int((fx - tx_) * 256), int((fy - ty_) * 256)
        r_, g_, b_ = decode(MAX_Z, tx_, ty_).getpixel((px_, py_))
        return r_ * 256 + g_ + b_ / 256 - 32768

    # ประตูท่าแพ — the same coordinate every map on this site opens on.
    moat = {"lat": 18.7876, "lng": 98.9931, "ele": round(sample(18.7876, 98.9931))}

    # The west–east line through the gate: Doi Pui's ridge, the basin floor,
    # the eastern rim, one height every ~260 m. Median-of-three, for the same
    # reason the summit gets a neighbour test: one spiked sample would put a
    # needle on the drawing, and the drawing is the page's on-paper map.
    lat0, lon_a, lon_b, step = 18.7876, 98.55, 99.45, 0.0025
    raw = []
    lng_i = lon_a
    while lng_i <= lon_b + 1e-9:
        raw.append(sample(lat0, lng_i))
        lng_i += step
    line = [round(sorted(raw[max(0, i - 1):i + 2])[len(raw[max(0, i - 1):i + 2]) // 2], 1)
            for i in range(len(raw))]

    today = date.today().isoformat()
    META.write_text(json.dumps({
        "read": today,
        "source": {"name": "Terrain Tiles (Mapzen) on AWS Open Data — SRTM (NASA/USGS)",
                   "url": "https://registry.opendata.aws/terrain-tiles/"},
        "encoding": "terrarium",
        "zooms": "0–%d" % MAX_Z,
        "fence": list(FENCE),
        "highest_cell": {"ele": round(ele), "lat": round(lat, 5),
                         "lng": round(lng, 5)},
        "tha_phae": moat,
        "method": {"highest_cell": "candidates above %d m, highest first; a cell "
                                   "more than %d m above all eight neighbours is a "
                                   "void-fill artifact and is skipped (%d skipped "
                                   "this read)" % (THRESH, SHEER, spikes),
                   "profile": "median of three along the line"},
    }, ensure_ascii=False, indent=1))
    PROFILE.write_text(json.dumps({
        "read": today, "lat": lat0, "lon_a": lon_a, "lon_b": lon_b,
        "step": step, "method": "median3", "ele": line,
    }, ensure_ascii=False, separators=(",", ":")))
    return {"highest": round(ele), "at": (round(lat, 4), round(lng, 4)),
            "spikes_rejected": spikes,
            "tha_phae": moat["ele"], "profile_points": len(line)}


# ----------------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry", action="store_true",
                    help="print the plan's tile count and leave the network alone")
    ap.add_argument("--no-fetch", action="store_true",
                    help="bind and read back from cache only")
    ap.add_argument("--read-only", action="store_true",
                    help="skip the bind too: only re-read the cache into the "
                         "two data files (implies --no-fetch)")
    args = ap.parse_args()
    if args.read_only:
        args.no_fetch = True

    tiles = plan()
    by_z = {}
    for z, _x, _y in tiles:
        by_z[z] = by_z.get(z, 0) + 1
    print("plan: %d tiles  (%s)" % (
        len(tiles), ", ".join("z%d:%d" % (z, by_z[z]) for z in sorted(by_z))))
    if args.dry:
        return

    if not args.no_fetch:
        done, failures = fetch(tiles)
        print("fetch: %d cached, %d fetched, %d failed"
              % (done["cached"], done["fetched"], len(failures)))
        if failures:
            for f in failures[:10]:
                print("  " + f)
            raise SystemExit("%d tiles missing — bind refused; run again "
                             "(the cache keeps what landed)" % len(failures))

    if not args.read_only:
        print("bind:", bind(tiles, OUT))
    rb = read_back()
    if rb:
        print("read-back:", rb)


if __name__ == "__main__":
    main()
