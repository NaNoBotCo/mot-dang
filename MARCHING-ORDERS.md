# มดแดง — marching orders

> Standing tasking for motdang.net, from the gemba walk of 2026-08-17.
> **Read `CLAUDE.md` first** (the rules that bite), then `AGENTS.md` (why the
> site is shaped this way), then `BOTS.md` (the org chart). This file says what
> to build next and how you will know it worked. The shared task board carries
> the moving state; this is the standing structure.
>
> House discipline: stdlib Python, local, static. Curated outranks crawled. Provenance travels with every fact. Ambiguity goes
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
| WO-65 | The second axis — `kind`, kind-aware ants, and the second gate | **BUILT** 2026-09-06 — the counter rule retired: `kinds.json` + `kind_layer.py`, 10 kinds over 24,059 records (16 unplaced); the nine ants re-cut to 5 universal + 4 the kind's own (commerce byte-identical); `place_has_substance()` now asks what a record's OWN KIND owes — indexable 13,630 → 14,286, held-out-of-index 1,708 → 677; `tests/test_kinds.py`. Nan's decisions J/K/L/M still open. |
| WO-66 | THE EDGE — bus shelters, tree shrines, named sois, wells (decision J) | **BUILT** 2026-09-06 — two kinds added (`sacred` 40 records, hand-checked; `way`), `edge_layer.py` PROJECTS 1,077 named ways (432 sois) out of data/streets.json where they had been fully modelled and never admitted as records; the vernacular for all four classes (49 terms, Thai + reading + gloss) written into kinds.json and gated; compiler learned `cat_not`. Shelters, shrines and wells need one OSM pull each — network, so Nan's trigger. |
| WO-67 | ที่จอดรถ — the elephants he got when he asked for parking (Michael's report) | **BUILT** 2026-09-06 — three faults, three fixes. (1) A mined shelf can no longer open a rich door: the chang teaser's "the gate and the chedis that carry its name" had made `gate` an elephant word, so every gate in this city opened the elephant panel; `search-core/mine.py` now reads an English teaser as a LIST not as prose (17 junk terms dropped, 1 real one lost), and 15 residue words are stopped by name. (2) A failed search no longer wears a door: in partial mode no panel renders, the page's own "nothing matches all of…" comes FIRST, the heading says *partial matches*, and a stuck reader is handed the ants and a crawl request. (3) The catalogue held ZERO parking among 22,351 places — now 1,796 (CM 1,361 / CR 435), and 1,711 of them were unnamed, so they publish under a name derived from their tags plus a bearing (`ที่จอดรถ · ใกล้ประตูท่าแพ 80 ม.`), stamped `derived` so no give-back can ever offer OSM a name we wrote. Plus the fourth fault found on the way: `parse_intent` ate every bare constraint, so `parking`, `wifi`, `open now` and `wheelchair` each returned zero rows — fixed in both halves of searchcore, parity 528/528. `access:parking` now has a column. New `parking` kind (the pin IS the answer). tests/test_search.py grew 13 rich-door cases. |
| WO-68 | ใกล้ = ระยะทาง · near a landmark is a DISTANCE, and the results page slashed back | **BUILT** 2026-09-07 — Nan: "Near a landmark should sort by distance. Also declutter results page. Slash and burn. If it doesn't answer a question, it is invisible." A landmark named in the query is lifted out of it (68 points from the bearings register, published as `search_landmarks.json`), the proximity word with it, and what remains is what the reader wants — then rows sort by metres from the point and each carries its distance. Romanisation drift is a RULE not a list: `th?a\s*ph?ae` matches taphae/thapae/tapae/tha phae, because the aspirate and the space are whoever painted the sign's choice. The landmark's own record is hoisted first (typing "tha phae gate" returned the gate FOURTH). A stated constraint now NARROWS where a mined shelf word only lifts. Declutter: the now·near strip hides on a query, the province chip prints only when results span both, the count/cap duplication is gone, the thesaurus status line is cut, "wrong results?" appears only when the search struggled, and shelf headings step aside under a distance sort. **`tests/test_search_page.py` is new and is the point** — it renders the page under a DOM stub, and it exists because a `const` in the temporal dead zone had taken every search on the site down while test_search.py passed 32/33, the fault being four lines below where that file stops looking. |
| WO-69 | บัตรผลการค้นหา — a result is a PLACE, not a link: chips, a lamp, metres, a map, and finding BY TAG | **BUILT** 2026-09-07 — Michael: "if I see something I like on the list of results, I want map controls of it accessible, links to related (nearby/near time) things, interactivity, and relationships... discovery should EXPLICITLY allow searching/finding by tags... if you need to explain something using words, you're fucking up." The index carries the relations at last (`t` tags · `tt` trade tags · `st` street · `ar` district · `hk` opening schedule, every one an int into the new `docs/data/search_tables.json`; the unread `h` string came off, net +200 KB). Search takes `tag= sub= cat= st= ar= near=`, with no words at all if you like; a tag typed in the box or written `#vegan` is lifted out of the query into a filter, and the constraints searchcore already lifted (vegan, wifi, wheelchair, delivery, open late) narrow instead of printing "this page cannot filter on it yet". A row is now a card: up to three chips that are each a filter, the metres when a point is known, an open-now lamp (absent when nobody recorded hours — never "closed"), a 📍, and a body that opens IN PLACE with a mini map, the three nearest other places, same-kind-nearby, what is on here, and add-to-plan. A results map, lazy-loaded so no search pays a megabyte for it, with near-me through the one MDLOC door. Fourteen instructional sentences deleted and replaced by chips. `tests/test_index_weight.py` NEW; test_search + test_search_page extended. Note: go/card. |
| WO-70 | คำที่หายากคือคำถาม — the rare word IS the question | **BUILT** 2026-09-07 — Michael's "best place to buy a Martin guitar" put Guitar House ~230th: `buy` matched 261 rows, `martin` 4, `guitar` 4, and nothing in the score knew the difference. When no row matches every word the partial pile is ranked by Σ log(N/df) over the words each row actually matched. Guitar House, Intune and Cin Guitars are now the top three; "cheap tok sen massage old city" answers with tok sen shops. Rows that matched everything are untouched, and every existing case still passes. In build.py's caller only — searchcore.js is not touched. |
| WO-71 | ทิศทาง + สามทางให้เดินต่อ — orientation on every listing, and the three ways to wander | **BUILT** 2026-09-07 — WO-64's hook is APPLIED at last (Nan 9/6: "all listing pages to have landmarks and orientations... orientation in comparison to other objects is this site's actual secret sauce"): 93% of sampled place pages carry a ทิศทาง row, /landmarks.html and data/landmarks.json exist, and an approximate pin says so instead of quoting metres. Under the map, Nan's §6: the five nearest places we hold, same-kind-nearby (ALL of them, nearest first, via `?sub=…&near=…`), and 🎲. The Map row opens OUR city map first — no place page had ever linked to it. "More like this" is retired: it was a fourth way to wander, ranked by record completeness rather than by where anything is. Five sentences cut from the shared template. `tests/test_page_weight.py` check 2 now grades repeated prose (21), all prose (37) and total (159) separately, because the single 140-word cap was counting per-place FACTS as boilerplate. |
| WO-72 | คำอ่าน — the romaniser's three faults, measured over all 15,947 Thai names | **BUILT** 2026-09-07 — `tests/test_translit.py` was RED on both floors this morning without the romaniser having changed (the pair set is drawn live and new records arrived whose English name is a different name). Under it: run-on compounds 5,678 → 1,044 (ประตูท่าแพ was "Pratuthaphae"), stranded tails 18 → 0 (บุ่น was "Bu Na"), English leaking mid-name 117 → 0 (วัดถ้ำพระ was "Wat Cave Phra"). The segmenter is now dynamic-programming, the objective ported from thapsap so both projects cut Thai the same way. Floors 42.8% → 46.9% exact, 68.1% → 70.4% close, both green. 72.8% of readings changed. |
| WO-73 | พิกัด — the gazetteer stops being confidently wrong | **BUILT** 2026-09-07 — its docstring claimed 80% calibration; measured, 63%. The worst five results of every run were one failure: ถนนโชตนา in อ.ฝาง matched to the Chiang Mai stub of a road that runs 128 km north, declared ±280 m. Three witnesses added: the อำเภอ the address names (43 centres were in admin_areas.json since August, read by nothing) refuses a road, tambon or postcode that falls outside it; a street nobody corroborates answers at ±3,000 m and so is never published; and the sign's spelling is a RULE (the h after t/p/k, the space) plus 25 curated rows in the new `data/curated/street_aliases.json` — the fix named on 9/5 and never built. Calibration 63% → 75%, unplaceable 971 → 189. A dry run offers 194 new pins, NOT written. `tests/test_geocode_local.py` NEW. |
| WO-74 | แตะแล้วตอบ — one card, every map, and it can be explored | **BUILT 2026-09-07, not yet in a build** — Nan: *"if you click a point on a motdang map, it should allow you to explore information about what you clicked."* Measured first: of 25,889 pages carrying a map a tap answered on place pages (five neighbour dots), 95 shelf maps, /map.html (one shelf on by default), /here.html, the results map and /toilets — and answered nothing on 534 soi maps, 9 event maps, the merit round, /doi.html, /plan.html or the homepage. New `tapcard.py` → tap.css/tap.js, offered by page() on the same test that pulls in MapLibre, so every map page — and every map built later — carries it. md.js's MDCARD stays as the fallback and its three call sites now ask for the card by name, so every existing map upgrades without an edit. Her calls, 9/7: a sheet on a phone and a docked panel ≥900px, NEVER a centred modal (nothing trapped, nothing dimmed, 44px targets, rem sizes so it survives 200% text); silence on bare ground and on anything in the tiles we hold no record for; tag chips FILTER the map where it can filter and otherwise open the same filter on the results map; the three nearest MOVE the card in place with a pushState each, so the phone's own Back walks the trail and then closes it. Soi maps get marks (`mdtap_attrs`); the results map now carries tags, street, district and hours to the card. `tests/test_tap.py` NEW — 26 checks under a DOM stub. Still to do: event and merit marks, tag ints on place-map neighbours and on the explore/here layers, and the build itself. |
| WO-76 | บรรทัดที่สอง — a result you can act on without opening it | **BUILT 2026-09-08, not wired and not built** — Michael: *"Records that appear in search/map/discoverability should not require you to click them to see basic information… rank/sort results according to tags and your own matching criteria, without ever leaving the results page… most of the details could fit on a line or 2… you need basic information about links in order to decide whether clicking is worth the extra nav effort."* WO-69's card shipped the relations to the browser and then discarded four of them at render time: **every tag** (capped at one chip, 127 slugs exist), **every trade tag** (never shown), the street AND the district (whichever came first won), and the opening schedule (spent on a lamp; the hours themselves unread). Those four cost nothing — they were already ints on the row. New `rowline_layer.py` → `MDROW`, appended to md.js and its sheet to style.css, so no second request. The line reads what it is · where it is · when it shuts · ☎ the number · its own page, in the order a person scans; past the fifth chip a **+N that folds open IN PLACE**, every chip a filter, so you can narrow by any tag you can see. Two new index fields — `ph` (60,921 rows) and `w` (70,730, facebook.com/ shortened to f/) — **2.82 MB, and the address deliberately left off at 2.05 MB because the street and district chips already say it**. **83% of records will carry a phone or their own page on the row**; a name-and-a-pin record renders NO line rather than an empty bar. refine's sort gains ตรงแท็กมากสุด / most tags matched, which only ever REORDERS. The map card (WO-74) reads the same two attributes and gains the hours in words. `tests/test_rowline.py` NEW — 40 checks under a DOM stub; verified by hand in a browser on real records at 375 px and 200% text. **Not applied**: build.py was hot all morning (a build running since 08:37, build.py edited at 09:13 by another session) — `importers/apply_rowline_hook.py` holds ten anchored idempotent edits and REFUSED once already when trades_layer landed mid-chain, which is what it is for. Note go/rowline-note. |
| WO-77 | ภาษา — the toggle that was applied after the page had already been drawn, and the values that were never in two languages to begin with | **BUILT 2026-09-08, not built into docs/ and not deployed** — Nan and Michael: *"the language toggle on motdang.net fails a lot… there seem to be a bunch of loose terms presented only in one script, which detracts from accessibility and removes opportunity for humans to see patterns/infer meaning."* Note go/language. **TWO DIFFERENT FAULTS.** (1) **The toggle was applied AFTER first paint.** Every page shipped a bare `<body>` and the stored choice was written by md.js — 248 KB, and the LAST tag on the page. A reader who had chosen English got a fully painted bilingual page and then the switch, on every navigation; on 1.5 Mbps that is seconds, and from the outside it is indistinguishable from a toggle that failed. The class moved to `<html>` and is written by a 180-byte inline head script before the first pixel; the stylesheet's 29 `body.lang-*` selectors moved with it, and the served page now carries `lang-both` so a no-script reader gets both languages instead of Thai alone. (2) **408 Thai runs and 966 Latin runs across 59 sampled live pages sat outside any `.th`/`.en` span**, so the toggle could not touch them — and on a place page they were all in one place: **THE LABELS WERE BILINGUAL AND THE VALUES WERE NOT.** `bi("API","API")` also printed "API · API"; fixed inside `bi()`. **THE CENSUS over 88,161 records: 55,472 Thai names with no English, 36,442 addresses with no Latin character in them, 33,369 attribute values printing in Thai alone over 59 fields.** WO-72's romaniser reaches a NAME (189 of 196 in the sample) and reached nothing else. **New `terms.py` + `data/curated/thai_terms.json`, which COMPOSE rather than list** — `registerUses` is 39 values built from a dozen words and `levels` is 35 built from six and a number, so a table of parts covers the fortieth value the register invents and says nothing when it cannot. Coverage of what the pages print: **นิกาย 1,717/1,717 · ประเภทวัด 1,717 · วิสุงคามสีมา 1,717 · ระดับชั้น 1,516 · สังกัดเขตพื้นที่ 1,302 · ประเภทตามใบอนุญาต 243 · ผู้รับใบอนุญาต 196 all at 100%, and 34,257 of 36,442 Thai-only addresses (94%) decomposed into ตำบล/อำเภอ/จังหวัด/ถนน, each labelled by the word the address itself used and each name READ, never translated.** ป.6 is Grade 6 and ม.3 is Grade 9 — the offset is a fixed case in the test, because getting it wrong sends a parent to the wrong school. **THREE REFUSALS:** a **gloss beats a reading** (the first draft printed "ได้รับ · Draiba · granted", where the middle word is neither useful nor correct — a reading is for a NAME, something you say aloud or show a driver); **a half-gloss is refused entirely** (one unknown Thai word takes the whole value down, because "residential unit · ??? · balcony area" reads as though the site understood the row); and **nothing translates a name** — where a head word is a dictionary word and the tail is a name, ลานจอดรถ มหาวิทยาลัยเชียงใหม่, the head is glossed and the name is read. **The admin lexicon went 59 → 403**: `build_trade_lexicon.py` read only the curated file, which holds 43 อำเภอ and 16 ตำบล, so of the 294 ตำบล the catalogue prints on 3,031 records it could read **8%**; it now reads the catalogue's own names too, curated first so an อำเภอ keeps its road-sign spelling. **The 13 source-credit agencies on 4,662 records now carry the English they publish themselves** (ONAB, OBEC, Thai FDA, DGA, the Treasury Department) — the credit is how a reader weighs a row and it was legible to half the readership. Also paired, each on every page: the copy-link button, the sponsor label, the อ่านง่าย button's face (it had a bilingual aria-label and a Thai-only label), the มดแดง map link, the พ.ศ. edition date on 1,371 temples (now with its CE year), the 29 horoscope chips, and the currency names — the last two under **Nan's own P2 rule of 7 September**, so the English half stands down in ไทย+EN and appears only for a reader who chose English. **MEASURED: runs of Thai the toggle cannot hide went 6.9 → 3.3 per place page, and 3.0 of the remainder are the masthead logo and the toggle buttons themselves; bare Thai `<dd>` values went 300 across 200 built pages → 0 across 30 freshly rendered ones.** `tests/test_terms.py` (28 checks incl. the refusals and a corpus floor) and `tests/test_language.py` (pre-paint script, the `<html>` class, every stylesheet rule that hides a language, no bare Thai in a value) both NEW and green; test_translit and test_alt_text re-run green. **NOT BUILT AND NOT DEPLOYED** — a build has held the lock since 08:37 and WO-76 is in the same file today; test_language stays red against the old docs/ until the standing walk rebuilds, which is the gate working. **Held for Nan (note §F1–F5):** the 25 cinema titles on the front page (a film title is a name and wants the distributor's own English, which is an unrun fetch) · the /listings/ pages, which carry their own copy of the toggle from the other repo and still flash · the reading not yet reaching search RESULT rows, shelf pages or the home page's shelf names · two letter-rule holes found in passing (ได้รับ → "Draiba", แก้วนวรัฐ → "Kwaenorat") · `registerUses` glossed and printing nowhere. **F2–F5 EXECUTED the same day** (Nan: *"f1--leave the cinema stuff alone. don't add an additional fix to what already kinda works. Execute F2-F5."*). **F2** — the LISTING SHEET had the identical fault in its own `th.py`: class on `<body>`, written at the foot. Moved to `<html>`, `LANG_PREPAINT` in all three heads, `class="lang-both"` served, seven selectors repointed across th.py/sheet.py; rebuilt, **all 12 of its suites green**. **F3** — two of the three places named turned out to be ALREADY DONE and the note was repeating a 9/6 measurement: shelf pages carry 1,209 readings and a 205-row search carries 199, both from WO-72. What WAS wrong is the same fault one level down — **the result row's name and its reading were both unmarked**, so the name showed in every mode by accident rather than by the `.solo` rule and the READING printed for a reader who had asked for Thai alone. New `mdSolo()`, the client twin of `name_bi()`; `mdBi()` learnt the same identical-pair collapse `bi()` learnt. And `MD_CATWORDS` welds "th · en" into ONE string — right for the search haystack, wrong on a chip — so every result row printed both languages whichever you picked; a 23-entry `MD_CATPAIR` now feeds the three places a shelf word is SHOWN. Front page: the event slides printed the venue as one welded string (now the pair as markup), and **the day of the week and the zodiac year were written as PLAIN TEXT by the live updater**, so moving the date put the Thai back whichever language you had chosen — `bl()`, the pair-writer, was sitting two lines below. **F4** — แก้ว read "Kwae" (ว taken as the second half of a กว cluster instead of the final /o/) and นวรัฐ read "Norat" (the unwritten vowel dropped), so ถ.แก้วนวรัฐ read "Kwaenorat"; ได้รับ read "Draiba" because ดร is a LOANWORD cluster and this is ได้ + รับ. แคว really is Khwae and แก้ว really is Kaeo and nothing in the spelling separates them, so the four went to `rtgs_lexicon.json`; one rule changed — the lead-vowel cluster exception now applies to NATIVE clusters only. **Corpus floor moved: exact 46.9% → 47.6%, close 70.4% → 70.7%**, and เบรก is still Brek. **F5** — `registerUses` printed NOWHERE on 559 records while the assessed value beside it printed all along, so the page said what a square metre is worth and not whether the unit may be lived in; new ตามทะเบียนใช้เป็น · Registered use row, and the gloss stopped repeating the register's own parenthetical restatement. **F1 stands untouched at her instruction.** **STILL NOT BUILT OR DEPLOYED, and the standing walk is RESTING on her 2026-09-05 instruction — this needs her go.** |
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
| WO-21 | วิว-น้ำตก — views & photo spots: the shelf, the measurements, the doors the data is behind | **ZERO-NETWORK HALF BUILT** 2026-08-20 — `notes/views-proposal-2026-08-20.md`; `importers/audit_views.py`; `views_hit()` rides the WO-19 fence and files **18 waterfalls + 2 viewpoints** the attraction dragnet had already caught (แม่สา, บัวตอง, the Inthanon set, ขุนกรณ์, the CR skywalk); `sights` gains a น้ำตก child; JSON-LD `Waterfall`; `direction`/`ele` kept at import and rendered (หันไปทาง · Faces / Elevation); claims census 54 → `cache/views_claims_*.txt`; scratch build 20,371 pages, all gates PASS. **The doors await Nan's numbered go** (note §doors): wide `views` group · Commons uncapped re-run · TTD key · WO-16 lists · DNP fee/hours reads · the `view` tag · her own picks | · **2026-08-21 postscript**: seed list replaced by a full-breadth mine per [[feedback_known_empty_can_be_wrong]] — HIDING 11 sorted spot/container/station + 9 toponym strays guarded (`cache/views_review_*.txt`); the roll now reports **findable** vs **present** after ภูชี้ฟ้า read green while being 2 unpinned register rows on no view shelf; 1 real dupe pair (`views_dupes_cm.txt`); **261 sights records match no child** (cr 234, mostly `dgth`, incl. ภูชี้ฟ้า and the CR clock tower) — the eco register's single type field cannot sort them, nothing auto-shelved; the `view` tag deliberately NOT shipped (tags.json derives nothing from names — needs an attr or Nan's call) · **DOOR 1 WALKED 2026-08-21** (Nan's go): wide `views` group (viewpoint · named waterfalls · named peaks) province-wide both provinces, neither `incomplete` — cm 500 / cr 231 elements. **viewpoint 103→178 · waterfall 18→61 · peak 0→168 (110 with elevations)**; ดอยอินทนนท์ 2,565 m was absent from the directory in every form until today, now schema.org `Mountain`. Rules written only after counting; `waterway=waterfall` sits below `natural=water`. Build 21,688 pp, all gates PASS. **Door 2 correction: harvest_commons' AREA SWEEP DOES NOT EXIST** (docstring describes two passes, `main()` implements one) — by-place pass aimed per the script's own advice rather than 3.1 h of uncapped requests · **DOORS 2+3 WALKED 2026-08-21**: Commons **59→107 photographs, 28 on the view shelves** (Doi Inthanon, Doi Suthep, บัวตอง, วชิรธาร, แม่ยะ, สิริภูมิ, หมอกฟ้า, ม่อนแจ่ม, ออบหลวง), hot-linked with photographer+licence; `enrich_wikipedia` **33 blurbs** over 100 candidates (most peaks have a Wikidata item but no article) — Inthanon/Suthep/Pui/อ่างขาง/ภูชี้ฟ้า/ดอยตุง/นางนอน/ผาตั้ง + the national parks, bilingual, CC BY-SA. **New guard: a LIST is not a description** — สารภี station's Thai sitelink is รายชื่อสถานีรถไฟ สายเหนือ, so its blurb described the whole line; refused in either language, the other still stands. Build 21,701 pp, all gates PASS
| WO-19 | ช้าง — the elephant shelf, the register of what each camp states, the city's elephant names, /chang.html, and the wichaa article | **BUILT** 2026-08-19, crawl folded 2026-08-20 — `notes/elephant-proposal-2026-08-19.md` (+ postscript); 0 camps → 18 curated → **30 on the shelf** after the `elephants` Overpass group (zoo·theme_park·attraction, fenced: 290 non-elephant elements to `cache/elephant_review_*.txt`); 8 merges onto surveyed pins; needs-pin 6→3; Ruammit CR entered; register with `stated`/`unstated`; wichaa `entity_chang` 31 witnesses; CR zoo selector `incomplete`, re-run when Overpass is calmer |
| WO-22 | เสริมสวย-ตัดผม — the barber correction, the words to ask with, and the census of the silence | **ZERO-NETWORK HALF BUILT** 2026-08-20, Nan's ask (afro-textured hair · americana/british barbers · extensions · braids · updos · digital perms · high-tech studios · house calls) — `notes/beauty-proposal-2026-08-20.md`; `importers/audit_beauty.py`; **barber 6 → 62** and **salon 0 → 62** off the shops' own signs (126 shelf corrections); `beauty/extensions` child; the **30-facet `beauty` set** covering all eight axes; `male`/`female`/`unisex` rescued from the import (26 shops now state who they cut for); `beauty_layer.py` → **/beauty.html** — 22 words with RTGS/tone/root, 5 whole sentences, both shelves, and a printed census showing **0 of 18,686** records name a perm, an updo, textured hair or a house call. **All four doors run 2026-08-21** on Nan's go: door 1 wide crawl → **0 supply shops, 0 wigs, 0 home stylists** (a question closed; 41 cosmetics filed nowhere) · door 2 site reads → only **8 of 18** links were first-hand, 3 domains dead, **4 read, 1 states six services** (New York, New York — `digiperm` and `updo` go 0 → 1) · door 3 → the survey instrument is built and published (`/reader/hair-words.pdf`), the walk is Nan's · door 4 → **blocked**, TTD needs an account only Nan can make, and it is spa not hair anyway |
| WO-23 | น้ำพุร้อน — hot springs, the whole north: the shelf CM held zero of, the seventeen-province register, /namphuron.html | **BUILT** 2026-08-20/21, Nan's go ("BIGLY… the whole north is ok") — `notes/hotsprings-proposal-2026-08-20.md`; CM **0 → 16 records** (สันกำแพง w/ its own site's posted prices, โป่งเดือด, เทพพนม, ฝาง, ดอยสะเก็ด, มะลิกา…), CR 3 → 9 (แม่ขะจาน's four faces merged to one, ผาเสริฐ, โป่งพระบาท, ห้วยหมากเลี่ยม); register `data/hotsprings.json` **98 springs / 14 provinces, 63 with measured temperatures** — OSM area-clipped per ISO province (`hotsprings` group WIDE + `harvest_hotsprings.py`), the **DMR inventory read whole** (66 northern rows, temp+pH), DNP park list + MHS's own hot-spring CSV (pins), curated stated-facts w/ fetched sources; `springs_hit()`/`audit_hotsprings.py` one-copy rules (bare โป่ง never matched; village/school/temple/office/campsite/bus-stop fences all witnessed by real catches); generic-key guard after a bare-worded spring folded 60 km wrong; /namphuron.html = drawn no-tile map (54 pins) + stated-register + primer; `sights` น้ำพุร้อน child; thesaurus ring widened; phichit asked short (1 selector, said on the page; `--fetch` when mirrors calm); scratch build 21,402 pp, all gates PASS |
| WO-24 | คำตอบก่อนลิงก์ — search rich doors + the namesake split: a curated card over the rows for topics the site keeps a page for, and ชื่อพ้อง filed behind their own header | **BUILT** 2026-08-20, Nan's ask after typing "elephant" ("pre-stage some rich information… place names with Chang in them are not differentiated… might be systemic") — `notes/search-doors-2026-08-20.md`; `data/curated/search_panels.json` (10 panels: chang · muaythai · cooking · beauty · womens-health · toilets · festivals · flights · massage · wat; build.py refuses a malformed pair); triggers by lifted shelf / term variants / query substring, first to speak wins, panel shelves join the +0.5 lift; on-shelf rows split from namesakes whenever the query names a shelf — systemic, not elephant-special; `tests/test_search.py` REPAIRED (its extraction markers predated search-core and the whole file failed at HEAD) and extended to 26 queries + a door-href walk; searchcore/mined tables untouched, no parity run needed |
| WO-25 | ดูแลต่อเนื่อง — ongoing care: the care register (hospital departments · US-insurance/FMP paperwork · คลินิกพิเศษ), /care.html, the desk sheet | **BUILT — ALL SEVEN DOORS WALKED** 2026-08-21, Nan's own case walked through her own site, then her go ("start with 1 and move down the list") — `notes/ongoing-care-proposal-2026-08-21.md`. **The gemba**: cardiologist/menopause/insurance/FMP/DTV all **0 results**; `clinic → chang` in the mined shelf table sent every clinic query to the ELEPHANT door; corpus held **zero** menopause/hormone/endocrine/internal-med/checkup records and **154 hospitals nearly all contactless** (Rajavej: a name and a pin). **Door 1** `importers/read_care_sites.py` + `data/curated/care_targets.json` — verifies before it believes (a candidate is the hospital's site only if the page carries its own name); 49/77 fetches, **13/20 targets verified** → `data/curated/care.json`: **7 hospitals, 38 stated facts, 11 recorded unread**, every claim with its sentence + url + date. **THE FIND: Rajavej publishes its own TRICARE-and-FMP page** with a named desk, email and extension — and states **คลินิกโรคหัวใจ** (Tue/Sat) and **คลินิกต่อมไร้ท่อ** (Mon eve): the `heart` key in specialty.py had **zero members corpus-wide**. **คลินิกพิเศษ/นอกเวลา** surfaced as a whole tier (CR Prachanukroh SMC 16.00–20.00, Suan Dok's own lines, Chiangmai Hospital's roster). **Door 2 BLOCKED and published**: all three official DTV sources unreadable to a fetch (React shells; MFA path = nav only, "DTV" appears 0×) — **no visa rules recorded**, the attempts printed instead. **Door 3** va.gov FMP read first-hand (page states last-updated 2026-08-06): benefits letter → hand to provider → provider files; Thailand not on the toll-free list. **Door 4** desk contacts recovered incl. Rajavej's; 2 stored "official sites" found wrong. **Door 5** zero-network hygiene: **27 merge pairs + 4 retags** — Bangkok ×2, Fang ×4, Lanna's 3 buildings, Chiang Khong ×3 + 20 district hospitals doubled by OSM/MOPH; the **café filed as a hospital** (its own description: "First aid room"); **3 vets** off the people-medicine shelf. **Door 6 fixed at the root**: `GENERIC_PREMISES` in search-core `mine.py` drops bare premises words mined from English teaser prose (`clinic` came out of "…the elephant clinic…"), 5 wrong turns gone incl. `schools → cooking+learn+school`; **7 ongoing-care groups added to hand.thesaurus.json** — a thesaurus term is never segmented — taking **โรคหัวใจ 641 → 0 rows, อายุรกรรม 2,558 → 0, ใบรับรองแพทย์ 2,076 → 0** with the door answering; parity 528/528 clean. **Door 7** `/reader/care-words.pdf` — the seven desk questions (itemised receipt · เวชระเบียน · after-hours · "have you filed FMP before?"), linked from the page. `care_layer.py` → **/care.html**; `care` search panel; **test_search 26 → 43 green**; publish gate + alt-text PASS |
| WO-27 | อสังหาฯ-ที่พัก — the residential split, the words before the deposit, /realestate.html, and the farang door | **ZERO-NETWORK BUILT** 2026-08-21, Nan's thesis ("the farang SEO crowd… is going to come thru the door of real estate… enrich deeply, while leaving room for interstitial expansion") — `notes/realestate-proposal-2026-08-21.md`; the condo shelf held **316** buildings and the names say condominium on **53** (the barber lie again, read off the signs): `realestate_sub()` splits **condo 53 · apartment 242 · dorm 22** at classify(), the moobaan child kept as a NAMED SLOT without a match rule (wiring was tried; test_facets refused a rule matching zero records, correctly — one line wires it when the landuse door lands), Sunshine Apartment agent→apartment by retag receipt (`add_sub` taught to the applier); `importers/audit_realestate.py` — agents printed whole (5 is ALL OSM holds; is Sara + อคิน ลิสซิ่ง flagged for a person), จัดสรร appears only in VILLAGE names, **0 สำนักงานที่ดิน in the whole catalogue**, hotel-side 60 counted never re-filed; register `data/curated/realestate.json` empty-and-saying-so with the 12-site first-hand read queue; 12-key `realestate` facet set + worker keys (worker redeploy is Nan's move; new keys filter harmlessly until then); `/realestate.html` — the words w/ RTGS/tone/root (ค่าไฟหน่วยละ first; why a Mansion is cheap; เซ้ง), six desk sentences (TM30 and the quota asked as questions pointed at the desk and the นิติบุคคล — no statute recited unfetched), the four shelves, ใกล้หอนาฬิกาเชียงราย (metres from catalogue coords, method stated), the census of silences; `realestate` search panel by variants/query ONLY (the mined table sends หมู่บ้าน + "buildings" here — a village name must not be doored; test_search holds หมู่บ้านป่าไผ่), แมนชั่น + mansion widen the thesaurus ring; asked `monthly-apartment` + `student-dorm`. **ALL SIX RUNNABLE DOORS RUN 2026-08-21** (Nan: "go ahead on everything you can") — land offices 0→4 · dorms 22→84 · estates 0→22 with 590 villages fenced out · 6 building sites read (2 speak; a Booking.com affiliate redirect caught masquerading as a building own-site) · agents = a closed question (403s and JS shells; portals are not sources) · the Treasury condominium register harvested (385 northern buildings; 366 CM vs our 53) and land-valuation recorded UNUSABLE (cadastral keys only). Door 7 TTD still blocked on WO-17 key |
| WO-28 | โรงเรียนพระปริยัติธรรม + สถาบันอุดมศึกษา — the two registers the schools shelf was still waiting on | **BUILT** 2026-08-21 — the last empty child on the school tree filled: **27 monastic schools**, 13 of them pinned at the temple the register says they stand in, and the temple's own page now names the school it hosts; **7 higher-education institutions** the crawl never had, incl. both Buddhist universities. `KNOWN_EMPTY` entry retired with its receipt. |
| WO-30 | ใครเลี้ยงมด — the page that says a person makes this, the English half of the description, and the nod ledger | **BUILT** 2026-08-21 — `/who.html` (footer + llms.txt + sitemap, `meta name=author` + JSON-LD `Person`), the no-desc fallback made a full sentence in BOTH languages + `og:locale:alternate`, and `heard.py` — the recognition ledger, which is NOT part of the site and is fenced out of both publish paths. Scratch build 21,703 pp; publish gate + alt-text + asked all PASS. Section below. |
| WO-29 | ฉีดน้ำเลี้ยงข้อเข่า — the knee-injection question: the ortho silence, the words, the twelve calls | **PROPOSED** 2026-08-21, a stranger's Facebook question Nan brought to the site ("Who can provide me with a knee viscosupplementation injection in Chiang Mai?") — `notes/knee-injection-proposal-2026-08-21.md` + the call sheet at `notes/knee-call-sheet-2026-08-21.md`. **The census: 0 records in 19,980 carry viscosupplementation, hyaluronan, osteoarthritis or PRP in any spelling; 2 carry orthopaedics at all; 1 of those 3 ortho records has a phone.** Widening the `ortho` pattern was tested and gains ZERO — the silence is the naming custom (a Thai clinic is named after its doctor), not a mapping bug. Door 1 is zero-network and needs only a telephone. |
| WO-31 | สมาธิสั้น — the ADHD page: the three questions people fold into one rumour, the molecules, and the register the corpus could not supply | **BUILT** 2026-08-21 — `adhd_layer.py` → **/adhd.html**, `data/curated/adhd.json`, `importers/audit_adhd.py`. **The census: 0 of 20,327 records in both provinces name this care in any spelling, in either language — no สมาธิสั้น, no ADHD, no เมทิลเฟนิเดต; FIVE carry จิตเวช/พัฒนาการเด็ก at all, and two of those five are the same hospital entered twice.** So the register is curated research at the `additions-*.json` bar — the place's OWN words, on its own site, dated — and the **grade rides on every row**: 1 `stated` (RICD, which names it itself) · 3 `psychiatry` (the sign says จิตเวช, the door this care goes through here, but it has not said ADHD) · 2 `route` (a teaching hospital where the department is standard for the class, nobody having confirmed this one) · 1 `unread` (its own page would not open, recorded as that and nothing more). `ADHD_NAME_RX` is one object the audit imports, so the page's sentence and the audit's count cannot drift; สมาธิ alone is never a rule — it is meditation, and it is in the name of half the temples in the province. **The design is keeping three questions apart**, because collapsing them is what makes a person believe there is no door: (1) WHICH SCHEDULE a molecule sits in — the amphetamine family is a category-1 narcotic and **no permit exists to apply for**, while methylphenidate is a category-2 psychotropic a traveller may carry with papers, and atomoxetine is an ordinary prescription medicine; the page links the อย. checker rather than copying a table that will rot. (2) WHAT THE NATIONAL LIST STOCKS — บัญชี ค, tablet, 10 mg only, which makes a person arriving on a long-acting formulation a **supply** problem and not a legal one, and those are solved differently. (3) WHAT A DESK WILL DO — handed over as questions to ask, never recited as fate. No dose, no brand recommended, no doctor named; brand names appear in ONE place, the molecule table, so a reader can match the small print on their own box to a legal class. `adhd` search panel (10 → 14 panels) + the `adhd-words` reader sheet. Blocked and said so: adhdthailand.com fails its TLS handshake from this machine (named as a lead, NOT linked as a register) and the DMH's own per-institution service PDFs refuse a fetch. · **2026-08-22 — the dead-ref rule.** The สวนดอก record cites the faculty page that did not resolve, which is honest provenance and was also an `<a href>` to a URL link-health had buried: the publish gate refused it, correctly, and **the whole site stood unpublished from 23:02 to 10:15** while WO-27, WO-30 and this page waited on disk. Every outbound link in the layer now goes through `out_a()` — alive, and it is a link; dead or address-less, and the label keeps its place while the address, the verdict and the date of the check move into the tooltip. A citation that no longer opens is still evidence; it just stops being a door. Scratch build 22,094 pp, links to broken URLs 1 → 0. · **2026-08-22 — the fourth molecule, from a reader's own question** (Nan uses armodafinil): the row that was missing. Both official tables read whole — the **PSYCHO list** (วัตถุออกฤทธิ์, updated 25.07.2025, four categories) and the **NARCO list** (ยาเสพติดให้โทษ, updated 15.09.2025) — and **neither names modafinil or armodafinil**: methylphenidate sits in the psychotropic category-2 column, thirteen M-substances are listed there, and this is not one of them. **The asymmetry the registers show:** the อย. checker's own substance database — 2,569 generic names, queried at `blind_ddl_drug`, the endpoint its own autocomplete calls — **contains modafinil and does not contain armodafinil at all**, so the enantiomer has no entry of its own to be ruled on. **The checker will not rule on anything** until a traveller enters family name, given names, arrival and departure dates, e-mail and country AND ticks the terms — so "check it yourself" is a form, not a lookup, and the site fills it in for nobody. Two things refused a read and are printed as refusals, not guesses: the National List search ('The action you have requested is not allowed', 2026-08-22) and the ยาทะเบียนตำรับ product registry (pertento timed out, porta redirected) — which means the site states the CLASS and says nothing about STOCK, a different question and the one a pharmacy answers. **Layer fix that came with it:** `CARRY_FLAG` gains `unstated` ("ยังไม่มีคำตัดสิน · no verdict on file") and the lookup's default now points there instead of at `permitted-limited` — a molecule nobody has ruled on was rendering as "may be carried in, with papers", which is the page inventing the one fact it exists to keep honest. |

