# Work orders — the underused-granary build-out (gemba of 2026-08-17)

> New session? **Read CLAUDE.md first** — the rules that bite — then AGENTS.md, then
> BOTS.md for the org chart. This file is the tasking that came out of the 2026-08-17
> gemba walk: what the walk found sitting unused, and the numbered work orders that
> put it to work. The shared task board carries the moving state; each order below
> names its board task.
>
> Everything stays stdlib, local, static, no tracking. Network-heavy fetches are
> manual-trigger and get confirmed with Nan before they run. **Bots build and test;
> Nan publishes.** No work order below ends in a deploy.

## What the gemba found (the punchline numbers)

- `venues[]` in `data/festivals.json` holds 52 bilingual free-text venue strings and
  **no place ids** — the strict matcher lights a festival band on only **13 of
  12,319** place pages (`festivals_layer.py:337,875-903`).
- Place records carry **86 distinct `attrs` keys**; `known_facts()` renders ~20 of
  them (`build.py:5728`) and search matches **3 index fields** (`build.py:2397-2455`).
- Every place map computes up to 9 neighbours and draws them as **text labels, not
  links** (`build.py:4903-4918`). ~110k internal edges, sitting unrendered.
- The sibling registry `~/Developer/claude code projects/wat-registry/registry.db`
  holds **43,858 temples** — sect, rank, **founded_be/founded_ce**, wisung, full
  tambon/amphoe hierarchy, and often phone — against our 596 `wat` records, unjoined.
  Wats are our **0%-contactable** category (stats page); the registry can fix that
  without one network request.
- Mean ant rank **1.68 / 9**; `enrich_sites.py` has processed **269 of 998**
  website-bearing places.
- `data/wichaa_links.json` already matches **523 temples** to wichaa.net pages.
- Sorts and facets have **no URL state** — nothing faceted is linkable or crawlable.

Sequence: **WO-1 → WO-2 → WO-6 are the first wave** (pure local joins, no network,
biggest visible change per hour). WO-4/WO-5 second. WO-3/WO-7 third.

---

## WO-1 — Join the wat registry (ancientness arrives)

**Why.** 596 wat records with no founding era, no sect, no rank, no contact — while
a government register with all of it sits one directory over. This one join gives
place-page enrichment, the ancientness sort (WO-5), and wat phone numbers at once.

**Read first.** `wat-registry/build.py` (schema), `wat-registry/thairom.py` (the
reusable Thai-name normaliser), `wat-registry/match.py` (match discipline: exact →
fuzzy → **review list, never a guess**), `importers/import_all.py:37-60`,
`CLAUDE.md:50,292` (curated outranks crawls; researched facts go in
`data/curated/`, never canonical).

**Steps.**
1. New gatherer `importers/import_wat_registry.py`. Open
   `wat-registry/registry.db` read-only. Candidate set: `temples` rows where
   `changwat_th` ∈ {เชียงใหม่, เชียงราย} (~2,000 rows, not 43,858).
2. Match our 596 `cat:wat` places on normalised Thai name (`thairom`-style key)
   **and** geography: amphoe when we can derive it (postcode → amphoe, or street/
   tambon attrs), else province + no same-name collision. Two temples, one name,
   one amphoe → **review file**, not a coin flip. Print the review list the way
   `link_wichaa.py` prints `too_close_to_call`.
3. Write matches to `data/curated/wat_registry.json` keyed by place id:
   `{code, name_th, sect, rank, founded_be, founded_ce, wisung, wisung_date,
   tambon_th, amphoe_th, phone, website, source: "ONAB register BE 2567 (Open
   Government Data of Thailand)", matched_how}`.
4. `import_all.py`: merge into `attrs` (`watCode`, `sect` — curated wins over the
   OSM `sect` already on 588 records —, `foundedBE`, `foundedCE`, `watRank`,
   `wisungDate`, `tambon`, `amphoe`) and into top-level `phone`/`website` **only
   where empty** (curated fills, never overwrites a field-confirmed value).
5. `known_facts()` (`build.py:5728`): render founded (`ก่อตั้ง พ.ศ. …` · `Founded
   … CE`), sect, rank, wisung date, and รหัสวัด with the ONAB provenance line, in
   the same dated-mark style the royal-grade panel uses.

**Writes.** `data/curated/wat_registry.json` · review file `cache/wat_registry_review.txt`.

**Acceptance.** ≥500/596 matched with zero guessed matches; wat detail pages show
the founded line; wat contactable % moves off 0 on `/stats.html`; `python3 -m
pytest tests/` green; re-run is idempotent (byte-same curated file).

**Rules that bite.** Never write canonical. The ant rank stays unweighted
(`CLAUDE.md:60`) — registry phone lights the phone ant like any phone. Dated marks:
carry the register's edition year like the royal list does.

---

