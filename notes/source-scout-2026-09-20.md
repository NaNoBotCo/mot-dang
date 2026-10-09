# source-scout — 2026-09-20 (second run)

Three `to-scout` sources measured, one of them the largest yield the register has
ever carried. Two entries added, one existing entry re-measured against two
KNOWN_EMPTY shelves. Two forks raised. No importer written, nothing published,
nothing posted.

Headline: **the Department of Tourism's public licence lookup is an enumerable
register**, and it hands back 1,374 currently-licensed Chiang Mai and Chiang Rai
tour businesses with street addresses, phones and emails — into a shelf tree
that has no shelf for them.

## What I measured

### 1. tat-registered-tour-businesses — WORKS, and it is the biggest door yet

`esvcs.dot.go.th/e-service/LicenseInformationPage` is a Vite SPA; its bundle
names one API host. The search box posts to
**`https://esapi.dot.go.th/api/report/tour-business`** with
`{"full_name": "<text>"}` — no key, no session, no bot check — and **`full_name`
is a substring match**, which is what turns a verifier into a register.

- Five queries (`า` · `ิ` · `ทัวร์` · `ุ` · `เ`) → **5,323 distinct CM+CR licence
  records**. 20–47 MB per call, answered in 2.0–3.6 s.
- **1,374 are currently ปกติ — Chiang Mai 1,200, Chiang Rai 174.** The rest:
  3,463 ยกเลิก, 403 expired, 70 revoked, 13 suspended.
- **35 fields.** On the 2,133-row `ทัวร์` slice: name_th 2133/2133 · name_en 2132
  · address_no 2133 · tambon 2129 · amphoe 2129 · postcode 2133 · **mobile 1742**
  · landline 1012 · **email 1415** · website 275.
- Active CM amphoe spread: เมืองเชียงใหม่ 639 · สันทราย 116 · สันกำแพง 81 ·
  สารภี 72 · หางดง 72 · ดอยสะเก็ด 53.
- Whole-normalised-name match of the 1,374 active against `data/canonical`:
  **131 hit, 1,243 unmatched.**
- **It corroborates against a second state source.** สำนักงานจังหวัดเชียงใหม่
  `dataset_10_344` (fetched today, and a count file, not a list) says Chiang Mai
  held **1,128** licensed tour businesses in 2567. I count **1,200** active. Two
  offices, two methods, the same number — which is the first time a yield in this
  register has had an independent check on it.

**Two fields are a private individual's and I stripped them before writing
anything to disk:** `identity_no` is a 13-digit Thai national ID and
`requester_name` is a natural person — **1,569 of 2,133** rows in one slice were
`requester_type: person`. They are named in the register entry as never-store.

**Refused on the same API, deliberately:** `/report/guide` and
`/report/tour-leader`. Those enumerate licensed **guides** and **tour leaders**,
who are people, not places. Not called, not sampled, not registered as a source.

**And the finding that stops it being an import:** `data/categories.json` has 28
shelves and **none of them is tour agencies**. The nearest is `sights/community`
(ชุมชนท่องเที่ยว), which is community tourism — a different thing. So this source
is measured, it works, and it has nowhere to land. Fork raised.

Sample (personal fields stripped):
`cache/source_scout/tat-registered-tour-businesses/2026-09-20.json`

### 2. instagram-business — PARTIAL, identity only, and that is the whole answer

Measured the way the LINE lane was: against handles **we already hold**, not
against guesses. `data/canonical` + `curated/enrich.json` carry **492 distinct
Instagram handles**. Five read logged-out with our own UA:

- **5/5 HTTP 200. No login wall, no challenge, no browser impersonation needed.**
- `og:title` 5/5 and `og:description` 5/5 — but og:description is *follower,
  following and post counts*, not the bio.
- **0/5 address · 0/5 phone · 0/5 category · 0/5 bio · 0/5 hours.** `biography`,
  `business_phone_number`, `business_address_json`, `category_name`,
  `external_url` and `is_business_account` appear **zero times** in ~700 kB of
  HTML. The old `?__a=1` JSON endpoint is gone.
- 3/5 carry a non-empty display name; two shops never set one.

