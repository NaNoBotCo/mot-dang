# มดแดง Mot Dang — Chiang Mai · Chiang Rai city directory

Thai-first, 1997-directory-genre city index + GIS. The dataset is the product;
the directory pages and (later) the map are two lenses on it. Chiang Mai is the
full build-out; Chiang Rai is a wireframe that grows.

## Quickstart

```bash
pip3 install --user qrcode        # once — build.py inlines a QR per place page
python3 importers/import_all.py   # fold source corpora -> data/canonical/{cm,cr}.json
python3 build.py                  # -> docs/ (GitHub Pages ready, .nojekyll included)
open docs/index.html              # works from file://, offline
```

Or use the Desktop launcher: **Mot Dang.command**. Without `qrcode` installed,
build.py still runs fine — QR boxes are just skipped.

## Ground rules

- **Thai canonical, EN a display layer** (client-side toggle; more languages later).
- **Category tree is data** — [data/categories.json](data/categories.json). Empty
  categories are hidden by the build: no empty shelves, ever.
- **A wireframe shelf must mean "no data", never "wrong rule".** A child whose
  `match` names a sub nobody emits renders identically to one genuinely waiting
  for data — muted, 🐜 มดกำลังไปเก็บ — so a typo reads to every visitor as "Chiang
  Mai has no tattoo studios". It hid 35 studios, 56 salons and 40 vegetarian
  kitchens that were in the data the whole time. `tests/test_facets.py` now
  fails on a rule that matches nothing and on records that reach no shelf;
  shelves deliberately awaiting data are listed in `KNOWN_EMPTY`, so leaving one
  empty is a decision someone wrote down rather than an accident.
- **A shelf's name is a promise.** `repair/home` was called ช่างบ้าน-**ประปา-ไฟ**
  and held no plumbers and no electricians, because OSM maps none here — so it
  was renamed to what it actually holds. Likewise `community/intl-clubs` read
  ชมรมนานาชาติ over a Thai school's alumni association and a village hall, and
  is now ชมรม-สมาคม. If the data cannot keep the label's promise, change the
  label, not the reader's expectations.
- **Field/curated truth beats crawled truth** — records in `data/curated/` always
  win over a crawl refresh (same discipline as mueang-map).
- **Provenance on every page** — source type + fetch date shown to readers.
- **No tracking, no analytics, no third-party behaviour scripts.** Type and page
  data are self-hosted and baked. One exception, on map pages only: the basemap
  fetches vector tiles from our own bucket and label glyphs from Protomaps'
  font host, both configured in `map_shell.py`. A page with no map makes no
  external request at all. Nothing anywhere reports a reader to anybody.
  Ads, when they come, are flat-rate text + tasteful static cards marked ผู้สนับสนุน.
- **Never publish local paths**; build output is checked. Publish only as NaNoBotCo.

## Data sources (all local, zero network)

| source | records | lands in |
|---|---|---|
| thai-answers/catalog.db | 316 massage venues | cm/นวด-สปา |
| cm-womens-health osm-health.json | 258 facilities | cm/หมอ + ของจำเป็น |
| mueang-map canonical osm.json | 378 lens points | cm/วัด ร้านอาหาร ที่เที่ยว |
| mueang-map osm-chiang-rai.json | 289 wats | cr/วัด (wireframe seed) |
| data/curated/featured-chiang-rai.json | hand-entered field truth | cr featured |
| mueang-map's Commons metadata (`media` field) | 114 real, licensed wat photos | assets/photos/ — see `importers/import_photos_commons.py` |
| cache/overpass/*/fixtures.json | 833 ATM/toilet points | facets on 321 shops — see `importers/import_fixtures.py` |
| cache/overpass/*/{crafts,community,business}.json | 222 elements | laundries, coworking, clubs, trades — the three categories that had shelves but no query |

## Facets — telling one branch of a chain from the next

A crawl gives 386 7-Elevens identical records: same brand, same wikidata id,
same website, 386 pins. But nobody chooses a 7-Eleven by its brand. They choose
the one with the cash machine, or the bake-off oven, or somewhere to sit — and
none of that is in OpenStreetMap. Of 385 7-Elevens in the snapshot, **two**
carried `has:slurpee`, **one** carried `amenity=atm`, **one** carried
`internet_access`. Mapping them better is a data-collection problem wearing a
crawl's clothes.

- **[data/facets.json](data/facets.json) is the schema** — 13 facets, Thai/EN
  labels, an icon, and the question to ask a passer-by. Same discipline as the
  category tree: the list is data, not code. `appliesTo` matches `record.sub`,
  so nothing here is 7-Eleven-specific — pharmacies and fuel stations inherit
  the row when their turn comes.
- **Presence is the only claim.** An absent facet renders as *nothing*, never
  as "no". We know 109 shops have an ATM; we do not know the other 406 lack
  one, and a directory that implied it would be lying quietly.
- **The border is the provenance.** Dashed = joined by distance from a map
  point. Solid = tagged in OSM. Solid and bold = a person stood there. A reader
  can tell how much to trust a tag before they open the tooltip.
