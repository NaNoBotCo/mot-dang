#!/usr/bin/env python3
"""🔎 Soft eyes — the fields the catalogue already holds and never says.

Nan, 2026-09-08: *"I think we can actually infer and derive additional fields
and tags than what our data sources originally gave us, just by looking at
everything we already have together, with soft eyes."*

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
Every pass here reads only what is already on the record and writes what that
material plainly says. No crawl, no source, no model, no guess dressed as a
fact. Where a derivation cannot be checked it is written as what the string
SAID rather than as what the place IS, under a different key, so the two are
never confused and a better gazetteer can promote it later.

WHY IT IS NOT tags_mine.py
--------------------------
`tags_mine` (WO-76) mints a tag per VALUE of a categorical field —
overtureCategory, cuisine, brand. That axis is done and this does not touch it.
What it cannot reach is what this reads: free text (an address, a name),
structure across records (a shared pin, a repeated name), the FORMAT of a value
(a phone prefix, a script), and two fields that disagree.

THE MEASUREMENTS THAT MADE IT WORTH BUILDING (2026-09-08, 88,161 records)
    22,108 addresses name a ตำบล — 19,405 of them carry no attrs.tambon
    17,295 name an อำเภอ        — 14,362 carry no attrs.amphoe
    10,773 carry a postcode      —  7,506 carry no attrs.postcode
  attrs.amphoe was on 3.7% of records and NOTHING in the repo derived it; it
  arrived only on records whose register happened to include it.

EVERY WRITE IS FIRST-WRITER-WINS AND CARRIES A RECEIPT
-----------------------------------------------------
A pass never overwrites a value that is already there — an importer's fact, a
curated correction and an owner's claim all outrank a derivation, and
`provenance.stamp` is first-writer-wins for the same reason. Each field written
here is stamped `how="derived"` against a source key naming the pass, so the
OSM give-back gate excludes all of it automatically: `giveable()` requires
`how == "stated"`, and a reading of our own is not somebody else's survey.

RUN IT
    python3 derive.py            # over data/canonical/*.json, in place
    python3 derive.py --dry      # count only, write nothing

It is also called from the tail of importers/import_all.py, so a fresh import
carries the same fields. Both paths are safe to repeat: every pass is
deterministic and idempotent.
"""
from __future__ import annotations

import datetime
import difflib
import json
import math
import os
import re
import sys
from pathlib import Path

import provenance

ROOT = Path(__file__).resolve().parent
CANON = ROOT / "data" / "canonical"
ADMIN = ROOT / "data" / "curated" / "admin_areas.json"
BUILD_LOCK = ROOT / "cache" / "build.lock"

TODAY = ""  # set by main(); an empty `at` is omitted by provenance.stamp


# --------------------------------------------------------------- the reading

# The province's own อำเภอเมือง, which an address almost never spells out: it
# says "อ.เมือง" and expects the reader to know which city they are standing in.
MUANG = {"cm": "เมืองเชียงใหม่", "cr": "เมืองเชียงราย"}

# Every marker that can end the run of Thai letters after another marker. A
# Thai address is written without spaces between a marker and its name and
# often without spaces between the parts either, so "อำเภอสารภีจังหวัดเชียงใหม่"
# has to stop at จังหวัด or the amphoe comes out as three words joined.
MARKERS = r"(?:ตำบล|ต\.|แขวง|อำเภอ|อ\.|เขต|จังหวัด|จ\.|ถนน|ถ\.|ซอย|ซ\.|หมู่|ม\.)"

# A marker's own initial left stranded at the end of a grab: "เมือง จ" is
# "อ.เมือง จ.เชียงใหม่" with the จ. abbreviation's dot missing.
_TRAILING_INITIAL = re.compile(r"\s+(จ|ต|ม|ถ|ซ|อ)$")


def normalise(s: str) -> str:
    """The Thai typing faults that make a correct name fail a match.

    เ+เ is typed instead of แ often enough to be worth one line — เเม่ริม for
    แม่ริม appeared on 13 records in two provinces. ํ+า is typed for ำ on 228
    records' roads — ราชดําเนิน read "Ratdanoen" and matched no street. The
    zero-width space arrives from copy-pasted register rows.
    """
    return s.replace("เเ", "แ").replace("ํา", "ำ").replace("​", "").strip()


def _grab(address: str, markers: str) -> str | None:
    """The Thai run that follows `markers`, cut at the next marker."""
    m = re.search(rf"(?:{markers})\s*([ก-๙]+(?:\s[ก-๙]+)?)", address)
    if not m:
        return None
    value = re.split(MARKERS, m.group(1).strip())[0].strip()
    value = _TRAILING_INITIAL.sub("", value).strip()
    return value or None


def resolve_amphoe(raw: str, prov: str, known: dict) -> tuple[str | None, str | None]:
    """Match a grabbed อำเภอ against the province's real ones, or refuse.

    The gazetteer is complete for this field — 25 amphoe in Chiang Mai, 18 in
    Chiang Rai, the real counts — so an unmatched grab is either a typo, a
    different province, or a bad parse, and in all three cases writing it would
    be worse than leaving the field empty. Returns the mode of the match so the
    weaker ones stay countable rather than invisible.
    """
    raw = normalise(raw)
    if raw in known:
        return raw, "exact"
    if raw.startswith("เมือง"):
        return MUANG[prov], "muang"
    flat = raw.replace(" ", "")
    for name in known:
        if flat == name or flat.startswith(name) or name.startswith(flat):
            return name, "prefix"
    near = difflib.get_close_matches(flat, list(known), n=1, cutoff=0.86)
    if near:
        return near[0], "near"
    return None, None


