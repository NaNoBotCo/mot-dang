#!/usr/bin/env python3
"""harvest_streetview.py — Mapillary photos along the streets, for street view.

    python3 importers/harvest_streetview.py --area oldcity
    python3 importers/harvest_streetview.py --bbox w,s,e,n
    python3 importers/harvest_streetview.py --self-test       # no network

Her pick (a), 2026-10-13: street view from our own copies. harvest_mapillary.py
keeps one photo per place; this keeps the photos along each drive or walk
(a Mapillary "sequence"), about one every STEP_M metres, so a reader can step
down a street. Runs on motdang-server, in the staging folder, like the other
harvest (her word 2026-10-11: rented storage, not the Mac).

Writes:
  assets/streetphotos/sv/<imageId>.jpg   1024 px, as Mapillary serves it
  data/streetview/<cell>.json            one file per 0.01° cell (about 1.1 km)
      {"by": [names], "seq": {seqId: [year, byIndex]},
       "img": [[imageId, lat, lng, heading, seqId, order, "YYYY-MM-DD"|null], ...]}
  cache/streetview-harvest.json          tiles done, so a stopped run resumes

A photo already downloaded for a place (data/street_photos.json) is linked,
not fetched again. Photos with no photographer name are left out: CC BY-SA
wants the name (credit_of in harvest_mapillary.py). 360° panoramas are left
out: the viewer shows flat photos.
"""

import argparse
import json
import math
import os
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harvest_mapillary as hm  # noqa: E402

ROOT = hm.ROOT
OUT_IMG = ROOT / "assets" / "streetphotos" / "sv"   # rides the streetphotos media route
OUT_IDX = ROOT / "data" / "streetview"
STATE = ROOT / "cache" / "streetview-harvest.json"
LOCK = "/srv/state/stage.lock"          # held by the server walk while it copies staging

FIELDS = ("id", "captured_at", "compass_angle", "computed_compass_angle",
          "geometry", "computed_geometry", "thumb_1024_url", "creator",
          "is_pano", "sequence")
AREAS = {
    # The moat and a ring of about 300 m around it.
    "oldcity": (98.9780, 18.7760, 99.0040, 18.8000),
}
TILE = 0.002          # about 220 m; split further when Mapillary hits its cap
CAP = 2000
STEP_M = 8.0          # keep a photo once the camera has moved this far
TURN_DEG = 50.0       # or turned this much
CELL = 0.01


def cell_of(lat, lng):
    return "%d_%d" % (math.floor(lat / CELL), math.floor(lng / CELL))


# ── fetch ────────────────────────────────────────────────────────────────────

