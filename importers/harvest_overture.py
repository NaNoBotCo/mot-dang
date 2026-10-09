#!/usr/bin/env python3
"""🐜 Overture Maps Places for Chiang Mai and Chiang Rai — the fetch half.

WHY THIS EXISTS, AND WHY IT DID NOT UNTIL TODAY
-----------------------------------------------
Nan, 2026-09-06: "OSM should not be the single or even the first source of
ground truth" — because a place describes itself on Facebook and OSM answers
"what did a mapper walk past". The blocker was never policy, it was mechanism:
five logged-out fetches of facebook.com produced no fact, and dressing a
script as a browser to get one is off-limits.

Overture Places IS that mechanism. 99% of its Chiang Mai rows come from Meta —
they are Facebook business pages, with the page's own phone and address —
delivered as open data under CDLA-Permissive 2.0, from a public bucket, with
no account, no scraping and no terms to breach.

It was parked on 2026-08-19 ("GB-scale parquet, not stdlib — its own
decision"). Both halves of that reason are gone: duckdb reads the remote
parquet in place and takes the rows it wants, so the extract is 33 seconds and
nothing lands on disk but Chiang Mai and Chiang Rai.

WHAT THIS IS NOT
----------------
Not first truth either. It is Facebook's view of the world: a closed shop
keeps its page, an owner's house can be a business "location", and 30% of the
rows carry a confidence below 0.5. It is a SECOND WITNESS WITH A PHONE NUMBER.
Everything downstream in import_overture.py treats it that way.

THE LICENCE, PLAINLY
--------------------
CDLA-Permissive 2.0: use it, publish it, attribute it. It does NOT clear a
contribution to OpenStreetMap — different licence, and Meta's and Foursquare's
rows are in here, and `foursquare` is already on provenance.py's NOT_GIVEABLE_VIA
list. So every record and field this brings in is classed `directory` and can
never be given back (go/osm-gate). That is a cost, counted: on 2026-09-07 no
record in the catalogue had a giveable OR licence-waiting field, so the cost
of taking it today is zero.

    python3 importers/harvest_overture.py            # latest release
    python3 importers/harvest_overture.py --release 2026-08-19.0
    python3 importers/harvest_overture.py --check    # what is on disk

Needs duckdb (`python3 -m pip install duckdb`). The importer that reads the
cache does not — it is stdlib, like every other importer here.
"""
import argparse
import gzip
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "overture"
OUT = CACHE / "cmcr.jsonl.gz"
MANIFEST = CACHE / "manifest.json"

BUCKET = "s3://overturemaps-us-west-2/release"
LICENCE = "CDLA-Permissive-2.0"
ATTRIBUTION = "© Overture Maps Foundation"

# The two provinces, as a bounding box wide enough to hold both and no wider.
# The box is a first cut only — a row is kept by its POSTCODE (50xxx Chiang
# Mai, 57xxx Chiang Rai) or by naming a province, because the box also covers
# Lamphun, Lampang, Phayao and a slice of Mae Hong Son.
BBOX = (98.0, 17.2, 100.6, 20.5)

FIELDS = """
  id,
  names.primary AS name,
  names.common AS names_common,
  categories.primary AS cat,
  categories.alternate AS cat_alt,
  confidence,
  operating_status,
  phones[1] AS phone,
  websites[1] AS website,
  socials AS socials,
  emails[1] AS email,
  addresses[1].freeform AS address,
  addresses[1].locality AS locality,
  addresses[1].postcode AS postcode,
  addresses[1].region AS region,
  brand.names.primary AS brand,
  sources[1].dataset AS dataset,
  sources[1].update_time AS updated,
  (bbox.xmin + bbox.xmax) / 2 AS lng,
  (bbox.ymin + bbox.ymax) / 2 AS lat
"""


def latest_release(con):
    """The newest release directory in the bucket, or None if it will not say."""
    try:
        rows = con.execute(
            f"SELECT file FROM glob('{BUCKET}/*/theme=places/type=place/*.parquet')"
        ).fetchall()
    except Exception as e:                                   # pragma: no cover
        print(f"could not list releases: {e}", file=sys.stderr)
        return None
    rel = sorted({f[0].split("/release/")[1].split("/")[0] for f in rows})
    return rel[-1] if rel else None


