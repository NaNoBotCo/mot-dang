#!/usr/bin/env python3
"""Pull gifts from มรดกข้อมูล · Bequeath your data (motdang.net/bequeath).

The Worker (repo: ~/Developer/claude code projects/bequeath) keeps each gift
in the PRIVATE bucket motdang-bequeath: the raw files at raw/<gift>/..., and
cards/<gift>.json, the manifest with the gift's state, review and current use
card. Nothing serves that bucket. This reads it over the S3 API with the R2
credentials already on this Mac (~/.mot-dang-r2.json or R2_* in the
environment), the same arrangement as the listing-photo inbox in
listing-sheet/intake.py --photos-pull.

For each gift:

  in use now, or released by its keeper, and not held for review
      -> read the raw files, cut everything inside the blur circle around
         home, write
           data/curated/gifts/<gift>.json   the card id, version and sha, the
                                            permitted uses, credit, licence
                                            and counts. No points, no home.
           cache/gifts/<gift>/points.json   the points, places and photo
                                            locations, after the blur.
           cache/gifts/<gift>/photos/       the photos, as given.
  sealed, withdrawn, or held
      -> both removed if present.

cache/ is outside git and outside the source archive (build.py SOURCE_NEVER);
data/curated/ is inside both, which is why the curated file carries the card
and not the data.

A sealed gift ("after me") is stored encrypted in the bucket and is not
usable, so this never fetches it. The Worker decrypts a gift back to plain
bytes when it is released — by the keeper's code, or when its date passes —
so every gift this reads is already plaintext. No key handling here.

The blur: home is the marked point, or the most frequent night spot in the
gift (22:00-05:00 Bangkok, on a ~220 m grid, three points or more). The circle
is centred up to a third of the radius away from home, in a direction fixed
by the gift id, and widened by the same distance, so home stays inside it and
the edge of the cut does not point at it. A gift asking for a blur whose home
cannot be found keeps its points out (home_not_found).

Not wired into the walk. It would run beside sync_claims.py, before build.py:
    python3 importers/bequeath_pull.py
and tests/test_gifts_gate.py after the build, beside test_publish_gate.py.

    python3 importers/bequeath_pull.py                 pull from R2
    python3 importers/bequeath_pull.py --from DIR      a folder laid out like
                                                       the bucket (the Worker's
                                                       dev server writes one)
    python3 importers/bequeath_pull.py --dry-run
    python3 importers/bequeath_pull.py --root DIR      write under DIR, not this repo
"""
import hashlib
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "data" / "curated" / "gifts"
CACHE = ROOT / "cache" / "gifts"
BUCKET = "motdang-bequeath"

NIGHT_FROM, NIGHT_TO = 22, 5
TZ = 7 * 3600
CELL = 0.002
NIGHT_MIN = 3
ZIP_MAX_ENTRIES = 5000
ZIP_MAX_DECLARED = 400 * 1024 * 1024
ZIP_MAX_RATIO = 200
READ_MAX = 256 * 1024 * 1024       # one file inflated or read, here at home
DATA_IN_ZIP = re.compile(r"\.(json|gpx|kml|geojson|csv|fit)$", re.I)
MEDIA = re.compile(r"\.(jpe?g|heic|heif|png|gif|webp|mp4|mov|m4v|avi|3gp|mkv|webm|tiff?|dng|raw)$", re.I)


# ---------------------------------------------------------------- reading
class Found:
    """Points, places and names gathered from one gift."""

    def __init__(self):
        self.points = []   # [lat, lon, t_ms|None, t_end|None]
        self.places = []   # {name, lat, lon}
        self.photos = []   # {file, lat, lon, taken, people}

    def add(self, lat, lon, t=None, t_end=None):
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            return False
        if not (math.isfinite(lat) and math.isfinite(lon)) or abs(lat) > 90 or abs(lon) > 180:
            return False
        if lat == 0 and lon == 0:
            return False
        self.points.append([round(lat, 6), round(lon, 6), t, t_end])
        return True

    def place(self, name, lat, lon):
        try:
            lat, lon = float(lat), float(lon)
            ok = math.isfinite(lat) and math.isfinite(lon) and not (lat == 0 and lon == 0)
        except (TypeError, ValueError):
            ok = False
        self.places.append({"name": (name or "")[:200], "lat": round(lat, 6) if ok else None,
                            "lon": round(lon, 6) if ok else None})


