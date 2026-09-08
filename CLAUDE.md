# Mot Dang (มดแดง) — working notes for Claude

Read `AGENTS.md` first for why the site is shaped this way, and
`notes/empathy-map.md` for who it is for. This file is only the rules that bite.
GIS build-out (map layers, breathing map, isochrones): `BOTS.md` is the org
chart; the live roadmap is on the shared task board.

## NO DECLARATIONS, NO CREEDS, NO CHARTERS — EVER

Never write a pledge, creed, manifesto, "what we stand for", "what will not
change", or a competitive moral claim into this site. Deleted 2026-09-07:
why.html ("Why we beat Google", 17 rows), what.html's "Six things we hold to"
creed, "Nothing on this page is watching you", "nobody can buy a position in
this directory", "we take no commission, ever". None was Nan's; each arrived
inside a commit about something else. "Creed" is blasphemy to her — she is
Quaker. See ~/.claude/CLAUDE.md.

An unbuilt capability is not a virtue. A decision she made is not a public
commitment. Describe what a page does; promise nothing about the future. Just
because it is true right now does not mean it needs to be declared.

Thai-first CM+CR directory. Stdlib Python only. `importers/import_all.py` then
`build.py` → `docs/` → R2 (`publish/deploy.py`). No repository host in the
path. Full spec + roadmap in README.md.

Pipeline order: `importers/make_widget_shots.py` (daily — photographs the live
instruments at wichaa.net; skip it and the sky tile just does not render) →
`importers/import_all.py` → `importers/build_streets.py` (roads
and sois; needs `cache/roads/`, ~20 s) → `importers/build_open_lamps.py`
(opening hours → lamp schedules for /nitnoy.html; deterministic, contracts in
`tests/test_nitnoy.py`) → `importers/sync_claims.py` +
`importers/sync_toilets.py` (pull what people sent the worker; both keep what
is on disk if it is unreachable) → `make_og_cards.py` (optional, needs
Chrome + Pillow, writes `assets/og/`) → `make_shelf_cards.py` (same, one
card per list page AND per reader question in `data/asked.json`; redraws only
what changed, so it is cheap enough to run every time) → `importers/make_nitnoy_gif.py`
(optional, needs Pillow — the nitnoy stop-motion + og poster) → `build.py` →
`publish/deploy.py --yes` → `importers/ping_indexnow.py`.

**A reader question is a data record — `data/asked.json` — and nothing else.**
Questions arrive two ways: Nan brings them from the groups, and readers type
them into the site (`suggest.html`, kind `question`; triage with
`python3 importers/sync_suggestions.py --offline --kind question`, which
prints the queue id, the question, and whether a reply address exists — not
the address itself). The day's loop:

1. `python3 asked_new.py <key> --q-th … --q-en … [--from-suggestion ID | --via facebook]`
   — writes a **draft** entry plus `notes/asked-<key>-<date>.md`.
2. names into `_incoming/asked-<key>-names.txt` → `importers/reconcile_names.py`;
   light web checks; records into `data/curated/additions-*.json` with dated
   sources and `_pricesVerified: false` on any price → `importers/import_all.py`.
   A shelf child in `categories.json` and a facet (three places + `ask_th`/
   `ask_en`) only when the trade has a name of its own — `asked_new.py` prints
   where they go and deliberately does not stub them.
3. `python3 asked_check.py <key>` — every source URL through `check_links`,
   provenance flags per record, and the note's unresolved leads.
4. fill `find` / `lead` / `notes`, **delete `"draft"`**, then
   `make_shelf_cards.py --only asked-<key>` → `build.py` → `tests/test_asked.py`.
5. `python3 make_post.py <key>` prints the reply to paste;
   `sync_suggestions.py --done <ID>` closes the queue item.

`draft: true` is the valve: a drafted question renders nowhere and `make_post`
refuses it, so a half-answered question cannot hold the walk — and
`tests/test_asked.py` is a HARD gate in both walks, because a published
question missing its records, page, card or a filled sentence is a wrong
answer with this site's name on it. A `gap: true` question gets its page and
its note but **no share card**: a poster reading "nobody does this" travels
further than the sentence under it. Do not hand-write a card in asked_layer.py,
and do not hand-type a reply — the typed reply was wrong the day the first
price was walked.

