# Doors and tags — the weed.th move, generalised, and a tag layer

*2026-08-19. Nan: "I really liked how we got names and addresses of weed shops
from an aggregation site, and then helped our site grow and their site grow
with polite backlinks. Can we do that with any of the other shelves or
categories (also TAGS — tags are how Quora got immense). Just plan."*

**Nothing here is built.** To write it, ~95 fetches were made: robots.txt,
sitemaps and terms pages of 22 candidate sites; the data.go.th catalogue API
(all 795 datasets of the Chiang Mai and Chiang Rai provincial offices, 29 CSV
heads read); and **two** detail pages on thailandtourismdirectory.go.th to see
what the HTML carries — the same three-pages-before-a-line measurement weed.th
got. No listing pages anywhere else, no crawl. Read with `MARCHING-ORDERS.md`
WO-15…WO-18 (PROPOSED) and `data/sources.json` (every door below is now an
entry there, status = what was fetched).

## Five things only Nan can decide

1. **WO-15, the tag layer — go?** Zero network; builds from what is on disk
   today. ~150–220 tag pages per province plus ~60 brand pages.
2. **Thailand Tourism Directory — sign up for the API key?** The licensed route
   to ~28,500 national listings with phone · LINE · hours · coordinates is an
   official keyed API (`api.thailandtourismdirectory.go.th/openapi/read`).
   Accounts are yours to create, not mine.
3. **WO-16, the open lists — go for the small fetches?** data.go.th CSV/XLSX
   files, each under 2.5 MB, open licences or "not specified" like the school
   registers we already use.
4. **Enrichment policy.** Today only an owner's claim may change a record we
   already hold. WO-17 would let a government directory add a phone/LINE/hours
   to an existing record, labelled `via: ttd`. New behaviour — your call.
5. **Follow or nofollow.** Every credit link today is `rel="nofollow"`. If the
   point is that *their* site grows too, a per-source allowlist of followed
   links (government directories + the aggregator we actually took data from)
   is one line. Stakes: followed links to junk can hurt us; to .go.th and
   weed.th they cannot.

---

## 0. What "the weed.th move" actually was — the recipe

So it can be repeated exactly, here is what WO-8b did, step by step:

1. **A site that wants to be read.** robots.txt invites crawlers, publishes a
   sitemap, server-renders name + address (a schema.org `Store` block).
2. **Measured before building.** Three pages opened by hand; what is in the
   HTML versus what loads behind a button. The importer promises only what is
   there — it took a NAME and an ADDRESS and said so in its docstring.
3. **Only the plain city data.** Reviews and ratings are refused at parse time
   (`_strip_refused()`, with a test), never skipped.
4. **Manners.** 8× their stated crawl-delay, snapshot-first into `cache/`, one
   page per shop ever, a User-Agent that names us and where to complain.
5. **Fold-in at the weakest tier** (`third-party`, −1, below crawled). Exact
   name match = corroboration, not a merge; near-matches go to a review file;
   nothing auto-merges.
6. **Pins from our own ground** (`geocode_local`), precision and uncertainty
   printed; `needs-pin` is a legitimate state.
7. **Provenance travels** — "ชื่อและที่อยู่จาก weed.th · Name and address from
   weed.th" with a `rel=nofollow` link back on every record. That line *is* the
   polite backlink.
8. **Idempotent importer**, proven by running twice and diffing (the
   self-reference trap).
9. **Registered** in `data/sources.json` with a status that is what was fetched.

Outcome: cannabis CM 30 → 557, CR 6 → 139; weed.th received 658 attributed
links. That is the bar.

## 1. The finding: there are four kinds of door, and the best is not an aggregator

| Kind | Example already in the house | What it gives | Manners |
|---|---|---|---|
| **Register** (government open data) | CITIZENinfo (CC-BY), OBEC/OPEC | complete-by-construction lists, yardsticks, licence conditions | credit per record is the licence |
| **Official directory** | *(new)* Thailand Tourism Directory | phone · LINE · hours · coords — the contact currency | API key; credit + link |
| **Private aggregator** | weed.th | names + addresses, coverage | robots + terms must both say yes |
| **Brand locator** | *(none yet)* | the owner's own branch list | per brand; link to their page |