def to_ms(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return int(v) if v > 1e12 else int(v * 1000) if v > 1e9 else None
    s = str(v).strip()
    if re.fullmatch(r"\d{12,14}", s):
        return int(s)
    try:
        s2 = s.replace("Z", "+00:00")
        d = datetime.fromisoformat(re.sub(r"(\.\d{6})\d+", r"\1", s2))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return int(d.timestamp() * 1000)
    except ValueError:
        return None


def latlng_text(s):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*°?\s*,\s*(-?\d+(?:\.\d+)?)", str(s or ""))
    return (float(m.group(1)), float(m.group(2))) if m else None


def latlng_url(u):
    s = str(u or "")
    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", s) \
        or re.search(r"[?&](?:q|query|ll|center)=(-?\d+\.\d+),\s*(-?\d+\.\d+)", s) \
        or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", s)
    return (float(m.group(1)), float(m.group(2))) if m else None


def e7(v):
    try:
        return float(v) / 1e7
    except (TypeError, ValueError):
        return None


def _attr(s, name):
    m = re.search(r"\b%s\s*=\s*[\"']([^\"']*)[\"']" % name, s)
    return m.group(1) if m else None


def _inner(s, tag):
    m = re.search(r"<(?:\w+:)?%s\b[^>]*>([\s\S]*?)</(?:\w+:)?%s>" % (tag, tag), s)
    if not m:
        return None
    v = re.sub(r"<!\[CDATA\[([\s\S]*?)\]\]>", r"\1", m.group(1))
    return (v.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            .replace("&apos;", "'").replace("&amp;", "&").strip())


def read_gpx(text, f):
    for m in re.finditer(r"<(?:\w+:)?(trkpt|rtept|wpt)\b([^>]*?)(?:/>|>([\s\S]*?)</(?:\w+:)?\1>)", text):
        lat, lon, body = _attr(m.group(2), "lat"), _attr(m.group(2), "lon"), m.group(3) or ""
        if m.group(1) == "wpt":
            f.place(_inner(body, "name"), lat, lon)
        else:
            f.add(lat, lon, to_ms(_inner(body, "time")))


def read_kml(text, f):
    any_pm = False
    for m in re.finditer(r"<(?:\w+:)?Placemark\b[^>]*>([\s\S]*?)</(?:\w+:)?Placemark>", text):
        any_pm = True
        body = m.group(1)
        if re.search(r"<(?:\w+:)?Point\b", body) and not re.search(r"<(?:\w+:)?(LineString|Polygon|Track|MultiTrack)\b", body):
            c = re.search(r"<(?:\w+:)?coordinates>([\s\S]*?)</(?:\w+:)?coordinates>", body)
            parts = re.split(r"[\s,]+", c.group(1).strip()) if c else []
            f.place(_inner(body, "name"), parts[1] if len(parts) > 1 else None, parts[0] if parts else None)
            continue
        _kml_geometry(body, f)
    if not any_pm:
        _kml_geometry(text, f)


def _kml_geometry(body, f):
    for c in re.finditer(r"<(?:\w+:)?coordinates>([\s\S]*?)</(?:\w+:)?coordinates>", body):
        for tup in c.group(1).split():
            p = tup.split(",")
            if len(p) >= 2:
                f.add(p[1], p[0])
    for tr in re.finditer(r"<(?:\w+:)?Track\b[^>]*>([\s\S]*?)</(?:\w+:)?Track>", body):
        whens = [to_ms(x.strip()) for x in re.findall(r"<(?:\w+:)?when>([^<]*)</(?:\w+:)?when>", tr.group(1))]
        coords = [x.split() for x in re.findall(r"<(?:\w+:)?coord>([^<]*)</(?:\w+:)?coord>", tr.group(1))]
        for i, c in enumerate(coords):
            if len(c) >= 2:
                f.add(c[1], c[0], whens[i] if i < len(whens) else None)


def json_kind(j):
    if isinstance(j, list):
        first = next((x for x in j if isinstance(x, dict)), None)
        if first and "startTime" in first and ("visit" in first or "activity" in first or "timelinePath" in first):
            return "timeline-ios"
        return None
    if not isinstance(j, dict):
        return None
    if isinstance(j.get("locations"), list):
        return "takeout-records"
    if isinstance(j.get("timelineObjects"), list):
        return "takeout-semantic"
    if isinstance(j.get("semanticSegments"), list) or isinstance(j.get("rawSignals"), list):
        return "timeline"
    if j.get("type") == "FeatureCollection" and isinstance(j.get("features"), list):
        saved = any(isinstance(ft, dict) and isinstance(ft.get("properties"), dict)
                    and any(k in ft["properties"] for k in ("google_maps_url", "location", "Title"))
                    for ft in j["features"])
        return "saved-places" if saved else "geojson"
    if j.get("type") in ("Feature", "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon",
                         "MultiPolygon", "GeometryCollection"):
        return "geojson"
    return None


