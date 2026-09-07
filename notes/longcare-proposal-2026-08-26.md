# ดูแลระยะยาว — long-term care: the four questions, the mended shelf, the graded register · WO-32 · 2026-08-26

Nan's ask: "enrich active retirement, convalescence, addiction medicine, and
nursing homes on motdang.net and defiant.to."

Four questions people type as one worried search. This order keeps them apart,
because folding them together is how the family that needs a bed tonight gets
a lifestyle article, and how a person hunting a convalescent bed reads rehab
brochures.

## The measurement — search

Typed at /search before the walk, all of them the way a reader types:

| query | rows | what answered |
|---|---|---|
| nursing home | 2 | the two P.D. records, filed under **Volunteering** |
| บ้านพักคนชรา | 0 | nothing |
| พักฟื้น / convalescence | 0 | nothing |
| assisted living | 0 | nothing (Dok Kaew Gardens existed — as Volunteering) |
| detox / addiction | 0 | nothing (ธัญญารักษ์ answered only its own name) |
| เลิกเหล้า | 0 | nothing |
| retirement | 1 | **Elephant retirement park** |

## The measurement — corpus

20,700 records, both canonical files, whole-record grep, 2026-08-26:
`บ้านพักคนชรา` 0 · `พักฟื้น` 0 · `hospice` 0 · `convalescen` 0 · `detox` 0 ·
`dementia` 0 · `assisted living` 0 · `เนอร์สซิ่งโฮม` 2 (one place, mapped
twice) · `ดูแลผู้สูงอายุ` 2 · `ธัญญารักษ์` 1 · `\brehab\b` 3 (one of them
twice) · `เวชศาสตร์ผู้สูงอายุ` 1.

The care is nearly unnamed here for the same reason as WO-29's knees and
WO-31's psychiatry — and on top of the naming custom sat a **classifier bug**:
`import_overpass.py` filed every `amenity=social_facility` as
community/volunteer and threw the `social_facility=nursing_home|
assisted_living|rehabilitation` subtag away. A nursing home, an
assisted-living garden run by McKean, and the best-known residential rehab in
the province all stood on the volunteer shelf. The cached crawl
(cache/overpass/cm/community.json) held the truth the whole time — eleven
`social_facility` elements, six of them this order's.

## What this walk already fixed (zero network)

1. **The rule, not a list** — `importers/audit_longcare.py` owns
   `longcare_hit()` (one copy, the audit_elephant arrangement);
   `classify()` now files `social_facility=nursing_home|assisted_living|
   rehabilitation`, `group_home` for seniors, `amenity=nursing_home` and
   `healthcare=nursing_home|hospice` as **medical/long-care** before the
   volunteer line. Fenced and witnessed: the orphanages (บ้านร่มไทร,
   บ้านกิ่งแก้ว), the Skill Center (disabled training), Projects For Asia
   (outreach), Baan dol sook (ambulatory — care that visits; left until read).
2. **The shelf** — `long-care` child on the medical tree
   (ดูแลระยะยาว-บ้านพักคนชรา), matching `facilityType=long-care`.
3. **Three merges** — P.D. Nursing Home ×2 (one compound, two mappers),
   The River Rehab ×2 (second node's own note says its location came from an
   OSM note), สวนปรุง OSM/MOPH pair (the WO-25 district-hospital situation).
4. **Two specialty keys** — `geriatric` (เวชศาสตร์ผู้สูงอายุ; bare ผู้สูงอายุ
   never a rule — it is in every senior club's name) and `addiction`
   (ธัญญารักษ์, \brehab\b fenced from Rehabilitation so McKean and the SSO
   workers' centre stay out).
5. **The register** — `data/curated/longcare.json`, grade on every row:
   `mapped` (a mapper's statement; nobody has read the place's own site) ·
   `route` (the door this care ordinarily runs through, unconfirmed) ·
   `stated` (own words, own site — **zero rows hold it and the page prints
   that**) · leads in unread[] with their refs.
6. **The page** — `longcare_layer.py` → /longcare.html: the four sections,
   the grades, the census of silences, the words with RTGS and roots
   (ผู้ป่วยติดเตียง · ญาติเฝ้า · พักฟื้น · เลิกเหล้า), the not-read table.
   Convalescence renders as a census and three real doors, NOT a register —
   there is nothing to register yet, and saying so is the content.
   Active retirement renders as doors to the shelves it actually lives on
   (realestate, community, care.html) — a life, not a bed.
7. **The wiring** — `longcare_band()` on the medical shelf; `longcare`
   search panel (15th); 7 thesaurus groups in search-core (mined, synced,
   parity 528/528 clean).

## The rule this lens runs on

The grade rides every row, and the empty `stated` tier is printed. No
rankings, no named clinicians, no outcome claims, no medical advice. The
addiction section ranks nothing and recommends nothing — each facility
speaks for itself or not at all, and wanting to stop is an ordinary errand,
not a whisper.

## The doors — every fetch awaits Nan's numbered go

1. **The wide `longcare` Overpass group**, both provinces —
   `amenity=nursing_home`, `healthcare=nursing_home|hospice|rehabilitation`,
   `social_facility=*` province-wide (the WO-21/WO-23 wide-group pattern).
   The sibling project's crawl already proves the yield: Helping Hands
   (osm:node/4459060103, with its own site), Kanya (osm:node/4405355467),
   วัยทองนิเวศน์ (osm:way/761166888), ศูนย์ดูแลผู้ป่วยต่อเนื่อง
   (osm:way/1267029609), McKean (osm:way/145954356) — none selected by the
   current groups.
2. **The สบส. licence register** — กรมสนับสนุนบริการสุขภาพ licenses
   กิจการดูแลผู้สูงอายุ; the register would say how many houses the two
   provinces actually hold. (data.go.th harvest on disk holds neither this
   nor the addiction clinics — checked: the 262 ยาเสพติด hits are FDA
   licence categories.)
3. **The DMS addiction-facility register** — ธัญญารักษ์ network and licensed
   สถานฟื้นฟูสมรรถภาพผู้ติดยาเสพติด.
4. **Own-site reads** via `care_targets.json` + `read_care_sites.py`
   (verify-before-believe, snapshots, 7-day staleness): The Cabin, Dawn,
   The River, Dok Kaew/McKean, PD, Helping Hands, ธัญญารักษ์เชียงใหม่,
   สวนปรุง — the rows that would turn `mapped` into `stated`.
5. **The defiant partners.db fold** — zero network in the fetch sense (data
   already on disk from the sibling crawl) but a new import source for
   import_all.py, so it is asked as a door, not slipped in.

## What this order refuses

No "best rehab in Chiang Mai". No cost tables nobody read from a source. No
dementia-care claims off a general nursing-home sign. No amphoe-level
"retirement community" invented from a moobaan name. No hospice row until a
place states the word itself — ประคับประคอง is a department's word, and no
department here has been read saying it.

## defiant.to — done the same day (its own repo, its own conventions)

The rehab bucket in partners/common.py split (physio 7 · addiction 4 ·
rehab 4 · geriatric 11 in the public directory); /retirement/, /recovery/,
/addiction/ built from vault notes at the =Diabetes.md bar (no unsourced
claims, explicit not-read lists); /senior-living/ cross-linked and added to
the site index. Built, QA green, NOT deployed (the wrangler token is dead
since 8/26; cf-sentinel watches).
