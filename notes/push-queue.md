# Push queue

What is finished and waiting to go out. Written 2026-08-01 13:35.

Last push: **2026-07-30 20:57** (`origin/main`). Since then local `main` has run
three commits ahead and collected two days of uncommitted work on top. Nothing
below is speculative — every item is on disk and building.

## Hold before you push

A second Claude session was building this repo at 13:34 (build.py plus the
facet and routing tests). Both builds `rmtree(docs/)` on start, so a `git add
docs/` taken while one is running captures a half-written tree. Check it is
quiet first:

```bash
ps -eo pid,etime,command | grep "[b]uild.py"
```

Nothing back means clear. `ps aux | grep -c build.py` counts its own shell and
will lie to you — use the line above.

---

## 1. Committed, not pushed — 3 commits

| Commit | What |
|---|---|
| `6463b4e32` | Say which channels are ours; `notes/empathy-map.md` — who the site is for |
| `c254771cb` | Share cards for 1,343 places (`make_og_cards.py`, `assets/og/`) |
| `f96d5948b` | Rebuild: share cards wired in, channels stated, 10,595 pages |

All three already authored `NaNoBotCo <skunkhaus@gmail.com>`.

## 2. The soi tier — ถนน/ซอย as a page tier (2026-07-31)

891 road pages, 354 sois, a road row on every place page, `/soi.html` index.

- new: `importers/crawl_roads.py`, `importers/build_road_graph.py`,
  `importers/build_streets.py`
- new: `data/streets.json` (808K), `data/road_graph.json` (544K)
- new: `notes/map-ideas.md` — the 12-idea map roadmap this came out of
- in `build.py`: `street_page`, `street_map_svg`, `build_street_pages`,
  `soi_sort_key`, `street_method_note`
- in `CLAUDE.md`: the street rules (publish the method, never render a
  `nearest` match as an address, never merge two spellings, ASCII slugs)

Accuracy is measured and printed on the page: of the 472 records that both
state a street and stand near one, `nearest` gets 84.3% exactly right, 91.9%
right-road-or-its-own-soi.

## 3. The route planner

- new: `make_plan_demo.py`, `assets/plan-demo.gif`, `assets/plan-afternoon.gif`,
  `assets/plan-demo.json`
- new: `tests/test_routing.py`, `tests/test_moat_geometry.py` — both pass
- in `build.py`: `build_plan_page`, `plan_hero_html`, `plan_demo_figure`,
  `plan_key`, `plan_toggle_btn`

Capped to the road graph's box — old city plus about 2 km, 5,676 of 10,463
places, all cm. CR has no road data at all yet.

## 4. Facets — what a branch actually has (the other session, in flight today)

- new: `data/facets.json`, `importers/import_fixtures.py`, `tests/test_facets.py`
- in `build.py`: `facet_set_of`, `facet_bits`, `facet_pills`, `facet_door`,
  `facet_panel`, `facet_ticks`, `facet_chips`
- in `worker/worker.js`: closed 13-key vocabulary mirrored from
  `data/facets.json`; facets alone can never open a claim

**This one is still moving.** Confirm the session is done before including it.

## 5. Importers and categories

- `importers/import_overpass.py` — `addr:*` family wired through (48 → 1,333
  addresses); `diet:vegetarian=only` only, so the มังสวิรัติ-เจ shelf stops
  reading 0 while pointing เจ-keepers at pork-and-rice shops; barber split off
  hair; `beauty=` split on `;` so 44 salons stop falling off every shelf
- `importers/crawl_overpass.py`, `importers/import_all.py`
- `data/categories.json` — the new children those rules feed
- `data/canonical/cm.json`, `data/canonical/cr.json` — reimported

## 6. Privacy notice and the birth chart

- new: `/privacy.html` — bilingual, controller named by contact address only,
  deletion route, and a plain statement that there is no mailing list yet
- new: `/chart.html` + `docs/chart.js` — ดวงจีนสี่เสา, drawn by the engine that
  had been finished and parity-tested for days with nothing rendering it.
  `assets/bazi.js` and `data/solar_terms.json` are now copied into `docs/`
  by `build.py` rather than left where the wipe can eat them.