def read_json(kind, j, f):
    g = lambda d, *ks: _dig(d, ks)  # noqa: E731
    if kind == "takeout-records":
        for l in j.get("locations") or []:
            f.add(e7(l.get("latitudeE7")), e7(l.get("longitudeE7")), to_ms(l.get("timestamp", l.get("timestampMs"))))
    elif kind == "takeout-semantic":
        for o in j.get("timelineObjects") or []:
            v = o.get("placeVisit")
            if v:
                loc = v.get("location") or {}
                f.add(e7(loc.get("latitudeE7")), e7(loc.get("longitudeE7")),
                      to_ms(g(v, "duration", "startTimestamp") or g(v, "duration", "startTimestampMs")),
                      to_ms(g(v, "duration", "endTimestamp") or g(v, "duration", "endTimestampMs")))
            a = o.get("activitySegment")
            if a:
                s, e = a.get("startLocation") or {}, a.get("endLocation") or {}
                f.add(e7(s.get("latitudeE7")), e7(s.get("longitudeE7")), to_ms(g(a, "duration", "startTimestamp")))
                for p in g(a, "waypointPath", "waypoints") or []:
                    f.add(e7(p.get("latE7")), e7(p.get("lngE7")))
                for p in g(a, "simplifiedRawPath", "points") or []:
                    f.add(e7(p.get("latE7")), e7(p.get("lngE7")), to_ms(p.get("timestamp", p.get("timestampMs"))))
                f.add(e7(e.get("latitudeE7")), e7(e.get("longitudeE7")), to_ms(g(a, "duration", "endTimestamp")))
    elif kind == "timeline":
        for s in j.get("semanticSegments") or []:
            st, en = to_ms(s.get("startTime")), to_ms(s.get("endTime"))
            ll = latlng_text(g(s, "visit", "topCandidate", "placeLocation", "latLng"))
            if ll:
                f.add(ll[0], ll[1], st, en)
            a, b = latlng_text(g(s, "activity", "start", "latLng")), latlng_text(g(s, "activity", "end", "latLng"))
            if a:
                f.add(a[0], a[1], st)
            if b:
                f.add(b[0], b[1], en)
            for p in s.get("timelinePath") or []:
                ll = latlng_text(p.get("point"))
                if ll:
                    f.add(ll[0], ll[1], to_ms(p.get("time")))
        for r in j.get("rawSignals") or []:
            pos = r.get("position") or {}
            ll = latlng_text(pos.get("LatLng") or pos.get("latLng"))
            if ll:
                f.add(ll[0], ll[1], to_ms(pos.get("timestamp") or r.get("timestamp")))
    elif kind == "timeline-ios":
        for s in j:
            if not isinstance(s, dict):
                continue
            st, en = to_ms(s.get("startTime")), to_ms(s.get("endTime"))
            p = latlng_text(g(s, "visit", "topCandidate", "placeLocation"))
            if p:
                f.add(p[0], p[1], st, en)
            a, b = latlng_text(g(s, "activity", "start")), latlng_text(g(s, "activity", "end"))
            if a:
                f.add(a[0], a[1], st)
            if b:
                f.add(b[0], b[1], en)
            for q in s.get("timelinePath") or []:
                ll = latlng_text(q.get("point"))
                try:
                    off = float(q.get("durationMinutesOffsetFromStartTime"))
                except (TypeError, ValueError):
                    off = None
                if ll:
                    f.add(ll[0], ll[1], st + int(off * 60000) if st is not None and off is not None else None)
    elif kind == "saved-places":
        for ft in j.get("features") or []:
            p = (ft or {}).get("properties") or {}
            coords = g(ft, "geometry", "coordinates") or [None, None]
            lon, lat = (coords + [None, None])[:2]
            if not lat and not lon:
                ll = latlng_url(p.get("google_maps_url")) or latlng_text(g(p, "location", "latLng"))
                if ll:
                    lat, lon = ll
            f.place(g(p, "location", "name") or p.get("Title") or p.get("name") or "", lat, lon)
    elif kind == "geojson":
        _geojson(j, f)


def _dig(d, ks):
    for k in ks:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _geojson(g, f, props=None):
    if not isinstance(g, dict):
        return
    t = g.get("type")
    if t == "FeatureCollection":
        for x in g.get("features") or []:
            _geojson(x, f)
        return
    if t == "Feature":
        _geojson(g.get("geometry"), f, g.get("properties") or {})
        return
    times = (props or {}).get("coordTimes") or (props or {}).get("times")
    c = g.get("coordinates") or []

    def pt(xy, i):
        if isinstance(xy, list) and len(xy) >= 2:
            f.add(xy[1], xy[0], to_ms(times[i]) if isinstance(times, list) and i < len(times) and not isinstance(times[i], list)
                  else to_ms((props or {}).get("time")))
    if t == "Point":
        if props and (props.get("name") or props.get("title")) and len(c) >= 2:
            f.place(props.get("name") or props.get("title"), c[1], c[0])
        else:
            pt(c, 0)
    elif t in ("MultiPoint", "LineString"):
        for i, x in enumerate(c):
            pt(x, i)
    elif t in ("MultiLineString", "Polygon"):
        for line in c:
            for i, x in enumerate(line or []):
                pt(x, i)
    elif t == "MultiPolygon":
        for poly in c:
            for line in poly or []:
                for i, x in enumerate(line or []):
                    pt(x, i)
    elif t == "GeometryCollection":
        for x in g.get("geometries") or []:
            _geojson(x, f, props)


