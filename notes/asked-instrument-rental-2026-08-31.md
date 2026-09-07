# instrument-rental — อยากเล่นดนตรีที่เชียงใหม่ ซื้อหรือเช่าเครื่องดนตรีได้ที่ไหน ต้องลงไปกรุงเทพไหม

*I want to play here — where do I buy or rent an instrument in Chiang Mai, and do I have to go to Bangkok?*

- asked_on: 2026-08-31
- via: other (Nan)
- status: RELEASED — `draft` deleted; 25 records, shelf `shopping/music`, research in `data/curated/music.json`

## The question, in the trade's own word

**เครื่องดนตรี** (khrueang dontri) is the shop word and it was never in doubt.
The word that actually decided this work order was the RENTAL word, and there
are three of them, not one:

| Thai | what it buys | who answers |
|---|---|---|
| **เช่ารายเดือน** | a student's instrument for a term | Churairat, Piano Center |
| **เช่ารายวัน** / แบ็คไลน์ | backline for an event | Triple A Sound, LNW Event, Sound VIP |
| **ห้องซ้อม** (rehearsal room) | an hour on a kit you don't own | ten rooms in the city |

Searching `เช่าเครื่องดนตรี เชียงใหม่` returns the first two and **misses the
third entirely** — and the third is what most people asking this question
actually want. ห้องซ้อม is not a rental word in the trade's own vocabulary, but
it is the same need met. That is the ขัดขี้ไคล lesson arriving from a new
direction: not a shop calling itself something else, but a SERVICE filed under
a word nobody would search.

- word tried: เครื่องดนตรี · ให้เช่าเครื่องดนตรี · เช่าเปียโน · เช่าไวโอลิน · เช่าเครื่องเป่า · ห้องซ้อมดนตรี · สะล้อ ซอ ซึง

## The measurement, which is the headline

`importers/crawl_overpass.py` has carried `nwr["shop"="musical_instrument"]["name"]`
inside the `making` group for as long as that group has existed. **The `making`
group had never been run.** No `cache/overpass/cm/making.json`, none for `cr`.
Twenty-odd groups in the cache directory and this one absent.

Run for this work order on 2026-08-31:

```
cm/making: 42 elements (province-wide)
  nwr["shop"="musical_instrument"]["name"] -> 1
```

**One.** And the one is `node/4559279126` — **Piano Center**, Suthep Road,
+66 53 277 990, open daily 08:30–21:00 — which is **a piano rental firm**. The
reader's question is where to rent an instrument in Chiang Mai and the single
record the open map holds was the answer, sitting behind a selector nobody had
ever fired.

This is a harder version of the beauty-shelf failure. There, a shelf sat empty
under a stated reason that had stopped being true. Here there was no reason and
no number — the query existed in the source and was never sent, so nothing ever
looked wrong. **A selector that has never run is not a measurement, and an
absent cache file is the only thing that shows it.**

Second-order: OSM `node/5234292721` "Greens Music" is in our data as
`shopping/mall`. It is Green Music at 67/4-5 Prapokklao, an instrument shop
with rehearsal rooms. So the map's coverage of this trade is one correct record
and one misfiled one.

## Sources (url · fetched 2026-08-31 · what it supports)

**The twenty categories**
- namm.org/blog/industry-insights-key-takeaways-2025-global-report — US: fretted +38% in the decade, digital/electronic +36.5%, pedals ~$200M
- pianodreamers.com/guitar-sales-statistics/ — US guitar split (electric 58 / acoustic 36 / classical 6, Music Trades); NAMM ownership 69% acoustic, 60% electric
- centralfifetimes.com/news/national/25126061… — ABRSM Making Music 2024, 1,000+ children 5–17: electric guitar 17% (13% in 2014), piano 16%, recorder 16% (28%), flute 15% (7%), keyboard 13%
- thestrad.com/electric-guitar-overtakes-violin… — ABRSM 2024: electric guitar passes violin; the most-played six
- geyemusic.com/article_detail/view/117773 — Thai ranked list: acoustic guitar, electric guitar, Electone, ukulele, harmonica, sax, violin, piano, flute, bongos

**Renting**
- churairatmusic.com/rent-service/marching-and-concert-rental — student monthly rates, 3/6/12-month terms, deposits
- churairatmusic.com/th/rent-service/piano-rental/990-baht/home-use — piano tiers, delivery 2,500, deposits 20,000/35,000/65,000
- churairatmusic.com/en/contact — the Chiang Mai showroom: Khao Shong Park, 24/5, San Phi Suea, 093-090-9018
- cmhy.city/en/place/15574-Churairat-Music-Chiang-Mai — **the branch's own listing naming instrument rental among its services**
- themusicthailand.com/9-ร้านเช่าเปียโนทั่วไทย/ — nine piano rental firms compared; Churairat and Piano Center both serve Chiang Mai
- bravomusic.co.th/rental — Bangkok orchestral day rates AND the collect-in-person / Bangkok-delivery-only terms
- doremimusic-cm.com/en/piano-room-for-rent-in-chiangmai/ — 4 piano rooms, 350 THB/hr, Hang Dong
- chiangmai.net/business-directory/category/musical-instrument-rental — the rental category holds ONE business (Patr Music)