## WO-2 — Give festivals their places (`venues[].place_id`)

**Why.** The festival↔place graph is 13 edges wide because venues are prose. IDs
turn the matcher from a guess into a lookup: every venue place page gains its
festival band, and every festival page gains real links and a drawn venue map.

**Read first.** `data/festivals.json` (`venues[]` shape), `festivals_layer.py:337`
(`venue_places()`), `:535` (`build_festival_page()`), `:875-903` (band injection),
`build.py:6440` (`event_map_svg()` — the drawing you will reuse), `tests/test_festivals.py`.

**Steps.**
1. One-off resolver `importers/resolve_festival_venues.py`: run each of the 52
   `venues[].th/en` strings through the existing strict matcher **plus** an alias
   pass over `data/curated/venue_aliases.json`. Output three buckets:
   `matched` (write `place_id`), `ambiguous`, `no_candidate` — the last two into a
   review file for Nan/field walk, never guessed.
2. Edit `data/festivals.json`: add `place_id` to matched venues. Free-text stays —
   it is the display name and the fallback.
3. `venue_places()`: prefer `place_id` lookup; fall back to the matcher for
   id-less venues so nothing regresses.
4. Festival pages: venue list entries with an id become links to the place page,
   and festivals with ≥1 located venue get an `event_map_svg()` venue map.
5. Place pages: the festival band now lights up on every matched venue.
6. While in the file: `confidence: needs-verification` festivals (9) keep their
   dashed-wheel mark — ids do not upgrade confidence.

**Writes.** `data/festivals.json` (additive field) · review file · layer edits.

**Acceptance.** Festival bands on ≥40 place pages (`grep -rl festhere docs/*/p | wc -l`);
every festival page with a located venue shows the map; zero dead venue links;
`tests/test_festivals.py` green.

---

## WO-3 — Surface what we already carry, then finish the enrichment walk

**Why.** 86 attrs keys, ~20 rendered. Descriptions exist on 236+102 records and
never print. Blurbs exist on 23 of 12,319. The site's own first-hand enricher has
729 website-bearing places still unread.

**Read first.** `build.py:5728` (`known_facts()`), `enrich_sites.py` (etiquette
header: robots.txt, 1s pause, one page per place, NOT_FIRST_HAND blocklist),
`CLAUDE.md:292`.

**Steps.**
1. `known_facts()` additions, each with its provenance style: `cuisine` (linked to
   a search for that cuisine), `brand`/`operator`, `diet`, `wheelchair`, `email`
   (mailto), `altNames`/`namesOther` ("also answers to …" — they are already
   search aliases, `build.py:9816`).
2. Blurb fallback: where `blurb_th/blurb_en` are empty but `attrs.description` /
   `descriptionTh` exist, render them as the blurb with a "จาก OpenStreetMap ·
   from OpenStreetMap" provenance tail.
3. **[network — confirm with Nan before running]** New gatherer
   `importers/enrich_wikipedia.py` for the ~350 places carrying `attrs.wikidata`,
   `attrs.brandWikipedia`, or `attrs.heritage`: fetch the Wikipedia TH+EN lead
   extract (REST summary endpoint, 1 rps, cached in `cache/wikipedia/`), write to
   `data/curated/enrich.json` as blurbs with `source` + article revision date.
   CC BY-SA: credit line and link render with the blurb, same pattern as photo
   credits. Wats and sights first — they are the pages readers cite.
4. **[network — confirm with Nan before running]** `enrich_sites.py` batches of
   100 (`--limit 100`) until the 998 are done; fold into `morning_walk.sh` only
   after three clean manual runs.

**Writes.** `build.py` render additions · `data/curated/enrich.json` growth ·
`cache/wikipedia/`.

**Acceptance.** Blurb coverage 23 → 250+; cuisine/brand/diet rows visible on pages
that carry them; every borrowed sentence carries its credit; ant-rank mean moves
and `/stats.html` shows it.

---

## WO-4 — Search that forgives (index, thesaurus, empty state)

**Why.** "kow soi" returns silence. The index matches name/alias only, ships as
one 2.79 MB file, and knows nothing of categories, streets, or cuisine that the
data already holds.

**Read first.** `build.py:2397-2455` (the matcher — shipped as `docs/md.js`),
`:9801,9816-9834` (index build), `:10315-10317` (index write), `tests/test_search.py`
and `CLAUDE.md:286-291` (**touch the block, run the test**), and — for the
pattern — `manuscript-wiki/wiki.py:2251-2276` (wichaa's `_thesaurus`/`_expand_token`,
the same trick this order ports over).

**Steps.**
1. **Index fields.** Add to each entry: `su` (sub labels TH+EN), `cu` (cuisine),
   `br` (brand), `st` (street name). Fold category/sub display names into the
   haystack so ร้านกาแฟ / "cafe" / "coffee" match the shelf, not just names.
