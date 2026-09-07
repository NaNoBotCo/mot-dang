# แผนที่มีชีวิต — the maps gemba, 2026-08-20

> Nan's brief, verbatim in spirit: maps move from back burner to front burner.
> UX first (scrolling, panning, pinching, exploding, touching points), then
> appearance (contrast, more descriptive, more information per map), then
> architecture — page features surfacing on personalized/sharable maps, maps as
> a PRIMARY entry point to the site, touching multiple points and having those
> touches add meaning. Her verdict on today's state: "maps feel dead."
>
> This note is the assessment and the proposed order (WO-20). **No code was
> changed in this pass.** Findings are tagged by how they were established:
> `[live]` verified on https://motdang.net in a browser this session,
> `[code]` read directly from source, `[measured]` a number computed from the
> repo's own data. Platform weighting uses actual Thailand statistics
> (StatCounter, July 2026), per Nan's instruction.

## Platform reality the priorities are weighted by

- Thailand web traffic: **mobile 59.16% / desktop 40.84%** (StatCounter, Jul 2026).
  A go-somewhere city directory skews far past the national mean; Nan's working
  figure of ~90% phones (Android-heavy, plenty of iPhones) is the right planning
  number for this site.
- Mobile OS: **Android 64.27% / iOS 35.69%.** Vendors: Apple 35.7%, Samsung
  18.7%, OPPO 17.0%, vivo 10.7%, Xiaomi 6.4%, realme 4.7% — i.e. the Android
  two-thirds is mostly mid/budget tier. Assume modest GPU/CPU, and treat the
  ~1 MB MapLibre parse (282 KB over the wire, zstd `[live]`) as real cost.
- Mobile viewports cluster **360–414 CSS px wide** (top: 414×896 19.8%,
  360×800 11.5%, 390×844 9.0%). Everything below was tested at 375×812.
- Sharing here is LINE-first (the site's own design), so many map views open
  inside the LINE in-app WebView: cramped viewport, no install, first-party
  fetches only is already the right instinct.

## What already stands (the gemba found strong bones)

- `map_shell.py` is a genuinely good architecture: ONE map constructor
  sitewide; self-hosted PMTiles vector basemap (cm-cr.pmtiles, z0-15) mounted
  over a drawn-SVG fallback that prints, survives scripting-off, and returns on
  tile failure; lazy mount; no geolocation prompt ever from a map. 16,665 built
  pages carry a mounted map `[measured]`.
- `map_ground.py` paints the same ground in the same palette into every
  Python-drawn picture (cards, gifs, posters) — share cards already stand on
  real ground.
- The road graph + `plan.html` is a real multi-stop instrument: up to 8 stops,
  road-true legs, moat-gate crossings, one `?stops=` share link. The seed of
  "multiple points with meaning" already exists.
- The per-category GeoJSON (44 files) is baked every build; `open_lamps.json`
  knows opening rhythms; venue-state boards (muaythai/cooking/chang) hold
  structured facts. The DATA for information-dense maps exists; the maps just
  don't drink from it yet.

## Findings, ranked

### A. Touch answers nothing (the reason they feel dead)

1. **Neighbour links die the moment tiles load — on all 12,309 place maps.**
   `[live][code]` `map_shell.py:537-538` sets `.mdmap.mdmap-on .mdmap-draw
   {pointer-events:none}` and re-enables only `.loopin` — a class only
   `toilets_layer.py` emits. `place_map()`'s nine neighbour links are
   `<g class="nbs">` (build.py ~5445ff), so with a live basemap their computed
   `pointer-events` is `none` (verified on
   /cm/p/0114210300023.html: 9 links, `none` mounted, `auto` fallback).
   WO-7's "110,000 internal edges" are unclickable in exactly the state
   readers see. One CSS line broke it; one CSS line fixes it.
2. **`mdmap:click` has one consumer on the whole site** (toilets origin move).
   `[code]` Everywhere else a tap on the ground dispatches an event nobody
   hears. Place maps, shelf maps, merit, soi, events, plan: touching the map
   changes nothing.
3. **Shelf-map taps are a precision lottery on phones.** `[code]` The nearest-
   point hit test uses a 14-viewBox-unit radius (build.py ~3280) — ≈7 CSS px
   on a 360-wide phone — and a hit NAVIGATES instantly, no preview, so a fat
   finger opens the wrong page and costs a reload on cell data. Desktop gets
   hover names; touch gets nothing between "miss" and "gone".

### B. Gestures fight the reader

4. **Every map captures scroll.** `[live]` No `cooperativeGestures` anywhere;
   wheel over the canvas is consumed (verified: `defaultPrevented: true` on
   /cm/food/), one-finger drag pans the map. On phones the map bands
   (~160–190 px tall at 375 w) eat the thumb-scroll mid-page; on desktop the
   food shelf's 922×675 canvas hijacks the wheel. The vendored MapLibre
   supports `cooperativeGestures` `[code]` — config, not upgrade.
5. **Two-finger twist breaks pin registration.** `[code]` `dragRotate:false`
   disables MOUSE rotation only; `touchZoomRotate`'s rotation is on by
   default and nothing calls `disableRotation()` (grepped map_shell.py JS).
   `sync()`'s translate+scale math explicitly assumes bearing 0 (its own
   comment). A casual twist on Android/iOS skews every drawn overlay off the
   ground, and with `showCompass:false` there is no button to re-north.
   Verify once on a real phone, then fix: `map.touchZoomRotate.disableRotation()`.
