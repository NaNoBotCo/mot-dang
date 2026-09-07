# มวยไทย — events, locations, culture: making Mot Dang deep where it was thin

*2026-08-19. Nan: "motdang.net should be muuuuuuccch richer and deeper in muay
thai. It's events, locations, and culture." This note is the measurement, the
rule the shelf runs on, and what was built the same day under WO-12. Read with
`MARCHING-ORDERS.md` WO-12; the reasoning is here and is not repeated there.*

## The measurement, before any proposal

Muay thai lived on this site as **twenty records on two shelves, split by how
a mapper tagged the door**, and nothing else.

| What a reader asks | What the site held on 2026-08-19 morning |
|---|---|
| Where are the stadiums, and who fights tonight? | **No stadium shelf.** One stadium (Kawila) filed as a *camp* under the schools shelf. Thapae, Loi Kroh and Chiangmai Boxing Stadium absent — OpenStreetMap has no node for any of them. |
| Where can I train? | 13 ค่ายมวย on `school/muaythai` (found by NAME — `sport=muay_thai` is tagged on **zero** elements in both provinces, rechecked twice for WO-11) and 6 more on `learn/gym` ("มวยไทย-ยิม"), where Hong Thong and Santai sit between fitness centres. 6 of 19 contactable. |
| Where do I buy gloves? | Nothing. No crawl group has ever asked; no shelf to be empty on. |
| Is there an event? | `data/events.json` (Meetup + Payap feeds): zero. `data/festivals.json`: zero — not even วันมวยไทย. |
| What am I looking at when the music starts? | Nothing. No primer, no words, no reader sheet. Two Commons photographs in `image_picks.json` tagged `sport`. |
| Does wichaa carry it? | No. The manuscript catalogue (6,986) holds no ตำรามวย and no เจิง; `/waikhru` is the machine blessing; `/yant` indexes designs without saying where the prajiad goes. |

