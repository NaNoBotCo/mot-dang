# เซเว่นทุกซอย — the branch layer · WO-38 · 2026-08-27

Nan's ask: *"do a much deeper enrichment dive on 7-11's. They are so individual
and complex, we've barely scratched the surface!"*

## What the shelf holds today, counted before anything was chosen

726 convenience records (cm 516 · cr 210). 404 carry `brand: 7-Eleven`; 255
carry no brand at all. The facet row built for exactly this shelf (the
`convenience` set, whose own note says "386 7-Elevens with identical records")
is filled like this: open24 278 · atm 122 · toilet 40 · wheelchair 16 ·
aircon 3 · wifi 2. Everything else waits for a person at the door.

The first hope — that OSM's `alt_name` carries the สาขา branch name — is
false and measured: 270 of 456 cached 7-Eleven elements carry `alt_name`, and
every single one of them says `7-11`. The branch's own name lives only with
CP All, which is WO-18's parked door. So this order works the seams already
on disk.

## The seams, each with its measurement

**1. The barber lie, again (names read in the shop's language).** 57 records
NAMED `7-Eleven`/`เซเว่น` carry no `brand` attr — the mapper typed the name
and skipped the tag. The true seven count is 461, not 404. Same read gives
Lotus-named and Big-C-named strays. Fence witnessed in the cache: way
544559166 is named "7-Eleven" and carries `not:brand:wikidata=Q259340` — a
mapper explicitly saying *not really one*; the name rule must skip any record
whose tags deny the brand. Rule lands at import (attrs.brand, provenance
`brandFrom: osm-name`), so the existing brand-tag pages grow on their own.

**2. In or beside a petrol station.** Join convenience ↔ our own 435 fuel
records: 41 at 30 m · 92 at 50 m · 110 at 80 m · 125 at 120 m · 140 at
150 m. The rate falls from 2.55 hits/m (30→50) to 0.6 (50→80) and settles
near 0.4–0.5 past 80 — a forecourt is 40–70 m deep, so 50 m still splits a
station from its own shop, and past 80 m the additions are neighbours across
the road. **80 m**, worded "in/beside a petrol station" so the boundary case
is inside the claim, value `osm-near` (it is a distance join and renders
dashed like one).

**3. The doubled sevens.** Same-brand pairs: 13 ≤ 80 m · 23 ≤ 120 m ·
31 ≤ 150 m · 49 ≤ 200 m. The two closest "pairs" (1 m, 6 m) are the same
shop mapped twice — merge candidates for the audit, not twins. Real pairs
start at 44 m. **150 m** is the twin line (both visible from one spot);
rendered on the branch page as a link to its double, and on the hub as the
list.

**4. Who the branch stands beside.** 601 of 726 branches have a *named*
non-convenience catalogue record within 120 m — median distance 27 m. Each
branch page gains its neighbours in words (name + measured metres, method
stated, same manners as the `via: nearest` road line). The identity CP All
won't give us, our own catalogue can: not "สาขา X" but "the 7-Eleven beside
X".

**5. The city measured in sevens.** From every named place in the catalogue
to its nearest 7-Eleven: **median 285 m**; 5,654 places within 200 m; 10,195
within 500 m; 2,552 places have none within ~5 km (the deep-rural edge,
stated as a count, not hidden). Lives on the hub as the coverage strip.

**6. Tags still on the table.** `has:slurpee` on two stores (a facet with two
witnesses is still evidence); `payment:*` on 14 (the card TAG_RULES already
exist and were filtered out only because the convenience set never declared a
`card` facet — declaring it turns them on); `level: -1` on 2 (too thin for an
in-mall facet; noted, not built).

**7. What every branch can do (the class voice).** The other half of "so
individual and complex" is what any branch does that farang readers don't
guess: bill counter, banking agent deposits, parcels, free microwave, the
chiller's posted sale windows, top-ups — and the one thing it normally does
NOT have, the customer toilet, in the exact wording data/toilets.json already
carries. Class sentences stay class sentences (the toilets rule: never one
voice); per-branch truth stays in the facet row. Confidence:
general-knowledge, labeled, festivals-style.

## What gets built (all zero network)

- `data/facets.json` convenience set += `card` 💳 · `slurpee` 🥤 ·
  `atstation` ⛽ (auto: fuel-within-80m).
- `importers/import_fixtures.py` += slurpee TAG_RULE + the fuel join (curve
  in the docstring, ATM-story style).
- `importers/import_overpass.py` += brand-from-name, fenced (exact patterns
  only, `not:brand:wikidata` denial wins, convenience-sub only).
- `build.py` += `SEVEN_CTX` (twins + named neighbours, computed once per
  build from records in memory) · a guarded band on convenience place pages
  (double link · neighbours in words · door to the hub) · seven_layer hook.
- `seven_layer.py` → **/seven.html เซเว่นทุกซอย** — census live from the
  records, brand table linking the tag pages, the doubled-sevens list, the
  coverage strip, the class primer, the words (RTGS/tone/root), the facet
  questions as the door-survey CTA, zone counts via zone_of. Emits
  `docs/data/seven.json`.
- `importers/audit_convenience.py` — the name census with receipts, the 57
  brand candidates, the two merge-suspect pairs, the denial way, strays
  (เซเว่น สตาร์ the condo is the witnessed toponym-stray).
- `data/curated/search_panels.json` += `seven` panel (18th).
- `tests/test_seven.py` + test_search queries for the panel.

## Doors NOT walked (each needs Nan's word)

1. **WO-18 stands as-is** — CP All's locator holds the สาขา names and
   per-branch services; parked behind its own robots/terms check, after
   WO-17. This order neither opens nor duplicates it.
2. **Fixtures refresh** — the ATM/toilet points are from 2026-07-27; a
   re-crawl is a network act.
3. **An in-mall facet** — needs mall polygons or a door survey; 2 basement
   `level` tags are not enough to build on.

## Postscript, same evening — the built numbers, where they moved

- **Sevens 404 → 462, not 463.** The first import run said 463 because the
  residue fence did not exist yet and "7-11 หลอด biers Bier Stube" — the
  beer stall trading in 7-Eleven livery — had been branded. The fence
  refused it (and the slash fix regained "7-Eleven 7/11"), settling at
  462 = 404 + 58 by-sign. The wrong number lasted one import cycle and the
  audit's REFUSED report is where it shows.
- **Median 340 m, not 285.** The proposal's quick measurement quietly
  dropped the 2,552 records with no seven inside its search window, which
  biases the middle low. The layer counts the beyond-5-km records in the
  population (coverage() explains why the median stays exact), and the
  full-population numbers are: median 340 m · 6,004 within 200 m · 10,617
  within 500 m · 2,693 beyond 5 km. The page prints only these.
- **Doubled sevens 31 → 34 pairs** — three pairs appeared when the by-sign
  fills gave both halves a brand.

## Held calls for Nan

- The hub's brand table names every chain the shelf holds; whether โชห่วย
  (the no-brand 255) deserve their own shelf child is a naming call, hers.
- A drawn twins map on the hub (the pairs have coordinates; the page ships
  without it rather than guessing at a projection style she hasn't seen).