So Instagram logged-out sits **between** the two Facebook lanes: it answers where
`facebook-page-logged-out-fetch` returns HTTP 400, but it returns no more than
Facebook's `og:title` did. **No enrichment importer** — it would write nothing we
do not already hold. Its one use is confirming a handle still exists and what the shop currently calls itself.

Sample: `cache/source_scout/instagram-business/2026-09-20.json`

### 3. thai-yellow-pages — PARTIAL: a profile reads, a listing does not enumerate

- A profile page fetches at **200, 132 kB**, plain UA, and **robots.txt permits
  it** — the only relevant `Disallow`s are `/search/` and `/profiles/` (the
  Drupal code directory, not the listings).
- One profile read end-to-end: name, หมวดหมู่, **full address to tambon and
  postcode**, phone, fax. **No JSON-LD anywhere on the page** — every fact has to
  come out of rendered Thai text. No coordinates, no hours.
- Enumeration, two doors, both measured: `/ypsearch?keyword=…` **302s back to the
  home page** (the form needs the site's own JS), and `/heading/<Thai category>`
  answers 200 **with a province filter and a pager** but serves **zero
  `/profile/` links** in the HTML — the rows are drawn client-side. No
  `sitemap.xml` (404).

Leads only, one at a time, behind a name we already hold. Not worth a browser
session: its best field is the address, and DBD and the DOT register both carry
that first-hand.

## What I added

- **`cdd-otop-producer-register`** — measured, `works`. กรมการพัฒนาชุมชน's
  ทะเบียนผู้ประกอบการ OTOP (data.go.th `otop45`), one 22 MB CSV, no key, Open
  Data Common, published yearly (2024 / 2025 / 2026 editions side by side).
  **98,177 rows nationwide; เชียงใหม่ 2,217 · เชียงราย 2,210 = 4,427**, and
  **every single one carries อำเภอ and ตำบล**. Six columns only — no street
  address, no phone, no coordinates, no product.
  I counted the **name shapes**, because they decide what may be used at all:
  กลุ่ม… 1,182 · วิสาหกิจชุมชน… 432 · institutional 189 · juristic 169 · ร้าน…
  132 · **a personal title (นาย/นาง/นางสาว) 569** · other 1,754 — mostly trade
  names (P.DESIGN, สไบทอง, ทิพย์สมุนไพร, ฝ้ายละอ่อน, เป่าแก้วศิลป์เชียงใหม่) but
  with bare personal names among them. **The 569 are refused by rule**, and the
  gate has to test the NAME, not the ลักษณะ column: 2,297 rows are filed as sole
  producers and most of those still trade under a shop name.
  Sample: `cache/source_scout/cdd-otop-producer-register/2026-09-20.json`
- **`dataforthai-tsic-directory`** — `blocked`, 0 rows. A commercial directory
  over the DBD register, browsable by TSIC code. **403 to our own UA** while its
  robots.txt permits everything but `/api/` — the block is the server, not the
  policy, and we do not dress a script up as a browser. Recorded so nobody
  rediscovers it; it is second-hand anyway.

## Shelf discovery this run

**`shopping`** (259 unmatched in `fb_discovery.json`, the largest gap, uncovered
before) — where it licenses: DBD by TSIC 47xxx, already in the register. Where
it **associates**: the OTOP producer register above, which is the craft and
fabric half of that shelf and is now measured at 4,427 CM+CR producers with a
tambon each. Where the **city** lists it: the ของฝาก/OTOP outlet counts already
noted from the provincial portals (200 in เมืองเชียงใหม่ alone, 2567).

**`("home-services","handyman")` and `("home-services","housekeeper")`, both on
KNOWN_EMPTY** — and the answer is the WO-22 lesson one layer further out. Those
two shelves sit there reading "1 name hit in 24,000" and "46 name hits for
รับซ่อม, every one a…", which is **true about shop names and false about the
trade**: a cleaner or a builder in this city does not put แม่บ้าน or ช่างซ่อมบ้าน
on a sign, it registers a company under an **objective code**. Measured in three
months of DBD (2568-06/07/08, 1,156 CM+CR rows):

| TSIC | trade | rows, 3 months |
|---|---|---|
| 81210 | การบริการทำความสะอาดทั่วไปของตัวอาคาร | 10 |
| 43210 | การติดตั้งไฟฟ้า | 9 |
| 43223 | ระบบระบายอากาศ / แอร์ | 4 |
| 81293 | กำจัดปลวกและแมลง | 2 |
| 95220 | ซ่อมเครื่องใช้ในบ้าน | 1 |
| 43299 | งานติดตั้งเฉพาะทางอื่น | 1 |

Named, off the rows: หจก.นอร์ท คลีนนิ่ง (81210, ต.นางแล, เชียงราย) ·
บจ.พรีเมียมสะอาด (81210) · หจก.กฤษณา ริด เทอร์ไมท์ (81293, อ.แม่อาย) ·
หจก.999 วอเทอร์ เซอร์วิส (95220). At ~9 a month the 55-month archive is on the
order of **400–500 CM+CR home-services firms** — and `home-services/pest-control`
has 22 unmatched leads waiting in `fb_discovery.json` as well.
**Those two KNOWN_EMPTY reasons should be re-read the day `import_dbd.py` runs.**
I have written that into the DBD entry rather than editing `test_facets.py`:
the list comes down when the shelf fills, not when a bot predicts it will.

## What I refused to add, and why

- **`/report/guide` and `/report/tour-leader`** on the DOT API — licensed guides
  and tour leaders are natural persons. Not called, not sampled, not registered.
- **`identity_no` and `requester_name`** from the tour register — a 13-digit
  national ID and a person's name, on 1,569 of 2,133 rows in one slice. Stripped
  before the cache sample was written, and named as never-store in the entry.
- **The 569 OTOP rows beginning นาย/นาง/นางสาว** — named individuals, and the
  bare personal names in the 1,754 "other" bucket with them.
- **`dataforthai.com`** — 403 to our own UA, declared. Registered as blocked rather than
  worked around.
- **Thai Yellow Pages `/heading/` bulk** — reachable only by driving a browser
  through client-rendered listing pages, for an address two better sources
  already carry first-hand.
- **A cleaning-trade association** — I searched in Thai for
  สมาคมผู้ประกอบการทำความสะอาด and found no association with a member list, only
  companies and directories. Last week I wrote down two association domains I had
  guessed and both failed DNS; this week I searched instead, found nothing real,
  and am writing down the nothing. A source I only imagine exists is not a source.

## Forks raised (`_incoming/forks-for-nan.txt`)

1. **1,374 licensed tour operators, and no shelf to put them on.** New top-level
   shelf / a child under sights / verify-and-enrich only / nothing. Recommend
   verify-and-enrich now; I would not open a tour-agency shelf without her.
   Expiry 2026-10-20, default nothing. Carries a smaller question inside it: the
   3,949 cancelled and expired licences — my answer is that they are history and
   never render, and I would not print "licensed until 2020" about a trading
   business without her.
2. **The tour register publishes no reuse terms at all.** Read the silence as
   open / verify-only / write and ask. Recommend reading it as open AND writing —
   and answering it together with the 2026-09-06 tourism-ministry fork, because
   it is the same silence from the same ministry.

## Next week, in order

1. **The MOTS v2 API** — still owed from 2026-09-06, and it is the only source
   scouted with coordinates, hours and a price in one schema. `ckan.mots.go.th`
   502'd all that afternoon; retry the doc.
2. **`line-official-account`, the reverse direction** — can an OA be found FROM a
   shop's name, rather than only read once a link is on disk? That is what turns
   the one working logged-out own-voice lane from enrichment into discovery, and
   it needs the search-budget fork answered.
3. **เทศบาลนครเชียงใหม่'s own licence lists** — ตลาดสด and food-handling
   (สะสมอาหาร) licences, a different office from both provincial portals, and the
   `food` shelf (174 unmatched) is the biggest on the site. Never reached.

Behind those: สสจ.เชียงใหม่ for a published รายชื่อสถานพยาบาล, and
`lazada-shopee-storefront`, which is still `to-scout` and still waiting on the
policy question of whether an online-only seller gets a shelf at all.