6. **No rails, no recovery.** `[code][live]` No `maxBounds` (pan to open sea),
   no `minZoom` floor (zoom out to a blank planet — tiles only cover CM+CR),
   no re-center/home control, no expand/fullscreen, zoom buttons at
   MapLibre's default ~29 px (guideline 44). The fallback SVG accepts no
   gestures at all, so on slow cells the map is an inert picture with no sign
   it would ever have moved.

### C. Appearance: quiet to the point of silence

7. **Ground contrast measures 1.05–1.38:1** `[measured]` against paper
   #FBF6EC (WCAG floor for meaningful graphics: 3:1): minor roads 1.06,
   major 1.05, highway 1.13, casing 1.38, water 1.29, green 1.10. Labels are
   fine (8.06:1). Beautiful in the hand, washed out at 360 px in sunlight —
   and Nan is low-vision. The palette lives in `data/basemap_style.json` +
   `map_ground.PALETTE` (kept in sync by `tests/test_ground.py`), so one
   retune moves site + cards together. Target ~1.8–2.5:1 fills, ≥3:1 water +
   casings; verify at 360 px.
8. **Maps under-inform.** `[code]` Only two symbol layers (place + road
   labels); no landmark anchors (gates, wats, hospitals, markets), no legend
   anywhere, no scale-appropriate POI names — though the catalogue itself
   holds all of them. Venue-states never reach a map: fight-tonight,
   session-today, open-now lamps all render as lists only.
9. **Mobile renders maps at ~52% of design size.** `[live]` The SVG overlays
   are laid out for desktop widths and scale down: neighbour labels 8.5 px
   Thai text, dots r=1.9 px, tap targets 19 px tall at 375 w. Thai with tone
   marks at 8.5 px is decoration, not information.

### D. Architecture: no doors

10. **There is no explore map.** No /map.html; the homepage carries no map
    and no แผนที่ nav entry `[live]`. The 44 baked GeoJSON files are drawn
    only as one-shelf dot maps. Nothing shows "everything near me" or lets
    two shelves share a frame. The directory tree is the only entry.
11. **Meaning flows one way: list → map.** Stops join a plan from listing
    rows; pins join my.html from shelf pages. No map can add to a plan, pin
    to my-page, or open a preview. The map is output only (toilets excepted).
