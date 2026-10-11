"""pics_layer.py — NaN's own pictures, placed on the ground and linked to their pages.

One pool, three readers:
  * the front page's "pictures near you" strip (homebits.GEO_JS, NaN 2026-09-28: "the
    front page draws from all of them … you should be able to interact with the picture,
    get taken to the picture's place page")
  * the route strip on a place page (road_router), and the heading view (/ahead)
  * the camera-saw-it row on a place page (seen_row)

Reads data/curated/own_pictures.json, data/curated/own_pictures_meta.json (exact time,
capture point, heading — importers/make_picture_meta.py), data/curated/field_seen.json
(importers/make_field_seen.py) and the Field site's data/paths.json. Writes
docs/data/pics/<cell>.json, 0.01° cells, fetched by the browser only once it has a
position, plus docs/data/pics/index.json naming the cells that exist.

A row: [lat, lng, thumb, href, th, en, date, hh:mm, heading or -1, slug, w, h]
Paths are root-relative: the pool is read from pages at every depth.
"""

import datetime
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUR = ROOT / "data" / "curated"
FIELD_PATHS = [ROOT.parent / "field" / "data" / "paths.json",
               ROOT / "assets" / "field" / "data" / "paths.json"]
CELL = 0.01
FRESH_DAYS = 365          # NaN 2026-09-28: keep the record, show it only under a year old

_PLACES = {}              # id -> record
_HREF = {}                # id -> "<prov>/p/<slug>"
_SEEN = None
_META = None
TH_MONTHS = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
             "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


_MARKETS = []             # (lat, lng, id) of market records, for a market picture with no place
_BYSIZE = {}              # file size -> record id, from assets/photos/<id>.jpg


def bind(data_by_prov, place_href):
    _PLACES.clear()
    _MARKETS.clear()
    for recs in data_by_prov.values():
        for r in recs:
            _PLACES[r["id"]] = r
            # a market, or a craft community of stalls and lanes (โหล่งฮิมคาว around Chamcha)
            if r.get("lat") is not None and ("market" in (r.get("cat") or [])
                                             or "community-tourism" in (r.get("sub") or [])):
                _MARKETS.append((float(r["lat"]), float(r["lng"]), r["id"]))
    _HREF.clear()
    _HREF.update(place_href or {})
    # A ride picture cut for a place page is a byte copy of that page's lead photo
    # (own_strip() dedupes the same way), so its size names the place.
    _BYSIZE.clear()
    ph = ROOT / "assets" / "photos"
    if ph.exists():
        for f in ph.iterdir():
            if f.stem in _HREF:
                _BYSIZE.setdefault(f.stat().st_size, f.stem)


def _m(a, b, c, d):
    x = math.radians(c - a)
    y = math.radians(d - b) * math.cos(math.radians((a + c) / 2))
    return 6371000 * math.hypot(x, y)


def _json(p, default):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return default


def meta():
    global _META
    if _META is None:
        m = _json(CUR / "own_pictures_meta.json", {})
        _META = m.get("pictures", m) if isinstance(m, dict) else {}
    return _META


def seen():
    global _SEEN
    if _SEEN is None:
        _SEEN = (_json(CUR / "field_seen.json", {}) or {}).get("seen") or {}
    return _SEEN


_FP = None


def field_paths():
    global _FP
    if _FP is None:
        _FP = {}
        for p in FIELD_PATHS:
            d = _json(p, None)
            if isinstance(d, dict):
                _FP = d
                break
    return _FP


def _name(r):
    th = (r.get("nameTh") or "").strip()
    en = (r.get("nameEn") or r.get("name") or "").strip()
    if th == en:
        en = ""
    return th, en


def href_of(p, fpaths=None):
    """Where a tap on the picture goes: the place it shows, else its Field page,
    else the map at the spot it was taken."""
    rid = place_of(p)
    if rid:
        return "/" + _HREF[rid] + ".html"
    fp = (fpaths if fpaths is not None else field_paths()).get(p["slug"])
    if fp:
        return "/field/" + fp.lstrip("/")
    la, lo = where_taken(p)
    return f"/map.html#18/{la:.5f}/{lo:.5f}"


