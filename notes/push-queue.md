# Push queue

What is waiting to go out, and what shipped last time.

## Waiting

**Two commits, queued 2026-08-02 — the two infographics from the map-ideas
round, built.** `git push origin main`, then `python3 importers/ping_indexnow.py`.

The two the 2026-08-01 session tested against the data and asked to build
("the wat-name morphology and the 7-Eleven distance — pure computation on data
already on disk"). Both are now pages, computed fresh every build:

- **`/watnames.html` — ชื่อวัดบอกภูมิประเทศ.** 270 unique Thai wat names in CM
  read against their coordinates; the leading word predicts the distance from
  the moat (เชียง 2.1 กม. → ทุ่ง 11.8 กม.). The quick test's numbers moved once
  the method got proper: leading-element matching only (วัดสันป่าข่อย is a สัน
  name, not ป่า; วัดสันติธรรม is peace, not a ridge), ำ/ํา unicode folding,
  name-dedup, and Thai-script resolution. 23 wats carry only romanised names
  and are excluded — Wat Chiang Man among them, stated on the page.
- **`/seven.html` — ใกล้เซเว่นแค่ไหน.** Median 240 m from 10,332 places to the
  nearest of 338 branches; 74% within 500 m, 86% within 1 km. Histogram,
  per-category medians (massage 151 m → wats 1,560 m), and a ~550 m-cell
  contour map of central CM with the moat overlaid (374 cells, cells under
  3 places left blank and the blank stated).
- Both publish raw numbers (`data/watnames.json`, `data/seven.json`), link each
  other, hang off stats.html ("เรื่องที่ข้อมูลเล่า") and llms.txt. BUILD_DATE
  bumped to 2026-08-02. 11,811 pages (+2).

Verified before queueing: all seven suites green, zero `/Users/` leaks, both
pages DOM-checked through the local server (site chrome, charts, sortable
tables, moat polygon + 236 branch dots all present), and every class the new
pages use has a rule — except `.lede`, which has no rule anywhere on the site
(reach.html ships the same way; a plain paragraph, not an invisible block —
noted, not fixed, since it predates this work).

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
