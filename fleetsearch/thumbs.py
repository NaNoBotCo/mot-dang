#!/usr/bin/env python3
"""fleetsearch/thumbs.py — the picture beside each search result.

    python3 fleetsearch/thumbs.py            # pages.jsonl → cache/fleetsearch/thumbs/
    python3 fleetsearch/thumbs.py --upload   # … and copy them to R2 under tiles/find/

A row gets the page's own picture when it has one, and a piece of map with its
pin when it does not. Both are 144 px squares, drawn at twice the size the
results page shows them, so they stay sharp on a phone.

PICTURES (thumbs/p/<hash>.webp). The crawler hands over `img` as a file in the
site's build or a URL on another host. Files are read off the disk. Of the
URLs, two kinds are fetched, small, once, and kept: IIIF scans (wichaa's
manuscripts, asked for at 300 px through the IIIF size parameter) and
Wikimedia Commons originals (asked for as Commons' own 330 px thumbnail).
Anything else on another host is left alone. The key is a hash of the file's
bytes, or of the URL for a fetched one, so a picture that changes gets a new
address rather than a stale cache.

An image that stands on more than PER_SITE_CAP pages of one site is that site's
decoration — a banner, a section header — and not the listing's picture.

MAP CELLS (thumbs/g/<x>_<y>.webp). A cell is a 2×2 block of zoom-16 tiles —
about 1.2 km across in Chiang Mai — chosen so the pin lands in its middle half,
never on an edge. One cell serves every page pinned inside it; the results page
draws the pin over it in CSS. The ground is Mot Dang's own basemap archive
(assets/tiles/cm-cr.pmtiles) read by map_ground.py, the painter the share
cards already use, so a thumbnail and the live map are the same map. A pin
outside that archive's bounds gets no cell.

WHY R2 UNDER tiles/: publish/deploy.py syncs docs/ onto the bucket and deletes
whatever docs/ does not hold — except tiles/**, which it excludes so the
basemap survives. These files are made here, not by build.py, so they live
where the sync does not reach. `--upload` is `rclone copy`, which adds and
replaces and never deletes.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CACHE = REPO / "cache" / "fleetsearch"
PAGES = CACHE / "pages.jsonl"
OUT = CACHE / "thumbs"
INDEX = CACHE / "thumbs.json"
FETCHED = CACHE / "thumbs-src"          # the small originals fetched from other hosts

PX = 144
QUALITY = 72
CELL_Z = 16
PER_SITE_CAP = 25
R2_PREFIX = "tiles/find"
UA = "motdang-fleetsearch/1.0 (https://motdang.net/find; thumbnails for search results)"

sys.path.insert(0, str(REPO))


# ------------------------------------------------------------------ the cell

def cell_of(lat: float, lon: float) -> tuple[int, int, float, float]:
    """(x, y) of the zoom-16 tile at the cell's top-left, and the pin's place
    inside the cell as fractions 0..1. The same arithmetic runs in
    publish/fleetsearch.js to place the dot."""
    n = 2 ** CELL_Z
    X = (lon + 180.0) / 360.0 * n
    Y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    tx, ty = int(math.floor(X)), int(math.floor(Y))
    hx = tx if X - tx >= 0.5 else tx - 1
    hy = ty if Y - ty >= 0.5 else ty - 1
    return hx, hy, (X - hx) / 2.0, (Y - hy) / 2.0


def tile_corner(x: int, y: int, z: int) -> tuple[float, float]:
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


_G = None


def _ground():
    global _G
    if _G is None:
        import map_ground
        _G = map_ground.Ground()
    return _G


def inked(im, paper) -> bool:
    """Whether a cell shows anything but paper. A pin on blank paper — the
    basemap holds no road, water or wood within 600 m of it — says nothing,
    so that row goes without a map."""
    px = im.convert("RGB").resize((72, 72)).getdata()
    ink = sum(1 for c in px if max(abs(c[0] - paper[0]), abs(c[1] - paper[1]), abs(c[2] - paper[2])) > 14)
    return ink >= 0.015 * 72 * 72


def draw_cell(job):
    """One cell → its .webp, or the reason it has none."""
    hx, hy, dst = job
    from PIL import Image
    g = _ground()
    if not g.available:
        return hx, hy, "no ground archive"
    n_, w_ = tile_corner(hx, hy, CELL_Z)
    s_, e_ = tile_corner(hx + 2, hy + 2, CELL_Z)
    ss = 3
    big = PX * ss
    im = Image.new("RGB", (big, big), g.palette["paper"])

    def xy(p):
        return ((p[1] - w_) / (e_ - w_) * big, (n_ - p[0]) / (n_ - s_) * big)
    try:
        ok = g.paint(im, xy, (s_, w_, n_, e_), width_px=big, scale=ss * 0.8, contrast=1.6)
    except Exception as e:                      # one bad tile must not stop the run
        return hx, hy, f"paint: {e!r}"[:200]
    if not ok:
        return hx, hy, "empty ground"
    im = im.resize((PX, PX), Image.LANCZOS)
    if not inked(im, g.palette["paper"]):
        return hx, hy, "blank paper"
    tmp = dst.with_suffix(".tmp")
    im.save(tmp, "WEBP", quality=QUALITY, method=6)
    os.replace(tmp, dst)
    return hx, hy, ""


# ------------------------------------------------------------------ pictures

RE_IIIF = re.compile(r"^(https?://[^?#]+?)/(full|square|\d+,\d+,\d+,\d+|pct:[^/]+)/[^/]+/(\d+|!?\d*)/(default|color|gray|native)\.(jpg|png|webp)$")
RE_COMMONS = re.compile(r"^https://upload\.wikimedia\.org/wikipedia/commons/(?!thumb/)([0-9a-f])/([0-9a-f]{2})/([^/?#]+)$")


def remote_small(url: str) -> str:
    """A URL on another host → the address of a small copy, or '' when there
    is no polite way to ask for one."""
    m = RE_IIIF.match(url)
    if m:
        return f"{m.group(1)}/full/!300,300/0/default.jpg"
    m = RE_COMMONS.match(url)
    if m and not m.group(3).lower().endswith((".svg", ".tif", ".tiff", ".pdf", ".djvu")):
        f = m.group(3)
        return (f"https://upload.wikimedia.org/wikipedia/commons/thumb/{m.group(1)}/{m.group(2)}/{f}/330px-{f}")
    if url.startswith("https://upload.wikimedia.org/wikipedia/commons/thumb/"):
        return url
    return ""


def fetch(url: str, dst: Path) -> str:
    if dst.exists():
        return ""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read(4_000_000)
    except (urllib.error.URLError, OSError, ValueError) as e:
        return f"fetch: {e}"[:200]
    dst.write_bytes(body)
    return ""


def square(src, dst: Path) -> str:
    from PIL import Image, ImageOps
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = Image.new("RGB", im.size, (255, 253, 248))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            else:
                im = im.convert("RGB")
            w, h = im.size
            if min(w, h) < 48:
                return "too small"
            s = min(w, h)
            im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
            im = im.resize((PX, PX), Image.LANCZOS)
            tmp = dst.with_suffix(".tmp")
            im.save(tmp, "WEBP", quality=QUALITY, method=6)
            os.replace(tmp, dst)
    except Exception as e:                      # a broken file is a missing picture
        return f"image: {e!r}"[:200]
    return ""


def picture_job(src: str):
    """One `img` value → (src, key or '', reason)."""
    if src.startswith("file:"):
        f = Path(src[5:])
        try:
            key = hashlib.sha1(f.read_bytes()).hexdigest()[:16]
        except OSError as e:
            return src, "", f"read: {e}"
        dst = OUT / "p" / f"{key}.webp"
        why = "" if dst.exists() else square(f, dst)
        return src, ("" if why else key), why
    small = remote_small(src)
    if not small:
        return src, "", "another host, no small copy"
    key = hashlib.sha1(small.encode()).hexdigest()[:16]
    dst = OUT / "p" / f"{key}.webp"
    if dst.exists():
        return src, key, ""
    raw = FETCHED / f"{key}.img"
    why = fetch(small, raw)
    if why:
        return src, "", why
    why = square(raw, dst)
    return src, ("" if why else key), why


# ------------------------------------------------------------------ the run

def plan(pages=PAGES):
    """pages.jsonl → (pictures wanted, cells wanted)."""
    per_site = collections.defaultdict(collections.Counter)
    rows = []
    with open(pages, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows.append((r["site"], r.get("img") or "", r.get("lat"), r.get("lon")))
            if r.get("img"):
                per_site[r["site"]][r["img"]] += 1
    pics, cells = set(), set()
    for site, img, lat, lon in rows:
        if img and per_site[site][img] <= PER_SITE_CAP:
            pics.add(img)
        if lat is not None and lon is not None:
            hx, hy, _, _ = cell_of(lat, lon)
            cells.add((hx, hy))
    return pics, cells, {s: [k for k, v in c.items() if v > PER_SITE_CAP] for s, c in per_site.items()}


def bounds():
    try:
        import map_ground
        a = map_ground.Ground().archive
        return a.bounds                           # S, W, N, E
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--fetch-jobs", type=int, default=6)
    ap.add_argument("--upload", action="store_true", help="also copy to R2 under tiles/find/")
    ap.add_argument("--upload-only", action="store_true")
    ap.add_argument("--pages", default=str(PAGES), help="another corpus, to draw ahead of a crawl")
    a = ap.parse_args(argv)
    if a.upload_only:
        return upload()
    (OUT / "p").mkdir(parents=True, exist_ok=True)
    (OUT / "g").mkdir(parents=True, exist_ok=True)
    FETCHED.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pics, cells, decor = plan(Path(a.pages))
    b = bounds()
    if b:
        s, w, n, e = b

        def inside(c):
            lat, lon = tile_corner(c[0] + 1, c[1] + 1, CELL_Z)      # the cell's centre
            return s <= lat <= n and w <= lon <= e
        outside = {c for c in cells if not inside(c)}
        cells -= outside
    else:
        outside = set(cells)
        cells = set()
    print(f"{len(pics)} pictures, {len(cells)} map cells wanted "
          f"({len(outside)} pinned cells outside the ground)", file=sys.stderr)

    old = {}
    if INDEX.exists():
        try:
            old = json.loads(INDEX.read_text(encoding="utf-8"))
        except ValueError:
            old = {}
    done_pics, failed = {}, {}
    local = sorted(p for p in pics if p.startswith("file:"))
    remote = sorted(p for p in pics if not p.startswith("file:"))
    with Pool(a.jobs) as pool:
        for src, key, why in pool.imap_unordered(picture_job, local, chunksize=16):
            (done_pics.__setitem__(src, key) if key else failed.__setitem__(src, why))
    # Other hosts are asked a few at a time. A failure is remembered and not
    # asked again on the next run; deleting thumbs.json forgets them all.
    # A 429 is "not now", not "never", so it is asked again next run.
    skip = {k for k, v in (old.get("failed") or {}).items() if v.startswith("fetch") and "429" not in v}
    todo = [p for p in remote if p not in skip]
    iiif = [p for p in todo if "wikimedia.org" not in p]
    commons = [p for p in todo if "wikimedia.org" in p]
    with Pool(a.fetch_jobs) as pool:
        for src, key, why in pool.imap_unordered(picture_job, iiif, chunksize=4):
            (done_pics.__setitem__(src, key) if key else failed.__setitem__(src, why))
    # Wikimedia answers 429 to six at once, so Commons is asked one at a time.
    for src in commons:
        small = remote_small(src)
        asked = bool(small) and not (FETCHED / f"{hashlib.sha1(small.encode()).hexdigest()[:16]}.img").exists()
        src, key, why = picture_job(src)
        if "429" in why:
            time.sleep(30)
            src, key, why = picture_job(src)
        (done_pics.__setitem__(src, key) if key else failed.__setitem__(src, why))
        if asked:
            time.sleep(1.0)
    for p in remote:
        if p in skip and p not in done_pics:
            failed[p] = old["failed"][p]
    print(f"  pictures: {len(done_pics)} made or kept, {len(failed)} without  {time.time()-t0:.0f}s",
          file=sys.stderr)

    done_cells, empty = [], []
    jobs = []
    paper = None
    for hx, hy in sorted(cells):
        dst = OUT / "g" / f"{hx}_{hy}.webp"
        if dst.exists():
            if paper is None:
                paper = _ground().palette["paper"]
            from PIL import Image
            with Image.open(dst) as im:
                ok = inked(im, paper)
            if ok:
                done_cells.append(f"{hx}_{hy}")
            else:
                dst.unlink()
                empty.append(f"{hx}_{hy}")
        else:
            jobs.append((hx, hy, dst))
    if jobs:
        with Pool(a.jobs) as pool:
            for i, (hx, hy, why) in enumerate(pool.imap_unordered(draw_cell, jobs, chunksize=8)):
                (empty.append(f"{hx}_{hy}") if why else done_cells.append(f"{hx}_{hy}"))
                if (i + 1) % 1000 == 0:
                    print(f"  cells {i+1}/{len(jobs)}  {time.time()-t0:.0f}s", file=sys.stderr)
    print(f"  cells: {len(done_cells)} drawn or kept, {len(empty)} empty  {time.time()-t0:.0f}s",
          file=sys.stderr)

    INDEX.write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "px": PX, "z": CELL_Z, "prefix": R2_PREFIX,
        "pics": done_pics, "cells": sorted(done_cells),
        "failed": failed, "empty": sorted(empty), "decoration": decor,
    }, ensure_ascii=False, indent=0))
    kb = sum(p.stat().st_size for p in OUT.rglob("*.webp")) / 1024
    print(f"{INDEX}: {len(done_pics)} pictures + {len(done_cells)} cells, {kb/1024:.1f} MB on disk",
          file=sys.stderr)
    if a.upload:
        return upload()
    return 0


def upload() -> int:
    """rclone copy thumbs/ → R2 tiles/find/. Adds and replaces; never deletes."""
    sys.path.insert(0, str(REPO / "publish"))
    import deploy
    env = deploy.rclone_env(deploy.creds())
    dest = f"R2:{deploy.BUCKET}/{R2_PREFIX}"
    t = time.time()
    r = subprocess.run(["rclone", "copy", str(OUT), dest, "--checksum", "--include", "*.webp",
                        "--transfers", "64", "--checkers", "32", "--s3-no-head", "--fast-list",
                        "--stats", "15s", "--stats-one-line", "--stats-log-level", "NOTICE"],
                       env=env)
    print(f"uploaded to {dest} in {time.time()-t:.0f}s (exit {r.returncode})", file=sys.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