def harvest(release=None, out=OUT):
    try:
        import duckdb
    except ImportError:
        sys.exit("harvest_overture needs duckdb: python3 -m pip install duckdb")
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
    release = release or latest_release(con)
    if not release:
        sys.exit("no Overture release found; pass --release")
    src = f"{BUCKET}/{release}/theme=places/type=place/*"
    x0, y0, x1, y1 = BBOX
    print(f"overture {release}: reading the north …")
    con.execute(f"""
        CREATE TABLE north AS SELECT {FIELDS}
        FROM read_parquet('{src}', hive_partitioning=1)
        WHERE bbox.xmin BETWEEN {x0} AND {x1}
          AND bbox.ymin BETWEEN {y0} AND {y1}
    """)
    # The postcode is the witness, and the province name is the fallback for
    # the rows that carry no postcode. Same discipline as WO-73's district
    # test: a coordinate inside a box is not a claim about which province it
    # is in.
    con.execute("""
        CREATE TABLE cmcr AS SELECT *,
          CASE WHEN postcode LIKE '50%' THEN 'cm'
               WHEN postcode LIKE '57%' THEN 'cr'
               WHEN lower(region) LIKE '%chiang mai%' OR region LIKE '%เชียงใหม่%' THEN 'cm'
               WHEN lower(region) LIKE '%chiang rai%' OR region LIKE '%เชียงราย%' THEN 'cr'
          END AS province
        FROM north
        WHERE postcode LIKE '50%' OR postcode LIKE '57%'
           OR lower(region) LIKE '%chiang mai%' OR region LIKE '%เชียงใหม่%'
           OR lower(region) LIKE '%chiang rai%' OR region LIKE '%เชียงราย%'
    """)
    rows = con.execute("""
        SELECT id, name, names_common, cat, cat_alt, confidence, operating_status,
               phone, website, socials, email, address, locality, postcode,
               region, brand, dataset, updated, lng, lat, province
        FROM cmcr WHERE name IS NOT NULL AND province IS NOT NULL
    """).fetchall()
    cols = ["id", "name", "namesCommon", "cat", "catAlt", "confidence",
            "status", "phone", "website", "socials", "email", "address",
            "locality", "postcode", "region", "brand", "dataset", "updated",
            "lng", "lat", "province"]
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(out) + ".part")
    counts = {"cm": 0, "cr": 0}
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        for r in rows:
            d = dict(zip(cols, r))
            d["namesCommon"] = dict(d["namesCommon"] or {})
            d["catAlt"] = list(d["catAlt"] or [])
            d["socials"] = list(d["socials"] or [])
            counts[d["province"]] += 1
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    tmp.replace(out)                       # atomic: a half-written cache is a lie
    manifest = {
        "release": release, "fetched": date.today().isoformat(),
        "licence": LICENCE, "attribution": ATTRIBUTION,
        "source": f"{BUCKET}/{release}/theme=places/type=place/",
        "rows": len(rows), "cm": counts["cm"], "cr": counts["cr"],
        "bbox": list(BBOX),
        "note": "Meta/Facebook business pages in the main. A second witness, "
                "not first truth. Never giveable to OpenStreetMap.",  # stylecheck: allow — licence note for the operator
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"overture {release}: {len(rows)} rows "
          f"(cm {counts['cm']}, cr {counts['cr']}) → {out.relative_to(ROOT)}")
    return manifest


def check():
    if not MANIFEST.exists() or not OUT.exists():
        print("no overture cache on disk — run importers/harvest_overture.py")
        return 1
    m = json.loads(MANIFEST.read_text())
    print(f"release {m['release']} fetched {m['fetched']} · {m['rows']} rows "
          f"(cm {m['cm']}, cr {m['cr']}) · {m['licence']}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--release", help="e.g. 2026-08-19.0; default is the newest")
    ap.add_argument("--check", action="store_true", help="report what is cached")
    a = ap.parse_args()
    sys.exit(check() if a.check else (harvest(a.release) and 0))
