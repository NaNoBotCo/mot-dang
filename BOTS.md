# The map bots — org chart & tasking

> New session? **Read CLAUDE.md first** — the rules that bite — then AGENTS.md for
> why the site is shaped this way. This file is the org chart for the GIS build-out:
> who does what, what each one reads, what it writes, and how a coordinate travels
> from a crawl (or a person standing somewhere) into a layer a reader can feel.
>
> The shared task board holds the live roadmap (11 tasks as of 2026-08-03; the map
> foundation task gates the visual layers). This file is the standing structure;
> the board is the moving state.

Everything here is stdlib Python, runs locally, and ships static files. Published
pages carry **no tracking and no third-party behaviour scripts** — anything live
reaches the page only through our own Cloudflare worker, snapshot-synced to
`data/` the way `sync_toilets.py` already does. The one read-time fetch is the
basemap on map pages (own bucket for tiles, Protomaps for label glyphs), set up
in `map_shell.py` and nowhere else; pages without a map fetch nothing. One gatherer at a time, politely; network-heavy fetches are
manual-trigger and get confirmed with Nan before they run.

## The pipeline, in one line

```
GATHER → ENRICH → LAYER → VERIFY → (PUBLISH)
 fetch    precompute  build.py hooks  tests+gates   docs/ → GitHub Pages
```

A layer is two things joined: geometry somebody stood behind, and a rendering that
makes it felt. Gatherers own the first, layer bots own the second, and the seam
between them is always a file in `data/` with provenance on it.

---

## Tier 1 — GATHERERS  (bring geometry and facts in)

| bot | reads | writes | cadence |
|---|---|---|---|
| `importers/fetch_dem.py` *(to build)* | Copernicus GLO-30 open DEM, CM+CR bbox | `cache/dem/` | once; re-run only if bbox grows |
| `importers/fetch_footprints.py` *(to build)* | OSM Overpass or Overture buildings | `cache/footprints/` | quarterly at most, manual |
| `importers/refresh_hours.py` *(to build)* | Overpass, `opening_hours` diff only | `cache/overpass/hours.json` | monthly, manual |
| `importers/sync_toilets.py` *(live)* | worker `toilet:` keyspace | `data/toilets` snapshots | with pipeline |
| worker `firms`/`pm25` fetch *(to build)* | NASA FIRMS + open PM2.5, two provinces | worker KV → synced to `data/sky_season.json` | daily **in season only** |
| field GPS traces (a person) | the street itself | `data/curated/festival_geo.json` | one festival per month as dates arrive |

Gatherer contracts:
- **Curated/field truth always outranks a crawl refresh.** Same discipline as the
  rest of the repo: nothing in `data/curated/` is ever overwritten by an importer.
- **A sync keeps what is on disk** when the source is unreachable — never write an
  empty file over real data (`sync_claims.py` is the model).
- **Attribution travels with the geometry.** OSM/Overture/Copernicus credit lines
  land in the layer's provenance block, not a footnote to be rediscovered.

## Tier 2 — ENRICHERS  (turn raw geometry into precomputed, static answers)

| bot | reads | writes | job |
|---|---|---|---|
| `importers/build_hillshade.py` *(to build)* | `cache/dem/` | `assets/hillshade/` raster tiles | render once, offline; Doi Suthep presses on the west edge |
| `importers/build_isochrones.py` *(to build)* | `data/road_graph.json` | `data/isochrones.json` | 5/10/15-min walk polygons on a city grid |
| `importers/build_open_lamps.py` *(LIVE)* | canonical `hours` fields | `data/open_lamps.json` | parse opening_hours → minute-of-week intervals + meal curves + market rhythms; contracts in `tests/test_nitnoy.py` |
| `importers/make_nitnoy_gif.py` *(LIVE, optional — Pillow)* | `data/open_lamps.json`, road graph | `assets/nitnoy.gif` + `nitnoy_poster.png` | one Saturday in 48 frames; poster = og:image |
| `importers/build_cuisine_dots.py` *(to build)* | canonical `attrs.cuisine` | `data/cuisine_dots.json` + cuisine→color map | dot layer over the FULL dataset, not a shortlist |
| `importers/build_basemap.py` *(to build)* | `cache/roads/`, `data/streets.json` | `assets/tiles/*.pmtiles` | the self-hosted vector basemap |