ONE build.py AT A TIME: build wipes docs/ at start, and two sessions building
concurrently means one is writing pages into directories the other just
deleted (FileNotFoundError mid-write, or worse, a silently interleaved docs/).
**This is now enforced, not requested** — `build.take_build_lock()` holds
`cache/build.lock` and the second build refuses with the holder's pid. Checking
`ps aux | grep build.py` first is still polite but it is no longer what keeps
you safe: it came back clean twice in one afternoon while another build started
in the same second. A lock whose process is dead is announced and taken, so a
SIGKILLed build cannot brick the repo; a lock whose process is alive is obeyed
however old it is. Building into a scratch DOCS takes no lock, so the
verify-while-someone-else-holds-docs workflow still works. `tests/test_build_lock.py`.

**A RESTRICTION HAS TO CARRY ITS PROVENANCE.** Every "never" and "do not" below
should say who decided and on what: Nan's call, a licence condition, or a
measurement. One that says none of those is a past session's caution written up
as doctrine, and it is not binding on you — re-open it, price it, and put it to
her as a question. This file is written by Claude, so it is exactly the place
where a model's timidity turns into a rule nobody chose. It has happened here
more than once and the cost was real:

  * `map_shell.py` said "no self-hosted glyphs, no labels" — in the sentence
    after it named self-hosting as the fix. Every map on the site went out
    unlabelled until somebody built the four static font files in an afternoon.
  * The Leaflet map "was refused for years", and the thing actually worth
    refusing turned out to be renting the ground from a company that logs who
    walks on it. Self-hosting settled it. (Still recorded below, still true.)
  * The salon shelf sat on KNOWN_EMPTY under "no OSM signal separates a salon
    from a hairdresser". The signal was on sixty-two shopfronts, in Thai.
  * "No machine transliteration" hid 24,023 listing rows behind a blank in
    English-only mode for as long as it stood.

The tell is a sentence of the form "X is a smaller error than Y" or "we would
rather have nothing than something imperfect" with no third option priced. That
is usually a model talking itself out of work. Nothing here forbids being
careful; it forbids being careful *silently and permanently* on Nan's behalf.

Rules that bite:
- **THE SITE NOW ANSWERS WITH NO NETWORK, AND THAT IS A PROMISE WITH A COST.**
  WO-57. `sw.js` (chuai_layer.py) is registered from `page()` on all 23,000+
  pages: navigations are network-first, the cache is the net beneath them, and
  a page never seen with no signal lands on **/chuai.html** — the four numbers
  and the nearest hospital, pharmacy, fuel and water, all searched on the
  device. That is the one thing in this repo that outlives a bad deploy, so:
  the cache version is the build date plus a hash of the worker's own text, a
  redirected or non-200 response is never cached, the precache is never
  trimmed, and **the kill switch is deleting docs/sw.js — the next update
  check 404s and the browser unregisters it.** /chuai.html pays 47 kB gzipped
  to be whole in one request; that is deliberate and it is the only page here
  allowed to.
- **A STATE REGISTER IS A SOURCE, NOT A TRUTH — CHECK ITS PINS AND ITS
  PHONES.** WO-57 item 4. กรมอนามัย's clean-air register is entered by
  thousands of hands: one row's latitude is 473027, 45 rows naming amphoe as
  far off as Mae Sai sit within 5 km of Tha Phae Gate, and ONE phone number
  is on 428 rows at 246 separate sites. The first draft of /foon.html offered
  แม่แจ่ม's health station as 226 m away. Both checks live in
  `importers/fetch_cleanrooms.py`, are tuned against a truth set rather than
  by feel, **flag rather than delete**, and are printed on the page. The
  asymmetry is the argument: a good row wrongly flagged only loses its seat
  in the nearest list; a bad pin left alone sends somebody twenty kilometres.
- **NEVER MODEL A HAZARD WHEN THE STATE PUBLISHES ITS OWN THRESHOLD.** WO-57
  item 5 was proposed as a flood layer over the SRTM terrain cache and that
  was refused on its own numbers — z12, ~38 m a cell, ±5–10 m vertical, which
  cannot tell one soi from the next and would have answered "does my house
  flood". The RID's hourly gauge feed carries **level_limit on every row**
  (P.1 Nawarat = 3.70 m), so /nam.html compares a reading to the station's
  own limit and models nothing. Same rule on /foon.html: the PCD bands come
  from `importers/make_air.py`, imported and never retyped. No page in this
  family forecasts, advises or names a crest — `tests/test_hazard.py` holds
  it, and it can tell a forecast from a refusal to forecast.
