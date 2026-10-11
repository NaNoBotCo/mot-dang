#!/usr/bin/env python3
"""🐜 Foursquare OS Places -> Mot Dang records. The stdlib half.

Reads what importers/harvest_foursquare.py left in cache/foursquare/ and
returns NEW RECORDS ONLY. Zero network.

WHY NEW RECORDS ONLY — THIS IS THE WHOLE DESIGN
------------------------------------------------
Measured 2026-09-08 against the live 88,161-record catalogue: matched to
records we already hold, Foursquare would add 307 phone numbers. Overture
added 3,631. Foursquare carries a phone on 7.5% of its own northern-Thailand
rows against Overture's 82%, because Overture is Facebook business pages and
Facebook is where a Thai shop writes its phone number down.

So `apply()` deliberately does NOT enrich. A record we already hold is left
exactly as it is, which also means no existing record's give-back status can
be changed by this importer. Only the new-record path runs.

WHAT COMES IN
-------------
Rows with a Chiang Mai (50xxx) or Chiang Rai (57xxx) postcode, still trading,
whose category maps to a shelf, that do not match a record we hold and do not
stand within REVIEW_M of a same-shelf record we hold. Measured floor: 35,310
candidates before the shelf map and the neighbour test; 11,536 survive both.

The 210,241 rows inside the bbox with no postcode are NOT imported. The box
covers Lamphun, Lampang, Phayao and part of Mae Hong Son, and a row with no
postcode cannot be placed in a province without guessing. They stay in the
cache; when the gazetteer can answer "which amphoe is this pin in" from the
tambon polygons, that is the pass that claims them.

WHAT IT IS NOT
--------------
Not first truth. Foursquare's view persists closed shops, repeats chains, and
its 2024 mirror is twenty months stale. Every record it makes is
`confidence: third-party`, source type `directory`, via `foursquare` — which
is on provenance.py's NOT_GIVEABLE_VIA, so none of it can ever be pushed to
OpenStreetMap. That is OSM's licence rule, not a rule about what we may take
in, and it costs nothing here: these records were never giveable and, because
provenance is per-field, they cannot make an existing record less giveable.

    python3 importers/import_foursquare.py            # dry run, prints counts
    python3 importers/import_foursquare.py --sample 20

import_all.py calls apply(final, prov) the way it calls import_overture.
"""
import argparse
import gzip
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import provenance as P  # noqa: E402

CACHE = ROOT / "cache" / "foursquare"
DATA = CACHE / "cmcr.jsonl.gz"
MANIFEST = CACHE / "manifest.json"
CATMAP = ROOT / "data" / "curated" / "foursquare_categories.json"

# A row standing this close to a record we already hold on the same shelf is
# almost certainly that record under another name. Sent to review, not
# imported. Same number as the Overture importer uses, for the same reason.
REVIEW_M = 30

# An address must look like one. Foursquare writes bare locality names into
# the address field often enough that a plain string is not evidence.
_ADDRESSY = re.compile(r"\d|ถนน|ซอย|หมู่|ต\.|อ\.|ตำบล|อำเภอ|Rd|Road|Soi|Moo")
_THAI = re.compile(r"[฀-๿]")
_RULES = None


def _norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"\b(ร้าน|บริษัท|หจก|บจ|จำกัด|the|co|ltd)\b", "", s)
    return re.sub(r"[^0-9a-z฀-๿]+", "", s)


def _metres(lng1, lat1, lng2, lat2):
    dx = (lng2 - lng1) * 111320 * math.cos(math.radians((lat1 + lat2) / 2))
    dy = (lat2 - lat1) * 110540
    return math.hypot(dx, dy)


def manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def load(province=None):
    if not DATA.exists():
        return []
    out = []
    for line in gzip.open(DATA, "rt", encoding="utf-8"):
        d = json.loads(line)
        if province and d.get("province") != province:
            continue
        out.append(d)
    return out


def _rules():
    global _RULES
    if _RULES is None:
        doc = json.loads(CATMAP.read_text())
        _RULES = [(re.compile(r["match"], re.I), r["cat"], r.get("sub"))
                  for r in doc["rules"]]
    return _RULES


def shelf_of(row):
    """(cat, sub) for a Foursquare row, or None when nothing here files it.

    RULES OUTER, LABELS INNER — deliberately. A place often carries several
    labels and the order Foursquare returns them in is not significance. The
    rule file IS ordered by specificity, so consulting every label against the
    most specific rule first is what puts พอเพียง คาเฟ่ on the cafe shelf
    instead of the shopping one, which is where label order alone put it.
    """
    labels = row.get("cats") or []
    for rx, c, s in _rules():
        for label in labels:
            if rx.search(label):
                return c, s
    return None


def _source(row, m):
    return {
        "type": "directory",
        "via": "foursquare",
        "ref": f"https://foursquare.com/v/{row['id']}",
        "licence": m.get("licence", "Apache-2.0"),
        "attribution": m.get("attribution", ""),
        "release": m.get("release", ""),
        "fetched": m.get("fetched", ""),
    }


def _index(records):
    g = {}
    for r in records:
        if r.get("lat") and r.get("lng"):
            g.setdefault((int(r["lat"] / 0.003), int(r["lng"] / 0.003)), []).append(r)
    return g


def _held(row, grid):
    """The record we already hold that this row IS, or None."""
    n = _norm(row.get("name"))
    if not n:
        return None
    gy, gx = int(row["lat"] / 0.003), int(row["lng"] / 0.003)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for r in grid.get((gy + dy, gx + dx), ()):
                if n in (_norm(r.get("name")), _norm(r.get("nameTh")), _norm(r.get("nameEn"))):
                    if _metres(row["lng"], row["lat"], r["lng"], r["lat"]) <= 300:
                        return r
    return None


