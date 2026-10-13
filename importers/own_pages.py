#!/usr/bin/env python3
"""People's own pages, folded into the places they describe.

Nan, 2026-10-13: "information posted on minisites should be used everywhere it
can be to make all of motdang better."

A page made with the page maker lives at sites.motdang.net/<name> (Worker
project motdang-pages) and is published as a JSON feed:

    GET https://sites.motdang.net/feed.json   live pages only

This importer reads that feed and ties each page that carries a pin to the
place record it describes. Two outputs, one file, `data/curated/own_pages.json`:

    matched    a page that IS a record we hold: the record id, the page's
               address and tier, and the facts the page states (phone, LINE,
               web, hours as an OSM string, menu items with prices, photos
               with their credit). `lacks` names the ones the record did not
               hold when this ran.
    proposed   a page with a pin inside a province we cover and no record
               nearby: a record in the shape additions-*.json use, source type
               `own-site`, labelled "own page". It is a proposal. It joins the
               catalogue when its entry carries "admit": true, because a free
               page is made in a minute by anyone and the directory is not the
               place to find that out. `--admit NAME` sets it by hand
               ("admitted": "hand"). Nan, 2026-10-13 (C192): a page also joins
               on its own, "admitted": "auto", once it has been live AUTO_DAYS
               days and the feed says it has had no reports; a report, or a
               feed with no `reports` count, takes that away on the next run.

`apply(final, prov)` is called by importers/import_all.py on the merged list,
before Overture, and writes the matched facts into the record. It never
overwrites: a value already on the record stays, and the page's value waits
in the file. Each fact it writes carries provenance (provenance.py) as
`own-site:sites.motdang.net`, stated, with the day the feed was read, and the
record gains one `sources[]` line naming the page. Running it twice says the
same thing, because the facts are reapplied from the file each import.

IDENTITY IS NAME AND PROXIMITY, as with Overture (importers/import_overture.py):
within MATCH_M of the record's pin, and the names agree - the same words once
the generic ones (ร้าน, cafe, coffee) are set aside, one inside the other, or
the same consonant skeleton read in either script (build_wats.skeleton, the
test harvest_commons.names_agree uses for a photograph). A page with no pin is
never matched; a pin outside the covered provinces is never proposed.

    python3 importers/own_pages.py                      # report only
    python3 importers/own_pages.py --write              # data/curated/own_pages.json
    python3 importers/own_pages.py --fixture tests/fixtures/own_pages_feed.json
    python3 importers/own_pages.py --admit example-new-shop --write

The standing walk runs `--write` each pass, so a page that turns seven days old joins on the
next pass (importers/standing_walk.sh).

The feed is fetched with a short timeout; the last good copy is kept at
cache/own_pages/feed.json and is what a failed fetch falls back to. With no
feed at all the file on disk is left as it was.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

FEED_URL = "https://sites.motdang.net/feed.json"
PAGES_HOST = "https://sites.motdang.net/"
CACHE = ROOT / "cache" / "own_pages" / "feed.json"
OUT = ROOT / "data" / "curated" / "own_pages.json"
CANON = ROOT / "data" / "canonical"

AUTO_DAYS = 7         # a proposal joins on its own after this many live days with no reports (C192)
MATCH_M = 80          # a pin the owner placed and a pin a mapper placed agree to this
MIN_CORE = 3          # a name has to be this long once its generic words are gone
UA = "motdang-own-pages/1 (+https://motdang.net)"
SOURCE_TYPE = "own-site"
SOURCE_VIA = "sites.motdang.net"
SOURCE_KEY = f"{SOURCE_TYPE}:{SOURCE_VIA}"     # provenance.source_key() of the source below

# What kind of page becomes what kind of record. A person's page, an event and
# a group are not places and are never proposed as one (they are still found by
# the search, and a person's page matches nothing).
KIND_CAT = {"food": "food", "shop": "shopping", "service": "business"}

_THAI = re.compile(r"[฀-๿]")
# Words that name a kind of place, not a place.
_GENERIC = re.compile(
    r"ร้านอาหาร|ร้านกาแฟ|ร้าน|คาเฟ่|เชียงใหม่|"
    r"\b(?:cafe|coffee|restaurant|shop|store|house|home|the|chiang|mai)\b", re.I)


# ------------------------------------------------------------------ the feed

def _pages_of(doc) -> list:
    """The feed's pages that can be trusted to be what they say: a dict with a
    name, an https address on the pages host, and a title. The feed is data,
    and an address that points anywhere else is dropped here rather than
    printed on a place page."""
    out = []
    for p in (doc or {}).get("pages") or []:
        if not isinstance(p, dict):
            continue
        url, name, title = p.get("url"), p.get("name"), p.get("title")
        if not (isinstance(url, str) and url.startswith(PAGES_HOST) and name and title):
            continue
        out.append(p)
    return out


def fetch_feed(cache=CACHE, fixture=None, url=FEED_URL, timeout=20, offline=False):
    """(doc, via) with via one of fixture / live / cache / none.

    A good live answer is written to `cache`. A failed fetch reads it back, and
    a missing one answers (None, "none"): the caller keeps whatever it had."""
    cache = Path(cache)
    if fixture:
        return json.loads(Path(fixture).read_text(encoding="utf-8")), "fixture"
    if not offline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status == 200:
                    doc = json.loads(r.read(20_000_000).decode("utf-8"))
                    if isinstance(doc, dict) and isinstance(doc.get("pages"), list):
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        tmp = cache.with_suffix(".tmp")
                        tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
                        tmp.replace(cache)
                        return doc, "live"
        except Exception:  # noqa: BLE001 - any failure is the cached copy's turn
            pass
    try:
        doc = json.loads(cache.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and isinstance(doc.get("pages"), list):
            return doc, "cache"
    except (OSError, ValueError):
        pass
    return None, "none"


# --------------------------------------------------------------- page facts

_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def _hhmm(s) -> str:
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", str(s or ""))
    return "%02d:%s" % (int(m.group(1)), m.group(2)) if m else ""


def hours_string(h) -> str:
    """The page's week as an OSM opening_hours string ('Mo-Fr 08:00-17:00; Sa
    09:00-14:00,16:00-19:00'), which is what a record's `hours` holds and what
    importers/build_open_lamps.py reads. '' when the page lists none, when it is
    switched off, or when its clock is not Thailand's: a record's hours are
    read in Chiang Mai time."""
    if not isinstance(h, dict) or not h.get("on"):
        return ""
    if h.get("always"):
        return "Mo-Su 00:00-24:00"
    if not _clock_ok(h):
        return ""
    week = h.get("week") or []
    per_day = []
    for i in range(7):
        spans = []
        for s in (week[i] if i < len(week) and week[i] else []):
            if not (isinstance(s, (list, tuple)) and len(s) == 2):
                continue
            a, b = _hhmm(s[0]), _hhmm(s[1])
            if not (a and b):
                continue
            if b == "00:00" and a != "00:00":
                b = "24:00"
            spans.append(f"{a}-{b}")
        per_day.append(",".join(spans))
    out, i = [], 0
    while i < 7:
        if not per_day[i]:
            i += 1
            continue
        j = i
        while j + 1 < 7 and per_day[j + 1] == per_day[i]:
            j += 1
        days = _DAYS[i] if i == j else f"{_DAYS[i]}-{_DAYS[j]}"
        out.append(f"{days} {per_day[i]}")
        i = j + 1
    return "; ".join(out)


def _clock_ok(h) -> bool:
    return (h.get("tz") or "Asia/Bangkok") in ("Asia/Bangkok", "Asia/Ho_Chi_Minh", "Asia/Jakarta")


def sched_of(h):
    """The page's hours as minute-of-week intervals (Monday 00:00 is minute 0,
    the shape fleetsearch's `scheds` table holds), or None when the page lists
    none. A span that ends at or before it starts runs past midnight."""
    if not isinstance(h, dict) or not h.get("on") or not _clock_ok(h):
        return None
    if h.get("always"):
        return [[0, 7 * 1440]]
    out = []
    for i, day in enumerate((h.get("week") or [])[:7]):
        for s in day or []:
            if not (isinstance(s, (list, tuple)) and len(s) == 2):
                continue
            a, b = _hhmm(s[0]), _hhmm(s[1])
            if not (a and b):
                continue
            ma = int(a[:2]) * 60 + int(a[3:])
            mb = int(b[:2]) * 60 + int(b[3:])
            if mb <= ma:
                mb += 1440
            out.append([i * 1440 + ma, i * 1440 + mb])
    return out or None


def _s(v, cap=400) -> str:
    return unicodedata.normalize("NFC", str(v or "")).strip()[:cap]


def facts_of(p: dict) -> dict:
    """What a page states, keyed the way the record keys it. Empty values are
    left out; nothing is guessed."""
    f = {}
    for k, cap in (("phone", 60), ("line", 200), ("web", 300), ("facebook", 300),
                   ("instagram", 200), ("addr", 300)):
        v = _s(p.get(k), cap)
        if v:
            f["address" if k == "addr" else k] = v
    hrs = hours_string(p.get("hours"))
    if hrs:
        f["hours"] = hrs
    items = []
    for it in (p.get("items") or [])[:60]:
        if isinstance(it, dict) and _s(it.get("n")):
            items.append({k: v for k, v in (("n", _s(it.get("n"), 120)), ("p", _s(it.get("p"), 30)),
                                            ("note", _s(it.get("note"), 160))) if v})
    if items:
        f["items"] = items
        f["currency"] = _s(p.get("currency"), 8) or "THB"
    photos = []
    for ph in (p.get("photos") or [])[:12]:
        if isinstance(ph, dict) and str(ph.get("url") or "").startswith("https://"):
            e = {"url": ph["url"]}
            if str(ph.get("small") or "").startswith("https://"):
                e["small"] = ph["small"]
            c = ph.get("credit")
            if isinstance(c, dict):
                e["credit"] = {k: _s(c.get(k), 300) for k in ("title", "by", "src", "license", "licenseUrl")
                               if _s(c.get(k), 300)}
            photos.append(e)
    if photos:
        f["photos"] = photos
    return f


# ----------------------------------------------------------------- matching

def _norm(s) -> str:
    s = unicodedata.normalize("NFC", str(s or "")).lower()
    return re.sub(r"[\s\-.()\[\],/'\"·•|_]+", "", s)


def _core(s) -> str:
    """A name with its generic words and spaces taken out."""
    return _norm(_GENERIC.sub(" ", unicodedata.normalize("NFC", str(s or "")).lower()))


def _skeleton(s) -> str:
    try:
        from build_wats import skeleton
    except Exception:  # noqa: BLE001 - the skeleton is a second opinion; its absence is no match
        return ""
    return skeleton(s)


def page_names(p: dict) -> list:
    """The page's title as the names it carries: the whole, and each half when
    it is written 'ไทย · English' or 'ไทย (English)'."""
    t = _s(p.get("title"), 200)
    parts = [t] + [x for x in re.split(r"\s[·|/–—-]\s|[()（）]", t) if x.strip()]
    seen, out = set(), []
    for x in parts:
        x = x.strip()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def names_agree(rec_names, page_names_) -> str:
    """'' when the names do not agree, else the way they do."""
    rec_names = [n for n in rec_names if n]
    pairs = [(_core(a), _core(b)) for a in rec_names for b in page_names_]
    pairs = [(a, b) for a, b in pairs if len(a) >= MIN_CORE and len(b) >= MIN_CORE]
    if any(a == b for a, b in pairs):
        return "same name"
    if any(len(min(a, b, key=len)) >= 4 and (a in b or b in a) for a, b in pairs):
        return "one name inside the other"
    sk_page = {k for k in (_skeleton(b) for b in page_names_) if len(k) >= 4}
    for a in rec_names:
        if len(_skeleton(a)) >= 4 and _skeleton(a) in sk_page:
            return "same name read in either script"
    return ""


def _metres(lat1, lng1, lat2, lng2) -> float:
    p = math.pi / 180
    return 6371000 * math.hypot((lng2 - lng1) * p * math.cos((lat1 + lat2) / 2 * p), (lat2 - lat1) * p)


def _cell(lat, lng):
    return int(lng / 0.002), int(lat / 0.002)


def _grid(records) -> dict:
    g = defaultdict(list)
    for r in records:
        if r.get("lat") is not None and r.get("lng") is not None:
            g[_cell(r["lat"], r["lng"])].append(r)
    return g


def match_page(p: dict, grid: dict):
    """(record, metres, how) for the nearest record this page IS, or None."""
    lat, lng = p.get("lat"), p.get("lng")
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return None
    names = page_names(p)
    gx, gy = _cell(lat, lng)
    best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for r in grid.get((gx + dx, gy + dy), ()):
                if (r.get("geoPrecision") or "exact") == "needs-pin":
                    continue
                d = _metres(lat, lng, r["lat"], r["lng"])
                if d > MATCH_M or (best is not None and d >= best[1]):
                    continue
                how = names_agree([r.get("name"), r.get("nameTh"), r.get("nameEn")], names)
                if how:
                    best = (r, d, how)
    return best


# ------------------------------------------------------------ province / pin

_PROV = None


def province_of(lat, lng) -> str:
    """The province key whose polygons hold this pin (data/admin_boundaries.json,
    the set derive.py reads), or ''. Only provinces data/coverage.json lists
    are answered."""
    global _PROV
    import derive
    if _PROV is None:
        cov = json.loads((ROOT / "data" / "coverage.json").read_text(encoding="utf-8"))
        _PROV = {p["key"] for p in cov["provinces"]}
    polys = derive._load_polys()
    for key, levels in polys.items():
        if key not in _PROV:
            continue
        for feat in levels.get("amphoe") or []:
            if derive._contains(feat, lat, lng):
                return key
    return ""


# ------------------------------------------------------------------ records

def _is_thai(s) -> bool:
    return bool(_THAI.search(s or ""))


def source_of(p: dict, seen: str) -> dict:
    return {"type": SOURCE_TYPE, "via": SOURCE_VIA, "ref": p["url"], "fetched": seen, "label": "own page"}


def proposal_of(p: dict, prov: str, seen: str) -> dict:
    """A record in the shape additions-*.json use, for a page no record holds."""
    kind = p.get("kind")
    title = _s(p.get("title"), 200)
    th = en = None
    for part in page_names(p)[1:] or [title]:
        if _is_thai(part) and not th:
            th = part
        elif not _is_thai(part) and not en:
            en = part
    if not th and not en:
        th = title if _is_thai(title) else None
        en = None if th else title
    f = facts_of(p)
    cat = KIND_CAT.get(kind, "business")
    attrs = {"pinVia": "own-page-pin", "ownPage": {"url": p["url"], "tier": p.get("tier") or "free", "seen": seen}}
    rec = {
        "id": f"{prov}-own-{re.sub(r'[^a-z0-9-]', '', str(p['name']).lower())[:60]}",
        "province": prov, "cat": [cat], "sub": [],
        "name": th or en, "nameTh": th, "nameEn": en,
        "lat": round(float(p["lat"]), 6), "lng": round(float(p["lng"]), 6),
        "geoPrecision": "exact",
        "address": f.get("address") or None, "phone": f.get("phone") or None,
        "website": None, "hours": f.get("hours") or "",
        "attrs": attrs, "featured": False, "landmark": False,
        "sources": [source_of(p, seen)], "confidence": "crawled", "updatedAt": seen,
    }
    return rec


# -------------------------------------------------------------------- build

def days_live(p: dict, seen: str):
    """Whole days from the page's first publish to the day the feed was read; None when unknown."""
    try:
        return (date.fromisoformat(seen[:10]) - datetime.fromisoformat(str(p.get("published")).replace("Z", "+00:00")).date()).days
    except (ValueError, TypeError):
        return None


