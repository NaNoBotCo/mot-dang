# Push queue

What is waiting to go out, and what shipped last time.

## Waiting

**Uncommitted — /toilets.html, the one question asked under a clock.**
/walk.html says how thick the city is with toilets; this says where one is,
now. Same points, opposite instrument.

The finding that shaped it: of 344 mapped toilets in Chiang Mai, **exactly one
records what it charges**, and only 18 admit a fee at all. The 5-10 baht price
is not in OSM to be crawled — it is field truth or nothing, which is why three
report doors ship with the page rather than after it.

Coverage goes from 431 pins to **1,310 places anyone may walk into** (fuel 259,
wat 591, market 113, park 107, university 69, museum 58, hospital 57, mall 37,
terminal 19) plus **5,313 that oblige a customer**, from an 11-tier class model
in `data/toilets.json`. A tier is a habit, worded as one, and always loses to a
verified point or a field report. Exclusions are written down with reasons —
convenience stores are not a tier, because Thai 7-Elevens do not keep a
customer toilet.

Also: the `toilet` facet had `appliesTo: ["convenience"]` only, so the question
was never once asked of 4,153 food records or 398 bars — new `sitdown` facet
set fixes that (614 food records picked up facets that previously rendered
nowhere), and `import_fixtures.py` now filters facets to the keys a record's
own set defines, which two sets made necessary.

**Worker DEPLOYED 2026-08-03** on her go-ahead — version
`ed9a38bf-1e20-4748-8d62-302286b21b95`, account annika@pfau.haus. `POST
/toilet`, `GET /toilets` and the LINE toilet branch are live; `/claims` checked
unregressed. Tested end to end against the deployed worker: bad report word and
bad place id both rejected, three real reports written, `seen`/`agrees`
counters correct, `sync_toilets.py` → build → the row rendered "checked by a
person · free" where its sit-down tier would have said "buy something". Test
key then deleted from REMOTE KV and the whole pipeline re-run clean — 0 rows
carry a report in the shipped build. Add `python3 importers/sync_toilets.py`
to the pipeline before `build.py`.

Plus a **which-way panel** above the list: your dot centred, the ten nearest as
tier-coloured emoji pins, labelled range rings, north marker, and the moat and
its nine gates from `MOAT_POLY`/`_moat_crossings()` when any of it is in frame.
Tap a pin, its row highlights. Drawn in the browser (it has to centre on the
reader) but still no tiles and no library.

Verified in a real browser this time (own server on 8873, the 8643 slot was
held): sort monotonic, four filters, lazy customer file, tick failure path,
landmark fallback, tile square and not overflowing, pin→row tap, and the moat
appearing at Tha Phae but correctly absent from Chiang Rai. Full build 11,813
pages; publish gate, facets, alt-text, errands and plan-routes all pass.

**Uncommitted — the plan map now draws the walk it charges for, and the moat
names itself.** From an audit of the ten ไหว้พระ ๙ วัด rounds run against the
shipped `docs/md.js` and the real graph (80 legs, both modes).

Two rendering faults, both in `route()`, neither of which touched a distance:
the drawn line was only the junction-to-junction chain, so the piece of road
from a stop out to its first junction was left to a straight stub — **34 of 80
legs drew under 60% of their own ground, worst 280 m of an 1,846 m walk** — and
a leg with both stops on one edge returned `path:null`, drawing **nothing at
all while still reporting a distance** (4 of 80). `cutEdge()` cuts the end
pieces in; after: 0 and 0, and no distance moved by a metre.

