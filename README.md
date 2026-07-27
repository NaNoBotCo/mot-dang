# มดแดง Mot Dang — Chiang Mai · Chiang Rai city directory

Thai-first, 1997-directory-genre city index + GIS. The dataset is the product;
the directory pages and (later) the map are two lenses on it. Chiang Mai is the
full build-out; Chiang Rai is a wireframe that grows.

## Quickstart

```bash
python3 importers/import_all.py   # fold source corpora -> data/canonical/{cm,cr}.json
python3 build.py                  # -> docs/ (GitHub Pages ready, .nojekyll included)
open docs/index.html              # works from file://, offline
```

Or use the Desktop launcher: **Mot Dang.command**.

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

## Roadmap

- **Phase 1** (this): directory site, CM full from existing corpora, CR wireframe.
- **Phase 1.5**: CM Overpass crawl for hotels, markets, intl schools, condo buildings.
- **Phase 2**: GIS layer — per-category GeoJSON already ships; add map pages,
  ตำบล/ซอย browse tree, landmark-relative "near หอนาฬิกา" queries.
- **Phase 3**: suggest/moderation loop (mueang-map Cloudflare worker pattern).
- **Phase 4**: sponsors — 1997-innocent ad model.
