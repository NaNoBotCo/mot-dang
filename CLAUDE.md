# Mot Dang (มดแดง) — working notes for Claude

Read `AGENTS.md` first for why the site is shaped this way, and
`notes/empathy-map.md` for who it is for. This file is only the rules that bite.
GIS build-out (map layers, breathing map, isochrones): `BOTS.md` is the org
chart; the live roadmap is on the shared task board.

Thai-first CM+CR directory. Stdlib Python only. `importers/import_all.py` then
`build.py` → `docs/` (GitHub Pages). Full spec + roadmap in README.md.

Pipeline order: `importers/make_widget_shots.py` (daily — photographs the live
instruments at wichaa.net; skip it and the sky tile just does not render) →
`importers/import_all.py` → `importers/build_streets.py` (roads
and sois; needs `cache/roads/`, ~20 s) → `importers/build_open_lamps.py`
(opening hours → lamp schedules for /nitnoy.html; deterministic, contracts in
`tests/test_nitnoy.py`) → `importers/sync_claims.py` +
`importers/sync_toilets.py` (pull what people sent the worker; both keep what
is on disk if it is unreachable) → `make_og_cards.py` (optional, needs
Chrome + Pillow, writes `assets/og/`) → `importers/make_nitnoy_gif.py`
(optional, needs Pillow — the nitnoy stop-motion + og poster) → `build.py` →
push → `importers/ping_indexnow.py`.

ONE build.py AT A TIME: build wipes docs/ at start, and two sessions building
concurrently means one is writing pages into directories the other just
deleted (FileNotFoundError mid-write, or worse, a silently interleaved docs/).
`ps aux | grep build.py` before building; wait, don't race.

Rules that bite:
- Empty categories are hidden by design — don't "fix" that.
- **An Overpass timeout looks exactly like an empty province.** It answers HTTP
  200 with valid JSON, an empty `elements` list, and the error in `remark` —
  and because the crawl is snapshot-first, writing that to cache means the
  group is never asked again. A shelf sits empty forever with a cached file
  standing there as proof it was crawled. `fetch()` raises `OverpassRemark` on
  this now. If a group ever comes back suspiciously empty, check `remark`
  before you believe it.
- **A province is an AREA, never a bounding box.** Chiang Rai is wedged against
  Laos and Myanmar: a rectangle round it returns Bokeo International Airport
  and the Houayxay speedboat pier (Laos), the Tha Ton boat landing (Mae Ai,
  which is Chiang Mai) and the pier to Wat Tilok Aram (Kwan Phayao). Filing any
  of those as "Chiang Rai" is a falsehood about someone else's province or
  someone else's country. Province-wide groups (`WIDE_GROUPS`) clip to
  `area["ISO3166-2"=...]` — TH-50 Chiang Mai, TH-57 Chiang Rai — which is exact
  and language-independent. Ferry terminals went 6 → 2 when this was fixed.
- Province-wide queries are split ONE SELECTOR PER QUERY (`fetch_wide`) and
  merged. Eight selectors over a whole province in one query is what timed out
  above; each on its own finishes comfortably, and the pauses between them keep
  the same manners the group loop does.
- `data/curated/` is field truth: never let an importer or crawl overwrite it.
- No external requests, fonts, or scripts in published pages; OSM attribution stays.
- Before committing docs/: `grep -rl "/Users/" docs/` must be empty.
- Banned words in copy and code comments: "load-bearing", "honest" (user rule).
- Wording stays auspicious — no ominous names/labels in nav or titles.
- Ant rank is 0–9, one per field present (`ANT_FIELDS` in build.py). Never weight
  it, never let an advertiser move it — the whole point is that it is readable
  off the page. The freshness ant needs a human touch, not a bulk crawl.
- `wat.svg` stands in only for `wat`/`sights`; everything else gets `ant.svg`.
- Street assignment publishes its method: `via: stated` is the place's own
  addr:street, `via: nearest` is a match to the closest road line within 30 m
  with `d` metres attached. Never render a `nearest` match as an address, and
  never merge two spellings of a road — point them at each other instead.
- Street slugs are ASCII for the same reason `place_slug` is: git on macOS
  renormalizes Unicode filenames and the mismatch is a 404 after deploy.
- `data/curated/honours.json` — royal temple grades and food marks. Nothing goes
  in `royal`/`food` without a fetched source URL; leads live in `unverified` and
  are never rendered. Every food mark carries `edition` and the badge prints the
  year, because those lists change annually.
- data/line.json holds the LINE OA id; empty means the LINE blocks stay hidden.
- **Two kinds of toilet knowledge, never one voice.** `toilets_layer.py` mixes
  431 mapped points (`amenity=toilets` — certain about the spot, nearly always
  silent about price) with ~6,600 venues whose CLASS keeps one. A tier is a
  HABIT: it renders as "stations like this normally have a free toilet" and
  must never become "this station has a toilet". The sentence we stand behind
  lives in `data/toilets.json`, in both languages, and is the only wording that
  should be reused — including by bots, which llms.txt tells so explicitly.
  A verified point or a field report at the same spot always outranks the tier,
  `toiletnone` included: it is the one absence this site records, because a
  person who stood at the door and found nothing is giving testimony, and it is
  the only way a wrong guess comes off the page.
