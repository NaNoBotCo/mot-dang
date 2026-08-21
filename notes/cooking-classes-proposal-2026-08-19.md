# เรียนทำอาหารไทย — the class board, the shelf, the primer: making Mot Dang deep where it was scattered

*2026-08-19. Nan: "similar to muay thai on mot dang, enrich Thai cooking
classes (all kinds)." This note is the measurement, the rule the shelf runs
on, and what was built the same day under WO-14. Read with `MARCHING-ORDERS.md`
WO-14; the reasoning is here and is not repeated there. The muay thai note
(`notes/muay-thai-proposal-2026-08-19.md`) is the template this follows.*

## The measurement, before any proposal

Thai cooking classes lived on this site as **twenty-five records on seven
shelves, split by how a mapper tagged the door**, and nothing else.

| What a reader asks | What the site held on 2026-08-19 afternoon |
|---|---|
| Where can I take a Thai cooking class? | **Nine** records on `school/cooking`, found by NAME — the OpenStreetMap tag for a cooking school, `amenity=cooking_school`, is on **zero** elements in both provinces (census 2026-08-07) and the schools crawl group does not ask for it. **Nine more** sat among the restaurants on `food/thai` (Siam Garden Cooking School, Zabb-E-Lee Thai Cooking School, Thai Akha Cooking School, Pantawan Cooking, Cooking Love ×2, Chang cooking…), **two** on `food/vegetarian` (May Kaidee), **three** on `school/training` (Cooking@home, Sammy's Organic Thai Cooking, Smart Cook), **one** on `school/music-art` (Gap's Thai CULINARY ART School — the "art school" rule fired first) and **one** on `repair/auto` (Siam Rice — Thai cookery school). 3 of 25 contactable. |
| Which kind — on a farm, at somebody's home, vegan, Northern, a dessert class, carving, a hotel studio, a course for a trade? | No axis at all. One child, `cooking`, under the schools shelf. |
| When do the classes run, what do they cost, will they fetch me? | Nothing. No record carried a session, a price or a pickup radius. |
| Is it on the calendar? | Nothing. Not even กินเจ, the nine days when every vegan kitchen in town is the story. |
| What am I looking at when the pestle comes out? | Nothing. No primer, no words, no reader sheet. |
| Chiang Rai? | **Zero** records. Not one, by name or by tag. |

So "all kinds" is not an enrichment of a thin shelf: it is an axis (what kind
of class), a board (when, what posted price, who fetches you), a calendar
day, a primer, a sheet, and a second province — and the one shelf that existed
was a single child whose name rule missed half the town.

## The rule this shelf runs on

Massage's rule was *never infer respectability*. Muay thai's was *the venue
states its own nights, or the page says nobody has*. Cooking's is the same
rule at a stove:

**The school states its own sessions, its own prices, its own pickup radius —
or the page says nobody has stated them. And no sorting of kitchens into
tourist and real, school and activity.** A farm class in San Sai with a
minivan and a twelve-seat kitchen on Rachadamnoen Soi 5 are both cooking
schools; the menu is the menu. "Which one is authentic" is a tourist question
this site does not answer (`feedback_no_tourist_framing`). What it answers is
*which days, from when, posted at how much, by whose word, seen on what date,
and what kind of class it calls itself*.

Four consequences, all in the data shape:

- `data/curated/cooking_classes.json` carries `sessions` ONLY as the school
  itself states them (`stated_by: "venue…"`, `source`, `fetched`); `days`
  holds BYDAY codes only when the school states weekdays ("closed Sundays",
  "open daily", "365 days") and is **null when it does not — null means NOT
  STATED, never closed**. The board renders a null-days school in grey across
  all seven columns and the legend says why.
- Prices carry `_pricesVerified: false` until somebody reads the board at the
  door, exactly as the stadiums and the reader sheets do. A price read off the
  school's own site is still "posted", never "costs".