12. **Personal + shareable seeds never meet the map.** localStorage pins,
    `?stops=` plan links, og-cards with real ground, QR pipeline — all built.
    Missing only: a "my map" view, shareable map-view URLs (#z/lat/lng/cats),
    and share-a-view-as-picture (client canvas + Web Share API file share —
    LINE-ready poster, credit drawn in pixels per `credit_mark()` discipline).
13. **Tile serving stands on the wrong URL.** `[live]` `data/basemap.json`
    points at `pub-…r2.dev` — Cloudflare's rate-limited development host —
    while `https://motdang.net/tiles/cm-cr.pmtiles` already answers 206 via
    publish/worker.js. Same-origin = one fewer DNS+TLS on every phone, no
    dev-URL throttle, no third-party host. Tiles also ship without
    Cache-Control `[live]`; add one in the worker. Glyphs still come from
    protomaps.github.io — the one third-party request left; self-host the
    font PBFs in the bucket (verify Thai ranges render first).
14. Doc drift, small: BOTS.md still says "docs/ → GitHub Pages" and lists
    map_shell as "(to build)".

## Proposed WO-20 — แผนที่มีชีวิต (the living maps)

Phased so every phase pays on its own. Steps 1–2 are bug-fix sized; nothing
here waits on a crawl. Build, test, leave on disk.

**Phase 1 — un-dead every existing map (days; config + one layer of JS)**
   a. Pointer events: extend the `.loopin` re-enable to the drawn links
      (`.nbs a` and kin), with ≥44 px invisible hit circles and mobile-side
      label floors (media-query the SVG text or bump viewBox type at small
      widths). Fixes finding 1/9 partly.
   b. Manners: `cooperativeGestures:true` sitewide; `touchZoomRotate
      .disableRotation()`; `maxBounds` on the CM+CR envelope (97.3,17.0,
      100.6,20.5 padded), `minZoom:7`; 44 px controls; a ⌂ re-center
      control; an expand control on place/shelf maps. Fixes 4/5/6.
   c. Tap = card, everywhere: one bottom-sheet mini-card component in md.js —
      tap a pin/dot/neighbour → name, shelf, ant rank, distance, [เปิดหน้า ·
      open] [🧭 เพิ่มลงแผน · add to plan] [📌 my page]. Second tap or the
      button navigates; first tap never does. Wire it to `mdmap:click` +
      the shelf nearest-point test + neighbour pins. Fixes 2/3/11 in one
      pattern and makes EVERY map multi-point-meaningful.
   d. Serving: basemap.json url → motdang.net/tiles/…; Cache-Control on
      tiles in publish/worker.js; self-host glyphs after a Thai-range check.
      Fixes 13.
   Acceptance: on a 375 px viewport — page scrolls with a thumb over any
   map; twist changes nothing; every visible pin answers a tap with a card;
   neighbour links work WITH tiles on; a wrong tap never navigates.

**Phase 2 — the map answers back (contrast + information)**
   e. Contrast retune in basemap_style.json + map_ground.PALETTE together
      (test_ground keeps them agreeing): fills ~1.8–2.5:1, water+casing
      ≥3:1 at doorstep zoom. Optional "เส้นชัด · bold ground" toggle stored
      like md-lang, for sunlight and for low vision.
   f. Landmark anchor layer from the catalogue's own records: gates + แจ่ง,
      royal-grade wats, hospitals, markets, transport nodes — sparse,
      always-on, bilingual, at z<15. A legend chip + scale bar on every
      mounted map (the drawn ones already have bars).
   g. States on pins: open-now lamp tint from open_lamps.json; ⚔ tonight on
      muaythai dots (fight_nights.json); "sessions today" on cooking. The
      venue-states rule finally reaches the ground.
   Acceptance: a shelf map names what a stranger is looking at (title,
   legend, landmarks) and shows at least one live state without opening a
   single row.

**Phase 3 — maps as doors (entry point, personal, shareable)**
   h. `/map.html` — the explore map: full-viewport, shelf chips as filters
      (the Yahoo row as map UI), per-category GeoJSON loaded on demand,
      MDLOC near-me, URL hash `#z/lat/lng/cats` so every view is a link.
      Homepage gains a live mini-map module + แผนที่ in the primary chips;
      app.html grows toward it (the PWA already ships the offline basemap).
   i. Map → plan/my everywhere the card shows (done in 1c, surfaced here);
      my.html gains "แผนที่ของฉัน · my map" rendering pinned shelves+places.
   j. Share a view as a picture: canvas snapshot of frame + chosen pins +
      moat + ODbL credit in pixels → Web Share API file (Android Chrome +
      iOS Safari both ship it) with the view URL in the caption. The og-card
      look, made by the reader.
   Acceptance: a reader can open the site, never touch the directory tree,
   and still reach any page — and can send a friend a picture of THEIR five
   pins that carries a working link back.

**Phase 4 — joy (after 1–3; some already on BOTS.md)**
   ant_trails on real edges (idle mascot), festival_flood, nitnoy lamps on
   the explore map after dark, สุ่มพาไป animating between random pins,
   reach_layer ink-blot isochrones on tap (BOTS #4 — lands naturally on the
   1c card as "เดินถึงไหนใน ๑๕ นาที").

## BUILT 2026-08-20 — Phase 1 entire, plus Phase 2 (e) and (f)

Nan chose "Phase 1 + the contrast pass". All of it is on disk and through the
gates; the standing walk ships it. `cache/walk-rest` held the site still during
the work and has been removed.

**Phase 1a — touch.** `map_shell.CSS`: the `pointer-events` re-enable is stated
by what a mark IS (`.mdmap-draw a`) rather than by the one class the toilets
page happened to use, so a link drawn on a map is a door on every surface,
tiles or no tiles. Each neighbour anchor gained an invisible `.hit` disc, its
`data-n/-sub/-lat/-lng/-plan/-rank`, and the rest of the fingertip tolerance is
done at runtime where the reader's real pixels can be measured.

**Phase 1b — manners.** `cooperativeGestures` (two fingers move the map, the
page keeps its scroll; ctrl/⌘+wheel on a desktop), with the prompt written
Thai-first. `touchZoomRotate.disableRotation()` — the twist that skewed every
drawn pin off its street. `maxBounds` on the two provinces + `minZoom` 7.2, both
published from `data/basemap.json` so the fence moves with the archive.
44 px controls, a ◎ re-center, a full-screen control (feature-detected — iPhone
Safari cannot, and a dead button is worse than none), and a LIVE scale bar that
retires the drawn one whenever there is ground under it.

**Phase 1c — the card.** `MDCARD` in md.js: one bottom sheet any map opens.
Name, shelf, 🐜 rank, distance-from-here, then **เปิดหน้า · Open** and
**🧭 เพิ่มลงแผน · Add to my plan** (same `md-plan` store as every listing row,
so the rings stay in sync). **The first touch never navigates.** Wired to
neighbour anchors, to near-misses, to bare-ground `mdmap:click` — the event that
had exactly one listener on this whole site — and to the shelf map.
*Found on the way:* the shelf map bound its hover and click to the SVG, which
goes `pointer-events:none` on mount, so shelf hover and click died with tiles on
too — the same root cause as the neighbour bug. Both now bind to the holder.

**Phase 1d — serving.** Tiles moved off the rate-limited `pub-*.r2.dev`
development host to the site's own origin (relative path, absolutised against
data-root). Verified byte-identical first (sha256 of the same range on both
hosts) — and the site origin already answers `206` with
`immutable` caching, which **corrects finding 13 above**: it was the r2.dev URL
that shipped without Cache-Control, not the site. Glyphs are now self-hosted
too (`assets/glyphs/NotoSans/`, four ranges, SIL OFL, README beside them), which
removes **the last third-party request any page on this site made**. The stack
is renamed without spaces on purpose, and map.js absolutises only the part
before `{fontstack}` — percent-encoding those braces silently unlabels every
map. `pbf` named in the publish worker's MIME table.

