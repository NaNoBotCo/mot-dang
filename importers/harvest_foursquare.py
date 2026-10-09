#!/usr/bin/env python3
"""🐜 Foursquare OS Places for Chiang Mai and Chiang Rai — the fetch half.

WHY, AND WHAT IT IS WORTH — MEASURED BEFORE IT WAS BUILT
--------------------------------------------------------
Nan, 2026-09-08: "YES we DO want to add a quarter million facebookish
records -- get on it!"

The honest count is smaller than a quarter million, and the difference is my
fault for quoting a rectangle. 252,621 rows sit inside the pmtiles fence, but
that fence also covers Lamphun, Lampang, Phayao and part of Mae Hong Son.
Restricted to a CM or CR POSTCODE, measured 2026-09-08 against the live
88,161-record catalogue:

    postcode-confirmed CM/CR rows            42,380
    still trading (no date_closed)           40,807
    already ours (name + <=300 m)             5,463
    NOT ours — candidate new records         36,808
      of those, still trading                35,310
      of those, carrying a phone              7,172
      of those, Thai script in the name      20,216

    what they are: dining 18,049 · retail 4,555 · community and government
    4,261 · business services 4,120 · travel 3,026 · landmarks 1,685 ·
    health 866 · arts 693 · sport 425 · events 58

So the number is ~35,000 live, unheld places, 57% of them Thai-named. That is
a 40% growth in the catalogue, not a trebling.

AS AN ENRICHER IT IS FINISHED — DO NOT USE IT FOR THAT
------------------------------------------------------
Matched against records we already hold, Foursquare would add 307 phones.
Overture added 3,631. The reason is structural, not a stale snapshot:
Overture is 99% Facebook business pages and it already took our phone
coverage from 20.4% to 70%; Foursquare carries a phone on 7.5% of its own
northern-Thailand rows. `apply()` in the importer therefore takes NEW
RECORDS ONLY and deliberately declines to touch a field on a record we hold.

TWO SOURCES, ONE SHAPE
----------------------
  mirror (default)  do-me/foursquare_places_100M — ungated, Apache-2.0,
                    a 2024 snapshot of the same data. Works today, no click.
  gated             foursquare/fsq-os-places — the real thing, refreshed
                    monthly, currently dt=2026-08-11. Twenty months newer.
                    Returns 403 until somebody with the account presses
                    "Agree and access repository" on the dataset page. That
                    is a licence acceptance and it is Nan's to make, not
                    mine, which is why this defaults to the mirror.

Switch with --gated once the click is done. Same columns, same output.

LICENCE, PLAINLY
----------------
Apache-2.0. Use it, publish it, attribute it. It does NOT clear a
contribution to OpenStreetMap, and `foursquare` is already on
provenance.py's NOT_GIVEABLE_VIA for that reason — see the note at the bottom
of this docstring. Everything this brings in is classed `directory`.

    python3 importers/harvest_foursquare.py              # the mirror
    python3 importers/harvest_foursquare.py --gated      # after the click
    python3 importers/harvest_foursquare.py --check      # what is on disk

Needs duckdb (`python3 -m pip install duckdb`). The importer that reads this
cache is stdlib, like every other importer here.

ON NOT_GIVEABLE_VIA, SO NOBODY HAS TO ASK AGAIN
--------------------------------------------
That list governs what we may UPLOAD TO OPENSTREETMAP. It has nothing to do
with what we may take in. Taking data in is wide open — Nan, 2026-09-08:
"we should be aggressively using share-alike". The give-back direction is
narrow because OSM's own licence requires contributed data be free of
third-party rights; pushing a directory's rows into OSM is barred by OSM,
not by us. The list was written for the 2026-09-05 give-back audit, which
existed to execute Nan's decision that day to contribute BROADLY —
everything licence-clean. Adding 35,000 Foursquare records costs nothing
against that: they were never giveable, and they do not make any existing
record less giveable, because provenance is per-field.
"""
import argparse
import gzip
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "foursquare"
OUT = CACHE / "cmcr.jsonl.gz"
MANIFEST = CACHE / "manifest.json"

MIRROR = "hf://datasets/do-me/foursquare_places_100M/foursquare_places.parquet"
GATED = "hf://datasets/foursquare/fsq-os-places/release/dt={release}/places/parquet/*.parquet"
GATED_REPO = "foursquare/fsq-os-places"

LICENCE = "Apache-2.0"
ATTRIBUTION = "© Foursquare Labs, Inc. — Foursquare Open Source Places"

# Wide enough to hold both provinces and no wider. The box is a first cut
# only: a row is KEPT by its postcode (50xxx Chiang Mai, 57xxx Chiang Rai),
# because the box also covers Lamphun, Lampang, Phayao and a slice of Mae
# Hong Son. Rows inside the box with no postcode are written out too, marked
# `province: null`, so the importer can decide rather than this file guessing.
BBOX = (97.3, 17.0, 100.6, 20.5)