- **[importers/import_fixtures.py](importers/import_fixtures.py) works two
  seams** the shop record itself does not have. OSM maps an ATM as its own node
  *beside* the store: joining `amenity=atm` within 30m takes the known ATM count
  from 1 to 109. The hit curve flattens past 30m (73 at 20m, 79 at 30m, 87 at
  50m) — the extra hits at 50m are bank lobbies across the road, so 30m is where
  evidence stops and guessing starts.
- **Filter chips are AND, not OR** — the question is always "a cash machine
  *and* somewhere to sit", never either. The heading count follows the filter so
  it can never contradict what is on screen.
- **The vocabulary lives in three files** (schema, worker, build) because a
  Cloudflare Worker cannot read the repo at request time.
  [tests/test_facets.py](tests/test_facets.py) fails if they drift: an
  unrecognised key is silently discarded by the worker, so a contributor would
  tick "has a bakery", get a success message, and lose the fact.
- **Ticks can never open a claim.** Claiming locks a record against everyone
  else, so letting a passer-by claim by ticking a box would let a stranger lock
  a shop out of its own listing. A claim still needs a real way to reach the
  shop; ticks only ride along.

## The 1997 layer

- **Search + services bar** on every page; **subcategory shelves** with counts;
  empty shelves show muted with 🐜 มดกำลังไปเก็บ.
- **my.html** — the personal start page: pin shelves, get "+N new" badges since
  your last visit, a daily pick drawn from *your* pins, custom links, sticky
  notes. All localStorage; Mot Dang follows no one around.
- **Sorting**: ก→ฮ or 📍 ใกล้ฉัน (client-side geolocation, nothing leaves the device).
- **Sharing**: pill-button row — native Web Share (mobile), LINE, WhatsApp,
  Telegram, copy-link — on every page type; place pages also get
  an inline QR code (base64 PNG, zero extra requests) to scan or print by a door.