So "events, locations, culture" is not an enrichment of a thin shelf. It is
three pillars and only one of them had a foundation — and that one was the
hole in the schools shelf that WO-11 already named ("the register that should
list … muay thai camps … is empty as published").

## The rule this shelf runs on

Massage's rule was *never infer respectability*. Culture's was *never infer
whether a reader is allowed in, never infer price*. Muay thai's is:

**The venue states its own nights, its own prices, its own door rules — or the
page says nobody has stated them. Rings into real and
touristic.** A stadium beside Tha Phae Gate with a VIP drink and a stadium on
Kong Sai Road where the bettors stand are both stadiums; the card is the card.
"Which one is authentic" is a tourist question this site does not answer
(`feedback_no_tourist_framing`). What it answers is *which nights, from when,
for how much, by whose word, seen on what date*.

Three consequences, all in the data shape:

- `data/curated/fight_nights.json` carries `days` ONLY for nights the venue
  itself states (`stated_by: "venue"`, `source`, `fetched`). What a listing or
  a reseller says goes in `days_reported`, by name and date, and renders in
  italics with a `?`. A venue nobody has stated nights for still appears,
  under *ask before you go* — silence about the weekday is not "no fights".
- Prices carry `_pricesVerified: false` until somebody reads the board at the
  door, exactly as the reader sheets and the ขัดขี้ไคล records do. A price read
  off the venue's own site is still "posted", never "costs".
- The audit (`importers/audit_muaythai.py`) reads NAMES and the crawl's own
  sub, and nothing else. A mapper's *description* that says muay thai
  (Go gym) is a LEAD for a person, not a proposal. Bare มวย is never a rule —
  หมวย is a nickname (เจ๊หมวย ผัดไทย) and มวยผม is a hair bun; every Thai term
  is a compound, the กระท่อม discipline again.

## What was built (2026-08-19), pillar by pillar

### Locations — the shelf

- **Tree, additive:** new top-level cat `muaythai` (มวยไทย) with three
  children — `stadium` สนามมวย-ดูมวย · `camp` ค่ายมวย-ยิมมวยไทย · `gear`
  ร้านอุปกรณ์มวย. `school/muaythai` and `learn/gym` keep every record and every
  URL; a record reaches the new shelf by gaining a SECOND cat through
  `data/curated/shelves.json` — WO-10's move. `learn`'s teaser no longer sends
  "ค่ายมวย" to the fitness shelf. Icon `i-glove` drawn into the sprite;
  schema.org `SportsActivityLocation`, with `StadiumOrArena` and
  `SportingGoodsStore` through `SCHEMA_TYPE_SUB`.
- **Audit → shelves.json:** `audit_muaythai.py --emit` proposed 20 entries
  (19 camp, 1 stadium), every one with `source: osm name: …` or `osm sub:
  muaythai`. Applied. Kawila Boxing Stadium now carries `stadium` as well as
  the camp sub it was filed under; the misfile is on the fix ledger.
- **Three curated stadiums** in `additions-chiang-mai.json`, each from its own
  site, dated: Thaphae Boxing Stadium (pin = Tha Phae Gate, `approx`, says so),
  Loi Kroh Boxing Stadium (pin = the middle of Loi Kroh Lane 3 from the local
  gazetteer, ±180 m, `approx`, says so), Chiangmai Boxing Stadium / Sorying
  Arena (177 Chang Phueak Rd, `needs-pin` — the gazetteer can only give the
  road's midpoint ±884 m, which is not a pin; it is on /pins.html).
- **`known_facts()`** renders the venue's own statements: fight nights (and
  who stated them), nights as others list them, tickets (with the unwalked
  mark), training, a second phone, what the pin is.
- **Facet set `muaythai`** (15 facets, `appliesToCat`, sits BEFORE the school
  set so a camp meets drop-in / beginners / woman trainer / kids / ED visa /
  stay / fighters on the cards / fight nights / gear sold — not the school
  bus). Nothing is ticked; `_muaythai_note` says why. `muaythai/gear` is in
  KNOWN_EMPTY with its reason.
- **Search:** the teasers carry the vocabulary (สนามมวย ค่ายมวย ยิมมวยไทย
  ไหว้ครูรำมวย มงคล ประเจียด · stadiums fight nights camps gyms gear wai khru);
  `search-core/mine.py` re-mined, `sync.py` re-synced. "สนามมวย" and "fight"
  now narrow to the shelf.

### Events — the board and the calendar

- **`data/curated/fight_nights.json`** — the weekly board: four venues (two
  with venue-stated nights, Loi Kroh with weekly-but-unstated, Kawila with
  reported-only), three *unconfirmed* rings (Kalare — own Facebook read closed
  late 2025 while resellers still sell it; Anusarn and Pavilion — a dated
  listing marks them closed), and a Chiang Rai line (no weekly ring found; The
  Underdog camp is on the shelf).
- **Into the harvest:** `muaythai_layer.raw_events()` turns venue-stated
  nights into weekly events with a BYDAY list (one event per stadium, not
  six), merged into `EVENTS_RAW` at import so /events.html, the home carousel,
  the stadium's own page band, `events.ics` (RRULE with several weekdays — a
  one-line addition to `event_vevent`) and the JSON all carry them through
  the one path. Source label "กระดานคืนชกมวย · the fight board".
- **Two national days** in `festivals.json`: วันมวยไทย 6 Feb (Cabinet, 3 May
  2011, สมเด็จพระเจ้าเสือ) and วันนายขนมต้ม · World Wai Khru 17 Mar (Ayutthaya),
  both `national`, `fixed`, `general-knowledge`; the festivals test's canon
  count bumped 33 → 35 deliberately.

### Culture — the primer, from the seat