FIELDS = """
  fsq_place_id AS id,
  name,
  latitude AS lat,
  longitude AS lng,
  address,
  locality,
  region,
  postcode,
  country,
  tel AS phone,
  website,
  email,
  instagram,
  facebook_id,
  fsq_category_labels AS cats,
  date_created,
  date_refreshed,
  date_closed
"""


def _token():
    p = Path.home() / ".cache" / "huggingface" / "token"
    return p.read_text().strip() if p.exists() else None


def _province(postcode):
    pc = (postcode or "").strip()
    if pc.startswith("50"):
        return "cm"
    if pc.startswith("57"):
        return "cr"
    return None


def latest_release(con):
    """Newest dt= directory in the gated repo, or None if it will not say."""
    try:
        rows = con.execute(
            f"SELECT file FROM glob('hf://datasets/{GATED_REPO}/release/*/places/parquet/*.parquet')"
        ).fetchall()
    except Exception as e:                                   # pragma: no cover
        print(f"could not list releases (gate not accepted?): {e}", file=sys.stderr)
        return None
    rel = sorted({f[0].split("/release/")[1].split("/")[0].replace("dt=", "") for f in rows})
    return rel[-1] if rel else None


def harvest(gated=False, release=None, out=OUT):
    try:
        import duckdb
    except ImportError:
        sys.exit("harvest_foursquare needs duckdb: python3 -m pip install duckdb")
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    tok = _token()
    if tok:
        con.execute(f"CREATE SECRET hf1 (TYPE huggingface, TOKEN '{tok}');")
    else:
        print("no huggingface token on disk — the mirror may still work", file=sys.stderr)

    if gated:
        release = release or latest_release(con)
        if not release:
            sys.exit(
                "the gated release is unreachable.\n"
                f"  Someone with the account must press 'Agree and access repository' at\n"
                f"  https://huggingface.co/datasets/{GATED_REPO}\n"
                "  Until then, run without --gated to use the 2024 mirror."
            )
        src = GATED.format(release=release)
    else:
        release, src = "mirror-2024", MIRROR

    w, s, e, n = BBOX
    sql = f"""
        SELECT {FIELDS}
        FROM '{src}'
        WHERE latitude BETWEEN {s} AND {n}
          AND longitude BETWEEN {w} AND {e}
          AND name IS NOT NULL
    """
    print(f"reading {src}", file=sys.stderr)
    rows = con.execute(sql).fetchall()
    cols = [d[0] for d in con.description]

    kept, cm, cr, unplaced, closed = [], 0, 0, 0, 0
    for r in rows:
        d = dict(zip(cols, r))
        prov = _province(d.get("postcode"))
        if prov == "cm":
            cm += 1
        elif prov == "cr":
            cr += 1
        else:
            unplaced += 1
        if d.get("date_closed"):
            closed += 1
        d["province"] = prov
        d["cats"] = list(d.get("cats") or [])
        kept.append(d)

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for d in kept:
            f.write(json.dumps(d, ensure_ascii=False, default=str) + "\n")
    tmp.replace(out)

    manifest = {
        "release": release,
        "gated": bool(gated),
        "fetched": date.today().isoformat(),
        "licence": LICENCE,
        "attribution": ATTRIBUTION,
        "source": src,
        "rows": len(kept),
        "cm": cm,
        "cr": cr,
        "no_postcode_in_bbox": unplaced,
        "marked_closed": closed,
        "bbox": list(BBOX),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(
        f"wrote {out.relative_to(ROOT)}  {len(kept):,} rows"
        f"  (cm {cm:,} · cr {cr:,} · no postcode {unplaced:,} · closed {closed:,})"
    )
    return manifest


def check():
    if not MANIFEST.exists():
        print("nothing harvested yet")
        return 1
    m = json.loads(MANIFEST.read_text())
    print(json.dumps(m, indent=1, ensure_ascii=False))
    if not OUT.exists():
        print("\nMANIFEST WITHOUT DATA — cmcr.jsonl.gz is missing; re-harvest.")
        return 1
    n = sum(1 for _ in gzip.open(OUT, "rt", encoding="utf-8"))
    print(f"\n{OUT.relative_to(ROOT)}: {n:,} rows on disk")
    if n != m.get("rows"):
        print(f"MISMATCH: manifest says {m.get('rows'):,}. Re-harvest.")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gated", action="store_true",
                    help="use foursquare/fsq-os-places (needs the licence click)")
    ap.add_argument("--release", help="a specific gated release, e.g. 2026-08-11")
    ap.add_argument("--check", action="store_true", help="what is on disk")
    a = ap.parse_args()
    if a.check:
        return check()
    harvest(gated=a.gated, release=a.release)
    return 0


if __name__ == "__main__":
    sys.exit(main())
