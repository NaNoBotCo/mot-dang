#!/usr/bin/env python3
"""Amphoe and tambon POLYGONS for Chiang Mai and Chiang Rai, from the national
administrative boundary set. Stdlib only, like everything else in this path.

    python3 importers/import_admin_boundaries.py            # report, write nothing
    python3 importers/import_admin_boundaries.py --write    # write data/admin_boundaries.json

WHY THIS EXISTS
---------------
Every area question this site can nearly answer has been blocked on the same
missing thing: the catalogue knows which tambon a place is in (WO-69 put
`ar` in the index) but nothing on disk knows where a tambon IS. So "records
per tambon", "ants per tambon", a coverage choropleth, and area colouring on
the map were all written down as wanting "tambon polygons, not held".

They were held. On 2026-09-08, while clearing 16 GB of dead scratch builds off
a disk that was 99% full and killing every build part-way, the national set
turned up sitting in a temp directory:

    /private/tmp/claude-501/tha_adm/tha_admin{0,1,2,3}.geojson   1.4 GB

Downloaded 2026-09-07 by another session, never brought into the repo, and one
`rm -rf` away from being lost. adm3 is tambon (7,431 nationally), adm2 amphoe
(934), adm1 province, and every feature carries BOTH scripts — `adm3_name`
romanised and `adm3_name1` in Thai — plus a P-code, plus `valid_on`.

PROVENANCE, AND THE ONE THING STILL UNVERIFIED
----------------------------------------------
The files' own fields say: Thailand, CRS84, `valid_on` 2022-01-22, P-codes in
the TH## / TH#### / TH###### shape. That shape and those field names are the
OCHA COD-AB (Common Operational Datasets, Administrative Boundaries) layout,
published through the Humanitarian Data Exchange.

**The licence is NOT recorded in the files and I did not verify it.** COD-AB
sets are normally free to use with attribution, but "normally" is not a
licence, and this site states per-field provenance and honours share-alike
rather than guessing. So this importer writes the boundaries with
`"licence": "UNVERIFIED"` and `_publish_gate` false, and nothing downstream
should draw them on a public page until the source page is read and the real
licence and attribution string are written in here. Checking it is one page:
https://data.humdata.org/dataset/cod-ab-tha

Using them INTERNALLY — counting records per tambon, auditing coverage — is a
different question from publishing the shapes, and the internal use is not
gated on this.

SIMPLIFICATION, MEASURED NOT GUESSED
------------------------------------
Full resolution is unusable in a browser: the national adm3 file is 700 MB for
7,431 features, ~94 kB each, and the two provinces alone come to tens of MB.
So the rings go through Douglas-Peucker at a tolerance stated in DEGREES and
converted to metres in the report, and the run prints the before/after point
counts and byte sizes so the trade is visible rather than assumed.

Tolerance is a fork, not a fact: 0.0005° (~55 m at this latitude) keeps a
tambon's shape honest on a city-scale choropleth and is the default. A map
that zooms to a street wants the full geometry and should fetch it per-feature
instead of shipping every ring to every reader.
"""

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "admin_boundaries.json"

# Where the national files were found. Deliberately a list: this is a temp
# directory and will not survive, so the second entry is where they belong if
# somebody chooses to keep them.
SOURCES = [
    Path("/private/tmp/claude-501/tha_adm"),
    ROOT / "cache" / "admin",
]

# Chiang Mai and Chiang Rai. Verified against the files: adm1_pcode TH50 is
# เชียงใหม่ and TH57 is เชียงราย.
PROVINCES = {"TH50": "cm", "TH57": "cr"}

# ~55 m at 18.8°N. See the docstring: a fork, not a fact.
TOLERANCE_DEG = 0.0005

# The fence the rest of the site uses, so a boundary that lands in the Barents
# Sea because somebody swapped lat and lng is caught here and not on the map.
FENCE = (97.3, 17.0, 100.6, 20.5)


def find_source():
    for d in SOURCES:
        if (d / "tha_admin3.geojson").exists():
            return d
    return None


