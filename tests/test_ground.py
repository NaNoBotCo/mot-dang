#!/usr/bin/env python3
"""map_ground.py — the reader that puts a basemap under the drawn pictures.

Three things are worth holding still here, and they are the three that have
already gone wrong once each:

1. The palette must be the site's. map_ground reads data/basemap_style.json so
   the cards and the live maps are one map; the literals in the module are only
   a fallback, and a fallback that has drifted from the style file is a card
   that quietly stops matching the site.

2. Polygon holes must be holes. The Chiang Mai moat is a ring. Fill both of its
   rings solid and the whole old city becomes water — which is what happened,
   and which reads as a faint smear rather than as an obvious bug.

3. Roads are measured in metres, not in a fraction of the picture. The
   fraction rule drew forty-metre-wide "major roads" on a city-wide frame and
   painted the moat out from both banks. The test is scale-invariance: the same
   road on a frame twice as wide must not come out twice as thick.

Everything here degrades to a skip when there is no tile archive on the
machine, because a machine without the tiles is a supported state — the site
builds, and every picture keeps its paper.

Run: python3 tests/test_ground.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import map_ground  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print("%-4s %s%s" % ("ok" if ok else "FAIL", name, "" if ok else "  — " + detail))
    if not ok:
        fails.append(name)


# ---------------------------------------------------------------- 1. palette
style = json.loads((ROOT / "data" / "basemap_style.json").read_text())
by_id = {l.get("id"): l for l in style["layers"]}
for lid, key, slot in (("earth", "background-color", "paper"),
                       ("water", "fill-color", "water"),
                       ("buildings", "fill-color", "building"),
                       ("roads-casing", "line-color", "casing")):
    want = map_ground._hex(by_id[lid]["paint"][key], None)
    check("palette %s matches %s in the style file" % (slot, lid),
          map_ground.PALETTE[slot] == want,
          "module has %s, style says %s" % (map_ground.PALETTE[slot], want))

check("night palette carries every key the day one does",
      set(map_ground.PALETTE_NIGHT) == set(map_ground.PALETTE))
check("night ground is darker than night lamp light (#f6b73c)",
      max(map_ground.PALETTE_NIGHT["highway"]) < 0xF6)

# -------------------------------------------------------------- 2. ring area
# A unit square, clockwise in screen coordinates (y down) — MVT's exterior
# winding — must come out positive; its reverse must come out negative.
cw = [(0, 0), (10, 0), (10, 10), (0, 10)]
check("shoelace calls a clockwise ring exterior", map_ground._area(cw) > 0)
check("shoelace calls an anticlockwise ring a hole", map_ground._area(cw[::-1]) < 0)

# ------------------------------------------------------------ 3. the archive
g = map_ground.shared()
if not g.available:
    print("\nno tile archive at %s — the drawing checks are skipped, which is "
          "the same state the site falls back to." % g.path)
    raise SystemExit(1 if fails else 0)

MOAT = (18.7814, 98.9781, 18.7954, 98.9934)      # S, W, N, E


def render(size, span_m):
    return g.picture((18.7884, 98.98575), (size, size), span_m=span_m,
                     credit=False, scale=False)


def road_px(im, kind, span_m, size):
    """What width the painter would use for `kind` at this scale."""
    mpp = span_m / size
    metres, floor = map_ground.ROAD_M[kind]
    return max(metres / mpp, floor)


# The moat, drawn at a scale where the whole ring is in frame, has to be a
# RING: water where the banks are and dry ground in the middle of it. Read as
# a column down the centre of the picture — it should cross water twice, once
# at the north bank and once at the south, and nothing in between.
im = render(600, 2400)
px = im.load()


def blueish(c):
    return c[2] > c[0] + 6


column = [blueish(px[300, y]) for y in range(600)]
crossings = sum(1 for y in range(1, 600) if column[y] and not column[y - 1])
check("the column crosses the moat twice — north bank and south",
      crossings == 2, "%d crossing(s)" % crossings)
check("the middle of the old city is dry",
      not any(column[220:380]), "water inside the walls")

# Roads in metres: double the ground a frame covers and a road must get
# THINNER on screen, not stay put. (The old fraction-of-width rule made this
# ratio exactly 1.0, which is how the moat got painted out.)
narrow = road_px(im, "major_road", 1200, 600)
wide = road_px(im, "major_road", 4800, 600)
check("a major road thins as the frame widens", wide < narrow * 0.6,
      "%.1f px vs %.1f px" % (wide, narrow))
check("a soi never vanishes entirely, however wide the frame",
      road_px(im, "minor_road", 40000, 600) >= 1.0)

# A pmtiles read is a binary format with a Hilbert index in it; one round trip
# through the projection is cheap insurance that neither is out.
z = 14
for lat, lng in ((18.7884, 98.98575), (19.9094, 99.8325)):
    x, y = map_ground.lnglat_to_tile(lng, lat, z)
    lng2, lat2 = map_ground.tile_to_lnglat(x, y, z)
    check("web mercator round-trips at %.3f, %.3f" % (lat, lng),
          abs(lat - lat2) < 1e-9 and abs(lng - lng2) < 1e-9)

check("tile ids are unique across a zoom level",
      len({map_ground.zxy_to_tileid(3, x, y) for x in range(8) for y in range(8)}) == 64)

# Both cities have ground under them, or a card for Chiang Rai is a blank.
for name, (lat, lng) in (("Chiang Mai", (18.7876, 98.9931)),
                         ("Chiang Rai", (19.9094, 99.8325))):
    bbox = (lat - 0.004, lng - 0.004, lat + 0.004, lng + 0.004)
    data = g.fetch(bbox, g.zoom_for(bbox, 500))
    check("%s has roads in the archive" % name, len(data.get("roads", [])) > 20,
          "%d features" % len(data.get("roads", [])))

print("\n%d check(s) failed" % len(fails) if fails else "\nall good")
raise SystemExit(1 if fails else 0)