def place_of(p):
    """The record a picture shows: its placeId, else the page whose lead photo it is,
    else — for a market or its goods — the market it was taken in (within 150 m)."""
    for rid in [p.get("placeId"), *(p.get("places") or [])]:
        if rid and rid in _HREF:
            return rid
    f = ROOT / "assets" / p.get("file", "")
    if f.is_file() and f.stat().st_size in _BYSIZE:
        return _BYSIZE[f.stat().st_size]
    if p.get("subject") in ("market", "merch") or "market" in (p.get("topic") or []) \
            or p["slug"].startswith("chamcha-"):
        la, lo = float(p["lat"]), float(p["lng"])
        best = min(((_m(la, lo, a, b), i) for a, b, i in _MARKETS if abs(a - la) < 0.002),
                   default=None)
        if best and best[0] <= 150 and best[1] in _HREF:
            return best[1]
    return None


def where_taken(p):
    m = meta().get(p["slug"]) or {}
    cap = m.get("cap")
    if cap and len(cap) == 2:
        return float(cap[0]), float(cap[1])
    return float(p["lat"]), float(p["lng"])


def thumb_of(slug):
    small = ROOT / "assets" / "band" / (slug + ".jpg")
    return ("/band/" if small.exists() else "/site/") + slug + ".jpg"


def rows():
    picks = _json(CUR / "own_pictures.json", {}).get("picks") or []
    fpaths = field_paths()
    out = []
    for p in picks:
        if not p.get("usable") or p.get("lat") is None or p.get("lng") is None:
            continue
        if not (ROOT / "assets" / p["file"]).exists():
            continue
        la, lo = where_taken(p)
        th, en = (p.get("description_th") or "").strip(), (p.get("description") or p.get("title") or "").strip()
        rid = place_of(p)
        if rid and rid in _PLACES and p.get("subject") not in ("market", "merch", "aesthetic"):
            nth, nen = _name(_PLACES[rid])
            th, en = nth or th, nen or en
        m = meta().get(p["slug"]) or {}
        taken = m.get("taken") or ""
        hm = taken[11:16] if len(taken) >= 16 else ""
        hd = m.get("heading")
        out.append([round(la, 6), round(lo, 6), thumb_of(p["slug"]), href_of(p, fpaths),
                    th[:80], en[:80], p.get("date") or "", hm,
                    round(hd) % 360 if isinstance(hd, (int, float)) else -1,
                    p["slug"], int(p.get("width") or 0), int(p.get("height") or 0)])
    return out


def cell_key(la, lo):
    return f"{math.floor(la / CELL)}_{math.floor(lo / CELL)}"


def emit(docs):
    d = Path(docs) / "data" / "pics"
    d.mkdir(parents=True, exist_ok=True)
    cells = {}
    for r in rows():
        cells.setdefault(cell_key(r[0], r[1]), []).append(r)
    for k, rs in cells.items():
        rs.sort(key=lambda r: (r[6], r[7]), reverse=True)
        (d / f"{k}.json").write_text(json.dumps(rs, ensure_ascii=False, separators=(",", ":")))
    (d / "index.json").write_text(json.dumps(
        {"cell": CELL, "row": ["lat", "lng", "thumb", "href", "th", "en", "date", "time",
                               "heading", "slug", "w", "h"],
         "cells": {k: len(v) for k, v in sorted(cells.items())}},
        separators=(",", ":")))
    n = sum(len(v) for v in cells.values())
    return f"  pictures: {n} placed in {len(cells)} cells, " \
           f"{sum(1 for v in cells.values() for r in v if not r[3].startswith('/map'))} linked to a page"


def _fmt(iso):
    d = datetime.date.fromisoformat(iso[:10])
    hm = iso[11:16] if len(iso) >= 16 else ""
    th = f"{d.day} {TH_MONTHS[d.month]} {d.year + 543}" + (f" {hm} น." if hm else "")
    en = d.strftime("%-d %b %Y") + (f", {hm}" if hm else "")
    return th, en


def seen_row(r, bi, esc, today=None):
    """<dt>/<dd> for a place the camera passed within the last year, else ""."""
    s = seen().get(r["id"])
    if not s or not s.get("last"):
        return ""
    today = today or datetime.date.today()
    try:
        age = (today - datetime.date.fromisoformat(s["last"][:10])).days
    except ValueError:
        return ""
    if age > FRESH_DAYS or age < 0:
        return ""
    th, en = _fmt(s["last"])
    sign = (s.get("sign") or "").strip()
    sg = (f' · {bi("ป้ายอ่านว่า", "sign read")} <q>{esc(sign)}</q>' if sign else "")
    return (f"<dt>{bi('กล้องเห็นล่าสุด', 'Camera last saw it')}</dt>"
            f"<dd>{bi(th, en)}{sg}</dd>")