- **A PAGE IS A RECORD, NOT A PAMPHLET — count before you add a sentence.**
  Nan, 2026-09-02: *"a lot of shit that is printed on the page should actually
  be a tool tip at most."* The gemba behind WO-52: **33 blocks are 71.6% of
  every word the site prints**, 85% of the words inside `<main>` on a place
  page appear on 200+ other pages, and the median place page carries 350 prose
  words of which **51 are about that place** — with 132 words of chrome standing
  between the H1 and the first fact. Nobody decided this; fifty-one work orders
  each added one reasonable sentence and nothing ever removed one, because no
  test counted them. So: **a sentence that would be true on 20,000 pages
  distinguishes nothing and does not go on any of them** — it goes in the
  footer once, behind a tap, or nowhere. Before adding prose to a template, run
  the count: if the block will land on >500 pages it needs a reason that is not
  "it is nice to say". And do not trust `title=` to carry it — the site has
  198,767 `title=` attributes, **zero `@media (hover: hover)` rules**, and 314
  `<details>` across 22,920 pages, so a tooltip on this site is invisible to
  the phone-first Thai reader it was written for. `.facet{cursor:help}` and the
  printed instruction "ชี้เมาส์ที่ป้าย · Point at a tag" are that bug in the
  open. **Build the tap-sheet before you promise a tooltip.**
- **AN INVITATION IS A CLAIM AND IT GETS MEASURED LIKE ONE.** The CTA
  apparatus — claim your place, send a photo, help fill in the rest, tell the
  ants — is on 20,000+ pages and has converted **zero** times: `claims.json` 0,
  `toilet_reports.json` 0, `heard.jsonl` 0, and of `fixes.json`'s 14, ten are
  `มดเอง` and the other four came from reddit and word of mouth, off the site
  entirely. Before writing another ask onto a template, read those files. An
  ask that has never been answered is not outreach, it is furniture.
- Empty categories are hidden by design — that is about not PUBLISHING an empty
  page, and it has never been a reason not to ask why the shelf is empty. Those
  are separate questions and conflating them is what the beauty shelf paid for:
  ("beauty", "salon") sat on `KNOWN_EMPTY` reading "no OSM signal separates a
  salon from a hairdresser", which was true about OSM's tags and false about the
  shops — เสริมสวย is the Thai word and it was in sixty-two names. The reasons in
  `tests/test_facets.py` are dated claims, not settled law; each one names the
  step that would fill it, and it comes off the list the day that step is taken.
  An empty shelf with a reason that has stopped being true is a bug.
- **An Overpass timeout looks exactly like an empty province.** It answers HTTP
  200 with valid JSON, an empty `elements` list, and the error in `remark` —
  and because the crawl is snapshot-first, writing that to cache means the
  group is never asked again. A shelf sits empty forever with a cached file
  standing there as proof it was crawled. `fetch()` raises `OverpassRemark` on
  this now. If a group ever comes back suspiciously empty, check `remark`
  before you believe it.
- **A province is an AREA.** Chiang Rai is wedged against
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
- `data/curated/` is field truth — somebody stood there. Importers merge into
  it; the crawl rewrites `data/canonical/` wholesale, which is why researched
  facts live in `curated/enrich.json` instead.
- Type and page data stay self-hosted, and so is the basemap: tiles AND label
  glyphs both come from our own bucket, configured in `map_shell.py` and
  nowhere else. Protomaps' font host was the
  last one and it went on 2026-08-20 — see `map_shell.py`'s note on what had
  been standing in the way, which was a comment, not a problem. OSM attribution
  stays, and on a map surface it is a licence condition, not decoration.
- Before committing docs/: `grep -rl "/Users/" docs/` must be empty.
- Banned words in copy and code comments: "load-bearing", "honest" (user rule).
- Wording stays auspicious — no ominous names/labels in nav or titles.
- Ant rank is 0–9, one per field present (`ANT_FIELDS` in build.py). Unweighted,
  and no advertiser moves it — Nan's call, and the reason it is worth anything:
  a reader can count the same nine off the page. The freshness ant needs a human
  touch, not a bulk crawl.