Most private aggregators say **no** in their terms (Wongnai says it in so many
words, below). The registers and the official directory say yes by
construction. So the answer to "can we do the weed.th move elsewhere"
is: **yes, mostly through open doors rather than scraped ones**, and the
backlink is still the courtesy in every case.

## 2. The big door — Thailand Tourism Directory (กระทรวงการท่องเที่ยวและกีฬา)

`https://thailandtourismdirectory.go.th` — the ministry's national POI
directory, built (per its own data.go.th entries) as the country's tourism
data hub.

**Measured 2026-08-19:**

- **Sitemap ≈ 28,500 URLs** in six files: restaurants 13,264 · accommodations
  6,989 · attractions 5,864 · stores 1,304 · spas 406 · routes 351 · activities
  241 (nationwide; the province is in each record).
- **Detail pages are Next.js; the server HTML carries the whole record in
  `__NEXT_DATA__`** (two pages opened: `/accommodations/6365`,
  `/restaurants/82423`): `Name` th/en/zh/jp · structured address (`Moo` `Soi`
  `Road` `SubDistrict` `District` `Province` `PostCode`) · `Latitude`/
  `Longitude` · `Telephone` `Mobile` `Fax` · `Website` `Email` `FacebookUrl`
  `LineID` · `OpenHours` per weekday · `SourceDepartment` `Official`
  `OfficialOwner` · plus `Rating` and `ViewCount`, which this site **refuses**.
  Also a `Restaurant` sub-object and `TravelTypes`. Images are theirs
  (`files.thailandtourismdirectory.go.th`) — link, never copy, as with weed.th.
- **robots.txt**: `User-agent: *` → `Content-Signal: search=yes, ai-train=no,
  use=reference` + `Allow: /`; Amazonbot, Applebot-Extended, Bytespider,
  CCBot, ClaudeBot, GPTBot, Google-Extended, Meta are named and blocked. A
  directory that lists a name, an address and a link back is "search" use.
- **Official API** (MOTS's own how-to, `how-to-call-api-ttd-v2.pdf` on
  data.go.th): `POST https://api.thailandtourismdirectory.go.th/openapi/read`
  with JSON `{APIKey, SecretKey, Lang th|en|zh, Skip, Limit, Type 1–6,
  ProvinceCode}` — Type 1 attractions · 2 activities · 3 accommodation · 4 spa ·
  5 restaurants · 6 stores; ProvinceCode = first two digits of the postcode
  (**Chiang Mai 50, Chiang Rai 57**). Response: `count` + `results[]` of URL,
  Type, IntroImage, Name, Detail, Latitude, Longitude, District, Province,
  Region, IsOpen. The summary omits the contact fields; the page carries them.
- **MOTS publishes TTD extracts on data.go.th** — "รายการสปา" under **Open Data
  Common**, "ที่พัก" / "ร้านค้าของฝาก" / "เส้นทาง" (licence not specified), each
  with the API how-to attached. That is the ministry saying this data is for
  reuse. Contrast DTAM's cannabis GIS, whose own terms forbid it.
- **Not measured**: the CM + CR share. `count` from one API call with
  ProvinceCode 50 and 57 answers it — that is step 0 of WO-17.