Moat rule as asked: a side crossing the frame is drawn AND named (the label was
pinned to the ring's north corner, off-canvas on 5 of 10 → water, no name), and
every gate or แจ่ง corner in frame is drawn AND named bilingually from
`_moat_crossings()` reading the catalogue's own nine records. 58 gate labels
across the ten rounds.

One real data gap left, disclosed on the page rather than hidden: **วัดเมืองลัง
is 450 m from any road in our graph** where OSM has a footpath 10 m away, so a
4.3 km walk read as 916 m. Needs the road crawl extended at the north-east of
the box — her go-ahead.

**Names are bilingual everywhere now, not one language instead of the other.**
`name_pair()` + `name_bi/name_text/name_th/name_en` in build.py; every heading,
breadcrumb, listing row, card, related link, `<title>`, alt, aria-label, share
text, RSS item and merit stop shows both where the record holds both. Verified
in all three reading modes: **ไทย** gives วัดเจดีย์หลวงวรวิหาร, **EN** gives Wat
Chedi Luang, **ไทย + EN** gives the pair — that temple headed its own page in
English only until now. Searchable both ways (`index.json` `n` Thai, `e` Latin,
matched concatenated), sortable by whichever name is on the screen (`data-ne`),
machine-readable both ways (JSON-LD `alternateName`, a resolved `names` block in
every per-place `.json`, `nameTh`/`nameEn` in the geojson), and `bi()` now puts
`lang=` on each half so a screen reader stops reading English in a Thai voice.
`name_of()` is untouched, so no slug moves.

Also: `data/curated/names.json` (Chedi Luang / Chiang Man / Phan Tao / Si Koet
had no Thai name at all; each filled from the th.wikipedia title already in its
own record, with the URL) — this needed `importers/import_all.py`, so
`data/canonical/*.json` are regenerated: 4 nameTh filled, 0 records added or
removed, and the rest of that diff is the `facets` attrs the committed files
predated; `build_merit.py` folds a second spelling of a temple
(round nine was visiting วัดปันเส่า and วัดปันเสา(พันเสา), 22 m apart, so it
was eight temples) — `data/merit.json` regenerated, rounds 1–8 unchanged, 9 and
10 recomposed; `tests/test_plan_routes.js` guards all of it; the plan page's
"distances are straight-line" caveat was three months stale and now says what
the page actually does.

Wants a full `build.py` run before it goes out — docs/ is from 21:20 and knows
none of this. Everything above was verified against a scratch build
(`build.DOCS` overridden, 11,813 pages, 104 s) because another session held
docs/: `test_plan_routes.js`, `test_alt_text.py` (21,463 imgs, 0 missing) and
`test_publish_gate.py` (277 broken URLs on file, 0 linked, 0 path leaks) all
pass on it, as do `test_routing`, `test_moat_geometry`, `test_errands`,
`test_facets`. Then `node tests/test_plan_routes.js` with the rest.

**One commit, `1ec47f0fee` — toilets + drinking water join /walk.html; the
section is now a layer list** (a new walking map = one more entry). Toilets
from the fixtures harvest (329 sites, 118 in frame, ~13 a walk from the moat
centre — the dark core is the temple district). Water harvested fresh via new
importers/fetch_water_points.py (169 → 61 in frame, ~9 from the centre;
snapshot gitignored like all cache). Thin-layer caption triggers under 40
in-frame sites — neither needed it. walk.html = 4 maps, 940 KB, deliberate.
`git push origin main`, then `python3 importers/ping_indexnow.py`.

## Last push — 2026-08-02 (fifth), `8acb54f23e`

/walk.html live — ATMs and pharmacies as sites-within-a-~10-minute-walk on
TRUE network distance (foot-graph Dijkstra; moat crossable only at
bridges/gates, verified 242 m across = 562 m walked). ATM 263 sites from the
fixtures crawl; pharmacies harvested fresh (catalog held 29 — main crawl
never asked; new importers/fetch_pharmacy_points.py, snapshot gitignored, a
fresh clone runs it once). Frame/underlay/tracer hoisted shared across all
three maps; seven.html byte-identical across the refactor. Verified live
~60 s after push (walk.html copy + walk.json atMoatCentre 18/10). IndexNow
4,286 URLs, 200.

## Last push — 2026-08-02 (fourth), `74ba13be17`

Four commits, all from her review rounds on the seven map: the street
underlay from our own road graph (frame snapped to the crawled area; bands
painted once as even-odd rings so translucency doesn't compound); log bands
+ edge labels + scale bar; the store dedup (records within 25 m count once
— node-and-building doubles; old city 12 dots → 11 real stores, 387 → 383);
and the metric change that cured the urticaria — **sum, don't min**: the map
is now branches-within-a-~10-min-walk (800 m soft count, layers 1/2/4/8/16),
drawn as organic isopleths instead of per-branch bullseyes. Caption carries
~14 branches within a walk of the moat centre, edge median ~3, beside the
nearest-distance medians. Verified live ~60 s after push by cache-busted
fetch. IndexNow 4,285 URLs, 200.

**Rules worth keeping from this arc:** darkest = nearest/most (her standing
rule); for distance-to-X audits, audit the X set first (names catch what
brand tags miss; node+building doubles need a ≤25 m merge); frame a map
where the finding lives and label what lies beyond the frame; and when a
nearest-distance map reads as a rash, the cure is a density metric, not a
palette.

## Last push — 2026-08-02 (second), `3d7a8fd70f`

The seven map redrawn as the distance field itself, on her "more granular" —
marching squares over a ~110 m grid of distance-to-nearest-branch, layered at
250/500/1000/2000 m; every point in frame has a value, so granularity no
longer depends on where the catalog holds places. Verified live ~60 s after
push by cache-busted fetch (the sevclip markup and the เส้นชั้น copy both
serving). IndexNow 4,285 URLs, 200.

## Last push — 2026-08-02, `2530aca502`, 11,811 pages

Three commits: the two infographics from the map-ideas round (`c8c1afb2bd`),
the ledger, and the ramp flip at Nan's direction — **darkest = nearest**, her
standing rule now for any distance/density colouring here ("the ink sits where
the branches crowd"). Overlays had to follow the flip: moat outline + label
cream, branch dots white with a green ring, or they drown in the dark centre.

New live: `/watnames.html` (เชียง 2.1 กม. → ทุ่ง 11.8 กม.; 23 romanised-only
names excluded and said so), `/seven.html` (median 240 ม., 74% ≤500 ม., massage
151 ม. → wats 1,560 ม., the ~550 m contour map), `data/watnames.json`,
`data/seven.json`, the "เรื่องที่ข้อมูลเล่า" strip on stats.html, llms.txt
entries. Verified live by cache-busted content fetch ~60 s after push: both
pages, both JSONs, the flipped colours (#8F2E13 cells + cream moat stroke),
the stats strip. IndexNow took 4,285 URLs, 200 first try. All seven suites
green before the push, authors NaNoBotCo only.

## Last push — 2026-08-01, `4a42b00225`, 11,809 pages

Seven commits, held while other sessions worked and then sent as **one push** —
the previous round's two "Page build failed" errors came from three pushes
landing ninety seconds apart, not from anything in the content.

| Commit | What |
|---|---|
| `4fa766c4ad` | The CSS for a block that had shipped without it |
| `96875b82da` | Ledger |
| `02590f98bc` | The design study, ported |
| `a6076574dd` | ไหว้พระ ๙ วัด — nine-temple merit routes |
| `20aa8c5df7` | Real instrument photographs; placeholders demoted |
| `073c5a6f7e` | Errands as kinds, not names |
| `4a42b00225` | Ledger + the two rules the merit page runs on |

New with those: `importers/routing.py` (the road graph walked from Python, so
build-time work can bake real distances without shipping the reader half a
megabyte of graph), `importers/build_merit.py` → `data/merit.json`,
`/merit.html`, and `tests/test_errands.py`. `PLAN_MAX` went 8 → 9, because
ไหว้พระ ๙ วัด is nine stops by definition.

Verified live: `/merit.html` with ten rounds, ten maps, the not-a-ranking line
and the eight postures; the errand panel on `/plan.html`; `solveErrands` in
`md.js`; `.elsewhere`, `.cool`, `.meritcard` and `.planerr` all present in the
served stylesheet; every self-hosted woff2 answering 200; footer at 2026-08-01.
IndexNow took 4,283 URLs, 200 first try.

**Two things worth carrying forward.** The Pages API's `commit` field lags — it
reported the previous SHA while the new content was already being served, so
verify by fetching content, never by trusting that field. And `motdang.net`
serves a stale `md.js` to an un-busted URL for a while after a push: a plain
`curl` said the errand solver was missing when `?cb=` proved it was there and
byte-identical. Bust the cache before believing a file did not deploy.

**The guard from last time, run by hand this round:** collect every class the
HTML uses, compare against every stylesheet actually served — `docs/style.css`,
`docs/festivals.css`, and any inline `<style>`. 405 classes used, 384 styled.
The 21 without a rule are JS hooks (`.rand`, `.copylink`, `.fix`, `.submit`) and
tile modifiers styled through their parent — no repeat of the `.elsewhere` case,
where a whole block shipped with nothing to render it. Reading only one
stylesheet gives 33 false positives; read them all.

## Older waiting notes

**One commit, `4fa766c4ad`, held back at Nan's instruction — but it is a fix to
something already live, so it is worth pushing sooner rather than at leisure.**

`git push origin main`, then `python3 importers/ping_indexnow.py`.

The "read more elsewhere" block went out in `09ee7d2305` while the CSS rule for
it stayed behind in `build.py`. `docs/style.css` has no `.elsewhere` or `.cool`,
so the block is **live and unstyled on 862 place pages**. This commit is the
rebuild that makes the two agree. All six suites pass.

How it happened, since it will happen again otherwise: work in progress in the
working tree got swept into an unrelated commit by a concurrent session, and
`docs/` was committed from a build older than the `build.py` beside it. Nothing
checks that the built stylesheet still covers the classes the builder emits —
`build.py` and `docs/` can disagree silently. A cheap guard would be to collect
the class names build.py writes and assert each one appears in `CSS`.

## Scrub — 2026-08-01, history rewritten

The cinema showtime request recipe (the address, the form it takes, the screen
ids) had been published twice: as documentation in `data/sources.json` and as
working code in `importers/make_showtimes.py`. Both are now clean, and the
recipe lives in `~/.mot-dang-showtimes.json` outside the tree, on the LINE-token
arrangement. History was rewritten with `git filter-repo --replace-text` and
force-pushed; the tip tree came out byte-identical, so nothing on the site
changed.

Two things worth knowing next time:

- **Token-level redaction is not redaction.** The first pass replaced only the
  field names and the endpoint, and the surviving prose still read "POST to
  /[removed]/ WITH the slash" — enough to reconstruct it. The pass that worked
  replaced whole passages by regex, then the tokens.
- **A force-push does not delete anything from GitHub.** The pre-rewrite commits
  are still fetchable by full SHA and still hold the recipe. Purging them takes
  a request to GitHub Support, or deleting and recreating the repo. Until then
  treat the recipe as exposed — it was public for three days on a site that
  invites crawlers by name.

## Last push — 2026-08-01, `84a7d296c`, 11,807 pages

A gap-closing push rather than a feature one. Two commits.

| Commit | What |
|---|---|
| `d73ec33dd` | The four data files `llms.txt` promised and did not serve; `BUILD_DATE` |
| `84a7d296c` | The rebuild — 906 road pages as the catalog reached 10,673 records |

**What it fixed.** `llms.txt` named `data/streets.json`, `data/weather.json`
and `data/showtimes.json` under `motdang.net/data/`; all three answered 404,
because `build.py` never copied them out of `data/`. On a site whose stated
posture is that crawlers are welcome, a manifest pointing at missing files is
the one bug that undoes the posture. Every `/data/` URL the file names now
resolves — worth re-checking whenever a new one is added to `llms.txt`, since
nothing enforces the pairing yet.

`BUILD_DATE` had sat at 2026-07-29 through the 08-01 push, so all 11,793
footers dated the site three days before its own rebuild.

All five suites green before pushing: publish gate (11,807 pages, 0 links to
the 277 dead URLs, 0 path leaks, CNAME intact), facets, routing, moat
geometry, bazi parity.

## Previous push — 2026-08-01, `240a67766`, 11,793 pages

Two days of work had been sitting local: `origin/main` was last updated
2026-07-30 20:57, three commits behind with roughly twenty thousand
uncommitted files on top. Six commits went out.

| Commit | What |
|---|---|
| `1b5e0f269` | ถนน/ซอย page tier — 891 roads, 354 sois, method and accuracy published |
| `e30a336f4` | Route planner — walking and riding as two networks |
| `ad3ea0961` | Facets — closed 13-word vocabulary, mirrored in the worker |
| `8cfd60ce1` | `addr:*` wired through (48 → 1,333 addresses); three shelves that read zero |
| `7899d4812` | Privacy notice, the birth chart, and the publish gate |
| `240a67766` | The rebuild |

Verified live: `/chart.html`, `/privacy.html`, `/chart.js`, `/bazi.js`,
`/data/solar_terms.json`, `/soi.html` all 200; the new nav on all 11,793
pages. IndexNow accepted 4,276 sitemap URLs — the first attempt returned 403
and the retry went through, so a single 403 there means try again before
believing the key is wrong.

## Before the next push

```bash
ps -eo pid,etime,command | grep "[b]uild.py"     # must return nothing
python3 build.py
python3 tests/test_publish_gate.py
python3 tests/test_alt_text.py
python3 tests/test_facets.py && python3 tests/test_routing.py && python3 tests/test_moat_geometry.py && python3 tests/test_bazi_parity.py
git log origin/main..HEAD --format='%an <%ae>' | sort -u   # NaNoBotCo only
```

After pushing, `python3 importers/ping_indexnow.py`. A ten-thousand-file push
takes 2–3 minutes before new URLs stop 404-ing — use an `until` loop, not
chained sleeps.

Three things that cost time last round, all now rules in `CLAUDE.md`:

- **Two builds at once leave you with a mixed site.** About 1,400 pages kept an
  older nav and it was invisible by eye. Count a nav link against the page
  total.
- **A stale `.git/HEAD.lock`** can be a day old with no git process behind it.
  Check its age and `ps` before believing "another git process is running".
- **zsh eats backticks in `git commit -m`.** Multi-paragraph messages go
  through `git commit -F <file>`.

---

## Backlog

Ordered by what is closest to done. Reviewed 2026-08-01 — items 1–4 are all
blocked on something only Nan can give: a Cloudflare namespace, or the
go-ahead a network crawl needs under `CLAUDE.md`. Items 5 and 6 need neither
and are the two that can start cold.

1. **The mailing list.** The chart and the privacy notice have shipped, so the
   blocker is gone; what is left is the collecting half, and it needs
   infrastructure under your Cloudflare account. To build: a Worker endpoint on
   a **new** KV namespace (`mot-dang-claims` exposes a public `GET /claims`, so
   contact and birth data cannot live there), the two-store split (list =
   contact + consent record + unsubscribe token, no birth data; demographics =
   coarsened birth year+month, province, day-of-week, animal, sign, with no
   contact and no join key), a CSV export behind a shared secret, and
   unsubscribe. Then set `listEndpoint` in `data/config.json` and the form on
   `/chart.html` appears by itself. Sending marketing stays out of scope —
   collect consent, send later.
2. **Photos for the 479 wats that have coordinates and none.**
   `harvest_commons.py` is built and correct — it wants running against that
   set rather than arbitrary records.
3. **The four unfound พระประจำวันเกิด postures** — ถวายเนตร, ห้ามญาติ, อุ้มบาตร,
   รำพึง. Walk `Category:Buddha statues in Thailand` subcategories; a text
   search returns books that *mention* a posture, not images that depict it.
4. **Events, phase (b)** — the routine crawl for one-off dated events. Sources
   surveyed in `importers/EVENT_SOURCES.md`; the page says plainly it is not
   built rather than implying completeness.
5. **Rich alt text**, and highlighting external links worth following.
6. **A fix in `taoist-oracle`, not here:** `year_pillar` decides the 立春
   boundary by civil day while `month_pillar` decides it by solar instant, so
   they disagree for anyone born on 立春 day before the exact moment.
   `bazi.js` deliberately reproduces the civil-day rule to keep parity
   meaningful — fix upstream first, then regenerate.

## Queued 2026-08-01 — the design study, ported. NOT PUSHED.

Nan liked the CSS in the Claude Design homepage study and asked for it in as
many places as it fits, but not at the price the study paid: it had thrown out
the almanac, the fortune, เซียมซี, the lucky numbers, the ant ranks and the
contribute doors. Every one of those is still here, restyled. Verified rather
than assumed — the rebuilt homepage lost zero element ids and zero `data-fo /
-ho / -hx / -siamsi` hooks against the previous build, and all ten widget tiles
render.

- Palette retuned in `:root`; one design layer appended to `CSS`. Because every
  rule already drew from those variables, the whole 11,808 pages moved together.
- Self-hosted Chonburi / Prompt / Sriracha, 132 KB, unicode-range split.
- 145 of her 151 picks resolved to Wikimedia Commons, licensed, downloaded and
  tagged on four axes. 4 dropped and named (2 publicdomainpictures.net, 2 an
  upload URL shape the recogniser still misses).
- New on the homepage, all additive: a hero, nine shelf tiles with real counts,
  a gold claim band, an after-dark band. New page `/pictures.html`.

### Found on the way, worth knowing

- **The study captioned pictures by filename.** Its ของกิน tile and its khao soi
  listing both used `Chiang Mai photo-7544.jpg`, which is a spirit house with
  red Fanta on it; its Warorot Market card used a green spirit house. Seven of
  her picks are named "photo-66", "photo-7498" and so on and were tagged here by
  opening them and looking. Same family as the proximity-is-not-identity lesson
  in `harvest_commons.py`.
- **Slug truncation at 60 chars collided**, so two Baan Dum photographs became
  one file and one catalogue entry pointed at the other one's picture — a
  wrong-attribution bug. Fixed with a digest suffix on clash only.
- **7 of 73 event titles carried raw HTML entities** from the WordPress feed and
  rendered as `Qigong for Balance &#038; Self-Empowerment`. Decoded at the door
  in `harvest_events.py`; the file on disk was fixed too, so no re-harvest.
- **The route-planner promo is 1,619 px tall on a phone** and is what actually
  buries the almanac — three times the hero above it, and it predates all of
  this. Untouched, because shortening it is a call about her feature, not a
  styling decision. Worth a decision.
- **59 place pages still hot-link `upload.wikimedia.org`.** Pre-existing, and
  now inconsistent with the new art, which is served from our own domain
  precisely because the site promises it follows no one around. The downloader
  to fix it already exists.

## Queued 2026-08-01 (second round) — real instruments, fewer placeholders.

- **The moon stopped being drawn here.** It had appeared three ways: a moondial
  copy in a `#m-moon` module, a home-made disc baked into `sky.json`, and a
  home-made Jupiter beside it. One of them printed "มุมโดยประมาณ ไม่ใช้เอฟีเมอริส
  · angle approximated, no ephemeris here" on the page. All three are gone.
  `importers/make_widget_shots.py` photographs **wichaa.net/moon, /jovilabe and
  /redspot** daily and the sky tile shows those three, each linking back to the
  working instrument. `docs/moon-disc.svg`, `moon_phase_svg()` and
  `jupiter_svg()` are deleted; `sky.json` keeps the numbers, which is what the
  live caption reads.
  - The crop is a **CSS selector**, not a pixel box, so wichaa's header can grow
    a row without breaking it. First attempt styled the selector directly and
    `.instrument` matched more than once — the jovilabe came back as a stack of
    its stat cards. It now marks ONE element and styles the mark.
  - It **refuses a blank frame** (colour count + inked fraction) and keeps
    yesterday's shot rather than shipping a white square.
- **"Cast your own"** on the hexagram tile → wichaa.net/divination. The day's
  hexagram is the same for everybody, which is the time method working as
  intended, and is exactly why the other kind deserves a door.
- **Placeholders demoted.** The front page carried **20** copies of the same wat
  drawing; it now carries **0**. They stay on a place's own page, toned down,
  where they sit beside "send us a photograph" and earn it. Cards with no
  photograph became `.textonly`. The placeholder is also no longer published as
  the schema.org `image` — that was telling every crawler a shop's picture is a
  line drawing of a temple.
- Fixed while in there: the sky caption was hand-building its two language
  spans and rendered "แรม 4 ค่ำWaning" with no separator. Through `mdBi()` now,
  the same fix the Thai horoscope line already needed once.

### Still to do on this line (her direction, not yet built)

Animated GIF previews of each tool in the widget picker, and the **actual
compact widget** running on the reader's own page rather than a picture of one.
The screenshot pipeline is the first step: `make_widget_shots.py` already loads
each instrument in a real browser and isolates one element, so emitting a short
animated loop is the same trick with several frames, and the "compact live
version" wants the instruments to expose an embeddable size.

### Needs a decision

`make_widget_shots.py` refreshes on demand and is option 13 on the Desktop
launcher. Nothing SCHEDULES it yet, and a daily refresh only reaches the live
site if the day's shot is also committed and pushed — GitHub Pages rebuilds on
push, not on a clock. Say the word and it goes in as a launchd job beside the
dead-man's-switch one, with the push included or left to you.

### One open question, unanswered since 2026-07-29

`data/sources.json` publicly documents the Major Cineplex showtime endpoint,
including the trailing-slash trick that makes it answer. It can be trimmed to
"verified, see importer" and forced out of history if you would rather that
stayed private. Say the word either way.