def _perp(p, a, b):
    """Perpendicular distance from p to segment ab, in degrees.

    Plain planar maths on lon/lat. Over one province that is fine — the
    error from ignoring the earth's curvature at this scale is far below the
    tolerance itself — and it keeps this file stdlib-only.
    """
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplify(ring, tol):
    """Douglas-Peucker, iterative so a 40,000-point coastline cannot blow the
    recursion limit. Always returns a closed ring of at least 4 points; a
    'simplified' polygon with two corners is not a smaller truth, it is a
    wrong one, so anything that would collapse is returned as-is."""
    if len(ring) <= 4:
        return ring
    keep = [False] * len(ring)
    keep[0] = keep[-1] = True
    stack = [(0, len(ring) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        worst, at = -1.0, -1
        for k in range(i + 1, j):
            d = _perp(ring[k], ring[i], ring[j])
            if d > worst:
                worst, at = d, k
        if worst > tol:
            keep[at] = True
            stack.append((i, at))
            stack.append((at, j))
    out = [p for p, k in zip(ring, keep) if k]
    if len(out) < 4:
        return ring
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def walk_rings(geom, fn):
    """Apply fn to every ring, whatever the geometry type is."""
    t = geom.get("type")
    if t == "Polygon":
        geom["coordinates"] = [fn(r) for r in geom["coordinates"]]
    elif t == "MultiPolygon":
        geom["coordinates"] = [[fn(r) for r in poly] for poly in geom["coordinates"]]
    return geom


def count_points(geom):
    t, c = geom.get("type"), geom.get("coordinates", [])
    if t == "Polygon":
        return sum(len(r) for r in c)
    if t == "MultiPolygon":
        return sum(len(r) for poly in c for r in poly)
    return 0


def extract(level, src, tol=TOLERANCE_DEG):
    """One pass over the national file, keeping only our two provinces.

    Line-based on purpose. Each file holds exactly one feature per line (935
    lines for adm2, 7,432 for adm3 — checked), so this reads a 700 MB file
    without holding it in memory and without a JSON streaming dependency.
    A line that does not carry one of our P-codes is never parsed at all,
    which is what makes the adm3 pass take seconds rather than minutes.
    """
    path = src / ("tha_admin%d.geojson" % level)
    kept, stats = [], {"pts_before": 0, "pts_after": 0, "scanned": 0}
    key = "adm%d" % level
    with path.open() as fh:
        for line in fh:
            stats["scanned"] += 1
            if not any(('"adm1_pcode": "%s"' % p) in line for p in PROVINCES):
                continue
            line = line.rstrip().rstrip(",")
            try:
                feat = json.loads(line)
            except ValueError:
                continue
            p = feat.get("properties", {})
            geom = feat.get("geometry")
            if not geom:
                continue
            stats["pts_before"] += count_points(geom)
            geom = walk_rings(geom, lambda r: simplify(r, tol))
            stats["pts_after"] += count_points(geom)
            kept.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "level": key,
                    "pcode": p.get(key + "_pcode"),
                    "nameEn": p.get(key + "_name"),
                    "name": p.get(key + "_name1"),
                    "amphoeEn": p.get("adm2_name") if level == 3 else None,
                    "amphoe": p.get("adm2_name1") if level == 3 else None,
                    "province": PROVINCES.get(p.get("adm1_pcode")),
                    "provinceName": p.get("adm1_name1"),
                    "validOn": p.get("valid_on"),
                },
            })
    return kept, stats


def fence_check(feats):
    """Every coordinate inside the two-province fence, or say which is not."""
    w, s, e, n = FENCE
    bad = []
    for f in feats:
        for x, y in iter_coords(f["geometry"]):
            if not (w <= x <= e and s <= y <= n):
                bad.append((f["properties"]["pcode"], x, y))
                break
    return bad


def iter_coords(geom):
    t, c = geom.get("type"), geom.get("coordinates", [])
    if t == "Polygon":
        for r in c:
            for pt in r:
                yield pt[0], pt[1]
    elif t == "MultiPolygon":
        for poly in c:
            for r in poly:
                for pt in r:
                    yield pt[0], pt[1]


def main():
    write = "--write" in sys.argv
    src = find_source()
    if not src:
        sys.exit("no national boundary files found. Looked in:\n  %s\n"
                 "They are the COD-AB Thailand set (adm0-adm3 GeoJSON);\n"
                 "see this file's docstring for where they came from."
                 % "\n  ".join(str(d) for d in SOURCES))
    print("source: %s" % src)

    out = {
        "_comment": "Amphoe (adm2) and tambon (adm3) polygons for Chiang Mai "
                    "and Chiang Rai, simplified. Written by "
                    "importers/import_admin_boundaries.py — read its docstring "
                    "before publishing these shapes.",
        "licence": "UNVERIFIED",
        "_licence_note": "The source files carry no licence field. The field "
                         "layout and P-codes are OCHA COD-AB, normally free to "
                         "use with attribution — but 'normally' is not a "
                         "licence. Read https://data.humdata.org/dataset/cod-ab-tha "
                         "and write the real licence and attribution string "
                         "here before any of this is drawn on a public page.",
        "_publish_gate": False,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tolerance_deg": TOLERANCE_DEG,
        "tolerance_m_approx": round(TOLERANCE_DEG * 111_320 * math.cos(math.radians(18.8))),
        "levels": {},
    }

    for level, label in ((2, "amphoe"), (3, "tambon")):
        t0 = time.time()
        feats, st = extract(level, src)
        by_prov = {}
        for f in feats:
            by_prov[f["properties"]["province"]] = by_prov.get(
                f["properties"]["province"], 0) + 1
        bad = fence_check(feats)
        raw = json.dumps({"type": "FeatureCollection", "features": feats},
                         ensure_ascii=False)
        print("\n%s (adm%d): %d features  %s  %.1fs" %
              (label, level, len(feats),
               " · ".join("%s %d" % kv for kv in sorted(by_prov.items())),
               time.time() - t0))
        print("  points %s → %s (%.0f%% dropped)  ·  %.1f MB as written"
              % (f"{st['pts_before']:,}", f"{st['pts_after']:,}",
                 100 * (1 - st["pts_after"] / max(st["pts_before"], 1)),
                 len(raw.encode()) / 1e6))
        if bad:
            print("  OUTSIDE THE FENCE: %d feature(s), first %s" % (len(bad), bad[0]))
        out["levels"][label] = {
            "count": len(feats), "byProvince": by_prov,
            "pointsBefore": st["pts_before"], "pointsAfter": st["pts_after"],
            "outsideFence": len(bad),
            "features": feats,
        }

    if not write:
        print("\n(report only — add --write to save %s)" % OUT.relative_to(ROOT))
        return 0
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print("\nwrote %s  (%.1f MB)"
          % (OUT.relative_to(ROOT), OUT.stat().st_size / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