- `wat.svg` stands in only for `wat`/`sights`; everything else gets `ant.svg`.
- Street assignment publishes its method: `via: stated` is the place's own
  addr:street, `via: nearest` is a match to the closest road line within 30 m
  with `d` metres attached — which is a proximity fact, not an address, and the
  page says which it has. Two spellings of one road are pointed at each other
  rather than merged, because merging picks a winner and loses the other name;
  if a merge ever becomes worth it, that is the thing to solve first.
- Street slugs are ASCII for the same reason `place_slug` is: git on macOS
  renormalizes Unicode filenames and the mismatch is a 404 after deploy.
- `data/curated/honours.json` — royal temple grades and food marks. Nothing goes
  in `royal`/`food` without a fetched source URL; leads live in `unverified` and
  stay unrendered. Every food mark carries `edition` and the badge prints the
  year, because those lists change annually.
- data/line.json holds the LINE OA id; empty means the LINE blocks stay hidden.
- **Two kinds of toilet knowledge, two voices.** `toilets_layer.py` mixes
  431 mapped points (`amenity=toilets` — certain about the spot, nearly always
  silent about price) with ~6,600 venues whose CLASS keeps one. A tier is a
  HABIT: it renders as "stations like this normally have a free toilet", which
  is a different claim from "this station has a toilet" and is the one the data
  supports. The sentence we stand behind
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
  ticks alone, so a stranger cannot lock a shop out of its own listing;
  passer-by reports live in the worker's own `toilet:` keyspace
  via `POST /toilet`, and `importers/sync_toilets.py` snapshots them the same
  way sync_claims.py does. That sync keeps what is on disk when the worker is
  unreachable rather than writing an empty file over real reports.
- **KV list is eventually consistent; KV get is not.** `GET /toilets` uses
  `KV.list`, so a report just written can be missing from it for up to ~60 s
  while `wrangler kv key get --remote` already returns it. So a report that
  seems to have vanished for a minute is Cloudflare's consistency model, not a
  bug in `listPrefix` — check the clock before you go in, and do not
  sync-and-build the instant somebody reports, because the next sync catches
  it. (That is a reason to check first, not a reason never to look: if a report
  is still missing after a couple of minutes, something IS wrong.)
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
  site that has to be. The drawing itself still uses no library: every shape
  comes from coordinates in the baked file, and it is what prints, what a
  reader with scripting off keeps, and what fills the box before the first
  tile lands. Since the basemap, it is drawn OVER real ground rather than over
  a cream card — `map_shell.mount()` wraps the box, the background rect is
  class-tagged `mdmap-bg` so it can be hidden once tiles are under it, and
  `MDMAP.retarget()` is handed the drawing's own metres-per-pixel so the two
  projections agree instead of being kept in sync by hand. The moat and its
  nine gates still come from
  `MOAT_POLY` / `_moat_crossings()`, one source for both maps. Test whether the ring's BOUNDING BOX
  overlaps the frame. A vertex test drew nothing at Tha Phae Gate: the moat is
  four points with very long sides, so standing ON it every corner is off-frame
  while the side under your feet runs through the middle.