def read_csv(text, f):
    import csv
    rows = [r for r in csv.reader(io.StringIO(text.lstrip("﻿"))) if any(c.strip() for c in r)]
    if not rows:
        return
    head = [h.strip().lower() for h in rows[0]]

    def col(*names):
        return next((i for i, h in enumerate(head) if h in names), -1)
    i_lat, i_lon = col("latitude", "lat", "y"), col("longitude", "lon", "lng", "long", "x")
    i_name, i_url = col("title", "name", "place", "ชื่อ"), col("url", "link", "google maps url", "google_maps_url")
    for r in rows[1:]:
        cell = lambda i: r[i] if 0 <= i < len(r) else ""  # noqa: E731
        lat, lon = cell(i_lat), cell(i_lon)
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            ll = latlng_url(cell(i_url))
            lat, lon = ll if ll else (None, None)
        f.place(cell(i_name), lat, lon)


FIT_EPOCH_MS = 631065600000


def read_fit(b, f):
    if len(b) < 14 or b[0] not in (12, 14) or b[8:12] != b".FIT":
        return False
    hsize = b[0]
    end = min(len(b), hsize + struct.unpack_from("<I", b, 4)[0])
    defs, p, last_ts = {}, hsize, None
    semi = 180 / 2 ** 31
    while p < end:
        h = b[p]
        p += 1
        if h & 0x80:
            local, off = (h >> 5) & 3, h & 31
            d = defs.get(local)
            if d is None:
                return False
            if last_ts is not None:
                ts = (last_ts & ~31) + off
                if off < (last_ts & 31):
                    ts += 32
                last_ts = ts
            r = _fit_data(b, d, p, end, semi)
            if r is None:
                break
            p, lat, lon, _ = r
            if d["global"] == 20 and lat is not None:
                f.add(lat, lon, FIT_EPOCH_MS + last_ts * 1000 if last_ts is not None else None)
            continue
        local = h & 15
        if h & 0x40:
            if p + 5 > end:
                break
            le = b[p + 1] == 0
            glob = struct.unpack_from("<H" if le else ">H", b, p + 2)[0]
            nf = b[p + 4]
            p += 5
            fields = []
            for _ in range(nf):
                if p + 3 > end:
                    return False
                fields.append((b[p], b[p + 1]))
                p += 3
            dev = 0
            if h & 0x20:
                nd = b[p]
                p += 1
                for _ in range(nd):
                    dev += b[p + 1]
                    p += 3
            defs[local] = {"le": le, "global": glob, "fields": fields, "dev": dev}
            continue
        d = defs.get(local)
        if d is None:
            return False
        r = _fit_data(b, d, p, end, semi)
        if r is None:
            break
        p, lat, lon, ts = r
        if ts is not None:
            last_ts = ts
        if d["global"] == 20 and lat is not None:
            t = ts if ts is not None else last_ts
            f.add(lat, lon, FIT_EPOCH_MS + t * 1000 if t is not None else None)
    return True


def _fit_data(b, d, at, end, semi):
    lat = lon = ts = None
    e = "<" if d["le"] else ">"
    for num, size in d["fields"]:
        if at + size > end:
            return None
        if d["global"] == 20 and num in (0, 1) and size == 4:
            v = struct.unpack_from(e + "i", b, at)[0]
            if v != 0x7FFFFFFF:
                if num == 0:
                    lat = v * semi
                else:
                    lon = v * semi
        elif num == 253 and size == 4:
            v = struct.unpack_from(e + "I", b, at)[0]
            if v != 0xFFFFFFFF:
                ts = v
        at += size
    at += d["dev"]
    if at > end:
        return None
    return at, lat if (lat is not None and lon is not None) else None, lon, ts


