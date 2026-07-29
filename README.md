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
- **Field/curated truth beats crawled truth** — records in `data/curated/` always
  win over a crawl refresh (same discipline as mueang-map).
- **Provenance on every page** — source type + fetch date shown to readers.
- **No tracking, no third-party scripts, no external requests** on published pages.
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

## The 1997 layer

- **Search + services bar** on every page; **subcategory shelves** with counts;
  empty shelves show muted with 🐜 มดกำลังไปเก็บ.
- **my.html** — the personal start page: pin shelves, get "+N new" badges since
  your last visit, a daily pick drawn from *your* pins, custom links, sticky
  notes. All localStorage; Mot Dang follows no one around.
- **Sorting**: ก→ฮ or 📍 ใกล้ฉัน (client-side geolocation, nothing leaves the device).
- **Sharing**: pill-button row — native Web Share (mobile), LINE, WhatsApp,
  Telegram, Facebook, X, copy-link — on every page type; place pages also get
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