Enricher contracts:
- **Precompute over serve.** If a question can be answered at build time, it ships
  as a static file. No layer gets a server.
- **Presence is the only claim** — the facet rule, extended to time and space. A
  place with no `hours` renders *neutral* on the breathing map, never dark-as-closed.
  An isochrone says what is reachable, never that the rest is unreachable (the graph
  has gaps). The absence of a dot is silence, not "no".
- **Deterministic output.** Same inputs → byte-same files, so git diffs of `data/`
  mean something.

## Tier 3 — LAYER BOTS  (build.py hooks — the two-line-hook discipline)

`festivals_layer.py` and `toilets_layer.py` set the pattern: a layer is one module,
and its hook into `build.py` is ~2 lines. Each new layer follows it.

| layer module | reads | renders | task |
|---|---|---|---|
| `map_shell.py` *(to build)* | vendored MapLibre + pmtiles in `assets/vendor/` | the shared map page all layers mount on | #1 |
| `nitnoy_layer.py` *(LIVE — /nitnoy.html)* | `open_lamps.json` + shared city frame | เมืองหลับนิดหน่อย: time-scrubber lamp map, meal curves, market rhythm, stop-motion | #2 |
| `reach_layer.py` *(to build)* | `isochrones.json` | tap-anywhere ink-blot walk-sheds | #4 |
| `terroir_layer.py` *(to build)* | `cuisine_dots.json` | cuisine dot-painting + legend-as-filter | #5 |
| `festival_flood.py` *(to build)* | `festival_geo.json`, wat coords, year wheel | when×where animation per festival | #7 |
| `sect_layer.py` *(to build)* | wat `attrs.sect`, Commons photos | Mahanikai/Thammayut map, photo hovercards | #9 |
| `ant_trails.py` *(to build)* | `road_graph.json` edges | idle-state mascot ants on real paths | #10 |
| `sky_season.py` *(to build)* | `data/sky_season.json` | ฟ้าฤดูนี้ — almanac-register seasonal sky | #11 |

Layer contracts:
- **Wording stays auspicious** in every nav item, title, and label. The seasonal-sky
  layer especially: it is an almanac page, a companion to `solar_terms.json`.
- Banned in copy and comments: "load-bearing", "honest".
- **Respect `prefers-reduced-motion`** — every animated layer has a still form.
- **Provenance on the page**: each layer states its sources and fetch dates the way
  place pages already do. The dashed/solid/bold border grammar extends to map
  geometry: crawled / tagged / a-person-stood-here.
- Thai canonical, EN a display layer, like everywhere else on the site.

## Tier 4 — VERIFIERS  (gates that keep a wrong map off the pages)

| check | guards against |
|---|---|
| `tests/test_facets.py` *(live)* | rules that match nothing; records reaching no shelf |
| docs/ grep for `/Users/` *(live)* | local paths leaking into the publish |
| external-request grep *(extend)* | any CDN/font/script URL in docs/ — vendored files only |
| `tests/test_layers.py` *(to build)* | a lamp claiming closed without hours data; an isochrone polygon escaping its bbox; a festival route not backed by a `data/curated/` entry |
| build determinism check *(to build)* | enricher output that churns without input changes |

The wireframe lesson applies to maps double: **an empty layer must mean "no data",
never "wrong rule"** — a projection bug or a bad join reads to every visitor as
"Chiang Mai has nothing there". A layer whose source file is missing renders the
มดกำลังไปเก็บ state, and a layer whose source file is *malformed* fails the build.

---

## How a coordinate travels (the point of the chart)

A monk's-alms-hour lamp on the breathing map starts as an `opening_hours` string a
mapper typed (GATHER), becomes a minute-of-week bitmap (ENRICH), lights a dot at
05:30 on the scrubber (LAYER), and could not have shipped dark-as-closed for the
7,000 places we know nothing about (VERIFY). Every layer should be traceable
end-to-end like that, and if it can't be, the gap belongs on the task board —
not silently absorbed.