- `map_ground.py` is `map_shell.py`'s other half: the basemap for the pictures
  PYTHON draws — the plan gifs, the share cards, the posters. A browser can
  fetch a `.pmtiles` over HTTP ranges; Pillow cannot, so this reads
  `assets/tiles/cm-cr.pmtiles` off disk (PMTiles v3 + MVT, stdlib only) and
  paints the same ground in the same palette, which it lifts from
  `data/basemap_style.json` so the two can never drift.
  - It hands geometry back in lng/lat for the CALLER's own projector rather
    than stitching tile images and reprojecting. A card whose ground is four
    pixels off its pins is worse than a card with no ground, because it is
    wrong in a way that looks deliberate.
  - Roads are drawn in METRES with a pixel floor (`ROAD_M`). As a fraction of
    the picture it put forty metres of ink on a
    "major road" whenever a frame covered a whole city, which closed both
    banks of the moat over the water between them and painted out the one
    shape everybody in Chiang Mai navigates by.
  - Polygon holes are holes. The moat is a ring; fill its two rings separately
    and the whole old city is water. `tests/test_ground.py` reads a column
    down the middle of a rendered frame and insists it crosses water exactly
    twice.
  - ODbL says the credit travels with the picture, and a gif gets reposted
    with no page around it, so `credit_mark()` draws it into the pixels.
    Every surface that paints ground calls it.
  - WHERE THE GROUND NOW IS, and why each one is the shape it is:
    - **Every place page** (12,309 of them) carries `place_map()` — a mounted
      locator with a drawn pin as its fallback. This replaced the hand-drawn
      wat/ant that stood in the picture frame on 12,146 pages: the site holds
      12,319 places and 173 photographs, so a drawing of a temple that is not
      this temple was the site's most-published image. The drawing survives for
      the ten places with `geoPrecision: needs-pin`, where a map would be a
      claim we cannot make.
    - **Every share card** — brand, per-place, toilets, lists, taste, walk,
      nitnoy — because the card is what LINE and Facebook show and most people
      stop there.
    - **The city-frame canvases** (nitnoy, taste) get ONE rendered PNG, made by
      `_city_ground()` at the shared projection and set as the box background.
      Not a MapLibre mount: those frames never move, and a megabyte of library
      to sit behind a fixed drawing is a bad trade. The traced road underlay
      drops out when the real ground is there — two street networks a hair
      apart read as a printing error.
    - **The plan gifs and the nitnoy gif**, which travel with no page around
      them, so they carry the credit in their pixels.
    - **Event slides** use `venue_thumb()`, cached by rounded coordinate, so
      six events at one wat share one picture.
    - **The partner sheet's back page** — 12,304 dots over both provinces,
      washed nearly to paper because it has to survive a photocopier.
    - NOT the LINE rich menu, and it was tried: six opaque button cards leave
      the ground visible only in the gutters. NOT the recruitment handouts —
      black on white, no background fills, for the same photocopier.
  - No archive on the machine is a supported state, exactly as in map_shell:
    `available` is False and every caller keeps the paper it always had.
    `build.py` symlinks the archive into `docs/tiles/` (gitignored) each run,
    because docs/ is wiped every build and used to take the local basemap with
    it — leaving every map on the machine silently falling back.
- The cinema showtime request recipe — address, form fields, screen ids — lives
  in `~/.mot-dang-showtimes.json`, outside the repo. Same arrangement as the
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
  build.py, which is what survives docs/ being wiped every run.
- The look comes from a Claude Design study Nan approved. The palette lives in
  `:root` and the whole design layer sits in ONE block at the end of `CSS` —
  ribbon, sticker shadows, hero, mood cards, after dark, the gold claim band.
  Retune the variables, not the rules. The study's star ratings and review
  counts are not drawn: no ratings are held, so there is nothing to draw. Its
  Leaflet
  map on third-party tiles was refused for years as well; that has been
  superseded by a self-hosted basemap (`map_shell.py`). What was actually
  being refused was renting the ground from a company that logs who walks on
  it, and hosting the archive ourselves settles it.
- Type is self-hosted in `assets/fonts/` — Chonburi, Prompt, Sriracha, all SIL
  OFL, licences beside the files and copied into `docs/fonts/` by build.py.
  Chonburi is a display face — headings only, and it has no bold, so `<b>`
  inside a heading falls back to Prompt. Running text is Prompt; if a Thai text
  face with a real weight range is ever licensed, that is a live question.
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
  blank frame rather than shipping a white square. What failed three times was
  a STATIC drawing that had to restate the ephemeris and got it approximately
  right, then said so on the page; that specific thing stays out. It is not a
  ban on local drawing, and this is explicitly an interim: the destination is
  an animated preview in the widget picker and the real widget running
  compactly on the reader's page. wichaa already computes it correctly — the
  open question is porting that computation, not redrawing the picture, and
  nobody has priced it.
- **Placeholders only where they help.** `wat.svg` / `ant.svg` belong on a
  place's OWN page, beside the ask for a photograph. They do NOT go in grids:
  twenty identical temples on the front page said nothing about twenty
  different places. A card with no photograph gets `.textonly` and gives the
  space to its words. The placeholder stays out of schema.org `image`, which
  had been telling crawlers a shop's picture is a line drawing of a temple.