**Phase 2e — contrast.** Retuned by solving for a target ratio while holding
each colour's hue, applied in ONE pass to `basemap_style.json`,
`map_ground.PALETTE` and the drawn SVG fallbacks in build.py so the three can
not drift: water 1.29 → **2.15**, casing 1.38 → **2.77**, buildings 1.15 →
**1.71**, green 1.10 → **1.50**, highway 1.13 → **1.70**. Roads stay white
ribbons — what draws a street is the casing under it, now 2.9:1 from the road.
*The first attempt boosted saturation as well and produced a lime-green,
traffic-cone-orange map; hue and saturation held, lightness alone, is the
setting that keeps Nan's approved look.* Because the ground now has real ink,
pins keep their dominance by **halo** rather than by the map staying pale:
neighbour rings 1.4 → 2.4, named shelf pins 1.6 → 2.4, and a white halo coat
under the shelf dot layer.

**Phase 2f — anchors, key, and type that survives a phone.** Shelf maps draw
the nine gates and แจ่ง corners from `_moat_crossings()` — the catalogue's own
records, never a typed list — as diamonds, never dots, so a landmark cannot be
counted as a listing. A four-row key sits under each shelf map. `legible()` in
map.js finishes the sum the drawing cannot: a 640-unit frame in 337 px rendered
10.5-unit Thai at **5.5 px**; it now grows to an 11 px floor, thickens the halo
with it, and hides any label that would then print through another. On the food
shelf that is 5 readable names instead of 9 unreadable ones.