- Convenience stores are NOT a toilet tier and that is deliberate — Thai 7-
  Elevens do not normally keep a customer one. Their existing `toilet` facet
  means "there is one within 30 m". Different claim, different words; the
  reasons for every exclusion are written in `data/toilets.json` under
  `excluded`, and belong there rather than being rediscovered.
- A toilet report is not a claim. `applyClaim()` refuses to open a claim from
  ticks alone (a stranger must never be able to lock a shop out of its own
  listing), so passer-by reports live in the worker's own `toilet:` keyspace
  via `POST /toilet`, and `importers/sync_toilets.py` snapshots them the same
  way sync_claims.py does. That sync keeps what is on disk when the worker is
  unreachable rather than writing an empty file over real reports.
- **KV list is eventually consistent; KV get is not.** `GET /toilets` uses
  `KV.list`, so a report just written can be missing from it for up to ~60 s
  while `wrangler kv key get --remote` already returns it. Do not go bug-
  hunting in `listPrefix` over this, and do not sync-and-build the instant
  somebody reports — the next sync catches it.
- Cleaning up test data in KV: `--remote` or you are editing the local
  simulation and silently changing nothing real. `wrangler kv key delete` has
  no `--force` — passing it prints usage and deletes nothing, which looks
  exactly like a successful run if you do not read the output. Always list the
  prefix afterwards to confirm.
- The toilets page sorts by distance and NOTHING else. An earlier version
  nudged confirmed rows up by 90 m and produced a list reading 80, 120, 270,
  180 — on a page promising "nearest first" that reads as broken. Confidence
  belongs in the row's chips, not in the sort.
- The which-way panel on /toilets.html is drawn in the BROWSER, not at build
  time, because it centres on wherever the reader is — the one map on this
  site that has to be. Still no tiles and no library: every shape comes from
  coordinates in the baked file, and the moat and its nine gates come from
  `MOAT_POLY` / `_moat_crossings()`, so a gate can never sit in one place on
  the plan map and somewhere else here. Test whether the ring's BOUNDING BOX
  overlaps the frame, never whether a corner is inside it: the moat is four
  points with very long sides, and standing at Tha Phae Gate — on the moat —
  every corner is off-frame while the side you are standing on runs through
  the middle. The vertex test drew nothing there.
- The cinema showtime request recipe — address, form fields, screen ids — lives
  in `~/.mot-dang-showtimes.json`, never in the repo. Same arrangement as the
  LINE channel token. `make_showtimes.py --template` prints the shape; without
  the file that one importer explains itself and exits, and nothing else cares.
  Do not put it back in `data/sources.json`; it was removed from history once.
- `/chart.html` computes in the reader's browser and has nowhere to send a birth
  date. Keep it that way. The "email me this" block appears only when
  `data/config.json` gains a `listEndpoint`, the same gate as the LINE blocks —
  and `/privacy.html` has to describe the collecting before the gate opens.
- `assets/bazi.js` is GENERATED by `importers/make_bazi_js.py` from
  `../taoist-oracle`. Edit it there and regenerate, or `tests/test_bazi_parity.py`
  starts failing. It and `data/solar_terms.json` are copied into `docs/` by
  build.py — never hand-place them, docs/ is wiped every run.
- The look comes from a Claude Design study Nan approved. The palette lives in
  `:root` and the whole design layer sits in ONE block at the end of `CSS` —
  ribbon, sticker shadows, hero, mood cards, after dark, the gold claim band.
  Retune the variables, not the rules. Two things from that study are refused
  on purpose and must stay refused: star ratings and review counts (we hold no
  ratings; drawing them invents facts about named businesses) and a Leaflet map
  on third-party tiles (every tile is a request to someone else's server from a
  site that promises it follows no one around).
- Type is self-hosted in `assets/fonts/` — Chonburi, Prompt, Sriracha, all SIL
  OFL, licences beside the files and copied into `docs/fonts/` by build.py.
  Chonburi is a display face: headings only, never running text, and it has no
  bold, so `<b>` inside a heading falls back to Prompt.
- `data/curated/image_picks.json` + `assets/site/` are Nan's own city pictures,
  resolved by `importers/import_image_picks.py`. They are the site's FURNITURE,
  not place photos: a picture of a red songthaew may head the transport shelf
  without being that songthaew. Reach them through `art()` on four axes —
  topic, season, place, mood. It is deterministic on purpose (a random pick
  would redraw the homepage every build) and returns nothing rather than
  something else when a request cannot be met. `local=True` for anything over a
  shelf, and `not_topic=("people",)` for decoration: a portrait used as
  wallpaper or as a category tile makes scenery of a named stranger, which is
  the framing this site does not do. Credit is a licence condition, not a
  courtesy — `/pictures.html` is generated from what was actually drawn.