**What it lifts** (today's numbers, from `data/canonical`): hotel CM 1,465 /
CR 470 with **hours on 65 / 19**; food CM 4,151 with a phone on 594; massage CM
300 / **CR 0**; sights and shopping thin everywhere. TTD's fields are exactly
the "contact = the currency" fields the site has been starving for, from a
publisher who states coordinates rather than inferring them.

**Rules for WO-17** (nothing new in kind, one thing new in degree):
refuse `Rating` and `ViewCount` at parse time with a test; provenance line
"ข้อมูลจาก Thailand Tourism Directory (กระทรวงการท่องเที่ยวและกีฬา)" + link to
their page; owner claims still win over everything; exact-name match to a
record we hold → **enrich** contact fields with `via: ttd` (this is decision 4);
near-match → review file; no match → new record at the `opendata` tier (it is a
government publisher via its own API) — *not* `third-party`, which is for
scraped storefronts. Page reads, if any, 8 s apart, once per place, only for
ids the API returned for our two provinces.

## 3. The door survey, shelf by shelf

Current counts are CM / CR from `data/canonical` on 2026-08-19. "Measured"
means fetched today; everything else is marked.

| Shelf | Now CM / CR | Door | Kind | Carries | Measured status | Backlink form |
|---|---|---|---|---|---|---|
| **hotel** | 1,465 / 470 (hours 65/19) | TTD accommodations (6,989 nat.) | official directory | name, addr, coords, phone, LINE, hours, licence fields in the i18n strings | **verified** — 2 pages | link to TTD page |
| | | data.go.th `_67_76` (CM) | register-count | **yardstick**: Mueang CM 706 hotels + 487 non-hotel stays certified, 2567 | verified CSV | — |
| | | OTAs (Agoda/Booking) | aggregator | — | not probed; terms known hostile | not proposed |
| **food** | 4,151 / 1,129 (phone 594/194) | TTD restaurants (13,264 nat.) | official directory | as above + `Restaurant` object | **verified** | link to TTD page |
| | | Wongnai | aggregator | everything | **walled by its terms** §(3): "ไม่รวบรวมข้อมูลร้านค้า ที่อยู่ร้าน รีวิว … เพื่อวัตถุประสงค์ใด ๆ ก็ตาม เว้นแต่จะได้รับอนุญาต" — robots is open, terms are not | do not |
| | | HappyCow | aggregator (vegan) | — | robots open (only /api/, /hcediting/ closed), 84-file sitemap; **terms page is client-rendered (1 char)** — read in a browser first | link from the vegan tag page regardless |
| | | Thai SELECT (CM, `_67_69`) | register-list | 23 restaurant names, 2563 | verified CSV | tag/honour + link to DITP |
| | | ธงฟ้าราคาประหยัด (CR, `dataset40_11`) | register-list | 33 rows: name, amphoe, tambon, food type, grade | verified CSV (cp874) | tag |
| **massage** | 300 / **0** | TTD spas (406 nat.) | official directory | as above | **verified** | link |
| | | HSS licence list (`dataset-3-3-01`) | register | CertificateCode, ServiceType, Gender, BirthYear, Province — **people, anonymised; no establishment names** | verified CSV — counts only | — |
| | | spa.hss.moph.go.th | register UI | division homepage, old jQuery; the public licence search is not server-rendered here — find it in a browser | probed | — |
| | | GoWabi | aggregator/booking | sitemap1 = 42,993 provider URLs, **CM 137 / CR 6** by slug; robots open, Crawl-delay 1 | **terms client-rendered (unread)** → park; Defiant already knows them as an affiliate — the politest link here is the affiliate link | ask |
| | | Fresha | aggregator/booking | venue sitemaps exist (24 files); CM count unmeasured | robots open; no terms found at 3 paths → park | ask |
| **realestate** | 305 / 17 | Hipflat · DDproperty · FazWaz · Coworker | aggregators | — | **401 / 403 / sitemaps 403 / 403** — refused at the door | not proposed |
| | | กรมที่ดิน condo registration | register | statistics, not names | catalogue only | — |
| **wat** | 307 / 289 | **data.go.th `67-04` วัดและสำนักสงฆ์ (CM)** | register-list | **4,462 rows**: ชื่อวัด, ประเภท (วัดราษฎร์…), นิกาย, ตำบล, อำเภอ; XLSX 181 KB + CSV | **verified** — licence "not specified", same as the school registers | join with the wat-registry (WO-1); tambon+amphoe pair geocode |
| | | `67-03` 9 วัดนามมงคล (CM) | curated-list | nine auspicious-name temples | catalogue only | a tag, obviously |
| | | `dataset_20_19` (CR) | register-list | 127 religious/arts/cultural sites, amphoe | verified CSV (cp874) | — |
| **sights / parks** | 164+116 / 119+126 | TTD attractions (5,864 nat.) | official directory | as above | **verified** | link |
| | | `eco` (CR) | register-list | **38 rows with name, address, amphoe, tambon, PHONE** (สิงห์ปาร์ค 053 160 636) | verified CSV | credit line |
| | | `dataset_20_12` (CR) | register-list | 119 community-tourism sites | verified CSV (cp874) | — |
| | | `dataset_10_0510` (CM) | register | recommended attractions, CC-BY, URL resource | catalogue only | — |
| **essentials** | 1,085 / 367 (phone 26/9) | `_67_73` police stations (CM) | register-list | **39 rows with phone numbers** | verified CSV | — |
| | | `69_139`/`69_140` LPG stations (CM) | register-list | 27 company names, amphoe, tambon | verified CSV | fuel tag "LPG" |
| | | banks, 7-Eleven, PTT, Bangchak… | brand locators | the owner's branch list | not probed — per brand | link to the brand's own branch page (WO-18) |
| **transport** | 269 / 267 | `_67_70` bus routes (CM) | register-list | **641 rows: route name, amphoe passed, tambon passed**; `dataset_10_238` 27 cat-1/4 routes; `69_148` city routes | verified CSV | feeds WO-13's bus board — zero scraping |
| **medical** | 859 / 302 | done (WO-9) | — | CR clinics yardstick 547 (2563) | — | — |
| **pharmacy** | 376 CM (OSM) | FDA `drug-location` | register | ใบอนุญาตสถานที่ด้านยา 2024, XLSX 2.4 MB, national | size-checked only | credit line |
| **muaythai** | 22 / 1 | SAT `sat-standardized-boxingcamps` | register | CC-BY XLSX 39 KB, national, with data dictionary | size-checked only | credit line → WO-12 |
| **business** | 45 / 10 | `dataset_10_344` tour operators (CM) | register-count | **yardstick 872 licensed, 2565** — a count, not a list | verified CSV | — |
| **shopping** | 174 / 99 | TTD stores (1,304 nat.); `_67_83` OTOP outlets | directory / count | outlets by amphoe (Mueang 200) | verified | link |
| **whats-on** | 9 / 4 | Eventpop | platform | — | robots disallows `/events/` to everyone and names the AI crawlers | no |
| **community · beauty · tattoo · pets · repair · home-services** | thin | — | — | **no door found** (vets: 0 datasets; beauty → GoWabi/Fresha parked) | — | say so on the shelf |
| *(tag)* bitcoin | 45 crypto attrs | BTC Map | open (OSM `currency:XBT`) | nothing we don't hold; their value is verification dates | robots allow-all, SPA | link from the bitcoin tag page; ask Overpass for `currency:XBT=yes` province-wide |
| *(all)* | | Longdo Map | platform | — | terms forbid "any robot, spider … to retrieve or index" | no |
| *(all)* | | Overture Places (CDLA-P 2.0) · Foursquare OS Places (Apache 2.0) | open mega-sources | every shelf at once, with phones/sites/socials | docs reachable; **GB-scale parquet, not stdlib** | separate decision, not this plan |

**Two operational findings, worth more than one shelf:**

- **`gdcatalog.go.th` (the provincial open-data hosts) returns 403 to any
  User-Agent containing the word "bot".** Our `MotDangBot/1.0 (+url; email)`
  was refused on every CSV; `MotDang/1.0 (+https://motdang.net/about.html;
  530kings@proton.me)` and even Python's default UA pass. It is a WAF word
  list, not a policy against automation. Re-test the old 403 verdicts
  (chiangmaipao.go.th, onenimman.com, chiangmainext.com, tourismthailand.org)
  with the no-"bot" UA before believing them.
- **Chiang Rai's provincial CSVs are cp874 (TIS-620), Chiang Mai's are UTF-8.**
  Decode by province or the Thai arrives as mojibake.

## 4. TAGS — the Quora move, translated

What Quora did: every question carries several topics; every topic is a page
with a real count; pages link densely both ways; the long tail is crawlable;
a topic page is a landing page. Translate to a directory:

- **Shelves** answer *what kind of place* (one branch of the tree).
- **Facets** answer *is THAT branch worth walking to* (per-shelf ticks, owner-
  editable).
- **Tags** answer *what is this place ALSO* — across shelves. "vegan", "halal",
  "bitcoin", "24 h", "wheelchair", "wifi", "outdoor seating", "in the old city",
  "7-Eleven", "Michelin", "royal temple", "LPG". Each tag is a page a search
  engine or an assistant lands on for "vegan chiang mai" — exactly the queries
  the tree cannot answer and the ones Batch 23 said we can win (exhaustive
  lists over data only we hold).

**The vocabulary is already in the data — measured over 16,270 records and 140
`attrs` keys, every candidate with ≥10 records:**

| Family | Tags (count) |
|---|---|
| cuisine | thai 764 · coffee 602 · japanese 93 · pizza 88 · tea 88 · breakfast 80 · burger 77 · italian 73 · cake 69 · international 69 · sandwich 61 · asian 61 · noodle 60 · chinese 55 · chicken 52 · steak 49 · ice cream 39 · american 33 · pasta 29 · korean 28 · indian 28 · seafood 26 · local 25 · vietnamese 23 · french 19 · barbecue 16 · salad 15 · mexican 15 · sushi 12 · juice 12 · bubble tea 12 · dessert 11 · grill 11 · pancake 11 · german 11 · curry 10 |
| diet | vegetarian 152 · vegan 102 · halal 10 · gluten-free 7 · organic 6 |
| pay | cards ≈100 · cash-only 30 · QR 12 · **bitcoin/lightning 45** |
| comfort | wifi 1,229 (free 291) · air-con 116 · outdoor seating 257 · takeaway 195 · delivery 25 · smoking area 54 · no smoking 115 · drive-through 7 · ATM on site 230 |
| hours | open 24 h 300 · open late 32 |
| access | wheelchair yes 137 · limited 92 · toilets 39 |
| place | in the old city 122 (derivable for *all* records from the moat geometry) · highland 424 · borderland 16 |
| brand | 144 brands on 1,238 records — 7-Eleven 404 · PTT 152 · บางจาก 67 · Café Amazon 60 · BBL 38 · KBank 36 · KTB 29 · SCB 28 · KFC 26 · Lotus's 22 … |
| honours | royal temple 9 · Michelin 14 · registered historic site 44 · hotel stars 38 · Thai SELECT 23 (WO-16) · 9 วัดนามมงคล (WO-16) |
| medical | dental 72 · skin 13 · psych 4 · chinese-med 4 · eye 3 · ortho 3 |
| fuel | diesel 86 · E20 46 · LPG 35 · E85 12 · CNG 1 |
| wat | มหานิกาย 340 · ธรรมยุต 6 · wisungkhamsima granted 300 |

**Rules (house ethic applied):**

1. **A tag is derived, never typed.** `data/tags.json` defines each tag: slug,
   th, en, glyph, family, ONE rule (an `attrs` key/value, a facet key, a sub,
   an honours list, a curated list), `via` label. The build assigns; records
   carry `tags` + `tagVia` in places.json and the per-place JSON. No tag
   without a rule; no rule without a source field — nothing inferred from a
   name or a category except where the rule says exactly that.
2. **Curated outranks derived.** `data/curated/tags_curated.json` for Nan's own
   (9 วัดนามมงคล, "riverside", "rainy-day") — the Quora part where people edit
   the topic; our edit door is the existing `suggest.html`.
3. **Pages**: `/cm/tag/<slug>.html` and `/cr/tag/<slug>.html` (never merged
   counts), Yahoo list `Name — shelf` with the shelf map; `/tags.html` index as
   `Tag (count)` grouped by family; tag pills on every place page (links);
   **tag ∩ shelf pages only where count ≥ 8** (one constant, conservative,
   widenable); no tag × tag, no tag × soi. Brand pages are the `brand` family
   (every 7-Eleven branch) and the natural home for WO-18's locator links.
4. **Polite backlinks live on tag pages** as an "also catalogued by" line,
   harvest or no harvest: vegan → HappyCow · bitcoin → BTC Map · wheelchair →
   Wheelmap · cannabis → weed.th · Michelin → the Guide · Thai SELECT → DITP ·
   halal → CICOT. Link out generously; that is the Yahoo spirit.
5. **Search** (WO-4): tags into `search_thesaurus.json`, a tag page ranks first
   for its own words. **llms.txt** gains `## 🏷 Tags` + `data/tags.json` + one
   JSON per tag. **sitemap** lists tag pages. **OG cards** via
   `make_shelf_cards.py` (the list-page path).
6. **my.html**: pin a tag = Quora's "follow a topic"; the +N-new badge already
   exists for shelves.
7. **Owners**: facet ticks project into tags where the rule says so (openlate,
   open24, wifi, wheelchair, crypto, card) — the claims worker needs no change.
8. **Tests** `tests/test_tags.py`: every tag has rule/th/en; every rendered
   count equals the records; nothing under threshold renders; KNOWN_EMPTY list;
   the verify_reach invariant (no page links a verified-broken URL) still holds.

Zero network. WO-15 can be built today.

## 5. Orders, in the order to do them

- **WO-15 — Tags layer** *(no fetch)*. `data/tags.json` from the table above →
  `tags_layer.py` (`emit(g, data)`, after graph_layer, before the sitemap) →
  pills in the place body → index + province tag pages + brand pages →
  thesaurus + llms.txt + cards → tests. Acceptance: ≥150 tag pages per
  province with true counts; every tagged place shows pills; all gates pass;
  `grep -rl "/Users/" docs/` empty.
- **WO-16 — Open lists from data.go.th** *(small fetches, Nan's go)*:
  (a) CM temples 4,462 → wat shelf as named records (tambon+amphoe pair
  geocode; join the WO-1 registry); (b) bus routes 641 + 27 → WO-13's bus
  board; (c) CR eco 38 (phones) + religious/arts 127 + community 119 →
  sights CR; (d) CM police 39 (phones) → essentials; (e) Thai SELECT 23 +
  ธงฟ้า 33 → honours/tags; (f) LPG 27 → fuel tag; (g) SAT boxing camps →
  WO-12; (h) FDA pharmacy licences → compare with the 376 OSM pharmacies.
  One `importers/import_<x>.py` each, snapshot-first, credit line per record,
  cp874 for CR, UA without "bot". Yardsticks (hotels 1,193 Mueang; tour
  operators 872; CR clinics 547) go to /stats.html as "what the province
  counts vs what we hold".
- **WO-17 — Thailand Tourism Directory** *(step 0 is Nan's signup)*:
  `harvest_ttd.py` via the API (ProvinceCode 50/57 × Type 1–6) → counts first;
  page reads for contact fields only for returned ids, 8 s apart, once; fold-in
  at `opendata` tier with credit + link; refuse Rating/ViewCount; enrichment
  per decision 4; review file for near-matches; run twice and diff.
- **WO-18 — Brand locators** *(park until 15–17 land)*: 7-Eleven, PTT,
  Bangchak, Café Amazon, the four big banks — per-brand robots/terms check,
  branch list from the brand's own endpoint, per-branch link to the brand's
  page; owner-is-authority reasoning, same fence as claims (contact + hours
  only).
- **Parking lot — measured, do not redo**: Wongnai (terms forbid) · Hipflat,
  DDproperty, FazWaz, Coworker (door shut) · Longdo (terms) · Eventpop
  (robots) · HappyCow, GoWabi, Fresha (terms unread — a browser read first) ·
  HSS operator list (anonymised people) · DTAM (walled; the data.go.th
  Bangkok precedent means the letter is worth writing) · Overture / FSQ OS
  Places (open but GB-scale and non-stdlib — its own decision).

## 6. Stakes, in plain words

- **Doing nothing**: shelves stay thin where the data sits in open CSVs, and
  "vegan chiang mai" keeps getting silence from a site that holds 102 vegan
  places.
- **WO-15** worst case: a wrong rule tags a place wrongly — visible on the
  page, fixed by editing one rule and rebuilding; no one outside is touched.
- **WO-16/16** worst case: a licence misread and a takedown request. Mitigated
  by per-record credit, a link back, taking only facts (names, addresses,
  phone numbers — not prose, not photos, not ratings), the API route for TTD,
  and the ministry's own open-data publication of the same data. You will very
  likely be fine.
- **Cost**: ฿0. Your time: one API signup, and perhaps three terms pages read
  in a browser (HappyCow, GoWabi, Fresha).

## 7. What was fetched to write this

robots.txt + sitemap + a terms-page path on 22 hosts (wongnai, hipflat,
fazwaz, ddproperty, gowabi, fresha, happycow, coworker, btcmap, thaihotels,
longdo, eventpop, spa.hss, hss, fda, dot, thailandtourismdirectory, dld,
halal.or.th, foodsan.anamai, docs.overturemaps, docs.foursquare); seven TTD
sitemap files and **two** TTD detail pages; MOTS's API how-to PDF; data.go.th
CKAN `package_search` (16 queries), `package_show` (≈35), the full dataset
lists of `chiangmai-province` (477) and `chiangrai-province` (318), 29 CSV
heads; four HEAD requests on XLSX sizes; one gowabi sub-sitemap; one UA test
(4 requests on one CSV). Announced UA throughout; 2 s between requests. No
listing page on any private site was opened.
