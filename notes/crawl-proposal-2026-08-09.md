# Crawl proposal — the selectors the crawler never asks for

Written 2026-08-09. **Nothing here has been run.** A network crawl needs her
go-ahead (CLAUDE.md), and this is the thing to say yes or no to.

Source: `cache/census/*.csv`, already on disk from `census_overpass.py` — a
per-key value tally over TH-50 and TH-57 diffed against the selectors in
`crawl_overpass.py`. No new fetch was made to produce this list.

## The number

**8,594 POIs across 48 selectors** that map onto shelves Mot Dang already has.
A further ~1,400 sit in selectors with no obvious shelf and are listed at the
bottom rather than smuggled in.

## ⚠ Crawling is not enough — the trap this repo has already hit twice

`import_overpass.py:classify()` needs a matching rule for every selector added,
or the records are fetched and then **silently dropped at import** — the record
count does not move and nothing errors. This bit the parks/tattoo crawl
(Batch 12c) and the `cafe` subcategory sat at zero for weeks the same way.
So each row below is two edits, not one: a selector in `crawl_overpass.py`
**and** a rule in `classify()`.

## The biggest gap: medical, and especially Chiang Rai's

| selector | CM | CR | → shelf |
|---|---:|---:|---|
| `amenity=clinic` | 111 | 79 | medical |
| `amenity=hospital` | 90 | 47 | medical |
| `healthcare=clinic` | 66 | 68 | medical |
| `amenity=doctors` | 101 | 18 | medical |
| `amenity=dentist` | 95 | 17 | medical |
| `healthcare=hospital` | 28 | 17 | medical |
| `healthcare=dentist` | 24 | 10 | medical |
| `shop=optician` | 66 | 19 | medical |
| **total** | **581** | **275** | |

Chiang Rai currently holds **4 medical records in total**, because the medical
shelf arrived from `cm-womens-health`, which is Chiang Mai only. This is the
single largest correctable hole in the catalogue.

## Everything else that maps to an existing shelf

| selector | CM | CR | → shelf |
|---|---:|---:|---|
| `shop=massage` | 344 | 50 | beauty |
| `leisure=swimming_pool` | 307 | 56 | fitness |
| `office=government` | 216 | 121 | essentials |
| `shop=variety_store` | 38 | 274 | shopping |
| `amenity=pharmacy` | 263 | 23 | essentials |
| `amenity=police` | 141 | 86 | essentials |
| `shop=supermarket` | 131 | 89 | shopping |
| `shop=motorcycle` | 140 | 77 | repair |
| `shop=clothes` | 134 | 72 | shopping |
| `shop=car` | 129 | 75 | repair |
| `shop=funeral_directors` | 52 | 123 | community |
| `tourism=attraction` | 352 | 179 | sights |
| `tourism=information` | 130 | 33 | sights |
| `shop=fuel` | 118 | 32 | transport |
| `tourism=camp_site` | 100 | 21 | hotels |
| `tourism=artwork` | 61 | 43 | culture |
| `amenity=crematorium` | 89 | 14 | community |
| `shop=jewelry` | 71 | 25 | shopping |
| `tourism=apartment` | 80 | 16 | realestate |
| `shop=travel_agency` | 74 | 14 | business |
| `shop=tyres` | 44 | 28 | repair |
| `shop=furniture` | 42 | 21 | shopping |
| `amenity=kindergarten` | 41 | 18 | learn |
| `shop=electronics` | 38 | 18 | shopping |
| `shop=copyshop` | 43 | 12 | business |
| `leisure=sports_centre` | 48 | 7 | fitness |
| `healthcare=pharmacy` | 44 | 9 | essentials |
| `shop=car_parts` | 36 | 17 | repair |
| `shop=greengrocer` | 36 | 12 | food |
| `amenity=nightclub` | 39 | 8 | whats-on |
| `amenity=library` | 33 | 13 | learn |
| `shop=books` | 29 | 5 | shopping |
| `shop=stationery` | 21 | 9 | shopping |
| `leisure=fitness_station` | 26 | 4 | fitness |
| `amenity=college` | 20 | 8 | learn |
| `shop=kiosk` | 5 | 22 | shopping |
| `shop=sports` | 23 | 3 | shopping |
| `shop=tailor` | 15 | 11 | crafts |

Notes on three of these:

- **`shop=massage` 394** — the massage shelf holds 289 CM records today, all of
  which arrived via `thai-answers`. This is a different tag from anything the
  crawler asks for, so the overlap is likely partial, not total.
- **`shop=variety_store` 274 in CR vs 38 in CM** — that lopsidedness is a
  mapping-convention difference between the two provinces, not a real one.
  Expect it to behave like a convenience-store shelf in CR.
- **`tourism=wilderness_hut` 241 in CM** (not in the table) — the count is high
  enough to look like a mapping project rather than 241 findable huts. Worth
  eyeballing the raw elements before giving it a shelf.

## Needs a decision, not just a yes

**`amenity=place_of_worship` — 1,595 CM / 700 CR = 2,295.**

Not simply "more wats". This tag covers mosques, churches, Chinese shrines and
Sikh gurdwaras alongside Buddhist temples, and Mot Dang's `wat` shelf is
Buddhist by name. Taking it needs a `classify()` rule keyed on `religion=` and
`denomination=`, and probably new shelves rather than one swollen one. The
catalogue already holds 596 wat records from `mueang-map`; OSM ids dedup
naturally, so the real question is what the non-Buddhist ~200 get called.

Worth doing — it is the largest single block on the list — but it is a taxonomy
decision first and a crawl second.

## Deliberately not proposed

Street furniture and landcover, which have no shelf and would swamp the
directory: `parking` (1,632), `parking_space` (1,647), `shelter` (966),
`leisure=pitch` (658), `bench` (157), `post_box` (183), `telephone` (183),
`drinking_water` (203 — already collected separately by
`fetch_water_points.py`), `motorcycle_parking` (132).

Plus ~1,400 POIs in selectors with no obvious home yet — `shop=bicycle` (83),
`amenity=car_wash` (80), `shop=coffee` (71), `tourism=chalet` (70),
`craft=gardener` (60), `amenity=bureau_de_change` (58), `amenity=monastery`
(55), `amenity=fire_station` (49), `tourism=motel` (49) and a long tail. Several
of these deserve shelves; they just need naming first.

## If she says yes

1. Add selectors to the relevant groups in `crawl_overpass.py`.
2. Add the matching `classify()` rules in `import_overpass.py` — **in the same
   change**, or the crawl yields nothing visible.
3. Run the gentle crawl per province (snapshot-first, expect 504s from
   overpass-api.de and several retries; CR needed 5–6 attempts on some groups).
4. `import_all.py`, then `build_streets` / `build_open_lamps` / `build_taste`,
   then `build.py`.
5. Re-run the suites; `test_taste.py` will fail on a stale `taste.json` if step
   4's derived layers are skipped, and it looks like nondeterminism.