def metres(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r, rad = 6371000.0, math.radians
    return 2 * r * math.asin(math.sqrt(
        math.sin(rad(lat2 - lat1) / 2) ** 2
        + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(rad(lng2 - lng1) / 2) ** 2))


def parse_address(address: str) -> dict:
    """Everything a Thai address string says about where it is.

    Returns raw readings only — validation is the caller's, because what counts
    as a real ตำบล depends on a gazetteer this function does not hold.
    """
    if not address:
        return {}
    out = {}
    amphoe = _grab(address, r"อำเภอ|(?<![ก-๙])อ\.|เขต")
    if amphoe:
        out["amphoe"] = amphoe
    tambon = _grab(address, r"ตำบล|(?<![ก-๙])ต\.|แขวง")
    if tambon:
        out["tambon"] = normalise(tambon)
    road = _grab(address, r"ถนน|(?<![ก-๙])ถ\.")
    if road:
        out["road"] = normalise(road)

    # ซอย takes a number as often as a name, so it is grabbed separately.
    soi = re.search(r"(?:ซอย|(?<![ก-๙])ซ\.)\s*([ก-๙\w]+)", address)
    if soi:
        out["soi"] = re.split(MARKERS, normalise(soi.group(1)))[0].strip() or None
    moo = re.search(r"(?:หมู่ที่|หมู่|(?<![ก-๙])ม\.)\s*(\d{1,2})", address)
    if moo:
        out["moo"] = moo.group(1)

    # A Thai postcode is five digits; a house number can be five digits too, so
    # it only counts when it stands as its own word.
    post = re.search(r"(?<!\d)(\d{5})(?!\d)", address)
    if post and not re.search(rf"\d/{post.group(1)}|{post.group(1)}/", address):
        out["postcode"] = post.group(1)
    return {k: v for k, v in out.items() if v}


# ----------------------------------------------------------------- the pass

SRC = "derived:address-parse"


def note_source(record: dict) -> None:
    """Put the source on the record that its stamps are about to name.

    `provenance.stamp()` writes a KEY into the provenance table; nothing was
    writing the `sources[]` entry that key points at. 59,719 receipts named a
    source their own record did not carry, `class_of_key()` answered UNKNOWN
    for every one of them, and `validate()` reported each as a dropped source.

    Appended, never prepended: build.py reads `sources[0]` as the record's
    origin and its fetch date, and this is not that. Idempotent, so the pass
    can run twice.
    """
    for s in record.get("sources") or []:
        if provenance.source_key(s) == SRC:
            return
    record.setdefault("sources", []).append(
        {"type": "derived", "via": "address-parse", "fetched": TODAY})


def stamp(record: dict, field: str) -> None:
    """One door for both halves of a receipt, so neither can be forgotten."""
    note_source(record)
    provenance.stamp(record, field, SRC, provenance.DERIVED, TODAY)


def apply_address(records: list, prov: str, counts: dict | None = None) -> int:
    """Write what each record's own address says about where it stands.

    Two grades of answer, kept apart on purpose:

      attrs.amphoe        a name the province's gazetteer confirms is real
      attrs.tambonSaid    what the string said, where nothing can confirm it

    The gazetteer covers every อำเภอ and almost no ตำบล (15 of Chiang Mai's, 1
    of Chiang Rai's), so tambon cannot be validated the same way. Writing it
    into attrs.tambon anyway would put an unchecked reading in the same field
    as a register's fact. It goes to attrs.tambonSaid instead — no reader is
    misled, no work is lost, and the day the tambon gazetteer is filled the
    promotion is a one-line pass over this key.

    THE PIN IS A SECOND WITNESS. Where a record has a pin, the parsed amphoe is
    checked against that amphoe's boundary centre and radius from
    admin_areas.json. Agreement is not recorded — it is the expected case and a
    flag for it would be noise. DISAGREEMENT is recorded, on the record, as
    attrs.amphoeDisputed: either the pin is wrong or the address is, and the
    pair is worth more to whoever fixes it than either half alone.
    """
    areas = json.loads(ADMIN.read_text())["areas"].get(prov, {})
    known = areas.get("amphoe", {})
    known_tambon = set(areas.get("tambon", {}))
    # Every tambon the corpus already holds as a fact is a name we can confirm.
    known_tambon |= {(r.get("attrs") or {}).get("tambon")
                     for r in records if (r.get("attrs") or {}).get("tambon")}
    known_tambon.discard(None)

    c = counts if counts is not None else {}
    written = 0
    for r in records:
        address = r.get("address")
        if not address:
            continue
        said = parse_address(address)
        if not said:
            continue
        attrs = r.setdefault("attrs", {})

        if said.get("amphoe") and not attrs.get("amphoe"):
            name, mode = resolve_amphoe(said["amphoe"], prov, known)
            if name:
                attrs["amphoe"] = name
                stamp(r, "amphoe")
                c[f"amphoe/{mode}"] = c.get(f"amphoe/{mode}", 0) + 1
                written += 1
                if r.get("lat") and name in known:
                    lat, lng, radius = known[name]
                    if metres(lat, lng, r["lat"], r["lng"]) > radius:
                        attrs["amphoeDisputed"] = "the pin falls outside this อำเภอ"
                        c["amphoe/disputed by the pin"] = c.get("amphoe/disputed by the pin", 0) + 1
            else:
                c["amphoe/no such อำเภอ in this province"] = \
                    c.get("amphoe/no such อำเภอ in this province", 0) + 1

        if said.get("tambon") and not attrs.get("tambon"):
            t = said["tambon"]
            if t in known_tambon:
                attrs["tambon"] = t
                stamp(r, "tambon")
                c["tambon/confirmed"] = c.get("tambon/confirmed", 0) + 1
                written += 1
            elif not attrs.get("tambonSaid"):
                attrs["tambonSaid"] = t
                c["tambon/said, unconfirmed"] = c.get("tambon/said, unconfirmed", 0) + 1
                written += 1

        for field in ("postcode", "road", "soi", "moo"):
            if said.get(field) and not attrs.get(field):
                attrs[field] = said[field]
                if field in provenance.TRACKED:
                    stamp(r, field)
                c[field] = c.get(field, 0) + 1
                written += 1
    return written



# ------------------------------------------------------ where the pin stands

# THE PIN IS A THIRD WITNESS, AND FOR 66,519 RECORDS THE ONLY ONE. Nan,
# 2026-09-10: "records SHOULD include province name. That's a big gap … can some
# of these fields be intuited? Province name is a no-brainer on what should be
# a much longer list." and, on the source: tambon and amphoe from the pin, yes.
# OSM holds no tambon boundaries for either province (0 relations at
# admin_level 8 on 2026-09-10; the amphoe relations exist), so the polygons are
# OCHA's COD-AB set — Royal Thai Survey Department, CC BY-IGO (verified
# 2026-09-10 against the HDX record), already on this disk since 9/8 as
# data/admin_boundaries.json, simplified to ~53 m. A pin inside a polygon is
# written as that tambon and amphoe; a pin within 60 m of a boundary is left
# alone, because at 53 m simplification the line itself is that uncertain.
BOUNDARIES = ROOT / "data" / "admin_boundaries.json"
SRC_POLY = "derived:admin-polygon"
POLY_EDGE_M = 60.0
_POLYS = None
# The date the polygons were obtained, not the date this test last ran. Stamping
# TODAY here rewrote the admin-polygon provenance on ~89,000 place records every
# time the build crossed midnight, and every rewritten record was a fresh upload
# to R2 — 4.3 GiB and ~$4/month of class A operations to say the same thing in a
# different ink. COD-AB has not moved since it was imported; the stamp should
# not move either. importers/import_admin_boundaries.py writes `generated`.
_POLY_FETCHED = None


def poly_fetched():
    """ISO date the COD-AB polygons on this disk were made, or TODAY if unknown."""
    _load_polys()
    return _POLY_FETCHED or TODAY


def _load_polys():
    """{prov: {"amphoe": [feat…], "tambon": [feat…]}} with a bbox on each."""
    global _POLYS, _POLY_FETCHED
    if _POLYS is not None:
        return _POLYS
    _POLYS = {}
    if not BOUNDARIES.exists():
        return _POLYS
    doc = json.loads(BOUNDARIES.read_text())
    _POLY_FETCHED = str(doc.get("generated") or "")[:10] or None
    if not _POLY_FETCHED:
        _POLY_FETCHED = datetime.date.fromtimestamp(
            BOUNDARIES.stat().st_mtime).isoformat()
    for level, block in (doc.get("levels") or {}).items():
        feats = block.get("features") if isinstance(block, dict) else block   # a level = {count, byProvince, features…}
        for f in feats or []:
            if not isinstance(f, dict):
                continue
            pr = f.get("properties") or {}
            g = f.get("geometry") or {}
            polys = [g["coordinates"]] if g.get("type") == "Polygon" else (g.get("coordinates") or [])
            rings = [[(pt[1], pt[0]) for pt in ring] for poly in polys for ring in poly[:1]]   # outer rings, (lat, lng)
            holes = [[(pt[1], pt[0]) for pt in ring] for poly in polys for ring in poly[1:]]
            if not rings:
                continue
            lats = [la for ring in rings for la, _ in ring]
            lngs = [ln for ring in rings for _, ln in ring]
            _POLYS.setdefault(pr.get("province"), {}).setdefault(level, []).append({
                "name": normalise(pr.get("name") or ""), "nameEn": pr.get("nameEn") or "",
                "amphoe": normalise(pr.get("amphoe") or ""), "pcode": pr.get("pcode"),
                "bbox": (min(lats), min(lngs), max(lats), max(lngs)), "rings": rings, "holes": holes})
    return _POLYS


def _in_ring(lat, lng, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        la1, ln1 = ring[i]
        la2, ln2 = ring[j]
        if (la1 > lat) != (la2 > lat):
            x = (ln2 - ln1) * (lat - la1) / ((la2 - la1) or 1e-12) + ln1
            if lng < x:
                inside = not inside
        j = i
    return inside


def _edge_m(lat, lng, ring):
    """Metres from the point to the nearest vertex of the ring — a cheap floor
    on the distance to the boundary, enough to say "too close to call"."""
    best = 1e9
    coslat = math.cos(math.radians(lat))
    for la, ln in ring:
        d = math.hypot((la - lat) * 111320.0, (ln - lng) * 111320.0 * coslat)
        if d < best:
            best = d
    return best


def _contains(feat, lat, lng):
    b = feat["bbox"]
    if not (b[0] <= lat <= b[2] and b[1] <= lng <= b[3]):
        return False
    if any(_in_ring(lat, lng, h) for h in feat["holes"]):
        return False
    return any(_in_ring(lat, lng, r) for r in feat["rings"])


def _near_edge(feat, lat, lng):
    return any(_edge_m(lat, lng, r) < POLY_EDGE_M for r in feat["rings"])


def note_poly_source(record: dict) -> None:
    for s in record.get("sources") or []:
        if provenance.source_key(s) == SRC_POLY:
            return
    record.setdefault("sources", []).append(
        {"type": "derived", "via": "admin-polygon", "fetched": poly_fetched(),
         "ref": "COD-AB Thailand (OCHA / Royal Thai Survey Department), CC BY-IGO"})


def stamp_poly(record: dict, field: str) -> None:
    note_poly_source(record)
    provenance.stamp(record, field, SRC_POLY, provenance.DERIVED, poly_fetched())


def apply_admin_polygon(records: list, prov: str, counts: dict | None = None) -> int:
    """Write the อำเภอ and ตำบล a pinned record stands in, from the polygons.

    First-writer-wins, like every pass here: an importer's fact, a register's
    field or the address pass's reading stands, and the polygon only fills what
    is empty. Where the polygon and an existing value DISAGREE the pair is
    recorded (attrs.amphoeDisputed / attrs.tambonDisputed) — either the pin
    or the field is wrong, and both halves are worth more than either alone.
    A tambonSaid the polygon agrees with is promoted to tambon, receipt and all.
    """
    polys = _load_polys().get(prov) or {}
    amphoe_f = polys.get("amphoe") or []
    tambon_f = polys.get("tambon") or []
    if not amphoe_f:
        return 0
    by_amphoe: dict = {}
    for t in tambon_f:
        by_amphoe.setdefault(t["amphoe"], []).append(t)
    c = counts if counts is not None else {}
    written = 0
    for r in records:
        lat, lng = r.get("lat"), r.get("lng")
        if lat is None or lng is None or (r.get("geoPrecision") or "exact") == "needs-pin":
            continue
        a = next((f for f in amphoe_f if _contains(f, lat, lng)), None)
        if a is None:
            c["polygon/pin outside every อำเภอ"] = c.get("polygon/pin outside every อำเภอ", 0) + 1
            continue
        attrs = r.setdefault("attrs", {})
        if not attrs.get("amphoe"):
            if _near_edge(a, lat, lng):
                c["amphoe/too close to a boundary to call"] = c.get("amphoe/too close to a boundary to call", 0) + 1
            else:
                attrs["amphoe"] = a["name"]
                stamp_poly(r, "amphoe")
                c["amphoe/polygon"] = c.get("amphoe/polygon", 0) + 1
                written += 1
        elif normalise(attrs["amphoe"]) != a["name"] and not attrs.get("amphoeDisputed") and not _near_edge(a, lat, lng):
            attrs["amphoeDisputed"] = f"the pin falls inside อำเภอ{a['name']}"
            c["amphoe/field disagrees with the pin"] = c.get("amphoe/field disagrees with the pin", 0) + 1
        t = next((f for f in by_amphoe.get(a["name"], []) if _contains(f, lat, lng)), None)
        if t is None:
            continue
        if not attrs.get("tambon"):
            if _near_edge(t, lat, lng):
                c["tambon/too close to a boundary to call"] = c.get("tambon/too close to a boundary to call", 0) + 1
                continue
            attrs["tambon"] = t["name"]
            stamp_poly(r, "tambon")
            if normalise(attrs.get("tambonSaid") or "") == t["name"]:
                attrs.pop("tambonSaid", None)
                c["tambon/said, confirmed by the pin"] = c.get("tambon/said, confirmed by the pin", 0) + 1
            else:
                c["tambon/polygon"] = c.get("tambon/polygon", 0) + 1
            written += 1
        elif normalise(attrs["tambon"]) != t["name"] and not attrs.get("tambonDisputed") and not _near_edge(t, lat, lng):
            attrs["tambonDisputed"] = f"the pin falls inside ตำบล{t['name']}"
            c["tambon/field disagrees with the pin"] = c.get("tambon/field disagrees with the pin", 0) + 1
    return written


# -------------------------------------------------------------- by the water

# RIVERSIDE IS A FACT THE PIN IMPLIES (Nan, 2026-09-10, search item 2). The
# river lines are OpenStreetMap's (importers/harvest_rivers.py → cache/water/
# rivers.json, ODbL). A pin within RIVER_M of a line is written riverside with
# the river's name; nothing else is inferred — which bank, which view, are not
# ours to say from a line. First-writer-wins like every pass here.
RIVERS = ROOT / "cache" / "water" / "rivers.json"
SRC_RIVER = "derived:river-line"
RIVER_M = 150.0        # riverside: the median of the 232 places that say so themselves (147 m)
RIVER_NEAR_M = 400.0   # the river's name and the metres, kept as facts, up to here
_RIVER_GRID = None
_RIVER_CELL = 0.01   # ~1.1 km


def _river_grid():
    global _RIVER_GRID
    if _RIVER_GRID is not None:
        return _RIVER_GRID
    _RIVER_GRID = {}
    if not RIVERS.exists():
        return _RIVER_GRID
    doc = json.loads(RIVERS.read_text())
    for w in doc.get("ways") or []:
        pts = [tuple(p) for p in (w.get("points") or [])]
        name = normalise(w.get("name") or "")
        for a, b in zip(pts, pts[1:]):
            # every cell the segment's bbox touches gets the segment
            la0, la1 = sorted((a[0], b[0])); ln0, ln1 = sorted((a[1], b[1]))
            ci0, ci1 = int(la0 // _RIVER_CELL), int(la1 // _RIVER_CELL)
            cj0, cj1 = int(ln0 // _RIVER_CELL), int(ln1 // _RIVER_CELL)
            for ci in range(ci0, ci1 + 1):
                for cj in range(cj0, cj1 + 1):
                    _RIVER_GRID.setdefault((ci, cj), []).append((a, b, name))
    return _RIVER_GRID


def _seg_m(lat, lng, a, b):
    """Metres from a point to a segment, on a flat local map."""
    kx = math.cos(math.radians(lat))
    ax, ay = (a[1] - lng) * 111320.0 * kx, (a[0] - lat) * 111320.0
    bx, by = (b[1] - lng) * 111320.0 * kx, (b[0] - lat) * 111320.0
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(ax, ay)
    t = max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def nearest_river(lat, lng):
    """(metres, name) of the nearest river segment within ~1 km, or None."""
    grid = _river_grid()
    if not grid:
        return None
    ci, cj = int(lat // _RIVER_CELL), int(lng // _RIVER_CELL)
    best = None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for a, b, name in grid.get((ci + di, cj + dj), ()):
                d = _seg_m(lat, lng, a, b)
                if best is None or d < best[0]:
                    best = (d, name)
    return best


def note_river_source(record: dict) -> None:
    for s in record.get("sources") or []:
        if provenance.source_key(s) == SRC_RIVER:
            return
    record.setdefault("sources", []).append(
        {"type": "derived", "via": "river-line", "fetched": TODAY,
         "ref": "OpenStreetMap waterway=river lines (ODbL), importers/harvest_rivers.py"})


def apply_riverside(records: list, prov: str, counts: dict | None = None) -> int:
    """attrs.riverside = True and attrs.riverName for a pin within RIVER_M of a
    river line. Written only where absent; never removed by this pass."""
    if not _river_grid():
        return 0
    c = counts if counts is not None else {}
    written = 0
    for r in records:
        lat, lng = r.get("lat"), r.get("lng")
        if lat is None or lng is None or (r.get("geoPrecision") or "exact") == "needs-pin":
            continue
        attrs = r.setdefault("attrs", {})
        if attrs.get("riverside") is not None:
            continue
        hit = nearest_river(lat, lng)
        if not hit or hit[0] > RIVER_NEAR_M:
            continue
        # The metres and the name are facts about the pin, kept to 400 m so
        # "kok river" reaches what stands along it; riverside is the judgment,
        # and it is drawn at 150 m — the median of the places that call
        # themselves riverside (measured 2026-09-10 over 232 of them).
        if hit[1] and not attrs.get("riverName"):
            attrs["riverName"] = hit[1]
        if attrs.get("riverM") is None:
            attrs["riverM"] = int(round(hit[0]))
        if hit[0] <= RIVER_M:
            attrs["riverside"] = True
            note_river_source(r)
            provenance.stamp(r, "riverside", SRC_RIVER, provenance.DERIVED, TODAY)
            key = f"riverside/{hit[1] or 'unnamed'}"
            c[key] = c.get(key, 0) + 1
            written += 1
        else:
            c["river/named within 400 m, not riverside"] = c.get("river/named within 400 m, not riverside", 0) + 1
            written += 1
    return written


# ---------------------------------------------------- what the name is shaped like

# Honorifics a Thai shop name opens with. Recorded as WHAT THE NAME CARRIES and
# nothing more: "แม่" in front of a kitchen's name is a fact about the sign, not
# a claim about who owns it or cooks there, and the field is named so that no
# consumer can mistake one for the other.
HONORIFICS = ("แม่", "ป้า", "ลุง", "พี่", "น้า", "ยาย", "อา")

_THAI = re.compile(r"[ก-๙]")
_LATIN = re.compile(r"[A-Za-z]")
# A company form, which says a registered business rather than a stall.
_COMPANY = re.compile(r"หจก\.|บจก\.|บริษัท|ห\.จ\.ก\.|ห้างหุ้นส่วน")
# "สาขา X" — a branch, and the branch's own name. Everything after the word up
# to a bracket or the end, because a branch name is frequently a place name
# with spaces in it ("สาขา บิ๊กซี เชียงใหม่").
_BRANCH = re.compile(r"สาขา\s*([^()\[\]]{1,40})")


def apply_name_shape(records: list, prov: str, counts: dict | None = None) -> int:
    """What a name says about itself, in fields instead of prose.

    Four readings, all of them about the STRING and none about the business:

      attrs.nameScript    thai | latin | both — which alphabet the sign is in.
                          The axis the search-disease note keeps circling: a
                          shelf that is 97% Latin-named was built out of a map
                          rather than out of the city, and until now that could
                          only be measured in a one-off script.
      attrs.nameHonorific แม่ · ป้า · ลุง · พี่ · น้า, when the name opens with
                          one. 6,281 records do. It is a fact about the sign.
      attrs.branchName    what follows สาขา. 2,289 records name a branch and
                          the catalogue has been throwing that word away.
      attrs.companyForm   หจก./บจก./บริษัท, when the name carries one.
    """
    c = counts if counts is not None else {}
    written = 0
    for r in records:
        name = (r.get("name") or "").strip()
        if not name:
            continue
        attrs = r.setdefault("attrs", {})
        whole = " ".join(filter(None, (name, r.get("nameTh"), r.get("nameEn"))))

        if not attrs.get("nameScript"):
            th, la = bool(_THAI.search(whole)), bool(_LATIN.search(whole))
            script = "both" if th and la else "thai" if th else "latin" if la else None
            if script:
                attrs["nameScript"] = script
                c[f"nameScript/{script}"] = c.get(f"nameScript/{script}", 0) + 1
                written += 1

        if not attrs.get("nameHonorific"):
            for h in HONORIFICS:
                # Only in front, and only followed by more Thai — "แม่" inside
                # แม่ริม (a district) or แม่น้ำ (a river) is not an honorific.
                if name.startswith(h) and _THAI.match(name[len(h):len(h) + 1] or ""):
                    attrs["nameHonorific"] = h
                    c["nameHonorific"] = c.get("nameHonorific", 0) + 1
                    written += 1
                    break

        if not attrs.get("branchName"):
            m = _BRANCH.search(name)
            if m:
                branch = m.group(1).strip(" -–·,")
                if branch:
                    attrs["branchName"] = branch
                    c["branchName"] = c.get("branchName", 0) + 1
                    written += 1

        if not attrs.get("companyForm") and _COMPANY.search(name):
            attrs["companyForm"] = _COMPANY.search(name).group(0)
            c["companyForm"] = c.get("companyForm", 0) + 1
            written += 1
    return written


# --------------------------------------------------- what the contact is shaped like

def line_type(phone: str) -> str | None:
    """What KIND of line a Thai number is.

    A 053 landline is a business with a fixed address that has had it long
    enough to want one; an 02 number on a Chiang Mai record is a Bangkok head
    office, which is a different fact from a local shop and today looks exactly
    like one. Mobile says nothing either way — most of the corpus is mobile —
    but naming it keeps the field total.
    """
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("66"):
        digits = "0" + digits[2:]
    if not digits.startswith("0"):
        return None
    if digits.startswith("053"):
        return "landline-local"
    if digits.startswith("02"):
        return "landline-bangkok"
    if re.match(r"0[689]", digits):
        return "mobile"
    return "landline-other"


_RENTED = ("wixsite", "blogspot", "wordpress.com", "shopee.", "lazada.", "linktr.")


def apply_contact_shape(records: list, prov: str, counts: dict | None = None) -> int:
    """attrs.lineType and attrs.frontDoor — the format of a value, read.

    frontDoor is where a reader would actually land: a place whose only address
    on the web is a Facebook page is reachable differently from one with its own
    domain, and a rented page (a marketplace stall, a linktree) is a third
    thing. 59.8% of the corpus is facebook-only; nothing has been able to say so.
    """
    c = counts if counts is not None else {}
    written = 0
    for r in records:
        attrs = r.setdefault("attrs", {})
        if r.get("phone") and not attrs.get("lineType"):
            kind = line_type(r["phone"])
            if kind:
                attrs["lineType"] = kind
                c[f"lineType/{kind}"] = c.get(f"lineType/{kind}", 0) + 1
                written += 1
        if not attrs.get("frontDoor"):
            site = (r.get("website") or "").lower()
            door = None
            if site and "facebook." not in site:
                door = "rented" if any(h in site for h in _RENTED) else "own-site"
            elif site or attrs.get("facebook"):
                door = "facebook"
            if door:
                attrs["frontDoor"] = door
                c[f"frontDoor/{door}"] = c.get(f"frontDoor/{door}", 0) + 1
                written += 1
    return written


# ------------------------------------------------ what the records say about each other

def _chain_key(name: str) -> str:
    """A name with its branch clause removed, for grouping."""
    return re.sub(r"\s+", " ", re.sub(r"สาขา.*$", "", name or "")).strip().lower()


MIN_CHAIN = 3

# A name this repo generated is not a name a business chose. The parking
# locators (WO-67) write "ที่จอดรถ · ย่าน<area>" onto unnamed car parks and stamp
# the name `derived`, so 87 of them at 87 pins read exactly like a chain of 87
# branches. The provenance table already knows the difference; this asks it.
def _name_is_ours(record: dict) -> bool:
    return ((record.get("provenance") or {}).get("name") or {}).get("how") == "derived"


# A standard-issue government facility whose official name is the same in every
# tambon in the country. Thirty of them share a name and none of them is a
# branch of the other twenty-nine. Not caught by the lexicon test because it is
# an institution's title, not a trade word, so it is named here explicitly
# rather than reached for by a rule that would also swallow real chains.
STATE_TYPES = (
    "โรงพยาบาลส่งเสริมสุขภาพตำบล", "สถานีตำรวจภูธร", "ที่ว่าการอำเภอ",
    "สำนักงานเทศบาลตำบล", "องค์การบริหารส่วนตำบล", "โรงเรียนบ้าน",
    "การไฟฟ้าส่วนภูมิภาค", "สำนักงานสาธารณสุขอำเภอ",
)

_LEXICON = None


def _generic(label: str) -> bool:
    """True when the shared name is a trade, not a brand.

    "ซักผ้าหยอดเหรียญ" (coin laundry) stands at 50 pins and is not a chain of 50
    branches — it is fifty shops that describe themselves the same way, which is
    what a trade word is for. data/trade_lexicon.json is the list of words the
    corpus itself uses that way, so the test is a lookup rather than a judgement.
    """
    global _LEXICON
    if _LEXICON is None:
        path = ROOT / "data" / "trade_lexicon.json"
        _LEXICON = set(json.loads(path.read_text()).get("tags", {})) if path.exists() else set()
    flat = label.strip()
    if flat in _LEXICON:
        return True
    if any(flat.startswith(t) for t in STATE_TYPES):
        return True
    # A label that is nothing but a trade word plus a state prefix, e.g.
    # โรงพยาบาลส่งเสริมสุขภาพตำบล — the name of a KIND of clinic, one per tambon.
    return any(flat == w or (len(w) >= 8 and flat.startswith(w) and len(flat) - len(w) <= 2)
               for w in _LEXICON)


def apply_chains(records: list, prov: str, counts: dict | None = None) -> int:
    """A name repeated at three separate pins is a chain, and says so.

    attrs.brand is set on 2,385 records and 5,217 stand in a group of three or
    more that share a name — 2,832 records in a chain the catalogue does not
    know is a chain. Chain-versus-independent is a thing a reader wants to
    filter on and cannot ask for today.

    THE PINS HAVE TO BE DIFFERENT. Three records at one coordinate sharing a
    name are a duplicate, a food court, or one shop entered three times — never
    a chain — and counting them as one would turn the messiest corner of the
    catalogue into confident branding.
    """
    c = counts if counts is not None else {}
    groups: dict = {}
    for r in records:
        if _name_is_ours(r):
            continue
        key = _chain_key(r.get("name") or "")
        if len(key) < 3:
            continue
        groups.setdefault(key, []).append(r)

    written = 0
    for key, members in groups.items():
        pins = {(round(r["lat"], 4), round(r["lng"], 4)) for r in members if r.get("lat")}
        if len(pins) < MIN_CHAIN:
            continue
        # The name as it is most often written, rather than lowercased.
        label = max((r.get("name") or "" for r in members), key=len)
        label = re.sub(r"สาขา.*$", "", label).strip(" -–·,([{")
        if _generic(label):
            c["brand/a trade word, not a brand — refused"] = \
                c.get("brand/a trade word, not a brand — refused", 0) + 1
            continue
        for r in members:
            attrs = r.setdefault("attrs", {})
            if attrs.get("brand"):
                continue
            attrs["brand"] = label
            attrs["chainSize"] = len(pins)
            c["brand/from a repeated name"] = c.get("brand/from a repeated name", 0) + 1
            written += 1
    return written


# A place whose name says it CONTAINS other places. The matching rule matters
# more than the word list, and the first attempt got it wrong in a way worth
# recording: a bare substring search put วัดสันห้าง (a temple whose name merely
# contains ห้าง) and "UP 420 (Weed Station)" forward as hosts of 43 and 92
# tenants. Thai is written without spaces, so a substring is not a word.
#
# So: a Thai host word must OPEN the name — Thai names for these buildings lead
# with their type (ตลาด…, ห้าง…, โรงพยาบาล…, มหาวิทยาลัย…) — and a Latin one must
# stand as a whole word.
_HOST_TH = re.compile(
    r"^(?:ตลาด|ห้างสรรพสินค้า|เซ็นทรัล|เมญ่า|มาย่า|พรอมเมนาดา|โรงพยาบาล|"
    r"มหาวิทยาลัย|สนามบิน|ศูนย์การค้า|กาดสวนแก้ว|กาดหลวง)")
_HOST_EN = re.compile(
    r"\b(?:Central (?:Festival|Airport|Plaza)|Maya|Promenada|"
    r"Shopping Mall|Mall|Market|Hospital|University|Airport)\b", re.I)

# Above this, a shared coordinate is not a building. A geocoder that could not
# place a record often drops it on a district centre, and those piles reach the
# dozens — 92 records at one pin is an artefact of that, not a mall.
MAX_VENUE = 20


def _is_host(record: dict) -> bool:
    name = (record.get("name") or "").strip()
    return bool(_HOST_TH.match(name) or _HOST_EN.search(name))


def apply_venues(records: list, prov: str, counts: dict | None = None) -> int:
    """A shared pin is a venue, not a duplicate.

    926 pins hold three or more records. Where exactly ONE member of such a
    group names itself a market, mall, hospital, campus or station, the others
    stand inside it — and "inside Central Festival" is a fact the catalogue can
    state, plus a tenant list, which is a page type the site does not have.

    EXACTLY ONE, or nothing. Two hosts at one coordinate means the pin is a
    building cluster and picking between them would be a coin toss written as a
    fact. The refusal is counted so the size of that case stays visible.
    """
    c = counts if counts is not None else {}
    pins: dict = {}
    for r in records:
        if r.get("lat"):
            pins.setdefault((round(r["lat"], 5), round(r["lng"], 5)), []).append(r)

    written = 0
    for members in pins.values():
        if not 3 <= len(members) <= MAX_VENUE:
            if len(members) > MAX_VENUE:
                c["insideOf/too many at one pin to be a building"] = \
                    c.get("insideOf/too many at one pin to be a building", 0) + 1
            continue
        # A pile of approximate pins is a geocoder's shrug, not a tenancy.
        if any(r.get("geoPrecision") != "exact" for r in members):
            c["insideOf/a pin nobody stood on, refused"] = \
                c.get("insideOf/a pin nobody stood on, refused", 0) + 1
            continue
        hosts = [r for r in members if _is_host(r)]
        if len(hosts) != 1:
            if len(hosts) > 1:
                c["insideOf/two hosts at one pin, refused"] = \
                    c.get("insideOf/two hosts at one pin, refused", 0) + 1
            continue
        host = hosts[0]
        for r in members:
            if r is host:
                continue
            attrs = r.setdefault("attrs", {})
            if attrs.get("insideOf"):
                continue
            attrs["insideOf"] = host.get("name")
            attrs["insideOfId"] = host.get("id")
            c["insideOf"] = c.get("insideOf", 0) + 1
            written += 1
    return written


# ------------------------------------------------------- two fields that disagree

def apply_category_agreement(records: list, prov: str, counts: dict | None = None) -> int:
    """Whether our sub-shelf and Overture's own word are saying the same thing.

    44,440 records carry both. They agree on 8,166 and differ on 36,274. A
    difference is not an error — the two vocabularies are not the same
    vocabulary — but it is the cheapest quality signal in the corpus and it has
    never been written down. `agree` means one word contains the other after
    the separators are stripped; anything else is `differ`, and the field is
    named `catAgreement` rather than `catCorrect` because that is all it knows.
    """
    c = counts if counts is not None else {}
    written = 0
    flat = lambda s: re.sub(r"[-_\s]", "", (s or "").lower())
    for r in records:
        attrs = r.setdefault("attrs", {})
        other = attrs.get("overtureCategory")
        subs = r.get("sub") or []
        if not other or not subs or attrs.get("catAgreement"):
            continue
        ours = flat("".join(subs))
        theirs = flat(other)
        verdict = "agree" if theirs and (theirs in ours or ours in theirs) else "differ"
        attrs["catAgreement"] = verdict
        c[f"catAgreement/{verdict}"] = c.get(f"catAgreement/{verdict}", 0) + 1
        written += 1
    return written


# ------------------------------------------------------------------- runner

PASSES = [
    ("address", apply_address),
    ("admin polygon", apply_admin_polygon),
    ("riverside", apply_riverside),
    ("name shape", apply_name_shape),
    ("contact shape", apply_contact_shape),
    ("chains", apply_chains),
    ("venues", apply_venues),
    ("category agreement", apply_category_agreement),
]


def a_build_is_running() -> int | None:
    """The pid of a live build.py, or None.

    THIS PASS WRITES WHAT A BUILD READS. build.py takes cache/build.lock to stop
    two builds fighting over docs/; the same lock answers a second question it
    was not written for — whether it is safe to rewrite data/canonical/ right
    now. A build that reads the catalogue half-way through a rewrite produces a
    site whose numbers are from two different catalogues and whose failure is a
    puzzle three days later, so the same file is honoured here rather than a
    second mechanism invented beside it.

    A lock whose process is gone is stale and ignored — the build's own rule.
    """
    if not BUILD_LOCK.exists():
        return None
    try:
        pid = int(BUILD_LOCK.read_text().split()[0])
        os.kill(pid, 0)
    except (ValueError, IndexError, OSError):
        return None
    return pid


def main() -> None:
    global TODAY
    import datetime
    TODAY = datetime.date.today().isoformat()
    dry = "--dry" in sys.argv

    held = a_build_is_running()
    if held and not dry:
        raise SystemExit(
            f"\n  NOT WRITING: build.py (pid {held}) is running and reads the same\n"
            f"  catalogue this would rewrite. Wait for it, then run again — or use\n"
            f"  --dry, which only counts.\n")

    # Checking was not enough: a build could start in the gap between the check
    # and the write, which is the exact race build.py's own lock exists to end.
    # So the lock is HELD for the duration, in build.py's format, and released
    # in a finally — a crash here must not leave a lock nobody can explain.
    taken = False
    if not dry:
        BUILD_LOCK.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(BUILD_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, f"{os.getpid()}\n{__import__('datetime').datetime.now().isoformat(timespec='seconds')}\n".encode())
            os.close(fd)
            taken = True
        except FileExistsError:
            raise SystemExit("\n  NOT WRITING: a build took the lock a moment ago.\n")
    try:
        _run(dry)
    finally:
        if taken:
            BUILD_LOCK.unlink(missing_ok=True)


def _run(dry: bool) -> None:

    for prov in ("cm", "cr"):
        path = CANON / f"{prov}.json"
        records = json.loads(path.read_text())
        counts: dict = {}
        total = 0
        for name, fn in PASSES:
            total += fn(records, prov, counts)
        print(f"{prov}: {total:,} field(s) derived over {len(records):,} records")
        for k in sorted(counts):
            print(f"      {k:<44} {counts[k]:>7,}")
        if not dry:
            path.write_text(json.dumps(records, ensure_ascii=False, indent=1),
                            encoding="utf-8")
    if dry:
        print("\n--dry: nothing written")


if __name__ == "__main__":
    main()