def admitted_how(p: dict, seen: str, by_hand: set):
    """"hand", "auto" or None. Auto needs AUTO_DAYS live days and a feed that says reports == 0."""
    if p["name"] in by_hand:
        return "hand"
    n, reports = days_live(p, seen), p.get("reports")
    if n is not None and n >= AUTO_DAYS and isinstance(reports, int) and not isinstance(reports, bool) and reports == 0:
        return "auto"
    return None


def build(pages, records, seen, previous=None) -> dict:
    """The document for data/curated/own_pages.json. `records` are the held
    records (any province); `previous` is the file as it stood, so an
    "admit" flag survives a regeneration."""
    # only a hand admission is carried over; an auto one is worked out again from the feed each run
    admitted = {e.get("page") for e in (previous or {}).get("proposed", [])
                if e.get("admit") and e.get("admitted") in (None, "hand")}
    grid = _grid(records)
    by_id = {r["id"]: r for r in records}
    matched, proposed, unpinned, outside = [], [], [], []
    for p in sorted(pages, key=lambda x: x["name"]):
        has_pin = isinstance(p.get("lat"), (int, float)) and isinstance(p.get("lng"), (int, float))
        if not has_pin:
            unpinned.append(p["name"])
            continue
        hit = match_page(p, grid)
        facts = facts_of(p)
        if hit:
            rec, d, how = hit
            lacks = [k for k in facts if k not in ("currency",) and _lacks(rec, k)]
            matched.append({"place": rec["id"], "page": p["name"], "url": p["url"],
                            "tier": p.get("tier") or "free", "title": _s(p.get("title"), 200),
                            "metres": round(d), "how": how, "seen": seen,
                            "updated": _s(p.get("updated"), 20)[:10], "facts": facts, "lacks": lacks})
            continue
        if p.get("kind") not in KIND_CAT:
            outside.append(p["name"])
            continue
        prov = province_of(float(p["lat"]), float(p["lng"]))
        if not prov:
            outside.append(p["name"])
            continue
        how = admitted_how(p, seen, admitted)
        e = {"page": p["name"], "url": p["url"], "tier": p.get("tier") or "free", "province": prov,
             "admit": how is not None, "admitted": how, "days_live": days_live(p, seen),
             "reports": p.get("reports"), "record": proposal_of(p, prov, seen)}
        proposed.append(e)
    return {
        "_note": "importers/own_pages.py writes this from https://sites.motdang.net/feed.json. "
                 "matched: pages that are records we hold; apply() fills the gaps on those records, "
                 "never over a value they have. proposed: pages with a pin and no record, admitted "
                 "only where admit is true: by hand (importers/own_pages.py --admit NAME) or on its own after "
                 f"{AUTO_DAYS} live days with the feed's reports count at 0.",
        "generated": seen,
        "matched": matched, "proposed": proposed,
        "unpinned": unpinned, "not_proposed": outside,
    }