- The audit (`importers/audit_cooking.py`) reads NAMES and the crawl's own
  sub, and nothing else. Its guards are the กระท่อม discipline again: บ้าน is
  never a rule (it opens thousands of business names — BaanThai Cookery School
  is a school, not a home kitchen); bare เจ is never a rule (เจ๊, เจริญ, เจดีย์);
  a name that says only *Cook* (Smart Cook, Cook with Love) is a LEAD for a
  person, not a proposal; wood carving is carving and not cooking, so every
  kind-child is claimed only on a record that is already a class.
- **Nothing on the board becomes an event.** A class that runs every morning
  is a booking, not a happening, and ten daily "events" would bury the real
  ones on /events.html. The board lives on its page and on each school's own
  record (the `known_facts` rows) — a deliberate departure from the fight
  board, stated in `build.py` where the muay layer is merged.

## What was built (2026-08-19), pillar by pillar

### Locations — the shelf

- **Tree, additive:** new top-level cat `cooking` (เรียนทำอาหารไทย · Thai
  Cooking Classes) with nine children — `class` โรงเรียนสอนทำอาหารไทย · `farm`
  คลาสในสวน-ฟาร์มออร์แกนิก · `home` เรียนที่บ้านครู · `vegan` อาหารเจ-มังสวิรัติ-วีแกน ·
  `northern` อาหารเหนือ-ล้านนา-อาข่า-ไทใหญ่ · `dessert` ขนมไทย · `carving`
  แกะสลักผักผลไม้ · `hotel` คลาสในโรงแรม-รีสอร์ต · `vocational`
  หลักสูตรอาชีพ-สารพัดช่าง-อาชีวะ. Nine, because a number that is arbitrary is
  made nine here. `school/cooking` and `food/thai` keep every record and every
  URL; a record reaches the new shelf by gaining a SECOND cat through
  `data/curated/shelves.json` — WO-10's move, WO-12's again. Icon `i-khrok`
  (the mortar and pestle) drawn into the sprite; schema.org `School`; the
  shelf header's art topic is the market pictures, because every class starts
  at a stall.
- **Audit → shelves.json:** `audit_cooking.py --emit` proposed 22 entries,
  every one `osm name: …` or `osm sub: cooking`. Applied, plus three hand
  entries from the schools' own pages read the same day: May Kaidee's
  `dessert` (its own course list names a Thai Desserts course), Asia Scenic's
  `farm` + `carving` (its own course pages), Four Seasons Resort's `hotel`
  (the Rim Tai Kitchen page, read in a browser because the site refuses
  non-browser fetches).
- **Classifier fix:** `culinary (?:school|academy)` missed "Culinary Art
  School"; it is now `culinary (?:arts? )?(?:school|academy|institute)`, and
  `amenity=cooking_school` is mapped in `SCHOOL_TAG_SUB` so the day a mapper
  uses the tag the record lands right — the crawl selector itself is a network
  change and waits on Nan's go.
- **Two merges** in `merges.json`, each a person's look: the Thai Secret
  node and way at 58 Moo 1 T. Pa Phai (the way keeps, the node's website folds
  in); the two Thai Kitchen Cookery Centre nodes eleven metres apart on Loi
  Kroh Soi 1 (the one spelt "Kirtchen" folds in).
- **Four curated schools** — Mama Noi and Grandma's Home (CM), Suwannee and
  Akha Kitchen (CR) — each from its own site, dated, each `needs-pin` and
  saying why (the gazetteer knows Den Ha–Dong Mada Road only to the tambon,
  ±1.5 km, which is not a pin; Mama Noi's Ton Kham Soi 2 is not in it; Akha
  Kitchen states no address). On /pins.html.
- **Eight records enriched** from their own sites through `enrich.json` —
  BaanThai, Thai Secret, Thai Farm (the OSM point is the in-town office; the
  farm is ~17 km out, and the pin note says so), Asia Scenic (address, phone,
  three session kinds, the carving course), May Kaidee (school and
  restaurant, separate addresses), Siam Garden, Four Seasons.