- **The moon is not drawn here.** It used to be, three different ways, and one
  of them told the reader on the page that its angle was approximate. The sky
  tile now shows daily photographs of wichaa.net/moon, /jovilabe and /redspot,
  taken by `importers/make_widget_shots.py`, each linking back to the working
  instrument. The crop is a CSS selector in that file, not a pixel box, so a
  new row in wichaa's header does not break it — and the importer refuses a
  blank frame rather than shipping a white square. Do not add another local
  moon drawing. Interim by design: the destination is an animated preview in
  the widget picker and the real widget running compactly on the reader's page.
- **Placeholders only where they help.** `wat.svg` / `ant.svg` belong on a
  place's OWN page, beside the ask for a photograph. They do NOT go in grids:
  twenty identical temples on the front page said nothing about twenty
  different places. A card with no photograph gets `.textonly` and gives the
  space to its words. The placeholder is never published as a schema.org
  `image` — that told crawlers a shop's picture is a line drawing of a temple.
- **Temples are never ranked against each other.** `/merit.html` numbers nine
  stops because a walk has an order, and says in words that the order is the
  shortest way round and not a ranking. Royal grade appears because the Sangha
  assigned it, never as a reason one temple leads. The พระประจำวันเกิด strip is
  "what to look for at any temple" — pairing a weekday with particular temples
  is not in the tradition and is not ours to invent.
- `importers/routing.py` is a second implementation of the routing in
  `build.py`'s plan JS. They must agree, above all on `oneway` binding ride and
  not foot, and on the snap walk-in being added at both ends.
- **The line on the plan map is the journey in the number beside it.** A stop
  snaps part-way along an edge, so a leg starts and ends with a PIECE of a
  road; `route()` cuts those pieces in (`cutEdge`) and returns a path even when
  both stops sit on one edge. Draw only the junction chain and a 1.8 km walk
  comes out as 280 m of road with a straight line over the rest, and a
  same-edge leg draws nothing at all while still reporting a distance. The
  `#8a7a62` stub means one thing only: the walk in from the pin to the road.
- **A stop more than `FAR_FROM_ROAD` (100 m) from any road in the graph is not
  really on the network** and its leg says so on the page, with a link out to
  OSM. วัดเมืองลัง is the one on the merit rounds: 450 m from our nearest
  junction where OSM has a footpath 10 m away, so a 4.3 km walk read as 916 m.
  Extending the road crawl there is the real fix and needs her go-ahead.
- **Moat and gates on the plan map, by rule, not by luck.** If a side of the
  ring crosses the frame it is drawn AND named; every gate or แจ่ง corner
  inside the frame is drawn AND named, in both languages; a frame wholly inside
  the walls says so in words. The nine come from `_moat_crossings()` reading
  the catalogue's own records — never a hand-typed list of gate names.
- **A place is shown under both its names, never one instead of the other.**
  `name_pair(r)` resolves the pair — Thai from `nameTh` or from `name` when
  that is the Thai one, Latin from `nameEn` or from `name` — and everything a
  reader sees goes through `name_bi()` (markup), `name_text()` (alt, title,
  aria, share) or `name_th()`/`name_en()` (inside a sentence in one language).
  `name_of()` stays the single canonical string and must not change shape:
  `place_slug` reads it, and a slug that moves is a 404 after deploy.
  A listing row carries `data-n` (both, so either language filters it) and
  `data-ne` (Latin alone, so ก→ฮ in English-only mode sorts by the name on the
  screen). `index.json` carries Thai in `n` and Latin in `e`; search matches
  the two concatenated. JSON-LD keeps one `name` and puts the other in
  `alternateName`; per-place `.json` publishes the resolved pair as `names`.
  `bi()` puts `lang=` on each half — the page element says `lang="th"`, so
  without it every English gloss on the site is read aloud in a Thai voice.
- `data/curated/names.json` — names a crawl left empty. Same rule as
  `honours.json`: nothing enters `names` without a fetched source URL, leads
  wait in `unverified` and are never rendered, and a curated name only ever
  fills an empty field. No machine transliteration: an absent English name is
  a smaller error than an invented one. Run `importers/import_all.py` for a
  change here to reach `data/canonical/`.
- `importers/build_merit.py` folds a second spelling of a temple only when the
  looser key and the ground both agree (`loose_name` + `SAME_PLACE_M`). A round
  of nine that visits one temple twice is eight.
- `node tests/test_plan_routes.js` after the build, with the others. Set
  `MD_DOCS` to a scratch build if somebody else is holding `docs/`.
- Run `tests/test_publish_gate.py` after the build and before `git add docs/`.
- Every image says what it is FOR, not what it is. `tests/test_alt_text.py`
  fails a missing `alt`, an unlabelled `role="img"`, and a label that is only
  the medium ("QR code", "map", "chart"). Use `bi_text()` for alt and
  aria-label — `bi()` returns spans, and markup inside an attribute gets read
  out loud. Match both quote styles when scanning HTML: the moondial sibling
  emits `role='img'`.
- Never run two builds at once. Both wipe docs/, and the loser silently keeps
  the other's older pages — count a nav link against the page total to catch it.
- Public pushes only as NaNoBotCo, and only when the user says publish.
- Network crawls (Overpass etc.) need the user's go-ahead first.
