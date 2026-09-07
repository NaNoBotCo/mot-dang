# รถ-เดินทาง — the transport layer: boards, stations, how the city moves

*2026-08-19. Nan: "Just like motdang enriched its Muai Thai layer hugely, it
now needs to hugely enrich its transportation layer. Do we have a flights
widget yet? bus widget? Train widget?" This note is the measurement, the rule
the layer should run on, and what a WO-13 would build — in the shape of
`muay-thai-proposal-2026-08-19.md`, because the starting picture is the same
one: a shelf of mapper-tagged scraps and nothing a reader can plan a journey
from. Nothing here is built. Read with `MARCHING-ORDERS.md` WO-13 (PROPOSED).*

## The three answers first

| Widget | State on 2026-08-19 |
|---|---|
| **Flights** | **Yes, live, and orphaned.** `flights_layer.py` → `/flights.html` (the route board: 34 nonstop routes, 29 airlines, CNX 30 destinations · CEI 4, monthly arrival counts, seasons, `as_of 2026-08-02`, Aviasales referral links on marker `749581.motdang`, declared in both languages) and `/widgets/flights.html` (the 2 KB mini-board). Both return 200 on motdang.net. **Reachable only from `my.html`'s opt-in iframe gallery (`data/widgets.json`) and by URL.** Not linked from the transport shelf, not from the home page, not from `/widgets.html` (whose thirteen tiles are events · toilets · today · siamsi · maha lap · reading · weather · PM2.5 · hexagram · time · showtimes · lottery), not in the svcbar. A reader on `/cm/transport/` cannot find it. |
| **Bus** | **No.** No board, no data file, no layer. Green Bus, Nakhonchai Air and บขส. appear on the site only as bare OSM node names. |
| **Train** | **No.** No board, no shelf child. The railway station exists as one OSM node filed under `transport/station` with `nameTh` = "เชียงใหม่", `nameEn` = "Chiang Mai" — sorted under ช among the songthaew stops, with `operator: การรถไฟแห่งประเทศไทย` and a website in attrs that nobody reads. Chiang Rai has no railway (the Den Chai–Chiang Rai line is under construction; the opening year is to be stated from SRT's own page, not from memory). |

## The measurement, before any proposal

`transport` ("รถ-เดินทาง · Getting Around") holds **536 records** — 269 CM,
267 CR — and 435 of them are fuel stations. The shelf as published:

| Child | CM | CR | phone | web | hours | curated | Note |
|---|---|---|---|---|---|---|---|
| rental เช่ารถ-มอเตอร์ไซค์ | 29 | 11 | 4 | 3 | 8 | 0 | 36 of 40 unreachable; 2 have a Thai name |
| station สถานี-ท่ารถ | 35 | 18 | **0** | 1 | **0** | 0 | every record 🐜1; OSM scraps — "Minibus to go to ChiangMai 140B", "Songthaew statonight to go to ChiangMai"; Arcade 2 and 3, Chang Phueak, CR Terminals 1 and 2 present as bare names; the railway station hidden as "เชียงใหม่", with Saraphi and Pa Sao (`railway=station`, categories 3 and 4) beside it unlabelled; the two Doi Suthep "stations" are the temple **funicular**'s bottom and top (`station=funicular`) and the shelf cannot say so; นครชัยแอร์ counters in both provinces |
| airport สนามบิน | 2 | 2 | 1 | 1 | 0 | 0 | CNX is in twice (one node, one terminal polygon); CEI once plus its terminal building |
| songthaew รถแดง-สองแถว | — | — | | | | | **no `match` rule at all** — a wireframe with no reason given, not on `tests/test_facets.py` KNOWN_EMPTY; does not even render on CR |
| fuel ปั๊มน้ำมัน | 202 | 233 | 2 | 44 | 13 | 0 | the bulk of the shelf |
| *(pier)* | 1 | 2 | 0 | 0 | 0 | 0 | **orphan sub** — Tha Ton boat landing, Chiang Saen port: counted in the shelf total, no child to stand on |
| *(tours)* | — | 1 | 1 | 1 | | 1 | Laila Group, curated; no child |
| *(taxi — not on the shelf at all)* | 4 in cache | 1 in cache | 1 | | | | `cache/overpass/cm/stations.json` holds four `amenity=taxi` nodes — two "Taxi Meter" ranks, Mae Rim Car Rent Taxi Service, and คิวรถขึ้นภูพิงค์-ดอยปุย ("Mini Taxi", Sri Wichai Rd, **with a phone**) — and CR one; `importers/import_overpass.py:431-435` has no branch for `amenity=taxi`, so all five are dropped before the canonical file. The crawl group `stations` already asks for them (`crawl_overpass.py:152`). |

Where the tags went: the `stations` crawl group asks Overpass for aerodrome ·
terminal · `bus_station` · `public_transport=station` · `railway=station|halt`
· `ferry_terminal` · `taxi`, and the cache keeps every tag. The importer then
folds bus station, railway station, halt and public-transport station into
ONE sub, `station` (`import_overpass.py:433-435`), sends `ferry_terminal` to
`pier` (a sub with no shelf child), and returns `None` for taxi. So the
knowledge a reader needs — *this is a train station, this is a bus terminal,
this is a taxi rank, this is the funicular* — was fetched on 2026-07-27, is on
disk, and is thrown away at import. The split is a branch in one function and
four children in `categories.json`; it needs no network.

What a reader asks, against what the site holds:

| What a reader asks | What the site held on 2026-08-19 |
|---|---|
| I land at CNX at 22:00 — how do I get to the old city, and what does it cost? | Nothing. The airport record has a phone and a site; no card says taxi counter, red truck, Grab, or a fare by whose word. |
| Which bus goes to Chiang Rai / Pai / Bangkok, from which terminal, how often? | Nothing. Arcade 2, Arcade 3 and Chang Phueak are three names with no phone, no hours, no operators, no destinations. No board. |
| Is there a train? When? | One node named "เชียงใหม่". No timetable, no board, no link to SRT's own booking page. |
| How does a red truck work — do I flag it, share it, where do I say I'm going? | Nothing — the child exists on the tree and is empty with no reason. The search thesaurus already knows รถแดง · สองแถว · songthaew (WO-4) and lands the reader on the empty shelf. |
| Which coloured songthaew goes to Mae Rim / Samoeng / Tha Ton, from where? | Fourteen OSM stop-nodes whose NAMES carry the answer ("yellow songthaew to Tha Ton", "Songthaew stop from Chiangmai to Samoeng", "White or silver Songtaews to Doi Pui") — filed as stations, unlinked, ungrouped, by a mapper's word. |
| Where do I rent a scooter near me? | 40 records, 4 with a phone. |
| Who flies here? | Answered, well, on a page nobody is led to. |
| Plan a route | `plan.html` plans a walk or a ride between places on the old-city graph (`importers/routing.py`, `ride_plan.py`). It says nothing about any public vehicle. |

So "transport" is today one board (flights) that the shelf does not know about,
and one shelf that is 81 % fuel pumps. The bus, the train, the red truck and
the airport transfer — the four things a person actually means by "getting
around" — have no foundation at all.

## The rule this layer runs on

Massage: *never infer respectability*. Culture: *never infer whether a reader
is allowed in, never infer price*. Muay thai: *the venue states its own
nights, or the page says nobody has*. Transport:

**The operator states its own timetable, its own fare, its own terminal — dated,
by name — or the page says nobody has. A board is a season, never a departures
screen. The ways to move sit side by side: a red truck, a Grab, a metered taxi
and your own two feet are four ways, the card is the card.**

Consequences, in the data shape:

- Every route row carries `stated_by` (operator · terminal · listing · mapper),
  `source` and `fetched`. Operator-stated rows render plain; listing/mapper
  rows render italic with `?`, exactly the `days_reported` convention of
  `fight_nights.json`. A terminal with no stated departures still appears,
  under *ask at the window* — silence about a route is not "no bus".
- **Fares carry `_pricesVerified: false` until read at a window or on a
  vehicle.** A fare read off the operator's site is "posted", never "costs".
  Red-truck fares in particular: the page states what a named source stated on
  a date (the municipality, the cooperative, a terminal sign) and otherwise
  says *agree before you board* — which is information, not a warning.
- **Bakes flat, like the flights board.** Nothing is fetched at read time; no
  live arrivals; no vehicle is followed. The
  board's `as_of` is printed on the board. The flights layer already proves
  the shape: hand-refreshed data file, season-sized cadence, one voice per
  kind of number.
- **Referral links are declared** in both languages, as `/flights.html`
  declares its Aviasales marker. If bus/rail booking earns through the same
  Travelpayouts account (12Go is the usual SE-Asia partner there — *to verify
  in the marketplace before a single link is written*), the link is an ordinary
  `<a>` and the page says what it is. If not, the link goes to the operator's
  own booking page, plain.
- **No tourist sorting.** No "locals take the red truck", no "avoid the taxi
  mafia", no scam paragraph. `feedback_no_tourist_framing`. What the page
  answers is *which vehicle, from where, to where, how often, for how much, by
  whose word, seen on what date*.
- **Nothing enters on memory.** Every operator page and every timetable is
  fetched, dated and cited before a row exists — and network fetches are
  manual-trigger, confirmed with Nan (`MARCHING-ORDERS.md` header; CLAUDE.md
  last line). This note lists the fetches; it does not run them.

## What WO-13 would build, pillar by pillar

### Boards — the widgets (the question asked)

Three data files, one renderer pattern, copied from `flights_layer.py`:

- **`data/buses.json` → `/buses.html` + `widgets/buses.html`.** Terminals
  (Arcade 2 · Arcade 3 · Chang Phueak · CR Terminal 1 · CR Terminal 2 as the
  spine; Mae Sai, Chiang Khong, Fang, Chiang Dao, Phrao, Thoeng, Wiang Kaen
  as the rest — the OSM nodes already exist, they gain facts), operators
  (Green Bus · Nakhonchai Air · Sombat Tour · บขส. Transport Co. · the
  Prempracha / Chiang Mai–Thaton lines the OSM nodes name), routes
  `{from_terminal, to, operators[], class, per_day or departures[] as stated,
  duration_stated, fare_stated{min,max,_pricesVerified:false}, stated_by,
  source, fetched}`. The mini-board: the five terminals, each with its
  destinations and "~n/day · operator", as the flights mini-board does
  airports. *Not* a departures screen — the board says so in its first line.
- **`data/trains.json` → `/trains.html` + `widgets/trains.html`.** SRT's
  Northern Line at Chiang Mai: each train by number and class, departure and
  arrival as SRT states them, the days it runs, `as_of`, a link to SRT's own
  booking page. A Chiang Rai line that says, from SRT's own page with a date,
  what is and is not there yet. Small data, large value — the one board a
  reader can hold in the head.
- **`data/songthaew.json` → the red-truck card and the coloured lines.** The
  how-it-works card (flag · say where · shared · pay on getting down · เหมา to
  charter) and one row per coloured line *as a named source states it* —
  starting from the fourteen OSM stop-nodes whose names already say "yellow to
  Tha Ton", "white/silver to Doi Pui", "orange to Chiang Mai", each a
  `stated_by: mapper` row with its stop id, until a terminal sign or the
  cooperative's own notice upgrades it. Renders on `/transport.html` and on
  each stop's page. Fares only with `_pricesVerified` and a dated source.
- **The airport transfer card** on both airport pages and the hub: what AOT's
  own CNX / CEI pages state about taxi counters, airport buses or vans, and
  ride-hail pickup — fetched and dated; the card is empty-with-a-reason until
  then.
- **`/transport.html` — the hub**, the `/muaythai.html` analogue: the three
  boards' porches (flights · buses · trains), the red-truck card, "from the
  airport / from the station / from Arcade to the old city", the shelf porch
  (counts per child, every terminal one line with its reach ☎ 🌐), and the
  words (below). Svcbar chip **`ไปยังไง · Getting there`**; a band on every
  transport shelf page pointing at the hub; the flights board linked from the
  hub, the shelf and `/widgets.html` the same day — that alone repairs the
  orphan.

### Locations — the shelf

- **Tree, additive:** `station` splits by what a thing IS — by the OSM tag the
  cache already holds, not by what a mapper typed in the name —
  `bus-terminal` สถานีขนส่ง-ท่ารถ (`amenity=bus_station`) · `train`
  สถานีรถไฟ-รถราง (`railway=station|halt`; the Doi Suthep pair labelled
  *funicular* from `station=funicular`) · `songthaew` (gains its `match` at
  last: `highway=bus_stop` + the stop-nodes by name + the curated lines) ·
  `pier` ท่าเรือ (the orphan gets a child) · `taxi` แท็กซี่-คิวรถ
  (`amenity=taxi` — five nodes in cache today, so it is a shelf, not a card) ·
  `airport` stays (CNX deduplicated through `merges.json`; the two airfields
  and Sky Adventure stay off it, as `import_overpass.py` already decides) ·
  `rental` stays · `fuel` stays. Every existing record keeps its URL. The
  split is the branch at `import_overpass.py:431-435` returning the tag's own
  sub instead of `station`, plus the children in `categories.json`; curated
  second-cat moves go through `data/curated/shelves.json` (WO-10's move).
- **Audit → review file:** `importers/audit_transport.py` reads the cache's
  tags and the records' NAMES — zero network — and prints what the split will
  do before it does it: which of the 53 become train / bus-terminal / stop /
  pier / taxi by tag, which stop-nodes carry a line in their name ("yellow …
  to Tha Ton"), and what is left that only a person can file. Bare รถ is never
  a rule (รถ is in every car-park and repair shop); every Thai term is a
  compound, the กระท่อม discipline. Ambiguity goes to the review file, never
  to a coin flip.
- **Curated, each from its own page, dated:** Arcade 2 and 3 and Chang
  Phueak (phone, hours, operators at the window), CR Terminal 1 and 2, the
  railway station under its own name (สถานีรถไฟเชียงใหม่ via `names.json`,
  keeping "ป๋ายราง" as the alt name OSM gave it), the Green Bus and Nakhonchai
  Air counters, the Tha Ton and Chiang Saen piers with what sails from them.
  `known_facts()` gains: operators here · destinations · ticket window hours ·
  which songthaew lines call · what the pin is.
- **Facet set `transport`** (`appliesToCat`): luggage storage · left luggage ·
  ticket window hours · card payment · wheelchair (OSM already carries
  `wheelchair: limited` on the railway node — it renders today nowhere) ·
  night departures · helmet included (rental) · passport held (rental — asked,
  never inferred) · delivers to hotel (rental). Nothing ticked; `_transport_note`
  says why. `songthaew` and `pier` either match or go on KNOWN_EMPTY with
  their reason — never a wireframe with no reason again.
- **Search:** teasers carry the vocabulary (สถานีขนส่ง อาเขต ช้างเผือก สถานีรถไฟ
  รถแดง สองแถว ท่าเรือ เช่ามอไซค์ · Arcade Chang Phueak railway red truck
  songthaew pier scooter rental); `search-core/mine.py` re-mined, `sync.py`
  re-synced, so "train" lands on the train shelf and not on a node called
  เชียงใหม่.

### Culture — the primer, from the bench seat

- **The words**, script · RTGS · tone · root, on the hub: รถแดง *rot daeng*
  (รถ from Skt. *ratha*, chariot) · สองแถว *song thaeo* "two rows", the benches ·
  ท่ารถ *tha rot* (ท่า a landing — the same word as the pier) · สถานีขนส่ง *sathani
  khon song* · สถานีรถไฟ *sathani rot fai* "fire-car" · ท่าอากาศยาน / สนามบิน ·
  รถตู้ *rot tu* "cabinet car", the van · รถเมล์ *rot me*, from "mail" · วิน
  *win*, the motorcycle-taxi queue · เหมา *mao*, to charter · ตั๋ว *tua* ·
  ลงตรงนี้ "down here, please" · อาเขต *a-khet*, Arcade. Tones checked against
  the dictionary before print, as for `muay-words`.
- **How a red truck works**, in one card, from the rule above: flag it, say
  the place, it may already carry others, it may say no, pay when you get
  down, เหมา when you want it to yourself. No fare number without a dated,
  named source. The same card in the reader-sheet format (`transport-words`)
  once the words are checked; a `transport-money` sheet waits, as `muay-money`
  does, on fares read at windows.
- **The coloured lines and where they leave from** — Warorot, Chang Phueak,
  the south side — as a diagram on the hub, drawn ONLY from rows that have a
  source; a line with a mapper's word only is dotted and says so.
- **Joins stated from this side:** `/plan.html` (the last kilometre on foot,
  from the terminal to the pin), `/merit.html` (the nine temples begin at a
  gate a red truck knows), `/festivals.html` (Yi Peng nights — which roads
  close is an events fact, not a transport guess), wichaa `/thairoots` for
  the roots. Skip DJT and `flighthelper` are the same marker and the same
  airport-avoidance thinking; the flights board already sits beside them in
  `widgets.json`.

## What this note is deliberately not proposing

- **No live departures, no vehicle tracking, no GTFS.** None is published for
  either city that this site could bake; a board that looked live and was not
  would be the one thing worse than no board. Season-sized, dated, flat.
- **No scrape of 12Go, Baolau or Rome2rio.** Aggregators' rows are a listing's
  word; the operator's own page is the source, and where there is none the
  page says *ask at the window*.
- **No fare advice and no scam paragraph.** "Agree before you board" is the
  whole of it; the rest is `feedback_no_tourist_framing`.
- **Four ways side by side**; the card is the card.
- **No Overpass crawl in this note.** The re-tagging of the 53 station records
  and the five taxi ranks needs no network at all — the `stations` group
  already fetched railway, halt, ferry terminal and taxi on 2026-07-27. The
  one thing it did NOT ask for is the songthaew **lines**: `route=bus`
  relations and `highway=bus_stop` / `public_transport=platform` (the cache
  has a single bus_stop, and that only because a mapper also tagged it
  `public_transport=station`). That is one manual fetch on Nan's go, and it
  would likely add stops, not fares.

## What it costs, and what goes wrong if not done

The chore: one new layer file per board (copy `flights_layer.py`, ~300 lines
each), three hand-made JSON data files from ~8 operator pages, an audit
script, a categories/shelves/facets/KNOWN_EMPTY pass, a hub page, the mine
and sync, and the tests (`tests/test_transport.py` on the same pattern as
`test_asked.py`: every route row has `stated_by`+`source`+`fetched`; every
fare has `_pricesVerified`; every board prints its `as_of`; no wireframe
without a KNOWN_EMPTY reason). One session for the boards and the hub, a
second for the shelf split and the curated terminals; the walk ships each as
it clears the gate.

The worst case of leaving it: the shelf's second line says "Getting Around"
and a reader who types *train* is shown a node called เชียงใหม่; the one good
board on the subject stays unlinked; and the three OSM terminal names keep
standing in for a transport layer the site does not have.

## Open, in order of value — the proposed WO-13 sequence

1. **Repair the orphan (no data, one build):** link `/flights.html` from the
   transport shelf band, `/widgets.html`, and a svcbar chip; add the flights
   tile to `/widgets.html`'s thirteen. Half an hour. *Could ship today.*
2. **The zero-network split:** `audit_transport.py` (review file first) → the
   branch at `import_overpass.py:431-435` → `importers/import_all.py` from the
   cache on disk; children `bus-terminal` · `train` · `songthaew` · `pier` ·
   `taxi` in `categories.json`; `merges.json` for CNX; `names.json` for the
   railway station (สถานีรถไฟเชียงใหม่, old name ป๋ายราง kept); the funicular
   pair labelled; KNOWN_EMPTY reasons for whatever stays empty;
   `tests/test_facets.py` and the shelf-card gate re-run. One afternoon; no
   fetch. Measured gain: 53 scraps → five shelves a reader can name, plus five
   taxi ranks the site has been holding since July and never showed.
3. **The fetch list (Nan's go, one manual run, dated):** SRT timetable page
   for Chiang Mai + the SRT line page for Chiang Rai · Green Bus routes · Nakhonchai
   Air routes · Sombat Tour routes · บขส. routes from CM and CR · AOT's CNX and
   CEI ground-transport pages · the Chiang Mai and Chiang Rai DLT terminal
   pages for Arcade / Chang Phueak / Terminals 1–2 · Travelpayouts marketplace
   for the bus/rail partner. Eight-to-ten pages, each saved under
   `cache/transport/` with its date, each cited on the row it feeds.
4. **Three boards + hub** from (3): `buses.json` · `trains.json` ·
   `songthaew.json` → `/buses.html` · `/trains.html` · `/transport.html` ·
   `widgets/buses.html` · `widgets/trains.html`; `widgets.json` gains both;
   `llms.txt` 🚌 section ("read `stated_by` and `as_of` before repeating a
   time").
5. **Curated terminals and the airport card** from (3), each dated.
6. **The door survey:** five terminals, one errand — window hours, operators,
   the songthaew lines that call, a fare sign photographed (clears
   `_pricesVerified` for whatever the sign states); the rental shelf's 36
   unreachable shops by a ride past the moat's north and east sides.
7. **Reader sheets** `transport-words` · `transport-money` (waits on 6).
8. **`asked.json`:** the first question is already known — *from the airport
   to the old city, how, and what does it cost?* — it becomes a record the
   day (3) gives it a sourced answer, and a share card the same day.