- **`known_facts()`** renders the school's own statements: `classSessions`
  (+via) · `classPrices` (+the unwalked mark) · `pickup` · `groupSize` ·
  `menuNote` · `teachLang` · `pinNote`.
- **Facet set `cooking`** (23 facets, `appliesToCat`, sits BEFORE the school
  set so a cooking school meets same-day booking / evening class / half day /
  market walk / pickup / own stove / veg / halal / allergies / kids / private
  / English / **Thai** / recipes / certificate / multi-day / ED visa / prices on
  show / the two licences / aircon / parking / step-free — not the school bus
  and the lunch). Nothing is ticked; `_cooking_note` says why. The two
  licence facets are paperwork, photographable, positive only: a
  โรงเรียนนอกระบบ registered with สช. under the Private School Act B.E. 2550 hangs
  a numbered licence; a class that fetches you and walks a market may instead
  be a tour business with a TAT licence number (Suwannee prints hers). Neither
  absence is recorded and neither is a judgement. 14 new keys added to
  `worker/worker.js` FACET_KEYS — worker NOT redeployed.
- **Search:** the teasers carry the vocabulary; `search-core/mine.py` re-mined,
  `sync.py` re-synced. "สอนทำอาหาร", "cooking", "ขนมไทย", "แกะสลักผักผลไม้",
  "มังสวิรัติ" narrow to the shelf. The first draft hijacked broad words —
  "hotel", "market", "vegan", "northern", "ล้านนา" mapped to the cooking shelf
  alone — and the teasers were rewritten until they did not.

### Events — the board, and the one calendar day

- **`data/curated/cooking_classes.json`** — the weekly board: twelve schools
  with their own word (four state weekdays — Thai Secret closes Sundays, Mama
  Noi and Siam Garden run daily, May Kaidee's school closes Sunday — eight
  state sessions but not days), one row not tied to a record (Thai Akha
  Kitchen: the site's name and the OSM name share one distinctive token, which
  the strict matcher does not call a match — `maybe_place` names the
  candidate for a person), three sites that could not be read that day
  (Zabb-E-Lee redirects to an unrelated domain, Cooking@home's certificate has
  expired, Pantawan refuses bots), four names not confirmed (the town's first
  school's domain now redirects to a gambling landing and is never linked;
  Basil's certificate has expired; Smart Cook's site says "coming soon";
  Thai Orchid and Galangal have no readable site), and a Chiang Rai line.
- **กินเจ** in `festivals.json` — national, Chinese-lunar, nine days of the
  ninth month; the festivals test's canon count bumped 35 → 36 deliberately.
  The vegan card on the primer points at it.

### Culture — the primer, from the chopping board

- **`/cooking.html`** (`cooking_layer.py`): *which class today* (the reader's
  own weekday, Asia/Bangkok, swapped in by a dozen lines of inline JS; the
  page as built names the build day), the weekly board (bold = the school
  states the day, grey = sessions stated but not days, — = the school states
  no class), a card per school with sessions, posted price, pickup, menu,
  booking, source and date, the unread sites, the unconfirmed names, the
  Chiang Rai line, the shelf's porch (counts per province and child, every
  school one line with its reach ☎ LINE 🌐 and a 📋 for the ones on the
  board, unranked), and nine primer cards: the market first and the five
  tastes; galangal is not ginger, kaffir lime, the three basils; the mortar
  and why you pound; the wok and the fire; the Northern menu and sticky rice
  (*Tradition holds—* for khao soi and hang le); เจ · มังสวิรัติ · วีแกน; money,
  the van and the commission; twenty words with script, RTGS and tone; the
  paper on the wall — สช. licence, TAT licence, and the DSD skill standard for
  ผู้ประกอบอาหารไทย, stated as paperwork, "ask to see". Then the joins, stated
  from this side: wichaa.net/thairoots (ข้าว that means all food, กิน), /taste
  (eat tonight what you cooked), /festivals/kin-je, the markets shelf.
