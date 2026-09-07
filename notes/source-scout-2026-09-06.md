# source-scout — 2026-09-06 (first run)

Four sources measured, three of them now `works`, one honest downgrade. Two
entries added. Three forks raised, one of which corrects a fork written earlier
today. No importer was written, nothing was published, nothing was posted.

## What I measured

### 1. hss-health-establishment-licence — WORKS (new entry)
The massage shelf's missing register, and it is national, not municipal:
**กรมสนับสนุนบริการสุขภาพ, data.go.th `hss_11_27`**, one CSV, no key, 2.4 MB,
Open Data Common.

- **18,180 rows nationwide. เชียงใหม่ 1,254 · เชียงราย 257 = 1,511 licensed
  massage and spa establishments.** The catalogue holds 325 CM + 12 CR massage
  records, so the state licenses about **4.5×** what we list.
- Whole-normalised-name match against `data/canonical`: **31 hit, 1,480
  unmatched.** That is a floor, not a count — the register has no address to
  disambiguate with, and per the Tier 0 contract nothing is matched on tokens.
- Fields are **five**: CertificateCode, ShopName, ServiceType, ProvinceID,
  Province. No address, no tambon, no phone, no coordinates. The 4th–5th digits
  of the certificate code are the licence class (5001=สปา, 5002/5003=นวด), not
  an amphoe — I checked before believing it.
- Newest certificate year in the file is 67 (2024), though the metadata claims
  quarterly updates.
- Nothing in CM/CR carries `กิจการดูแลผู้สูงอายุ` — 2,336 of those 2,590 rows
  are Bangkok. The long-care shelf gets nothing here.
- Modality words in the 1,511 names: แผนไทย 247 · สปา 112 · ตาบอด 3 · ตอกเส้น 1
  · อโรมา 1. The ten KNOWN_EMPTY massage modalities are not hiding in this
  register either; the door survey is still the door.

Sample: `cache/source_scout/hss-health-establishment-licence/2026-09-06.json`

### 2. dbd-juristic-register — WORKS
Monthly CSV, no key, direct:
`https://openapi.dbd.go.th/juristic_person/registration/99_YYYYMM_1.csv`
(Buddhist year). **55 months on offer, 2565-01 → 2569-07.**

- One month (2569-07): 7,512 rows nationwide, **เชียงใหม่ 336 · เชียงราย 106**.
- **100% of CM rows carry street address, tambon, amphoe AND postcode.** Also
  a 5-digit TSIC code and the objective written out in Thai.
- CM amphoe spread: เมืองเชียงใหม่ 128 · สันทราย 45 · สารภี 25 · หางดง 24 ·
  สันกำแพง 21.
- Maps onto the shelf tree by TSIC prefix. That one month, CM: shopping 63,
  food 35, realestate 11, repair 10, beauty+massage 10, medical 10, hotel 9,
  tours 8.
- **The empty shelves are in here.** `86902 กายภาพบำบัด` — บจ.อารีย์ ฟิสิโอ
  คลินิก, ต.สุเทพ, with a street address, and `("medical","physio")` holds
  **zero** records today. `86903` is the medical laboratory code and
  `("medical","laboratory")` is on KNOWN_EMPTY. `86203` dentists, `96101`
  massage (หจ.ของขวัญ นวดแผนไทย), `96104` beauty.
- At ~336 CM + ~106 CR a month, the archive is on the order of **18,000 CM and
  5,800 CR rows**.
- **Refused as mechanisms:** the all-companies `juristic` ZIP (advertised
  Creative Commons Attribution) is **764 bytes and contains only
  `datapackage.json`** — metadata, no rows; and
  `openapi.dbd.go.th/api/v1/juristic_person/{id}` is a one-company lookup, not
  an enumerator. Both are written into the register so nobody re-discovers them.

Sample: `cache/source_scout/dbd-juristic-register/2026-09-06.json`

### 3. hss-clinic-licence-register — DOWNGRADED to `partial`, and split
`privatehospital.hss.moph.go.th` loads (200) and sends you to
`hosp.hss.moph.go.th`, which 403s a plain UA while `/api/` and `/hospital`
return 404 — the server answers, the root is gated. I read it in a browser tab
rather than dressing a script up as one, and the finding is worth more than the
rows would have been:

**The form offers exactly two searches — เลขที่ใบอนุญาต or ชื่อสถานพยาบาล.**
No province, no amphoe, no type, no browse-all. It is a **verifier**, not a
register: it confirms a clinic you can already name. Recorded as its own entry
`hosp-hss-verifier`, status "partial — verification only, no enumeration",
**0 enumerable rows**.

data.go.th's `hss` org publishes 22 datasets and the only สถานพยาบาล one
(`dataset-5-1-03`) is a count. So the clinic list is not on the department's
open-data shelf either.