2. **Split by province.** `index-cm.json` + `index-cr.json`; load the reader's
   province first (their toggle already exists), fetch the other only when
   needed. Satellite-connection rule: smaller first paint, same coverage.
3. **Thesaurus.** New `data/search_thesaurus.json`: groups of equivalents crossing
   script and transliteration drift — khao/kow/kao/ข้าว, soi/soy/ซอย,
   wat/วัด/temple, massage/นวด, kafe/cafe/coffee/กาแฟ, chedi/เจดีย์/stupa … ~100
   groups seeded from `altNames`, cuisine values, and category labels. Expand
   query terms before matching, exactly as wichaa does on both its search paths.
4. **Results with handles.** Group results under category headers with counts
   (tap a header = filter chip); each row shows category · street · ant chips.
   `c[]` already ships in the index unused — use it.
5. **The empty state is a door, never a wall.** No hits → show near-misses (the
   Levenshtein pass already computes them), the top category doors, and the
   "ถามมด · Ask the ants" door. Announce loosened modes bilingually as the
   matcher already does (`build.py:2449`).
6. **URL state.** `?q=`, chip filters, and sort choice live in the querystring on
   search **and** listing pages — every view linkable, shareable, crawlable.
7. Update `tests/test_search.py` fixtures: "kow soi", "coffe", "วดเจดีย" (typo)
   must all land; keep the 200-cap and announced-loosening behaviour.

**Writes.** `build.py` index+matcher block · `data/search_thesaurus.json` · test
fixtures.

**Acceptance.** The three probe queries return; province split halves the first
fetch; node `tests/test_search.py` green; a pasted search URL reproduces the view.

---

## WO-5 — New sorts: by neighbourhood, by ancientness, by open-now

**Why.** Category is one spine. The street graph (942 streets, 4,112 placed
records), the registry founding years (WO-1), and the open-lamps schedules are
three more, already on disk.

**Read first.** `build.py:5253` (`toolbar()`), `:2718-2792` (sort JS),
`:5204` (`entry_li()` — where `data-*` attributes are minted), `data/streets.json`,
`data/open_lamps.json`, `CLAUDE.md:107` (toilets sort by distance only —
confidence in chips, never the sort).

**Steps.**
1. **`sort-age`** — conditional button (the `sort-royal` pattern) on shelves where
   ≥3 entries carry `data-founded` (from WO-1). Label: `เก่าแก่ · Ancient first`.
   Oldest at top; undated entries keep their alphabetical place below, never
   pretending a date.
2. **`group-area`** — a toggle on category listings: `เรียงตามย่าน · By
   neighbourhood`. Regroup the `ul.dir` under street/tambon headers using each
   entry's `data-street` (from `streets.json` edges; tambon from WO-1/postcode
   as fallback). Headers link to the soi pages.
3. **`chip-open`** — an "เปิดอยู่ · open now" facet chip on food/essentials
   shelves, computed client-side from a `data-lamp` minute-of-week attribute
   baked from `open_lamps.json`. Absence of hours = neutral, never dark-as-closed
   (the BOTS.md enricher contract).
4. All three states join the WO-4 URL state.

**Writes.** `build.py` toolbar/entry/JS blocks.

**Acceptance.** Wat shelf sorts by founding year; food shelf regroups by soi with
linked headers; open-now chip counts match `open-now.html` for the same minute;
sorts/chips survive a link round-trip.

---

## WO-6 — The Mot Dang graph (stretchy, elastic, receipts on every edge)

**Why.** wichaa already runs a corpus-scale graph with a provenance vocabulary and
per-edge receipts (`manuscript-wiki/cartography.py`, 23,604 nodes / 126,852
edges). Mot Dang has the edges *in the data* — on_street 4,112, near ~110k,
festival 52 (after WO-2), wichaa 523, cuisine 2,122, brand 1,221 — and renders
almost none of them. Port the pattern, not a framework: stdlib, deterministic,
static JSONL.