# ---------------------------------------------------------------- photos
def exif_block(b, kind):
    if kind == "heic":
        return heic_exif(b)
    if b[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 4 <= len(b) and b[i] == 0xFF:
        m = b[i + 1]
        if m in (0xDA, 0xD9):
            break
        ln = (b[i + 2] << 8) | b[i + 3]
        if ln < 2:
            break
        if m == 0xE1 and b[i + 4:i + 10] == b"Exif\x00\x00":
            return b[i + 10:i + 2 + ln]
        i += 2 + ln
    return None


def heic_exif(b):
    def boxes(frm, to):
        p = frm
        while p + 8 <= to:
            size = struct.unpack_from(">I", b, p)[0]
            head = 8
            if size == 1:
                size, head = struct.unpack_from(">Q", b, p + 8)[0], 16
            elif size == 0:
                size = to - p
            if size < head or p + size > to:
                return
            yield b[p + 4:p + 8].decode("latin-1"), p + head, p + size
            p += size
    meta = next(((s, e) for t, s, e in boxes(0, len(b)) if t == "meta"), None)
    if not meta:
        return None
    exif_id, iloc = None, None
    for t, s, e in boxes(meta[0] + 4, meta[1]):
        if t == "iinf":
            v = b[s]
            for t2, s2, e2 in boxes(s + 4 + (2 if v == 0 else 4), e):
                ev = b[s2]
                if t2 != "infe" or ev < 2:
                    continue
                iid = struct.unpack_from(">H" if ev == 2 else ">I", b, s2 + 4)[0]
                typ = b[s2 + 4 + (2 if ev == 2 else 4) + 2:s2 + 4 + (2 if ev == 2 else 4) + 6]
                if typ == b"Exif":
                    exif_id = iid
        elif t == "iloc":
            iloc = (s, e)
    if exif_id is None or not iloc:
        return None
    s = iloc[0]
    v = b[s]
    p = s + 4
    off_size, len_size, base_size = b[p] >> 4, b[p] & 15, b[p + 1] >> 4
    idx_size = b[p + 1] & 15 if v >= 1 else 0
    p += 2

    def un(at, n):
        return int.from_bytes(b[at:at + n], "big") if n else 0
    count = un(p, 2 if v < 2 else 4)
    p += 2 if v < 2 else 4
    for _ in range(count):
        iid = un(p, 2 if v < 2 else 4)
        p += 2 if v < 2 else 4
        method = 0
        if v >= 1:
            method = un(p, 2) & 15
            p += 2
        p += 2
        base = un(p, base_size)
        p += base_size
        n = un(p, 2)
        p += 2
        first = None
        for _ in range(n):
            p += idx_size
            o, ln = un(p, off_size), un(p + off_size, len_size)
            p += off_size + len_size
            first = first or (o, ln)
        if iid != exif_id:
            continue
        if method != 0 or not first:
            return None
        at = base + first[0]
        data = b[at:at + (first[1] or len(b) - at)]
        if len(data) < 4:
            return None
        skip = 4 + struct.unpack_from(">I", data, 0)[0]
        return data[skip:] if skip < len(data) else None
    return None


def read_exif(t):
    out = {"lat": None, "lon": None, "taken": None}
    if not t or len(t) < 8 or t[:2] not in (b"II", b"MM"):
        return out
    e = "<" if t[:2] == b"II" else ">"
    size = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8}

    def ifd(off):
        tags = {}
        if off < 8 or off + 2 > len(t):
            return tags
        n = struct.unpack_from(e + "H", t, off)[0]
        for k in range(min(n, 500)):
            en = off + 2 + k * 12
            if en + 12 > len(t):
                break
            tag, typ, cnt = struct.unpack_from(e + "HHI", t, en)
            nbytes = size.get(typ, 1) * cnt
            at = en + 8 if nbytes <= 4 else struct.unpack_from(e + "I", t, en + 8)[0]
            if at + nbytes <= len(t) and nbytes <= 65536:
                tags[tag] = (typ, cnt, at)
        return tags

    def rat(v):
        if not v or v[0] not in (5, 10):
            return None
        out_ = []
        for k in range(v[1]):
            n, d = struct.unpack_from(e + "II", t, v[2] + k * 8)
            out_.append(n / d if d else float("nan"))
        return out_
    try:
        i0 = ifd(struct.unpack_from(e + "I", t, 4)[0])
        ex = ifd(struct.unpack_from(e + "I", t, i0[0x8769][2])[0]) if 0x8769 in i0 else {}
        w = ex.get(0x9003) or i0.get(0x0132)
        if w and w[0] == 2:
            s = t[w[2]:w[2] + w[1]].split(b"\x00")[0].decode("ascii", "replace")
            m = re.match(r"(\d{4}):(\d\d):(\d\d) (\d\d):(\d\d):(\d\d)", s)
            if m and m.group(1) != "0000":
                out["taken"] = "%s-%s-%s %s:%s:%s" % m.groups()
        if 0x8825 in i0:
            g = ifd(struct.unpack_from(e + "I", t, i0[0x8825][2])[0])
            la, lo = rat(g.get(2)), rat(g.get(4))
            if la and lo and len(la) >= 3 and len(lo) >= 3:
                lat, lon = la[0] + la[1] / 60 + la[2] / 3600, lo[0] + lo[1] / 60 + lo[2] / 3600
                if g.get(1) and t[g[1][2]:g[1][2] + 1] == b"S":
                    lat = -lat
                if g.get(3) and t[g[3][2]:g[3][2] + 1] == b"W":
                    lon = -lon
                if math.isfinite(lat) and math.isfinite(lon) and not (lat == 0 and lon == 0) and abs(lat) <= 90 and abs(lon) <= 180:
                    out["lat"], out["lon"] = round(lat, 6), round(lon, 6)
    except (struct.error, KeyError, IndexError):
        pass
    return out