**Two things the screenshot caught that the DOM probes did not**, both fixed:
`legible()` ran only on MapLibre's `load`, so the drawing a reader looks at
while tiles are in flight — and keeps for good if tiles never arrive — stayed
tiny; it now runs at mount and on tile failure. And the key, drawn in the SVG,
had its box sized in units that did not grow with the text while the collision
pass dropped "the moat" from a map with a moat on it. A key is chrome, not
geometry: it is HTML now, so it wraps, scales with the reader's own type, and
cannot be dropped.

**Verified**, on a Range-capable local server at 375×812 (this site's own QA
rule — screenshots drift, DOM numbers are the proof; and MapLibre never fires
`load` in a throttled tab, so the mounted state was exercised by class): from a
two-deep page `data-root` resolves tiles to `206 PMTiles` and the Thai glyph
range to `200 / 57,363 real bytes`; neighbour links compute `pointer-events:
auto` **with tiles mounted** (was `none`); a tap opens the card — 🐜2, "10 ม./m
จากที่นี่" — and does **not** navigate; the plan button round-trips through
`md-plan` and flips its label; Escape closes; a shelf tap answers "Roo Bar" with
its road and its link while a tap on empty ground stays silent; **zero
third-party requests on a map page**, and zero `protomaps.github.io` anywhere in
`docs/`.

**Gates:** build clean (17,974 pages), `test_ground`, `test_moat_geometry`,
`test_alt_text`, `test_facets`, `test_asked`, `test_shelf_cards`, `test_nitnoy`,
`test_publish_gate`, `test_build_lock`, `node test_plan_routes` all PASS; no
`/Users/` in docs/.

**One pre-existing failure, NOT from this work and left alone:**
`tests/test_search.py` cannot find its extraction marker
(`const norm=s=>s.toLowerCase()`) — the string is absent from the **committed
HEAD** as well, so the search JS was refactored elsewhere and the test's markers
were never moved with it. It needs whoever owns that refactor, not this order.

## BUILT 2026-08-20, same day — PHASE 3, and 2g with it

Nan: "yes pls" to the whole list, then "start with 1, then move on". So the
rest of the order went in: the explore map, the door to it, the personal map,
the picture, and the states.

