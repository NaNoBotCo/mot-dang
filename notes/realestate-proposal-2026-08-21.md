# WO-27 — อสังหาฯ-ที่พัก: the split, the words, the register, and the farang door

*2026-08-21. Zero-network BUILT. The doors below await a numbered go.*

Nan's ask, verbatim: *"I'm thinking if the farang SEO crowd is going to show ANY
interest in motdang, it's going to come thru the door of real estate. Real estate
on motdang is extremely underdeveloped. I might partner with someone like Laila,
who has a real estate side gig, or maybe perfect homes CM (although I don't think
our interests 100% align). Let's enrich deeply, while leaving room for
intestitial expansion."*

Two instructions in that: enrich deeply, and leave interstitial room. §2 is the
depth that needed no network; §4 is where the room was left and what each slot
waits for. The launch rule stands unchanged: *catalog stable things (condo
BUILDINGS + agents/developers), not churny listings.*

---

## 1. What the measurement found

`importers/audit_realestate.py` (new, zero network) reads every record's own name.

| finding | number |
|---|---|
| records on the shelf, both provinces | **322** (cm 305 · cr 17) |
| filed as "condo" before today | **316** |
| names (or the mapper's description) that say condominium | **53** |
| names that say แมนชั่น · คอร์ท · อพาร์ตเมนต์ · residence | 79 |
| names that say หอพัก / dorm | **22** |
| names that state nothing (the tag's word — building=apartments — is all there is) | 162 |
| agents | **5** — and the census says OSM holds no more to crawl |
| monthly words sitting on the hotel shelf | **60** — counted, never re-filed by a rule |
| สำนักงานที่ดิน anywhere in the catalogue | **0** |
| names saying furnished / posting a rate | **0 / 0** |
| จัดสรร in a name | 3 — all villages (a health station, a school…), zero estates |
| phones · first-hand websites · stated floor counts | 41 · 14 (12 first-hand) · 77 |

The condo shelf was the barber shelf again (6 of 62): one OSM value, one sub,
and the label lying about five-sixths of what stood under it. A reader hunting a
condominium was shown แมนชั่น; the reader hunting a ห้องเช่า — the median reader
of this shelf — could not see the monthly trade at all under a condo label.

Two traps measured and dodged: the mined search table maps **หมู่บ้าน** and
**"buildings"** to this shelf, so the new panel triggers by variants and query
substring ONLY (a village name must not open a housing-estate door — the
มังสวิรัติ lesson, now held by a test); and **คอร์ท/court** is safe only inside
building=apartments (sport courts carry it too).

## 2. Built, all zero-network

- **The split at classify()** — `realestate_sub()` in import_overpass.py: หอพัก
  → dorm, คอนโด (name or mapper's description) → condo, everything else →
  apartment, the tag's own word. Receipt in data/fixes.json under มดเอง.
  "Condotel" stays off the condo shelf by the word boundary.
- **categories.json** — condo relabelled อาคารชุด-คอนโด / Condominiums (it
  claimed all buildings; now it claims the 53 that claim it); new `apartment`
  and `dorm` children; **moobaan stays a named slot without a match rule, on
  purpose** — wiring was tried and test_facets refused it, correctly: a rule
  matching zero records is the silently-empty-cafe bug, and the child shows
  as a wireframe shelf either way. One line wires it the day the landuse
  door lands records.
- **One retag** — Sunshine Apartment, office=estate_agent whose only word is a
  building's name: agent → apartment, receipt in retags.json (add_sub support
  added to apply_curated_retags — it could drop a sub but never add one).
- **audit_realestate.py** — the split census recomputed from classify()'s own
  function (two implementations = one implementation), the whole agent shelf
  printed with the two rows needing a person (is Sara — a person's name, the
  unlisted-by-default question; อคิน ลิสซิ่ง — a leasing slug, a lead not a
  retag), the guards shown working every run.
- **data/curated/realestate.json** — the register, empty and saying so, with
  the discipline written in: rents only as posted with dates, rates per unit,
  and the foreign quota ONLY ever as a dated statement from the juristic
  office — a facet tick would rot into a lie a week after it was true.
- **The `realestate` facet set** (12 keys: monthly · daily · furnished · lift ·
  pool · gym · keycard · pets · laundry · rateboard · shortok · guard) +
  the keys in worker/worker.js. Until the worker is redeployed (manual
  `npx wrangler deploy`, Nan's move) an owner ticking the new keys is
  filtered out, harmlessly.
- **/realestate.html** (`realestate_layer.py`) — the words with RTGS/tone/root
  (ค่าไฟหน่วยละ first; why the cheapest buildings are called Mansion; เซ้ง the
  Teochew loan), six desk sentences (TM30 and the foreign-quota question asked
  as questions, pointed at the desk and the นิติบุคคล — this page does not
  recite statutes it has not fetched), the four shelves, the census of
  silences, the register with its 12-building read queue, and **ใกล้หอนาฬิกา
  เชียงราย** — every CR residential record within 1.5 km of the clock tower,
  metres computed from catalogue coordinates and said so. Band on the shelf
  pages, same shape as beauty's.
- **Search**: `realestate` panel (variants/query only, no shelves trigger),
  แมนชั่น + mansion added to the existing condo-apartment thesaurus ring,
  test_search grown by four cases including the หมู่บ้านป่าไผ่ no-fire guard.
- **Two asked pages** — `monthly-apartment` and `student-dorm`, the two
  questions this shelf is actually asked, each ending in the door sentence.

## 3. The doors — awaiting Nan's numbered go

1. **Read the 12 first-hand sites** (the register queue: Airport Home Condominium,
   Life in Town, วีระชัยคอร์ต, Ping View, Smith Suites, the two Hinokï towers,
   Nimman and Me, The Mirror, Riverside Condominium, The Empire Residence, The
   Iris Chotana) — read_beauty_sites manners, rents/rates/services as stated,
   with the sentence each was read from. This fills the register its page is
   already shaped around.
2. **The Land Office selector** — `office=government` (with `government=*` kept)
   in both provinces; ZERO สำนักงานที่ดิน in the catalogue is the buying
   door's biggest hole, and it also lands the อำเภอ offices the essentials
   shelf is asked about.
3. **The moobaan door** — `landuse=residential["name"]` WIDE, area-clipped. The
   named housing estates OSM does hold arrive here; the audit's fences and the
   wired child are already waiting for them.
4. **The dormitory selector** — `building=dormitory["name"]`, one run; the
   census cannot see building keys, so the only way to close the question is
   to ask it once.
5. **Agents, curated by hand** — the real agencies (Perfect Homes CM and peers)
   entered as curated records with fetched sources, the featured-chiang-rai
   pattern. This is door work and Nan's relationships, not a crawl — OSM has
   nothing more to give here.
6. **data.go.th parking lot** — the Treasury's assessed land prices and the
   Land Department's condominium-juristic registry are the two official sets
   that would enrich condo rows; each needs its dataset id found, then one
   line in harvest_datagoth.SOURCES (the WO-16 pattern).
7. **TTD** (pinned on WO-17's key) — lodging-heavy, probably thin here; listed
   so the question stays closed rather than reopened hopefully.

## 3b. POSTSCRIPT — all six runnable doors run, 2026-08-21

Nan's go, same day: *"go ahead on everything you can!"* Door 7 (TTD) stayed
shut — it needs an account only she can make. What the other six were worth:

**Door 1 — the site reads: 6 read, 2 speak, and one defect found in my own
reader.** Of the 12 first-hand links, five domains no longer resolve
(Airport Home Condominium, both Hinokï towers, The Iris Chotana) and one
refuses robots (The Mirror). Six were read; **two state anything at all** —
Ping View (furnished, lift, pool) and Smith Suites (furnished, pool), each
with the sentence it came from. The defect: **Life in Town's own domain now
302s to `rogotravel.com/red.php?url=…booking.com…`**, an affiliate
redirector into an OTA. The first-hand rule was being checked BEFORE the
redirects, so that page passed as "the building's own site" and its silence
would have been published as the building's own silence. `read_one()` now
re-checks `first_hand()` on the FINAL url; the row was deleted and refetched.
A lapsed domain pointed at an affiliate farm is the commonest way this goes
wrong, and it is the same class of bug as the beauty reader's scheme-less
URL. Also added: `page_chars`, because a building that "states nothing" out
of 56 characters has not been read, it has been visited.

**Door 2 — the Land Office: 0 → 4, and the gap named.** `office=government`
had never been asked for by any selector (`amenity=townhall` was the only
government rule, and a Land Office is not a townhall). 165 CM + 108 CR
offices folded onto `essentials/gov`; among them
**สำนักงานที่ดินจังหวัดเชียงใหม่ สาขาสันทราย, สาขาเชียงดาว, กรมที่ดิน and
สำนักงานที่ดินจังหวัดเชียงราย**. What is still missing is on the page in
words: the open map has two Chiang Mai BRANCHES and not the Mueang seat,
which is the one most people go to.

**Door 3 — the estates: 0 → 22, with 590 villages fenced OUT.** This was the
door with something to lose. `landuse=residential["name"]` returns where
people LIVE — 531 named areas in CM, 81 in CR — and nearly all of them are
villages wearing หมู่บ้าน, the ordinary word. Only จัดสรร or a developer's
own name on the arch files a record (`audit_realestate.moobaan_hit`, one
copy, borrowed by the importer the way the elephant and spring fences are).
22 passed and every one is a real development — Supalai ×8, Pruksa ×4,
Quality Houses, Perfect Place, กัลปพฤกษ์, and one that says ที่ดินจัดสรร
outright. The other **590 are in `cache/moobaan_review_<prov>.txt`** where a
person can read them. Filing somebody's village as a gated development is a
falsehood about their home address, and that is why bare หมู่บ้าน is not a
rule and never will be.

**Door 4 — dormitories: 22 → 84.** `building=dormitory` tags student housing
on the building rather than in the name, so the shelf had only ever held the
ones that wrote หอพัก on the sign. 62 more, one selector, question closed.

**Door 5 — the agents: a closed question, not a yield.** The brokerage trade
cannot be read first-hand today. Perfect Homes answers **403** to an
announced reader; RE/MAX's branch page renders client-side and hands back
**one character**. Everything else a search returns — ddproperty,
thailand-property, lazudi, chiangmailocator, northernthailand — is a PORTAL,
somebody else's listing of an agency rather than the agency speaking, which
this repo does not treat as a source. So no agent record was invented from a
third-party directory of unknown vintage. The shelf stays at five and the
page now says why in both languages. **This door is Nan's relationships and
always was** — Laila's own details are hers to give, and a partner's record
should come from the partner.

**Door 6 — data.go.th: one dataset unusable, one that changes the page.**
Both ids found and both recorded in `data/sources.json` so neither is
re-discovered hopefully:
- `land-valuation` (กรมธนารักษ์, Open Data Common, edition 2026-06-25) is
  real, current and per-province — and **UNUSABLE**: 41 MB, 1,060,644 CM
  parcels keyed by `UTMMAP1-4 + LAND_NO`, the cadastral map sheet and parcel
  number, with no address, no district and no coordinate. It cannot be joined
  to anything without the cadastral geometry, which is neither open nor here.
- `condominium-valuation` **is** joinable and is now harvested by
  `importers/harvest_condo_register.py` → `data/curated/condo_register.json`:
  **385 registered condominium buildings in the north (366 CM, 19 CR)** with
  the Treasury's assessed value per m². Two traps, both measured and both
  written into the importer: the CSV is **cp874**, and read as UTF-8 a search
  for เชียงใหม่ returns ZERO rows rather than failing; and the file is one
  national 122,112-row export ordered by province code with **the north at
  the END**, so any size-capped read (the shared harvester stops at 6 MB)
  comes back with no Chiang Mai in it at all.

  What it changes: the government counts **366 condominium buildings in
  Chiang Mai; this catalogue holds 53** by name. That gap is now on the page
  as a measured work-list. **Eight** register rows join a record by EXACT
  normalized name and carry their assessed spread. A substring join was tried
  and **rejected** — it matched นครพิงค์คอนโดมิเนียม to เพชรนครพิงค์, a
  different building, and folded two registered buildings onto one record
  called บ้านสวน. Sixteen loose matches became eight true ones. And every
  line says what ราคาประเมิน is: the basis for transfer fees, not a market
  price, normally well below one.

## 4. The interstitial room, by design

- **Sub slots named, not stubbed**: `serviced`, `developer`,
  `property-management`, `juristic` are the next children when records exist
  to stand on them — an empty child is hidden by design, so wiring them today
  would be invisible; naming them here is what keeps the tree's shape ready.
- **The hotel-side 60** stay where their tourism tag put them, counted on the
  board every build. When somebody reads those venues' own pages, the ones
  that state a monthly trade gain the second shelf through shelves.json with
  receipts — the Hub 53 pattern, one by one, never by rule.
- **The facet set is the growth surface**: an owner claiming their building
  answers the questions no crawl ever will, and the claim flow (scope-fenced
  to contacts + hours + facets) already exists.
- **Listings stay out** — the launch rule. If a partner's inventory ever
  appears it is a marked ผู้สนับสนุน card under the ads doctrine (flat rate,
  no tracking, never reordering a shelf), not records. The register's rent
  fields hold what a BUILDING posts about itself, dated — that is the line
  between a catalogue and a marketplace, and it is where this site stands.
- **The foreign-quota shape** is settled in the register's readme before the
  first row exists: a dated statement from the building's own channel, never
  a facet, never an inference. (The same shape serves the หอนาฬิกา scouting
  list — when CR condo records exist, the near-the-tower section grows them
  with no new code.)

## 5. The farang door, without growth mechanics

AGENTS.md says the farang expat "is already won and is not the frontier" — and
its no-growth-mechanics rule stands. Nan's thesis today is different and
compatible: the farang searcher arrives through real-estate queries, so the
DOOR must exist and answer well. What was built is the door and nothing else:
a bilingual page whose English half actually answers (condo · apartment ·
dormitory · the per-unit rate · the quota question), schema.org and the og
card it already gets, two asked pages shaped like the long-tail queries, and
the same Thai-first page serving the ห้องเช่า reader first. No engagement
loop, no A/B, no app — the site's own bot-hospitality (llms.txt, places.json,
sitemap) is the distribution.

## 6. The partner note (for Nan, nothing sent)

Laila's side gig and Perfect Homes CM want different things from a directory:
an agent wants leads and placement; this site sells neither. What it CAN offer
a partner without bending: a claimed, enriched agency listing (free, like
everyone's), sponsor cards under the marked-box doctrine, and the register as
a shared instrument — a partner who helps fill building facts gets a better
city, not a better rank. Laila's records are already featured field-truth in
CR; that pattern (hand-entered, sourced, marked when sponsored) is the shape
that fits both her and Perfect Homes — and the interests that "don't 100%
align" (placement, exclusivity, lead capture) are exactly the parts the site's
constitution already refuses, which makes the conversation short and clean.