def _lacks(rec: dict, key: str) -> bool:
    """Did the record lack this fact, not counting a value this importer wrote
    itself on an earlier pass (attrs.ownPage.filled lists those)."""
    attrs = rec.get("attrs") or {}
    ours = key in ((attrs.get("ownPage") or {}).get("filled") or [])
    held = {
        "phone": bool(rec.get("phone")), "hours": bool(rec.get("hours")),
        "address": bool(rec.get("address")), "web": bool(rec.get("website")),
        "line": bool(attrs.get("lineId") or attrs.get("lineUrl")),
        "facebook": bool(attrs.get("facebook")), "instagram": bool(attrs.get("instagram")),
        "items": False, "photos": False,       # a record holds neither
    }.get(key, False)
    return ours or not held


def _line_attr(line: str):
    line = (line or "").strip()
    if line.startswith("http"):
        return "lineUrl", line
    return "lineId", line


def _load_doc():
    try:
        d = json.loads(OUT.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def apply(final, prov, doc=None):
    """Write the matched pages' facts into `final`, and return (filled, [new
    records]) the way import_overture.apply does. `doc` is the parsed
    own_pages.json (read from disk when None)."""
    import provenance as P
    import import_overture as O
    doc = doc if doc is not None else _load_doc()
    if not doc:
        return 0, []
    by_id = {r["id"]: r for r in final}
    filled = 0
    for m in doc.get("matched") or []:
        rec = by_id.get(m.get("place"))
        if rec is None:
            continue
        f, seen = m.get("facts") or {}, m.get("seen") or doc.get("generated") or ""
        src = {"type": SOURCE_TYPE, "via": SOURCE_VIA, "ref": m["url"], "fetched": seen, "label": "own page"}
        wrote = []
        attrs = rec.setdefault("attrs", {})
        if f.get("phone") and not rec.get("phone"):
            rec["phone"] = f["phone"]
            P.stamp(rec, "phone", SOURCE_KEY, P.STATED, seen)
            wrote.append("phone")
        if f.get("hours") and not rec.get("hours"):
            rec["hours"] = f["hours"]
            P.stamp(rec, "hours", SOURCE_KEY, P.STATED, seen)
            wrote.append("hours")
        if f.get("address") and not rec.get("address"):
            rec["address"] = f["address"]
            P.stamp(rec, "address", SOURCE_KEY, P.STATED, seen)
            wrote.append("address")
        site, extra = O._split_website(f.get("web"))
        if site and not rec.get("website"):
            rec["website"] = site
            P.stamp(rec, "website", SOURCE_KEY, P.STATED, seen)
            wrote.append("web")
        for k, v in (extra or {}).items():            # a "website" that is a Facebook page, a LINE link
            if v and not attrs.get(k):
                attrs[k] = v
                wrote.append({"lineUrl": "line"}.get(k, k))
        if f.get("line") and not (attrs.get("lineId") or attrs.get("lineUrl")):
            k, v = _line_attr(f["line"])
            attrs[k] = v
            wrote.append("line")
        for k in ("facebook", "instagram"):
            if f.get(k) and not attrs.get(k):
                attrs[k] = f[k]
                wrote.append(k)
        if f.get("items") and not attrs.get("ownMenu"):
            attrs["ownMenu"] = {"items": f["items"], "currency": f.get("currency") or "THB", "seen": seen}
            wrote.append("items")
        if f.get("photos") and not attrs.get("ownPhotos"):
            attrs["ownPhotos"] = f["photos"]
            wrote.append("photos")
        # The page itself: always carried, because the place page links to it.
        before = (attrs.get("ownPage") or {}).get("filled") or []
        attrs["ownPage"] = {"url": m["url"], "tier": m.get("tier") or "free", "seen": seen,
                            "filled": sorted(set(before) | set(wrote))}
        if not any(P.source_key(s) == SOURCE_KEY and s.get("ref") == m["url"] for s in rec.get("sources") or []):
            rec.setdefault("sources", []).append(src)
        if wrote:
            filled += 1
    new = []
    have = set(by_id)
    for e in doc.get("proposed") or []:
        if not e.get("admit") or e.get("province") != prov:
            continue
        rec = e.get("record") or {}
        if rec.get("id") and rec["id"] not in have:
            rec = json.loads(json.dumps(rec))            # a copy: the doc stays as it was read
            seen = (rec.get("updatedAt") or "")
            for field in ("name", "nameTh", "nameEn", "phone", "address", "lat", "lng", "hours"):
                if rec.get(field):
                    P.stamp(rec, field, SOURCE_KEY, P.STATED, seen)
            new.append(rec)
            have.add(rec["id"])
    return filled, new


# ---------------------------------------------------------------------- run

def held_records() -> list:
    out = []
    for f in sorted(CANON.glob("*.json")):
        try:
            out += [r for r in json.loads(f.read_text(encoding="utf-8")) if isinstance(r, dict)]
        except (OSError, ValueError):
            print(f"own_pages: {f.name} did not parse; skipped")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="write data/curated/own_pages.json")
    ap.add_argument("--fixture", help="read this feed file instead of the live one")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--cache", default=str(CACHE))
    ap.add_argument("--records", help="records from this JSON file instead of data/canonical/")
    ap.add_argument("--offline", action="store_true", help="the cached feed only")
    ap.add_argument("--admit", action="append", default=[], help="admit this proposed page")
    a = ap.parse_args(argv)

    out = Path(a.out)
    try:
        previous = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = {}
    doc, via = fetch_feed(a.cache, a.fixture, offline=a.offline)
    if doc is None:
        print("own_pages: no feed (live fetch failed, no cached copy); left everything as it was")
        return 0
    pages = _pages_of(doc)
    seen = str(doc.get("generated") or "")[:10] or date.today().isoformat()
    if a.records:
        records = json.loads(Path(a.records).read_text(encoding="utf-8"))
    else:
        records = held_records()
    result = build(pages, records, seen, previous)
    for name in a.admit:
        hit = [e for e in result["proposed"] if e["page"] == name]
        if not hit:
            print(f"own_pages: --admit {name}: no such proposed page")
            continue
        hit[0]["admit"], hit[0]["admitted"] = True, "hand"
    print(f"own_pages: {len(pages)} page(s) from the {via} feed of {seen}: "
          f"{len(result['matched'])} matched, {len(result['proposed'])} proposed "
          f"({sum(1 for e in result['proposed'] if e['admit'])} admitted), "
          f"{len(result['unpinned'])} without a pin, {len(result['not_proposed'])} not proposed")
    for m in result["matched"]:
        print(f"  matched   {m['page']} -> {m['place']} ({m['metres']} m, {m['how']}); lacks {', '.join(m['lacks']) or 'nothing'}")
    for e in result["proposed"]:
        print(f"  proposed  {e['page']} -> {e['record']['id']} {'ADMITTED (' + e['admitted'] + ')' if e['admit'] else ''}")
    if a.write:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        tmp.replace(out)
        print(f"own_pages: wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