**`/map.html` — the other front door.** New `explore_layer.py` (one module, a
two-line hook, per BOTS.md). Opens on Chiang Mai; **47 shelf chips** across
both provinces, each labelled with the number of points it will actually
paint; up to **six shelves at once**, each in its own ink, the chip carrying
the ink so the chip row IS the legend. Six is a cap with a reason: a seventh
colour would have to repeat one, which would say two shelves are one shelf.
Shelf data comes from the per-category GeoJSON build.py has always written and
nothing ever drew (WO-7's original finding), fetched **only when a chip is
switched on** — nothing pulls down a shelf nobody asked for. A tap answers with
the same MDCARD every other map uses, so what a touch is worth does not change
from page to page.
- **`geojson()` gained `slug` and `rank`** — every consumer of those public
  files was holding a point it could not turn into a URL, because the slug is
  derived from the name by rules a browser does not have. Coordinates trimmed
  to five decimals (about a metre, finer than any pin here is surveyed to) for
  a third off what a phone pulls down.
- **The view IS the link.** `#zoom/lat/lng/shelf,shelf`, written with
  `replaceState` so panning does not fill the back button, read on load so a
  link somebody was sent opens on what they were shown.
- **`MDMAP.ready(el, fn)`** is new in map_shell — the way a layer that paints
  INTO the map gets the map without constructing one. map_shell stays the only
  constructor, which is the rule that matters. `data-mdfull` also turns
  cooperative gestures OFF for this page (one finger should pan a map that IS
  the page) and turns `preserveDrawingBuffer` ON only here, so the picture can
  be read back without costing memory on twelve thousand place pages.

**The door.** แผนที่เมือง · The city map is now the **first dark chip** in the
sitewide nav (new `i-map` in the sprite), and the front page carries a live
postcard of the old city — moat, named gates, real ground — that opens it.
Deliberately not a small copy of the explore map: no chips, no fetching, one
door.

**My map.** my.html's pinned shelves become `map.html#…/cm-wat,cm-food`. No
second engine and nothing stored anywhere but the reader's own browser — the
personal map is the explore map opened at what they pinned. Past six it says
the map shows six at a time rather than quietly dropping the rest.

**Send this view.** On /map.html: the canvas plus a band carrying the shelf
names and the ODbL credit **drawn into the pixels**, handed to the system share
sheet as a PNG with the view URL as the text. A link pasted into LINE does not
unfurl; the picture is what people look at. Offered only where `canShare` says
files can actually go — a button that silently does nothing is worse than none.

**Phase 2g — open now.** The lamp schedules the nitnoy map already bakes
(2,423 places) light a **green ring** around what is known to be open at this
minute, computed in the reader's own clock with no request to anybody. It
**emphasises and never filters**: a place with no hours on record is not
closed, most places here have never told anyone their hours, and a map that
dimmed them would publish a claim about thousands of businesses nobody made.
The counter says how many are known-open so the reader can see how partial that
knowledge is. Fight-night and class-session states are NOT done — they are four
venues and twelve schools, better as their own small layer than as a filter.

**When the map cannot open at all**, the picker does not sit there looking
like buttons that do nothing: the chips are disabled, the map-only controls are
hidden, and one bilingual line points at the shelf list below, which is the
whole directory as plain links. Verified by loading the built `explore.js`
against the picker markup with no map.js present — chips `disabled` +
`aria-disabled`, four controls hidden, the list still reachable.

**Gates on the completed build (20,378 pages, 42,073 files):**
`test_ground` · `test_moat_geometry` · `test_alt_text` · `test_facets` ·
`test_asked` · `test_nitnoy` · `test_publish_gate` · `test_tags` ·
`node test_plan_routes` all PASS; no `/Users/` in docs/; CNAME present.
A 31-check structural pass over the built files also passes: chips carry their
shelf key, the directory list is under the map, the box is full-page, the view
is written to AND read from the address bar, open-now rings rather than
filters, a hidden shelf restores its rings, the one location door is used, the
shared card is used, the credit is drawn into the shared picture, every
GeoJSON point has a slug, both glyph ranges ship real bytes, and no page asks
a third party for fonts. The script order was checked too — `page()` prepends
`map_shell.head()` to `extra_head`, so map.js always runs before explore.js;
had it been the other way round, explore.js would have bailed silently and the
map would never have initialised.
`test_shelf_cards` is ADVISORY in the walk and kept naming newly-created
sub-shelves as the other session's imports landed (`sights/waterfall`, then
`beauty/salon`, `beauty/barber`); `make_shelf_cards.py` was run twice for
them, and the next build copies the cards in.

**Still open:** Phase 4 joy (ant trails, festival flood, night lamps on the
explore map, สุ่มพาไป walking between pins, tap-anywhere walk-sheds), the
fight/class states above, the `.pbf` MIME line in `publish/worker.js` (needs a
manual `npx wrangler deploy`; glyphs serve fine without it), and a walk on
Nan's own phone — the vivo was not reachable over wireless adb this session
(mDNS found nothing; the debug port moves after a reboot).