**Read first.** `manuscript-wiki/cartography.py:24-35` (the provenance vocabulary:
`authored / adjudicated / computed / derived` — and the rule that `w` is a real
count or metres, `ev` a human-readable receipt, **nothing from a model's priors**),
`build.py:4870-4918` (`place_map()` neighbours), `data/wichaa_links.json`,
BOTS.md Tier-3 (two-line-hook discipline).

**Steps.**
1. New layer `graph_layer.py`, hooked from `build()` like `festivals_layer`
   (~2 lines). Nodes: place (12,319), street (942), category (23), sub (66),
   festival (33), cuisine (top values ≥5 places), brand (≥3 branches), tambon.
   Edges with receipts:
   - `on_street` — from `streets.json` (`via:stated` vs `via:nearest` in `ev`)
   - `near` — the place-map neighbour computation, reused (metres in `w`)
   - `in_category` / `sub_of` — canonical fields
   - `hosts_festival` — WO-2 ids (`ev`: the festival window)
   - `serves_cuisine`, `branch_of` — attrs
   - `same_wat_as_wichaa` — the 523 matched pairs (`ev`: "same Thai name, ≤400 m")
2. Emit `docs/api/graph/{nodes.jsonl,edges.jsonl,summary.json}` + `graph.jsonld`
   (schema.org `Place`/`Event` typing). Deterministic ordering (sorted ids, no
   timestamps) so rebuilds are byte-identical — the wichaa discipline.
3. **Neighbour labels become links.** `build.py:4903-4918`: wrap the drawn label
   in `<a href>` to the neighbour's page. One small change, ~110k new edges a
   reader can walk. Keep the collision/omission logic untouched.
4. **Threads band on place pages** (the elastic part): after "More like this",
   render up to 5 typed lateral links *with their receipts*: "อยู่ถนนเดียวกันอีก
   23 ร้าน · 23 more on this road" → soi page; "312 m apart" → neighbour;
   "สาขาเดียวกัน 12 แห่ง · same brand, 12 branches" → search chip; "งานประจำปี
   อินทขีล · hosts Inthakhin" → festival page; "หน้าวัดในคลัง wichaa · this wat
   in the wichaa archive" → wichaa.net. Structural shelf edges (in_category)
   stay out of threads — the breadcrumb already carries them (wichaa's rule).
5. Advertise the graph on `/source.html` and in `llms.txt` — CC BY like the rest.

**Writes.** `graph_layer.py` · 2-line hook · neighbour-link change · threads band.

**Acceptance.** ≥120k edges; every edge carries `prov`+`w`+`ev`; neighbour dots
clickable on all 12,309 place maps; threads render only where edges exist (no
empty band); two consecutive builds byte-identical; publish gate green.

---

## WO-7 — Maps that show the shelf, not just the pin

**Why.** 12,771 pages carry a map but every one is a single-place locator. The
category GeoJSON is already written (44 files) and drawn nowhere; festival venues
(WO-2) have coordinates and no map; soi maps don't say where the street continues.

**Read first.** `map_shell.py` (the only module that may construct a browser map —
`CLAUDE.md:51-56`), `build.py:4688` (`place_map()`), `:8606` (`street_map_svg()`),
`:9485` (`merit_map_svg()` — a multi-pin drawn map to copy), `data/basemap_style.json`.

**Steps.**
1. **Category maps.** `shelf_map()` in `build.py`: a drawn-SVG dot map per
   category index (dots from the category GeoJSON, labels for the ant-rank top
   10, the merit-map treatment), mounted through `map_shell` so tiles land
   underneath. Both provinces, 46 pages.
2. **Festival venue maps** — delivered in WO-2 via `event_map_svg()`; check the
   drawn-first/print/no-script states here as part of map QA.
3. **Soi continuations.** Under each street map, render `crosses` / `parent` /
   `aliases` from `streets.json` as links: "ตัดกับ · crosses …", "ต่อเป็น ·
   continues as …". The street graph becomes walkable page-to-page.
4. **Filter follows map.** On category pages, the WO-5 chips/sorts re-style the
   SVG dots (dim non-matching) — the drawn layer and the list stay one view.
5. No new fetch surfaces: same basemap, same glyphs, `url:""` degrade state still
   works (`map_shell.py:79`).

**Writes.** `shelf_map()` + mounts · soi continuation block · dot-filter JS.

**Acceptance.** 46 category maps render dots + top-10 labels with tiles under;
scripting-off still shows the drawn dots; soi pages link their crossings; filter
chips visibly dim dots; `tests/test_ground.py` and alt-text tests green.

---

## Standing contracts for every order above

- **Curated over crawled, always** (`CLAUDE.md:50`). Researched facts →
  `data/curated/enrich.json` or a new curated file — never `data/canonical/*`.
- **Provenance travels with the fact** — a dated mark, a source line, an edge
  receipt. If a bot cannot say where a fact came from, the fact does not ship.
- **No invented matches.** Ambiguity goes in a review file. `match.py` and
  `link_wichaa.py` are the house style.
- **Bilingual or it doesn't ship** — every reader-facing string TH · EN, auspicious
  register, no ominous framing.
- **Accessibility is structural**: sorts/facets are buttons with text labels;
  drawn SVG carries text equivalents; `tests/test_alt_text.py` stays green.
- **The ant rank is never weighted** (`CLAUDE.md:60`); stars do not exist.
- **One build at a time** (`CLAUDE.md:24`); publish is Nan's move
  (`publish/deploy.py` dry-run default, FLOOR 20000).
- **No GitHub links anywhere** (`CLAUDE.md:304`); source points at `/source/`.
