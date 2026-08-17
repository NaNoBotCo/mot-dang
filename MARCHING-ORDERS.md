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
> ship. **Bots build and test; Nan publishes.** No order below ends in a deploy.
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