- **`/muaythai.html`** (`muaythai_layer.py`): *who fights tonight* (the
  reader's own weekday, Asia/Bangkok, swapped in by a dozen lines of inline
  JS; the page as built names the build day), the weekly board (bold = venue
  states it, italic-? = reported), a card per venue with source and date, the
  unconfirmed rings, the shelf's porch (counts per province and child, every
  camp one line with its reach ☎ LINE 🌐, unranked), and the primer: wai khru
  and why the fight has not started; mongkhon and prajiad; the four musicians
  and the sarama; five rounds and the walked fifth; the bettors; ticket
  classes, the VIP drink and the "free pickup" commission; fourteen words
  with script, RTGS and tone; the word มวย and its hair-bun sense (*Tradition
  holds—* for the rope-bound-fist story); the two days; the north — เจิง,
  ตบมะผาบ, มวยท่าเสา, and temple-fair cards. Then the joins to wichaa, stated
  from this side: `/yant` (the designs folded into a prajiad), `/waikhru` (the
  same three beats, salute · receive · undertake), `/thairoots`.
- Nav: `ดูมวยคืนนี้ · Muay Thai tonight` in the svcbar on every page; a band on
  the Muay Thai shelf pages pointing at the board; llms.txt section that tells
  a bot to read `stated_by` before repeating a night.

## What this note is deliberately not proposing

- **No crawl.** `sport=muay_thai` is zero in both provinces; a broader
  Overpass ask (`leisure=sports_centre` + `sport=boxing`, `shop=sports`) is a
  network fetch and waits on Nan's go. It would likely add a few fitness-with-
  boxing gyms and no stadium — the stadiums are not in OSM at all.
- **No scrape of the stadiums' Facebook pages** for nightly cards. Login wall;
  the structural ceiling named in Batch 7b. The board is curated and dated,
  and says so.
- **No fighter names and no results.** That is sport journalism, perishable by
  the hour, and somebody else's.
- **No claim about children's bouts beyond "there are youth bouts on the
  cards"**. The law and its debate are a wichaa-side subject with sources,
  not a sentence on a fight board.

## Open, in order of value

1. **The door survey** — the 15 facets' `ask_th`/`ask_en` are its script.
   Nineteen camps, six contactable; a ride past the camps in the moat and on
   Huay Kaew fills phone + LINE + drop-in + beginners in an afternoon.
2. **Pins:** Chiangmai Boxing Stadium (177 Chang Phueak) and a surveyed pin for
   Loi Kroh's ring and Thaphae's door — three stops, one errand, /pins.html.
3. **Prices walked:** three boards read at three doors clears
   `_pricesVerified` for the stadiums; the camps' session/week/month rates are
   unknown and a reader sheet `muay-money` cannot ship before they are.
4. **Gear:** the Night Bazaar stalls and the Fairtex / Twins / Top King
   counters exist and are on no map. Curated additions by name and by walk;
   `audit_muaythai.py --only gear` is the check.
5. **Camps by name:** the kratom route — Team Quest (Mae Rim), Chay Yai, Siam
   No.1, Manop's, Kiatbusaba and the rest are known by name to anyone who
   trains here and to no crawl. Each needs its own site or page fetched and
   dated before it enters; none enter on memory.
6. **Reader sheets** `muay-words` / `muay-expect` / `muay-money` in
   `reader_sheets.json` + `make_reader_sheets.py` — the primer is the copy;
   the money sheet waits on (3).
7. **wichaa, the deep half:** an article (the articles door, beside Khun Phaen
   and sak yant) on มวย in the north — เจิง and ฟ้อนเจิง, ตบมะผาบ, the ram muay
   as wai khru, the mongkhon/prajiad/yant/katha chain, the word's root, the two
   days, Nai Khanom Tom as tradition. Per `feedback_wichaa_is_the_hub` the
   question is *where*, not *whether*; the Mot Dang primer links to it the day
   it exists, and the article links back to the board with "where to see the
   yant at work tonight". Not started; it wants the article voice and its own
   session.
8. **Loi Kroh's weekdays** — their site lists nights one at a time; a
   `--refetch` of their event pages for the next month would give the pattern
   by their own word. Light fetch, Nan's call.