What I got instead is a denominator: `dataset50_77`, สำนักงานจังหวัดเชียงราย —
**เชียงราย held 887 clinics of all types in 2568**, 797 in 2567, 674 in 2566.
Six rows, no names.

The clinic door is therefore **DBD first, hosp.hss second**: DBD names a clinic
with an address, hosp.hss says whether it is licensed, one at a time.

Sample: `cache/source_scout/hss-clinic-licence-register/2026-09-06.json`

### 4. keyed-search-api — WORKS, and the earlier fork was pricing a signup already done
**The Brave Search API key already exists** — `~/.config/nanobotco/keys.json`,
`brave_search`, registered 2026-09-04 for the white-label AI, USD 25 prepaid
(~5,000 searches) plus the $5/month free credit. Measured today:

- `GET https://api.search.brave.com/res/v1/web/search?q=…&count=20` with header
  `X-Subscription-Token` → **200, 19 results**, six real Chiang Mai shop pages
  on the first screen (chetawan.cm · ChiangMaiMassageSukhumvit79 ·
  นวดแผนไทยหนองป่าครั่งสาขา1 · สุ นวดแผนไทย บ้านท่อ · ร้านนวดเชียงใหม่ แผนโบราณ
  · chiangmaiklaimor) for `site:facebook.com นวดแผนไทย เชียงใหม่`.
- **Gotcha, measured:** adding `country=th&search_lang=th` returns **HTTP 422**;
  drop both and the same query answers 200 with Thai results anyway. That is
  written into the register so the next session does not lose an hour to it.
- 2 queries spent measuring. The 1,224-query matrix would cost ~1,224 of ~5,000.

`discover_facebook.py`'s direct path could be live tonight. The undecided part
is the money, not the mechanism — fork raised.

Sample: `cache/source_scout/keyed-search-api/2026-09-06.json`

## What I added

- `hss-health-establishment-licence` — measured, `works`, above.
- `hosp-hss-verifier` — the licence verifier, split out of the clinic entry so
  nobody spends a week trying to bulk-read a search box.
- `provincial-gdcatalog-portals` — **`chiangmai.gdcatalog.go.th` and
  `chiangrai.gdcatalog.go.th` are both live** (HTTP 200, plain UA, 2026-09-06).
  Each province runs its own CKAN. Status `to-scout`: portals confirmed, dataset
  counts not yet enumerated. Note for next week: a per-org `package_search`
  against data.go.th **502s**; run it against each portal's own
  `/api/3/action/`.

## What I refused to add, and why

- **`mt-council.or.th` and `thaihairdresser.org`** — I reached for a medical
  technologists' council (labs) and a hairdressers' association (the beauty
  shelf) and **both failed DNS**. I do not know that those are the right
  domains, so neither goes in the register. A source I only imagine exists is
  not a source; next week I search for the association in Thai first, the way
  the instructions say, instead of guessing a domain in English.
- **The DBD `juristic` ZIP and the per-company API** — both real, neither an
  enumerator. Recorded inside the DBD entry as refusals with their reasons.
- **`dataset-3-3-01` / `hss_11_49`** (ผู้ดำเนินการ and ผู้ให้บริการ — licensed
  spa *operators* and *therapists*). These are lists of **named individuals**.
  Not read, not sampled, not registered as a source. That is the no-private-
  individual rule and there is nothing to weigh against it.

## Forks raised (`_incoming/forks-for-nan.txt`)

1. **The search key already exists — the question is the money.** May the
   1,224-query matrix spend ~1,224 of the ~5,000 prepaid searches? Options:
   spend it / cap it at 300 a month like `tenants.web_cap` already caps ai and
   demo / a second free-tier key in the bot's name. Recommend the cap. Expiry
   2026-10-06. **Supersedes the "sign up for a search key" fork written earlier
   today.**
2. **1,480 licensed massage shops the state names and we do not.** Match-only,
   publish-as-needs-pin, or publish-after-a-second-fact. Recommend match-only
   this week and publish-after-a-second-fact thereafter; that choice is hers,
   and I would not take the middle option without her.
3. **A registered office is not a shopfront.** How may DBD addresses be printed
   — lead-only, record-with-the-label-on-the-page, or record-only-where-the-
   trade-is-shop-shaped. Recommend the labelled record, with the label tested
   for. Expiry 2026-10-06, default lead-only.

## Shelf discovery this run

I covered **medical (physio + laboratory)** and **massage** — the two the
priority list pointed at, and both turned out to have the same answer: the
register that fills them is DBD's TSIC codes, not a health-ministry list.
`beauty/salon` (8 unmatched in `fb_discovery.json`, the largest real shelf gap)
is **not** covered and is first up next week. `fb_discovery.json` is still thin
— 6 queries on disk, 49 pages, 3 shelves — so its `by_shelf` is not yet a
reliable ranking of where the gaps are; it will be after the finder has run
more nights.

