# The map bots — org chart & tasking

> New session? **Read CLAUDE.md first** — the rules that bite — then AGENTS.md for
> why the site is shaped this way. This file is the org chart for the GIS build-out:
> who does what, what each one reads, what it writes, and how a coordinate travels
> from a crawl (or a person standing somewhere) into a layer a reader can feel.
>
> The shared task board holds the live roadmap (11 tasks as of 2026-08-03; the map
> foundation task gates the visual layers). This file is the standing structure;
> the board is the moving state.

Everything here is stdlib Python, runs locally, and ships static files. Anything
live reaches the page through our own Cloudflare worker, snapshot-synced to
`data/` the way `sync_toilets.py` already does. The one read-time fetch is the
basemap on map pages (own bucket for tiles AND label glyphs), set up
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

## Tier 0 — SCOUTS & READERS  (the place's own voice comes first)

Nan, 2026-09-06: *"OSM should not be the single or even the first source of
ground truth… Let's use opus bots with high quality instructions, designed to do
exhaustive work and glean ALL kinds of data that can potentially be structured.
Not just filling in our current gaps, but identifying what potential information
sources exist and growing/scaling around them. In perpetuity."* Measured that
day: 63% of records are OSM, 1% carry a Facebook page, and 43 of 46 real CM
businesses found from the Facebook side matched nothing here.

| bot | model | reads | writes | cadence |
|---|---|---|---|---|
| `importers/discover_facebook.py` *(LIVE)* | none — stdlib | the query matrix: **tier 1** 612 shelf labels × province, **tier 2** 255 self-description words × province, **tier 3** every yielding word × 43 อำเภอ | `cache/fb_discovery/queries/`, `data/curated/fb_discovery.json` (leads, per-shelf denominators, catalogue match, **saturation state**) | resumable; a query is fresh for 30 days |
| `importers/reconcile_fb_vocab.py` *(LIVE)* | none — stdlib | `fbCategories` harvested off every page read | new words in `data/curated/fb_vocabulary.json` | after every read batch |
| `fb-finder` *(scheduled task, Opus)* | the queue | 250 searches a run → `_incoming/fb-search/`, deposited | **3× daily** 06:00 / 14:00 / 22:00 |
| `facebook-reader` *(scheduled task, Opus)* | `fb_discovery.json` unmatched rows; the page's About tab in Nan's logged-in Chrome | `data/curated/additions-*.json` records with `sources[{type:"own-facebook"}]`; `_incoming/fb-reader-<date>.txt` ledger; refusals with reasons | nightly 02:35, up to 25–30 pages, one at a time |
| `source-scout` *(scheduled task, Opus)* | `data/curated/source_register.json`; the empty-shelf survey; the web | new entries in `source_register.json` with a MEASURED mechanism; `notes/source-scout-<date>.md`; a fork for Nan when a source needs a licence call | weekly |

**"Until it's complete" — what that can honestly mean.** Nan, 2026-09-06: *"All
categories, no limits. Help the bots build this out until it's complete."* There is
no list of every business in two provinces to check ourselves against, so completeness
is measured as **saturation**, per shelf, and stated as what it is: when the last eight
queries on a shelf add under 10% new pages, that shelf is *saturated for this
vocabulary* — a statement about our searching, never about the city. The vocabulary is
what makes that honest rather than circular: every page read hands back the category
its owner chose, `reconcile_fb_vocab.py` folds new ones in, and those words go back
through the sweep. The loop runs until the city stops offering words we do not have.

Arithmetic, so nobody promises a date they cannot keep: 1,734 tier 1+2 queries at
750 searches a day is **~2–3 days**; tier 3 opens up to ~37,000 more and is
adaptive, so its real size is set by how many words yield — at the same rate,
weeks, not years. Reading is the narrow part: 25–30 pages a night is ~10,000 a
year, so the reader always works the biggest gaps first and the leads it has not
reached sit in `fb_discovery.json` losing nothing.

Tier 0 contracts:
- **Own voice outranks a directory, and a register outranks a crawl.** A fact read
  off the business's own page enters the record as a fact; a directory's copy
  enters as a lead. `source_register.json` grades every source.
- **A source is not "works" until it has a yield with a date.** The scout measures
  before it recommends; "to-scout" is an honest status.
- **No token matching.** A Facebook page is the same place as a record only by
  page identity or by whole name; everything else is a lead for a person.
- **A page with no location is still a business.** Online-first shops file as
  `needs-pin`, never dropped for lacking a pin — a place directory is not a map.
- **A name is never guessed into a URL** (`fburl.py`).
- **No private individual's data** — a sole trader's page is a business page;
  a person's profile is not read, not recorded, not linked.
- **Bounded batches, one page at a time, politely.** The reader stops at its batch
  size; the finder stops at a challenge page and resumes tomorrow.
- **Every refusal is written down with its reason** (the motorbike.json `refused`
  discipline), so the denominator is printable.

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
- **A sync keeps what is on disk** when the source is unreachable, rather than writing an
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
  place with no `hours` renders *neutral* on the breathing map rather than dark-as-closed.
  An isochrone says what is reachable, not that the rest is unreachable (the graph
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
not "wrong rule"** — a projection bug or a bad join reads to every visitor as
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

---

## Off to the side — the bot in the team group  *(added 2026-09-07)*

Not a pipeline bot: it gathers nothing by itself and writes no records. It is a
LINE Official Account (`@964yxgnk`, the one the contribute doors already point
at) sitting in the team chat, and it exists so a photo somebody took reaches the
repo with a place and a sender attached instead of dying in a chat scroll.

| piece | where | does |
|---|---|---|
| `motdang-line` Worker | its own repo, `line.motdang.net` | takes the LINE webhook, keeps photo bytes in R2 and a row per event in D1, replies in the chat |
| `importers/pull_line.py` | here | brings photos and bug reports down into `_incoming/line/`, each photo with a provenance sidecar |
| `motdang-line-desk` | scheduled task, hourly | runs the puller, then carries the new photos to Drive |

Two constraints worth knowing before proposing anything that leans on it: a LINE
bot **cannot read a message sent before it joined**, and LINE **drops photo bytes
after a while**, so there is no backfill — a photo is caught at
webhook time or not at all. The album and Keep are invisible to the API too;
only what is sent into the chat arrives.

Filing uses `docs/data/index.json`, so it can only name places the site can
already show. Building that index taught us something about our own names: 172
records read `Car park · 570 m from Tha Phae Gate`, and matching on that tail
files a photo of the gate under a car park. The bot strips the generated bearing
before matching. It files at 0.80 and clear of the runner-up, and asks otherwise
— an unfiled photo is a question for a person, not a gap for a bot to close.