- **Photos**: an original hand-drawn wat illustration is the default image
  everywhere a real photo is missing (deliberately — see `build.py`'s `WAT_SVG`).
  `assets/photos/<record-id>.jpg` overrides it automatically; 114 real,
  Wikimedia-Commons-licensed wat photos already populate this from mueang-map's
  existing crawl (proper credit line rendered from `assets/photos/credits.json`).
- **Sponsors**: rotating 1997-innocent ad boxes from [data/ads.json](data/ads.json),
  always marked ผู้สนับสนุน; policy on advertise.html.
- **Contact drive**: pages without phone/LINE/FB carry a "tell the ants" CTA that
  pre-fills a GitHub issue with the place id. Contact info is the directory's
  real currency — capture it everywhere.

## Route planner (plan.html)

The errand-run layer, for the person this site is actually for: someone on foot
or on a scooter who wants a noodle stand near a clinic near a nail place, this
afternoon.

- **Add a stop from anywhere** — a ring button on every listing row, a labelled
  pill on every place page. Both drive one `md-plan` list in localStorage, so
  the nav chip's count is live on every page. Cap is 8 stops.
- **The plan lives in its URL** — `plan.html?stops=cm:<slug>,cm:<slug>,…` in
  visiting order. That link *is* the plan: no account, no server state, so it
  can be handed to somebody over LINE. Arriving by a shared link never
  overwrites the reader's own plan silently — a banner offers to keep it.
- **One map, drawn in Python-free JS** — same inline-SVG approach as the events
  map, no library: numbered pins, both routed lines, a scale bar, a legend, and
  the moat for orientation. (Not yet wired to the basemap shell; when it is,
  the drawing stays exactly as it is and gains streets underneath.)
- **Routed on real streets, per mode.** See below — this is the part worth
  knowing about.
- **Out**: reorder by hand or by nearest-on-the-network, ⬇ download as a
  plain-text itinerary (names, addresses, live channels, per-leg distances for
  both modes, the share link), or share the run through the normal pill row.
- **`make_plan_demo.py`** draws the 200×200 looping demo beside the tool by
  routing on the same graph the page routes on, and writes
  `assets/plan-demo.json` so the caption always quotes the run being drawn.

### Two networks, not one route at two speeds

Nobody can fly. There are buildings in the way, sois that do not join up, a
one-way ring around the moat, and water you cross at a footbridge or a U-turn
and nowhere else — and a footbridge is no use to a scooter. So the planner
routes on the real network, twice, and a leg usually comes back with two
different distances. Straight-line distance is wrong in a city, and most wrong
for exactly the two people this page is for.

Pipeline:

```bash
python3 importers/crawl_roads.py        # 9 gentle Overpass tiles, ~3 MB cached
python3 importers/build_road_graph.py   # → data/road_graph.json
```

`crawl_roads.py` covers the old city plus roughly a 2 km ring (5.5 × 5.5 km),
tiled because one box of every highway times Overpass out, and snapshot-first
like every other crawl here. `build_road_graph.py` contracts it to junctions —
9,767 of them, 12,280 edges, 0.56 MB (178 KB gzipped) — keeping road shape for
drawing. Only `plan.html` fetches it.

Every edge carries four permission bits: `1` foot forward, `2` foot back, `4`
ride forward, `8` ride back. Three things then make the two modes diverge, all
of them tagged in OSM rather than guessed:

- **walk-only edges** (2,243) — footways, steps, the footbridges over the moat
- **edges no walker may use** (104) — the flyovers, tagged `foot=no`
- **oneway binds ride and not foot** (2,456 vs 11) — this is the one that does
  the work. On a one-way ring road the shop thirty metres behind you is a lap
  away, which is precisely why crossing the moat costs a scooter a U-turn and a
  walker a footbridge.

Worked example, the demo on the page: one leg is 419 m as the crow flies, 526 m
on foot, 762 m on a scooter. `tests/test_routing.py` re-runs the same directed
Dijkstra in Python and holds the port to the same answers.

Outside the box nothing is invented — the leg says it is a straight line and
offers an OpenStreetMap directions link. No traffic, no turn restrictions, and
the two speeds are flat assumptions: distances are real, times are arithmetic.

**What this replaced, and why it is worth remembering.** An earlier version
special-cased the moat: it tested each leg against the ring of four แจ่ง corners
and priced a crossing round the nearest gate. It was a real improvement over a
straight line and it was still wrong — it put that same leg at 878 m against
the network's 526 m on foot. Two lessons kept: a correction that only knows one
obstacle will confidently mis-price everything else, and the moat ring still
earns its keep as a *landmark* (`tests/test_moat_geometry.py`) even though it no
longer decides a distance. Also worth keeping: threading the gates into that
ring drew a prettier line and broke the containment test, because gate nodes sit
on the road crossing slightly *outside* the water.

## Bot hospitality

`robots.txt` explicitly allows the wildcard *and* every named AI crawler
(GPTBot, ClaudeBot, PerplexityBot, etc) — on purpose, unlike sites elsewhere
in this operator's corpus that block them. `sitemap.xml` lists every page;
`llms.txt` points agents at the open data (`data/places.json` is the full
record dump, `data/index.json` the slim search index, `data/*.geojson` per
category); every place page also carries schema.org JSON-LD.

## Festivals layer

Two tables, not one. A **festival** is the recurring canon — it carries a date
*rule* and never a date. An **event** is one dated instance of it, in one year,
at one venue. `data/festivals.json` is the canon (33 entries, hand-curated,
`confidence` marked per entry); `data/events.json` is the instances. The canon
is written once, so only instances need a crawl — which is why 33 festival
pages exist without a crawler behind them yet.

`festivals_layer.py` renders it: `/festivals.html` (the hub, with the year wheel
drawn at build time), a page per festival at `/festivals/<id>.html`, the
standalone `/festival-wheel.svg`, and `/festivals.ics` — fixed-date festivals
only, with `FREQ=YEARLY`, because a lunar festival has no date to publish and
does not get invented one. Festival venues are resolved to catalogue records
through the same strict `match_venue` the events layer uses, so a wat page
carries the festivals it hosts.

`build.py` calls it in two lines after `build_festivals_page()`. If those lines
go missing, `python3 festivals_layer.py` re-lays the whole layer over an
already-built `docs/`; `--wheel` redraws just the wheel.

### Getting this year's dates

`importers/harvest_festivals.py` turns "usually late May" into "26 May – 2 June,
announced by the province, here is the page". It reads the provincial PR offices
and Chiang Mai municipality — the spec's first-choice sources, TAT and the
Chiang Mai PAO, both refuse a plain fetch, and chiangmai.go.th serves a
self-signed certificate, all recorded in `data/sources.json`.

It will not publish a date on its own authority. A row only reaches the site as
`announced` if a canon festival matched, a date parsed, the source is official,
the date is in the future, the span is under 45 days, and the month is one the
canon already says this festival falls in — and the headline was *announcing*
rather than reporting. Thai government news is overwhelmingly retrospective, and
the first live run proved the point: without those gates it produced two dates,
both wrong (a marketing slogan with stray digits, and a King's-Birthday merit
ceremony matched to Khao Phansa). Everything else is held in
`data/festival_dates.json` as a `candidate` with the reason it was held, for a
human to look at. Nothing on the site reads candidates.

## Crawl (gentle by design)

`importers/crawl_overpass.py` — snapshot-first (cache/overpass/), one query at a
time, 12s pauses, retries that rest and rotate mirrors. Refresh with `--fetch`.

## Roadmap

- **Phase 2**: GIS layer — map pages, ตำบล/ซอย browse tree, landmark-relative
  "near หอนาฬิกา" queries (condo scouting included).
- **Phase 2.5**: what's-on feeds — showtimes + events baked like the ticker;
  weather + horoscope home modules.
- **Phase 3**: suggest/moderation worker (mueang-map Cloudflare pattern).
- **Phase 4**: paying sponsors on the advertise.html terms.