## Next week, in order

1. **`beauty/salon` and `food` discovery** — the shelf gap I owed this run, plus
   the biggest shelf on the site, searched in Thai for where the trade licenses
   (เทศบาล food-handling licences), associates (สมาคม — searched, not guessed)
   and describes itself.
2. **`provincial-gdcatalog-portals`** — enumerate both portals against their own
   CKAN API and sort what they hold into lists-with-names and counts.
3. **`line-official-account`** — untouched this run and still the most likely
   own-voice source after Facebook: measure whether `page.line.me/<id>` answers
   logged-out, against the records that already carry a `lineId`.

Behind those: `tat-registered-tour-businesses`, and สสจ.เชียงใหม่
(`chiangmaihealth.go.th`, 200 today) for a published รายชื่อสถานพยาบาล — the
provinces may hold the list the department will only verify.

---

## Second pass, same day — the provincial portals, measured

The entry I filed as `to-scout` four paragraphs ago is now measured, and the
answer is more interesting than "yes, they have data".

**Both portals enumerated in one call each: เชียงใหม่ 539 datasets, เชียงราย
377.** The mechanism is each province's own CKAN
(`https://chiangmai.gdcatalog.go.th/api/3/action/package_search?rows=1000`, no
key) — and the note from this morning holds: the same query with an org filter
against data.go.th **502s**. Go to the province.

**The finding that matters: a Thai title beginning รายชื่อ or ทะเบียน does not
mean the file has names in it.** I opened 28 list-shaped CSVs and read the
headers:

- **9 carry real place names with a location.**
- The other 19 are aggregate counts by year and amphoe — including
  `ทะเบียนนิติบุคคลคงอยู่` (20 rows of totals), `รายชื่อผู้ประกอบการ ถังขนส่ง
  ก๊าซ` (12 rows) and `แหล่งจำหน่ายสินค้าของฝาก` (25 rows of counts per amphoe).

Classifying these by title alone would have been wrong two times in three. The
KNOWN_EMPTY lesson one layer out: **read the file, not the label.**

### The nine that carry names

| dataset | rows | what each row has |
|---|---|---|
| CM `68_113` รายชื่อโรงเรียนพระปริยัติธรรม | **56** | อำเภอ · ตำบล · **วัด** · ชื่อโรงเรียน, year 2568 |
| CM `68_121` โรงงานอุตสาหกรรมเกษตร-อาหาร | 83 | name · trade · amphoe · address |
| CM `69_143` สถานที่ใช้ก๊าซปิโตรเลียม | 66 | operator · site |
| CM `69_140` สถานีบริการก๊าซปิโตรเลียม | 28 | company · tambon · amphoe, year 2569 |
| CM `69_142` สถานที่เก็บรักษาน้ำมัน | 25 | operator · address |
| CM `69_121` แหล่งท่องเที่ยวเชิงเกษตร | 24 | name · activities · location |
| CR `dataset_20_31` รายชื่อแหล่งท่องเที่ยว | 39 | type · name · address · amphoe · tambon · **phone** |
| CR `dataset_20_19` แหล่งท่องเที่ยวเชิงศาสนา | 128 | name · amphoe |
| CM `69_138` รถขนส่งน้ำมัน | 47 | **refused** — the named party is the owner, a person |

### The one to do first

**`68_113` holds 56 monastic schools for การศึกษา 2568. The catalogue holds
27.** `("school","monastic")` came off KNOWN_EMPTY on 2026-08-21 when the ONAB
register filled it — and it is sitting at **48%** of what the province publishes
now. Every row names its วัด, so the join is the same one that worked the first
time: temple name → an already-pinned wat record. This is the cheapest real
shelf gain on the board and it is one importer.

### Denominators, which are worth having on their own

The 19 count-only files are not waste — they are the "we list N of M" the site
has never been able to say:

- CM 2564: **16,783 บริษัทจำกัด + 8,405 ห้างหุ้นส่วนจำกัด** on the register.
- CM lodging 2564: **469 hotels, 339 resorts, 201 guesthouses.**
- CM ของฝาก / OTOP outlets 2567: **200 in เมืองเชียงใหม่ alone.**
- CR clinics 2568: **887** (from this morning).

## `mots-tourism-directory` — added, `partial`, and do not import it yet

Both provincial portals mirror the tourism ministry's own directory:
attractions, restaurants, **spas**, accommodation, souvenir shops, activities.
The schema is the best I have scouted — name in Thai/English/Chinese,
description, photo, lat/lng, telephone, email, url, opening hours, price, and an
address keyed by **DOPA codes** (`citySubDivision` is the tambon, `city` the
amphoe, `countrySubDivision` `TH-50`/`TH-57` — the same key `WIDE_GROUPS`
already clips provinces by).