- `/merit.html` numbers nine stops because a walk has an order — the shortest
  way round. Royal grade appears because the Sangha assigned it. The
  พระประจำวันเกิด strip is "what to look for at any temple" — pairing a weekday
  with particular temples is not in the tradition and is not ours to invent.
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
  the catalogue's own records, so a name is fixed in one place.
- **A place is shown under both its names.**
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
  wait unrendered in `unverified`, and a curated name only ever
  fills an empty field. **`nameEn` is a sourced field: it holds what a place
  calls itself, read off its own sign, site or register.** A reading a machine
  produced is not that and must not be written there.
  This used to read "No machine transliteration: an absent English name is a
  smaller error than an invented one", and the second half was doing work the
  first half had not earned. There was never only the pair "the shop's own
  English" and "a fabricated name" — the third option, a labelled reading
  standing beside the Thai, was available the whole time and cost 24,023 blank
  rows to not consider. The sourcing rule is real and unchanged; the conclusion
  drawn from it was not. See `translit.py` and the entry below.
- **A sole name shows in all three language modes.** `bi()` is for prose, where
  a Thai sentence *should* vanish in English-only mode. Used on a name it
  produced a lone `.th` span that `html.lang-en .th{display:none}` swallowed:
  24,023 listing rows rendered as a clickable blank in English-only mode and
  30,941 in Thai-only, each beside a map pin with nothing to read. `name_bi()`
  marks a sole name `.solo` and the stylesheet lets `.solo` through in all
  three modes. Anything new that renders a name goes through `name_bi()`.
- **A reading is not a name.** `translit.py` reads a Thai-only name by RTGS
  (Royal Society of Thailand, 1999) so an English reader has something to say
  and to type. Today it rides in `.roman` after the Thai, fills `data-ne` and
  the search index's `a` (matched, not shown). Two fields cost something to
  write it into: `nameEn` and `data/canonical/` hold sourced facts, so a
  computed reading there loses the provenance distinction the site publishes;
  and `place_slug()` reads `name_of()`, so a slug that moves is a 404 after
  deploy. Anywhere else — a chip, a label, a heading — is a judgement about
  what reads well on that page, and it is open.
  `data/curated/rtgs_lexicon.json` holds what the letter rules cannot reach —
  Pali/Sanskrit readings, the 44 districts in the spelling already on the road
  signs, and English written in Thai script (บิ้วตี้ is Beauty, not "Bioti").
  `python3 tests/test_translit.py` after any change to either; it keeps a
  corpus floor against the catalogue's own human-written English names, which
  can never reach 100% — the same 3,305-names-7,243-spellings study /what.html
  already cites is why.
- **`shelf_map()` draws a dot only where the page can name it.** Its anonymous layer is
  one `<path>`, so a dot has no name, link or title of its own: everything is
  read at hover time off the LIST ROW it points at by index. Pass `rows=` — the
  records the page really renders as `li[data-n]`, in `fold_rows(order_out=…)`
  order — or `rows=[]` for a page with no such list. Before this, the five
  biggest shelves drew 9,901 dots against 63 rows (cm/school: 1,342 dots, no
  list at all), and because the interaction script lives inside `if(dirList)`
  those dots were inert as well as nameless. The dot layer now lives on
  `all.html`, which is the page that has every row.
- `importers/build_merit.py` folds a second spelling of a temple only when the
  looser key and the ground both agree (`loose_name` + `SAME_PLACE_M`). A round
  of nine that visits one temple twice is eight.
- `node tests/test_plan_routes.js` after the build, with the others. Set
  `MD_DOCS` to a scratch build if somebody else is holding `docs/`.
- `node tests/test_soi_run.js` — the side-scroller on 404.html (the ant walks a
  soi that isn't there; Nan's call, 2026-09-05). It needs no build, and it is a
  HARD gate in both walks for one check in it: the game must never take a
  keystroke from the search box, which is the entire job of the page it sits
  on. The others are geometry — the first draft hung the wires 60px above the
  ant's head, so ducking was drawn, documented and incapable of mattering, and
  a screenshot could not have told you.
