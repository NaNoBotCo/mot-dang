# มดแดง — marching orders

> Standing tasking for motdang.net, from the gemba walk of 2026-08-17.
> **Read `CLAUDE.md` first** (the rules that bite), then `AGENTS.md` (why the
> site is shaped this way), then `BOTS.md` (the org chart). This file says what
> to build next and how you will know it worked. The shared task board carries
> the moving state; this is the standing structure.
>
> House discipline, no exceptions: stdlib Python, local, static, no tracking.
> Curated outranks crawled. Provenance travels with every fact. Ambiguity goes
> to a review file, never to a coin flip. Bilingual ไทย · EN or it does not
> ship. **Bots build and test; the standing walk publishes.** No order below
> ends in a deploy because none of them has to: `importers/standing_walk.sh`
> goes round every twenty minutes and ships whatever has cleared the gates.
> Finish your order, leave it on disk, and say what you built — do not deploy
> it, do not ask whether to, and do not report that you have not. To hold the
> site still on purpose, `cache/walk-rest`.
> Network fetches are manual-trigger and confirmed with Nan before they run.

## Status board

| # | Order | State |
|---|---|---|
| WO-1 | Temple register join (รหัสวัด, founding year, nikaya) | **DONE** 2026-08-17 |
| WO-2 | Festival venues get place ids | **DONE** 2026-08-17 |
| WO-6 | The graph + neighbour links | **DONE** 2026-08-17 |
| WO-4 | Search that forgives | **DONE** 2026-08-17 |
| WO-5 | Sorts: neighbourhood, ancientness | **DONE** 2026-08-17 (open-now open) |
| WO-3 | The detail page | **DONE** 2026-08-17 (site crawl running) |
| WO-7 | The maps | **DONE** 2026-08-17 (shelf maps interactive) |
| WO-2b | Class venues — "ทุกวัด", "the five gates" | new, from WO-2 |
| WO-8 | กัญชา-กระท่อม shelf — crawl, classify, facets, lamps | **BUILT** 2026-08-17 |
| WO-9 | The medical shelf — the one that had never been crawled | **BUILT** 2026-08-18 |
| WO-10 | หอสมุด·หอศิลป์·หัตถกรรม — the culture shelf | **BUILDING** 2026-08-18 — B+C done, A crawling |
| WO-11 | The schools shelf — โรงเรียน-สถานศึกษา, every school not just the international ones | **BUILT** 2026-08-18 — 14 → 2,416 schools |
| WO-12 | มวยไทย — events, locations, culture: the fight board, the shelf, the primer | **BUILT** 2026-08-19 — 20 records on two shelves → a shelf, a board, /muaythai.html |
| WO-13 | รถ-เดินทาง — the transport layer: the station split, the bus board, /transport.html, the orphaned flights board adopted | **BUILT** 2026-08-20 — `transport_layer.py` + the `classify()` split (train · bus · songthaew · taxi · funicular · pier): songthaew 0 → 20, taxi 0 → 5 (they were being DROPPED), train/funicular no longer one word; 674 licensed routes on the board; flights board finally linked. Section below. |
| WO-14 | เรียนทำอาหารไทย — Thai cooking classes, all kinds: the class board, the nine-child shelf, the primer, /cooking.html | **BUILT** 2026-08-19 — 25 records on seven shelves → a shelf, a board, a calendar day, a sheet, /cooking.html |
| WO-14 | สักยันต์-รอยสัก — the tattoo shelf: the สำนัก, the studios, the brow shops, the prices, the join to wichaa | **BUILDING** 2026-08-19 — `notes/sakyant-proposal-2026-08-19.md`; zero-network steps in hand; the two สำนัก and the brow/removal records await a light web check (Nan's go) |
| WO-15 | 🏷 Tags — the cross-shelf layer (vegan · bitcoin · wifi · wheelchair · 24 h · old city · brands · honours …), tag pages per province, `/tags.html`, pills on place pages | **BUILT** 2026-08-19 — `data/tags.json` (73 tags / 13 families, one rule each) + 47 brand tags generated; `tags_layer.py`; 182 tag pages + 163 tag×shelf pages; 5,483 records tagged; `tests/test_tags.py` PASS; zero network. Section below. |
| WO-16 | Open lists from data.go.th — the ONAB temple fold · bus routes · CR attractions w/ phones · police w/ phones · Thai SELECT · ธงฟ้า · LPG · SAT boxing camps · FDA pharmacy yardstick | **BUILT** 2026-08-20 — 18 sources harvested (`importers/harvest_datagoth.py`), **2,366 records folded** (`importers/import_opendata.py`): temples +2,009 (register on disk, both provinces), CR sights +238, ธงฟ้า +34, police +40 (all with phones), LPG +28, SAT camps +17; 5 Thai SELECT honours; 7 yardsticks on /stats.html; `data/bus_routes.json` (674) for WO-13; catalogue 16,272 → **18,666**. Section below. |
| WO-17 | Thailand Tourism Directory (กระทรวงการท่องเที่ยวและกีฬา) — ≈28,500 national listings with phone · LINE · hours · coords via its official keyed API; hotel/food/spa/sights/stores | **PINNED** (Nan, 2026-08-20 — awaiting her API key) · was PROPOSED 2026-08-19 — same note §2; step 0 = Nan registers for the API key; enrichment policy is decision 4 in the note |
| WO-18 | Brand locators — 7-Eleven · PTT · Bangchak · Café Amazon · the big banks, per-branch link to the brand's own page | **PARKED** 2026-08-19 — same note §5; after WO-15–17; per-brand robots/terms check first |
| WO-20 | แผนที่มีชีวิต — the living maps: touch that answers, gestures that behave, ground with ink in it | **PHASE 1 + 2e–f BUILT** 2026-08-20 — `notes/maps-gemba-2026-08-20.md`; the pointer-events regression that had made every neighbour link on 12,309 place maps untouchable whenever tiles were on, cooperative gestures + rotation lock + rails + ◎ + full screen, the MDCARD tap-sheet on every map, tiles and label glyphs both same-origin (last third-party request gone), contrast retune, gate anchors, key, and an 11 px type floor for phones. Phase 3 (/map.html, the nav door, my-map, shareable views) NOT started |
| WO-21 | วิว-น้ำตก — views & photo spots: the shelf, the measurements, the doors the data is behind | **ZERO-NETWORK HALF BUILT** 2026-08-20 — `notes/views-proposal-2026-08-20.md`; `importers/audit_views.py`; `views_hit()` rides the WO-19 fence and files **18 waterfalls + 2 viewpoints** the attraction dragnet had already caught (แม่สา, บัวตอง, the Inthanon set, ขุนกรณ์, the CR skywalk); `sights` gains a น้ำตก child; JSON-LD `Waterfall`; `direction`/`ele` kept at import and rendered (หันไปทาง · Faces / Elevation); claims census 54 → `cache/views_claims_*.txt`; scratch build 20,371 pages, all gates PASS. **The doors await Nan's numbered go** (note §doors): wide `views` group · Commons uncapped re-run · TTD key · WO-16 lists · DNP fee/hours reads · the `view` tag · her own picks | · **2026-08-21 postscript**: seed list replaced by a full-breadth mine per [[feedback_known_empty_can_be_wrong]] — HIDING 11 sorted spot/container/station + 9 toponym strays guarded (`cache/views_review_*.txt`); the roll now reports **findable** vs **present** after ภูชี้ฟ้า read green while being 2 unpinned register rows on no view shelf; 1 real dupe pair (`views_dupes_cm.txt`); **261 sights records match no child** (cr 234, mostly `dgth`, incl. ภูชี้ฟ้า and the CR clock tower) — the eco register's single type field cannot sort them, nothing auto-shelved; the `view` tag deliberately NOT shipped (tags.json derives nothing from names — needs an attr or Nan's call)
| WO-19 | ช้าง — the elephant shelf, the register of what each camp states, the city's elephant names, /chang.html, and the wichaa article | **BUILT** 2026-08-19, crawl folded 2026-08-20 — `notes/elephant-proposal-2026-08-19.md` (+ postscript); 0 camps → 18 curated → **30 on the shelf** after the `elephants` Overpass group (zoo·theme_park·attraction, fenced: 290 non-elephant elements to `cache/elephant_review_*.txt`); 8 merges onto surveyed pins; needs-pin 6→3; Ruammit CR entered; register with `stated`/`unstated`; wichaa `entity_chang` 31 witnesses; CR zoo selector `incomplete`, re-run when Overpass is calmer |
| WO-22 | เสริมสวย-ตัดผม — the barber correction, the words to ask with, and the census of the silence | **ZERO-NETWORK HALF BUILT** 2026-08-20, Nan's ask (afro-textured hair · americana/british barbers · extensions · braids · updos · digital perms · high-tech studios · house calls) — `notes/beauty-proposal-2026-08-20.md`; `importers/audit_beauty.py`; **barber 6 → 62** and **salon 0 → 62** off the shops' own signs (126 shelf corrections); `beauty/extensions` child; the **30-facet `beauty` set** covering all eight axes; `male`/`female`/`unisex` rescued from the import (26 shops now state who they cut for); `beauty_layer.py` → **/beauty.html** — 22 words with RTGS/tone/root, 5 whole sentences, both shelves, and a printed census showing **0 of 18,686** records name a perm, an updo, textured hair or a house call. **All four doors run 2026-08-21** on Nan's go: door 1 wide crawl → **0 supply shops, 0 wigs, 0 home stylists** (a question closed; 41 cosmetics filed nowhere) · door 2 site reads → only **8 of 18** links were first-hand, 3 domains dead, **4 read, 1 states six services** (New York, New York — `digiperm` and `updo` go 0 → 1) · door 3 → the survey instrument is built and published (`/reader/hair-words.pdf`), the walk is Nan's · door 4 → **blocked**, TTD needs an account only Nan can make, and it is spa not hair anyway |
| WO-23 | น้ำพุร้อน — hot springs, the whole north: the shelf CM held zero of, the seventeen-province register, /namphuron.html | **BUILT** 2026-08-20/21, Nan's go ("BIGLY… the whole north is ok") — `notes/hotsprings-proposal-2026-08-20.md`; CM **0 → 16 records** (สันกำแพง w/ its own site's posted prices, โป่งเดือด, เทพพนม, ฝาง, ดอยสะเก็ด, มะลิกา…), CR 3 → 9 (แม่ขะจาน's four faces merged to one, ผาเสริฐ, โป่งพระบาท, ห้วยหมากเลี่ยม); register `data/hotsprings.json` **98 springs / 14 provinces, 63 with measured temperatures** — OSM area-clipped per ISO province (`hotsprings` group WIDE + `harvest_hotsprings.py`), the **DMR inventory read whole** (66 northern rows, temp+pH), DNP park list + MHS's own hot-spring CSV (pins), curated stated-facts w/ fetched sources; `springs_hit()`/`audit_hotsprings.py` one-copy rules (bare โป่ง never matched; village/school/temple/office/campsite/bus-stop fences all witnessed by real catches); generic-key guard after a bare-worded spring folded 60 km wrong; /namphuron.html = drawn no-tile map (54 pins) + stated-register + primer; `sights` น้ำพุร้อน child; thesaurus ring widened; phichit asked short (1 selector, said on the page; `--fetch` when mirrors calm); scratch build 21,402 pp, all gates PASS |
| WO-24 | คำตอบก่อนลิงก์ — search rich doors + the namesake split: a curated card over the rows for topics the site keeps a page for, and ชื่อพ้อง filed behind their own header | **BUILT** 2026-08-20, Nan's ask after typing "elephant" ("pre-stage some rich information… place names with Chang in them are not differentiated… might be systemic") — `notes/search-doors-2026-08-20.md`; `data/curated/search_panels.json` (10 panels: chang · muaythai · cooking · beauty · womens-health · toilets · festivals · flights · massage · wat; build.py refuses a malformed pair); triggers by lifted shelf / term variants / query substring, first to speak wins, panel shelves join the +0.5 lift; on-shelf rows split from namesakes whenever the query names a shelf — systemic, not elephant-special; `tests/test_search.py` REPAIRED (its extraction markers predated search-core and the whole file failed at HEAD) and extended to 26 queries + a door-href walk; searchcore/mined tables untouched, no parity run needed |

WO-3 and WO-7 were marked standing because they are the two a reader actually
meets. Both have now been done, and the rule stays: anything added here is
weighed against whether the place page and the map get better for it.

**Everything below is built and committed locally. Nothing has been deployed —
`python3 publish/deploy.py --yes` is Nan's move and always has been.**

---

## WO-1 — Temple register join · DONE 2026-08-17

`importers/import_wat_registry.py` → `data/curated/wat_registry.json`, merged by
`import_all.py:apply_wat_registry()`, rendered in `build.py:known_facts()`.

**Landed:** 346 of 596 wat records stamped — all 346 with a founding year (range
658–2018 CE, median 1867), plus nikaya, standing, wisung-khamsima date, ตำบล/อำเภอ
and the permanent code. 298 matched province+exact, 27 district+exact, 21
province+fuzzy. 63 shrines and spirit houses were never matched (the register
does not hold them). 101 ambiguous names went to
`cache/wat_registry_review.txt`; 86 temples the register does not carry under
the name we hold.

**Correction now on the record.** The plan said this order would fix the wats'
0%-contactable standing. It does not, and the claim was wrong: the register
carries a phone on **6 temples nationwide** and a website on 1 — none in Chiang
Mai or Chiang Rai. What it brings is **time and place**: founding years for the
ancientness sort (WO-5), and ตำบล/อำเภอ for by-neighbourhood grouping. Wats
remain the least contactable shelf on the site and only a person at the gate
changes that. Do not re-derive contacts from this source.

**Open for a human:** the 101 in the review file. Each needs an อำเภอ, a look at
the pin, or a walk past the gate. Settling them by hand is a good errand for a
field day; nothing enters the join until one is settled.

---

## WO-3 — The place page: show what we already carry

**The finding.** Records hold **86 distinct `attrs` keys**. `known_facts()`
renders about twenty of them. Blurbs exist on 23 of 12,319 pages, while
`attrs.description` sits on 236 and `descriptionTh` on 102, unread. Mean ant
rank is 1.68 of 9 and nothing on the site scores above 6. A reader arriving at
a place page mostly meets a name, a pin and an invitation to fill it in.

**Read first.** `build.py:5728` (`known_facts()` — WO-1 added the temple block
at its foot, follow that shape), `build.py:6011-6016` (the body assembly order),
`build.py:5515` (`place_json()` — every page has a JSON twin and it must gain
the same fields), `importers/enrich_sites.py` (the etiquette header),
`CLAUDE.md:292`.

**Steps, in the order they pay.**
1. **Render the carried-and-silent attrs**, each as its own `<dl>` row with the
   provenance style the neighbours use: `cuisine` (2,122 records — link it to a
   search for that cuisine, it is a browse axis in disguise), `brand` and
   `operator` (1,221), `diet` (212), `wheelchair` (369), `email` (339, as a
   mailto), `altNames` / `namesOther` (538 + 363 — "also answers to…", already
   search aliases and still invisible on the page).
2. **Blurb fallback.** Where `blurb_th` / `blurb_en` are empty and
   `attrs.description` / `descriptionTh` exist, render those as the blurb with
   a "จาก OpenStreetMap · from OpenStreetMap" tail. 300+ pages gain a sentence
   the same day, and none of it is written by a machine.
3. **Say what is missing, precisely.** The ant panel counts; it does not name.
   Under it, name the two or three facts this page most wants — "ยังไม่มีเบอร์
   และเวลาเปิด · no phone and no opening hours yet" — because a specific ask is
   the one people answer.
4. **[network — confirm with Nan first]** `importers/enrich_wikipedia.py` for
   the ~350 places carrying `attrs.wikidata`, `brandWikipedia` or `heritage`:
   TH+EN lead extract from the Wikipedia REST summary endpoint, 1 rps, cached
   under `cache/wikipedia/`, written to `data/curated/enrich.json` with the
   article revision date. CC BY-SA — the credit and the link render with the
   blurb, exactly as photo credits do. Wats and sights first.
5. **[network — confirm with Nan first]** Finish `enrich_sites.py`: 269 of 998
   website-bearing places have been read. Batches of 100 (`--limit 100`), fold
   into `morning_walk.sh` only after three clean manual runs.

**Landed 2026-08-17.** 2,122 pages say what the kitchen cooks (each cuisine
linking to the search that now answers with the shelf), 1,477 name the chain a
branch belongs to, 403 show an email, 236 open with the mapper's own sentence
credited to OpenStreetMap, and **31 open with an encyclopaedia's**, credited
CC BY-SA with the article link and revision date. Step 3 turned out to be
already built — `next_ant()` names the two easiest missing facts as a favour.

**`importers/enrich_wikipedia.py`** reads only the article a place ALREADY
CITES. Most cite a Wikidata Q-id rather than a title, so the item's sitelinks
resolve id → article: the Q-id says *which* thing and a name search could not.
Chains are excluded — the article about 7-Eleven is about the company, and
printing it under one shop in Chiang Mai would say something untrue about that
shop.

**A bug worth remembering.** The first cache key replaced every non-ASCII
character with `_`, so every Thai title of the same LENGTH shared one file:
อุทยานแห่งชาติแม่ปืม was served มหาวิทยาลัยเชียงใหม่'s article, and Mae Puem
National Park went out described as a university. On a Thai-first site, a cache
key that cannot hold Thai is not a cache — it is a way of quietly swapping one
place's facts for another's. **Any new cache key on this site gets a hash, not a
sanitised name.** All 31 blurbs were purged, re-fetched and audited one by one
against their place.

---

## WO-7 — The maps: the shelf, the year, the way onward

**The finding.** 12,771 pages carry a map and **every one of them is a single
pin**. The category GeoJSON is already written to `docs/data/*.geojson` — 44
files — and drawn nowhere. Soi pages do not say where the street continues,
though `streets.json` holds `crosses`, `parent` and `aliases`. Festival venues
have coordinates and no map. And on all 12,309 place maps the up-to-nine
neighbours are computed, labelled, and **not clickable**.

**Read first.** `map_shell.py` — the ONLY module that may construct a browser
map (`CLAUDE.md:51-56`), and `map_shell.py:79` (`enabled()`: `url: ""` degrades
every map to drawn SVG, and that is a supported state, not a broken one).
`map_ground.py` for anything Pillow draws. `build.py:4688` (`place_map()`),
`:4865-4918` (the label-placement algorithm — push along the ray, leader line,
9 angles × 3 radii, **omit rather than overlap**; do not touch that logic),
`:8606` (`street_map_svg()`), `:9485` (`merit_map_svg()` — the multi-pin drawn
map to copy), `data/basemap_style.json` (the 14 style layers), `tests/test_ground.py`
and `tests/test_moat_geometry.py`.

**The rule that governs all of it.** The drawn SVG comes first and the tiles go
underneath. What Python draws is what prints, what a reader with scripting off
keeps, what a low-vision reader can have read aloud, and what fills the box
before the first tile lands. A map is never the only way to the information —
the linked list under it stays, always.

**Steps.**
1. **Neighbours become links.** `build.py:4903-4918`: wrap each drawn neighbour
   label and dot in `<a href>` to that place's page. One change, ~110,000 new
   internal edges, on every place page on the site. Keep the collision and
   omission logic exactly as it is. Do this first — it is the cheapest large
   thing on this whole list.
2. **Shelf maps.** New `shelf_map()` in `build.py`, mounted through
   `map_shell`: one drawn dot map per category index, dots from the GeoJSON
   already emitted, labels for the ant-rank top ten (the merit-map treatment),
   both provinces — 46 pages that currently open with a wall of names and no
   sense of where anything is.
3. **The filter and the map are one view.** On category pages the WO-5 chips
   and sorts re-style the dots — matching dots keep their ink, the rest dim.
   A reader filtering to "open now" should watch the city thin out.
4. **Soi continuations.** Under each street map, render `crosses`, `parent` and
   `aliases` from `streets.json` as links: "ตัดกับ · crosses …", "ต่อเป็น ·
   continues as …". 804 soi pages become a walkable graph instead of 804
   dead ends. Never merge two spellings of a road — point them at each other
   (`CLAUDE.md:67`).
5. **Festival venue maps** (needs WO-2's ids): `event_map_svg()` over a
   festival's located venues, on the festival page.
6. **Map QA is its own pass**, not an afterthought: drawn-first state, print,
   scripting off, `url: ""` degrade, alt text through `bi_text()`
   (`tests/test_alt_text.py` fails a label that is only the medium — "map" is
   not what a map is *for*), and the moat crossing the frame drawn AND named
   by rule.

**Landed 2026-08-17.** Neighbour dots are links on all 12,309 place maps.
**39** category shelves (not 46 — the rest hold fewer than eight placed points,
and a map of five dots says less than the list does) draw over the real
basemap, with the ten most complete listings named. 431 soi pages name the roads
they cross and 62 carry their other spelling.

**And the shelf map answers back.** The dots are one `<path>`, so there is
nothing to hover: md.js finds the nearest point to the pointer instead — a few
thousand comparisons, inside one frame, so a 4,013-place shelf responds like a
40-place one. Hover names the place, click opens it, and the facet chips thin
the **map** as well as the list.

The packed data is only `[x, y, rowIndex]` — **75 KB on the food shelf, down
from 357 KB**, because the name, link, facets and rank are already in the list
below and shipping them twice cost 282 KB to repeat the page to itself.
Verified: `corr(x, lng) = +1.000000`, `corr(y, lat) = −1.000000` across all 305
wat points, so every dot answers for its own row.

**Next on this order:** the same treatment for the province index maps, and a
drawn festival-venue map for Chiang Rai (`event_map_svg` frames itself against
the Chiang Mai moat, so a CR festival currently keeps its list instead).

---

## WO-2 — Festival venues get place ids

**The finding.** `data/festivals.json` holds 52 bilingual venue strings and no
ids, so `festivals_layer.py:337` re-runs a strict matcher at build time and only
**13 of 12,319** place pages ever show a festival band.

**Read first.** `festivals_layer.py:337` (`venue_places()`), `:535`
(`build_festival_page()`), `:875-903` (band injection), `build.py:6440`
(`event_map_svg()`), `data/curated/venue_aliases.json`, `tests/test_festivals.py`.

**Steps.** A one-off `importers/resolve_festival_venues.py` runs the 52 strings
through the strict matcher plus the alias file, and reports three buckets:
matched (write `place_id` into `festivals.json`), ambiguous, no-candidate — the
last two to a review file, never guessed. `venue_places()` then prefers the id
and falls back to the matcher so nothing regresses. Matched venues become links
on the festival page and gain a venue map; their place pages gain the festival
band. Free text stays — it is the display name and the fallback. Ids do not
upgrade a `needs-verification` festival: those 9 keep their dashed mark on the
wheel.

**Landed 2026-08-17.** `importers/resolve_festival_venues.py` settles the 52
strings once; 11 are catalogue places and carry `place_id`. Nine place pages
show a festival band and six festivals gained a drawn venue map.

**The acceptance target in this order was wrong and is corrected here.** It
asked for bands on ≥40 place pages, assuming the 52 venue strings were mostly
places. They are not: "ทุกวัด" (every temple), "วัดทั่วเชียงใหม่และเชียงราย",
"ประตูเมืองทั้งห้าและแจ่งทั้งสี่", "ดอยแม่สลอง", "คูเมืองเชียงใหม่",
"เส้นทางขบวนแห่: สะพานนวรัฐ – คูเมือง" — mountains, moats, procession routes,
whole quarters and classes of temple. **41 of 52 are correctly prose and always
will be.** Per-venue ids top out around 11. Getting festivals onto many pages
needs WO-2b, not more matching.

Three wrong matches were found and removed on the way, all worth knowing:
Tha Phae Gate resolved to *Punspace Tha Phae Gate*, a coworking office, because
the venue string carries a province suffix the record does not; Songkran's Phra
Buddha Sihing procession resolved to Chiang Rai's วัดพระสิงห์ because our
Chiang Mai record for Wat Phra Singh carries **no Thai name** for the Thai
string to reach; and the build-time fallback attached one venue to *both* Wat
Phra Singhs at once. The fallback now refuses a venue whose Thai and Latin
spellings disagree, and the Wat Phra Singh case is in
`cache/festival_venues_review.txt` with both candidates named.

**Open for a human:** that review file. The Chiang Mai record's missing Thai
name is the underlying fix and belongs in `data/curated/names.json` with a
fetched source, per `CLAUDE.md:274`.

---

## WO-2b — Class venues: "ทุกวัด", "the five gates"

**Why this is the real ceiling.** WO-2 showed that most festival venues are
classes, not addresses. เวียนเทียน on Visakha Bucha is kept at *every* temple;
Songkran runs the *five gates and four corners*. Those are the entries that
could put a festival band on hundreds of pages — and the site already holds
both sets: 596 wat records, and `_moat_crossings()` reading the catalogue's own
gate records rather than a hand-typed list.

**The wording rule this must obey, and it is not optional.** A class venue is a
HABIT OF A CLASS, exactly as a toilet tier is (`CLAUDE.md:75-85`). It renders as
*"เทศกาลนี้เก็บกันตามวัดทั่วไป · temples generally keep this festival"* and
must **never** become *"this temple holds Inthakhin"*. One is true of the
tradition; the other is a claim about a named temple that nobody verified, on
596 pages at once. A stated venue always outranks a class, the same way a
verified toilet point outranks a tier.

**Steps.** A `class` field on a venue (`every_wat`, `city_gates`,
`every_wat_in`), resolved at build time to the matching record set; the band
renders in class wording with a link to the festival; the festival page says
how many places the class covers. **Nan writes the class sentences** — the
toilets wording lives in `data/toilets.json` for the same reason, and this
belongs beside it rather than being drafted by a bot.

**Acceptance.** Class bands on the wat shelf read as a habit in both languages
and never as a claim; a stated venue on the same page suppresses the class line;
`tests/test_festivals.py` gains a case asserting the class wording.

---

## WO-6 — The graph: stretchy, elastic, a receipt on every edge

**The decision.** Port the pattern from `manuscript-wiki/cartography.py` — which
already runs 23,604 nodes and 126,852 edges — rather than inventing a second
system. Its vocabulary is the contract: **`authored`** (a human wrote it),
**`adjudicated`** (a written rule decided it, and it fails closed),
**`computed`** (catalogue columns or coordinates), **`derived`** (a bot noticed,
with cited counts). Every edge carries `w` — a real count or a distance in
metres, never an invented score — and `ev`, a receipt a reader can read.
Nothing is inferred from a language model's priors.

**Steps.** New `graph_layer.py` hooked from `build()` in two lines, the way
`festivals_layer` is. Nodes: place, street, category, sub, festival, cuisine
(values with ≥5 places), brand (≥3 branches), tambon and amphoe (WO-1). Edges:
`on_street` (`via:stated` vs `via:nearest` stated in `ev`), `near` (metres in
`w`, reusing the place-map neighbour computation), `in_category` / `sub_of`,
`hosts_festival` (WO-2 ids, festival window in `ev`), `serves_cuisine`,
`branch_of`, `same_wat_as_wichaa` (the 523 pairs in `data/wichaa_links.json`,
`ev`: "same Thai name, ≤400 m"). Emit `docs/api/graph/{nodes,edges}.jsonl` +
`summary.json` + `graph.jsonld` with schema.org typing. Deterministic ordering,
no timestamps, so an unchanged catalogue rebuilds byte-identical.

Then the part a reader sees: a **threads band** on place pages, after "More like
this" — up to five typed lateral links *with their receipts*: "อยู่ถนนเดียวกัน
อีก 23 ร้าน · 23 more on this road", "312 m apart", "สาขาเดียวกัน 12 แห่ง ·
same brand, 12 branches", "งานประจำปีอินทขีล · hosts Inthakhin", "หน้าวัดใน
คลัง wichaa · this wat in the wichaa archive". Structural shelf edges stay out —
the breadcrumb already carries them.

**Landed 2026-08-17.** `graph_layer.py`, hooked in two lines. **14,130 nodes,
63,464 edges** — `near` 29,893 · `in_category` 12,385 · `sub_of` 11,154 ·
`on_street` 4,762 · `serves_cuisine` 2,917 · `branch_of` 1,127 ·
`same_wat_as_wichaa` 523 · `in_amphoe`/`in_tambon` 346 each ·
`hosts_festival` 11. Provenance: 62,941 computed, **523 adjudicated**. Two
builds byte-identical. Written to `docs/api/graph/{nodes,edges}.jsonl` +
`summary.json` + `graph.jsonld`.

**Correction to this order's own arithmetic:** it promised "~110,000 neighbour
edges". That counted every drawn label on every map, in both directions, inside
the map frame. Deduplicated to one edge per pair, inside a 400 m radius and
capped at six per place, the honest number is **29,893**. The reader-facing win
is unchanged and it is the one that mattered: the neighbours drawn on all
12,309 place maps **are links now**.

**The threads band is built and deliberately empty.** It refuses any thread
with no destination, and today every thread it could show either has no page
(cuisine, brand) or already appears on the page (the wichaa link is a row in
"Read more elsewhere"). It lights itself the day WO-4 gives cuisine and brand a
filtered URL to point at — no further work, just the URL.

**Also fixed here:** `data/wichaa_links.json` records the Cloudflare Pages host,
so 523 pages were publishing a staging subdomain. Normalised to `wichaa.net`
where the file is loaded, which corrects the "Read more elsewhere" row too.
`importers/link_wichaa.py` should record `wichaa.net` at source.

**Still to do on this order:** advertise the graph on `/source.html` and in
`llms.txt` under CC BY.

---

## WO-4 — Search that forgives

**The finding.** "kow soi" returns silence; "khao soi" returns a flat list of 33
names. The index matches name and alias only — 3 fields — ships as one 2.79 MB
file, and knows nothing of the categories, streets, cuisines or brands the data
already holds. `c[]` ships in every entry and is never used.

**Read first.** `build.py:2397-2455` (the matcher, shipped as `docs/md.js`),
`:9816-9834` (index build), `tests/test_search.py` and **`CLAUDE.md:286-291` —
touch that block, run that test**. For the pattern, `manuscript-wiki/wiki.py:2251-2276`
is the thesaurus this order ports.

**Steps.** Index gains `su` (sub labels TH+EN), `cu` (cuisine), `br` (brand),
`st` (street), and folds category display names into the haystack. Split into
`index-cm.json` / `index-cr.json`, loading the reader's own province first — the
satellite-connection rule. New `data/search_thesaurus.json`, ~100 groups seeded
from `altNames`, cuisine values and category labels, crossing script and
transliteration drift (khao/kow/kao/ข้าว, wat/วัด/temple, chedi/เจดีย์/stupa),
expanded before matching. Results group under category headers with counts, each
row showing category · street · ant chips. **The empty state is a door**: near
misses (the Levenshtein pass already computes them), the top category doors, and
"ถามมด · Ask the ants". Everything — query, chips, sort — lives in the
querystring, so every view is linkable, shareable and crawlable.

**Landed 2026-08-17.** `data/search_thesaurus.json` holds 75 groups of
equivalent spellings across both scripts. **"kow soi": 0 → 121.** The index also
matches the shelf, cuisine, brand and road a place already carries: "coffee"
reaches 1,976, "temple" 826, "นวด" 680. Results group under their shelf with
counts; an empty search offers the shelves and the ants.

**The index got SMALLER while gaining four dimensions** — 2.79 → 3.38 MB, not
4.5 — because shelf words ship once in a lookup table instead of being copied
into twelve thousand entries.

Two bugs fixed on the way. The result count showed the 200-row **cap**, telling
a reader searching "coffee" the city holds 200 cafes when the directory knows
1,976; it now reports what was found and says how many are shown. And
`tests/test_search.py` failed any query over 200 hits — a guard written to catch
a *loosened* tier returning the catalogue, which would have forbidden shelf
matching outright. It now applies only to loosened tiers.

**Not done:** the province split (`index-cm.json` / `index-cr.json`) and URL
state for chips. The size win above removed most of the urgency from the first.

---

## WO-5 — Sorts: by neighbourhood, by ancientness, by open-now

**The decision.** Category is one spine among several. The street graph (942
streets, 4,112 placed records), WO-1's founding years and the open-lamp
schedules are three more, all already computed.

**Read first.** `build.py:5253` (`toolbar()`), `:2718-2792` (the sort JS),
`:5204` (`entry_li()`, where `data-*` is minted), `data/open_lamps.json`,
**`CLAUDE.md:107`** — the toilets page sorts by distance and nothing else;
confidence belongs in chips, never in a sort.

**Steps.** `sort-age` — conditional, on the `sort-royal` pattern, wherever ≥3
entries carry `data-founded`; label **เก่าแก่ · Ancient first**; oldest first,
undated entries keep their alphabetical place below and never pretend a date.
`group-area` — a toggle regrouping a listing under street or ตำบล headers that
link to the soi pages. `chip-open` — "เปิดอยู่ · open now" computed client-side
from a baked minute-of-week attribute; **absence of hours renders neutral, never
dark-as-closed**. All three join the WO-4 URL state.

**Landed 2026-08-17.** `sort-age` (เก่าแก่ก่อน · Ancient first) reads WO-1's
register years — Wat Lo Khro at 658, Wat Phra That Doi Kham at 687. An undated
place keeps its alphabetical seat *below* the dated ones rather than sorting as
year zero. `group-area` (เรียงตามย่าน) regroups a listing under its road with
the heading linked to that road's page; places the street graph never reached
gather under "ยังไม่รู้ว่าอยู่ถนนไหน · road not known yet", because not knowing
is a fact. Both appear only where the data supports them (3+ entries), the
existing `sort-royal` rule.

**Not done: the open-now chip.** The lamp schedules are baked and ready; the
chip is its own piece of work, and the neutral-not-dark rule is the part to get
right.

---

## WO-8 — the กัญชา-กระท่อม shelf · BUILT 2026-08-17

A whole trade was invisible. The Overpass crawl had never once asked for
`shop=cannabis`, so of 12,318 records the catalogue held exactly three, and all
three were filed somewhere else: a dispensary under `sights/historic`, a
cannabis cafe under `food/thai`, a kratom shop under `medical/thai-medicine`.

**Built:** a `cannabis` crawl group (province-wide in both provinces, in
`WIDE_GROUPS`), `cannabis_hit()` in `import_overpass.py`, a five-child category
in `categories.json`, a fourteen-row facet set, `i-leaf` in the sprite, and a
night lamp in `build_open_lamps.py`.

**The hut guard.** Kratom has no OSM tag of its own, so it is found by name or
not at all — and bare กระท่อม is the ordinary word for a hut. Only ใบกระท่อม,
น้ำกระท่อม, ร้านกระท่อม and the Latin spellings are matched, or every
กระท่อมริมน้ำ resort in two provinces arrives as a kratom bar. `\bweed\b` and
never a bare `weed`, for the seaweed shops.

**Ambiguity goes to a person.** Where the NAME says cannabis and the TAGS say
something else, the place keeps the shelf its tags earned and the disagreement
is written to `cache/cannabis_review_<province>.txt`. This caught a real one
immediately: "Weed leaf" in Chiang Rai is `historic=monument` — a monument named
for the leaf, not a shop, and a rule that trusted the name would have put a
statue on the dispensary shelf. Verdicts live in `data/curated/cannabis.json`
and survive a re-crawl. The review file says out loud that the answer is often
BOTH, and points at `shelves.json` rather than forcing a binary.

**The facets are the point.** OSM says a shop exists and sometimes when it
opens. It never says whether the ฿/gram is posted where you can read it before
asking, whether you can sit down, whether anyone behind the counter can tell you
what you are buying. Those are asked, not inferred. What the crawl CAN answer
now fills automatically: `open-late` reads closing times past 22:00 including
past midnight, `crypto` reads the Lightning tags, `card`, `seating`, `delivery`.

**Landed:** 36 on the shelf. Chiang Mai 30 — 26 ร้านกัญชา, 3 คาเฟ่, 1
ร้านน้ำใบกระท่อม. Chiang Rai 6 — 3 ร้านกัญชา, 2 คาเฟ่, 1 ร้านน้ำใบกระท่อม.
Fourteen carry hours, eight a phone, six a website, one a LINE id, and **four
take Bitcoin over Lightning**, which is a genuinely local fact no other
directory of this city holds. Both provinces have a shelf map and a
`<province>-cannabis.geojson`; `weed`, `ganja` and `dispensary` now expand to
กัญชา in the search thesaurus, and `kratom` to ใบกระท่อม — bare กระท่อม stays out
of that group for the same hut reason.

**Two bugs found on the way, neither of them cannabis's.**
`enrich_sites.py` crashed with a bare `ValueError` on any OSM `website` written
without a scheme — `www.stuffchiangmai.com` — and its catch-all filed that as
"unreadable", which reads like a malformed page. **57 of the 1,003 places that
carry a website were being counted as visited-and-broken without ever being
asked.** `as_url()` now assumes `http://`, matching what check_links.py already
stored, and the first shop it unblocked gave up a Facebook and an Instagram.
Rendering was never affected — the site emits no relative hrefs from these.
Separately, `fetch_wide()` raised when any one selector gave up, throwing away
every element the earlier selectors had already fetched; it now keeps them and
marks the group `incomplete` in the cache file and on screen, because the thing
to fear was never a failure, it was a cache file that looks whole.

**The coverage gap, stated plainly because it is the whole story.** OSM is
where this shelf comes from and OSM is thin here: 28 `shop=cannabis` in the
whole of Chiang Mai. The trade is far bigger than that. The register that would
settle it — DTAM's Medical Cannabis GIS — is recorded in `data/sources.json` as
`dtam-mcgis` with status `walled`: its own terms scope it to authorised
officials, forbid copying or republication, and forbid commercial use. An
unauthenticated endpoint is not a licence. So coverage grows the way this site
has always grown it — owners claiming their own listing, and people who walked
past telling the ants. Same department publishes the Bangkok equivalent as open
data, which makes "would you publish Chiang Mai and Chiang Rai on those terms
too" a real letter worth writing, not a fantasy.

**Open for a human:** the review file; whether the licensed-shop COUNT (an
aggregate, not the data) belongs on the shelf page as an honest "we hold N of
roughly M" line — that is Nan's call, not a bot's, and nothing was published.

---

## WO-9 — the medical shelf · BUILT 2026-08-18

**The finding, and it is the worst one this site has had.** `crawl_overpass.py`
had no selector for a clinic, a hospital, a dentist, a doctor or a pharmacy,
and `classify()` had no rule to file one. Every medical record on the site had
arrived sideways from the `cm-womens-health` import — a women's-health slice,
not a medical directory. **Chiang Rai held three medical records for the whole
province.** Four records in the entire catalogue carried an address. On a
directory people open when they are ill, the clinics had never been asked for.

**Two sources, and the good one is open.**
- `importers/import_citizeninfo.py` — ข้อมูลพิกัดสถานพยาบาลของรัฐ (CITIZENinfo),
  published by DGA on data.go.th under **Creative Commons Attribution**. 10,715
  state facilities nationwide, every one with coordinates the state surveyed;
  **514 in our provinces (cm 286, cr 228) — 469 รพ.สต. and 45 โรงพยาบาล.** This
  single file is why Chiang Rai stops being empty. Dated 2020-03-14 by its
  publisher and that date rides on every record: a รพ.สต. does not move, but it
  can close, and a six-year-old pin sold as current is a claim we have not
  earned. The credit is a licence condition and travels per record.
- The new `medical` crawl group, province-wide in both. **Chiang Mai: 667
  elements → 749 records** (376 pharmacies, 107 clinics, 90 doctors, 86
  dentists, 82 hospitals).

**Three gaps found on the way, none of them the one I was looking for.**
1. `shop=chemist` had NO rule in `classify()`, so 32 Chiang Mai chemists were
   classified as nothing and dropped at import — silently, for as long as the
   crawl has run.
2. Pharmacies were shelved under `essentials` ONLY, so somebody browsing for
   medicine never met one. A ร้านขายยา is where most people here go first with
   a fever. They now carry both categories, which is what they always were.
3. **The site listed 500+ medical places and did not say, anywhere, how to call
   an ambulance.** `data/curated/emergency.json` + `emergency_band()` put 1669,
   191, 199 and 1155 at the top of the medical shelf as `tel:` links, each
   naming the agency that issues it. Numbers only — no triage, no advice. A
   directory is not a clinician.

**The facets are the shelf.** OSM says a clinic exists; it never says whether
บัตรทอง or ประกันสังคม is honoured there, which is the difference between a visit
that costs nothing and one that costs a week's wages, and no directory of this
city states it. Thirteen rows: bathong, sosec, priceboard, **foreigninsure**
(VA/FMP/CHAMPVA and travel cover — the expat question nobody answers), openlate,
open24, weekend, walkin, english, chinese, **kammuang**, parking, wheelchair.
NOTHING is inferred from category: a state hospital is not assumed to take the
gold card and a private clinic is not assumed to refuse it. That rule bites
harder here than anywhere else on the site, because a wrong "no" sends a sick
person to the wrong door or stops them going.

**`sector` is printed only where it is known.** The register states it by
construction; a crawled clinic says nothing about whether it is state or
private, so nothing is printed. โรงพยาบาลนครพิงค์ and a private clinic carry the
same `amenity=hospital`, and guessing would have been wrong both ways.

**Duplicates are proposed, never folded.** The two sources cannot merge
themselves — `cm-moph-<code>` and `cm-osm-node-<id>` are different ids — so the
big hospitals arrive twice. `importers/audit_medical_dupes.py` writes
`cache/medical_dupes_<prov>.txt` with a ready-to-paste `merges.json` line and
says what each side carries, because which id to keep is a real choice: OSM
usually holds the phone and the hours, the register holds the government code
and the state's own pin.

**Open for a human:** the duplicate pairs; and the facets themselves, which by
design cannot be filled by any crawl — บัตรทอง and ประกันสังคม are a question for
somebody at the counter. สสจ.เชียงราย's own open figure is **628 clinics of all
types (2564)**, and that is the number this shelf should be read against.

---

## WO-10 — หอสมุด · หอศิลป์ · หัตถกรรม · PLANNED 2026-08-18

Full design note: **`notes/culture-shelf-proposal-2026-08-18.md`**. Read it
before touching any of this; the reasoning is there and is not repeated here.

Six domains Nan asked for in two passes — libraries, museums, bookshops, then
art galleries, culturally important handicraft places and studios. They are in
three different conditions and want three different fixes.

**The measurement.**

| Domain | Records | State |
|---|---|---|
| Museums | 58 | crawled, one undifferentiated `sub` |
| Galleries | 14 | crawled, and conflated with studios |
| Art studios | 14 (lens) | 7 are the same records as the galleries |
| Handicrafts | 85 (`shopping/crafts`) | a `craft=*`+gift dragnet |
| Libraries | 20 (lens) | **never crawled**; 17 are CMU faculty libraries |
| Bookshops | **0** | **never crawled, and no shelf to be empty on** |

`amenity=library`, `shop=books` and `shop=stationery` appear nowhere in
`importers/crawl_overpass.py:QUERIES`. This is the home-services/community/
business failure again, which that file already documents in its own comment —
"a reader saw *the ants are still collecting* where the truth was that no ant
was ever sent." Bookshops are a step past that: they were never given the shelf.

**The rule this shelf runs on.** Massage's rule was *never infer respectability*.
Here it is **never infer whether a reader is allowed in, and never infer what
something costs.** A university library is not marked closed to the public until
somebody asks at the desk. A wrong "no" stops a person going; a wrong "public"
sends them across town to a locked faculty door.

And: **"culturally important" is not a facet.** Importance reads off the
register — OTOP tier, GI, ครูศิลป์ของแผ่นดิน, ครูช่าง — dated and sourced, the
same way the สบส. licence works on the massage shelf. This site does not award
it. No authenticity sort either: *is anyone making anything here today* is
visible from the pavement and is a door question; deserving is not one we ask.

**BUILT — step C.** `importers/audit_culture.py`, zero network, read-only,
`--emit` prints `shelves.json`-ready entries. Same contract as
`audit_massage.py`. Five reports, 59 entries proposed over 191 candidates:
LIBRARY 15/20 · MUSEUM 26/72 · CRAFT 13/85 · BOOKS 5 found under other tags ·
STRAYS 8/85. It reads names, OSM's own `museum=*` subtag (recovered from
`cache/overpass/`, where import drops it), and nothing else.

**Four findings that stand on their own, whatever happens to the rest:**

1. **บ้านถวาย is filed as `market/fresh`.** The woodcarving village is in this
   directory as a wet market, and that one record is all the village has.
2. **เครื่องเขิน, แกะสลักไม้, ตุงล้านนา and จักสาน read ZERO.** Four Lanna crafts,
   none of which any crawl can currently see.
3. **Two of the twenty "libraries" are buildings** — อาคารเฉลิมพระเกียรติใหม่ and
   อาคารพาวเวอร์ส ฮอลล์, mis-lensed by the mueang-map import.
4. **Three stationery shops sit on three different wrong shelves** (`food/thai`,
   `shopping/diy`, `essentials/convenience`) because there is no right one.

**Two regex traps, found and fenced — both are house-style warnings:**
`(?<!ห)วัด`, because **จังหวัด ends in the letters วัด** and made every
"พิพิธภัณฑสถานแห่งชาติ จังหวัด…" a temple museum; and `\bse-ed\b`, because an
optional-separator SE-ED matches the English word **"Seed"** and filed
Liberated Seed Roasters as a bookshop.

**BUILT — step B, the tree.** Two new cats and ten new museum children, **purely
additive: 276 lines in, nothing removed, nothing re-keyed.**

- `read` — อ่าน-หนังสือ · Books & Libraries, 11 children
- `crafts` — หัตถกรรม-งานฝีมือ · Handicrafts & Makers, 11 children
- `museums-galleries` — +10 children; `museum` and `gallery` STAY at the head as
  the catch-alls that hold all 72 records today

**`shopping/crafts` and `sights/library` were not touched and keep every record
and every URL they have.** A record reaches the new cats by gaining a SECOND
cat through `shelves.json` — the move the coworking sweep used to put Hub 53 on
the business shelf without taking it off the hotel one. Nothing 404s.
`audit_culture.py --emit` now derives `add_cat` by READING the tree
(`sub_to_cat()`), so the two cannot drift; it currently proposes `read` on 20
records and `crafts` on 13, with no sub lacking a shelf.

**BUILT — the import rules.** `import_overpass.py:classify()` learns
`amenity=library`, `shop=books` (honouring OSM's own `second_hand=*`),
`shop=stationery`, `shop=newsagent`, `shop=art` and `shop=pottery`.
**`amenity=library` deliberately gets NO sub** — OSM never says whether a
library is the district public one or a faculty's, and that is the difference
that decides whether a reader may walk in. `shop=fabric`,
`shop=musical_instrument` and `shop=antiques` are crawled but left unclassified
on purpose: they have no honest shelf yet, and writing a rule for data nobody
has looked at is the guess this file exists to prevent.

**RUNNING — step A, the crawl.** Two new groups in `crawl_overpass.py`:

- `reading` — `amenity=library`, `shop=books`, `shop=stationery`,
  `shop=newsagent`, and a Thai name selector for ร้านหนังสือ|เครื่องเขียน|ห้องสมุด
- `making` — `shop=art|pottery|fabric|musical_instrument|antiques`, plus name
  selectors for the crafts. **Every Thai term is a compound.** Bare ตุง, เงิน,
  แกะ and ร่ม are ordinary words and none is asked for — ร่ม alone matches
  รพ.สต. ร่มเกล้า, and วัวลาย is a ROAD as well as the silver quarter. Same
  discipline as the hut guard on กระท่อม. `shop=jewelry` is deliberately NOT
  asked: here it is carried by the ร้านทอง gold traders, a different trade.

**Both are in `WIDE_GROUPS`**, and the reason is structural rather than a
preference: **ห้องสมุดประชาชนอำเภอ is one per อำเภอ by construction**, so a box
round the clock tower can only ever hold Mueang's — which is exactly why the
shelf reads as CMU's internal libraries. And the craft villages are villages:
Ban Tawai and Bo Sang sit within a few hundredths of a degree of the CM box
edge, which is luck, not coverage.

**The crawl was QUEUED, not raced.** A `--group schools --fetch` crawl was
already in flight when the go came, and a second concurrent crawl would have
doubled our request rate against Overpass under a User-Agent that calls itself
a gentle one-off harvest. WO-10's crawl waits on that PID and starts when it
exits. Likewise `categories.json` was not written until `cache/build.lock`
cleared.
- **D — the `reading` facet set**, `appliesToCat` on all three cats, every facet
  carrying `ask_th`/`ask_en` as the door survey's script.
- **E — KNOWN_EMPTY** with a reason per shelf, after A and C report.
- **F — the join.** Temple libraries (หอไตร) can carry `attrs.holdsManuscripts`
  and link to that wat's holdings on wichaa.net: **6,990 manuscripts already
  stamped with รหัสวัด, and 596 wat records keyed the same way.**
  `importers/link_wichaa.py` is the pattern. This is the highest-value item
  here and the one nobody else can build.
- **G — a `craft-words` reader sheet.** Waits. The copy decides the count.

**Open for a human:** whether galleries split commercial/artist-run at all —
OSM cannot say who sells the work on a wall, and both shelves start empty.

---

## WO-11 — the schools shelf · BUILDING 2026-08-18

**The gap, and it is the worst one found yet.** A directory for two provinces
held **fourteen schools**, and every one of them was international — because
`crawl_overpass.py` asked for `amenity=school` only where the name matched
`International|นานาชาติ`. One regex, written at launch and never revisited,
decided that the only schools worth crawling were the ones a foreigner might
attend. `classify()` then filed anything tagged `amenity=school` as
`school-intl`, so the moment that filter came off it would have labelled 800
village schools international.

Nan's brief: honour, map and differentiate **all** schools — language schools,
muay thai schools, religious schools included — with particular care for the
multilingual and farang-facing ones, because those are what people search for.

**Four registers found, all state-published, all free, no key.**
- `OBEC_SCHOOL_007` (สพฐ.) — **1,302 government schools** in the two provinces,
  with coordinates, class levels, enrolment, education service area, and a
  **telephone for 88% of them**. On a site whose overall contactable figure is
  about 19%, this one file is the largest deposit the directory has ever taken.
  424 of the schools stand on the ดอย.
- `gdpublish-cer` (สช.) — the private-school licences: **225 private schools,
  of which 25 are international** against OSM's 14. Carries the official type,
  the levels, the founding year and who holds the licence — five of them are
  licensed to a **wat**.
- `68_113` (ONAB) — โรงเรียนพระปริยัติธรรม, the monastic schools. Catalogued,
  Open Data Common, **not yet fetched**. Worth doing next because it joins the
  wat register: these schools sit inside named temples and รหัสวัด reaches them.
- `univ_uni_11_03` (MHESI) — the university list. Catalogued, not yet fetched.

**Built.** `importers/import_obec.py`, `importers/import_opec.py`, a widened
`schools` crawl group (14 selectors, now in `WIDE_GROUPS` so Chiang Mai is
covered province-wide like the register is), `school_sub()` in
`import_overpass.py` with the guards below, a 20-child `school` shelf in
`categories.json`, a 15-facet `school` set, schema.org types, and
`audit_medical_dupes.py` generalised to audit either register against the crawl.

**Guards that earned their keep, each caught by a dry run before it shipped.**
- มหาวิทยาลัย **contains** วิทยาลัย — Chiang Mai Rajabhat University arrived as
  a vocational college. Bare เทคนิค is worse: เทคนิคการแพทย์ is *medical
  technology*, and CMU's faculty of it was filed as a trade school.
- Bare มวย cannot be matched: **หมวย is an ordinary nickname** and ร้านหมวย is
  Muay's shop. Only มวยไทย, ค่ายมวย, สนามมวย, ยิมมวย and Latin `\bmuay\b`.
- A campus is full of buildings that are not schools. 37 records —
  ภาควิชาเคมี, โรงอาหารคณะครุศาสตร์ — were on the universities shelf, so
  "universities in Chiang Mai" answered with a canteen. They keep their own
  child rather than being dropped.
- **`international` is also what `food_sub()` returns for international
  cuisine.** An unguarded dual-shelf test on the sub alone put **579
  restaurants on the international-schools shelf**. Gated on the category now.
- An id must carry digits: `place_slug()` takes the digits out of an id for the
  filename and falls back to the id with punctuation stripped, so Thai-script
  slugs gave all 220 private-school records the stem `cmopec` and they would
  have overwritten one another's page. The register's own ลำดับ is used.

**The pins, measured rather than assumed.** Thai mappers on the OSM forum
report ~6% bad GPS in government sources of this kind. Against the register's
own geography it is **5 wrong pins in 1,302 — 0.38%**: two in other provinces
(one in Bangkok, one past Khon Kaen), three tens of kilometres from every other
school in their own district. The test is two-stage and deliberately not a flat
number — **อมก๋อย reaches the Tak border and its schools sit 45 km from their
district median while being exactly where they should be**, so a flat 25 km
rule would have thrown away 104 highland schools, which are precisely the
schools this shelf exists to carry. Refused pins keep their record.

**A measured dead end, so nobody looks twice.** The สช. *นอกระบบ* (non-formal)
export holds 134 rows nationwide and **zero** in either province — so the
register that ought to list this city's language schools, muay thai camps,
cooking schools and driving schools is empty in the published copy. Those
shelves are filled from the crawl and by name, the way kratom had to be.

**Where it stands.** The crawl landed clean — Chiang Mai 86 → **749** elements,
Chiang Rai 12 → **368**, neither incomplete. The shelf now reads **2,416
schools** (1,463 cm / 953 cr) against the fourteen it held this morning, **1,203
with a phone**, 174 awaiting a pin. **Nineteen of the twenty children are
populated**, cooking, dance and massage-school among them, all three filled from
names alone.

**`sport=muay_thai` returned ZERO across both provinces** — and the false-zero
recheck asked twice before believing it, so that is real, not a failed query. All
**14 ค่ายมวย** on the shelf, Buakaw Banchamek's gym and Kawila Boxing Stadium
included, were found by name. The หมวย guard is the whole reason that worked.

**311 duplicate pairs** (169 cm / 142 cr) — a school mapped in OSM and listed in
the register arrives as `<prov>-osm-…` and `<prov>-obec-…` and no merge on id can
see they are one place. `cache/school_dupes_<prov>.txt` has a paste-ready
merges.json line for each. **138 of them (44%) have an identical name and sit
within 50 m of each other**, which is the obvious first batch; the other 173 need
an eye. Nothing is merged automatically and nothing should be — the house rule is
human-confirmed pairs only.

**The one empty shelf is monastic**, and it is on `KNOWN_EMPTY` with its reason:
OSM has no tag for a โรงเรียนพระปริยัติธรรม, and the ONAB register that names
them has not been fetched. That is a known next step, not a hope.


**Two bugs only a browser found, after every structural gate was green.**
- **`sector: "state"` is set by two registers now**, and build.py printed the
  one label it had: every government school in both provinces was captioned
  **"สถานพยาบาลของรัฐ · state health facility"**. 1,292 pages. The check is
  gated on the category now and a state school is called one.
- **None of the register facts reached the page.** Levels, education area,
  enrolment, highland, ขยายโอกาส — all imported, all carried in `attrs`, none
  rendered, because attrs only appear where build.py names them (the gemba
  count was 86 keys carried, ~20 rendered). A school block was added beside the
  temple one. `foundedBE`/`foundedCE` are reused rather than a new key invented,
  so the private register's founding years render through the row the wat
  register already had — and sort-by-ancientness reaches schools for free.

**A third bug, older than this order, found by chasing the second.** `bi()`
escapes both halves — so a caller that hands it a sentence with a link in it
gets the anchor back as VISIBLE `&lt;a href=…&gt;` text. Three callers were
doing it, and only one was mine:
- the **weed.th provenance line** (WO-8b) — the "name and address from weed.th"
  credit has been shipping as a literal HTML tag on all **658** dispensary
  pages, so the link back that the attribution depends on was never a link;
- `/toilets.html`'s method note, where "see the walking-pace maps" printed its
  own tag at the reader;
- the register credit added here.

`bi()` takes `raw=True` now, escaping still the default, with the reason in its
docstring. **grep-based gates cannot catch this** — they look for the URL, and
the URL is there, inside escaped text. Verified after the fix by counting
escaped anchors across all 17,514 pages rather than by reading one.

Structural checks pass a page that says the wrong thing in perfectly valid
HTML. Both of these were invisible to publish_gate, alt_text and facets.

**Open, in order.** Settle `cache/school_dupes_<prov>.txt` into `merges.json`,
starting with the 138 exact matches · fetch the ONAB monastic register and join
it through รหัสวัด to the temples these schools sit inside · fetch the MHESI
university list so the universities shelf stops depending on how a mapper felt ·
walk the 174 pinless schools onto `/pins.html` · deploy the worker so owners can
tick the 13 new facet keys.

## WO-12 — มวยไทย: events, locations, culture · BUILT 2026-08-19

Full design note: **`notes/muay-thai-proposal-2026-08-19.md`**. Read it before
touching any of this; the measurement and the rule are there.

**The gap, in one line.** Muay thai was twenty records on two shelves, split
by how a mapper tagged the door — thirteen ค่ายมวย under `school/muaythai`
(found by NAME: `sport=muay_thai` is tagged on ZERO elements in both
provinces), six under `learn/gym` between the fitness centres, one stadium
(Kawila) filed as a camp — and **no stadium shelf, no Thapae, no Loi Kroh, no
Chiangmai Boxing Stadium, no event, no festival day, no primer.** Nan's brief:
"muuuuuuccch richer and deeper — events, locations, and culture."

**The rule.** The venue states its own nights, prices and door rules, or the
page says nobody has stated them; and no ranking of rings into real and
touristic. `data/curated/fight_nights.json` carries `days` only for nights the
VENUE states (`stated_by`, `source`, `fetched`); a listing's word goes in
`days_reported`, dated, and renders as reported. Prices keep
`_pricesVerified: false` until read at the door.

**BUILT — locations.** Top-level cat `muaythai` (stadium · camp · gear),
additive; `importers/audit_muaythai.py` (names + the crawl's own sub, zero
network, `--emit` → 20 shelves.json entries, applied); three curated stadiums
from their own sites, dated, with pins that say what they are (Thaphae = the
gate, `approx`; Loi Kroh = the middle of Lane 3, `approx`; Chiangmai Boxing
Stadium = `needs-pin`, on /pins.html); `known_facts()` renders fight nights,
tickets (unwalked mark), training, second phone, pin note; facet set
`muaythai` (15, sits BEFORE the school set); `muaythai/gear` in KNOWN_EMPTY;
search re-mined so สนามมวย and "fight" narrow to the shelf; glove icon,
schema.org types, svcbar chip `ดูมวยคืนนี้`.

**BUILT — events.** `muaythai_layer.raw_events()` merges venue-stated nights
into `EVENTS_RAW` as ONE weekly event per stadium with a BYDAY list (the
`.ics` RRULE gained a BYDAY-list branch); source "fight-nights". Two national
days in `festivals.json` — วันมวยไทย 6 Feb, วันนายขนมต้ม / World Wai Khru 17 Mar
— canon 33 → 35, test bumped on purpose.

**BUILT — culture.** `/muaythai.html`: who fights tonight (the reader's own
weekday), the weekly board, a card per venue with source and date, the
unconfirmed rings (Kalare, Anusarn, Pavilion) and the Chiang Rai line, the
shelf's porch with every camp and its reach, and the primer from the seat —
wai khru, mongkhon/prajiad, the four musicians, the five rounds, the bettors,
tickets and the free-pickup commission, fourteen words with script/RTGS/tone,
the word มวย, the two days, the north (เจิง, ตบมะผาบ, มวยท่าเสา, temple-fair
cards) — and the joins to wichaa stated from this side (/yant, /waikhru,
/thairoots). llms.txt tells a bot to read `stated_by` before repeating a night.

**NOT done, by design.** No crawl (Nan's go); no Facebook scrape of nightly
cards; no fighters, results or rankings; no real-vs-touristic sort; no
children's-bouts law paragraph on a fight board.

**Open, in order.** The door survey (15 asks, 19 camps, 6 contactable) · three
pins (Chiangmai Boxing Stadium, Loi Kroh's ring, Thaphae's door) · three
boards read to clear the price mark · gear shops by name and by walk · camps by
name (Team Quest, Chay Yai, Siam No.1, Manop's, Kiatbusaba…) each from its own
page, dated · reader sheets (`muay-words` first; `muay-money` waits on walked
prices) · the wichaa article (เจิง, the ram muay as wai khru, the
mongkhon/prajiad/yant chain — *where* on wichaa, not *whether*) · Loi Kroh's
weekdays by their own event pages.

---

## WO-13 — รถ-เดินทาง: the transport layer · PROPOSED 2026-08-19

Full design note: **`notes/transport-proposal-2026-08-19.md`**. The
measurement, the rule and the sequence are there and are not repeated here.

**The gap, in one line.** Nan asked "do we have a flights widget yet? bus
widget? train widget?" — **flights yes** (`flights_layer.py` → `/flights.html`
+ `widgets/flights.html`, live, 34 routes, `as_of 2026-08-02`, Aviasales marker
declared) **but reachable only from `my.html`'s gallery** — not the transport
shelf, not `/widgets.html`, not the svcbar; **bus no; train no.** The
`transport` shelf is 536 records, 435 of them fuel pumps; its 53 "stations" are
OSM scraps with zero phones and zero hours, the railway station among them
under the name "เชียงใหม่"; the songthaew child has no `match` and no
KNOWN_EMPTY reason; `pier` is an orphan sub; five `amenity=taxi` ranks sit in
`cache/overpass/*/stations.json` and are dropped at `import_overpass.py:431`.

**The rule.** The operator states its own timetable, fare and terminal —
dated, by name — or the page says nobody has. A board is a season, never a
departures screen. No ranking of ways to move; no tourist sorting; fares carry
`_pricesVerified: false` until read at a window. Bakes flat like the flights
board; referral links declared; nothing enters on memory.

**Sequence.** (1) repair the orphan — link the flights board from the shelf
band, `/widgets.html` and a svcbar chip, half an hour, no data; (2) the
zero-network split of `station` into train · bus-terminal · songthaew · pier ·
taxi from the tags already in cache; (3) the fetch list, Nan's go, one dated
manual run — SRT, Green Bus, Nakhonchai Air, Sombat Tour, บขส., AOT CNX/CEI,
DLT terminal pages, Travelpayouts marketplace for the bus/rail partner;
(4) `buses.json` · `trains.json` · `songthaew.json` → `/buses.html` ·
`/trains.html` · `/transport.html` + two mini-boards; (5) curated terminals and
the airport card; (6) the door survey at five terminals; (7) reader sheets;
(8) the first `asked.json` question — airport to the old city, how and for how
much. Steps 1–2 need no network and could ship on the next walk.

---

## WO-14 — สักยันต์-รอยสัก: the tattoo shelf · BUILDING 2026-08-19

Full design note: **`notes/sakyant-proposal-2026-08-19.md`**. Read it before
touching any of this; the measurement and the rule are there.

**The gap, in one line.** Thirty-four `shop=tattoo` points, all filed as
"Modern studios"; **สักยันต์, เจาะ and ลบรอยสัก empty on the live site** — the
สักยันต์ rule matched a lens no record has ever carried, so the shelf said
*Chiang Mai has no sak yant* while wichaa.net/yant, the 209-entry photo index
and a 52-page price book sat on the same machine, unlinked. Phone 6/30, website
6/30, blurbs 0, prices 0; a minigolf on the shelf; every studio also riding the
sights shelf through a lens mapping older than the category. Nan's question:
*"can the already pretty great information be even more enriched?"* — the
great part was on wichaa; Mot Dang had none of it.

**The rule.** Three things are sold under one word and the shelf keeps them
apart: a สำนัก or ajarn charges a yant with a katha (สักยันต์), a studio inks
designs yant-shaped or not (ร้านสักสมัยใหม่), a beauty shop tattoos brows and
lips (สักคิ้ว-สักปาก). A studio named after a yant is a studio until its own
page says an ajarn works there. Two price sources — the FAQ's hourly framing
and the design book's per-design rate card — are stated separately, each with
its date and `_pricesVerified: false`; the temple figure is transport and
interpreting, the monk's offering is named as separate and never folded in.
No screenshot is republished; no authenticity sort; สักขาลาย is its own
tradition and not a section here.

**BUILT — zero network, 2026-08-19.** `categories.json`: สักยันต์ matches
`sub: sak-yant` like its siblings; fifth child สักคิ้ว-สักปาก · Cosmetic
tattoo (`sub: cosmetic-tattoo`). `LENS_TO_CAT["tattoo"]` → `["tattoo"]` (all 31
mueang-map points are inside the Overpass crawl, so nothing is lost and the
studios leave sights). `importers/audit_tattoo.py` (names + the crawl's own
sub, review lists, `--emit`). `data/curated/retags.json` — a new, deliberately
small layer for an OSM tag a person has read against the door and found
wrong, evidence line required; first entry the minigolf. Sak Yant Chiang Mai
as a curated record in `additions-chiang-mai.json` (same id, tier curated):
`sub: sak-yant`, rate card, FAQ framing, second phone, resident ajarns, the
five-precepts doctrine, blurbs ไทย · EN, dated sources; `known_facts()` gained
a generic `priceCardTh/En/Via` row ("ราคาที่ประกาศ · Published prices", unwalked
mark) so a venue's own board renders anywhere. `yant_band()` on the
shelf page — what wichaa.net/yant, /na and the article ARE to this shelf, with
the fact that makes the join true (the นกคู่ on Arak Road is ms 6985's
ยันต์สาริกาคู่, a century apart), ending in the door sentence. `asked.json`
`sak-yant` drafted with `asked_new.py`, `draft: true`, lead/notes/links filled;
`notes/asked-sak-yant-2026-08-19.md` carries the leads. Search tables re-mined
(`search-core/mine.py motdang` + `sync.py`): สักคิ้ว-สักปาก / brow / lip /
cosmetic tattoo now narrow to the shelf. **New: `data/curated/moved.json` +
`write_moved_stubs()`** — correcting nameEn moved the SYCM page from
`…tatoo…` to `…chiang-mai…`; the old path now forwards (meta refresh +
canonical, noindex), written only where the new page exists. Fix-ledger
entries under มดเอง. Verified in a scratch build (`build.DOCS` redirected):
tattoo shelf 29 + สักยันต์ (1) + Chiang Rai สักคิ้ว-สักปาก (1), band renders,
SYCM page shows the board, minigolf on sights, draft unpublished;
`test_facets`, `test_asked`, `test_publish_gate`, `test_plan_routes.js` pass.

**NOT done, by design.** No crawl; no scrape of Google Maps or Facebook for
สำนัก; no plates from the design book; Gao Yord / the bamboo studios not
shelved under สักยันต์ on their names; no facet yet; no `/sakyant.html` yet
(the asked page carries the core).

**Open, in order.** (1) the two สำนัก from their own pages — อาจารย์ไก่
บารมีนาคราช, Spiritual Sak Yant / Ajarn Vee — → records → delete `draft` →
card → `make_post.py sak-yant`; (2) the brow shop (photo-mine #4) and the
Chiang Rai removal clinic (#5) — pin + source → `removal` off KNOWN_EMPTY;
(3) `/sakyant.html` and the lineage card on the SYCM page; (4) the three
yant-named studios from their own pages; (5) the door sentence is written —
three places, then the facet; (6) tell OpenStreetMap about the minigolf and
the "Tatoo" name:en; (7) `tests/test_search.py` looks for a `const norm=`
marker that left build.py when the core moved to search-core — it fails
before it tests anything and is in neither walk; retire or repoint it.

---

## WO-14 — เรียนทำอาหารไทย: the class board, the shelf, the primer · BUILT 2026-08-19

Full design note: **`notes/cooking-classes-proposal-2026-08-19.md`**. Read it
before touching any of this; the measurement and the rule are there.

**The gap, in one line.** Thai cooking classes were twenty-five records on
seven shelves, split by how a mapper tagged the door — nine on `school/cooking`
(found by NAME: `amenity=cooking_school` is on ZERO elements in both provinces),
nine among the restaurants on `food/thai`, two on `food/vegetarian`, three on
`school/training`, one on `school/music-art` (the "art school" rule beat
"culinary"), one on `repair/auto` — **with no axis of kind, no session, no
price, no pickup radius, no calendar day, no primer, and zero records in Chiang
Rai.** Nan's brief: "similar to muay thai — Thai cooking classes (all kinds)."

**The rule.** The school states its own sessions, prices and pickup radius, or
the page says nobody has; and no sorting of kitchens into tourist and real.
`data/curated/cooking_classes.json` carries `sessions` only as the SCHOOL
states them (`stated_by`, `source`, `fetched`); `days` is BYDAY codes only
when the school states weekdays and null when it does not — null means NOT
STATED, never closed. Prices keep `_pricesVerified: false` until read at the
door. Nothing on the board becomes an event: a daily class is a booking.

**BUILT — locations.** Top-level cat `cooking` with nine children (class ·
farm · home · vegan · northern · dessert · carving · hotel · vocational),
additive; `importers/audit_cooking.py` (names + the crawl's own sub, zero
network, `--emit` → 22 shelves.json entries, applied, plus three hand entries
from the schools' own pages); classifier fix for "Culinary Art School" and
`amenity=cooking_school` mapped; two merges (Thai Secret node+way, the two
Thai Kitchen Cookery Centre nodes); four curated schools from their own sites
— Mama Noi, Grandma's Home (CM), Suwannee, Akha Kitchen (CR) — all
`needs-pin`, on /pins.html; eight records enriched from their own sites
(`enrich.json`); `known_facts()` renders sessions, price (unwalked mark),
pickup, group size, menu, language, pin note; facet set `cooking` (23, sits
BEFORE the school set; two licence facets, positive only); `cooking/vocational`
in KNOWN_EMPTY with its reason; search re-mined so สอนทำอาหาร and "cooking"
narrow to the shelf without hijacking "hotel", "market", "vegan", "northern";
mortar-and-pestle icon; schema.org School; svcbar chip `เรียนทำอาหาร`.

**BUILT — the board and the day.** Twelve schools on the board (four state
weekdays, eight state sessions only), one row untied (Thai Akha Kitchen — one
shared token is not a match; `maybe_place` for a person), three unread sites
named and dated, four unconfirmed names, a Chiang Rai line. กินเจ added to
`festivals.json` — canon 35 → 36, test bumped on purpose.

**BUILT — culture.** `/cooking.html`: which class today (the reader's own
weekday), the weekly board, a card per school with source and date, the shelf's
porch with every school and its reach, nine primer cards (the market and the
five tastes · galangal is not ginger · the mortar · the wok · the Northern menu
and sticky rice · เจ-มังสวิรัติ-วีแกน · money and the commission · twenty words ·
the paper on the wall) and the joins (wichaa /thairoots, /taste, /festivals/
kin-je, the markets shelf). llms.txt 🍳 section. Reader sheet `cooking-words`
(two sides, measured); `cooking-money` deliberately not written. Fix ledger
entry (มดเอง).

**NOT done, by design.** No crawl (Nan's go); no booking-platform scrape; no
rankings or reviews; no tie on one shared token; no vocational record on
memory.

**Open, in order.** The door survey (23 asks, 25 schools) · four pins (Mama
Noi, Grandma's, Suwannee, Akha Kitchen) · three boards read to clear the price
mark and ship `cooking-money` · Thai Akha Kitchen ↔ Thai Akha Cooking School
at the door · the vocational shelf by each institution's own page
(Polytechnic, DSD 19, CMRU คหกรรม, the อาชีวะ colleges) · names with no readable
site (Thai Orchid, Galangal, Basil, Smart Cook, the town's first school) ·
hotel studios beyond Four Seasons · more Chiang Rai · the first `asked.json`
question · the wichaa article on the Northern kitchen (*where*, not
*whether*).

---

## WO-19 — ช้าง: the register, the shelf, the city's elephant names · BUILT 2026-08-19

Full design note: **`notes/elephant-proposal-2026-08-19.md`**. Read it before
touching any of this; the measurement and the rule are there.

**The gap, in one line.** Of 16,268 records, 66 carried ช้าง or "elephant"
in the name and **not one was an elephant camp** — `crawl_overpass.py` has
never asked for `tourism=zoo`, `attraction` or `theme_park`, so Maesa, ENP,
Patara and the whole Mae Taeng / Mae Wang / Mae Chaem valley were never
fetched; no hospital, no elephant day, no primer; and the manuscript
catalogue held **31 elephant witnesses** (a ลักขณะช้าง marks treatise, two
สู่ขวัญช้าง, the Chaddanta jataka ×4, the local white-elephant jatakas) that no
article had ever looked at. Nan's brief: "an enrichment on elephant-related
topics for Motdang AND wichaa."

**The rule.** The venue states what happens with its elephants — riding,
bathing, shows, hands-off, how many — or the page says nobody has stated it;
the law says what is registered; and no camp is ever ranked into ethical and
unethical, sanctuary and show. "sanctuary" and "ethical" are the venue's
words, quoted, dated. `data/curated/elephants.json` carries `stated` with the
value **`unstated`** where the pages read did not say — neither a no nor a
yes. Prices are the posted spread, `_pricesVerified: false`. No facet is ever
ticked from a name, a shelf or a website.

**BUILT — the shelf.** Top-level cat `chang` (camp · care · craft) after
`cooking`, additive; `importers/audit_elephant.py` (names + tags, zero
network, five reports, `--emit`; fences for ช้างเผือก / ช้างคลาน / ดอยช้าง /
ลุงช้าง / โรงพยาบาลช้าง(?!เผือก)); **16 curated records** in
`additions-chiang-mai.json` from their own sites, dated, pins at the
precision earned (5 from the venues' own map embeds or JSON-LD, 5 from the
gazetteer's road/tambon tiers, 6 `needs-pin` on /pins.html); Poopoopaper →
craft by name; the Anantara resort (CR) by its own name + the GTAEF page;
`known_facts()` renders selfDescription / ridingStated / elephantProgram /
elephantsStated; facet set `chang` (16, unticked); icon `i-chang`;
`TouristAttraction` / `VeterinaryCare` / `Store`; svcbar chip `ช้าง`; shelf
band; llms.txt 🐘 section.

**BUILT — the register.** `/chang.html` (`elephant_layer.py`): the table
(riding · bathing · shows · hands-off · elephants · posted; bold = stated in
words, italic = unstated), a card per venue with its self-description in
quotation and its source, the unreachable by name (Chai Lai Orchid 403,
Maetaman, Ran-Tong, Elephant Rescue Park 403, FAE 403, Anantara 403, Four
Seasons 403), the unconfirmed (Elephant Valley Thailand), the shelf's porch
with every camp and its reach, the two laws and the certifying bodies named
as what they are, Lampang's institute and hospital with phones, fourteen
landmark cards on the city's elephant names (*tradition holds*) plus the
live list of every record carrying the elephant in its name, and the primer
(ปาง, the mahout and the hook, the white elephant's marks, money from the
register, five questions at the gate, fifteen words, the roots, the national
day). Joins to wichaa stated from this side.

**BUILT — calendar.** วันช้างไทย 13 March in `festivals.json` (national,
fixed, general-knowledge); canon 36 → 37, test bumped on purpose.

**BUILT — wichaa.** `content/entity-chang.md` + the `chang` row in
`ENTITIES` / `ENTITY_HOOKS` / glossary / thesaurus in `wiki.py`; aliases are
compounds verified witness by witness (never bare `cang` — Bojjhaṅga; never
`chang` — ตำนานช้างแส่น is Chiang Saen).

**NOT done, by design.** No Facebook / Google / TripAdvisor scrape; no
welfare verdict, no ranking, no recommended list, no sort by hands-off; no
invented Thai names; no Lampang records. ~~No Overpass crawl~~ — run
2026-08-20 on Nan's go: `elephants` group (zoo · theme_park · attraction),
WIDE both provinces, FENCED (only elephant-declaring names enter, via
`chang_hit()` borrowing audit_elephant's rules; 212 CM + 78 CR other
attractions → `cache/elephant_review_<prov>.txt`, the menu for a future
attractions order). CM 21 camps, CR 1 (Ruammit); 8 merges keep the curated
ids and adopt surveyed pins (Maesa, ENP, Patara, TEH, HEH, Chiang Dao ETC;
EJS keeps its office pin; `elephant Freedom` deliberately NOT merged with
EFV — 2.7 km apart, door survey settles it); shelf 18 → 30, needs-pin 6 → 3.

**Open, in order.** CR's `tourism=zoo` selector (`crawl_overpass.py cr
--fetch --group elephants` on a calmer day — cache says `incomplete`) · the
three pins (BEES, ChangChill, Kindred Spirit) and the White Elephant
Monument · the thirteen no-register-row camps' own pages read → register rows (Anantara, Doiinthanon,
Elephant retirement park, New Elephant Home, Kanta, Hug, Adventure, Pride,
Camp Chi, Ghok Dee, Jamlearn, elephant Freedom, Ruammit) · the door survey
(the 16 facets are its script; `elephant Freedom` vs EFV is its first
question) · one gate read to clear a price · the unreachable by phone or
LINE · reader sheets · the shelf card on the next `make_shelf_cards.py` run ·
ms 538 (ลักขณะช้าง) read leaf by leaf.

---

## WO-15 — 🏷 Tags: the cross-shelf layer · BUILT 2026-08-19

Design note: **`notes/aggregators-and-tags-proposal-2026-08-19.md` §4** (the
Quora move, translated). Nan's go: "go on WO-15 tags, zero network."

**The finding.** The records held 140 distinct `attrs` keys and the site
rendered about twenty. `cuisine` on 2,125 records, `diet` on 213, `payment`
on 142, `wifi` on 1,229, `wheelchair` on 404, `brand` on 1,238, `crypto` on 45
— all of it readable on one place page at a time and reachable by nothing
else: no page for "vegan", no page for "bitcoin", no page for "7-Eleven",
and search found them only when the word was in the NAME. A shelf says what
kind of place this is; nothing said what a place *also* is.

**Built — zero network, everything from what was on disk:**
- `data/tags.json` — **73 tags in 13 families** (cuisine 34 · diet 5 · pay 4 ·
  comfort 10 · hours 2 · access 2 · place 1 · honours 3 · school 2 · medical 4
  · fuel 4 · wat 2), each with Thai/EN, a glyph and **exactly one rule** over
  a field the record carries (`attr` · `attr-dict` · `attr-list` · `attr-true`
  · `facet` · `moat` · `royal` · `food-award`). No tag without a rule, no rule
  without a source field; the vocabulary was mined first (≥10 records each)
  and nothing was invented. Thresholds: `min_tag` 3 (a page), `tag_shelf_min`
  8 (a tag×shelf page), `brand_min` 5.
- **Brand tags generated per chain** from `attrs.brand` through the same
  `_brand_index` the brand shelves fold by — **47 chains** (7-Eleven 330/129,
  PT, บางจาก, PTT, Café Amazon, the banks, KFC, Lotus's, Cosmo (CR only) …),
  slugs ASCII with accents folded (cafe-amazon).
- `tags_layer.py` — `assign()` right after `load()` (every place page already
  wears its pills), `pills()`, `search_words()`, `emit()` before the sitemap.
  `build.py`: the four hooks, `tag_pills()` after `facet_panel()`, tag words
  folded into the search index's `k`, 🏷 in the svcbar, a marigold pill style,
  `tags` + `tagVia` on every tagged record in `data/places.json`, a `## 🏷 Tags`
  section in llms.txt, `shelf_map(label_th=, label_en=)`.
- **Pages:** `/<prov>/tag/<slug>.html` — grouped by shelf with a heading per
  shelf (each record once, under its first shelf), the shelf map, the toolbar,
  GeoJSON + JSON downloads, an "also catalogued by" line (HappyCow · BTC Map ·
  Wheelmap · CICOT · the MICHELIN Guide, `rel=nofollow`), ItemList + breadcrumb
  JSON-LD; `/<prov>/tag/<slug>--<shelf>.html` where a shelf holds 8+ (membership
  = ANY shelf the record stands on, so an open-late pharmacy filed under
  essentials still reaches open-late--medical); `/tags.html` — *Tag (count)* by
  family, both provinces, Yahoo-style; `/data/tags.json`, `/data/tags/<prov>-
  <slug>.json`, `/data/<prov>-tag-<slug>.geojson`.
- **Landed (scratch build, 223 s, 17,933 pages):** **182 tag pages + 163
  tag×shelf pages** (CM 117 tags with a page, CR 65), **5,483 records tagged**
  (CM 4,298 of 11,677 · CR 1,185 of 4,595). Biggest: old-city 1,313 (computed from the pin and
  `MOAT_POLY`, never typed) · wifi 931/273 · 7-Eleven 330/129 · open-24h
  251/49 · outdoor seating 214/46 · wheelchair 174/21 · vegetarian 131/21 ·
  vegan 85/17 · bitcoin 30/15 · michelin 14 · royal temples 7/3. Empty on
  purpose and listed as such: ngv (one CNG pump).
- `tests/test_tags.py` — the contract (rule/th/en/family/kind), **a defined
  rule that matches nothing anywhere FAILS** unless named in KNOWN_EMPTY with
  a reason, page exists ⇔ count ≥ threshold, h1 = rows = tags.json =
  places.json, no tag×shelf page under 8 and none missing over it, every
  assignment carries a known `tagVia`, pills on tagged place pages link only to
  pages that exist, untagged pages show none, sitemap membership, no /Users/.
  **PASS.** Added to `standing_walk.sh` as an advisory (a wrong count is not a
  broken site). `README.md` gained a 🏷 Tags section beside Facets.

**Two bugs found in passing, both in `shelf_map`, both fixed:**
1. The ten named pins on every shelf page linked `p/<slug>.html` — from
   `/cm/food/index.html` that is `/cm/food/p/…`, a **404** (confirmed live).
   The JS click handler follows the nearest ROW's link, so mouse users never
   saw it; keyboard, no-JS and crawlers did. Now `"../" * (depth-1) + "p/"`.
2. The dots are packed with **row indexes** that md.js resolves against the
   DOM's `li[data-n]`, but `fold_rows` folds brand rows into `<details>`
   shelves and so reorders the DOM. Measured: on food (20 brand folds) the dot
   positions correlated **0.11** with the rows they pointed at; on wat (no
   folds) 1.00 — hovering a food dot named the wrong shop and clicking it opened
   it. `fold_rows(order_out=)` now reports the emitted order and the cat page
   draws the map from it (verified: 0 mismatches over 1,085 essentials rows).
   Tag×shelf pages deliberately carry no map for the same reason.

**Not done, on purpose:** OG cards for tag pages (`make_shelf_cards.py` does
not know them → brand card fallback, as designed); my.html pin-a-tag; tag words
in the search *thesaurus* (those files are the search-core session's — tags
ride in `k` instead and are found); `data/curated/tags_curated.json` (the
door exists, documented in README and the layer; nothing in it yet — 9
วัดนามมงคล from WO-16 is the first candidate).

**Scratch-built, not committed, not deployed.** The standing walk is resting
(`cache/walk-rest`, another session's, until 21:43) and ships the next quiet
round. Note for whoever builds next: `build.py` currently imports
`elephant_layer` (WO-19) whose file was not on disk during this build; the
scratch run stubbed it in-process to reach the tags hook.

---

## WO-16 — Open lists from data.go.th · BUILT 2026-08-20

Design note: `notes/aggregators-and-tags-proposal-2026-08-19.md` §3/§5.
Nan's go: "go on WO-16 open lists" (2026-08-20) — the confirmation the
fetches needed. 18 datasets harvested by **`importers/harvest_datagoth.py`**
(snapshot-first into `cache/datagoth/`, 3 s pauses, **UA without the word
"bot"** — the gdcatalog WAF's word list, measured 2026-08-19; CR files are
cp874; XLSX read with a stdlib zip+XML parser) → `data/curated/datagoth.json`.
Folded by **`importers/import_opendata.py`** (wired into import_all), proven
deterministic AND idempotent-after-landing by running it against a canonical
that already contained its own output — the import_weedth trap, tested this
time. Catalogue: **16,272 → 18,666 records**.

**The big one — the temple register fold (+2,009).** The ONAB register
already on disk from WO-1 (wat-registry/registry.db) holds 1,486 CM + 1,092
CR registered temples; the shelf held 596 records, 346 matched. The unmatched
register rows are now records: **CM wat 307 → 1,468, CR 289 → 1,137**, each
with รหัสวัด, rank, nikaya, founding year (→ the ancientness sort), wisung,
ตำบล/อำเภอ, postcode, credited to ONAB per record. Matching kept WO-1's
discipline (thairom.matchkey; a row any unstamped held record might be went
to review, 252 lines, never to a coin flip). Pins from our own ground:
~1,050 postcode/tambon-amphoe centroids with stated uncertainty, ~911
needs-pin. **CORRECTION to the note:** the provincial CSV's "4,462 temples"
is the same ~1,487 temples stacked three years deep (1,489 unique — measured)
— the register and the province agree; the CSV is the cross-check.

**The rest:**
- **CR sights +238** — the eco list (38, **with phone numbers**: สิงห์ปาร์ค
  053 160 636 …), religious/arts (127, dedup'd against the temple fold
  in-run), community-tourism villages (119). Cross-source dedup: ดอยแม่สลอง
  appears on two lists and lands once.
- **CM police +40, all 40 with a phone** (essentials/gov, `facilityType:
  police`); **LPG shops +28** (`attrs.fuel: [lpg]` → the LPG tag carries
  them); **ธงฟ้า +34** CR budget restaurants (`attrs.thongfah` = grade; the
  operator's PERSONAL name deliberately not taken); **SAT camps +17** (CM 4,
  CR 13 — the CR muay thai shelf held ONE record; `satStandard` carries the
  star level; the source's District/SubDistrict columns are swapped and its
  ภาค 5 rows carry no address at all, both measured).
- **Thai SELECT → honours.json**: 5 confident exact-name matches as food
  marks (award `thai-select`, edition 2563, source URL per entry — the
  honours rule), 17 names as unverified leads; `FOOD_AWARD` gained
  ไทยซีเล็กต์ 🍚. Tags added: `thai-select` (food-award rule), `thongfah` 🚩,
  `sat-camp` 🥊 — all derived, zero new mechanism.
- **7 yardsticks on /stats.html** ("ที่ทางการนับ กับที่มดแดงถือ") — official
  counts beside what we hold, each linking its dataset: hotels certified CM
  1,670 (2567) · stays CM 1,011 (2568) · tour operators CM 1,128 (2567 —
  the note's 872 was the 2565 figure) · CR clinics 887 (2568, was 547/2563)
  · OTOP outlets 2,670 · **retail-pharmacy licences CM 702 / CR 230** vs the
  catalogue's ~202/~20 — the FDA registry names ~3× the pharmacies we hold
  (`cache/fda_pharmacy_compare.txt`; folding the licence register is a
  possible next order, NOT part of this one).
- **`data/bus_routes.json` (674 routes)** — the provincial register (641) +
  27 numbered category-1/4 + city routes; no timetables exist in the source
  and none were invented. Copied into docs/data/, named in llms.txt, waiting
  for WO-13's board.
- **The pin hunt grew honest folds** — pins_layer now groups by
  province+shelf (`<details>`, small errands first) because the fold took it
  ~265 → ~1,500 rows, most of them register temples.

**Review for a human:** `cache/opendata_review.txt` (320 lines) — the
252 temple rows a held record might already be, and every non-temple fold
beside its similar-named neighbours; settle with eyes and merges.json.

**Not done, deliberately:** no enrichment of held records' contact fields
from any list (decision 4 in the note is still Nan's); no fold of the FDA
pharmacy names; ONAB CR temples ARE folded though the order named CM's rows
— same register, same code path, and a CR temple is not less real for the
note having counted CM's CSV; flagged here rather than assumed silently.

---

## WO-13 — รถ-เดินทาง: the transport layer · BUILT 2026-08-20

Note: `notes/transport-proposal-2026-08-19.md`. Nan's go 2026-08-20 ("2 go").
Zero network — every tag this uses was fetched on 2026-07-27 and then thrown
away at import.

**THE FINDING, and it was a branch not a crawl.** `import_overpass.classify()`
folded `amenity=bus_station`, `railway=station|halt` and
`public_transport=station` into ONE sub named `station`, and had **no branch at
all for `amenity=taxi`** — so five taxi ranks, one of them with a phone, were
dropped before the canonical file every single run. The Chiang Mai railway
station sat under ช among songthaew stops; the two Doi Suthep "stations" are
the temple funicular's ends and the shelf could not say so; `songthaew` had
been a child of the tree since the tree was written **with no `match` rule at
all**, so it rendered as "the ants haven't collected this yet" while 33 stops
sat in the cache.

**The split.** `train` · `bus` · `songthaew` · `taxi` · `funicular` · `pier`,
each a child of the shelf now. Landed, after the merge deduplicates elements that appear in more than one
cache file: **bus 28 · songthaew 20 · taxi 5 · train 3 · pier 3 · funicular 2** (fuel 435 and rental 40 unchanged). Chiang Rai
has no railway station in the catalogue and the page says exactly that rather
than explaining why. **The songthaew rule reads the NAME on purpose and only
here**: OSM has no tag for a red-truck route, so mappers wrote the destination
into the name ("Songthaew Stop from Chiangmai to Samoeng", "ท่ารถสองแถวกิ่วสไต") —
33 elements in the cache, 20 distinct places once merged
— reading it is the only way that child can ever fill, and the page says the
line is a mapper's note, not a timetable.

**`/transport.html`** — the bus board from `data/bus_routes.json` (WO-16's
register: 4 city routes with vehicle counts, 28 numbered หมวด 1/4 routes, and **28
provincial routes folded back out of 642 register rows** — the register writes
one row per district a route passes through, so เชียงใหม่-ฮอด-ดอยเต่า alone
fills 72 of them; the board prints each route once with the อำเภอ it runs through), then a section per split sub linking its shelf child, then
the **flights board — which existed since 2026-08-02 and was reachable from
nowhere**, now adopted. A porch band on the transport shelf points at it and
🚌 sits in the services bar.

**What it refuses:** no fare, no departure time, no journey length, anywhere.
The register lists routes, not times, and the page says so above the fold
before a reader can be misled — "the people who know that are at the terminal,
linked below."

---

## WO-16b — the pharmacy register, the temple verdicts, enrichment, follow · BUILT 2026-08-20

Nan, 2026-08-20: "1, 2 go. pin in 3. sure use government directories. your
call on follow vs no. Pls check 5." This is 1, 4, 5 and the follow call;
WO-13 above is 2; **WO-17 (Thailand Tourism Directory) is PINNED at her word,
not dropped** — it still needs her API-key registration.

**1 · The FDA pharmacy fold (+907).** The licence register named ~3× the
pharmacies the crawl had found. Retail licences only — `ขายยาแผนปัจจุบัน`, the
ordinary ขย.1; the บรรจุเสร็จ variants are limited licences and the
วัตถุออกฤทธิ์ / ยาเสพติด ones are permissions a pharmacy holds ON TOP of that,
not extra shops — and only where the licence is `คงอยู่`. **CM 202 → 882, CR
20 → 247.** Each record carries the shop's name, the district it is licensed
in, its licence number and the date it issued; dual-shelved essentials+medical
per WO-9. It states **no phone and no hours**, because the register has none.

**5 · The temple review, checked as asked** — `importers/audit_temple_review.py`.
The 252 held-out rows were all one shape: N register temples sharing a name
across DIFFERENT อำเภอ against ONE held record, so at most one per group is a
duplicate and the rest are missing temples. The tool **refutes, never picks**
(WO-1's rule stands): a row is released when the held record's own surveyed pin
is >12 km from every pin we know to stand in that row's district. The threshold
is measured, not chosen — over 2,050 ground pins in 59 districts, the distance
to the nearest same-district pin has p99 = 8.2 km (cm) / 5.9 km (cr), so 12 km
misjudges **0.27% / 0.54%**, printed by `--validate`. **75 rows released and
folded as the separate temples they are; 177 remain for a person** (107 of them
have no surveyed pin to test at all) in `cache/temple_shortlist.txt`, ranked
closest-to-settled first. Verdicts + evidence per code:
`data/curated/temple_verdicts.json`.

**4 · Government-directory enrichment — approved and wired.** `import_opendata.
enrich()` lets an open government list fill **phone / website / hours that a
held record leaves EMPTY**, never over a value already there, matched on exact
normalised name inside one province; an owner's claim still wins because claims
are applied later at build time. Small today (2 Chiang Rai records gained a
phone from the tourism list) and that is fine: **this is the mechanism WO-17
needs the day the TTD key exists**, tested before it is load-bearing.

**Follow vs nofollow — my call, made.** A per-host allowlist in
`build.credit_rel()`: **followed** for the publishers whose data is on the page
— every `.go.th`, OpenStreetMap, Wikidata/Wikipedia/Wikimedia, and weed.th, the
one private directory this site actually took names and addresses from (658
attributed links). **nofollow stays** for everything else: a place's own site, a
social page, the "also catalogued by" courtesy links. The rule behind it is who
we OWE, not who we like — linking to a .go.th register cannot hurt this site
and does help theirs, which was the whole bargain.

**Also:** the similar-name review test now strips trade words before comparing
(`ร้านขายยา`, `เภสัช`, `ฟาร์มาซี`…), because every one of 907 pharmacies matched
a held record literally named ร้านขายยา — the weed.th lesson, hit again:
740 → 353 review lines.

---

## Standing contracts

- **Curated over crawled.** Researched facts go to `data/curated/`, never to
  `data/canonical/*` — the crawl rewrites those wholesale.
- **Provenance travels with the fact.** A dated mark, a source line, an edge
  receipt. A fact that cannot say where it came from does not ship.
- **No invented matches.** Ambiguity goes to a review file. `wat-registry/match.py`
  and `importers/link_wichaa.py` are the house style.
- **Presence is the only claim.** No hours means neutral, not closed. An absent
  dot is silence, not "no". The one absence this site records is a person who
  stood at a door and found no toilet.
- **The ant rank is never weighted** and no advertiser moves it. Star ratings do
  not exist here and are refused on purpose.
- **Temples are never ranked against each other** (`CLAUDE.md:234`). Founding
  year is a fact and a sort; it is not a league table, and the copy must not
  read like one.
- **Accessibility is structural.** Sorts and facets are labelled buttons; drawn
  SVG carries text equivalents; the list under the map stays.
- **One build at a time** (`CLAUDE.md:24`). `ps aux | grep build.py` first.
- **No GitHub** (`CLAUDE.md:304`). Source is served from `/source/`.
- **Publishing is Nan's move**: `python3 publish/deploy.py --yes`, dry-run by
  default, `FLOOR = 20000`.

## WO-22 — เสริมสวย-ตัดผม: the barber correction, the words · ZERO-NETWORK HALF BUILT 2026-08-20

Nan's ask, verbatim: *"Do whatever you can to enrich mot dang for beauty/barbers.
particularly interested in afro textured hair, americana/british style barber shops
with hipsters, hair extensions, braids, updos, digital perms, high tech hair studios,
and people who make house calls."* Full note: `notes/beauty-proposal-2026-08-20.md`.

**Two shelves were lying, and the lie was readable in Thai the whole time.**

The barber shelf held **six** shops in a city with **sixty-two**. OpenStreetMap
sets `hairdresser=barber` on 6 of the 371 hairdresser/beauty points, so 6 is what
the classifier filed; fifty-three more shops put BARBER on their own shopfront —
สุเทพบาร์เบอร์, Sweeney Todds, Backstreet, Cutlers, เมืองใหม่บาร์เบอร์, Rebel House,
ปุ๊ บาร์เบอร์ — and sat on ร้านทำผม, indistinguishable from a blow-dry counter.

The salon shelf held **none of sixty-two**, and was on `KNOWN_EMPTY` with the
reason *"no OSM signal separates a salon from a hairdresser"*. True about the tags,
false about the shops: **เสริมสวย is THE Thai word for a women's salon** and it was
in sixty-two names. **Before a shelf is declared unfillable, read the names — in
the language the shop wrote them.** That line is now in `tests/test_facets.py`
where the wrong reason used to be.

**The four zeros are the other half of the finding, and they are honest.** Across
all 18,686 records in both provinces, **not one shopfront says perm, updo, afro,
textured or house call**. There is no name rule waiting to be written. Those axes
are answered by the shop stating it, an owner ticking their own facets, or a person
at the door — and by nothing else. `audit_beauty.py` prints all four counts every
run so the hole cannot quietly disappear (same discipline as GEAR in
`audit_muaythai.py`).

**The เปีย guard.** เปีย alone is a braid, and a bare rule files fifteen places as
braiding salons: บ้านเปียง / ยางเปียง / เปียงหลวง are village names, so it catches five
health stations, four temples, three schools and a bakery. Only ถักเปีย is ever a
rule. Strays print every run — same shape as the หมวย/มวย guard.

Built, all zero-network: `audit_beauty.py` (8 reports + `--emit`) · 126 shelf
corrections into `shelves.json`, each sourced `osm name: <the shop's own sign>` ·
`beauty/extensions` child · the 30-facet `beauty` set covering every one of the
eight axes · `male`/`female`/`unisex` rescued from the import (the ONLY three
things OSM knows about a hair shop, thrown away on every previous run; 26 shops
now state who they cut for; only `yes` counts, because this layer cannot render an
absence) · `data/curated/beauty.json` (register shape, empty and saying so) ·
`beauty_layer.py` → `/beauty.html` · 20 new facet keys in `worker/worker.js`.

**What /beauty.html refuses to do.** It does not sort barbers into the hip ones and
the ordinary ones, the farang ones and the Thai ones. All sixty-two are one
alphabetical unranked list, exactly like the elephant camps. Nan's
"americana/british with hipsters" is real and findable, and the honest way to serve
it is the shop's own name plus the facets it states — `razorshave`, `fade`, `beard`,
`priceboard` — never a vibe verdict attached to somebody's livelihood. And it does
not guess at textured hair: a wrong yes sends somebody with tightly coiled hair to
a chair where nobody has handled it before, which is worse than an honest silence.

**The words are the deliverable the crawl could never supply.** Five of the eight
axes are served today, with no network at all, by a person who can say ดัดดิจิตอล
(dàt dì-jì-tôn), ถักเปียแถว (thàk pia thɛ̌ɛo), เกล้าผม (glâo phǒm, เกล้า = to bind up
on the head), ต่อผม (tɔ̀ɔ phǒm) and ไปทำถึงที่ (bpai tham thʉ̌ng thîi). Those services
exist all over this city in shops that simply never wrote them down. A haircut you
cannot name is a haircut you do not get.

**Five reader questions** (`data/asked.json` → `/asked/*.html`), because these
are exactly the long-tail queries that reach a directory and exactly the ones it
was answering worst: `afro-textured-hair` (gap) · `braids-extensions` (1 shop, and
says so) · `digital-perm` (gap) · `hair-house-call` (gap) · `barbershop-shave`
(47 CM shops, 10 phoned). The three gaps carry no share card, per the 2026-08-19
decision that a poster reading "nobody does this" is the one card that travels
further than the sentence under it. Each gap page carries the Thai sentence to
ask with and a way to send the answer back, so the question closes by somebody
answering it rather than by us guessing.

**In the agent brief** (`/brief`): a 💈 section stating the number — 0 of 18,686
name a perm, an updo, textured hair or a house call — and asking any model
reading it NOT to name a shop for those services from this data. That is the
whole safety surface of this WO: the failure mode is a confident answer, not a
missing one.

**ALL FOUR DOORS RUN 2026-08-21** — Nan's go: *"go on all four doors."* Full
account in the note's postscript. What they were worth:

- **Door 1, the wide crawl — a closed question, not a yield.** `hairdresser_supply`,
  `wig` and `craft=hairdresser` returned **zero in both provinces**, each asked
  twice. The extension-and-wig supply trade and the stylist working from her own
  front room are not in OpenStreetMap here at all, so extensions and house calls
  cannot be answered by crawling — only by a shop stating it or a person at a
  door. `cosmetics` returned 41 and is filed NOWHERE: it is retail, this shelf is
  called เสริมสวย-ทำผม, half the rows are unnamed, and several are massage venues
  wearing a cosmetics tag that would have arrived as name-duplicates. The finding
  sits in the crawler beside the selectors so nobody re-runs it hoping.
- **Door 2, the site reads — one real row, and a number of mine corrected.**
  `importers/read_beauty_sites.py`, same manners and the same first-hand rule as
  `enrich_sites.py`. That rule cut the queue: **only 8 of the 18 links are the
  shop's own domain**; ten are Facebook/LINE, and a login wall is not a statement
  by a shop. My "18 shops to read" was overstated by more than half — the same
  class of error as the barber shelf. Of the 8: three domains dead, one timeout,
  one robots-refused, **four read**. **New York, New York states six services in
  its own words** (digital perm, Japanese straightening, colour, keratin, hair
  treatment, wedding hair), each stored with the sentence it came from — taking
  **`digiperm` and `updo` from 0 to 1**. Provenance `site` now sits between an OSM
  tag and a person at the door in `FACET_SRC_NOTE`. Fixed in passing:
  `enrich_sites.first_hand()` returned True for a scheme-less URL, so a Facebook
  link passed as a first-hand source — silent, and in the one place this repo is
  least willing to be wrong.
- **Door 3, the survey — the instrument is built; the walk is Nan's.**
  `assets/reader/hair-words.pdf`, two measured A4 sides, published at
  `/reader/hair-words.pdf` and linked from /beauty.html. Front: the chemical
  words nobody can improvise. Back: braids, updos, the coiled-hair question and
  its follow-up, the house-call phrase — and **what the door tells you before you
  ask**: the price board, the digital perm machine visible from the street, the
  photo wall. The other four sheets stay print-only; that is their WO's call.
- **Door 4, TTD — blocked, and always the weakest.** No TTD key on this machine,
  and the aggregators note already settled whose job that is: *"Accounts are yours
  to create, not mine."* The open alternative (MOTS's "รายการสปา" on data.go.th,
  Open Data Common) is real but its dataset id was never recorded and the key's
  base serves portal HTML at the CKAN paths; the unblock is one id, then one line
  in `harvest_datagoth.SOURCES`. Worth saying anyway: TTD spa is **406 listings
  nationally and it is spa, not hair** — it would grow `beauty-spa` and answer
  none of the eight axes.

**What remains, and it is now a short list:** the walk (door 3), Nan's TTD
account (door 4), and the one data-quality receipt below.

**Doors awaiting Nan's numbered go** (note §3): 1. widen the `beauty` Overpass
group — `hairdresser_supply`, `wig`, `cosmetics`, `craft=hairdresser` (the last is
likely zero here; worth one run to close the question) · 2. read the 18 shops that
already carry a website/Facebook/LINE — the first 18 register rows · 3. **the door
survey**, the only door that ever answers textured hair, digital perms and house
calls at scale · 4. TTD spa/beauty, blocked on WO-17's key. Also noted, no go
needed: `Akshaya E Centre` sits on `beauty/hair` with an Indian state government
website — a bad OSM record wanting a `retags.json` receipt.