- nav: Four Pillars in the services bar, Privacy in the footer — both on all
  11,793 pages
- `tests/test_publish_gate.py` — the pre-push checks, which kept being written
  as a scratch script and lost

Nothing on either page collects anything. The chart computes in the reader's
browser and the page has no endpoint to send a birth date to. The "email me
this chart" block only appears if `data/config.json` gains a `listEndpoint`,
the same way the LINE blocks stay hidden while `lineOaId` is empty — so the
Worker can be deployed later without touching the page.

## 7. `docs/`

12,405 modified files, 76 new directories, **11,793 pages**.  The nav and
template changes touch every page, so the diff is wide by design.

> A build collision happened while this was being prepared — a second
> `build.py` overlapped and about 1,400 pages kept an older nav. A clean
> rebuild with nothing else running fixed it; all 11,793 pages now carry the
> same header and footer. Check for the collision by counting a nav link
> against the page total, not by eye.

---

## Pre-push gate

```bash
python3 tests/test_publish_gate.py
```

Run it **after** the final build, not before. It checks the three things that
have bitten this repo: no page hyperlinks a URL that `check_links.py` verified
dead, no `/Users/...` path is published, `docs/CNAME` still says motdang.net.
Last clean run 13:33 — 11,558 pages, 277 broken URLs on file, 0 links to them,
0 leaks.

Then the rest of the suite:

```bash
python3 tests/test_facets.py && python3 tests/test_routing.py && python3 tests/test_moat_geometry.py && python3 tests/test_bazi_parity.py
```

All four passed at 13:32.

Author check — public commits are NaNoBotCo only:

```bash
git log origin/main..HEAD --format='%an <%ae>' | sort -u
```

## After the push

```bash
python3 importers/ping_indexnow.py
```

A ten-thousand-file push takes **2–3 minutes** before the new URLs stop
404-ing. Don't declare victory on the first curl — use an `until` loop in a
backgrounded Bash, not chained sleeps.

---

## Not in this push — the backlog

Ordered by what is closest to done.

1. **The mailing list.** The chart and the privacy notice shipped above, so the
   blocker is gone — what is left is the collecting half, and none of it can go
   in without your say-so because it needs infrastructure deployed under your
   account. Still to build: a Worker endpoint on a **new** KV namespace
   (`mot-dang-claims` exposes a public `GET /claims`, so contact and birth data
   cannot live there), the two-store split (list = contact + consent record +
   unsubscribe token, no birth data; demographics = coarsened birth year+month,
   province, day-of-week, animal, sign, no contact and no join key), a CSV
   export behind a shared secret, and unsubscribe. Then set `listEndpoint` in
   `data/config.json` and the form on `/chart.html` appears by itself. Sending
   marketing stays out of scope — collect consent, send later.
2. **Photos for the 479 wats that have coordinates and none.**
   `harvest_commons.py` is built and correct — it wants running against that
   set rather than arbitrary records.
3. **The four unfound พระประจำวันเกิด postures** — ถวายเนตร, ห้ามญาติ, อุ้มบาตร,
   รำพึง. Walk `Category:Buddha statues in Thailand` subcategories; text search
   returns books that *mention* a posture, not images that depict it.
4. **Events, phase (b)** — the routine crawl for one-off dated events. Sources
   surveyed in `importers/EVENT_SOURCES.md`; the page says plainly it is not
   built rather than implying completeness.
5. **Rich alt text**, and highlighting external links worth following.
6. **A fix in `taoist-oracle`, not here:** `year_pillar` decides the 立春
   boundary by civil day while `month_pillar` decides it by solar instant, so
   they disagree for anyone born on 立春 day before the exact moment.
   `bazi.js` deliberately reproduces the civil-day rule to keep parity
   meaningful — fix upstream first, then regenerate.

### One open question, unanswered since 2026-07-29

`data/sources.json` publicly documents the Major Cineplex showtime endpoint,
including the trailing-slash trick that makes it answer. It can be trimmed to
"verified, see importer" and forced out of history if you would rather that
stayed private. Say the word either way.