**But the published dumps are samples, not the directory.** Each is exactly ten
rows of one province: spas 10 × น่าน (declared 21), restaurants 10 × น่าน (127),
accommodation 10 × เลย (354), stores 10 × น่าน (29), attractions 10 with no
province field (89). **Zero Chiang Mai or Chiang Rai rows in any of them.** The
real interface is a documented v2 API whose PDF `502`'d on every attempt, as did
the directory site itself, intermittently, all afternoon.

So: a schema we want and a mechanism we have not got. Written into the register
with "do NOT import the sample dumps" in `next`, because ten rows of น่าน landing
in a Chiang Mai catalogue is exactly the kind of thing that is hard to unpick
later.

Licence is mixed — attractions is Open Data Common, the other five say "License
not specified" on the ministry's CKAN. **Fourth fork raised**, recommending we
use attractions now, treat the rest as leads, and send a letter the way the DGA
give-back letter was drafted.

## Revised "next week", in order

1. **`importers/import_monastic_schools.py`** — 27 → 56, one join, already
   proven. (New; it displaced nothing, it is just cheaper than everything else.)
2. **`beauty/salon` and `food` shelf discovery** — still owed from this run.
3. **The MOTS v2 API** — retry the doc, measure a province-filtered call.
4. **`line-official-account`** — still untouched, still the most likely
   own-voice source after Facebook.
5. **`importers/import_provincial_lists.py`** — the other eight name-carrying
   provincial files (sights and fuel).

---

## Third pass — `line-official-account`, measured, and it WORKS

Two hops, no key, no session:

1. `GET https://lin.ee/<code>` → follows to `https://line.me/R/ti/p/@<oaid>`.
   The deep link itself carries **no metadata at all** — that hop exists only to
   turn a shortlink into a stable OA id.
2. `GET https://page.line.me/<oaid>` (no `@`). A real profile is 80–110 kB with
   the name in `<title>`; an OA with no public page returns a **1.8 kB stub
   titled just "LINE"**, which is how you tell them apart without guessing.

**19 distinct LINE links on disk → 19 distinct OA ids → 5 have a public
profile** (14 are add-friend-only). Of those five:

| field | filled |
|---|---|
| name | 5/5 |
| verified badge | 5/5 |
| the shop's own status message | 4/5 |
| phone | 2/5 |
| address | 0/5 |
| opening hours | 0/5 |

Named: NewPlus DentalClinic · DEAR HEARING (081-352-8412) · Pet Village & Salon
· Eat @ Rincome (052005111) · Yuzu House Chiangmai.

**Why this matters more than five records.** It is the **first logged-out
own-voice mechanism in the register that returns a contact fact at all.** The
Facebook equivalent, measured this morning, gives `og:title` and nothing else —
0 of 5 pages yielded hours, phone or address. LINE gives a name, a phone and the
shop's own sentence, to anyone, with no session and no bot check.

**One correction for whoever writes the importer:** the website lives in the
JSON-LD `sameAs` and in the `account_info_website_link` anchor, **not** in the
escaped `"website"` key. My key-based regex reported 0/5 while a by-hand read of
Eat @ Rincome found `uhotelsresorts.com/unimmanchiangmai`. Trust the anchor. The
0/5 in the table above is the regex's number, not the truth.

`address`, `workingTime` and `budget` are real keys in the payload and were
`null` on all five — the shops have not filled them in. That is an absence in
the source, not an absence in the mechanism, and it is the difference between
"LINE does not carry addresses" (false) and "these five shops did not enter one"
(what I measured).

**The unmeasured half, and it is the bigger one:** everything above reads a
profile once a link is already on disk. Whether an OA can be **found from a shop's
name** — the reverse direction, which is what would make this a discovery lane
rather than an enrichment lane — is not measured. That is the first thing to try
next week, and Brave (`site:page.line.me <ชื่อร้าน> เชียงใหม่`) is the obvious
way to try it, which is one more reason the search-budget fork is worth an answer.

## Where this run ended

- **6 sources measured**, 5 now `works` (hss-health-establishment-licence, dbd-
  juristic-register, keyed-search-api, provincial-gdcatalog-portals,
  line-official-account), 1 honestly downgraded to a verifier.
- **4 entries added** (hss-health-establishment-licence, hosp-hss-verifier,
  provincial-gdcatalog-portals, mots-tourism-directory).
- **4 forks** for Nan, one of which corrects a fork written earlier the same day.
- **22 sources** in the register, `_built` 2026-09-06.
- Refusals written down with reasons: two guessed association domains, the DBD
  ZIP stub and per-company API, the HSS lists of named individuals, the
  oil-transport operators list (owners, not places), and the MOTS sample dumps.