# ---------------------------------------------------------------- one file
def sniff(b):
    if b[:4] == b"PK\x03\x04":
        return "zip"
    if b[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if len(b) > 12 and b[4:8] == b"ftyp" and b[8:12] in (b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"):
        return "heic"
    if len(b) >= 12 and b[0] in (12, 14) and b[8:12] == b".FIT":
        return "fit"
    return "text"


def read_file(b, f, depth=0):
    """Fill `f` from one file's bytes. Returns a kind, or 'refused:<why>'."""
    kind = sniff(b)
    if kind == "fit":
        return "fit" if read_fit(b, f) else "refused:fit"
    if kind == "zip":
        if depth:
            return "refused:zip-inside-zip"
        try:
            z = zipfile.ZipFile(io.BytesIO(b))
        except zipfile.BadZipFile:
            return "refused:zip"
        infos = [i for i in z.infolist() if not i.is_dir()]
        if len(infos) > ZIP_MAX_ENTRIES or sum(i.file_size for i in infos) > ZIP_MAX_DECLARED:
            return "refused:zip-too-big-inside"
        for i in infos:
            if MEDIA.search(i.filename):
                return "refused:zip-has-pictures"
            if i.compress_size and i.file_size / i.compress_size > ZIP_MAX_RATIO and i.file_size > 1024 * 1024:
                return "refused:zip-bomb-ratio"
        for i in infos:
            if not DATA_IN_ZIP.search(i.filename):
                continue
            with z.open(i) as fh:
                data = fh.read(min(i.file_size, READ_MAX) + 1)
            if len(data) > i.file_size:
                return "refused:zip-size-lie"
            got = read_file(data, f, depth + 1)
            if got.startswith("refused:zip") or got in ("refused:markup-file", "refused:xml-doctype"):
                return got
        return "zip"
    if kind in ("jpeg", "heic"):
        return kind
    text = b.decode("utf-8", "replace").lstrip("﻿")
    head = text.lstrip()[:2048].lower()
    if re.search(r"<svg[\s>]|<html[\s>]|<!doctype\s+html|<script[\s>]|<body[\s>]|<iframe[\s>]", head):
        return "refused:markup-file"
    s = text.lstrip()
    if s.startswith("<"):
        if re.search(r"<!doctype|<!entity", head):
            return "refused:xml-doctype"
        if re.search(r"<(\w+:)?gpx[\s>]", head):
            read_gpx(text, f)
            return "gpx"
        if re.search(r"<(\w+:)?kml[\s>]", head):
            read_kml(text, f)
            return "kml"
        return "refused:format"
    if s.startswith("{") or s.startswith("["):
        try:
            j = json.loads(s)
        except ValueError:
            return "refused:json-broken"
        k = json_kind(j)
        if not k:
            return "refused:json-unknown"
        read_json(k, j, f)
        return k
    read_csv(text, f)
    return "csv"


# ---------------------------------------------------------------- home and blur
def is_night(t, t_end=None):
    if t is None:
        return False
    h = datetime.fromtimestamp(t / 1000 + TZ, tz=timezone.utc).hour
    if h >= NIGHT_FROM or h < NIGHT_TO:
        return True
    if t_end is not None and t_end > t:
        d = datetime.fromtimestamp(t / 1000 + TZ, tz=timezone.utc)
        two = datetime(d.year, d.month, d.day, 2, tzinfo=timezone.utc).timestamp() * 1000 - TZ * 1000
        if h >= 2:
            two += 86400000
        return two <= t_end
    return False


def night_spot(points):
    """The mean of the points in the busiest night cell, or None."""
    cells = {}
    for lat, lon, t, t_end in points:
        if is_night(t, t_end):
            cells.setdefault((round(lat / CELL), round(lon / CELL)), []).append((lat, lon))
    if not cells:
        return None
    best = max(cells.values(), key=len)
    if len(best) < NIGHT_MIN:
        return None
    return (sum(p[0] for p in best) / len(best), sum(p[1] for p in best) / len(best))


def metres(a_lat, a_lon, b_lat, b_lon):
    r = math.pi / 180
    d = (math.sin((b_lat - a_lat) * r / 2) ** 2
         + math.cos(a_lat * r) * math.cos(b_lat * r) * math.sin((b_lon - a_lon) * r / 2) ** 2)
    return 6371000 * 2 * math.asin(math.sqrt(d))


def blur_circle(home, radius_m, gift_id):
    """(centre_lat, centre_lon, radius_m): shifted off home by up to a third
    of the radius, in a direction and distance fixed by the gift id, and
    widened by the shift so home stays at least `radius_m` inside."""
    h = hashlib.sha256(("bequeath-blur|" + gift_id).encode()).digest()
    ang = int.from_bytes(h[:4], "big") / 2 ** 32 * 2 * math.pi
    dist = int.from_bytes(h[4:8], "big") / 2 ** 32 * radius_m / 3
    dlat = dist * math.cos(ang) / 111320.0
    dlon = dist * math.sin(ang) / (111320.0 * math.cos(math.radians(home[0])))
    return (home[0] + dlat, home[1] + dlon, radius_m + dist)


def outside(circle, lat, lon):
    return circle is None or metres(circle[0], circle[1], lat, lon) > circle[2]


# ---------------------------------------------------------------- one gift
def usable(m):
    return m.get("state") in ("open", "released") and m.get("review") in ("ok", "reviewed")


def curated_record(m, found, cut, home_not_found, pulled_at):
    c = m["card"]
    ch = c["choices"]
    return {
        "gift_id": m["gift_id"],
        "card": {"id": c["id"], "version": c["version"], "sha": c["sha"], "created_at": c["created_at"]},
        "state": m["state"],
        "uses": c["uses"],
        "licence": ch.get("licence"),
        "credit": None if ch.get("credit") == "none" else ch.get("credit_name"),
        "blur_m": ch.get("blur_m"),
        "home_not_found": home_not_found,
        "counts": {"points": len(found.points), "places": sum(1 for p in found.places if p["lat"] is not None),
                   "photos": len(found.photos), "cut_near_home": cut},
        "data": "cache/gifts/%s/points.json" % m["gift_id"],
        "pulled_at": pulled_at,
    }


def process(m, fetch, root=ROOT, dry=False, log=print):
    """Read one usable gift through `fetch(key) -> bytes`, blur it, write it."""
    gid = m["gift_id"]
    if not re.fullmatch(r"g_[a-z0-9]{6,20}", gid):
        log("  skip  bad gift id %r" % gid[:40])
        return None
    ch = m["card"]["choices"]
    found = Found()
    photo_files = []
    for fi in m.get("files") or []:
        b = fetch(fi["key"])
        if b is None:
            log("  miss  %s %s" % (gid, fi["key"]))
            continue
        kind = read_file(b, found)
        if kind.startswith("refused"):
            log("  skip  %s %s (%s)" % (gid, fi["name"], kind))
            continue
        if kind in ("jpeg", "heic"):
            ex = read_exif(exif_block(b, kind))
            name = "%s-%s" % (fi["id"], re.sub(r"[^\w.-]+", "_", fi["name"])[:60])
            found.photos.append({"file": name, "lat": ex["lat"], "lon": ex["lon"], "taken": ex["taken"], "people": bool(fi.get("people"))})
            photo_files.append((name, b))
            if ex["lat"] is not None:
                found.add(ex["lat"], ex["lon"])

    blur = int(ch.get("blur_m") or 0)
    circle, home_not_found = None, False
    if blur > 0:
        home = None
        if ch.get("home") == "marked" and m.get("home"):
            home = (m["home"]["lat"], m["home"]["lon"])
        elif ch.get("home") == "found":
            home = night_spot(found.points)
        if home is None:
            home_not_found = True
        else:
            circle = blur_circle(home, blur, gid)

    cut = 0
    if home_not_found:
        cut = len(found.points) + len(found.places)
        found.points, found.places = [], []
        for p in found.photos:
            p["lat"] = p["lon"] = None
            p["withheld"] = "home-not-found"
    elif circle:
        keep = [p for p in found.points if outside(circle, p[0], p[1])]
        cut += len(found.points) - len(keep)
        found.points = keep
        keep_pl = [p for p in found.places if p["lat"] is None or outside(circle, p["lat"], p["lon"])]
        cut += len(found.places) - len(keep_pl)
        found.places = keep_pl
        kept_photos = []
        for p in found.photos:
            if p["lat"] is not None and not outside(circle, p["lat"], p["lon"]):
                cut += 1
                photo_files = [x for x in photo_files if x[0] != p["file"]]
                continue
            kept_photos.append(p)
        found.photos = kept_photos

    rec = curated_record(m, found, cut, home_not_found, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    log("  gift  %s %s: %d points, %d places, %d photos, %d cut near home%s"
        % (gid, m["state"], rec["counts"]["points"], rec["counts"]["places"], rec["counts"]["photos"], cut,
           " — HOME NOT FOUND, points held back" if home_not_found else ""))
    if dry:
        return rec
    cache = Path(root) / "cache" / "gifts" / gid
    if cache.exists():
        shutil.rmtree(cache)
    (cache / "photos").mkdir(parents=True, exist_ok=True)
    for name, b in photo_files:
        (cache / "photos" / name).write_bytes(b)
    points = [[p[0], p[1], p[2]] for p in found.points]
    (cache / "points.json").write_text(json.dumps({"gift_id": gid, "card_sha": m["card"]["sha"], "points": points,
                                                   "places": found.places, "photos": found.photos},
                                                  ensure_ascii=False), encoding="utf-8")
    cur = Path(root) / "data" / "curated" / "gifts"
    cur.mkdir(parents=True, exist_ok=True)
    (cur / ("%s.json" % gid)).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rec


def remove(gid, root=ROOT, dry=False, log=print, why=""):
    cur = Path(root) / "data" / "curated" / "gifts" / ("%s.json" % gid)
    cache = Path(root) / "cache" / "gifts" / gid
    if cur.exists() or cache.exists():
        log("  out   %s (%s)" % (gid, why))
        if not dry:
            if cur.exists():
                cur.unlink()
            if cache.exists():
                shutil.rmtree(cache)


def pull(list_cards, fetch, root=ROOT, dry=False, log=print):
    """`list_cards()` -> manifests; `fetch(key)` -> bytes or None."""
    seen = 0
    for m in list_cards():
        seen += 1
        gid = m.get("gift_id", "")
        if not re.fullmatch(r"g_[a-z0-9]{6,20}", gid):
            continue
        if usable(m):
            process(m, fetch, root=root, dry=dry, log=log)
        else:
            remove(gid, root=root, dry=dry, log=log, why="%s/%s" % (m.get("state"), m.get("review")))
    return seen


# ---------------------------------------------------------------- sources
def folder_source(d):
    d = Path(d)

    def list_cards():
        for p in sorted((d / "cards").glob("*.json")):
            try:
                yield json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                continue

    def fetch(key):
        p = (d / key).resolve()
        if not str(p).startswith(str(d.resolve())) or not p.is_file():
            return None
        return p.read_bytes()
    return list_cards, fetch


def _rclone(*args, timeout=600):
    cfg = Path.home() / ".mot-dang-r2.json"
    c = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
    for k, env_k in (("accountId", "R2_ACCOUNT_ID"), ("accessKeyId", "R2_ACCESS_KEY_ID"),
                     ("secretAccessKey", "R2_SECRET_ACCESS_KEY")):
        c.setdefault(k, os.environ.get(env_k))
    if not all(c.get(k) for k in ("accountId", "accessKeyId", "secretAccessKey")):
        raise RuntimeError("no R2 credentials (~/.mot-dang-r2.json or R2_* in the environment)")
    env = dict(os.environ, **{
        "RCLONE_CONFIG_R2_TYPE": "s3", "RCLONE_CONFIG_R2_PROVIDER": "Cloudflare",
        "RCLONE_CONFIG_R2_ACCESS_KEY_ID": c["accessKeyId"],
        "RCLONE_CONFIG_R2_SECRET_ACCESS_KEY": c["secretAccessKey"],
        "RCLONE_CONFIG_R2_ENDPOINT": "https://%s.r2.cloudflarestorage.com" % c["accountId"],
        "RCLONE_CONFIG_R2_NO_CHECK_BUCKET": "true"})
    proc = subprocess.run(["rclone"] + list(args), env=env, capture_output=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip()[-300:] or "rclone failed")
    return proc.stdout


def r2_source():
    def list_cards():
        with tempfile.TemporaryDirectory() as tmp:
            _rclone("copy", "R2:%s/cards" % BUCKET, tmp)
            for p in sorted(Path(tmp).glob("*.json")):
                try:
                    yield json.loads(p.read_text(encoding="utf-8"))
                except ValueError:
                    continue

    def fetch(key):
        if not key.startswith("raw/") or ".." in key:
            return None
        try:
            return _rclone("cat", "R2:%s/%s" % (BUCKET, key))
        except RuntimeError:
            return None
    return list_cards, fetch


def main(argv):
    dry = "--dry-run" in argv
    if "--from" in argv:
        src = folder_source(argv[argv.index("--from") + 1])
    else:
        try:
            _rclone("lsjson", "R2:%s/cards" % BUCKET, timeout=60)
        except (RuntimeError, OSError) as exc:
            print("  could not read %s: %s — nothing on disk changed" % (BUCKET, exc))
            return 0
        src = r2_source()
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    n = pull(*src, root=root, dry=dry)
    print("bequeath: %d gift card(s) read%s" % (n, " (dry run)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