- Nav: `เรียนทำอาหาร · Cooking classes` in the svcbar on every page; a band on
  the cooking shelf pages pointing at the board; llms.txt 🍳 section that tells
  a bot to read `stated_by` and that `days: null` means not stated.
- **Reader sheet `cooking-words`** (`assets/reader/cooking-words.pdf`, two
  sides, measured to 0.1 mm over like the others): the market words on the
  front, the stove words on the back, the posted spread as a plaque, the
  two papers in the look box. `cooking-money` is deliberately NOT written —
  it waits on three boards read at three doors (an in-town school, a farm
  school, a hotel studio).
- Fix ledger entry (มดเอง): seven shelves by the mapper's tag, the auto-repair
  misfile, the culinary-art-school miss.

## What this note is deliberately not proposing

- **No crawl.** `amenity=cooking_school` is zero in both provinces; adding
  the selector to the schools group is a network change and waits on Nan's go.
  It would likely add nothing today.
- **No scrape of booking platforms** (Cookly, GetYourGuide, Klook) for prices
  or schedules. A platform's price is a platform's price; the school's own
  site is the only word the board carries, and where the school posts no
  price the board says so.
- **No menu rankings, no "best class" list, no reviews.** The site holds no
  ratings and draws none.
- **No tie on one shared token.** Thai Akha Kitchen ↔ Thai Akha Cooking
  School is almost certainly one school renamed; almost is the word the
  review file is for.
- **No vocational records on memory.** The Polytechnic's site would not
  answer and the DSD page did not mention cooking; the child is truthfully
  empty with its reason in `tests/test_facets.py`.

## Open, in order of value

1. **The door survey** — the 23 facets' `ask_th`/`ask_en` are its script.
   Twenty-five schools, three contactable by phone in the crawl; the schools'
   own sites lifted that to a dozen. A morning on Rachadamnoen and Loi Kroh
   fills LINE + same-day + evening + pickup radius for the old-city schools.
2. **Pins:** Mama Noi, Grandma's (Saraphi), Suwannee (Den Ha–Dong Mada), Akha
   Kitchen — four stops, two provinces, /pins.html.
3. **Prices walked:** three boards read at three doors clears
   `_pricesVerified` and lets `cooking-money` ship.
4. **Thai Akha Kitchen ↔ Thai Akha Cooking School** — one look at the door
   settles the tie; then the board row gains its `place`.
5. **The vocational shelf by its own word:** the Polytechnic's short-course
   page (site unreachable 2026-08-19), DSD 19 Chiang Mai's test calendar
   (053 121002-3), CMRU คหกรรมศาสตร์, the vocational colleges — each enters
   the day its own page says อาหาร. `audit_cooking.py --only vocational` is the
   list.
6. **Names with no readable site:** Thai Orchid, Galangal, Basil (expired
   cert), Smart Cook ("coming soon"), Thai Cookery School (domain lost) — a
   phone call or a walk each; none enters on memory.
7. **Hotel studios beyond Four Seasons** — Dhara Dhevi (staged reopening),
   Anantara, Rachamankha, 137 Pillars, Shangri-La — each from its own page.
8. **Chiang Rai** — two schools from their own sites; the town surely holds
   more (Cooking with Ann was seen in a search result and not read).
9. **A reader question** (`asked.json`) — "a cooking class that picks up
   from Nimman, evening, vegan" is the shape readers ask in; the board can
   answer it the day somebody asks.
10. **wichaa, the deep half:** the Lanna medicine treatises hold the same
    roots the market teacher holds up — ข่า ขมิ้น ตะไคร้ — and an article on
    the Northern kitchen (ข้าวซอย's road, the ขันโตก, แกงฮังเล's name) would
    give the primer a door to open. Per `feedback_wichaa_is_the_hub` the
    question is *where*, not *whether*. Not started.