**Shops**
- thailandnomads.com/music-instrument-stops-chiang-mai/ — nine shops, addresses and phones
- salehere.co.th/articles/musical-instrument-at-chiang-mai — five shops, Thai addresses, hours
- salehere.co.th/articles/music-rehearsal-room-in-chiang-mai — ten rehearsal rooms
- musicarms.net/ร้าน-music-arms-สาขาเชียงใหม่/ — Star Avenue 7, 082-786-2391, category list
- cmmusicthailand.com — brass/woodwind specialist; the only page in either province naming oboe and bassoon
- chiangmailocator.com/chiang-mai-shops-4460:piano-center — Piano Center address and second number
- chiangraimusic.com/en/ — Chiang Rai Music, Phra Suphan Rd, 097-123-5959, and its own superlative
- cmhy.city/en/place/35818-Parinyapat-Thai-Music — Lanna instruments, Chang Phueak, 094-762-6333
- yellowpages.co.th ร้านล้านนาการดนตรี — 56 Huay Kaew Rd
- surin_lanna.plazathai.com — สุรินทร์ดนตรีล้านนา, a MAKER, 081-366-4929

## Leads — name · what is missing · why · the one act that clears it

- [ ] **Churairat Chiang Mai** — does the CM floor HOLD rental band and string stock, or does it come up from Bangkok, and how long? Every monthly price on this shelf hangs off this. → **one call, 093-090-9018**
- [ ] **Piano Center CM** — its rental service and the 900–1,200/month figure come from a third-party roundup, not pianocenter.co.th. → one call, 053-277-990
- [ ] **Patr Music** — rental confirmed by two directories, no rate card read, address unconfirmed from its own page. → message the Facebook page, or walk Sri Phum
- [ ] **Green Music room count** — 4 / 6 / 7 across three sources, and the 150–180 THB/hr is unconfirmed. → photograph the rate card; Toey Music is ten minutes away, so one walk clears both
- [ ] **Del Gesu Violin / Intune Guitar (CR)** — Facebook pages only, no address, phone or hours. → message both
- [ ] **The Lanna makers** — สุรินทร์ดนตรีล้านนา is a maker with no address. What does a ซึง cost and will he make to order? → 081-366-4929. This is the one question on the shelf Bangkok cannot answer
- [ ] **Chiang Rai** — two records for a whole province. → the province deserves the hour Chiang Mai got
- [ ] **OSM** — `Greens Music` node/5234292721 is filed `shopping/mall`. → fix in our data; consider an OSM edit
- [ ] **`cr/making`** — crawl was still running when this note was written. → read `cache/overpass/cr/making.json` and put the CR instrument-shop count into `music.json` `corpus`

## Decision

- **found 25** (cm 23, cr 2) — not a gap
- **shelf**: `shopping/music`, th `เครื่องดนตรี-ให้เช่า`, en `Instruments — buy & rent`. The shelf label carries the rental word because that is the half people arrive needing.
- **facet**: none yet. A `rents` facet is the obvious next one and it wants the door-survey sentence written before it is stubbed — the shelf is 25 records old and the flag is still mostly read off other people's directories.
- **what was NOT recorded, and why**:
  - **Bangkok backline houses** (IP Studio, Rocky Studio, W-Audio) — they rank for Chiang Mai searches and serve Bangkok only. Written into `music.json` `rental_clocks.day.note` so the next session does not re-find them and mistake them for coverage.
  - **fastwork.co/instrument-rental/chiangmai** — its search snippet promises rental "from 300 baht"; the page itself returns **พบงาน 0 งาน**. The snippet is not a source.
  - **Triple A Sound / LNW Event / Sound VIP** — real CM event-rental firms, but phone-and-Facebook only with no verified address. They are in `music.json` as leads, not as place records: a place record needs a place. (The snake precedent, inverted — there the answer was a number and we said so; here the number is real but the shelf is a shelf of addresses.)
  - **No shop ranked.** No brand advice. Chiang Rai Music's "largest in northern Thailand" is attributed, never restated.

## The answer, in one line

**No.** Chiang Mai sells nineteen of the twenty and rents most of them. Bangkok
is four things: **oboe, bassoon, harp, double bass** — plus a concert-grade
instrument for a single day, which Bravo Music will only hand over in person in
Bangkok. And it inverts once: for **สะล้อ ซอ ซึง**, Bangkok is the wrong
direction.

## Prices

All `_pricesVerified: false`. Nothing here has been read off a counter.

Monthly, from Churairat's national pages: flute 350 · clarinet 450 · trumpet 450
· alto sax 750 · French horn 1,550 · viola 550 · violin 950 · cello 550 · drum
kit 500 · xylophone 4,200. Upright piano 990 (+2,500 delivery both ways, 20,000
deposit) · Yamaha U1 2,500 · grand 5,500.

Hourly: rehearsal rooms ~150–300 · Doremi piano room 350.

Bangkok day rates (Bravo): violin/viola 3,000 · cello 5,000 · double bass 6,000
· harp 15,000 · commercial use 5,000 per instrument.

## The four outputs

- [x] records with dated sources in data/curated/additions-*.json → `importers/import_all.py`
- [x] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [ ] `python3 make_shelf_cards.py --only asked-instrument-rental` → `build.py` → `tests/test_asked.py`
- [ ] `python3 make_post.py instrument-rental` pasted back
