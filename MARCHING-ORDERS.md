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
| WO-2 | Festival venues get place ids | next |
| WO-6 | The Mot Dang graph + neighbour links + threads | next |
| WO-4 | Search that forgives | after WO-1 |
| WO-5 | Sorts: neighbourhood, ancientness, open-now | after WO-1 |
| WO-3 | **The detail page — everything we carry and never show** | standing |
| WO-7 | **The maps — the shelf, the year, the way onward** | standing |

WO-3 and WO-7 are marked standing rather than sequenced because they are the
two the reader actually meets. Nothing else on this list is worth shipping if
the place page and the map stay as thin as the walk found them.

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

**Acceptance.** Blurb coverage 23 → 250+ without step 4; cuisine, brand, diet
and alt-names rows visible wherever the data exists; every borrowed sentence
carries its credit; `place_json()` publishes each new field; mean ant rank and
`/stats.html` both move.

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

**Acceptance.** Neighbour dots clickable on all 12,309 place maps; 46 category
maps render dots with top-ten labels and tiles beneath; scripting off still
shows the drawn dots and the list; soi pages link their crossings; filter chips
visibly dim dots; `tests/test_ground.py`, `test_moat_geometry.py` and
`test_alt_text.py` green; no new fetch surface beyond the existing basemap.

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

**Acceptance.** Festival bands on ≥40 place pages
(`grep -rl festhere docs/*/p | wc -l`); every festival with a located venue
shows a map; zero dead venue links; `tests/test_festivals.py` green.

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

**Acceptance.** ≥120k edges, every one with `prov` + `w` + `ev`; threads render
only where edges exist, never as an empty band; two consecutive builds
byte-identical; graph advertised on `/source.html` and in `llms.txt` under CC BY.

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

**Acceptance.** "kow soi", "coffe" and "วดเจดีย" all land; first fetch roughly
halves; `tests/test_search.py` green with those three as fixtures; a pasted URL
reproduces the view.

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

**Acceptance.** Wat shelves sort by founding year; food shelves regroup by soi
with linked headers; the open-now chip agrees with `/open-now.html` for the same
minute; every state survives a link round-trip.

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