def _neighbour(row, cat, grid):
    """A same-shelf record standing within REVIEW_M, or None."""
    gy, gx = int(row["lat"] / 0.003), int(row["lng"] / 0.003)
    best = None
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for r in grid.get((gy + dy, gx + dx), ()):
                if cat not in (r.get("cat") or []):
                    continue
                d = _metres(row["lng"], row["lat"], r["lng"], r["lat"])
                if d <= REVIEW_M and (best is None or d < best[0]):
                    best = (d, r)
    return best


def apply(final, prov):
    """Return (enriched, new). `enriched` is always 0 — see the docstring."""
    m = manifest()
    rows = [r for r in load(prov) if r.get("lat") and r.get("lng")]
    if not rows:
        return 0, []

    grid = _index(final)
    review, unmapped, seen, new = [], {}, {}, []
    skipped_closed = skipped_held = skipped_unmapped = 0

    for row in rows:
        if row.get("date_closed"):
            skipped_closed += 1
            continue
        if _held(row, grid):
            skipped_held += 1
            continue
        shelf = shelf_of(row)
        if not shelf:
            skipped_unmapped += 1
            for lb in (row.get("cats") or [])[:1]:
                unmapped[" > ".join(lb.split(" > ")[:2])] = \
                    unmapped.get(" > ".join(lb.split(" > ")[:2]), 0) + 1
            continue
        cat, sub = shelf
        close = _neighbour(row, cat, grid)
        if close:
            d, other = close
            review.append(
                f"{round(d):3d} m  {row['name']}  [{cat}]  foursquare:{row['id']}\n"
                f"        stands beside  {other.get('name')}  {other['id']}")
            continue
        key = (_norm(row["name"]), round(row["lat"], 3), round(row["lng"], 3))
        if key in seen:
            continue
        seen[key] = row["id"]

        name = (row.get("name") or "").strip()
        is_thai = bool(_THAI.search(name))
        attrs = {"foursquareCategory": (row.get("cats") or [""])[0]}
        if row.get("facebook_id"):
            attrs["facebook"] = f"https://facebook.com/{int(row['facebook_id'])}"
        if row.get("instagram"):
            attrs["instagram"] = row["instagram"]
        if row.get("email"):
            attrs["email"] = row["email"]
        addr = row.get("address") or ""
        rec = {
            "id": f"{prov}-fsq-{row['id']}",
            "province": prov,
            "cat": [cat], "sub": [sub] if sub else [],
            "name": name,
            "nameTh": name if is_thai else None,
            "nameEn": None if is_thai else name,
            "lat": row["lat"], "lng": row["lng"],
            "geoPrecision": "exact",
            "address": addr if _ADDRESSY.search(addr) else None,
            "phone": row.get("phone"), "website": row.get("website"),
            "hours": None,
            "attrs": attrs, "featured": False, "landmark": False,
            "sources": [_source(row, m)],
            "confidence": "third-party",
            "updatedAt": m.get("fetched", ""),
        }
        key_src = P.source_key(rec["sources"][0])
        for field in ("name", "nameTh", "nameEn", "phone", "website", "address",
                      "lat", "lng"):
            if rec.get(field):
                P.stamp(rec, field, key_src, P.STATED, m.get("fetched", ""))
        # The shelf is OUR reading of their label, not their claim.
        P.stamp(rec, "cat", key_src, P.DERIVED, m.get("fetched", ""))
        if rec["sub"]:
            P.stamp(rec, "sub", key_src, P.DERIVED, m.get("fetched", ""))
        new.append(rec)

    if review:
        (ROOT / "cache" / f"foursquare_review_{prov}.txt").write_text(
            f"{len(review)} Foursquare rows standing within {REVIEW_M} m of a "
            f"same-shelf record we already hold. Not imported.\n\n"
            + "\n".join(review) + "\n", encoding="utf-8")
    if unmapped:
        lines = [f"{v:6d}  {k}" for k, v in
                 sorted(unmapped.items(), key=lambda x: -x[1])]
        (ROOT / "cache" / f"foursquare_unmapped_{prov}.txt").write_text(
            f"{skipped_unmapped} rows whose category no rule in "
            f"data/curated/foursquare_categories.json claims.\n"
            f"A shelf that should exist and does not is visible here, not silent.\n\n"
            + "\n".join(lines) + "\n", encoding="utf-8")

    print(f"  foursquare {prov}: {len(rows):,} rows -> {len(new):,} new records"
          f"  (closed {skipped_closed:,} · already ours {skipped_held:,} · "
          f"unmapped {skipped_unmapped:,} · beside one of ours {len(review):,})")
    return 0, new


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", type=int, default=0, help="print N new records")
    a = ap.parse_args()
    if not DATA.exists():
        sys.exit("nothing harvested — run importers/harvest_foursquare.py first")
    m = manifest()
    print(f"release {m.get('release')} · fetched {m.get('fetched')} · "
          f"{m.get('rows',0):,} rows cached")
    total = 0
    for prov in ("cm", "cr"):
        final = json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text())
        _, new = apply(final, prov)
        total += len(new)
        for rec in new[:a.sample]:
            print(f"    {rec['cat'][0]:<12} {rec['name'][:44]:<44} "
                  f"{rec.get('phone') or '':<14} {rec['id']}")
    print(f"\n  TOTAL new records available: {total:,}")
    print("  (dry run — import_all.py is what actually folds them in)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