def fetch(bbox, tok):
    w, s, e, n = bbox
    q = urllib.parse.urlencode({"fields": ",".join(FIELDS),
                                "bbox": "%.6f,%.6f,%.6f,%.6f" % (w, s, e, n),
                                "limit": str(CAP)})
    req = urllib.request.Request(hm.API + "?" + q, headers={
        "Authorization": "OAuth " + tok, "User-Agent": hm.UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8")).get("data") or []
        except urllib.error.HTTPError as ex:
            msg = hm._explain(ex.read(), ex.code)
            if "token" in msg.lower():
                raise RuntimeError(msg)
        except Exception as ex:          # timeouts on dense tiles; split below
            msg = str(ex)
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("tile %s: %s" % (bbox, msg))


def tile_images(bbox, tok, depth=0, say=print):
    """Every image in the box. A tile at the cap, or one that keeps timing
    out, is split in four rather than trusted."""
    try:
        got = fetch(bbox, tok)
    except RuntimeError as ex:
        if "token" in str(ex).lower() or depth >= 4:
            raise
        got = None
    if got is not None and (len(got) < CAP or depth >= 4):
        return got
    w, s, e, n = bbox
    mx, my = (w + e) / 2, (s + n) / 2
    out = []
    for b in ((w, s, mx, my), (mx, s, e, my), (w, my, mx, n), (mx, my, e, n)):
        out += tile_images(b, tok, depth + 1, say)
    return out


def tiles(bbox):
    w, s, e, n = bbox
    out, y = [], s
    while y < n - 1e-9:
        x = w
        while x < e - 1e-9:
            out.append((round(x, 6), round(y, 6),
                        round(min(x + TILE, e), 6), round(min(y + TILE, n), 6)))
            x += TILE
        y += TILE
    return out


# ── choose ───────────────────────────────────────────────────────────────────

def point(im):
    g = (im.get("computed_geometry") or im.get("geometry") or {}).get("coordinates")
    return (g[1], g[0]) if g and g[0] is not None else None


def heading(im):
    h = im.get("computed_compass_angle")
    if h is None:
        h = im.get("compass_angle")
    return None if h is None else float(h) % 360


def turn(a, b):
    if a is None or b is None:
        return 0.0
    d = abs(a - b) % 360
    return min(d, 360 - d)


def thin(seq_images):
    """One sequence, in capture order, thinned to a photo every STEP_M metres
    or at a turn. The first and last photo always stay."""
    ims = sorted(seq_images, key=lambda i: (i.get("captured_at") or 0, i["id"]))
    kept = []
    for i, im in enumerate(ims):
        p = point(im)
        if not p:
            continue
        if not kept or i == len(ims) - 1:
            kept.append(im)
            continue
        q = point(kept[-1])
        if (hm.metres(p[0], p[1], q[0], q[1]) >= STEP_M
                or turn(heading(im), heading(kept[-1])) >= TURN_DEG):
            kept.append(im)
    return kept


def usable(im):
    return (not im.get("is_pano") and im.get("thumb_1024_url")
            and im.get("sequence") and point(im)
            and ((im.get("creator") or {}).get("username") or "").strip())


def date_of(im):
    d = hm._when(im.get("captured_at"))
    return d if d and d >= "2000" else None


# ── write ────────────────────────────────────────────────────────────────────

def _locked(fn):
    try:
        import fcntl
        with open(LOCK, "a") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            return fn()
    except (FileNotFoundError, PermissionError):
        return fn()


def _atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    os.replace(tmp, path)


def write_cells(rows):
    """rows: {imageId: row dict}. Rewrites every cell the rows touch, merged
    with what the cell already holds."""
    by_cell = defaultdict(dict)
    for r in rows.values():
        by_cell[cell_of(r["lat"], r["lng"])][r["id"]] = r

    def go():
        for c, new in by_cell.items():
            p = OUT_IDX / ("%s.json" % c)
            old = {}
            if p.exists():
                d = json.loads(p.read_text())
                for i in d["img"]:
                    sid = i[4]
                    yr, bi = d["seq"].get(sid, [None, 0])
                    old[i[0]] = {"id": i[0], "lat": i[1], "lng": i[2], "h": i[3],
                                 "seq": sid, "ord": i[5], "date": i[6],
                                 "by": d["by"][bi]}
            old.update(new)
            names, seqs, img = [], {}, []
            for r in sorted(old.values(), key=lambda r: (r["seq"], r["ord"])):
                if r["by"] not in names:
                    names.append(r["by"])
                seqs.setdefault(r["seq"], [int(r["date"][:4]) if r["date"] else None,
                                           names.index(r["by"])])
                img.append([r["id"], round(r["lat"], 6), round(r["lng"], 6),
                            None if r["h"] is None else round(r["h"]),
                            r["seq"], r["ord"], r["date"]])
            _atomic(p, {"by": names, "seq": seqs, "img": img})
    _locked(go)


def known_files():
    """imageId -> a file harvest_mapillary.py already downloaded."""
    p = ROOT / "data" / "street_photos.json"
    if not p.exists():
        return {}
    out = {}
    for v in (json.loads(p.read_text()).get("photos") or {}).values():
        if v.get("imageId") and v.get("file"):
            out[str(v["imageId"])] = ROOT / "assets" / "streetphotos" / v["file"]
    return out


def save_image(im, have):
    dest = OUT_IMG / ("%s.jpg" % im["id"])
    if dest.exists() and dest.stat().st_size > 1024:
        return 0
    src = have.get(str(im["id"]))
    if src and src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, dest)
        except OSError:
            dest.write_bytes(src.read_bytes())
        return 0
    return hm.download(im["thumb_1024_url"], dest)


# ── run ──────────────────────────────────────────────────────────────────────

def harvest(bbox, tok, say=print):
    state = json.loads(STATE.read_text()) if STATE.exists() else {"done": []}
    done = set(map(tuple, state["done"]))
    todo = [t for t in tiles(bbox) if t not in done]
    have = known_files()
    say("tiles %d, left %d" % (len(tiles(bbox)), len(todo)))
    stop = {"now": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(now=True))

    # Sequences cross tiles, so thinning waits until a sequence's images are
    # all in hand: images collect per tile, thinning and downloads run per batch.
    seen = set()
    batch = defaultdict(dict)
    total = got = 0

    def flush():
        nonlocal got
        rows = {}
        for sid, ims in batch.items():
            for k, im in enumerate(thin(list(ims.values()))):
                try:
                    got += save_image(im, have)
                except Exception as ex:
                    say("  %s: %s" % (im["id"], ex))
                    continue
                lat, lng = point(im)
                rows[im["id"]] = {"id": im["id"], "lat": lat, "lng": lng,
                                  "h": heading(im), "seq": sid,
                                  "ord": int((im.get("captured_at") or 0) // 1000),
                                  "date": date_of(im),
                                  "by": im["creator"]["username"].strip()}
                time.sleep(0.05)
        write_cells(rows)
        batch.clear()
        return len(rows)

    for n, t in enumerate(todo, 1):
        if stop["now"]:
            break
        for im in tile_images(t, tok, say=say):
            if im["id"] in seen or not usable(im):
                continue
            seen.add(im["id"])
            batch[im["sequence"]][im["id"]] = im
        done.add(t)
        if n % 25 == 0 or n == len(todo):
            total += flush()
            state["done"] = sorted(done)
            _atomic(STATE, state)
            say("%s tile %d/%d · kept %d · downloaded %.1f MB"
                % (time.strftime("%H:%M"), n, len(todo), total, got / 1e6))
        time.sleep(hm.PAUSE)
    total += flush()
    state["done"] = sorted(done)
    _atomic(STATE, state)
    say("finished · kept %d · downloaded %.1f MB" % (total, got / 1e6))
    return total


def self_test(say=print):
    ok = True

    def check(name, cond):
        nonlocal ok
        say("  %-50s %s" % (name, "ok" if cond else "FAILED"))
        ok = ok and bool(cond)

    def im(i, lat, lng, h=0, t=0, **kw):
        d = {"id": str(i), "captured_at": 1700000000000 + t * 1000,
             "geometry": {"coordinates": [lng, lat]}, "compass_angle": h,
             "thumb_1024_url": "x", "sequence": "s", "creator": {"username": "u"}}
        d.update(kw)
        return d

    step = 0.00002     # about 2.2 m north
    line = [im(i, 18.79 + i * step, 98.99, t=i) for i in range(20)]
    kept = thin(line)
    check("thinning keeps about one per 8 m", 5 <= len(kept) <= 7)
    check("first and last stay", kept[0]["id"] == "0" and kept[-1]["id"] == "19")
    check("a turn keeps the photo",
          len(thin([im(0, 18.79, 98.99), im(1, 18.79, 98.99, h=90, t=1),
                    im(2, 18.79, 98.99, h=90, t=2)])) == 3)
    check("panoramas are left out", not usable(im(1, 18.79, 98.99, is_pano=True)))
    check("no photographer, left out", not usable(im(1, 18.79, 98.99, creator={})))
    check("1970 dates read as unknown", date_of(im(1, 0, 0, captured_at=5)) is None)
    check("cells are 0.01°", cell_of(18.7891, 98.9876) == "1878_9898")
    check("tiles cover the box", len(tiles((0, 0, 0.004, 0.004))) == 4)
    say("\nself-test: %s" % ("all checks passed" if ok else "FAILURES above"))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--area", choices=sorted(AREAS))
    ap.add_argument("--bbox", help="w,s,e,n")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return 0 if self_test() else 1
    if a.area:
        bbox = AREAS[a.area]
    elif a.bbox:
        bbox = tuple(float(x) for x in a.bbox.split(","))
    else:
        ap.error("--area or --bbox")
    try:
        tok = hm.token()
    except hm.NoToken as ex:
        print(ex, file=sys.stderr)
        return 2
    harvest(bbox, tok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
