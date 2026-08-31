# ในเวียงหรือนอกเวียง — the moat page · WO-37 · 2026-08-27

Nan's ask, verbatim in spirit: a page with lots of visualizations and
different clues, "perhaps some topology strategies," for how to tell if
you're inside or outside the moat — from someone who circles it daily and
still has, quote, 0 clue. So the reader is not a stranger to the water; the
reader is anyone who has never had to say HOW they know.

## The shape

`/moat.html`, built by `moat_layer.py`, hooked after the doi layer (the earth
page, then the water page). Door in the เมือง band: 🏯 คูเมือง-ในเวียง. A
17th search panel (`data/curated/search_panels.json`, id `moat`) catches
คูเมือง · ในเวียง · old city · แจ่ง · gate names, and doors to the page, the
🏯 old-city tag, and the map.

Nine ways to know, for the nine named crossings (five gates + four แจ่ง —
the counts match by accident and were kept on purpose), ordered by the range
they work from:

1. ดอยคือกำแพงตะวันตก — the mountain compass (10 km)
2. เส้นขอบฟ้า — skylines: chedi/palm inside, towers outside (500 m)
3. น้ำจริงกับน้ำหลอก — the moat vs the Ping vs Mae Kha (100 m)
4. อิฐกับแจ่ง — the corners and their Lanna names (rim, and in speech)
5. รถวนสองวง — the counter-rotating one-way rings (20 m, works at night)
6. ป้ายถนน — the royal name cluster, with its decoys named (5 m)
7. ซองจดหมาย — postcode 50200 as a ruling-out-only test (0 m, on paper)
8. โทโพโลยี — crossing parity (Jordan curve) + the closed-loop walk test,
   with a tally widget and the third answer (the rim is thick enough to
   stand in)
9. ถามคน แล้วก็ถามเครื่อง — nai wiang ko?, then the on-device GPS check

## Where every number comes from

- **Geometry** — `build.MOAT_POLY` + `_moat_crossings()`, the catalogue's own
  pins (never typed in the layer; ride_rules' 372 m lesson). Sides ~1,421 /
  1,514 / 1,532 / 1,518 m, ring 5,985 m, 2.23 km², tilt +1.6° off cardinal —
  all computed at build time.
- **Census** — live from `data/canonical/cm.json` at build: places, wats,
  food, hotels inside the quad; postcode split (87% of inside addresses read
  50200; 50200 also spills outside → stated as one-directional). Sentences
  heal themselves on every build.
- **Ring directions** — measured 2026-08-27 from `cache/roads/` (the WO-13
  snapshot): every `oneway=yes` segment within 110 m of the corner-to-corner
  ring, winding sense summed per road. Inner four (ศรีภูมิ มูลเมือง บำรุงบุรี
  อารักษ์) all counterclockwise; outer four (มณีนพรัตน์ คชสาร ช่างหล่อ
  บุญเรืองฤทธิ์) all clockwise; zero dissenting segments. Equivalently: water
  on the traffic's right, both banks. Cache is not a build input, so this is
  a dated static fact in the layer, like the street-name count (103 named
  streets inside, same snapshot). The outer south road is ถนนช่างหล่อ — the
  Buddha-casters' road, not an elephant road.
- **Ground tilt** — `data/terrain_profile.json` (the doi page's transect, lat
  18.7876): west wall 316 m, east wall 313 m, Ping bank 312 m. Guarded: the
  sentence drops itself if the profile is missing or disagrees. The corner
  names announce the same plumbing (หัวลิน head-of-conduit at the high
  corner, ก๊ะต๊ำ fish-trap at the low one) — the page lets the names and the
  transect corroborate each other.
- **Doi Suthep bearing** — computed from the catalogue's ดอยสุเทพ pin
  (~288°, ~10 km from the moat centroid); omitted if the pin goes missing.

## The checker

Button → `navigator.geolocation` → ray-cast against the four แจ่ง, chord
distance for the "on the rim" band (≤60 m; ride_rules measured the inner
roads at 13–22 m and outer at 50–62 m off the chords), nearest of the nine
crossings with distance and an eight-wind Thai direction word, and a loose-fix
warning past ±150 m. Entirely on-device, nothing transmitted, and the page
says so — the no-tracking rule holds because there is nothing to hold. No-JS
floor: the nine ways are the page, the corner coordinates print in a
`<details>`, and an eight-line `inWiang()` is offered to take away.

## The gate that was holding the walk — fixed in passing

The publish gate had been failing since WO-33 flagged it: `longcare.html`
rendered `theriverrehab.com` as a live `<a>` although its verdict on file is
broken, and that one link held the entire walk shut — nothing on the site
could ship. Fixed under this order because it stood between this order and
the door: `longcare_layer.py` now routes a row's `site` through the WO-31
dead-ref rule (`site_a()` — dotted span, verdict and check date in the
tooltip) and drops a broken url from the JSON-LD as well. Publish gate after
the fix: 22,165 pages, links to broken URLs 0, PASS. Alt-text, asked, search
and route gates all PASS the same evening.

## Held for Nan

- ~~The share card falls back to the brand card~~ **Done same evening, Nan's
  ask: `make_moat_card.py` (the make_toilet_card pattern — HTML through
  headless Chrome, geometry from the catalogue pins, the night ground under
  the square with its nine crossings lit, OSM credit marked). Writes
  `assets/og/moat.png`, copies itself into `docs/og/`, and `moat_layer.py`
  points og:image at it with the shelf_og fallback discipline — no card on
  disk, brand card stands in, the build never waits on Chrome.**
- แจ่งกู่เฮือง's gloss says "tradition ties the name to the ku of a noble
  called Hueang" — the หมื่นเฮือง story. If the wichaa side has a better
  provenance for the name, the gloss should inherit it.
- A tenth way exists (songthaew route colours behave differently in/out) but
  was not verifiable from the catalogue today, so it stayed out.