| WO-32 | ดูแลระยะยาว — long-term care: the four questions (บ้านพักคนชรา · พักฟื้น · บำบัด · วัยเกษียณ), the mended social_facility rule, /longcare.html | **ZERO-NETWORK BUILT** 2026-08-26, Nan's ask ("enrich active retirement, convalescence, addiction medicine, and nursing homes on motdang.net and defiant.to") — `notes/longcare-proposal-2026-08-26.md`. **The find: a classifier bug, not just a naming custom** — every `amenity=social_facility` filed as "Volunteering" with the `social_facility=nursing_home\|assisted_living\|rehabilitation` subtag thrown away; a nursing home, McKean's assisted-living garden and the best-known residential rehab in the province all stood on the volunteer shelf while the cached crawl held the truth. Rule mended at classify() (one copy in `importers/audit_longcare.py`, orphanage/training-centre/outreach fences witnessed); **medical gains a `long-care` child**; 3 merges (P.D. ×2, The River ×2, สวนปรุง OSM/MOPH); specialty gains `geriatric` + `addiction` (ธัญญารักษ์ the institution; \brehab\b fenced from Rehabilitation so McKean and the SSO centre stay out); register `data/curated/longcare.json` with the grade on every row — `mapped`/`route` only, and the **empty `stated` tier printed on purpose**; `longcare_layer.py` → /longcare.html (four sections kept apart; convalescence rendered as a census + three real doors because there is nothing to register yet; retirement rendered as doors to the shelves a LIFE lives on); medical-shelf band; `longcare` panel (15th); 7 thesaurus groups (parity 528/528). **Doors await Nan's numbered go** (note §doors): wide `longcare` Overpass group (sibling crawl proves ≥5 uncaught elements) · สบส. licence register · DMS addiction register · own-site reads via care_targets · the defiant partners.db fold. Same day on defiant.to: rehab bucket split (physio 7 · addiction 4 · rehab 4 · geriatric 11), /retirement/ + /recovery/ + /addiction/ built at the =Diabetes.md bar, QA green, NOT deployed (wrangler token dead 8/26). |
| WO-37 | ในเวียงหรือนอกเวียง — the moat page: nine ways to tell which side of the water you stand on, for the nine named crossings; the counter-rotating rings measured; the on-device checker | **ZERO-NETWORK BUILT** 2026-08-27, Nan's ask ("lots of visualizations and different clues, perhaps some topology strategies… I live here and circle the moat daily — still have 0 clue") — `notes/moat-inside-outside-2026-08-27.md`. `/moat.html` via `moat_layer.py` (hooked after the doi layer — earth page, then water page), 🏯 door in the เมือง band, 17th search panel (`moat`: คูเมือง · ในเวียง · แจ่ง · gate names). **Nine ways ordered by working range** — the mountain (10 km, with the doi transect showing the town leaning off it: west wall 316 m, east 313, Ping bank 312), the skyline, the three waters, the แจ่ง and their self-describing names (หัวลิน head-of-conduit at the high corner, ก๊ะต๊ำ fish-trap at the low), **the two one-way rings measured from the WO-13 roads snapshot — inner four counterclockwise, outer four clockwise, zero dissenting segments, i.e. water always on the traffic's right**, the royal street-name cluster WITH its decoys (ราชวงศ์ stands outside on purpose to fool sign-readers), postcode 50200 as a ruling-out-only test (87% of inside addresses, but 303 spills outside — measured live each build), the Jordan-curve crossing-parity rule with a tally widget and the closed-loop walk test (5,985 m ≈ 80 strolling minutes; a river never brings you home), and ในเวียงก่อ? + an entirely on-device point-in-square checker (geometry from `MOAT_POLY`/`_moat_crossings()`, nothing transmitted, no-JS floor prints the corners and hands over the eight-line function). Census strip live from the records (1,387 places · 40 wats — one every ~236 m · 535 food · 413 hotel) dooring to the 🏯 old-city tag. Held for Nan (note): the กู่เฮือง gloss could inherit better provenance from wichaa · a tenth way (songthaew colours) left out as unverifiable from the catalogue. Card no longer held: **`make_moat_card.py` drawn same evening on Nan's ask** — the night ground under the square, nine crossings lit, `assets/og/moat.png`, wired with the shelf_og fallback discipline. **In passing: the publish-gate failure WO-33 flagged (longcare.html → theriverrehab.com live `<a>` on a broken verdict) was holding the whole walk shut — fixed here by routing longcare's `site` through the WO-31 dead-ref rule (`site_a()`, JSON-LD guarded too). Gates after: publish 22,165 pp / 0 broken links PASS · alt-text PASS · asked PASS · routes PASS · search OK. The walk is free to ship.** |
| WO-36 | ย่าน — the bar lowered, the children split: HUB_MAX_ROWS 1,400, the curated zone file with the anchor rule, three children re-shelved by the parts of town people say out loud | **ZERO-NETWORK BUILT** 2026-08-26, Nan's numbered go on WO-35's held call 1 ("Go ahead with this, and also split the children") — `notes/zones-split-proposal-2026-08-26.md`. **Part 1, one number:** 2,500 → 1,400; essentials (2.2 MB→160 KB) · medical (1.9→136) · school (1.7→132) · hotel (1.5→120) flip to hubs on the WO-35 mechanism unchanged; wat still held by the coverage gate, all cr shelves under the bar. **Part 2, the spine measured before chosen:** the road graph reaches 838/1,609 thai records (52%) across 289 streets of ~3 places each; tambon/amphoe attrs 0; addresses 366/2,910 — all three printed as dead ends. What every record has is a pin, so: `data/curated/zones.json` — 10 city boxes (the moat and its named quarters) + 10 amphoe circles, first match wins, **every box holding named anchors from our own records** (the moat proven by วัดพระสิงห์ standing in it); `check_zone_anchors` refuses the whole build on a drift, `importers/audit_zones.py` the standalone witness (10 anchors OK; census: 1,528/14,490 = 10.5% in no zone → the รอบนอก fallback page, the road graph's "a fact, not a failure" rule). The first draft borrowed วัดเจ็ดยอด for two zones it sits between; the check caught it before the first build and the anchors were re-picked. **The three children past 1,000 rows** — food/thai (1,609, 1.7 MB→56 KB) · food/cafe (1,301, 1.4→56) · school/government (1,064, 1.2→64) — each now a zone hub mirroring the parent shape: `yan-<zone>.html` real listing pages with toolbar/sorts/facets, three doors as a taste per line, the complete roll at `all.html` noindex,follow with its MB printed on the door. Build 22,163 pp (+64). Held for Nan (note): zone names/bounds are hers to edit (curated data, not code) · cr zones a separate sitting · wiring zones into the "By neighbourhood" sort on unsplit shelves (touches md.js). |
| WO-35 | ชั้นที่โตเกินหน้าเดียว — the shelf that outgrew one page: cm food 4.2 MB → a 244 KB hub of its sub-shelves, the complete roll behind a weighted door | **ZERO-NETWORK BUILT** 2026-08-26, item 2 of Nan's "one at a time" — `notes/food-hub-proposal-2026-08-26.md`. **The measurement: cm/food/index.html was 4.2 MB — all 4,151 places, 4,227 links — while ten sub-shelves stood built beside it**; on the connections this site is for, a visitor's likely second click cost a minute of download. **The rule, not a food special-case:** `HUB_MAX_ROWS = 2500` with a double gate — past the bar AND children covering ≥90% (measured first: 11 food children cover 4,151/4,151 cm; cr's 34 strays sit under the bar and keep their plain listing). Only cm food crosses today; essentials (1,992) · medical (1,526) · school (1,493) · hotel (1,465) sit under it, wat (1,497) held back by the coverage gate — a shelf that grows past the bar flips on the next build with nobody remembering to. The hub keeps the art band, count, bands and map, then one line per sub-shelf (bold link · count · three doors as a taste), a ยังไม่เข้าชั้นย่อย section for any stray so nothing vanishes into "the children have it", and **📜 all.html — every row, toolbar and sorts intact, noindex,follow (the sub-shelves are the indexed copy), its ~4.2 MB printed on the door** so nobody on a hilltop opens it unwarned. Sub-shelves, place pages, GeoJSON, search, tags untouched; build 22,099 pp (+1: the roll). Three calls held for Nan (note): lower the bar to ~1,400 (essentials/medical/school/hotel go hub, one number) · split thai (1.7 MB)/cafe (1.4 MB) by neighbourhood · examples per child 3↔5. |
| WO-34 | ห้าครอบครัว — the quiet row banded: 21 header links regrouped into five labeled families, none removed, none renamed | **ZERO-NETWORK BUILT** 2026-08-26, Nan's ask ("could it be organized/navigated better?" → "one at a time") — `notes/header-bands-proposal-2026-08-26.md`. **The measurement: the `.svcbar` had grown to 21 links in one undifferentiated run on every page**, one door appended per work order since WO-12, six of whose labels also stand in the homepage category grid pointing at different addresses (board vs shelf) with nothing saying why. Regrouped in `page()` into `.svcgrp` families — เมือง · กิจกรรม · ดวง-เทศกาล · ช่วยมด · มดแดง — each opened by a `.svclbl` that is a label, not a door. Desktop: a line per family, label in mute ink with a gold bead. Phone: the one swipeable row untouched, labels riding as milestones. Every URL and every link's words exactly as before — no bookmark broken, no hand retrained; the twice-listed six stay, now legible (header = the board, grid = the shelf). Three trims listed in the note await Nan's numbered go. Items 2–4 of the same survey (the 4.2 MB food index → hub; the `learn/` slug-label mismatch; the root→/cm/ re-root before Chiang Rai) deliberately untouched — one at a time. |
| WO-33 | ของฝากที่เดินทางได้ — conservation and protection status of animals and plants, for the traveller at the airport: the carry-flag register, the four legal tiers, /souvenir.html | **BUILT** 2026-08-26, Nan's ask ("enrichment on the conservation and protection status of animals and plants… a problem for travelers at airports") — `notes/souvenir-wildlife-2026-08-26.md`. **The census (live in `souvenir_layer.py`): of 20,702 records, 0 say in their own name that they are a farm or nursery for these goods, 12 sit on the souvenir-handicraft rows, and a bare scan for เสือ/ผีเสื้อ/กล้วยไม้ meets 39 names that are nearly all namesakes** — ตำบลสันผีเสื้อ, Tiger Mart, orchid hotels: the WO-24 lesson measured again, and the reason the page is the coverage. Register `data/curated/wildlife.json` at the additions bar — **12 items × 4 carry flags** (`no` · `papers` · `ask` · `ok`), each with its class in BOTH systems (Thai tier + CITES appendix), a per-species link into the CITES checklist, and dated sources; **4 legal tiers** sourced from DNP's own legal-affairs page (สงวน — 21 species after the 2567 decree added the blue whale and the helmeted hornbill; คุ้มครอง — korkrasuang 2567 **with a 2nd edition dated 2569, this year**, which is why the page links registers and copies no lists; ควบคุม 2568; and the three CITES appendices with the checklist as the tool). **The page's one rule: legal to buy in Thailand is not legal to fly with** — ivory the sharpest case, lawfully sold domestically under the Ivory Tusks Act B.E. 2558 (FAO-mirrored text cited) while no traveller document exists for taking a piece out, and the customs airport list (fetched, quoted) names CITES wildlife among prohibited goods outright. The frame stays auspicious: h1 is the things that DO travel (silk, celadon, Bo Sang umbrellas — the `ok` row), the questions go to the till not the desk ("species on the receipt?", "farmed or wild?", "do you arrange the papers?"), and no penalty tables are recited. Every outbound link rides `out_a()` (the WO-31 dead-ref rule from day one). `souvenir` search panel (16th); `importers/audit_wildlife.py` — register integrity (a legal claim with no dated source exits 1) + the census with its hits printed. Blocked and said so on the page: cites.org's Thailand national-authorities page and its plant-export-procedures page both 403 a plain fetch (2026-08-26) — printed as refusals, with the DNP portal and the customs page's own DoA/DLD lines standing in. Scratch build 22,100 pp; alt-text + asked + search PASS; publish gate FAILS only on WO-32's longcare.html → theriverrehab.com dead href (not this order's page — flagged to that order). |
| WO-40 | โนตารี — the three doors of getting a paper sealed: the notarial-attorney facet, the MFA desk on floor 5, the consulate that moved, /asked/notary.html | **BUILT** 2026-08-28, Nan's ask ("Enrich Notarial services in Mot Dang") — `notes/asked-notary-2026-08-28.md`. **Census: 20,699 names, 0 say โนตารี/notary in either script; business/professional held 5 records (1 CM = a visa agency, 4 CR lawyer offices, none stating the work); the US Consulate and the MFA legalization desk were absent from the catalogue entirely.** Three curated records with dated own-page sources: **Aphiwat Bualoi Law Office** (Huay Kaew opp. MAYA, EN/TH, Lawyers Council notarial registration B.E. 2566 displayed, same-day if morning, `attrs.facets.notary`), **MFA legalization desk** (fl 5 Central Airport, Robinson side — ฿200/seal 2 working days, ฿400 express, fees quoted from the info.go.th manual, queue qlegal.consular.go.th, pinned by anchor-match to our own mall record), **US Consulate General** (US$50/seal by appointment — shipped `needs-pin` because **OSM still pins the old Wichayanon compound** while the consulate's own page states the superhighway address: the record's reader-facing warning is go-by-the-address-not-an-old-pin; both embassy pages 403 a plain fetch, refusals printed in the note). `asked/notary` page via the asked loop — the word first (three vocabularies, one per door: โนตารี / นิติกรณ์ / notarial services), which door for which paper with every price as-published-not-counter-confirmed, the framed-certificate check + the one phone sentence (works on the 4 CR offices too), **the apostille date said auspiciously: acceded 30 มิ.ย. 2569, in force 28 ก.พ. 2570 — the chain gets one link shorter (HCCH status table fetched)**, the RON at-home line taught as a question not a brand, doors to care/realestate/gov. `professional` facet set (WO-40): **notary 🖋 the one new FACET_KEY** (worker redeploy is Nan's move; until then it filters harmlessly, the WO-27/38 arrangement) + english/booking/card reused. `notary` search panel (19th) on the trade's three vocabularies + POA/proof-of-life phrasings, prices in the facts strip. Receipts in the note: the reconcile junk-matches (a train station named เชียงใหม่ answered for the consulate), and **the CR trap fetched: "Notary Public in Chiang Rai" is a Bangkok mail-in page wearing the province's name** — CR gets a sentence and the phone question, not an invented record. Leads left with their one act each: Siam Legal (site 403s; call), the 4 CR offices (call with the sentence), the translation-shop census (its own asked-key morning). |
| WO-38 | เซเว่นทุกซอย — the branch layer: the barber lie on the convenience shelf, the measured joins, the two voices, /seven.html | **ZERO-NETWORK BUILT** 2026-08-27, Nan's ask ("much deeper enrichment dive on 7-11's… so individual and complex, we've barely scratched the surface") — `notes/seven-proposal-2026-08-27.md`. **Sevens 404 → 462 off their own signs**: `seven_from_name` at import (`brandFrom: osm-name`, 58 receipts printed by the audit) with three witnessed fences — the `not:brand:wikidata` denial way, the เซเว่น สตาร์ condo held out by the sub fence, and **"7-11 หลอด biers Bier Stube" (the beer stall in 7-Eleven livery) refused by the residue rule**: a sign that says more than the brand is a nickname or an imitation. The hoped-for OSM branch names measured and found absent (270 `alt_name`s, every one just "7-11") — the real สาขา names are CP All's and stay WO-18's parked door. Facet set += `card` 💳 · `atstation` ⛽ · `slurpee` 🥤: **atstation 110 by the measured 80 m fuel join against our own 435 stations** (curve in import_fixtures.py's docstring, ATM-story style: 41@30 · 92@50 · 110@80 · 125@120 — the forecourt is 40–70 m deep, past 80 is across the road), card 13 (the payment TAG_RULES existed since WO-8 and were only ever filtered out by the set not declaring the key), slurpee 2 (two witnesses are still evidence). `SEVEN_CTX` in build.py — twins ≤ 150 m (real pairs start at 44 m; **the two closest "pairs" are 1 m and 6 m apart = one shop mapped twice, fenced at 25 m** and printed for the merge list) + named non-convenience anchors ≤ 120 m (**601/726 branches, median 27 m**) → the **sevenband on every convenience place page**: its double (labelled by the double's own anchor so two identical names tell apart), who it stands beside with metres and method stated, the door to the hub. `seven_layer.py` → **/seven.html** — census live (never pasted), brand table with the no-brand rows honoured as neighbourhood shops not data gaps, the doubled sevens, **the coverage strip: the median catalogue place stands 340 m from a seven, 6,004 places within 200 m, 2,693 beyond 5 km said plainly** (the proposal's 285 m was a biased quick pass — postscript in the note), zone table on WO-36's boxes, the chain-voice primer (9 cards, confidence: general-knowledge, alcohol windows pointed at the chiller's own sign — no statute recited unfetched, and **the toilet sentence reused verbatim from data/toilets.json**), counter words w/ RTGS+tone+root (โชห่วย from Teochew 雜貨), the door-survey asks riding the existing facet 🐜 route; emits docs/data/seven.json. `seven` search panel (18th) + 4 test_search queries; llms.txt gains "Sevens — two voices" beside the toilets section; worker FACET_KEYS += 3 (**redeploy is Nan's move; until then the new keys filter harmlessly**, the WO-27 arrangement). `importers/audit_convenience.py` — BY-SIGN receipts, REFUSED (2, both fences shown holding), **lotus 22 / big-c candidates printed for Nan, never a regex** (which era of the chain's name a sign carries is her call), 4 dupe pairs, and a stray worth her eye: **cr-osm-node-2148639746 is named เซเว่นอีเลฟเว่น in full Thai and filed as a MALL**. `tests/test_seven.py` 13 checks (radii kept in step across build.py/audit, the name rule's witnessed refusals, ctx integrity over real records, the band's fences) + test_facets green. Doors NOT walked, each needing her word: WO-18 brand locators (stands parked as-is) · fixtures re-crawl · an in-mall facet (2 basement `level` tags are not enough to build on) |
| WO-41 | สัญญาความสด — the freshness contract: Phase 0 discovery, the Coming-up repair (4d/4e), **and Phase 2 ingest hardening** | **PHASE 0 REPORTED + 4d/4e ZERO-NETWORK BUILT** 2026-08-28, the work-order brief ("eliminate stale-data display as a class") — `notes/freshness-phase0-2026-08-28.md`. **All four symptoms verified, two with sharper mechanisms than the order assumed.** (1) Events: EMPTY, not stale — Aug 24 a run completed with zero rows and WROTE the empty basket over the last good 69-event file (no min-rows guard); Aug 25→ every run CRASHES: harvest_events selects sources from the SHARED data/sources.json by `method==json` alone, later orders registered non-event sources there, and the OBEC school register's **17 MB JSON LIST** raises AttributeError past the too-narrow `(URLError,HTTPError,OSError)` net — watch_data.py has said "hollow" into the log every morning since, with nothing acting on it. (2) Lottery: false staleness exactly as diagnosed (fetched Aug 17, draw Aug 16 = current; next draw renders ~1 ก.ย. — the fetcher's presence-only rule keeps unconfirmed dates out, so the chip carries the ~ convention). (3) Coming up: month-distance selector + baked เดือนนี้ — verified on the built homepage (Mother's Day on Aug 28); **the chips are NOT the 4a offender** — they already compute ที่แล้ว-strings client-side (build.py's own comment: a baked today would rot). (4) Gold: structurally one cycle behind — finance fetches 07:10 only, standing walk refreshes weather+air alone. **Already-existing machinery the later phases must GROW, not duplicate: importers/watch_data.py is the manifest's embryo** (cadence-aware max-age, hollow checks, born of the 2026-08-16 triple-empty its docstring records). Frame mapped onto the house: launchd + two walks + cache/standing-walk.jsonl ledger; escalation → task board / cache flags. **4d/4e BUILT same day:** `occurrence()` — announced end-date filter (multi-day stays till it ends; announced-and-over falls through to the rule), **8 fixed festivals gain the machine-readable `day` their own window text states** (the four "usually the Nth weekend" fairs deliberately do not), roll-forward past the date (Mother's Day → 12 Aug next year by computation); unresolved movables leave the dated rows for the **ช่วงนี้ของปี around-line** (the order's separate list); server text absolute (no-JS floor always true; the เดือนนี้/เดือนหน้า literals are gone from the panel); every row carries data-until and **md.js prunes past rows at load on MD_TODAY** — the strip corrects itself even if every walk stops (the order's test 6, this panel). `tests/test_freshness.py` — frozen-clock at the symptom day (Aug 28 excludes Mother's Day, Aug 1 includes it with its absolute date; Songkran rolls to 13 Apr; no relative literals; pruner wiring) — **its own first draft caught a namesake: "akha" is inside mAKHA-bucha**, the WO-24 lesson again. Phases 1–3, 4a–c, 5, 6 await Nan's numbered go with the mapping in the note; the Phase-4a baked-วันนี้ worklist (cinema tile, wheel module, cooking board, festival what-is-shut) is inventoried there. **PHASE 2 BUILT 2026-08-28 on Nan's go** — `importers/ingest.py`, the five rules no fetcher can skip (validate before write · atomic tmp+rename · never destructive on failure · sidecar meta always · quorum), retrofitted through **all nine writers**. **THE EVENTS FEED IS BACK: 0 → 88 events, restored from the cache already on disk, zero network** — the selection now asks the registry what a source YIELDS (`"events" in yields`) instead of `method==json`, so the OBEC school register is no longer handed to the events parser; the per-source net widened from three transport errors to `Exception`, because isolation must hold against the failure nobody predicted; parse_tribe states its shape and raises a plain ValueError on a bare list. `MIN_ROWS=3`/`QUORUM=2` guard the PIPELINE, not the city's mood. **make_finance keeps its three sections apart** (fx/gold/crypto fail one at a time; a dead section keeps yesterday's numbers and is named in `stale_sections`, only an all-three failure is refused) — the 2026-08-16 `{"generated": today}`-and-nothing-else incident cannot recur. Lottery's unchanged-draw path now RECORDS the run while still leaving the file untouched (a sidecar that cannot tell "checked, nothing new" from "nobody looked" is the same blindness). Sidecars are gitignored per-machine state and their four snake_case stamps joined `walk_fingerprint.VOLATILE_KEYS`, so meta timestamps cannot rebuild the site every 20 min while a feed that STARTED FAILING still moves the gate. `tests/test_ingest.py` — 17 checks incl. the order's acceptance 4 (byte-identical previous file + failures++) and 5 (1 row vs min 15 refused), no-half-files, quorum, and both events defects driven through the real parser. **Live proof of the Phase 5 gold finding, in passing: make_finance run at 17:0x ICT returned TODAY's 16:56 price** — the 07:10-only schedule is the whole gap. |
| WO-42 | สบายขึ้น — the sign hung: what.html wired into the shell, the empty search taught to teach, one line of orientation in the hero, and the shelf made a rung | **ZERO-NETWORK BUILT** 2026-08-29, Nan's ask ("Many people commented 'I really like motdang.net but I don't know how to use it'. Come up with a plan to increase the sabai round here!" → "Please work your way through the list") — `notes/sabai-proposal-2026-08-29.md`. **The measurement that explains the whole comment thread: what.html had ZERO inbound links.** The page written for exactly that reader — six refusals, fifteen tappable plates, LIVE since 8/29 — was linked from nowhere: not the chipbar, not the svcbar's five families, not the footer (why/who/reach/privacy were there; what was not), not the homepage, not the 404; `grep -rl what.html docs/` returned the sitemap and the page itself. It could only be SENT, and `notes/what-page.md` says so in its own words (*"the reader is never someone browsing; it is always someone sent"*) — the commenters are the browsing readers, and the site had no sign on any wall for them. Four more, measured: search.html with no `?q=` rendered **empty** (`q ? … : ''`) so the richest instrument on the site taught a hesitating reader nothing about itself; the hero carried no orientation sentence; **the 404 was the best wayfinding page on the site** (a reader who mistyped got more help than one standing on the homepage); a place page's crumb was two rungs, with the shelf demoted to a หมวด table row below the fold. **Built, five edits in build.py:** what.html into `page()` itself — first door of the มดแดง family and a footer link beside why/who, which is **0 → 22,171 pages** carrying it — plus the hero and a first-time line on the 404, nothing renamed, no URL moved; `start()` in md.js renders **all 19 curated panels as words to type** (glyph, bilingual title, href of the panel's own trigger term), so a tap fills the box and opens that panel's rich card — one tap teaches the whole loop (ช้าง → box shows ช้าง, elephant panel with live count 30, 221 rows), with the top shelves as a second door and what.html for the reader more lost than that, **and no new fetch: the panel file is already loaded by that page**; one hero line in the ant voice ending in the door (*สารบัญของคนแถวนี้ ไม่จัดอันดับ ไม่หักค่าหัวคิว · The city's own directory — no rankings, no commission* → *เพิ่งมาครั้งแรก เริ่มตรงนี้*), set in `--ink-soft` not the mute ink because **an orientation line nobody can read orients nobody**, and **no popup, no first-run modal, no tour** — on the connections this site is for an overlay is the opposite of สบาย, and this site does not interrupt people; the crumb's **third rung** (หน้าแรก › เชียงใหม่ › shelf › place) in the nav **and** the BreadcrumbList JSON-LD so persona 6 gets the same trail, using the exact href the หมวด row has always used, so no address is invented. The share card needed nothing: `make_what_card.py` + `assets/og/what.png` already existed and the page already asked for it. `tests/test_sabai.py` — **24 checks, and the reason it exists is that a link nothing enforces is a link the next work order deletes by accident**: the five families intact AND the door inside the right one, the footer copy, the relative root two levels down, the hero line and its door and that it is **not `position:fixed`** (no tour creeping back in), the 404 line, the `start()` branch rendering instead of `''`, the pills being search queries drawn from already-fetched panels, every panel able to supply a word and a bilingual title, and four rungs in both nav and JSON-LD; it emits the 404 into a throwaway dir so it can never land in `docs/` while a real build owns it. test_search · test_tags · test_routing · test_asked · test_facets · test_seven · test_shrines · test_freshness · test_alt_text all re-run green; build 22,175 pp. **Nan's own build held the lock mid-session and refused the second build — the WO-33 lock working in the wild, first sighting.** Held for Nan (note): a chipbar chip for what.html (deliberately not taken — eight chips, nine is a crowd) · the hero wording (one string, hers) · the pill set (all 19 vs a hand-picked six) · a curated primary-shelf rule for which cat becomes the crumb · **Move 6, the two questions back to the commenters** (the empathy map's own closing rule — its six personas are hypotheses awaiting the first ten real conversations, and these are volunteers), drafted in the note, **unsent — the Messenger export runs before any posting push** · the three WO-34 header trims and survey items 3–4 remain untouched. |

| WO-43 | ยามเฝ้าค้นหา — the search guard: 6.8 MB fetched to answer nobody, and the doors moved out of the script into the page | **ZERO-NETWORK BUILT** 2026-08-30, Nan's "start with the search guard" off the §1 finding — `notes/sabai-survey-2026-08-30.md`. **The measurement: md.js read the query and then fetched `data/index.json` BEFORE checking whether there was one.** An empty search cost **6,840 KB — index.json 6,158 + segdict 306 + md.js 181 + thesaurus 122 + panels 40 + shelves 30 — about 36 s on a 1.5 Mbps link**, to be told nothing; and WO-42's teaching pills sat *inside* that same await, so **the teaching built to spare people the wait arrived last, after it**. Two halves, both shipped. **The guard:** `if(!q)return;` immediately after the query is read, ahead of `loadIndex()` — browser-verified, an empty search now fetches **no index, no thesaurus, no segdict, no panel file at all**; a real query is untouched (`?q=ช้าง` still opens the 🐘 panel with its live count of 30 over 221 rows). **The served doors:** `search_start_html()` renders the start state at BUILD time into `<ul id="results">` — **search.html's body went 27 chars → 1,312**, all 19 pills, page 28 KB, and it now works with scripts off and is visible to the crawlers and models whose stated pain in `notes/empathy-map.md` is client-rendered pages (two pages on the whole site carried a `<noscript>`). Two gains fell out of moving it server-side: the pairs go through `bi()` so **the language toggle finally reaches the start state** (the JS copy emitted plain "th · en" it could not touch), and the Thai terms are URL-encoded by Python instead of by hand. **The client-side `start()` is deleted, not kept as a second copy** — the served page is the only definition, so the two cannot drift. `tests/test_sabai.py` 24 → **27 checks**, its teacher section rewritten to ask the stronger question (not "can the script draw the doors" but "are the doors in the page before any script runs"), plus the guard's own shape and a check that the dead copy stays gone. Eleven suites green; build 22,175 pp. Still surveyed and NOT built (same note): the two failing ink tokens `--mute` 3.0:1 / `--gloss` 4.0:1 → `#816e53` / `#816d55` · the 32 pages over 600 KB the hub rule cannot reach (wat held by the coverage gate at 1,365 KB, tags never had the rule) · phone 14 % and **LINE 0 of 20,702** · three broken links incl. the ADHD desk sheet that was never generated. |

| WO-44 | หมึกเงียบที่อ่านออก — the quiet inks made readable: two token values, the ladder kept, the gold split into bead and ink, and a contrast gate | **ZERO-NETWORK BUILT** 2026-08-30, Nan's go on the §2 finding — `notes/sabai-survey-2026-08-30.md`. **The measurement: `--mute` sat at 3.0:1 against the paper and `--gloss` at 4.0:1, both under the 4.5:1 floor for body text — and they were not decorative.** Between them they set **91 rules, every one a `color:`** (no border, no background, no shadow), on exactly the smallest text the site prints: `.tinynote` · `.src` · `.cat` · `.teaser` · `.photodesc` · `.adlabel`, plus `.herosub`, the homepage's opening paragraph. **The site's whole trust argument — provenance lines, source credits, read-dates — was written in its least readable ink, at its smallest size.** Shipped: `--mute` `#a08b6c` → **`#7d6b51`**, `--gloss` `#8a755b` → **`#685845`**, same hue, darkened only, so nothing structural moved. **The survey's own first numbers were wrong and were corrected before shipping:** computed against the paper alone they gave `#816e53`, which falls to **4.3:1** on the `--card-alt` the chips and bands use — the shipped pair clears 4.5 on **all three** light surfaces (mute 4.7/5.0/4.5, gloss 6.3/6.7/6.0). **The ladder was treated as a thing worth keeping:** pushing both to the floor collapses them into one colour and spends a level of the palette to buy contrast, so `--gloss` was darkened proportionally instead — ink 14.9 > ink-soft 8.4 > gloss 6.3 > mute 4.7, four distinguishable steps; a `--soft`-floor variant was computed and **rejected** because it put gloss at 8.0 against ink-soft's 8.4, the same colour in effect. **The one residual is written down, not buried:** `--mute` on a `--soft` background is 3.5:1 and five bands do put muted text there (`.myhint` `.mtband` `.planhero .hnum` `.festwhen` `.widgetbox .wtitle`) — `--soft` is 49 borders to 24 backgrounds, so the fix belongs to those bands (inner text → `--ink-soft`, or a lighter background for the background uses), and the test asserts the exemption so it stays visible. `tests/test_contrast.py` — **checks that read the tokens OUT OF THE SHIPPED STYLESHEET** rather than from numbers copied into the test: the floor for all four inks across all three light surfaces, the ladder's order *and* a >1.15× gap so no two neighbours merge, the `--soft` exemption, and that both quiet inks stay `color:`-only so a later edit cannot quietly make one a border. Twelve suites green; build 22,175 pp. **THE GOLD SPLIT, same sitting, on Nan's "do the gold-ink fix too": `--gold` was doing two jobs at once.** As decoration — the ‧ bead after a band label, the underline on a hovered header link, the watermark on the dark side card — 2.8:1 is fine, because nothing there is read; as **text** it was the hero's "Kept up daily…" line at **2.79:1** and the nine-doors / care-shelf counts at **2.99:1**, all around 13 px. **Measured in the live DOM rather than inferred from the stylesheet, which mattered: `.heroeyebrow` takes its colour from a rule 230 lines from the one that sets its size, and the first CSS reading pinned it to the wrong place.** New token **`--gold-ink` `#8e6621`** — same **38° hue**, carried to 4.5:1 on card-alt / 4.7 paper / 5.1 card — swapped into exactly three rules (`.heroeyebrow` · `.doorcard .n` · `.careshelf .n`); `--gold` keeps the bead, the underline and the watermark unchanged. Verified live: eyebrow **2.79 → 4.74**, both counts **2.99 → 5.07**, bead still `#c08a2d`, and it still reads as gold (a warm amber, distinct from the ant red beside it and the ink-soft under it). The gate grew the rule that keeps the split honest: `--gold-ink` clears the floor on every light surface AND keeps gold's hue within 2°, while **`--gold` may sit under the floor only where nothing is read** — an allow-list of exactly two selectors. **That check caught its own first draft**, which counted `text-decoration-color:var(--gold)` as a text colour; the regex now refuses a `-color:` property and the hover underline is correctly left as decoration. `tests/test_contrast.py` now 26 checks; twelve suites green, build 22,175 pp. |
| WO-45 | จดหมายข่าวรายสัปดาห์ — the weekly events newsletter parsed, and the 62 venues no crawl had | **ZERO-NETWORK-TO-BUILD, BUILT** 2026-08-31, Nan's ask (*"Please use this content for motdang.net … I bet some of the locations mentioned don't even show up on crawl. Find out what/where they are and add all available details, everywhere. Be EXHAUSTIVE."*) — `notes/newsletter-ingest-2026-08-31.md`. **The instinct was right: 62 of the venues one issue names did not exist in the 14,493-record catalogue in any spelling, in either script** — Chiang Mai Marriott, Cross Chiang Mai Riverside, Anantara Chiang Mai Resort, the Gymkhana Club, Seven Fountains, Sand Creek Golf Course, Old Chiangmai Cultural Center, and Chiang Mai Hall inside Central Airport Plaza (the mall itself is still absent — the catalogue held six pharmacies inside it and not the building). **events.json 82 → 401 · contact_leads.json 4 → 99 venues · place pages with a "what's on here" band 0 → 89 · venue_aliases.json 4 → 148 keys · cm 14,493 → 14,558 records.** The issue: 39 pp, 67 dated listings + 122 weekly fixtures + 21 notices → 319 events and 139 leads, against 82 events and 4 leads from every crawled source combined. **`importers/read_newsletter.py`** — stdlib, no network (it arrives as email; a human drops the text at `_incoming/newsletter/YYYY-MM-DD.txt`), called by `harvest_events.py` as a local source so it rides WO-41 Phase 2's validate/atomic/never-destructive discipline and a bad parse is refused rather than published. **The prose is never copied**: the body is venue-supplied press-release copy and `sources.json` has said since 7/29 to treat this as a discovery feed "not as a thing to copy", so the parser takes the FACTS (when/where/how much/how to book) and generates every description; notices are standing offers, not happenings, and yield contacts only. **A weekly fixture is a rule, not a date** — stated weekday, projected onto its next TWO occurrences, each marked `from_rule`; the next issue restates the rule so nothing outlives its source (festival_dates.json's charter again). Two PDF facts no rule solves: page seams rejoin correctly at 30 of 39 and wrongly at 9, pinned per issue in `ISSUES` because a bad join silently merges two events; and a weekday header with no blank line rides the block above it (Saturday first parsed 41 items, Sunday 0). **Pins came from the venues themselves**: 19 listings carried a Google Maps link the venue published, 11 resolved to coordinates → `exact`, **each citing the link it came from, because a pin without a citation is an assertion**; the rest through `geocode_local.py`, landmark→`approx` / street→`block` / coarser→`needs-pin`, no geocoding service called (that file's docstring forbids it). Final spread 11 exact · 12 block · 6 approx · 33 needs-pin. **Two refusals:** every address that was MY inference rather than the issue's statement was deleted rather than pinned (Gymkhana's road, Anantara's, the Marriott's, Chotana Mall's tambon), and **Kad Kriangkrai's gazetteer answer was refused outright** — Chotana Road at a confident ±280 m, 12 km south of the Mae Rim market Google's own link names; address kept, pin not. **Venue→place matching, "not built yet" on 7/29, is built — and not fuzzy** (fuzzy gave Araksa Tea Garden → "Garden Restaurant"): strict `match_venue()` plus a much larger alias file, with the newsletter's own spellings folded first in `read_newsletter.CANON`. **All 95 venues resolve; 100% of newsletter events carrying a venue string land on a place — 231 of 231.** Five records written then removed as duplicates the catalogue already held (CFCNX, Soi Dog Blues, Stories, สนามกีฬาเทศบาลตำบลสุเทพ — 18 m from the rugby club's own map pin — and Duke's Ruamchok), each an alias instead. **`_missing_from_catalogue` 5 → 2**; Araksa Tea Garden closed in passing from the Payap lead sitting unused in contact_leads since July; still open are Bua Bhat Factory (a phone, no address) and NARIT Astronomy Park (0 records carry NARIT or สดร in either province). **37 EXISTING records gained a channel** via `curated/enrich.json` — 22 phones, 13 emails, 13 Facebook, 13 LINE, 2 WhatsApp, 4 websites, only fields the record lacked, nothing overwritten; a venue-supplied release is the venue's own words one hop out, not a directory's scrape, and the `license` says so. **Campaign links refused as `website`** (Favola's marriotth.tl menu shortlink, the InterContinental's truncated offer URL, buddhadailywisdom for วัดทุงยู — the organiser, not the temple); where the host WAS the venue's own only the origin was kept, because a seasonal path 404s long before the domain does. **Three defects the newsletter exposed in older code:** `event_when()` printed `%H:%M` unconditionally, so a listing stating a day and no hour rendered *"Every Monday at 00:00"* — the site telling readers a yoga class starts at midnight; the iCal and tribe feeds always carry a real time so nothing had ever shown it, and it honours `all_day` now. `dedupe_leads()` copied five fields and dropped Facebook, Instagram, LINE, WhatsApp and the maps pin on the floor — **while LINE ranks second only to the phone in `channels()`**. And **my own first pass filed LINE as `attrs.line`** when `channels()` reads `lineId`/`lineUrl`: 22 LINE contacts were silently invisible until the keys were fixed, and `phone` is semicolon-separated by house convention so a venue printing three numbers keeps all three. **The alias trap that cost 6 of 90 matches:** keys are looked up as `_vnorm(string)`, so a key written `UN Irish Pub & Restaurant` or `The Duke's` can never be hit — and `_vnorm` keeps the acute, so `café` needs its own key beside `cafe`. Time parsing earned two fixes: **"6-11pm" read as 23:00** (the meridiem sits only on the end of a range — Game Tree's Catan night five hours late) and **"12 noon until 3pm" read as 15:00**, opening a listing after it ended. **Sources the issue turned up, each recorded as MEASURED not as claimed:** **runlah.com verified and the best find** — event pages server-render a complete schema.org `SportsEvent` block (name, startDate +07:00, nested Place naming the province), no key, no JS, though its index is client-rendered at 213 words so slugs still come from this newsletter; **sansatan.com verified** (1,399 words of dates/distances/fees, no JSON-LD so it needs a parser); **thailandexhibition.com unverified** (200 but 294 words, no index path found); **ticketmelon.com blocked** (URLError — recorded as blocked, not empty, the 7/29 citylife distinction); **shutupwrite.com client-rendered**, its JSON-LD Organization boilerplate with no event data. `test_pins` caught my own error before it shipped: 4 records claimed an `exact` pin while naming a `pinVia`, and a surveyed pin is derived from nothing — the citation belongs in `sources`, where it already was. All suites green; build 22,242 pp into a scratch dir, because **Nan's own `deploy.py --yes` held the build lock for the whole sitting** (the WO-33 lock working in the wild, second sighting) — **the site is UNBUILT and UNDEPLOYED with these changes on disk; the next `build.py` + `deploy.py` is Nan's**. Held for Nan: **the partnership is still unanswered** (offered 7/28, nothing by 8/31 — two issues mined without one; ask again, ask differently, or keep mining is a fork, not a standing decision) · Central Airport Plaza itself (its two FDA pharmacy pins disagree by 4 km, so neither can be borrowed) · the next issue costs one paste plus ~10 min of hand-verifying its page seams · 1 Instagram and 3 WhatsApp group links reached no record because their listings named no pinnable venue · and **pre-existing, untouched**: `test_shelf_cards` fails on 6 orphan og cards (`shelf-cm-learn`, `-learn-gym`, `-transport-station` and the cr three) — verified unrelated, `learn` is a cat on 0 records and `station` a sub on 0 records in both provinces. |
| WO-46 | ผ้าปูที่นอนแบบไม่รัดมุม — the flat sheet: the home-textile shelf the catalogue has none of, the words to ask with, and three shrine groups rescued on the way | **ZERO-NETWORK BUILT** 2026-08-31, Nan's ask ("Getting farang style flat sheets in thailand is very challenging. Thais just use fitted and duvet cover. Can motdang help the handful of farangs who refuse to adapt to this reality?") then her go ("build the zero-network half of WO-46") — `notes/bedding-proposal-2026-08-31.md` + `notes/asked-flat-sheet-2026-08-31.md`. **The census, run the way WO-22 says to run one — the names first, in the language the shops wrote them: 20,778 records across both provinces, 28 words in both scripts, ZERO.** ผ้าปูที่นอน · เครื่องนอน · ที่นอน · ผ้านวม · ปลอกหมอน · ผ้าม่าน · รัดมุม · ผ้าเมตร · ร้านผ้า · ตัดเย็บ · ช่างเสื้อ · อุปกรณ์โรงแรม · bedding · bed linen · flat sheet · top sheet · duvet · mattress · fabric · seamstress · alteration all nil; only **textile** (2) and **ซักรีด** (2) survive anywhere. Home textiles are not a thin shelf here, they are an absent one — and this is NOT the beauty-shelf error repeating, because the names were read in Thai and the trade is genuinely missing from the catalogue rather than hiding in it under another word. **The tailor row was the tell**: `shopping/tailor` held 10, nine of them bespoke-suit houses with English signage and exactly one named in Thai — **รับซ่อมแซม เสื้อผ้า** (`cm-osm-node-13298710901`), which is a sign and not a business name. **Retagged** `sub: tailor → alterations` on its own name in both languages (name:en=repair clothes) against its single `craft=tailor` tag, which OSM uses for the whole needle trade; evidence read in `cache/overpass/cm/crafts.json`, crawled 2026-07-27, `cat` untouched, receipt in the record's own sources + a bilingual line in `data/fixes.json`. `import_all` reports **7 curated retags where there were 6**; tailor 10 → 9, alterations 0 → 1. **Three shelves opened, named for the trade and never for the asker** (the ขัดขี้ไคล rule: a shelf called "Flat Sheets" would hide every shop that calls it something else): `shopping/alterations` ซ่อมแซม-แก้เสื้อผ้า (1 record, renders), `shopping/fabric` ผ้าเมตร-ร้านผ้า and `shopping/bedding` เครื่องนอน-ผ้าปูที่นอน (0 records, correctly wireframe — no page built), with `shopping/tailor` relabelled **ร้านตัดสูท-ตัดชุด / Tailors** so it stops claiming a repair trade it does not hold. Both empty shelves are registered in `tests/test_facets.py` KNOWN_EMPTY with the census and — the part that matters — **neither reason says unfillable**: both wait on ONE crawl that has not been run, ranked in the note, hospitality supply first because that single fetch decides whether this shelf is five records or fifty. **Eight thesaurus groups**, written to `search-core/data/hand.thesaurus.json` and NOT to `data/search_thesaurus.json`, which is generated — `mine.py` + `sync.py` would have erased a local edit silently. **"flat sheet" now reaches ผ้าปูที่นอน** with nothing behind it yet, which is the correct state: the word works the day the first record lands. **ผ้าห่ม was deliberately left OUT** of the sheet group (a blanket is not a sheet; the mined table already pairs it with "blanket"), while flat/top/fitted DO sit beside ผ้าปูที่นอน as hyponyms rather than synonyms — a deliberate stretch of that file's contract, written up inline, because **Thai carries one generic word where English carries three specific ones and that asymmetry is the entire finding**. **THE DEFECT FOUND ON THE WAY, and it was one keystroke from being permanent: three WO-39 shrine groups existed ONLY in the generated file.** `city pillar · lak mueang · หลักเมือง · ศาลหลักเมือง · เสาหลักเมือง · **อินทขีล** · สะดือเมือง`, `devalaya · เทวาลัย · เทวสถาน`, and `shrine · spirit house · **joss house** · ศาล · ศาลพระภูมิ · ศาลเจ้า · หอผี` had been hand-written straight into `data/search_thesaurus.json` — a file whose own header says edits there are silently overwritten — so they were in no generator anywhere, and the first re-mine by anyone would have deleted Chiang Mai's own city pillar out of the search. `tests/test_shrines.py` caught it (check 7, "the words reach it"). All three recovered from git HEAD into `hand.thesaurus.json`; the shrine group came back RICHER than it left, keeping "joss house" and gaining the shelf label ศาลเจ้า-ศาลหลักเมือง through union-find. **A second staleness found and closed**: the search tables had never been re-mined since WO-39/WO-41/WO-45 landed — re-mining added 29 groups and dropped 14, so **the shrine shelf and the pest-control shelf had both shipped with vocabulary the search did not know**. Tables now 2,753 → **2,777 groups / 7,514 members**, shelf terms 618 → 624. **THREE CORRECTIONS TO THIS ORDER AS PROPOSED, all refusals rather than omissions: (1) ตลาดวโรรส was NOT re-shelved** — `retags.json` requires evidence a person read, the record carries a name, a pin and opening hours and nothing whatever about cloth, and the cloth floor is my knowledge and not a receipt; it stays `market`/`fresh` and becomes the top crawl target instead, with กาดหลวง on a second record 80 m away left unmerged (`merges.json` takes human-confirmed pairs only). **(2) `data/curated/bedding.json` was NOT created** — curated files are wired into `import_all` one at a time and an unread scaffold is dead weight; records go to `additions-chiang-mai.json` as the ขัดขี้ไคล five did, and the field contract lives in the note. **(3) the thesaurus edit changed repositories**, per the generated-file trap above. `asked_new.py flat-sheet --via other` opened the draft + its note, filled with the census, the ranked leads with the one act that clears each, and the refusals written in advance — no "sells flat sheets" flag from an inference, no `gap: true` (a gap publishes "nobody does this" and the finding is that the catalogue cannot SEE a trade, a different and possibly false sentence), no "Thais don't use these" framing in either language, and the free answer on the page regardless: **a duvet cover with no quilt inside IS a flat sheet sewn shut on three sides**. It **cannot leave draft** and the reason is structural — `find: {prov, sub}` resolves against tagged records and `sub: bedding` holds zero. Register → shelf → question, WO-39's order. **Verification: scratch build 22,258 pages** (`build.DOCS` repointed, no lock taken — the escape hatch `clear_docs()` documents), **30 of 34 suites green**; `test_facets` failed me correctly on the two unregistered empty shelves and passes now; `test_shrines`, `test_search`, `test_asked`, `test_tags`, `test_alt_text` green. The card check run against the scratch build shows **299 list pages · 299 cards · no orphans at all** — WO-45's 6 orphans are gone and the 137 seen mid-run were a concurrent build's wiped docs/, not a defect. Three shelves had no card; **all three drawn** (`shelf-cm-shopping-alterations` plus the two pre-existing `pest-control` ones), and `shelf_og()` reads `assets/og/` at build start so the next build resolves their og:image. `test_publish_gate` and `test_moat_geometry` read the real `docs/` and could not be evaluated: **another Claude session built this repo four times during this order** (pids 69828, 77125, 82512), and its first build read the catalogue 30 s before this order's `import_all` finished writing it — nothing corrupted, docs/ simply predates the retag. **UNBUILT and UNDEPLOYED against the real docs/; the standing walk (make_shelf_cards → build) closes both the cards and the pages on its next round.** |
| WO-47 | คำที่ร้านใช้ — the thesaurus made a page: 2,753 bilingual groups that only a search box can read, and the 1,149 that earn one | **PROPOSED** 2026-08-31, Nan's ask off WO-46 ("I think the thesaurus itself could benefit the public if it's made available in a friendly UX kind of way… shouldn't just be background knowledge") — `notes/thesaurus-public-proposal-2026-08-31.md`. **The site has been half-admitting this**: when search widens a query through the table it already tells the reader so — `build.py:3448` prints *รวมคำที่ความหมายเดียวกัน · including words that mean the same thing* — so a reader is told a table exists, told it changed their results, and given no way to look at it. **Measured: 2,753 groups · 7,427 terms · 2.7 per group · largest 25, and all 2,753 are bilingual** — there is no monolingual group in the file, which is unusual enough to be the whole product. Its own note says *synonymy only, spelling variants are the phonetic key's job*, so it is a meaning table and not a misspelling table, which is what makes it readable by a human. **Already fetched, not baked** (`build.py:3350–3356`): it is a public URL every reader's browser downloads, so publishing puts a door on a room the site already ships, and an edit busts the asset hash (`5408`) so the page cannot go stale against the search. **The filter is the design: only 1,149 of 2,753 groups have a footprint in the 20,778-record catalogue**; the other **1,604 are general-language synonymy** (`["abate","allay","decrease","ease","meliorate","บรรเทา"]`) — fine for widening a query, ruinous on a page, because it would present Mot Dang as offering a Thai–English dictionary it has not audited and should not be judged as. Those 1,604 keep working behind the search and get no pages. **A finding I nearly shipped and it was false**: 34 of 165 category values carry no thesaurus term — `hotel-full` (911), `health-station` (469), `bar-pub` (460), `street-food` (232) — which looks like a coverage hole and is not one. Those are internal slugs; checked directly, hotel · โรงแรม · bar · บาร์ · ผับ · street food · อาหารริมทาง · bakery · เบเกอรี่ · spa · สปา · museum · พิพิธภัณฑ์ are all present. Recorded because the next person to run that query gets the same wrong answer. **The shape**: `/kham.html` (คำ, word) on Yahoo-directory discipline — **Term (count)**, scannable, no search box needed to begin; group pages for the 1,149 showing every term in both scripts, how many records each reaches, and the shelf it opens, with a dead term shown as dead rather than hidden because that is a reader telling us where to crawl; **the search line made a link** — name the words and link the group where md.js already says it widened, one line, the smallest change and the highest-value, since it lands at the exact moment the reader wonders what just happened; and shelf headers carrying the words their trade is known by, so ขัดขี้ไคล/ระเบิดขี้ไคล are readable without a search. No new mining, no network — every number above came off disk. **Two blockers, both forks for Nan**: **provenance** — house law is that provenance travels with every fact and 7,427 terms currently travel with one sentence (*mined by mine.py from motdang data*), adequate for machinery nobody reads and thin for a page with a byline, so either `mine.py` writes per-group provenance on its next run (correct, costs a mining pass) or the page states prominently that these are mined from listings and unaudited (cheap, true, available today); and **คำเมือง** — the table already carries กาด beside ตลาด and เฮือง beside เรือง, and presented flatly as synonyms that flattens Lanna into a spelling variant of Central Thai, which is the error this site exists not to make. Marked as Northern, it becomes one of the better reasons to visit the page. **Voice constraint**: every gloss must read as *shops here say this*, never *the Thai for X is Y* — the site is not a language authority and the moment it sounds like one it is wrong. **WO-46 is this page's proof case.** |
| WO-50 | ไซส์ใหญ่ — the body Thai retail does not stock, and the two questions it splits into: clothes, which can be solved, and shoes, which largely cannot | **BUILT** 2026-08-31, Nan's ask (*"do a mot dang enrichment for large size men's and women's shoes and clothes"*) and her go on both halves of the fetch — `notes/asked-big-size-clothes-2026-08-31.md`, `notes/asked-big-size-shoes-2026-08-31.md`, `data/curated/bigsize.json`. **MEASURED FIRST, AND IT IS THE LARGEST HOLE THIS DIRECTORY HAS EVER FOUND IN ITSELF.** 14,665 records for Chiang Mai and 6,229 for Chiang Rai, and under `shopping/clothes` **zero**, under `shopping/shoes` **zero** — not a thin shelf, no shelf: neither key existed in `categories.json` this morning. Never OSM's fault: the census of 2026-08-07 counts **134 `shop=clothes` in TH-50 and 72 in TH-57**, which makes clothes the **sixth commonest shop value in Chiang Mai — ahead of supermarket, ahead of car, ahead of bakery** — plus 18 shoes, 10 boutique, 8 bag, 26 sports, 14 outdoor. **282 elements, on the open map the whole time.** The reason is one line long and it is in our own file: **`shop=clothes` and `shop=shoes` have NEVER appeared in `crawl_overpass.py` QUERIES, in any group, since the crawler was written**; the `shopping` group asks for doityourself, hardware, gift, second_hand, herbalist and healthcare=alternative, and not one is a clothes shop. Fifth sighting: เสริมสวย on sixty-two shopfronts, the notary, ห้องเสื้อ on a hundred and twenty-six, ห้องซ้อม, and now this. **AND THE ONE RECORD THAT SAID IT OUT LOUD WAS FILED AS A RESTAURANT** — of 20,894 records exactly one names itself big-size, **ร้านเสื้อผ้า The Bigsize** (node 4358877280), and it stood on the food shelf as a Thai restaurant because a mapper wrote `amenity=restaurant` and nothing here ever read the name; ร้านเสื้อผ้า is the first word of it. New `clothing` crawl group, **province-wide in both provinces against the house default** — a ring round the moat is the geometry that made WO-49's tailor shelf a register of the Night Bazaar the day before, and a size 47 is scarce and scattered by construction. **cm 106 + cr 42 elements → shelves 79/8/17 and 32/4/5, from one record between them.** `boutique` gave up on the CM run after six rests (Overpass 500), the group was correctly marked `incomplete`, and it was retried through `fetch_wide` and merged rather than left short. **TWO QUESTIONS, NEVER ONE VOICE** — the pest/snake rule, second subject: **a shirt can be MADE** (67 tailors, learned yesterday) and **a shoe cannot**, not at a price anyone pays for one pair, so the clothes page is a list of doors and the shoe page is a `gap: true` with a method, and folding them would let the fuller half hide how thin the other is. **THERE IS NO BIG-SIZE CATEGORY ANYWHERE** — not in OSM's tags, not on CMHY.city's **583-place apparel index** read whole for this order, so `read_bigsize_sites.py` scores every record for the words instead of filtering a category, and **exactly ONE of 583 says a big-size word on its own page**: ปุ้มปุ้ย บิ๊กไซส์ (สาขาคำเที่ยง), own tags เสื้อผ้าบิ๊กไซส์ + เสื้อผ้าสาวอวบอ้วน, own GPS, 081-169-2099 — and the Facebook trade surfaces the same shop independently. **THE GEOGRAPHY AND THE HOURS ARE THE MECHANISM**: the big-size women's trade is at **กาดหน้ามอ** and The Chiang Mai Complex and publishes **16:00–22:00 and 18:00–22:00** — a stall that opens at six in the evening is invisible to a daytime survey, which is why no map has it (third-party: Facebook served this fetcher a title line and nothing else, and it says so). **THE WORD ON THE LABEL IS NOT THE SIZE IN THE GARMENT**, proved by a Thai brand called **XLARGE** whose own chart stops at XL, whose denim stops at a 36-inch waist and whose socks are "ONE SIZE: US 7 ~ US 9"; **ฟรีไซส์ is a ceiling with a friendly name**, and the reply to it is *กี่นิ้ว*. **THE MOST USEFUL LINE ON THE CLOTHES PAGE IS COUNTER-INTUITIVE**: Uniqlo Thailand's XXL/3XL/4XL are an **online line, not stocked in branches** — walk into Central Festival and nothing passes XL — but **Click & Collect hands you the 4XL at that same branch**. The shop is right and the door is wrong. **THE SHOE ANSWER IS A NUMBER, NOT AN ADDRESS**: eight named shoe shops in the whole of Chiang Mai (three of them Bata, one a sandal stall) and about fifty brand counters on CMHY, and **not one advertises a size** — so **measure the foot in centimetres and say that**, because Mizuno Thailand and ไทยรัฐ (25 ก.ค. 2566) **agree exactly at 44 (28.0 cm) and 45 (29.0) and part company from 46 up**, half a centimetre being a full size, and the first table an ordinary search returns gives **44 = 24.6 cm — about a 39, three and a half sizes wrong** (printed, not used). The routes that do exist, in order: a **sports or outdoor** shop rather than a shoe shop (three Decathlons, Adidas, สปอร์ตแมกซ์, แสนทองสปอร์ต, APX, an Army Stores — which is why `sports-shop`, a shelf with one record and no selector behind it, is part of this order), *สั่งได้ไหม กี่วัน*, online, and made. **A NAME THAT READS WRONG IS NOT EVIDENCE**: nine records looked misfiled and **eight were checked against the element's own tags and only two retagged** — doi cycling studio really carries `clothes=sports;cycling_apparel`, Munee Hostel carries `clothes=women` with a 2026-02-08 `check_date`, and DECATHLON CHIANGMAI is a genuine café whose Thai name field holds the landmark 35 m away; the two with receipts are The Bigsize and "Motorbike & car rent 080-2464381" (`shop=outdoor`, and the name is the whole evidence). **A TRAP RECORDED**: **ไทยใหญ่ is Shan, not "big Thai"** — five shops sell ชุดไทยใหญ่ and a naive substring search for ใหญ่ files every one as a big-size shop; the reader scores whole words and gave them zero. **NO FACET** (a facet needs three places; there is one) and **NO big-size shelf invented** — a size claim made on a shop's behalf would be the one thing on the page nobody could check. **REFUSED**: a letter-to-letter conversion table (the most shareable thing available and the most likely to send somebody home with a shirt that does not fit), any ranking, softening **คนอ้วน** when quoting a shop that put it on its own sign, and publishing the Facebook/Instagram sellers as pinned records. **ATTEMPTED, PRINTED, NOT GUESSED**: facebook.com login-walled, uniqlo.com timed out twice, Pantip's replies load by script (the one line that came through is the poster's own — *รองเท้าหนังไซส์ใหญ่ หายากมากๆ* — and it is left as the question). All prices and every size range `_sizesVerified: false`; **the first lead is a walk of กาดหน้ามอ on an evening, and the second is five numbers — the biggest shoe on the shelf at Decathlon, Super Sport, Bata, Nike and Adidas — which turn the shoe page from a method into a list.** **CORRECTED THE SAME DAY, BY NAN** (*"with the number of kathoeys in CM, I thought it would be easier to find a large woman's going-out shoe"*) — and she was right: the shoe half was **asked in a man's numbers and answered in a man's shops**. เบอร์ 45–48 is a man's range; a large woman's going-out shoe is **41–45** and the word that finds it is **ส้นสูงไซส์ใหญ่**, big-size HIGH HEEL, not รองเท้าไซส์ใหญ่. Her inference is a demographic argument and it holds — CM has a large visible กะเทย/สาวสอง population and a working cabaret trade, so demand for a 42 in a heel is steady, and steady demand is supplied. Re-scored the 583-place corpus already on disk in the women's words and it answered immediately: **FIVE women's shoe shops standing side by side in ONE AISLE — โซนเครื่องแต่งกาย, ตลาดธานินทร์ — all tagged รองเท้าส้นสูง, all within 30 m, three with phones, two updated 2025-11-27, every one with its own published GPS**, plus รสริน on ถ.สันติธรรม: six records, `cm-curated-heels-*`. **NOT ONE was in the crawl** — a stall inside a covered market is not a `shop=shoes` node and never will be — which makes the first pass's headline number a plain error, now corrected on the page in its own note: **"eight named shoe shops in the whole of Chiang Mai" is true of OpenStreetMap and false about the city** (CMHY's รองเท้า category alone holds ~90). A count from a source that cannot see what you asked about is not a count. **None of the six publishes a size ceiling** (checked in each cached page), so they are a place to ASK — one sentence, ไซส์ใหญ่สุดเบอร์อะไร — and six counters in one walk is the honest shape of an answer. **THE TRADE NAMES ITS CUSTOMER**: a Thai retailer carrying women's 35–49 with heels to 8 in. writes *สำหรับผู้ที่เท้าอวบอูมหรือสาวสอง* on its own product pages, with a 40–46 foot chart and a size-up-one rule — the shoe is made and sold here in plain retail Thai; it is online, and a shoe is the one thing not to buy without standing up in it. **`gap: true` DROPPED** — the gap rule exists so a shareable poster never asserts an absence, and this page no longer asserts one; it has a list, a card and an aisle. `show: "phone"` dropped from both questions too: right for an exterminator, wrong for a shop you walk into, and it was silently hiding Uniqlo, H&M, American Eagle and two of the five Tanin stalls. **AND THE LEAD THAT OUTWEIGHS THE REST**: the answer is known precisely and cheaply by people this directory ALREADY HOLDS — **มูลนิธิเอ็มพลัส MPlus** (`cm-curated-mplus-chiangmai`, trans-health register, grade `stated`), **ศูนย์สุขภาพ แคร์แมท CAREMAT**, **มูลนิธิยังไพรด์ Young Pride Club**, and **Chiang Mai Cabaret Theatre** (`cm-osm-way-762611799`), whose performers need 42–45 in a heel every working night. One question, four contacts already on the site. **Asked as a question, never published as an assumption**: the register explicitly refuses to claim that the Tanin row carries a 43 or that it is where สาวสอง in Chiang Mai buy — neither is known, and a claim about a community's own shopping in this directory's voice on no evidence is the error the file exists to refuse. The answer belongs on the page in their words. Sixth sighting of the ขัดขี้ไคล lesson, and **the first time the wrong word was ours rather than the source's**. |
| WO-49 | ตัดเสื้อ — four trades, one English word: the tourist suit street, the uniform trade at the institution's gate, the ห้องเสื้อ that cut the gowns, and the 119 shops that mend | **BUILT** 2026-08-31, Nan's ask in three parts across one afternoon (*"do a mot dang enrichment on men' and women's tailoring, including uniform tailoring, in Chiang Mai and Chiang Rai. Deep dive, don't come back emptyhanded. **Good for tourists doesn't equal good for locals or expats--different needs and expectations, all valid**"*), then mid-build (*"where do the high ranking police officers get tailoring done, is a question I'm curious about....."*), then (*"Also high quality western and thai evening wear tailors. Probably not found on Loi Kroh road."*) — `notes/tailoring-2026-08-31.md`, `data/curated/tailor.json`. **MEASURED FIRST, and the shelf was worse than empty — it was WRONG.** Ten records under `sub=tailor` in Chiang Mai, **zero in the whole of Chiang Rai**; of the ten, **seven are farang suit shops inside 600 m of the Night Bazaar**, **one is a shoe-repair stall and one a bootmaker** (neither cuts cloth), and **exactly one** — รับซ่อมแซม เสื้อผ้า — is a Thai shop repairing clothes. The tailor shelf was a register of the tourist trade with two cobblers filed by mistake, and it answered none of Nan's three questions. The salon lesson and the notary lesson, third sighting: **KNOWN_EMPTY can be a fact about the search term, not about the city**. Read in Thai the city is not thin — CMHY.city carries **126** under ห้องเสื้อ-ตัดชุด, **119** under ร้านซ่อมผ้า-เครื่องแต่งกาย, **38** under ร้านเช่าชุด, **243 of 245 with their own published GPS**, 174 with a phone, **92 updated in 2025–2026**. **FOUR TRADES, NEVER ONE VOICE** — Nan's rule turned into structure, the `pest.json` two-voices rule generalised: a tourist wanting a suit before Friday, a police major wanting a ชุดปกติขาว that will pass inspection, a woman wanting a ชุดไทย for an ordination, and a long-stayer whose only trousers have split are not four grades of one customer; each strand carries its own words, prices and asks, and none is offered as an answer to another's question. **THE GEOGRAPHY IS THE FINDING**: the tourist trade is ONE STREET — 21 of 126 inside 600 m of the Night Bazaar, named Hong Kong, Boston, Europe International, James Bond, Tony, VIP, Vincent Bespoke, English trade names in Thai script, almost all one tag `#ตัดสูท` — while the uniform trade has NO street: 31 shops over ศรีภูมิ 8 · ช้างเผือก 6 · หายยา 6 · วัดเกต 4 · พระสิงห์ 3, clustering **around the institution they dress**, six of them on ถนนสนามกีฬา **38 m from the National Sports University**, cutting sports kit and embroidering school badges. Chiang Rai says the rule out loud in a shop's own name: **ร้านบอดี้โก๋ (หน้าค่ายฯ)** and ร้านโก๋ *ตรงข้ามประตูกลาง(ที่มีการขายผัก)*. **THE POLICE QUESTION, MEASURED RATHER THAN REPEATED**: the only reply on the one Pantip thread asking it is *แถวๆ ศาลากลาง* — measured against 31 shops' own coordinates, the median to the **new** government centre on Chotana is **5.3 km with 1 of 31 inside 2.5 km**, and to the **old** provincial hall at Three Kings **1.6 km with 22 of 31 inside 2 km**; the trade stayed when the offices moved, and the folk answer read the modern way sends a reader 5 km wrong. Chiang Mai is where the senior officers are and that is structural — **ตำรวจภูธรภาค 5** commands eight northern provinces including Chiang Rai from 311 ถนนมหิดล under a พล.ต.ท. — and **still no tailor sits at that gate**: nearest 1.9 km. Shops naming the work themselves: **เฟรนด์สูท** (`#ตัดชุดทหาร #ตัดชุดตำรวจ`, and its own page is *ร้านเฟรนด์ตัดสูทเช่าจักรยาน* — suits and bicycles), **นิวบอย** (`#ตัดชุดทุกเหล่าทับ`), and the real answer **เจ๊หล้าชุดและเครื่องหมายข้าราชการ** — *ชุด AND เครื่องหมาย* in its own shop name, because for a นายพล the cloth is the easy half and the **อินทรธนู · แพรแถบ · กระดุมครุฑ · ป้ายชื่อ** are the half that has to be right, normally a different shop entirely (CR: ร้านสตรองแมนโปลิศ, ณัฐพลเครื่องหมาย ติดสหกรณ์ออมทรัพย์ครู). **LIVE AND DATED**: RTP's own clarification of **19 มี.ค. 2569** — the draft กฎกระทรวง catalogues **60 uniforms (18 ordinary: ชาย 8 หญิง 10, + 42 special)** and *เครื่องแบบตำรวจที่เป็นสีกากีให้ใช้สีกากี สีผ้าพระราชทาน*; the colour-change reports were *ไม่เป็นความจริงแต่อย่างใด*; comments closed 3 เม.ย. 2569. **A draft is not in force**, and anyone about to spend 5,700 ฿ is owed both halves. **NAN'S THIRD ASK WAS RIGHT AND THE DATA AGREES**: the evening trade is not on Loi Kroh — it is in **ห้องเสื้อ** on residential streets: วรมน (มณีนพรัตน์), ภรณ์อำไพ (ราชวิถี), คุณแดงดีไซน์ (หนองหอย), สแกนดิ (ราชมรรคา); Thai formal at สุพัณณดา (cuts in **ไหมแก้ว** and sells the cloth), ห้องเสื้อชุลี (อารักษ์), ขวัญกัญจน์; and two traditions with their own tailors — **แสนหวี ตัดชุดไทยใหญ่** (Shan) and **แพรไหม** selling ชุดไตย *and Tai books at one counter*. Three nobody lists: **วีณา บราเซีย** takes **custom brassiere** orders (made-to-measure underwear barely exists as a listed trade and is the hardest thing to buy above Thai retail sizing), **โกแมว** dyes cloth any colour on Nimman 17, **บื๊กไซส์ชิกชิก** repairs and sells big sizes at one counter. **RENT OR CUT, THE FORK WITH NUMBERS** (`_pricesVerified: false` throughout, nothing walked): เดอะเกร็ท hires a white suit at **550 ฿** (ประกัน 1,000) and a ชุดข้าราชการ at **650 ฿** (1,500) against a bespoke ปกติขาว at **5,710 ฿** of which ~3,300 is the tailoring; ready-made khaki reported at **650 ฿** and **1,300 ฿ with cloth**; นำเทเลอร์ 1991 cuts a ชุดครุย from **9,000 ฿ on 60 working days** (Thai gowns 1,200–3,000, overseas 9,000–15,000) and hires CMU gowns. **38 rental houses in CM — a directory that lists only tailors tells a resident to buy the expensive answer.** **THE TWO ASKS CR CUSTOMERS EARNED**, turned into questions asked BEFORE the work and never into an accusation (the named shop is deliberately **not** listed): **ขอผ้าที่เหลือคืน** (4.50 m in, ~1 m used, 2 m back) and **ขอให้เขียนวันนัดลงในใบรับของ**; plus the move locals give first, in their own Kam Mueang — **ซื้อผ้างาม ๆ ไปหื้อร้านตัด หื้อร้านคิดเฉพาะค่าแรง**, with กาดหลวง as the cloth anchor (ผ้าเมืองฟอกนุ่ม · ผ้าหมักโคลน · ผ้าใยกัญชา · แพรพันวา). **BUILT**: `data/curated/tailor.json` (233 KB, 255 shop rows, every strand carrying its own sources and dates), **50 records into `additions-chiang-mai.json`** and **13 into `additions-chiang-rai.json`** — CR goes **0 → 13**, CM's tailor/alterations/fabric shelves **10 → 60** — plus facet set **`tailor` (14 facets: uniform · fulldresswhite · policeMilitary · insignia · schoolkit · sportskit · eveningwear · thaiformal · bridal · rental · repairs · copyGarment · englishSpoken · bigSizes)** over `tailor|alterations|fabric`. Importer green: cm 29 uniform · 16 eveningwear · 11 thaiformal · 4 fulldresswhite · 4 rental · 2 policeMilitary · 2 bridal · 2 repairs; cr all 13 carry theirs. **No shelf children added** — `tailor`, `alterations`, `fabric` already existed; the four-trade split belongs in facets, because the shelf says what kind of shop and the facet says whether it is worth walking to *that* one. **REFUSED AND WRITTEN DOWN**: no ranking and no "best tailor in Chiang Mai" — **every** English top-ten page found in this research was published by a tailor, one of them listing its competitors under its own brand; no efficacy claim in our voice; no complaint repeated against a named shop; **no pin the page cannot name** — all 13 CR records are `needs-pin` because Yellow Pages withholds the street and a tambon centroid is not a pin. **ATTEMPTED, PRINTED, NOT GUESSED**: **body-go.com now serves a reCAPTCHA wall where a shop used to be** (the Yellow Pages listing still stands, so the shop is not assumed closed — but its phone is a lead, not a fact); 23 Yellow Pages profile pages return 200 with the phone and street behind login/JS; TripAdvisor deliberately not mined (review aggregate would import a ranking through the back door); 2 of 245 CMHY fetches failed (ยาฮาดีไซน์, ฟรีสไตล์ 4x4, both repair). **DISCREPANCIES KEPT**: OSM files a bootmaker and a shoe-repair stall under `shop=tailor`, uncorrected upstream this pass and recorded so the count is not read as a count of tailors; the Pantip folk answer against the measurement; and three gown prices (300/day platform, 550–650 The Great, 9,000 bespoke) that are not contradictory but would mislead alone. **NO SILENT CAP**: **176 of the 245 CMHY shops have no place record yet** — they are all in the register as data with their own GPS, phone and directory-update date, and the register IS the work-list. **Doors, ranked**: 176 write-ups from data already on disk (zero network) · 13 CR pins from one afternoon's calls · one walked quotation turns 5,710 from published to ours · one call each settles `englishSpoken` and `copyGarment`, the two facets a long-stayer actually filters on · and whether ชุดไทยใหญ่ deserves its own line on the culture shelf rather than a facet. **Worker redeploy is Nan's** — until then the 14 new keys filter harmlessly, WO-27/38 arrangement |
| WO-48 | กำจัดปลวก และ งูเข้าบ้าน — the exterminator shelf a farang household needs and cannot phone for, and the free snake call beside it, kept in a separate voice | **BUILT** 2026-08-31, Nan's ask (*"Add motdang enrichment on exterminators. They don't speak english much, but everyone—including farangs—need them if they stay in cm long-term. Motdang should make it easy to reach/locate/and hire these services"*) and, mid-build, (*"can you also add a section on humane snake removal? Big thing around here"*) — `notes/asked-exterminator-2026-08-31.md`, `notes/asked-snake-in-the-house-2026-08-31.md`. **MEASURED FIRST and the ant had already been sent**: the `crafts` group asks Overpass for every named `craft=*` in both provinces and returns **102 elements in CM and 42 in CR — zero `craft=pest_control`, zero `shop=pest_control`**; the whole `home-services` category held **10 records, every one a landscaper** off `craft=gardener`. Not KNOWN_EMPTY-because-nobody-asked — the crawl ran, came back, and the trade is genuinely on Facebook, LINE and its own .co.th instead. The notary route, therefore: curated, one firm at a time. **The word is กำจัดปลวก, never "exterminator"** — every firm in two provinces names itself after the termite first and hangs rats, cockroaches, mosquitoes and bed bugs off it; the English word returns paid ads and the Thai word returns the trade with its price pages attached (ขัดขี้ไคล, fourth sighting). **11 records** (cm 8, cr 3), each read from its own page with the date on it: Unipest (CM head office + CR branch), GB Pest Control, Mini Bug ×2, Ikari, Green Nano Thai, Happy House, Mitrapap/MTP, Rentokil, Firesaver. **THE ONE CHECKABLE FACT, and no other directory carries it**: a firm spraying for hire holds permission for type-3 hazardous substances (or notified type 2) under พ.ร.บ.วัตถุอันตราย พ.ศ. 2535 and works under a **ผู้ควบคุมการใช้วัตถุอันตรายเพื่อใช้รับจ้าง** retrained every three years — and **อย. publishes public lookups for both the person and the premises**, so the register links the live tool rather than copying a table (the `wildlife.json` rule; the lists move). **Exactly one of eleven publishes its licence number** (Unipest, 83/2539). **Pricing is per LINEAR METRE of perimeter (LM), not floor area** — bait 400–700/LM, chemical injection 150–280/LM, pipework cheapest but only during construction — which is why two quotes for one house are not comparable until you know the number each was multiplied by; the page says ask for both halves. **Every price `_pricesVerified: false`**; only Happy House publishes one at all (3,900 first visit, from 6,900). **LINE first, phone second** — the reach answer to Nan's actual question: every firm keeps a LINE OA, and a photograph of the mud tubes beats a call in a language neither side shares; the register carries **9 Thai phone sentences** and the pest vocabulary with แมลงเม่า flagged as the sign to call rather than the thing to spray. **THE SNAKE HALF IS A SEPARATE VOICE BY RULE** — `pest.json`'s `_readme` forbids the merge (the toilets rule, second subject): `pest` is a trade you hire, `snake` is a **free** service you call on **199**, and folding them sells a householder a contract for a problem a state crew answers for nothing. The two touch at exactly one sentence, in both directions: **snakes follow rats**. Four numbers with their issuing agencies (199 · 1669 · **1367** Ramathibodi Poison Center, 24 h, public as well as doctors · **1362** พิทักษ์ป่า), six phone sentences ending in the one the page exists for — **ไม่ต้องฆ่านะ ขอให้เอาไปปล่อยได้ไหม** — while-you-wait do/don't, bitten do/don't (no tourniquet, no cutting, no ice), and the **14 protected snakes** with **งูเห่า deliberately noted as NOT among them**, because that is the argument: telling them apart at ten at night is not a householder's job. **Published as a candid `gap: true`** with the panel *คำตอบคือเบอร์โทร ไม่ใช่ที่อยู่ / the answer is a phone number, not an address* — pointing `find` at the 2 fire stations or at the hospitals was available and refused both times, and **the accepted cost is no share card** (the gap rule, kept rather than bent for a case that happens to be encouraging). **REFUSED AND WRITTEN DOWN**: an English directory lists a **snake farm** under snake removal on the same page that warns readers off snake shows because the animal is killed or displayed — both cannot be true, a name on a removal list is a recommendation, so it is not here and the page says why. **ATTEMPTED, PRINTED, NOT GUESSED**: rentokil.com 403 on both language paths (its record is `confidence: third-party` and says so in both languages), pca.fda.moph.go.th DNS-dead. **DISCREPANCY KEPT, NOT RESOLVED**: MTP publishes two different CM branch addresses on two of its own pages the same day, same phone — recorded, unpinned, and the blurb tells the reader to confirm on booking. **SIX OF ELEVEN LEFT `needs-pin`** rather than pinned: `geocode_local` reaches only postcode centroids for ต้นเปา, หนองผึ้ง, สันผักหวาน, หนองจ๊อม, ท่าสาย, บ้านดู่ — 3.3 to 12.5 km. A 12 km circle is not a pin. Three are pinned and say how (Chotana St 280 m · สันกลาง/สันกำแพง 592 m · ริมกก/เมืองเชียงราย 540 m). **No efficacy claim in our voice** — three firms make them (100% colony kill, herbal nano-particles, "proven safe by Thai health authorities") and all three are quoted as theirs. **No ranking**: `first` pins three for a stated reason written on the card — publishes a licence number / publishes a price / works in English. Shelf `home-services/pest-control` (กำจัดปลวก-แมลง-หนู) + teaser retuned; facet set `pest` (14 facets, **10 new worker FACET_KEYS**: `fdalicence termite rodent bedbug mosquito baitsystem pipesystem herbal warranty petsafe`), every `ask_th` a phone/LINE sentence because this trade has no door — `fdalicence` positive-only on the `hsscert` rule, `herbal` records that a firm *says* so, `petsafe` wants a number of hours not a reassurance. **`emergency.json` deliberately untouched** — its `_rule` is numbers-only, no triage, and 199 was already there. `test_asked` · `test_facets` · `test_publish_gate` green. **Doors, ranked**: eleven อย.-register lookups turn `fdalicence` from self-reported to measured (highest value) · one written quotation turns the LM ranges from published to walked · **one call to เทศบาลนครเชียงใหม่ 053-259000** turns "free" and "released" from reported to ours · ten calls settle `english` · six pins · whether CM has a named volunteer snake-catcher the way Phuket and Samui do (nothing found, and if one exists they enter by their own consent, the shibari rule). **Worker redeploy is Nan's** — until then the 10 new keys filter harmlessly, the WO-27/38 arrangement |
| WO-52 | หน้านี้ไม่ใช่ใบปลิว — the page is not a pamphlet: 33 blocks were 72% of every word on the site, and the CTA half of them had converted zero times | **BUILT** 2026-09-02, Nan's ask (*"a lot of shit that is printed on the page should actually be a tool tip at most"* → *"do the whole thing"* → *"be AGGRESSIVE"*). Gemba over all 22,920 built pages, then all four cuts taken. **Site prose 7,752,480 → 2,190,817 word-instances. Median place-page record 350 → 92 words. Words of repeated chrome between the name and the first fact: 132 → 0 (max 7).** Twelve CTAs that had returned literally nothing — `claims.json` 0, `toilet_reports.json` 0, `heard.jsonl` 0, and 10 of `fixes.json`'s 14 self-caught with the other 4 arriving from reddit and word of mouth — collapse to one link. The 55-word "this page is the record" paragraph (20,174 pp), the fix-log promise (22,052 pp), the Moo Deng footnote and the shoe-leather slogan (every page), three "no photo yet" captions (20,826 pp) and the photo ask (20,826 pp) are gone. **`mark()` + the stylesheet's first-ever `@media (hover:hover)`** gives the site the tap-sheet it never had — `<details>`, no JS, works on a thumb — and the notes worth keeping moved onto the marks they explain. Facet ledes moved from 8,000 place pages to the shelf above them. **`tests/test_page_weight.py` is the gate** (3 checks, HARD): nothing repeated above the first fact, median record ≤140 words, no long `title=` without a tap-sheet. All 37 suites PASS incl. publish gate + contrast; 2,500-page HTML nesting sweep clean. Deploy is Nan's. |
| WO-53 | หน้าแรกไม่ใช่ใบปลิว — the homepage was not in WO-52's count: one page never repeats, so it kept every blurb the place pages lost | **BUILT** 2026-09-02, Nan's ask (*"I still feel like 30-50% of the text could be cut. Did the page not fully update, or did you lack aggression?"* — the page had updated; the prune had never touched it). Her picks: weather for Chiang Mai, Chiang Rai and Réunion only (Saint Expédit's island); prose explainers gone (hero eyebrow, sub and orientation sentence; the route planner's lede, four bullets, moat note and coverage note; the map card's instruction; the newsletter's pitch; the claim band's paragraph; the Wikimedia note); blurbs gone (nine-doors sub-line and per-card line; after-dark eyebrow and per-card line); chipbar off the homepage and its two doors the svcbar lacked (My page, Add a place) added there; news ticker and Personalize panel deleted. The care shelf's register line and the events partner tip became `mark()` tap-sheets. Then her second pick, the duplicate events wall tile, dropped (carousel stays). **Homepage 4,397 → 3,136 words (−28%)**; the remaining bulk is widget data (weather, cinema, horoscope, katha), NOT picked. `min_rows` on weather.json 5 → 3. All 38 suites pass. |
| WO-54 | ถ่ายเอกสาร-แปลเอกสาร — the paper trades: copy shops at the gate of whichever office wants the copies, and the three counters a farang calls "document services" | **BUILT** 2026-09-04, Nan's ask ("deep dive and enrichment on copy shops and document preparation services. Use external sources if necessary"). **Measured first: the directory held ZERO copy shops in 20,700 records while the census on disk showed shop=copyshop 43 in CM and 12 in CR, craft=printer 1, office=visa 1, office=translation 1 — `shop=copyshop` had never been in any crawl group** (the WO-50 failure, sixth sighting); the one that slipped in was filed under repair/tech. New province-wide `paper` group (`crawl_overpass.py`, WIDE_GROUPS): **47 CM + 13 CR elements**, with `classify()` rules for copyshop/printing/translation/visa filed under `essentials` beside post and gov — where the reader stands when they need one. VFS Global (office=visa) and บ้านแปลภาษา (CR, office=translation) surface by their own tags. **Read in Thai: `importers/read_paper_sites.py` took CMHY.city's five paper categories whole — 522 places, 426 with GPS, 367 with a phone, 182 updated 2025–26** (one DNS blip cost 291 pages mid-run; snapshot-first re-read filled them). `importers/build_paper_register.py` → `data/curated/paper.json` (every row kept as the denominator) + **321 records into additions-chiang-mai.json (copyshop 130 · printing 187 · translation 4), 57 CMHY shops recognised as OSM doors within 80 m and NOT written twice** (dedupe is same-trade: a translation counter 60 m from a copy shop is a different shop), **144 refused and printed**: 82 with no published GPS, 58 photo studios (no photo shelf — 12 tag รูปติดบัตร, carried as the lead), 4 language schools filed by CMHY as translators. Two translation counters with first-hand sites but no directory pin ship `needs-pin` (Centa Care, Chiangmai Translation Service). **TWO VOICES (the pest/snake rule): a copy shop SELLS a copy, a translator or visa agent PREPARES a document** — three shelf children (`copyshop` ถ่ายเอกสาร-ปริ้นงาน · `printing` โรงพิมพ์-ป้าย · `translation` แปลเอกสาร-รับรอง), the `paper` facet set (10 new keys + english/open24/priceboard reused; worker FACET_KEYS), and two reader questions: `asked/copy-print` and `asked/document-prep`, the seal half linked to WO-40's notary page rather than restated. **The rule of where is in the shops' own names**: ลานนาก็อปปี้ *"ย้ายไป หน้าอาคารประกันสังคม"*, ดับเบิ้ลเอ *หน้าค่าย ป.พัน 7* — the trade stands at the gate of the office that wants the copies (WO-49's uniform-tailor rule again). **Facts read off their own pages, dated**: CM immigration's two doors — 71 M.3 Airport Rd (Mo–Fr 08:30–16:30) and **Central Festival 2nd floor, opened 2022-06-06** (Mo–Fr 09:00–17:00; OSM node 12619518873 IS that counter, now named/houred via enrich.json); **Promenada closed 2020-03-25** and half the English web still sends people there; **CR's city branch moved 2023-09-18 to Central Chiang Rai G floor beside the passport office** (own announcement) — no OSM record, so `cr-curated-immigration-central-chiangrai`; the TM.7 form's own text (4×6 cm photo) and Division 1's fee page (1,900 · re-entry 1,000/3,800), both 403 to WebFetch and read by curl/pdftotext; translation 350 ฿/page and an MFA RUN from 1,800 ฿/page (Centa Care's site) against the ministry's own 200 ฿ seal — the page says the run fee buys a queue-stander, not a seal; copies 1 ฿/page, 50 satang past 100 (a Santitham board via a 2025 review post; two shops are NAMED for their price, 35 สต. and 45 ส.ต.). All `_pricesVerified: false`. **Chiang Rai translation: every "แปลเอกสารเชียงราย" page found is a Bangkok firm working by post** — printed as the finding. Search: `paper` panel (21st) + 6 hand-thesaurus groups (written to `search-core/data/hand.thesaurus.json`, re-mined and synced: 2,819 groups, shelf terms 644), 4 cases in `tests/test_search.py`. **Refused**: no agent recommended, no ranking, no photo shelf invented, no visa rule beyond the form's own text. **Second pass, same day ("keep adding richness")**: the gate rule MEASURED — 64 of 157 CM copy shops within 150 m of a gov office/school/university/hospital (median 181 m) vs 119 of 516 7-Elevens (median 267 m), on the page as one sentence; **313 CMHY pages carry hours → 268 records gained an hours field with no network**; a lenient JSON-LD read recovered the 96 pages a JSON slip had hidden (523/523 GPS, 464 phones) — and its first version named 94 shops "ธุรกิจ" off the breadcrumb, caught by the tally, purged, regenerated; **`essentials/photo` shelf, 58 records, `idphoto` from the shops' own tags** (the 4×6 is made here); **nine translation/visa counters recovered with street+phone+GPS — Tha Phae/Inthawarorot is the one paper trade that clusters**, four counters on two streets; Modus (own site, needs-pin); photo sizes by country (TH/UK fetched, US refused and said so); reader sheet `paper-words` (10th). Records 321 → **456** (copyshop 174 · printing 215 · translation 8 · visa 1 · photo 58). Notes: `notes/asked-copy-print-2026-09-04.md`, `notes/asked-document-prep-2026-09-04.md`. |
| WO-51 | ไม้แกะสลักบ้านถวาย — the carving village 15 km south, the chain of six trades, the woods, and the fair that moves | **BUILT** 2026-08-31, Nan's ask ("a deep dive/enrichment on the woodcarvers' village (OTOP royal program) south of Chiang Mai"). **The measurement WO-10 filed as finding #1, now taken properly and printed: 82 records within 2.5 km of the Ban Tawai pin, 2 on a craft shelf, 0 whose name says carving — and the one record that names the village is filed `market/fresh`.** Against the province's own 2567 figure of 148 souvenir/OTOP outlets in Hang Dong, and the operators' own count to the Prime Minister on 7 Jun 2024: ~1,000 shops before COVID, ~500 after. Fixed the way Hub 53 was: `shelves.json` ADDS `shopping`/`crafts`, the market shelf and its URL survive, and it lands on the next `import_all` (not run here — WO-50's crawl was writing into `cache/overpass/`). **THE STEAK TRAP, third of its family after `(?<!ห)วัด` and `\bse-ed\b` and the first that is not confined to our code: `teak` case-insensitive returns 71 records, 58 of them steakhouses (steak *contains* teak), the other 13 cafes/resorts/a teak stand/วัดผาแตก romanised Pha Teak — wood shops among all 71: zero.** Page is a register, not a shelf: `data/curated/carve.json` (11 dated rows, 7 woods, 4 register honours, 20 sources, 3 printed refusals), `carve_layer.py` → `/tawai.html` + three inline-SVG instruments (the ground, the chain of hands, the timeline on true year scale). Spine is ผู้จัดการ's 2549 case study — a 3×4 m room at 10,000+ baht to an outsider and ~1,000 to a villager, a dragon at 800 on the canal and 3,000 on the frontage, the fair moved to suit the Night Safari — so the page states **where on the chain a reader is standing** and never who deserves to sell. Carry-flags NOT restated: `souvenir.html` holds them and `tests/test_tawai.py` fails if a Dalbergia/Aquilaria row here ever disagrees with `wildlife.json`. OTOP is **not** a royal project and the page says which three things are being confused (2544 Interior Ministry programme · the จามเทวี naming legend · SACIT's ครูช่างศิลปหัตถกรรม, held by นายยรรยงค์ คำยวง 2562). The fair runs on the FISCAL year — 34th 23–26 Jan 2568, 35th 26–28 Dec 2568, twice in one calendar year — and the gate fails if the editions list collapses to one month. **The section souvenir.html could not carry: a carved Buddha is not a carved elephant in law.** Its `finethings` row says handicraft is what the law leaves wide open — true of the elephant, false of the Buddha, which sits under พ.ร.บ.โบราณสถานฯ พ.ศ. 2504 (amended 2535): form **ศก.6** through สำนักพิพิธภัณฑสถานแห่งชาติ กรมศิลปากร, 2,000 baht/piece if judged Ayutthaya or older and 1,000 if later, 2 days in Bangkok and 5–7 upcountry, two colour photos per item, and **proof you own it** — which is what makes "can I have a receipt?" worth saying at the till. Source is DITP's own sheet, dated Sept 2560 on the page because a fee table with no edition reads as current forever. Souvenir.html now points back (`see_href` on the wildlife wood row + a guarded one-liner in `souvenir_layer.py`; a row without the field renders unchanged) — the chang/hom reciprocal contract. **`carve-words` reader sheet** (9th, `assets/reader/carve-words.pdf`, four blocks) published into the built site, third after hair-words and care-words, on the same argument: the person needing these words is on a footpath with a shopkeeper waiting, and two of them (พะยูง, พระพุทธรูป) change what may lawfully leave the country. `tawai` search panel (20th) with 4 cases added to `tests/test_search.py` incl. the `teak` trap query; llms.txt section; note `notes/tawai-woodcarving-2026-08-31.md`. **บ้านเหมืองกุง, the pottery village on the same road, has ZERO records — printed, not assumed.** Scratch build 22,748 pp; publish gate PASS (0 links to broken URLs, 0 /Users/ leaks); test_search PASS; test_tawai PASS. |
| WO-55 | กิจกรรมบำบัด — occupational therapy: the word no sign carries, the empty physio shelf found under it, the register read from the doors, /ot.html | **BUILT** 2026-09-04, Nan's ask (*"do a deep dive and enrichment on motdang for occupational therapy"*) — `notes/ot-2026-09-04.md`. **Census: 21,047 names, 0 say กิจกรรมบำบัด/occupational; 3 say physio; the medical tree's `physio` child matches NOTHING** (OSM holds no healthcare=physiotherapist in either province), so `/longcare.html` had linked to `cm/medical/physio/index.html`, a page never built — a 404 on a live page since 26 Aug, now re-pointed. `cache/care/` already held Nakornping stating งานกิจกรรมบำบัด at two doors with hours; the reads (cache/ot/, 50 fetches, verify-before-believe) added the CMU OT clinic at ศูนย์สุขภาพพร้อม (licensed OT stated, Mon–Fri 08–19), Maharaj's หน่วยกิจกรรมบำบัด (OPD20), ChivaCare, Kids Sense Play, and **Chiang Rai Prachanukroh's SMC กิจกรรมบำบัด after-hours clinic (Mon–Tue, Wed–Fri 16–20, Sat 08–16, ext 1112/1723) read off its own poster**. `data/curated/ot.json` = 14 graded rows (7 stated · 2 listed · 5 route) + 3 registers (สบส. licence name-check · OTAT, seated in CM at CMU's OT dept · the dept itself, the north's only OT school) + 8 unread with reasons (Kidsluck refused: Bangkok). `ot_layer.py` → /ot.html; `ot` panel + 3 thesaurus groups + 6 search cases (hotel guard); `ot` specialty key; care.json `ot` blocks on 4 hospitals; 4 additions; `importers/audit_ot.py`. Doors: fill the physio shelf from cmhy (≈20 clinics) · ring/write RICD + Suan Prung · merge CM Neuro's MOPH twin · special-schools pass · speech-therapy sister lens · an asked card. |
| WO-58 | ชั้นที่ไม่มีใครถาม — the shelves nobody had asked for: กายภาพบำบัด 0 → 20, ทันตกรรม +157, สัตวแพทย์ +165, ช่างซ่อม +354, ซักรีด +375 | **BUILT** 2026-09-04/05, Nan's go on the twenty follow-ups to WO-55 (*"please add all of these one by one"*). **One reader, one job, made a table:** `importers/cmhy.py` (the CMHY.city read as JOBS), `importers/cmhy_records.py` (same-shelf dedupe, record shape, upsert), `importers/build_trade_registers.py` (per-trade rules, every refusal written down). ~1,700 curated records added in a day. **Three rules were refusing real trades, and each refusal list read like a trade directory:** of 331 `mend` rows refused for 'no trade word', 31 said เปลี่ยนซิบ and 28 แก้ทรง (WO-49's alterations shelf), 14 อลูมิเนียม and 11 กระจก (repair/home, drawn at launch and never filled), 9 ซ่อมทีวี, 8 หุ้มเบาะ, and a knife-sharpening trade English has stopped having a word for; **ล้างแอร์ was refused for saying *wash* rather than *mend*** and is the most-called home trade in this city. Also mended: `craft=shoemaker` had sat on the TAILOR shelf since the first crawl. Seven new Overpass groups (funeral · bikes · laundry · mend · utilities · driving · optician). **The ส่งน้ำ trap:** the first utilities selector returned twenty-three irrigation canals (คลองส่งน้ำ, and the road beside one, and the Royal Irrigation Department's own office) — the teak/steak trap of WO-50, in Thai. |
| WO-60 | เลนส์ — the graded register made a layer: eleven new lenses on one renderer | **BUILT** 2026-09-04/05. care · trans-health · adhd · longcare · ot were the same page five times, so the shape is data now: `data/curated/lens/*.json` + `lens_layer.py` + `importers/sync_lens.py` (panel and thesaurus out to search) + `importers/audit_lens.py` (exit 1 on a register that would print a wrong page) + `importers/fetchlog.py` (verify-before-believe with a ledger). Eleven lenses: **speech · hearing · prosthetics · eyecare · vaccines · counselling · dementia · dialysis · stroke · specialed · mending**, every row graded stated/listed/route with its sentence, url and date. **Finds:** CMU's OT teaching clinic and its speech clinic; Chiang Rai Prachanukroh's after-hours SMC OT clinic read off its own poster; the Prostheses Foundation at Mae Rim; Suan Dok's ศูนย์โรคสมองภาคเหนือ; CM Neuro's memory clinic (Thursdays) and its geriatric clinic on the last **Sunday** of the month, the day a family can bring someone; the state travel-medicine clinic on Sri Don Chai opposite the Suriwong bookshop; **the optician shelf held ONE record against 85 `shop=optician` on the open map**; and twelve nursing homes the long-care register did not have, one stating Alzheimer's care in its own tags. |
| WO-61 | รับจ้างงานธุรกิจ — business process outsourcing | **BUILT** 2026-09-05, Nan's ask mid-run (*"can you enrich business process outsourcing?"*) — `notes/bpo-2026-09-05.md`. **Census: five names in 22,805 records**, two of them false positives (a hospital and a government audit office). The reason is the WO-9 naming custom one layer out: half this city's BPO is in Thai and calls itself สำนักงานบัญชี, never BPO; the other half is farang-facing and says 'outsourcing company' on a site no crawl reads. `/bpo.html` keeps three businesses apart — multilingual contact centre · accounting-payroll-visa back office · staffing. **CLBS on Mahidol Road states its own BOI promotion** and hires German, French, Spanish and Dutch speakers with visa, work permit and insurance: the nearest peer to the bpo-shop project and evidence the BOI route works for a Chiang Mai BPO. SANS states the whole back-office stack a new shop buys rather than builds. PRTR has no Chiang Mai office, and that is written into the register so nobody adds one from a search result. Registers a reader can check themselves: BOI · the DBD data warehouse (403 to a plain fetch — open it in a browser) · social security. No wages printed: nobody publishes one. |
| WO-62 | ใบขับขี่ · งานศพ · แว่นตา — the last of the twenty, and three tags that were lying | **BUILT** 2026-09-05. `/driving.html`: **Chiang Mai's two transport offices do different work** — licences at Mae Hia (192 ม.7, 053-277-156), motorcycle registration and drive-thru tax at Nong Hoi — and the queue must be booked a day ahead through DLT Smart Queue; a medical certificate must be under a month old; one school's own published prices (car 5,500 · motorcycle 1,000 · truck 6,000 · new-applicant training 500 · renewal 200), **read off a page still served in TIS-620**. `/funerals.html`: **155 of Chiang Rai's 156 `shop=funeral_directors` are village cremation grounds, not businesses** — believing the tag would have printed a city-essentials shelf claiming 156 funeral companies. The name now decides (สุสาน · ป่าช้า · ฌาปน · ณาปน · เมรุ → community/cremation, 278 grounds); the page gives the order of a Thai funeral, the itemised cost with **no figure invented**, and says a สุสาน here is a pyre, not a grave. **Three more tags had no rule at all:** `shop=optician` (the optometrist shelf held ONE record against 85 shops — Top Charoen alone has a dozen branches), `shop=musical_instrument` (all 23 music records were curated; the mapped shops were dropped), and `shop=fabric` + `antiques` + `jewelry` + four handicraft names from the `making` crawl (สยามศิลาดล, Baan Celadon, the Bo Sang sa-paper centre, WO-51's own carving-village centre). A crawl that runs and then drops its find is the same failure as a crawl that never runs, and harder to see. |
| WO-59 | โรคค้นหา — search disease: the unit of indexing is the NAME, the unit of demand is the NEED; four strains, the cure in eight phases, Phase 0 landed | **PHASE 0 BUILT + LIVE** 2026-09-05, Nan's BHAG (*"use Motdang to cure worldwide 'search disease' one city at a time, starting with Chiang Mai and Chiang Rai"*; the tok sen case: *"a tech debt issue, not a praxis issue"*) — diagnosis `notes/search-disease-2026-09-05.txt` (go/disease), plan `notes/search-disease-cure-plan-2026-09-05.txt` (go/cure), tally `notes/search-disease-status-2026-09-05.txt` (go/cure-status). **The measurement:** massage 302 records, 294 OSM, 21 Thai-named (7%); the whole province holds 16 OSM elements with นวด in the name against 337 in a Thai directory; ตอกเส้น in 24,216 records: 0. **The organism:** indexes hold what a thing is CALLED, never what it OFFERS, and the closer to a practice's epicentre the weaker the structured signal (the inverse-coverage law). Four strains: name · source · script · silence. **Phase 0 landed:** tok-sen 0 → 30 records (10 shelves.json tags + 20 additions incl. Phailin); the 73 name-rule records live on four shelves; `tests/test_facets.py` now FAILS on any zero child shelf without a written reason, on a child with no match rule, and on a KNOWN_EMPTY entry that has filled (four ruleless children got rules + read reasons); `tests/test_answer_shaped.py` asks the corpus the reader's question ("toksen in the old city, open past 21:00" → Lila Thai Massage) and passes; `tests/test_search.py` carries toksen and ตอกเส้น. **Live 18:10:** ai.motdang.net/api/search toksen 8 · ตอกเส้น 6 (both 0 that morning); index.json 76 tok-sen hits. **Open the same evening:** 3 KNOWN_EMPTY entries went stale within the day (chap-sen, cannabis/farm, cannabis/clinic) and the new test says so. **Phases 1–8 not started:** `data/curated/vocabulary.json` (one file → thesaurus, index_labels, MOTDANG_TAGS, coverage test) · Thai-native registers (thdata crawl was never persisted; CM massage still 8% Thai-named vs CR 100% off data.go.th) · `offers[]` + blurb (2,725 blurbs already held, none indexed) · hours/facets into the site index (4,398 hours held, none searchable) · one 50-question exam across three doors (GPT mine: 367 of Nan's own questions scored, 52 pass) · /coverage.html + the miss → work-item loop · Thai geocoder · Chiang Rai · CITY.md. **Forks, hers:** F1 zero-result counter · F2 geocoder · F3 Wongnai/GoWabi ToS · F4 offers evidence bar · F5 massage-first vs breadth · F6 AI answers → pages · F7 fold 1,070 cached OSM temples · F8 the pin cap · F9 three shelves the corpus already fills (pet-shop 64, northern cuisine 58, CR tourism kinds 228). Sibling work the same day: pins (go/pins, 287 applied, geocoder's three defects), the holding pen (go/held, 1,246 name-only records out of both indexes), the gap audit (go/gaps), the GPT mine (go/gptmine). |
| WO-56 | ปันนา = Punna — the condominium identity join: a resident's building held three times under two scripts and findable as neither | **BUILT** 2026-09-04, from Nan (*"friend uses motdang, says we don't have his condo on there"*) — `notes/condo-identity-2026-09-04.md`. **It was there three times**: two map footprints named only in Latin (Punna Residence, 55 m apart), five register rows named only in Thai (ปันนา เรสซิเดนซ์ 1 แอท นิมมาน …) with no pin, and nothing joining the halves — **185 of 353 mapped CM buildings carry no Thai name, while all 373 register rows are Thai-only**, so WO-27's exact-name join is blind by construction to every building whose two names are one word in two scripts. `loanword_candidates()` reads the register's Thai by RTGS and matches CONSONANT SKELETONS with the generic words stripped (ปันนา → Panna → `pn` = Punna), numbers compared separately and never assumed: **29 candidates** into `cache/condo_register_review_<prov>.txt`, merged by nobody. The floor is two consonants because Punna itself reduces to `pn`, and that is only safe because the Latin side is confined to the housing shelf — over the whole catalogue the same skeleton offered a temple for a condominium. **Six pairs settled by hand** (Ban Haw Kham · Pansook The Urban · Palm Springs Nimman Areca · The Star Hill · Mountain Front · Mountain View); **Punna deliberately NOT settled** — three footprints, five rows, no evidence which is 1. `settle_sub()`: a building the Treasury registers is an อาคารชุด under the Condominium Act B.E. 2522, so it files `condo` and the mapper's `apartment` comes off (7 re-filed, CM condo shelf 354 → 408). And the facts the site had held since WO-27 and printed on no page — **362 assessed spreads, 109 complex keys** — now render on the place page, the spread saying it is the transfer-fee basis and not a market price, the complex linking the sibling buildings (the only way a page tells One Plus Suan Dok 1 from the other ten). Open: the 27 candidates read once by a person. **Correction same day** (Nan: *"there's a lot of punnas in chiang mai"*): which footprint is which is NOT one question — **10 Punna records on the CM housing shelf**, 3 pinned and 7 register rows, across **4 tambon** and 3 product lines (Residence @ Nimman 1–2 · Oasis 1–2 at Wat Ket · 3/5/@หน้ามช by the university), so the pins cannot be assigned by elimination. **The name-family grouping is measured and NOT built — her fork**, written out in the note: every rule that groups all ten (consonant skeleton · one-edit chained · one-vowel) also merges words that differ only by a vowel because that is what they are (เพนนี Penny among the Punnas; chai with chao), and the only rule that never lies (exact romanized token) splits Punna 7 and 3. Recommended: exact token + a curated `name_families.json` of human-confirmed unions, same shape as merges.json. **She then asked "is this a holistic fix?" — it was not**, and the answer changed the build: measured across all 21,937 records, **every state register is Thai-only** (ONAB 2,084 · OBEC 1,302 · MOPH 490 · OPEC 168 at 100%; FDA 907 and condoreg 367 at 98%) against **58% of 14,851 OSM records Latin-only**, with **only 24% holding both scripts of their own name** — Punna is the shape of the whole catalogue. **So the fix went to the READING**: 20 building loanwords into `rtgs_lexicon.json` (ยูนีค was reading `Yu Nik`, ฮิลล์ไซด์ `Hinsai`, แฮปปี้ `Papi`) plus a new **`brand` section** — a name's own Latin spelling read off a record in this same catalogue, so ปันนา is Punna because three buildings here paint it that way; never an outside source, never a claim about ownership. With the readings right **no similarity test is needed**: 57 housing families on the exact token, 22 joining a register row to a mapped building, Punna's ten among them, and 242 pages now carry a Same-name row. `namejoin.py` is the shared vocabulary; `name_families.json` became the **refusal list** (30 kind/descriptor/place words — without it the shelf grouped 13 unrelated หอ N หญิง). **Then: "do the sweep everywhere"** — `importers/audit_readings.py` mines the 4,987 records that hold BOTH a Thai name and a human English one, keeping only pairs that share a consonant shape (a transliteration; กาแฟ→Coffee and เภสัช→Pharmacy are TRANSLATIONS and were left alone). **22 loanwords + 16 brand spellings**: วัตสัน `Wat San`→Watsons (**20 pharmacies, not one with an English name**), บู๊ทส์ `But`→Boots (13), ปตท `Patot`→PTT (42), กสิกร `Kasik`→Kasikorn (39), พีที→PT (37), บิ๊กซี→Big C (25), โลตัส→Lotus (23), ฟาสซิโน→Fascino (12), เทคโนโลยี→Technology (23 schools), คริสเตียน→Christian (13). Readings matching the sign **1,360→1,495 of 4,987 (27.3%→30.0%)**; **490 Thai-only records with no English name now carry the English word** (407 medical · 382 essentials · 36 housing · 9 schools). **The temple shelf answered differently**: wat readings are mostly right, and what is wrong there is Pali SEGMENTATION (วัดสุวรรณ→`Wat Suoraron`, วัดป่ายาง→`Wat Painga`) — named, NOT fixed. A BUG WORTH KEEPING: NFKD accent-folding ATE THAI (สระ อำ decomposes, the combining-mark filter dropped the nikhahit, เดอะยูนีค came back `yanik`) — fold accents on the Latin path only. |
| WO-57 | ภัยพิบัติ — the disaster layer: the site could not answer without a network, and could not say where to breathe or how high the river was | **ITEMS 1–6 BUILT** 2026-09-04, from Nan (*"motdang.net could potentially be a REAL asset in a local emergency or natural disaster... pre-stage useful and lifesaving resources, enrich what already exists"*, then *"let's work our way down the list"*) — `notes/WO-57 — ภัยพิบัติ — the disaster layer — PROPOSED 2026-09-04.txt`. **The gap counted first**: 23,434 pages and ZERO service workers, the four emergency numbers on ONE shelf, and 10 phone numbers across 593 state health facilities. (1) `chuai_layer.py` → **/chuai.html**, 2,227 lifeline rows baked inline (124 hospitals · 469 รพ.สต. · 1,030 pharmacies · 435 fuel · 169 mapped water points, 47 kB gzipped) with the nearest-thing search running on the device, plus **`sw.js`**: precaches the lifeline, serves navigations network-first, and falls back to /chuai.html so ANY address on the site, opened with no signal, lands on the numbers — verified by stopping the server and loading a page never visited. Kill switch: delete sw.js from the build. (2) the four numbers now render in the **footer of every page** — WO-52's own rule for a sentence true everywhere is "the footer once", and this is it; **1784** (สายด่วนสาธารณภัย, ปภ.) added to `emergency.json`, the one new number and the one thing here Nan should confirm. (3) `make_chuai_sheet.py` → **assets/chuai/chuai.pdf**, two sides of A4 reusing the handout rig; PCD bands carry a *stepped black bar* inside the colour because five colour fills photocopy to five identical greys; a ruled box for the numbers no directory can hold. (4) `importers/fetch_cleanrooms.py` + `foon_layer.py` → **/foon.html**: กรมอนามัย's clean-air register has a public API and holds **2,428 publicly accessible rooms with pins across both provinces** — a March 2026 newspaper said 45 in 13 of 25 districts, which is why the rule is read the register, not the article about it. **206 of its pins cannot be where the row says** (one row's latitude is 473027; 45 rows naming Mae Sai and Omkoi sit within 5 km of Tha Phae) and **458 rows carried a bulk-entry phone — one number on 428 rows at 246 separate sites**; both checks are tuned against a truth set, flag rather than delete, and are printed on the page. (5) `importers/make_ping.py` + `nam_layer.py` → **/nam.html**: the SRTM flood layer was REFUSED on its own numbers (z12, ~38 m a cell, ±5–10 m — a guess wearing a contour line) and replaced by something true: RID's hourly gauges, where **every row carries the station's own alert level** (P.1 Nawarat = 3.70 m), the river drawn in the order the water passes, and the Mae Tae → Nawarat lead time **measured** by cross-correlation (5 h, r=0.841, 736 hours over 30 days) instead of repeating the folk six-to-eight. No forecast, no advice; `tests/test_hazard.py` holds that line and can tell a forecast from a refusal to forecast. (6) `importers/enrich_from_cleanrooms.py` matched the register's phones onto the catalogue: **state health facilities went from 10 phones to 141**, refusing a match on a shared name, a bulk-entry number, or pins more than 5 km apart. New tests: `tests/test_chuai.py`, `tests/test_hazard.py`. `importers/watch_data.py` now watches ping.json (1 day) and cleanrooms.json (120 days). Open: which hospitals run a 24-hour ER (no source on this disk) · the 15 register names that are two facilities · the ~30 pins the amphoe check is too loose to catch · a second reader for the 1784 entry. |

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
same way the สบส. licence works on the massage shelf.

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
an eye. Nothing is merged automatically and nothing should be — the practice is
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

## WO-28 — the monastic schools and the universities · BUILT 2026-08-21

Nan's go 2026-08-21 ("let's do 1, 2"). Two fetches, both verified live first:
`68_113` (Open Data Common, สำนักงานจังหวัดเชียงใหม่) and MHESI's
`univ_uni_11_03`. Added to `harvest_datagoth.py`'s approved list; folded by
`import_opendata.py`.

**The last empty shelf on the school tree is filled, and it filled the way
the code predicted it would.** `school/monastic` sat in `test_facets.KNOWN_EMPTY`
with a written reason: OSM has no tag for a โรงเรียนพระปริยัติธรรม, and the
register that names them had not been fetched — "when it is, it joins through
รหัสวัด to the temples these schools sit inside, which is a thing no other
directory of either province can express."

That is now true. The register carries **วัด** — the temple each school stands
in — and **50 of its 56 rows matched a temple we hold. Four of those matches
are to `cm-onab-*` records that did not exist before Wednesday's ONAB fold.**
Landed: **27 monastic schools**, 13 pinned at their own temple, and
`apply_monastic()` writes the link back so the TEMPLE's page names the school
it hosts. Both halves render in `known_facts()` as ตั้งอยู่ในวัด and
โรงเรียนพระปริยัติธรรมในวัดนี้, each linking the other's page.

**A BORROWED PIN INHERITS THE LENDER'S ERROR BAR — caught before it shipped.**
The first cut stamped every temple-pinned school at ±150 m (a temple compound).
But วัดโขงขาว is itself placed by postcode centroid at **±12.5 km**, so its
school would have declared a twelve-kilometre guess as a hundred-and-fifty-metre
fact. The uncertainty is now `max(150, the temple's own)`; 150 m is the floor,
never the answer, and `watPinPrecision` records what kind of pin was borrowed.

**Universities (+7).** Name and province only — no address, no coordinates in
the register — so they land pinless and say so, the `import_opec` posture. The
gap they fill is real: both Buddhist universities (มจร วิทยาเขตเชียงใหม่, มจร
วิทยาลัยสงฆ์เชียงราย, มมร วิทยาเขตล้านนา), the national sports university's
Chiang Mai campus, วิทยาลัยเชียงราย. **The trap, caught:** the register files
"มหาวิทยาลัยรามคำแหง สาขาวิทยบริการฯ **จังหวัดแพร่**" under เชียงใหม่ — a row
whose NAME names another province is about that province whatever the column
says (the rule `import_citizeninfo` already keeps for addresses). It is
refused, with the reason, to the review file.

**A new gate, because nothing else could have caught this.** `tests/test_pins.py`
— a borrowed pin never claims to be surer than the record it was copied from;
an `exact` pin never names a `pinVia`, because a surveyed pin is derived from
nothing. Hard-fails on both. It also counts approx pins that state no error bar
at all — **12 of them, all hand-placed curated records** — and reports rather
than fails there: a person put those dots down on purpose, and restating
somebody's field truth as a number they did not choose would be the worse
error. Added to the standing walk as an advisory. Run against the pre-fix data
it caught all six violations; after the fix, PASS.

**The stale KNOWN_EMPTY came out with its receipt.** The README's own WO-22
lesson is that a written-down reason can stop being true and nothing checks it.
This one stopped being true today, so it was removed the same day, with a
comment saying what replaced it.

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
- Founding year is a fact and a sort key.
- **Accessibility is structural.** Sorts and facets are labelled buttons; drawn
  SVG carries text equivalents; the list under the map stays.
- **One build at a time** (`CLAUDE.md:24`). `ps aux | grep build.py` first.
- Source is served from `/source/`.
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


## WO-27 — อสังหาฯ-ที่พัก: the split, the words, the register, the farang door · ZERO-NETWORK BUILT 2026-08-21

Nan's ask, verbatim: *"I'm thinking if the farang SEO crowd is going to show ANY
interest in motdang, it's going to come thru the door of real estate. Real estate
on motdang is extremely underdeveloped. I might partner with someone like Laila,
who has a real estate side gig, or maybe perfect homes CM (although I don't think
our interests 100% align). Let's enrich deeply, while leaving room for
intestitial expansion."* Full note: `notes/realestate-proposal-2026-08-21.md`.

**The condo shelf was the barber shelf again.** Every named `building=apartments`
in both provinces — 316 of them — was filed as sub "condo" under a label reading
Condo Buildings. The buildings' own signs say condominium on **53**. The rest are
แมนชั่น, คอร์ท, อพาร์ตเมนต์ and หอพัก: the city's monthly housing, invisible to
the reader hunting a ห้องเช่า and misleading to the reader hunting a condo. The
split now lives in `classify()` itself (`realestate_sub()` — dorm, then condo,
then apartment as the tag's own default word), receipted in data/fixes.json.

**The farang door is a page, not a mechanic.** AGENTS.md's no-growth-mechanics
rule stands untouched: what was built is a bilingual board whose English half
actually answers the queries that arrive (condo · apartment · dormitory · the
per-unit electric rate · the quota question), plus two asked pages shaped like
the real long-tail. The same page serves the Thai monthly renter first — the
words are the deliverable, ค่าไฟหน่วยละเท่าไร above all.

**What the page does not carry.** No neighbourhood verdicts, no
farang-building/Thai-building sorting, no investment advice — and no statute
recited from memory: the foreign quota and the chanote transfer are given as
the QUESTION plus the office that answers it (นิติบุคคล · สำนักงานที่ดิน). Of
which the catalogue holds **zero** — printed on the page and in the audit every
run until the office=government door gets its go.

**The interstitial room** (note §4): sub slots named not stubbed (serviced ·
developer · property-management · juristic — an empty child is hidden, so the
note holds the shape); the 60 hotel-side monthly-worded venues counted every
build and re-shelved only one-by-one with receipts (the Hub 53 pattern); the
facet set as the owner-claim growth surface; listings kept OUT per the launch
rule — a partner's inventory would be marked ผู้สนับสนุน cards, never records,
and the register's readme fixes the foreign-quota shape (dated juristic
statement, never a facet) before the first row exists.

**ALL SIX RUNNABLE DOORS RUN 2026-08-21** — Nan's go: *"go ahead on
everything you can!"* Door 7 (TTD) stays shut, blocked on WO-17's key. Full
account in the note's postscript. What they were worth:

- **Door 1, the site reads — 6 read, 2 speak, one defect in my own reader.**
  Five domains no longer resolve, one refuses robots. Ping View (furnished ·
  lift · pool) and Smith Suites (furnished · pool) state services, each with
  the sentence it came from. **The catch: Life in Town's own domain now 302s
  into a Booking.com affiliate redirector**, and `first_hand()` was being
  checked BEFORE the redirects — so an OTA page passed as the building's own
  site and its silence would have shipped as the building's silence.
  `read_one()` re-checks the FINAL url now; row deleted and refetched. Same
  class as the beauty reader's scheme-less URL. `page_chars` added: a
  building that "states nothing" out of 56 characters was visited, not read.
- **Door 2, the Land Office — 0 → 4.** `office=government` had never been in
  any selector (`amenity=townhall` was the only government rule, and a Land
  Office is not a townhall): 165 CM + 108 CR offices onto `essentials/gov`,
  including สาขาสันทราย, สาขาเชียงดาว, กรมที่ดิน and CR's provincial office.
  The page names what is still missing — the open map holds two Chiang Mai
  branches but not the Mueang seat.
- **Door 3, the estates — 0 → 22, with 590 villages fenced OUT.** The door
  with something to lose: `landuse=residential["name"]` returns where people
  LIVE, and nearly all of it is villages wearing หมู่บ้าน. Only จัดสรร or a
  developer's name files (`audit_realestate.moobaan_hit`, one copy, borrowed
  by the importer like the elephant and spring fences); all 22 that passed
  are real developments (Supalai ×8, Pruksa ×4, Quality Houses, Perfect
  Place, กัลปพฤกษ์, one ที่ดินจัดสรร). The 590 sit in
  `cache/moobaan_review_<prov>.txt`. Shelf wired the same day it had records.
- **Door 4, dormitories — 22 → 84.** `building=dormitory` tags student
  housing on the building, not in the name. One selector, question closed.
- **Door 5, the agents — a closed question, not a yield.** The trade cannot
  be read first-hand: Perfect Homes answers **403**, RE/MAX's branch page
  renders client-side and returns **one character**, and every other search
  result is a PORTAL — somebody's listing OF an agency, not the agency
  speaking. No record was invented from a third-party directory. Five stays
  five, the page says why, and this door is Nan's relationships as described.
- **Door 6, data.go.th — one unusable, one that changes the page.** Both ids
  found, both in `data/sources.json` so neither is re-found hopefully.
  `land-valuation` is real, current, per-province and **UNUSABLE**: 41 MB,
  1,060,644 parcels keyed by cadastral map sheet + parcel number, no address,
  no coordinate, unjoinable without parcel geometry that is not open.
  `condominium-valuation` **is** joinable →
  `importers/harvest_condo_register.py` → **385 registered condominium
  buildings (366 CM, 19 CR)** with the Treasury's assessed value per m².
  Traps, both measured and both in the importer: the CSV is **cp874** (as
  UTF-8 a search for เชียงใหม่ returns ZERO rows rather than failing), and
  the north sits at the END of a 122,112-row national file, so any
  size-capped read (the shared harvester caps at 6 MB) returns no Chiang Mai
  at all. **The government counts 366 condominium buildings in Chiang Mai;
  this catalogue holds 53** — that gap is now a measured work-list on the
  page. Eight rows join a record by EXACT name; a substring join was tried
  and rejected (it put นครพิงค์คอนโดมิเนียม onto เพชรนครพิงค์, a different
  building, and folded two registers onto one บ้านสวน). Every line states
  that ราคาประเมิน is the transfer-fee basis, never a market price.

## WO-29 — ฉีดน้ำเลี้ยงข้อเข่า: the knee-injection question · PROPOSED 2026-08-21

Not Nan's own question this time — a stranger's, on Facebook: *"Who can provide
me with a knee viscosupplementation injection in Chiang Mai?"* She brought it to
the site and asked whether มดแดง could answer it. Full note:
`notes/knee-injection-proposal-2026-08-21.md`. Call sheet:
`notes/knee-call-sheet-2026-08-21.md`.

**It cannot, and the census says exactly how far short.** All 19,980 canonical
records, both provinces, zero network: **0** carry viscosupplementation ·
hyaluronan · osteoarthritis · ข้อเข่าเสื่อม · PRP · stem cell in any spelling.
**1** carries the word knee — วัดพระธาตุดอยสุเทพ, whose blurb mentions the climb.
**2** carry orthopaedics at all. The whole city's ortho supply, as this
catalogue holds it, is **three records**: Tanawat Clinic Orthopaedics (a mobile
number, no hours, no site), Clinic กระดูกและข้อ (a pin and nothing else), and
Chanakan Clinic (ortho by OSM tag, hours only, no phone). **One of the three can
be phoned.**

**The silence is the naming custom, not a mapping bug** — and this was tested,
not assumed. A widened `ortho` pattern (หมอกระดูก · ศัลยกรรมกระดูก · ข้อเข่า ·
เวชศาสตร์การกีฬา · sports medicine) run across all 19,980 records returns **zero
new records**. `importers/specialty.py` said why in its own docstring two orders
ago: a Thai clinic is named after its doctor, and a speciality is on the sign for
116 of 467 records with 72 of those dental. Five records in the corpus contain
กระดูก and three are food — ไก่ไร้กระดูก, ซุปกระดูก — which is why bare กระดูก
stays out of the pattern.

**Two fences already standing, recorded so nobody removes them.** `\bortho(?!dont)`
plus `OSM_SPECIALITY[orthodontics] → dental` means **M-Brace Orthodontic Clinic
is braces, not knees** and the specialty layer knows it: any knee selector
written by name-matching alone re-opens that hole. And `บุญบัวคลีนิค นวดจัดกระดูก`
(bone-setting massage, filed `thai-medicine`) must never be returned as an
answer to this question — it is a real thing, it is not this thing, and the
distinction belongs on the page in both languages.

**The rule, inherited whole from WO-25 because it was written for this: the desk
states, the register records, nobody advises.** No brand, no dosage, no whether
it works, no whether to have it, no ranking. New source type for the calls —
`{"type": "call", "ref": <number dialled>, "asked": …, "said": …, "fetched": …}` —
same discipline as every fetched page: a spoken claim is dated and attributed or
it does not exist. Absent stays silence, never a "no".

**Two decisions the build needs** (note §4): (1) a **register, not a facet** —
fold `services` blocks into the seven entries `care.json` already carries rather
than asking 2,038 medical records a question twelve can answer, feeding the
index the way `TRANSHEALTH_ROWS` does; (2) `_match()` in `asked_layer.py` tests
`attr` for truthiness, so `specialty: ["ortho"]` is unselectable — **one `spec`
clause** is the smallest honest fix, and the name-matching alternative both
misses Chanakan and re-opens the orthodontic hole. `show: "phone"` cannot carry
this card: it would render one row.

**Search measurement is OUTSTANDING** — `docs/data/index.json` was mid-rebuild
during the walk (two builds live, lock held 17:27), so the shipped block could
not be run. The probe is standing at `notes/knee-search-probe.py`, built on the same
extracted JS `tests/test_search.py` uses. Run it and paste the table into note
§2 before door 1.

**Doors awaiting Nan's numbered go** (note §5): 1. **the twelve calls** —
zero-network, one telephone, an afternoon, and the whole substance of this
order · 2. `read_care_sites.py` pointed at the seven verified hospitals' own
department pages plus Bangkok/Theppanya/Lanna/McCormick · 3. **Sriphat retried**
(CMU's private wing, on `care.json`'s `unread` list, likeliest holder of a named
orthopaedic clinic, one fetch) · 4. a wide `healthcare=*` re-pull to see whether
more speciality tags have landed since 2026-07-27 · 5. the pin, sign and number
for Clinic กระดูกและข้อ and for Chanakan — 1.5 km apart, one survey run · 6. TTD, pinned on
WO-17's key.

**If the calls come back empty, that is also publishable** — the census of the
silence, the way /beauty.html prints that 0 of 18,686 records name a house call.
A question closed is worth as much as a question answered.

---

## WO-30 — ใครเลี้ยงมด: the page that says a person makes this · BUILT 2026-08-21

*Numbered 30, not 29: another session minted WO-29 for the knee-injection
question the same day, and it was in the file first. Theirs stands.*

Nan's ask 2026-08-20: *"I want to start telling people 'you've heard of
motdang.net? then you've seen my work.'"* The recognition plan is
`notes/heard-of-it-proposal-2026-08-20.md`; this order closes the two gaps the
survey behind it found, and nothing else in the plan touches the codebase.

**The site had no author, anywhere, in 21,703 pages.** No about page, no
byline, no `meta name="author"`, no Person in any JSON-LD. `/brief` says it and
is `noindex` and written for an investor. So a stranger told "I make that site"
had no way to check, a machine summarising this corpus had nobody to credit —
and the sentence Nan wants to say had nothing on the site to land against.

`/who.html` — **ใครเลี้ยงมด · Who keeps the ants**. The institutional voice
stays: the register is the ants', not a CV. The ants do the walking; one person
feeds them. Four modules — who (named, with the config email, never a second
copy), how the ants walk (stdlib, static, the twenty-minute round, the source
downloadable from the site itself), and what happens when it is wrong (the city changes daily and
one person keeps this, so every fact is dated and the fix log is public). Then
`channels_block()`, which already existed and already names the accounts that
are NOT us — the thing that makes an impostor page expensive.

It is linked from the **footer on every page**, named in **llms.txt** as the
attribution for anyone summarising the corpus, and it is in the **sitemap**.
`/who` resolves too — the Worker already appends `.html`.

**The English half of the description was missing on every page that does not
pass its own.** `og:locale` is `th_TH` and the fallback was Thai with a short
English tail, so an English search result showed a snippet an English reader
could not read. Both halves are full sentences now, and `og:locale:alternate`
says the English exists.

**A LINK INSIDE `bi()` IS TWO LINKS.** The "read on" row was first written as
`bi("…<a href=…>…", "…<a href=…>…")`. `bi()` returns one lang-tagged span per
language, so that emits the anchor **twice**, once inside each — and it was the
only call in build.py shaped that way, which was the tell. Links go outside,
`bi()` carries the label: `<a href="…">{bi(th, en)}</a>`, the footer's own idiom.

## The nod ledger — `heard.py`, and why it is not part of the site

The plan is measured against conversations, not readers, so there was no
number anywhere that could answer *has anyone heard of this?*
`heard.py` is a numbered-menu CLI ([[user_accessibility]]): one keypress per
person Nan tells — **1** didn't know it · **2** knew the site · **3** knew it
was hers — plus an optional coarse room, appended to `data/heard.jsonl`.
`--report` prints the monthly rate against the plan's staged targets and which
rooms earn nods; `--undo` takes back a mis-keyed entry.

It counts **conversations Nan had, not readers**. It is a diary, not a tracker,
it never leaves the machine, and **no name of the other person is ever stored**
— a private log of who did not recognise her work is not a thing worth keeping.

**Fenced out of both publish paths, and checked rather than assumed.** `data/`
is copied into `docs/` by an explicit allowlist and `heard.jsonl` is not on it;
`SOURCE_TREES` carries `data/curated` and `data/canonical`, not `data/`. It is
named in `SOURCE_NEVER` anyway, so it stays out if `data/` is ever added as a
tree — the same belt-and-braces that comment already argues for `_incoming`.
Verified against the scratch build: 0 files under `docs/` mention it, and
`tar tzf` on the published archive returns 0 hits.

**Verification.** Scratch build (docs/ was held by another session, so
`build.DOCS` pointed at a scratch tree — the documented escape hatch):
**21,703 pages**. `test_publish_gate` PASS (7/7 essential, 0 links to the 325
known-broken URLs, 0 `/Users/` leaks, CNAME right), `test_alt_text` PASS
(21,706 files, 0 missing), `test_asked` PASS. who.html renders in both
languages with the live catalogue count (19,980 places) in its description.

**Not done, deliberately: `/who.html` does not link `/brief`.** The deck is
`noindex` and is an investor document with a candour slide on it. Putting it
one click from a public page aimed at readers is Nan's call, not a default.

---

## WO-38 — เซเว่นทุกซอย: the branch layer · ZERO-NETWORK BUILT 2026-08-27

Nan's ask: *"do a much deeper enrichment dive on 7-11's. They are so
individual and complex, we've barely scratched the surface!"* Full proposal
with every measurement: `notes/seven-proposal-2026-08-27.md`.

**The finding that shaped the order:** the hoped-for branch identity is not
in OSM. 270 of 456 cached seven elements carry `alt_name` and every single
one says `7-11`; hours are four spellings of 24/7; `operator` is three
spellings of the holding company. The สาขา names live with CP All (WO-18,
parked, robots/terms check first — this order neither opens nor duplicates
that door). So the depth came from four seams already on disk:

1. **The signs.** 58 records named 7-Eleven carried no brand tag → branded
   at import off their own signs (the WO-22 barber move), three fences
   witnessed in the cache and held in tests: the mapper's denial
   (`not:brand:wikidata`), the shelf fence (เซเว่น สตาร์ the condo), and the
   residue rule — "7-11 หลอด biers Bier Stube", the beer stall trading in
   7-Eleven livery, must never carry CP All's brand. 404 → **462 sevens**.
2. **The joins.** `atstation` ⛽ by the measured 80 m forecourt join (110
   branches), `card` 💳 unfiltered by finally declaring the key (13),
   `slurpee` 🥤 from the two stores that say so themselves. Worker keys
   added; **the worker redeploy is Nan's move**.
3. **The neighbours.** SEVEN_CTX: twins ≤ 150 m (dupes fenced at 25 m and
   printed for the merge list) and named anchors ≤ 120 m (601/726, median
   27 m) → the sevenband on every convenience page. Until WO-18 opens, a
   branch's name here is its neighbours, metres attached, method stated.
4. **The class voice.** /seven.html holds what any branch can do (bills,
   banking agent, parcels, the free microwave, the chiller's windows, the
   All Member question) at general-knowledge confidence, the toilets
   sentence reused verbatim, and the census/coverage counted live: **the
   median catalogue place stands 340 m from a seven; 2,693 places beyond
   5 km, said plainly** (34 doubled pairs; the note's postscript carries
   where the proposal's quick numbers moved and why).

**For Nan's eye, from the audit (`python3 importers/audit_convenience.py`):**
- 22 lotus-worded + 2 big-c-worded no-brand records — which era's brand
  string a sign carries (Tesco Lotus / Lotus's / go fresh) is a naming call,
  so they are printed, never regexed.
- 4 same-brand pairs under 25 m — one shop mapped twice, for the merge list.
- cr-osm-node-2148639746 is named เซเว่นอีเลฟเว่น in full Thai and filed as
  a **mall**; the sub fence rightly refuses to brand it, and it likely wants
  a retag receipt instead.

**Held calls (hers):** whether the 198 no-brand rows deserve a โชห่วย shelf
child of their own; a drawn twins map on the hub; the sevenband's reach
(currently convenience-only — pharmacies and fuel stations have the same
identical-records problem and the same machinery would serve).

**Doors not walked, each needing her word:** WO-18 (CP All locator — the
only source of real branch names + per-branch services); a fixtures
re-crawl (ATM/toilet points are 2026-07-27); an in-mall facet (2 basement
`level` tags are not enough to build on).

## WO-39 — ศาล-ศาลเจ้า-หลักเมือง: the shrines shelf, the register, the staged crawl · ZERO-NETWORK BUILT 2026-08-27

*Numbered 39: another session minted WO-38 for the 7-Eleven branch layer the
same day, and it was in notes/ first. Theirs stands.*

Nan's ask: *"a deep dive and enrichment for mot dang on spirit houses and
shrines around Chiang Mai and Chiang Rai."* The full measurement and rule are
`notes/shrines-proposal-2026-08-27.md`; the audit is
`importers/audit_shrines.py`, zero network, run it any time.

**The measurement in one line each:** the wat top shelf has been named
วัด-สิ่งศักดิ์สิทธิ์ since launch and no shrine has ever had a sub to stand
on; no crawl group ever asked `historic=wayside_shrine` or any
place_of_worship religion; thirteen real public shrines are in the catalogue
anyway (city pillars, founder-king shrines, two Chinese shrines out of town,
a devalaya), most under bare `wat`, findable only in the alphabet river;
ศาลเจ้าปุงเถ่ากง — the oldest Chinese shrine in Chiang Mai, in the
municipality's own telling — is absent from all 20,699 records; and the one
trace of the Mae Chan shrine is a pork-leg stall giving directions by it.

**Built on this order (zero network beyond five dated light reads):** the
`shrine` child under `wat` (ศาลเจ้า-ศาลหลักเมือง); shelves.json seats for the
found records, each sourced to the sign or the open list; the register
`data/shrines.json` (festivals genre — kind, recordId, rite tie, confidence
per row, sources with read dates, told-of names held in `unverified` and
never rendered); `/san.html` (shrine_layer.py — the drawn map, the register
by kind, the primer: ศาลพระภูมิ vs ศาลเจ้าที่, the ศาลเจ้า and their keepers,
หลักเมือง-อินทขีล-สะดือเมือง and the เสื้อเมือง idea, where a spirit house
retires — tradition's voice, promising nothing); thesaurus rings for
shrine/ศาลเจ้า/หลักเมือง/spirit house; the `shrines` crawl group STAGED with
its import fence hung (`shrines_hit`, rules one copy in the audit) and NOT
RUN — network crawls wait for Nan's word.

**The rule:** the keeper names the shrine; the calendar carries its source;
Public shrines only.
ever — the same refusal as stars.

**Doors left closed on purpose:** churches & mosques (their own order);
the venerated monuments question (ครูบาศรีวิชัย CR sits under `wat` today);
the trade shelf (11 `shop=religion` mapped, waits for the crawl); the wichaa
manuscript join (42 rite manuscripts — where they surface is Nan's call, no
dead links here); the ศาลเจ้าแม่จัน asked-card when a reader asks.

**Verification (same evening).** Full build under the lock: **22,169 pages**.
test_shrines PASS (21 register rows · 14 shelf records · page checked);
publish gate PASS (0 links to the 325 known-broken URLs, 0 `/Users/` leaks,
CNAME right); test_asked, test_alt_text, test_search, test_facets,
test_plan_routes all PASS. Both child shelves render 7 records each; the wat
shelf carries the 🏮 band; the svcbar carries the door; llms.txt tells bots
how to read the register and what never to rank. `make_shelf_cards` drew the
two new shelf cards (6 redrawn total). test_shelf_cards still FAILS on three
ORPHAN cards from an earlier shelf rename (`shelf-cr-learn`,
`shelf-cr-learn-gym`, `shelf-cr-transport-station`) — inherited, soft in the
walks, not this order's to delete while another session holds the rename.
The walk was rested (`cache/walk-rest`, timed) for the shared-file edits and
cleared on finish; shipping is the walk's job. One lead left on the table
deliberately: **Roi Dvarapala Ban Devalaya** (cm-osm-node-11513439400) sits
on community/clubs with a devalaya name — the review file will hold it when
the staged crawl runs, and its door needs a person before its shelf.

---

## WO-41 — สัญญาความสด: the freshness contract · PHASE 0 + 4d/4e 2026-08-28

The order's brief: stale-data display dies as a CLASS. Phase 0 (discovery,
no fixes) is reported in full in `notes/freshness-phase0-2026-08-28.md` —
the feed inventory, the real scheduling machinery and its outcomes, the
events pipeline's two distinct defects, the relative-string audit, and the
write-safety table. The four diagnosed symptoms all verified; the note also
records what the order re-specifies that already exists (watch_data.py is
the manifest's embryo and must be grown, not duplicated) and how the
order's GitHub-shaped frame maps onto this house (launchd + two walks +
the standing ledger; escalation to the task board, not to issues).

**Built same day, the order's own "ship today" pair (4d/4e):** the
Coming-up strip now selects by resolved date — announced instances until
their end, fixed-date festivals by the `day` their own window text states
(8 gained the field; the "usually the Nth weekend" fairs deliberately did
not), rolled forward past the date — with unresolved movables in their own
ช่วงนี้ของปี line, absolute server text, data-until on every row, and an
md.js load-time pruner so the strip stays true even if every walk stops.
`tests/test_freshness.py` holds it under a frozen clock.

### Phase 2 — BUILT 2026-08-28 (her go: "Go on Phase 2")

`importers/ingest.py` holds the five rules and every writer goes through it:
validate before write · atomic tmp+rename · never destructive on failure ·
sidecar meta always · quorum. What that bought, measured:

- **events.json 0 → 88, from the cache already on disk, zero network.** The
  harvester asks the registry what a source YIELDS; the school register is
  no longer handed to the events parser; the per-source net catches
  `Exception`, because isolation has to hold against the failure nobody
  predicted, and one wrong source now costs its own rows and nothing else's.
- **finance keeps its three sections apart** — a dead section keeps
  yesterday's numbers and says so in `stale_sections`; only an all-three
  failure is refused. The `{"generated": today}`-and-nothing-else file
  cannot happen again.
- **the sidecars** answer the question the site could not: not "how old is
  this file" but "when did this feed last SUCCEED, and how many runs has it
  failed since". That is what Phases 3, 4c and 6 read.
- `tests/test_ingest.py` — 17 checks, incl. the order's acceptance 4 and 5.

Sidecars are gitignored per-machine state; their stamps are in
`walk_fingerprint.VOLATILE_KEYS` so a meta rewrite cannot rebuild the site
every twenty minutes, while a feed that has STARTED FAILING still moves the
gate — which is right, because that is news the page should carry.

**Awaiting Nan's numbered go, in the order's own sequence:**
1. ~~Phase 2 — ingest hardening~~ **DONE above.**
2. Phase 1 — grow watch_data.py into the manifest (cadence kinds:
   continuous / business-day / scheduled-draw).
3. Phase 3 — the build gate acts on the manifest (degrade, fail, escalate
   to the task board).
4. Phase 4a–c — the baked-วันนี้ worklist (inventoried in the note) +
   validity-not-age chips (lottery reads "ผลงวด 16 ส.ค. · งวดต่อไป ~1 ก.ย.",
   the ~ per the house calendaring rule).
5. Phase 5 — an 18:00 ICT finance pass (the gold gap) + the heartbeat
   reading the standing ledger.
6. Phase 6 — /status + status.json from the manifest; open-now refuses
   red panels.

Also flagged in passing, not fixed: `make_ticker.py` is in no walk's
roster (dormant fetcher), and several fetcher User-Agent strings still
advertise the departed GitHub URL.

---

## WO-52 — หน้านี้ไม่ใช่ใบปลิว · the page is not a pamphlet · BUILT 2026-09-02

Nan's ask, 2026-09-02: *"a lot of shit that is printed on the page should
actually be a tool tip at most. Do a thorough gemba and come up with a plan of
action to heavily prune."*

### The gemba

Walked all 22,920 built pages in `docs/`, extracting every paragraph-level
block and counting how many pages carry each one.

- **33 distinct blocks account for 5,547,155 of the site's 7,752,480 prose
  word-instances — 71.6% of every word the site prints.**
- On a place page, **85% of the words inside `<main>` are blocks that appear on
  200+ other pages.** Sample of 400 place pages: 138,986 prose words, 117,889
  of them site-wide boilerplate.
- **Median place page: 350 words in `<main>`, of which 51 are about that
  place.** The floor: `cm/p/ban-hong-school-289210140.html` — 6 words of school
  inside 358 words of page.
- **Median 132 words of boilerplate stand between the H1 and the first
  place-specific block** (75th percentile: 204).
- Worked example, `cm/p/chang-puak-hospital-103540040.html`, a hospital: three
  facts on the page (open 24 h, open late, OSM as of 2026-07-27), wrapped in
  **fifteen** blocks of solicitation and self-description.

The five largest single blocks, by pages × words:

| pages | words | block |
|---|---|---|
| 20,174 | 55 | "This place keeps no website of its own — so this page is the record. Cite it, share it…" |
| 20,826 | 30 | "Have a photo of this place? Send it — your name goes under it." |
| 22,052 | 26 | "Reports here go somewhere: 14 fixes on the public log, dates and all" |
| 21,047 | 19 | "Some details on record — help fill in the rest, free." |
| 18,727 | 19 | "No photo of this place yet — this is where it stands" |

### The finding that decides it

**The CTA apparatus has never converted once through the page.**

- `data/claims.json` → **0 claims**, against "ยืนยันร้านของคุณ · Claim your
  place" printed on 20,174 pages.
- `data/toilet_reports.json` → **0 reports**.
- `data/heard.jsonl` → **0 lines**.
- `data/fixes.json` → 14 fixes, and the channels are their own answer: **10
  `มดเอง` (the ants' own audit), 3 reddit r/chiangmai, 1 word of mouth.**
  Reader-originated: 4, every one of them from OFF the site.
- `data/contact_leads.json` (99) is the ants' own harvest from a newsletter,
  not reader submissions. Unaffected by anything here.

So the sentence on 22,052 pages promising that reports go somewhere is
advertising a channel that has delivered nothing, while a channel nobody
advertises (reddit) delivered three quarters of the reader-reported fixes.

### The component that was never built

The site has no progressive-disclosure mechanism at all, which is why
everything is printed.

- `title=` attributes: **198,767 uses, 8.7 per page** — and `title=` does not
  open on touch. There is **not one `@media (hover: hover)` rule in
  `style.css`.**
- `<details>`: **314 uses across 22,920 pages** (0.01 per page).
- `<abbr>`, `popover`, `aria-describedby`: **zero**.
- `.facet{cursor:help}` (style.css:277) promises a tooltip a phone cannot
  open, and `README.md` describes reading a tag "before they open the tooltip"
  — a tooltip most readers have no way to open.
- The site then prints, on 1,256 pages, the sentence **"ชี้เมาส์ที่ป้ายเพื่อดู
  ว่ารู้มาจากไหน · Point at a tag to see where it came from"** — instructing a
  mouse gesture on a Thai-first, phone-first directory.

### Provenance check

Grepped CLAUDE.md, AGENTS.md, README.md and all 247 KB of MARCHING-ORDERS.md:
**no decision of Nan's puts any of these blocks on the place page.** They are
accretion — each work order added its own sentence, and nothing ever removed
one. Per this file's own rule, an addition with no provenance is a past
session's choice, not doctrine.

**No test asserts any of them.** Grepped all 36 files in `tests/` for the Thai
strings: zero hits. `test_sabai.py` checks `svcbar` grouping and
`test_festivals.py` / `test_tawai.py` use `note_th` on per-venue records — a
different, legitimate field. The prune is ungated.

### The four cuts

**Cut 1 — the CTA apparatus. 12 blocks, 1,816,399 word-instances, 23.4% of the
site, 0 conversions.**
Delete from the place page: the six `🐜 ช่วยเติม…` ant-asks (12,300 pages
between them), `บอกมดแดงว่าสาขานี้มีอะไร` (12,487), `มีข้อมูลบางส่วนแล้ว —
ช่วยเติมให้ครบได้ฟรี` (21,047), the photo-ask (20,826), the QR line
`สแกนแชร์หรือพกไว้หน้าร้าน` (21,048), the claim-box prose (20,174),
`รอปักหมุด` (2,099).
Replace all twelve with **one link at the foot of the record block** —
`🐜 เติมข้อมูล · Add what you know`. No sentence, no promise, no free-ness
claim. Every word explaining what happens moves to `add.html` / `claim.html`,
where the person who tapped is already asking the question those words answer.

**Cut 2 — the site talking about itself. 6 blocks, 2,131,267 word-instances,
27.5%.**
- "This place keeps no website of its own — so this page is the record" —
  true of 20,174 pages, therefore distinguishing nothing. **Delete.** If it
  must survive it is a JSON-LD statement for machines, not a paragraph for a
  person who came to find out when the clinic shuts.
- "Reports here go somewhere: 14 fixes…" (22,052 pp) — **delete.** The footer
  already carries `🛠 แจ้งปุ๊บ แก้ปั๊บ · Fix log` as a link. The sentence is a
  louder duplicate of a link that exists, and the number in it will age.
- The ant legend "🐜 = one ant per fact, nine when complete…" (1,719 pp, 67 w),
  the 😎 legend (1,592 pp), "Point at a tag…" (1,256 pp) — **move onto the mark
  itself** via Cut 4. A legend explaining a symbol belongs on the symbol.
- The Moo Deng disambiguation (every page) — **delete from the place page**,
  keep once on `/why.html`. Nobody on a hospital page is confusing the
  directory with a hippo.
- "Built from open data and shoe-leather" (every page) — **keep the date, drop
  the slogan.** `ปรับปรุง 2026-09-02` is the fact.

**Cut 3 — the category lede on the individual place page. 9 blocks, 779,371
word-instances, 10.1%.**
The 14 `note_th`/`note_en` blurbs in `data/facets.json` — "Two clinics on one
road are not the same clinic" (2,042 pp × 48 w), "Two schools on one road"
(2,970 × 59), the realestate set (774 × **214 w**), the beauty set (283 ×
**215 w**), massage (298 × 64), cannabis (694 × 42), convenience (726 × 33),
"the things people ask before they sit down" (4,504 × 43).
**Keep exactly one instance, on the shelf page**, where a reader choosing
between places is doing the comparison the sentence argues for. **Delete from
the place page**, where the choice is already made. This is a render-site
change, not a data change — the strings stay in `facets.json`.

**Cut 4 — build the disclosure component, then move the absence notices into
it. 6 blocks, 820,118 word-instances, 10.6%.**
Build one tap-sheet that works on touch and mouse with no JS — `<details>` /
`<button popovertarget>`, one `.mark` + `.marknote` CSS block, plus the
`@media (hover: hover)` rule `style.css` has never had. Then move in:
`ตำแหน่งโดยประมาณ` (3,053 pp), the three "no photo yet" variants (20,826),
`ยังไม่รู้ว่าสาขานี้มีอะไรบ้าง` (11,231), the road-from-addresses note (537),
the Wikidata-is-the-chain caveat (825), the archived-link note (353).
These are **true and worth keeping** — they are simply not worth a paragraph.
An absence is a mark on the thing that is absent.

### The gate

`tests/test_page_weight.py`, new, HARD:
1. No block appearing on >500 pages may sit inside `<main>` **above** the
   first place-specific block. (Today: 132 words of them, median.)
2. Median `<main>` prose on a place-page sample ≤ 120 words. (Today: 350.)
3. No `title=` carries text longer than 60 characters without a
   `.marknote` sibling — i.e. nothing important hides where a phone cannot
   reach it.

Without (1) and (2) this grows back, because that is exactly how it got here:
fifty-one work orders, each adding one reasonable sentence, and no test that
ever counted them.

### Expected outcome

| | now | after |
|---|---|---|
| median `<main>` prose, place page | 350 w | ~90 w |
| of which about that place | 51 w (15%) | 51 w (~57%) |
| chrome before the first fact | 132 w | 0 |
| site prose word-instances | 7.75 M | ~2.2 M |

### What could be lost, priced

- **SEO.** The "cite this page" text might be doing indexing work. Against: it
  is byte-identical on 20,174 pages, which is a duplicate-content signal rather
  than a ranking asset, and the unique text on those pages is currently
  outnumbered 6:1 by the identical text. Mitigation: cut one shelf first,
  watch, then proceed.
- **The claim funnel.** 0 claims means there is nothing to lose. If Nan reads
  the claim CTA as a long game, keep exactly one — the claim link — and delete
  the other eleven.
- **Owner outreach.** `contact_leads.json` came from a newsletter harvest, not
  the page. Untouched.
- **Tone.** The ant-voice warmth largely lives in these sentences. The reply:
  warmth that appears identically on 20,000 pages stops reading as warmth and
  starts reading as a template. Keep the voice in the places that are unique to
  a page — the facet notes, the "threads from here" line, the shelf ledes.

### What was built

Nan took the fork the same day: *"do the whole thing"*, then *"be AGGRESSIVE"*.
All four cuts, plus the component and the gate.

**The component that did not exist — `build.mark()` and `.mk` in CSS.** A
`<details>` tap-sheet: opens on tap, opens on Enter, needs no JS, degrades to
visible text with CSS off, and keeps `title=` on the summary so a pointer
still hovers. With it went **the first `@media (hover:hover)` rule this
stylesheet has ever had** — its absence is the whole reason 198,767 `title=`
attributes were written for a mouse on a phone-first Thai directory.
`.facet{cursor:help}` no longer promises what a thumb cannot open.

**Cut 1 — the asking.** `add_link()` replaces twelve doors: six `ช่วยเติม…`
ant-asks, `ant_panel`'s status line, `facet_door`, the photo ask, the three
`add_doors` cards, `door_ledger_line`'s promise and the claim sentence inside
`reach_block`. `ant_panel()`, `next_ant()` and `facet_door()` are deleted, not
merely unwired. One quiet line now closes the record: 🐜 เติมข้อมูล · Add what
you know. add_doors also came off the 1,004 road pages.

**Cut 2 — the site talking about itself.** Gone: the 55-word "this place keeps
no website of its own" (20,174 pp, the largest block on the site — the fact it
asserted is still in `place_json()` and the JSON-LD, where a citing tool
actually looks); "Reports here go somewhere: 14 fixes" (22,052 pp — the footer
already links the ledger, and the number in it aged); the 😎 legend (1,592 pp);
the 🐜 legend (1,719 pp, now the sort button's own note); the Moo Deng
disambiguation and "built from open data and shoe-leather" from every footer
(Moo Deng survives in `llms.txt`, which is who it was for); the QR caption
(21,048 pp — the alt text already says where the code goes).

**Cut 3 — the category lede, moved not deleted.** `facets.json`'s
`note_th`/`note_en` render once in `facet_chips()` on the shelf, where a reader
choosing between two clinics is doing the comparison the sentence argues for —
and no longer on the ~8,000 place pages under it, where the choice is made.

**Cut 4 — the absences.** Three "no photo yet" captions and the "we don't know
what this branch has" row are simply gone; a map looks like a map, an empty
row states its own emptiness, and the alt text still carries it for the reader
who cannot see the image. The four that are real claims about our own reach
became marks: approximate position (3,053 pp), the road not walked (537 pp),
the archived-website policy (353 pp), and the tag provenance — that last one
found by the gate, a **135-character note that had been sitting in `title=` on
every tagged page**, invisible to touch. It now lists, on the row's own 🏷
label, only the ways the tags on THAT page were earned.

**Also caught in passing, unrelated to the prune:** `<details class="hoingress">`
sat inside a `<p>` on /horoscope.html, so the browser was closing the paragraph
early and the styling below it applied to nothing. Fixed. A 2,500-page nesting
sweep now finds zero `<details>` inside a `<p>` or `<span>`.

### The gate — `tests/test_page_weight.py`

Three HARD checks, and the reason each exists:

1. **Nothing repeated stands between the name and the first fact.** Prose
   only: a `<dd>` reading "Doctors & Hospitals" repeats on thousands of pages
   and is still a fact about this one — repetition makes a value shared, not
   empty. A *paragraph* that reads the same on 500 others cannot be about this
   place. Cap 25 words; the site now sits at 0 median, 7 max.
2. **Median record prose ≤ 140 words.** It is 92.
3. **No `title=` over 100 characters without a tap-sheet.** 100 rather than 60
   because every note here is bilingual.

Without 1 and 2 this grows back, because that is exactly how it got here:
fifty-one work orders, each adding one reasonable sentence, and no test that
ever counted them.

### Where it landed

| | before | after |
|---|---|---|
| site-wide prose word-instances | 7,752,480 | **2,190,817** |
| median place-page record | 350 w | **92 w** |
| repeated chrome before the first fact | 132 w median | **0 w median, 7 max** |
| a place page on disk (Chang Puak Hospital) | 52,780 B | **48,319 B** |
| `@media (hover:hover)` rules in style.css | 0 | 1 |
| tap-sheets on a place page | 0 | ~0.6 average |

Verification: all **37** test suites pass, including `test_publish_gate.py`
and `test_contrast.py` (which caught `--mute` being used for a border — this
repo keeps the quiet inks text-only so they can be darkened without moving
structure; the mark's underline is `--gold`, the bead colour). Full build
22,920 pages. **DEPLOYED 2026-09-02 on Nan's say-so** — `publish/deploy.py
--yes` → r2://mot-dang-site → https://motdang.net/ , verified live (the six
deleted blocks return 0 hits on the deployed hospital page; `mark()` and the
hover query are in the shipped stylesheet). Tiles NOT pushed (`--tiles`, ~280
MB) — nothing here touched them.

### The one regression, caught after the first deploy

Cut 3 moved the facet ledes from the place pages to `facet_chips()` on the
shelf — but `facet_chips()` returned early when a shelf had no ticked chips
yet, so the lede went with it. Four sets — **massage, muay thai, chang,
realestate** — landed on NO page on the site. Realestate's is the 214-word one.

Found by checking where each of the 14 ledes actually rendered rather than
trusting that "moved" meant "arrived". Fixed: the lede is emitted whenever the
shelf has one facet set, chips or no chips. That is the right rule and not
merely the safe one — **a shelf with nothing ticked yet is exactly where a
reader most needs telling that two doors on one soi are not the same door.**

All 14 sets now land: convenience 12 · sitdown 65 · massage 8 · beauty 17 ·
cannabis 7 · medical 23 · muaythai 4 · cooking 15 · chang 6 · school 57 ·
realestate 8 · professional 2 · pest 2 · tailor 7.

**And the fix had a second bug under it, found the same way.** With the lede no
longer gated on chips, it appeared wherever `facet_chips()` found a single
facet set — but `len(sets) == 1` counts only the records that HAVE a set, so
ONE stray record decides a whole shelf. The laundry shelf holds one record with
`cat=massage`, so **ร้านซักรีด-สะดวกซัก · Laundry (59)** went live carrying
*"What comes off, what you lie on, who else is in the room, whether the price
is on a board outside."* It was harmless for as long as the lede rode on chips
that such a shelf never has, and it shipped the moment that gate came off.

Now a lede prints only where its set accounts for at least half the shelf
(`shelf_is_the_set`). Audited by printing every lede against its page's own
H1: all 14 land, every one on a shelf whose heading matches its subject, and
the laundry page carries none.

Lessons, both paid for on the live site:
1. **Verify the destination, not the departure.** On a move-not-delete, grep
   where the thing renders now and treat zero as failure.
2. **Removing a gate reveals what the gate was hiding.** `if not chips:
   return ""` was silently suppressing a wrong answer, not preventing one.
   Before deleting a guard, ask what has been sheltering behind it.

### Left standing on purpose

The 54 prose blocks still repeating on 500+ pages are the ones that should:
the provenance lines (`ข้อมูลจาก … · Data from … · <date>` — who said it and
when, which is the practice, not clutter), the one add link, and the section
headings. The sponsor block stays: it is revenue, and it is one line.

## WO-53 — หน้าแรกไม่ใช่ใบปลิว · the homepage is not a pamphlet either · BUILT 2026-09-02

Nan, 2026-09-02, after WO-52 went live: *"I still feel like 30-50% of the text
could be cut. Did the page not fully update, or did you lack aggression?"*

The page had updated — live was byte-identical to `docs/index.html`. WO-52
counted blocks by how many pages repeated them, and a homepage is one page, so
none of its prose ever entered the count. Scope miss, not a stale deploy.

### Her picks, and what each cost

| cut | where in build.py | words |
|---|---|---|
| weather to Chiang Mai · Chiang Rai · Réunion (Saint-Denis, `Indian/Reunion`) | `importers/make_weather.py` CITIES; default `md.wx` selection; `min_rows` 5 → 3 | ~120 |
| hero: eyebrow, sub, "no rankings" sentence, sticker gone; H1 + credit + Start-here link stay | `hero_html()` | ~90 |
| route planner: lede, four bullets, moat note, coverage note gone; H2, gif, three-row table, button stay | `plan_hero_html()` | ~200 |
| nine doors: sub-line and per-card blurb gone | `boards_html()` | ~150 |
| care shelf: register line → `mark()` tap-sheet | `care_shelf_html()` | ~25 |
| claim band: paragraph gone | `gold_band_html()` | ~50 |
| after dark: eyebrow and per-card line gone | `after_dark_html()` | ~40 |
| map card: instruction line gone | home assembly | ~20 |
| newsletter: pitch gone, form and privacy line stay (shared by every hub page) | `subscribe_block()` | ~40 |
| chipbar off the homepage only; My page + Add a place join the svcbar | `page(chipbar=)` | ~60 |
| news ticker + Personalize panel deleted; Wander stays | home assembly, md.js mods list | ~300 |
| events partner tip: hover bubble → `mark()` | home assembly | 0 (moved) |
| Wikimedia picture note gone (hero credit + footer already carry it) | home assembly | ~20 |

**4,397 → 3,418 words, −22%.** Shown the four widget cuts, she took ONE: the
"What is on" wall tile, printed a second time under the carousel, is skipped on
the homepage (`widget_wall(skip=("fortune", "events"))`; widgets.html keeps it).
**Now 3,136 words, −28%.** The rest — weather, cinema, horoscope, katha and
psalm — she declined by name. Not a fork any more; a decision.

### Rules it adds

- **One-page furniture is invisible to a repeat count.** WO-52's gemba
  measured the site by repetition; a page that exists once scored zero however
  fat it was. Measure the doorstep by absolute weight.
- **A removed block can have a second reader.** `tick_html` was built once and
  printed twice (home and my.html); deleting the builder broke the second
  page. `grep` every name before deleting its definition.
- **A guard sized to an old list is a bug waiting for a smaller list.**
  `ingest.write(min_rows=5)` refused the three-city weather.json and kept the
  fifteen-city one — silently, with a warning line. When a list shrinks,
  re-read every floor set against it.

## WO-54 — ถ่ายเอกสาร-แปลเอกสาร · the paper trades · BUILT 2026-09-04

Nan, 2026-09-04: *"Have motdang do a deep dive and enrichment on copy shops and
document preparation services. Use external sources if necessary. Don't be
verbose. Be effective."*

### What the measurement said

Zero copy shops in the directory; 43 + 12 on the open map, never asked for.
The same shape as WO-50 (shop=clothes) and WO-49 (shop=tailor): a shelf empty
because no selector had ever been written, not because the city lacked the
trade. CMHY.city, read in Thai, holds 522 places across five paper categories.

### Two voices

"Document preparation" is three counters — the immigration errand (do it
yourself; the shop at the gate copies and fills the form), the translation
counter (certified translation, sometimes an MFA run), and the seal (WO-40's
page). The register never offers one as the answer to another's question, and
the page says which line on the receipt is which.

### Rules it adds

- **A copy shop is at a gate, not in a quarter.** Two shops write the rule in
  their own names. Ask "where must the paper go" before "where is a copy shop".
- **Same door means same trade.** Deduping CMHY against OSM by distance alone
  swallowed a translation counter into a copy shop 60 m away; the match now
  requires the same trade family.
- **A network blip looks like an empty directory.** 291 of 523 CMHY pages
  failed on DNS mid-run with `!!` lines nobody read until the tally looked
  thin. `read_*_sites.py` readers print failures; the tally must be compared
  against the index count before it is believed.
- **A refusal is printed, never silent.** Every CMHY row is in the register
  with the reason it did or did not become a record.
- **A lenient parser needs the same tally check as a strict one.** The regex
  read that rescued 96 pages also named 94 shops after a breadcrumb.
- **Measure the rule you are about to print.** "At the gate" was two shop
  names until the distance table; now it is 41% vs 23% with a control.

### Open

Prices unwalked · lens shops and studios share the photo shelf until a door
survey splits them · CR copy shops carry no hours (Yellow Pages 403) · `shop=paint` node
4358880543 named ร้านถ่ายเอกสาร wants a shopfront read · deploy is Nan's.

## WO-63 — ผิวหนัง: the door a disease goes through · BUILT 2026-09-05

Nan's go: *"Use motdang to find providers who specialize in rosacea, then
improve all systems and processes that could lead to its discovery."*

### What the measurement said

`rosacea` / `โรซาเซีย`: 0 of 24,236 index entries, 0 results from the reader
assistant's place search, 0 reader questions in its log. `ผิวหนัง` on 14
records. "dermatologist chiang mai" at ai.motdang.net returned two dentists and
an osteopath at 0.51 — because `attrs.specialty` (importers/specialty.py, 13
records tagged `skin`) rode in search.html's index since WO-25 and NEVER in the
assistant's place text. The pattern is the search disease again: the disease is
on no sign, and the door it goes through — a dermatology clinic — was tagged on
the site but silent in the assistant.

### What was read, and who said what

Eight hospitals state a dermatology clinic on their own pages: Suan Dok's CMU
division (Tue/Thu/Fri mornings, floor 10 Sriphat building, UV room floor 12 —
the only state clinic in the north that prints its days), Sriphat (floor 5,
053-934733), Chiangmai Ram (its page draws the disease/aesthetic line in two
sentences), Bangkok Hospital CM (Bangkok Plaza floor 1, 08:00–16:30 daily),
Rajavej (skin disease four mornings; complexion every day), Chiangmai Hospital
(named among its special clinics), Kasemrad Sriburin and Overbrook in Chiang
Rai. McCormick's finder lists no dermatology department; Lanna returns 403;
DST's find-a-dermatologist answers with an empty body. Five aesthetic clinics
from the map sit in their own section, marked as the other door.

### Where it landed

- `data/curated/lens/skin.json` → `/skin.html`, 19 rows (8 stated · 9 listed ·
  2 route), 3 registers, 9 glossary words, 8 unread. Panel `skin` in
  search_panels.json; 8 thesaurus groups (rosacea, dermatologist, psoriasis,
  eczema, urticaria, vitiligo, melasma, phototherapy) into search-core's hand
  file, rolled out, parity OK.
- `build.py place_json`: the sidecar now carries `lens` {key, page, title,
  grade, for, words} — the same words the index gets.
- white-label-ai `scripts/index_motdang.py`: place text now carries `Treats:`
  from `attrs.specialty` and every register's words + page, placed AFTER the
  contact facts (Suan Dok's eight registers had filled the 1,500-char cap and
  cut its phone; cap now 2,000). `MOTDANG_DOCS` indexes a scratch build.
  Reindexed 2026-09-05: 3,806 + 111 places re-embedded. ai.motdang.net
  /api/search: "rosacea" 0 → 7 hits (Skin Centre, Ratika, Chiangmai Ram,
  Bangkok Hospital, Narada …); "dermatologist chiang mai" dentists → Chiangmai
  Ram 0.82, Bangkok Hospital 0.81, Rajavej 0.80. Two eval cases added.
- `lens_layer.rows_by_place` now keeps EVERY register a place is in (was one
  slot; the last lens in file order won, so Maharaj was the yellow-fever
  centre and lost its dermatology words). Sidecar field is `lenses`.
- `tests/test_search.py`: rosacea / โรซาเซีย / หมอผิวหนัง / dermatologist open
  the skin door and reach the stated hospitals.

### Rules it adds

- **A speciality the site knows is a speciality the assistant must know.** Any
  field build.py indexes for search.html has to reach the sidecar, because the
  sidecar is the assistant's whole knowledge of a place.
- **A disease no sign names is a page about the door, not the disease.** No
  rosacea claims were invented; the page says which counter treats skin
  disease and which treats complexion, in each hospital's own words.

### Open

Days and floor at Kasemrad Sriburin and Overbrook · Narada / Skin Centre /
Ratika / Dr. Vich own pages unread · Lanna, Theppanya, McCormick silent · DST
finder unreachable · no Chiang Mai price for a visit · site deploy is Nan's.

## WO-64 — ตรงนี้ · the site opening where the reader stands · BUILT 2026-09-06, staged

Nan 2026-09-06: *"if I open motdang.net standing in the old city, I'd
appreciate it if it actually just loaded up a map to where I am ... get
oriented, tell me what's nearby, navigate me, give me shareable information."*
Note for her: `notes/here-2026-09-06.txt` (go/here).

### Where it landed

- `here_layer.py` → `/here.html` + `here.js` + `here.css` + `data/here/<cell>.json`.
  One tap through MDLOC; then WHERE (inside the moat / which ย่าน / nearest gate
  with distance + compass word + arrow / GPS accuracy), NEARBY (every kind within
  ~1 km, nearest 3 each, pavement order, open/closed only where hours were
  posted), NAVIGATE (geo: link to the phone's own map app, plan.html?stops=,
  tel:, the dot follows the reader), SHARE (here.html#lat/lng built ONLY by a
  tap on a button that says the link carries a position; the map as a picture
  with ODbL in the pixels; every row is a place page).
- **Cells, not shelves:** the catalogue tiled into 0.01° cells; a phone fetches
  the 9 around it — 166 kB gzipped for the old city against 1.3 MB for
  cm-food.geojson alone. Opening-hour intervals ride inside each row, so "open
  now" never fetches open_lamps.json (683 kB).
- **The switch** `md-here` (a preference, never a coordinate): the page starts
  locating on open — only once the browser already says the permission is
  granted, so it can never raise the OS dialog.
- `tests/test_here.py`: no replaceState/pushState in here.js; localStorage holds
  the switch and nothing else; every fetch is to data/here/; JS and Python agree
  on cell keys (cross-checked in node); every pinned published place page is in
  exactly one cell; the 9 old-city cells stay under 320 kB gzipped.
- Built in an offline lane — a build by another session ran the whole time.
  **NOT in build.py yet:** the emit line, the homepage hop, and a nav chip.
  Exact snippets in the note §2. `hub=False` on purpose: the map is the first
  thing under the header.

### Rules it adds

- **A position is never written anywhere but the screen.** The one link that
  carries one is made by a tap on a button that says so. The test holds it.
- **A layer that draws INTO the basemap still goes through `MDMAP.ready`** — the
  third page to do so after /map.html and doi; no second constructor.

### Open

- Dots and the you-dot on the basemap unverified: the preview browser never
  created a WebGL canvas for any map on the site. Phone walk wanted.
- 75 catalogue records exist twice (same name, same pin, different ids, all
  `repair`) — probably today's cmhy / trade-lexicon import. The here list
  collapses them; nothing else does. Her call (note F5).
- Her forks F1–F4 in the note: hop policy, nav chip, radius, default kinds.

## WO-65 — ตอนนี้ · ใกล้ๆ · every page leads with NOW and NEAR · BUILT 2026-09-06, not built out to docs/

Beer (via Nan, 9/6): the most important thing on the site is what is
happening right now and what is nearby — events, weather, a place you
planned, a to-do. Everything else drawered, hidden or demoted. Nan: on
EVERY page, not only home. Note: notes/now-near-2026-09-06.txt (go/now-near).

Measured live 9/6: home is 128.5 kB / 168 links / 24 bands; events sit at
79 % of the page, weather at 50 %, six divination tiles above both; 24
events are dated today and none is above the fold. A place page carries 35
furniture links above its H1 (H1 at ~630 px); the svcbar has no slim rule.
_ev_strip is composed for the spare front page and never placed.

BUILT 2026-09-06 in an offline lane (the build lock was never free, so
nothing was run and docs/ was not touched; deploy is Nan's). Note:
notes/nownear-built-2026-09-06.txt. New file nownear_layer.py; six
anchored edits in build.py; two gates in tests/test_page_weight.py.

The header on every page is now masthead · search · one line · ☰ —
🎪 41 on today · 🌦 24° · PM2.5 17 ดี · 🗺 your plan (from localStorage,
hidden when empty), with the 8 chips and 27 svcbar links inside a closed
<details class="morenav">. The front page is that line, the name, three
event cards, the postcard map, the eight paths gptmine ranked, and five
closed folds holding everything that was there before — the finder (175
shelves) among them, because the card catalog is something you open.

Measured at 375 px: home 21,712 px → 2,789 px, 168 open links → 24;
place page 35 links above the H1 → 5, H1 630 px → 310 px. Opening every
fold restores 12,031 px and every link.

Still open: 📍 here (WO-64's hooks never landed, so /here.html is not on
the site; the cell is written and commented out), the place page's three
ways to wander, the n ≤ 3 search card, and forks F3, F4, F7–F10.
BUILD_DATE (build.py:80) reads 2026-09-05 on the 6th and the events cell
counts "today" from it — bump it before the next build.

The design: header = masthead · search · a NOW·NEAR strip (≤4 one-line
cells: 🌤 weather+air · 🎪 N on today · 🗺 your plan N stops · 📍 here) ·
one closed <details> holding the 8 chips and 27 svcbar links. Home
re-sorted: today's events, weather/air, plan+map, colour of the day, the
finder, then drawers. Place H1 from ~630 px to ~230 px. Snippets verbatim
in the note §3; a test for §3f goes in tests/test_page_weight.py.

Not built: build.py was hot all session (PID 92845 since 10:05). Forks
F1–F6 in the note are hers.

Nan, 9/6 afternoon — minimal, wanderable, desire paths (note §6): the
strip is one line of text; the finder goes behind ☰ (it is the card
catalog); a place page ends in three ways to wander — the 9 nearest
neighbours as text (neighbours_in already draws them), same kind nearby,
Take me somewhere. Paths are ALREADY logged first-party at
ask.motdang.net (white-label-ai D1: search_log 0006 — no seat id; site_gaps
0008 — candidate listings). Cloudflare fronts the site, so zone paths exist
without a beacon — her fork F7. search.html stays on-device (F10:
recommend no beacon). Weekly paths worklist to _incoming (F9).

## WO-70 — เวลา · the clock is the shop's, not the build's · BUILT 2026-09-07

Nan, 2026-09-07: "I want to add more temporal, interactive and live-navigation
features to motdang.net. What can we build with mostly what we already have?"

The survey answer was that most of it was already written and not reaching
anybody. Her calls the same day: build first and ship once at the end; the
📍 chip and NO homepage hop; the compass in, behind a tap.

### What was actually wrong

**BUILD_DATE is a stamp and it was being used as a clock.** A hand-typed string
at build.py:81, reading 2026-09-05 on the 7th. nownear_layer counted today's
events from it, so every one of 27,818 pages was printing **41 งานวันนี้ when
the day actually held 18** — not a rounding error, 2.3×, and wrong in the one
cell Beer's rule puts first.

**Two surfaces read the reader's clock instead of the shop's.** The WO-69
search lamp (build.py) and here.js's openState() both did
`new Date().getDay()`. Measured at one instant: a shop at week-minute 1410 in
Bangkok reads 1050 to a reader in London and 570 in Los Angeles — six and
fourteen hours out. /api/v1 has been right about the same place the whole
time, because publish/api.js:106 goes through Intl. The site disagreed with
its own API.

**The search lamp had never rendered at all.** docs/data/search_tables.json did
not exist in the built tree, so `hk` resolved to nothing on every card.

### What landed

1. **Today is the reader's.** `write_today_json()` bakes a 21-day window
   (602 bytes) and the strip picks its day with the `mdPick(doc).days[MD_TODAY]`
   pattern the sky and fortune tiles already used. `today_count` is unchanged
   and now called 21 times instead of once — one reading of a row, not two.
   Window exhausted → the cell goes quiet rather than lying. BUILD_DATE keeps
   the footer, the sitemap lastmod, the RSS date and the rotation salts, which
   are the jobs where a build stamp IS the fact.
2. **One reading of a schedule, in Bangkok time.** `mdWmin` / `mdOpen` /
   `mdEdge` / `mdWhen` in build.JS, published as `window.MDHOURS` so here.js
   and near.js stop growing their own. `null` never renders as shut — the
   contract build_open_lamps.py sets and tests/test_api_worker.js pins.
   `hourCycle:'h23'` because en-GB with hour12:false reports midnight as 24 on
   some engines: Bangkok Tue 00:00 must be 1440, not 2880. **publish/api.js:106
   wants the same eight characters — not touched here, the worker is a separate
   deploy.**
3. **The state between open and closed.** "ปิดใน 40 นาที" on search cards and
   here.html rows, inside the hour only: an edge nine hours out is the opening
   times, not news.
4. **/here.html wired.** here_layer.emit() after explore_layer (whose INKS it
   shares), an `i-pin` sprite, the chip in the ☰ drawer, and NOW·NEAR's 📍 cell
   uncommented — revealed only where the browser already reports geolocation as
   granted. No homepage hop: Nan's call. 3,368 cells, 174 kB gzipped for the
   old city against a 320 kB ceiling.
5. **The plan says whether you will still get in.** plan.html already routes on
   a real road graph with a 2-opt reorder and separate foot/scooter distances —
   that half was never missing. What was missing is time: place_json now carries
   `sched` (the week as intervals, beside the `hours` string it was parsed
   from), and each stop reads "ถึงประมาณ 14:20 — เปิดอยู่" or warns when arrival
   lands after closing. Travel time only, no invented dwell, so it says "about".
6. **The compass.** /here.html only, behind its own button, because iOS will
   not hand over orientation except from inside a tap. Refused, unsupported or
   silent, every arrow stays the static true bearing it already was. The
   heading is never stored, never written to a URL, never leaves the device.

### Bought on the way

**A DATA RACE LOOKS EXACTLY LIKE A BROKEN FILTER.** test_here failed at
"cells hold 23,943; catalogue has 25,243". Neither number was wrong: another
session rewrote data/canonical/*.json at 14:29:19, inside my build's
14:21:32–14:29:48. Re-running here_layer.rows() against the settled files gives
25,243 exactly. Checking the mtimes cost a minute; hunting the filter would
have cost an afternoon. The same afternoon, tests/test_nitnoy.py's determinism
check failed because data/open_lamps.json was stale from another session's
import — its own rerun fixed it. **Two "failures", zero defects, both found by
reading a timestamp before reading the code.**

**here_layer already dedupes on (province, slug)**, so the 75 duplicate
`repair` records were never going to double a nearby list. That fork stays open
for the records themselves; it was never a /here.html problem.

### Still Nan's

- publish/api.js:106 — the same `hourCycle:'h23'`, whenever the worker next
  deploys. Wrong only between 00:00 and 01:00 Bangkok, and only on some engines.
- Whether the 📍 cell should show for everyone rather than only where
  permission is already granted. It is a link, not a prompt; the conservative
  reading is shipped.
- The other surfaces MDHOURS could now light: place pages, shelf and hub rows,
  near.js. The helper is published and unused by them.
- WO-64's remaining forks are untouched: radius, default kinds, the runway and
  river lines, the 14 landmarks not on disk.

## WO-75 — ของเล่น · the toys, and the box that finds them · BUILT 2026-09-07, not built out

Nan, 2026-09-07: *"motdang.net should also be a place to download widgets and
apps. I'm not on the app store or play store. Maybe some other time idk. But I
have a ton of toys I'd like to make available for download (some paid). We keep
them on motdang.net, and we should be able to find them. But not a lot of
words. Maybe make it a category for the boolean search."*

Reader's note: `notes/toys-2026-09-07.txt` (go/toys). Register:
`data/curated/downloads.json` (go/toys-register).

**What was built.** `downloads_layer.py` → `/get.html`, plus
`docs/data/downloads.json` — the rows search.html adds to its own matcher.
Five toys on the shelf: the hongnam APK (already live at /app.html) and four
one-file HTML toys published from the repos that build them (lanna-almanac,
sam-ching, blinking-twelve, blinky-fidget). Nav chip beside Widgets.

**A toy is a row in the same ranked list, not a second search.** The rows
carry `u` (their own address) and `sh` (their shelf's) instead of a province
and a slug, and `c:["dl"]` — which makes `?cat=dl` a filter, "ของเล่น · Toys" a
group heading and a tappable chip, all from `_CATWORDS["dl"]`, with no new
machinery. `dl` is deliberately **not** in `CFG["categories"]`: that list
builds directories, counts and province pages, and a file is not a place.

**They are NOT in MD_IDX.** Everything that reads that array — the three
nearest, the plan, the map, the lucky button — assumes a place with a pin.
Four small guards in build.py's search JS took the rest: `rowHref()` uses `u`
when a row has one; a row with `u` gets no plan key and no panel; `spanProv`
skips rows with no province (counted in, one toy made every row in a one-city
result print "· เชียงใหม่"); the group heading takes `sh` where the shelf path
would otherwise be built from a province the row does not have.

**Three refusals, each a row not rendered, each printed in the build line by
id:** a toy naming nothing a reader can have; `price` with no `buy` (a baht
figure with nothing to tap); `draft: true`. Size, version and sha256 are read
off the bytes that ship — an .apk's version comes from the AndroidManifest.xml
beside it, never from the register, because a typed version goes stale under a
right fingerprint and that is worse than none.

**A one-file HTML toy is both.** It runs at its address on this site and it
saves to disk and still runs. So the primary button is Play and the size beside
it is the keeping — offering only the download would have been the worse half
as the only half.

**`get/` is out of three site-wide checks** (test_alt_text, test_chuai,
test_publish_gate) and out of sitemap.xml. The files in it are the toys
themselves, published byte-for-byte; making somebody's game pass this site's
page checks would mean editing the game. In exchange the layer counts images
with no alt text in each hosted toy and prints it in the build line — the fix
is then a change in the toy's own repo, which is where it belongs. Tonight: none.

**Verified against a real build (22:14).** The layer ran inside a full build:
`/get.html`, five files in `docs/get/`, `docs/data/downloads.json`.
`tests/test_downloads.py` all green. `tests/test_search.py` 40/42 — the two
failures (`'zzzzqqq'` matches 16 rows instead of nothing; `'kow soi'` loosens to
343) are the Overture fold, proved by re-running the identical suite with the
five toy rows emptied to `[]`: same two failures, same counts, same example
row. Handed to the fold's session in DO-NOT-DEPLOY-2026-09-07.txt. Builds ran
back-to-back all evening, so the suite runs against a `cp -R docs/data` snapshot
under `MD_DOCS` — otherwise the next build wipes docs/ mid-test.

### Still Nan's

- **The rail for the paid ones.** Ko-fi shop (no code, file lives off-site) /
  Gumroad–Lemon Squeezy (~5–10%, merchant of record) / Stripe link + a Worker
  minting a signed R2 URL (~3.65% + ฿11, file never leaves motdang.net, the
  customer email is yours). Costed in the note. Nothing waits on it: `buy` is
  any URL and the shelf ships free toys today.
- **Which toys go on the shelf.** Five are there because five could be verified
  in one night. The rest of the fleet — coucal faces, moat, poplucky, skipdjt,
  the taoist oracle, the jovilabe, thairoots, telltale — is a list, not a
  judgement, and adding one is one object in the register.
- Whether /get.html earns a door on the homepage or in the empty-search pills.
  It has the nav chip and the search; neither of those was a decision to make
  it small.