## THE PHONE WALK, 2026-08-21 — and the bug only it could find

Driven on Nan's own vivo V2537 (Android 16, Chrome 151) over wireless adb,
against the LIVE motdang.net. Everything built above works on the real device.
One production defect was found, and it was invisible everywhere else.

**`map.js` and `explore.js` shipped with NO cache-busting.** The worker serves
every `.js` with `public, max-age=604800`, and `md.js`/`live.js` have always
carried a `?v=<crc32>` — `map.js` never did, and `explore.js` was written
without one. On a phone that had opened a map page in the previous seven days,
Chrome kept a week-old `map.js` and paired it with today's HTML. The old file
has no `MDMAP.ready`, so `explore.js` threw on its first call and the explore
map came up with **no dots, no chips, no hash and no share button** while every
file on the server was correct. Symptom on the device: `MDMAP` present,
`MDMAP.ready` undefined, box mounted, tiles drawn, nothing else alive.
Proved by `Page.reload {ignoreCache:true}`, after which the same page came up
fully working. **Fixed**: `map_shell.version()` hashes the JS *and* the runtime
config (tile url, glyphs, bounds, minZoom, style layers — a changed tile URL
changes what the script does as surely as an edited line), `explore_layer.version()`
hashes its own JS, and both are emitted as `?v=`. Verified the hash moves when
the code moves. **Any future map surface must carry its version the same way.**

**What the device confirmed, with fresh files:**
- The nav door: tapping **แผนที่เมือง** on the front page reaches /map.html.
- The basemap draws with **self-hosted Thai glyphs** — บ้านป่าแดดเหนือ,
  หนองหอย, เชียงใหม่ all render, two lines, Thai over Latin.
- Default shelf paints: **252 dots rendered** in one frame.
- Three shelves at once in three inks — ant red, jade, blue — plainly apart
  from each other and from the ground (`rgb(194,64,28)`, `rgb(31,107,87)`,
  `rgb(20,71,155)`), counter reading `3/6 ชั้น · shelves`.
- The address bar carried it all:
  `#12.40/18.73396/98.99310/cm-wat,cm-food,cm-massage`.
- **A real fingertip tap on a dot** opened the card for *Green Cup* — province,
  🐜1, a working `cm/p/green-cup-…html` link, add-to-plan — and the page stayed
  on /map.html. The first touch does not navigate, on a real finger.
- **Open now**: 1,835 known-open ringed in green, the rest untouched, wording
  "green ring = known open; the rest have never said".
- **Send this view is offered on her phone** (`navigator.canShare` with files
  is true in Chrome 151/Android 16) — the one thing no desktop test could
  settle.
- Controls: zoom, ⛶ full screen and ◎ re-center stacked top-left, scale bar and
  the ODbL credit both legible at phone size.

**Working the phone again** (this cost 20 minutes): `adb mdns services` returns
an EMPTY list while the device is advertising, and the port `dns-sd -L` reports
is often STALE. Browse with `dns-sd -B _adb-tls-connect._tcp local.`, then find
the live port by scanning: `seq 30000 49999 | xargs -P 200 -I{} sh -c 'nc -z -G 1 -w 1 <ip> {} && echo {}'`.
`offline` after connecting means the key is not trusted and only Nan can fix
it. `KEYCODE_WAKEUP` turns the screen on; `KEYCODE_POWER` turns it back OFF.
Chrome can be driven properly: `adb forward tcp:9222 localabstract:chrome_devtools_remote`,
then `scratchpad/cdp.py` (stdlib WebSocket client, no packages) evaluates JS in
the live page — that is what found the stale-cache bug.

## Stakes, plainly

Phase 1 is a small chore (config lines, one CSS rule, one JS component).
Skipped, the worst case is what exists now: sixteen thousand pages carrying
maps that swallow scrolls, ignore fingers, and hide their own links — and the
GIS build-out (BOTS.md layers) inherits dead interaction underneath every new
layer it paints. Phases 2–3 are each ~a WO-12-sized order. Skipped, maps stay
a garnish on a list site; built, the map becomes the second front door — the
one a phone-holder standing on a soi actually wants.