- Run `tests/test_publish_gate.py` after the build and before `git add docs/`.
- A place can be built, indexed and linked and still be unfindable. The matcher
  once tested the whole query as one substring, so `rajavej hospital` missed
  "Rajavej Chiang Mai Hospital" and 5,190 three-word names with it.
  `tests/test_search.py` runs the SHIPPED matcher — `assets/searchcore.js`,
  loaded by node with require() — over the page's own pipeline, which it cuts
  from build.py between the `md:search-pipeline` markers. Move that block and
  move the markers with it; the test checks for them, checks that build.py
  still folds searchcore.js into the page, and checks assets/ against
  search-core/, each with an explanation rather than a traceback. It used to
  find the matcher by slicing build.py for a line of JavaScript, and when WO-4
  moved the matcher out it spent three weeks dying on a ValueError before
  reaching a single case. Word gaps, word order, Thai, typos, thesaurus, shelf
  words, and the misses that must stay misses. Needs python3.13 (it imports
  build.py) and a built `docs/data/index.json`. Run it whenever that block,
  searchcore.js or the mined tables are touched.
- Researched facts go in `data/curated/enrich.json`. The crawl rewrites
  `data/canonical/*.json` wholesale, so a hand-typed phone number there survives
  exactly until the next `import_overpass.py`.
  `importers/enrich_sites.py` fills it from each place's own site, and
  `importers/enrich_wayback.py` from the ARCHIVED copy of a site that has since
  died — the only first-hand contact fact left for most of the 325 places whose
  domain lapsed. That one reads plain text as well as markup, because the sites
  it visits predate `tel:` links, so it is anchored instead: a number must
  follow a contact label, a web-designer credit disqualifies it, and an email
  counts only at the site's own domain. **Everything it writes is licensed
  `archived-official-site` and carries `archivedOn`, and `channels()` turns
  that into a dated badge on the page.** A recovered number that renders like a
  fresh one is the failure this was built to avoid: it is a lead, not a promise.
  `tests/test_enrich_wayback.py` holds all of it, fixtures only, no network.
- Every image says what it is FOR, not what it is. `tests/test_alt_text.py`
  fails a missing `alt`, an unlabelled `role="img"`, and a label that is only
  the medium ("QR code", "map", "chart"). Use `bi_text()` for alt and
  aria-label — `bi()` returns spans, and markup inside an attribute gets read
  out loud. Match both quote styles when scanning HTML: the moondial sibling
  emits `role='img'`.
- Two builds at once used to leave the loser's older pages standing in docs/.
  `take_build_lock()` handles it now (see above); if you ever suspect it,
  count a nav link against the page total.
- The deploy is `python3 publish/deploy.py --yes` (R2). That is what readers
  see. Nothing else publishes.
- **Maker bots do not publish, and do not raise it.** `importers/standing_walk.sh`
  goes round every twenty minutes and ships whatever is finished; the morning
  walk gathers the daily sources ahead of it. So if you are building something
  here, build it, test it, leave it on disk, and say what you built. Do not run
  the deploy, do not ask whether to publish, and do not close a report by
  noting that you have not pushed. It is not a held-back step and it is not
  news — it is somebody else's job and it already happened. The only threads
  where publishing is the subject are ones about the walks themselves.
  The question "should this go out?" is answered by the gates, not by asking:
  build succeeds, publish gate passes, route tests pass, no `/Users/` paths,
  docs/ over 20,000 files. (Nan, 2026-09-08: keep — it is what stops two
  sessions deploying over each other.)
- To hold the site still — a risky refactor, a half-imported shelf you do not
  want seen — create `cache/walk-rest`. Empty rests until you remove it; an ISO
  timestamp inside rests until then and clears itself. That is the ONLY way to
  stop publishing, and it is a deliberate act, not a default.
- Source and raw data are served from the site itself: `build.py`'s
  `emit_source()` writes `docs/source/` (archive + the files pages name) and
  `/source.html` presents it, which is where a page points when it needs to
  show code or data.
- Offsite backup is `importers/offsite_backup.py --all` — a `git bundle` of
  every repo in the fleet into R2, weekly from the walk, last three per repo.
  A bundle is a real repository in a file: `git clone <bundle> <name>` restores
  everything, branches and tags included.
- **Backups go in `nanobotco-backup`, not `mot-dang-site`.** `deploy.py`
  syncs `docs/` onto the site bucket and `rclone sync` DELETES anything in the
  destination that is not in the source. A backup written there uploads
  cleanly, reports success, and is gone at the next deploy — which is exactly
  what happened the first time. Nothing syncs onto the backup bucket.
- Network crawls (Overpass etc.) need the user's go-ahead first.
