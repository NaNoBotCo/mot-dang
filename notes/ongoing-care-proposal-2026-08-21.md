# ดูแลต่อเนื่อง — ongoing care: the patient who stays, and the paperwork that follows her

*2026-08-21. Nan, walking her own case through her own site: "Can my own search
and GIS directory help me find specialized ongoing care?… Another thing that
interests 'good' farang tourists is a provider's ability to fill out US
insurance/FMP/ChampVA paperwork with little-no assistance. And on the thai
side, paperwork, patient plans, and ongoing service for medical DTVs is very
important. We need to enrich throughout from this lens. I'm a foreigner paying
mostly out of pocket in thailand for a lifelong condition that I manage better
here than at home." This note is the measurement, the rule, and the shape.
Read with `MARCHING-ORDERS.md` WO-25.*

*Privacy fence, stated up front: her personal case stays HERE, in notes/,
which `emit_source()` does not ship. Everything that reaches data/ or a page
is a fact about a FACILITY — what a desk states, what a site posts — never a
fact about a patient. That fence is why this order can exist at all.*

## The measurement — search, before any change

Every query below was run through the shipped search block against the built
index (2026-08-21 build, 18,679 places), the same harness as
`tests/test_search.py`. What a person managing a long condition actually
types, and what came back:

| She types | She got |
|---|---|
| `cardiologist`, `tachycardia`, `dysautonomia`, `syncope` | **0 results.** Hard zeros. |
| `menopause`, `endocrinologist`, `insurance`, `FMP`, `DTV` | **0 results.** |
| `cardiology` | 1 loose match: **Radiology** (an edit-distance cousin). |
| `POTS` | The cannabis dispensary "POTS (People Of The Sun)", exactly matched. A true namesake — the medical reading has no door to win against it. |
| `วัยทอง` | 2 loose rows — a รพ.สต. named **วังป้อง** (edit-distance again) and its temple. |
| `ฮอร์โมน`, `ฮอร์โมนทดแทน` | 436+ partial rows led by **Rock Me Burger** (the segmenter finds ร-โมน pieces everywhere). |
| `หัวใจเต้นเร็ว`, `โรคหัวใจ`, `หมอหัวใจ` | 633–2,140 partial rows of fried meatballs, dental clinics and pharmacies named ใจ. |
| `heart doctor` | 590 rows led by **Heart Dental Clinic** — the name field outranks everything (the known weight gap from the women's-health order). |
| `อายุรกรรม` (internal medicine — THE ongoing-care department word) | 2,522 partial rows: home-economics faculties, schools, cannabis research. |
| `ใบรับรองแพทย์` | 2,107 partial rows led by a pharmacy named สามใบเถา. |
| `เคลมประกัน` | 1 row: a school. |
| `CHAMPVA` | **Duang Champa hotel**, loosened. |
| `tilt table` | Table-tennis clubs. `holter` → hotels. |
| `international clinic` | The right dental centre — under the **ELEPHANT door** (see below). |
| `gynecologist`, `นรีเวช` | ✓ **43 rows, OB-GYN clinics on top, women's-health door opens** — the one lens already built (the women's-health order), and the proof the cure pattern works. |
| `กายภาพบำบัด`, `physical therapy` | ✓ 12 physio places. `rajavej` ✓ exact. `lab` ✓ 29 (top rows noisy). |

Two findings that are bugs, not gaps: **the mined shelf table maps the bare
word `clinic` → `['chang']`** (lifted from the "elephant clinics & hospitals"
child's English name), so every clinic-shaped query lifted elephant camps and
opened the elephant door over people-medicine. And the loose tier's
cross-domain cousins (cardiology→radiology, CHAMPVA→Champa) are working as
designed but say the tier out loud — livable once real doors exist.

## The measurement — corpus

The search cannot say what the data does not hold. Scanned all 19,975
canonical records:

- **Zero** records anywhere carry: วัยทอง/menopause · ฮอร์โมน/hormone ·
  ต่อมไร้ท่อ/เบาหวาน/ไทรอยด์ (endocrine, diabetes, thyroid) ·
  อายุรกรรม/internal medicine · ตรวจสุขภาพ/checkup · ประกัน/insurance.
- **One** medical record carries the word heart — a dental clinic. The
  `heart` specialty key exists in `importers/specialty.py` since the
  women's-health order and **no record in either province earns it.**
- Specialty coverage overall: dental 72 · general 18 · skin 13 · everything
  else single digits, out of 2,068 medical records.
- **154 hospitals** (non-รพ.สต.), and nearly every one is **contactless** —
  no phone, no site. Rajavej, her own hospital, is a name and a pin:
  no phone, no address, no hours. Bangkok Hospital CM appears **three times**
  (one copy has contact, two don't); Fang Hospital **four times**; a café
  ("Kew Mar Pan Café") is filed as a hospital; animal hospitals sit in
  `medical` and interleave every "hospital" search.
- What the corpus DOES hold, thinly: 3 neuro records (incl. the neurological
  hospital), 3 labs, 12 physio, the OB-GYN 43. The bones of the lens exist;
  the flesh was never crawled — **OSM maps buildings, and specialist ongoing
  care lives in DEPARTMENTS.** Sriphat's menopause clinic, Suan Dok's
  อายุรกรรม, Bangkok Hospital's heart centre: none of these will ever arrive
  by Overpass. They arrive the way the elephant register arrived: read from
  what each institution states, with the source and the date attached.

## What this walk already fixed (2026-08-21, zero network)

1. **`shelf_stops`** — new top-level key in `data/curated/search_panels.json`
   + a per-word guard in build.py's lift: `clinic` no longer lifts or doors
   the elephant shelf, while `elephant clinic` still does (the stop is per
   word, not per shelf). The lasting mend is a generic-institution-word rule
   in search-core's `shelves_motdang()` — filed in `search-core/SEARCH.md`
   Known gaps for the rollout lane.
2. **The women's-health door now answers the menopause reader**: panel
   variants gained `menopause · วัยทอง · hrt`, query substrings gained
   `menopause · วัยทอง · ประจำเดือน · ฮอร์โมน · hormone`, and the panel
   carries a วัยทอง fact chip. The glossary on /womens-health.html gained
   **คลินิกวัยทอง** (the sign and the desk word to ask for) and
   **ฮอร์โมนทดแทน** (HRT). A reader typing `menopause` — zero corpus rows —
   now gets the curated page instead of silence: the exact cure the
   women's-health order proved.
3. **`tests/test_search.py` 26 → 31 cases**, all green: the three new doors,
   the elephant-door guard, and the per-word stop each hold a case.
4. **Two reader questions staged** in the asked machinery (draft:true, render
   nowhere until the fieldwork fills them): `us-insurance-paperwork` — which
   hospitals issue itemized English receipts and complete FMP/CHAMPVA forms —
   and `dtv-medical` — where a medical-DTV treatment plan and hospital letters
   come from, and who keeps them current. Notes files opened for both.

## The rule this lens runs on

The elephants' rule was *the venue states and nothing ranks it*; the springs',
*the measurement carries its source*; the women's-health order's, *stated kept
apart from likely*. Here:

**The desk states; the paper carries its date; nothing is awarded.**

A hospital that says "we complete FMP claim forms" is quoted, sourced and
dated — never scored. A checkup package renders at its posted price with the
spread, `_pricesVerified: false` until a person stands at the counter. A
clinic roster is the hospital's own published list, fetched on a date. No
"best hospital for X", no named doctors, no medical advice, and the register
never gates: everything it knows is on the open page in both languages.

## The shape

1. **`data/curated/care.json`** — the care register, one entry per facility
   that states something, every field carrying `{source, fetched}`:
   - `clinics`: the departments the institution itself lists —
     `heart` · `menopause` (คลินิกวัยทอง) · `endocrine` (เบาหวาน-ไทรอยด์) ·
     `internal-med` (อายุรกรรม) · `neuro` · `physio` · `lab` · `checkup`
     (ศูนย์ตรวจสุขภาพ) — keys shared with `specialty.py` so search, page and
     place-band cannot disagree.
   - `paperwork`: `english_itemized_receipt` · `us_claim_forms`
     (FMP · CHAMPVA · CMS-1500) · `direct_billing` (named insurers) ·
     `intl_desk` {phone, email, LINE}.
   - `visa`: `dtv_treatment_plan` · `extension_letters` — the Thai-side
     paper a medical DTV lives on.
   - `continuity`: named-doctor booking · เวชระเบียน in English · telemed
     follow-up. And the quiet one that matters out of pocket:
     **คลินิกพิเศษ/นอกเวลา** — the after-hours special clinics where the
     same specialist sees you for a posted flat fee.
   - `packages`: posted checkup/lab prices, spread kept, verified flag.
2. **`care_layer.py` → `/care.html`** — the womens-health pattern: the
   register table with stated-vs-silent marked on every row, and a glossary
   of the sign words (อายุรกรรม · เฉพาะทาง · คลินิกพิเศษ · ใบรับรองแพทย์ ·
   เวชระเบียน · ใบเสร็จ · เคลมประกัน · ศูนย์…), Thai script · RTGS · gloss,
   because the department board in the lobby is in Thai.
3. **Search doors AFTER the page exists** (the panels rule): a `care` panel
   for cardiologist · อายุรกรรม · checkup · insurance · FMP · DTV-shaped
   queries; the POTS/heart family doors here too — the true answer for a
   0-row specialist query is this page.
4. **Place-page band** on every facility the register knows (the
   whats-on-here pattern), and the claim flow already lets the hospital's own
   desk correct its contact row.
5. **GIS**: the register's anchors as a drawn map on /care.html (the
   namphuron no-tile pattern), near-me sort already client-side; care anchors
   join /map.html when WO-20 Phase 3 opens.

## The doors — every fetch awaits Nan's numbered go

1. **Hospital site reads** (~18, the enrich_sites/check_links manners):
   Rajavej · Bangkok Hospital CM · CM Ram · Lanna · McCormick · Sriphat ·
   Maharaj/Suan Dok · CM Neurological · Central Memorial · CMC · Nakornping ·
   Klaimor · Chiangmai Hospital · Thanyarak · (CR) Overbrook · Kasemrad
   Sriburin · CR Prachanukroh · Mae Fah Luang — clinic rosters, intl/insurance
   desk pages, package prices. This is where heart goes 0 → real.
2. **The official DTV medical-stream page** (MFA/Thai eVisa) — one fetch; the
   visa column renders from the government's own checklist, dated.
3. **VA FMP provider documentation** (va.gov) — what a Thai hospital must
   produce for FMP billing; CHAMPVA overlap noted from household experience,
   kept as her field knowledge, sourced to the VA pages.
4. **Contact-vigor pass on the care anchors** — the "contact is the currency"
   rule finally applied to medical: 154 hospitals, nearly all silent. Some of
   it is her own phone book, walked provenance (Rajavej's front desk number
   is in her notes and not in her directory).
5. **Medical shelf hygiene** (zero network, next order): fold the duplicate
   hospitals (Bangkok ×3, Fang ×4, Chomthong ×2…), unfile the café, and give
   "hospital" queries the namesake split so animal hospitals stand under
   their own header.
6. **search-core mend** (rollout lane): the generic-institution-word rule in
   `shelves_motdang()`, eval queries for both readings of คลินิก.
7. **The desk sheet** — a bilingual one-page instrument (the hair-words.pdf
   precedent): the seven questions above, printed, so any desk visit — hers,
   a reader's — comes home as dated field truth. Building the sheet is a
   maker-bot job; the walking is hers, at her own pace, starting wherever
   she is already a patient.

---

# The doors walked — 2026-08-21, same day, on her numbered go ("start with 1 and move down")

## Door 1 — the hospital site reads. DONE, and the thesis landed on her own hospital.

`importers/read_care_sites.py` + `data/curated/care_targets.json` (20 targets,
candidate urls in preference order). **It verifies before it believes**: a
candidate counts as the hospital's own site only when the fetched page carries
one of that target's own names. Guessing domains is unavoidable here — most
care anchors carry no website in the crawl at all — so the guess is checked
rather than trusted. **49 of 77 fetches landed; 13 of 20 targets verified.**

**The find: Rajavej — her own hospital — publishes a TRICARE and FMP page.**
Not a mention: its own page, with a named desk, an email
(chairat.n@rajavejchiangmai.com), and an extension (052-011-999 ext 121). The
hospital states the desk is staffed by a retired US Army member with over
eleven years advising on TRICARE and FMP in Thailand. The directory held this
hospital as **a name and a pin** — no phone, no site, no address. It now has
all three, plus a department board.

**And the department board answers the POTS/menopause question directly.**
Rajavej states **คลินิกโรคหัวใจ** (heart clinic, Tue 17.00–19.00, Sat
13.00–15.00) and **คลินิกต่อมไร้ท่อ** (endocrine — thyroid, diabetes, hormones,
Mon 17.00–19.00), plus อายุรกรรมทั่วไป daily 08.00–20.00, สูติ-นรีเวช,
ระบบประสาทและสมอง, กายภาพบำบัด, ตรวจสุขภาพ. **The `heart` key in
`importers/specialty.py` had zero members in the entire corpus.** It has
members now, and they are stated, sourced and dated.

The evening hours are the finding under the finding: **คลินิกพิเศษ / นอกเวลา**,
the same specialists seeing patients after government hours for a posted extra
fee, is a whole tier of Thai healthcare that is almost never printed in
English. CR Prachanukroh states its SMC clinic runs **Mon–Fri 16.00–20.00 and
weekends from 08.00**; Suan Dok publishes separate after-hours switchboard
lines; Chiangmai Hospital lists a whole คลินิกพิเศษ roster; Overbrook names
คลินิกนอกเวลา. That phrase is now the delight line on the search door.

Register: **`data/curated/care.json` — 7 hospitals read, 38 stated facts, 11
recorded unread.** Every claim carries the sentence it was read from, the URL,
and the date.

**Two silences kept as silences.** (1) The Kasemrad chain site lists 73 centres
across ten branches behind a client-side picker, and its package prices are
tagged ปทุมธานี — reading that as the Sriburin branch's departments would
invent facts about a named hospital, so **no clinic claim is made at all**.
(2) Bangkok Hospital CM and CM Neuro verify as themselves but build their
content in the browser; recorded as readable-only-with-a-browser, not as empty.

## Door 2 — the official DTV page. BLOCKED, and the block is published.

All three official sources are unreadable to a plain fetch: **thaievisa.go.th
is a React shell** (117 characters of fallback text), **consular.mfa.go.th the
same** (55), and the MFA content path answers with navigation only — the words
*Destination*, *DTV* and *medical* appear **zero times**. So the register
carries **no visa requirements at all**, says it could not read them, prints
what it tried and what came back, and sends the reader to the portal. Writing
visa rules from memory is the exact failure `[[feedback_dont_hallucinate_rules]]`
exists to prevent, and a directory whose thesis is bot-legibility should say
out loud when a government's own page cannot be read by one.

## Door 3 — VA FMP. DONE, read first-hand.

va.gov's FMP page (fetched 2026-08-21; **the page states it was last updated
2026-08-06**) yields the mechanism, quoted not paraphrased: FMP covers care for
a **VA-rated service-connected** condition (or one associated with it that
makes it worse), **only outside the US**, and **the paper that matters is the
FMP benefits letter** — from VA.gov under Letters → Benefit letters and
documents — which you **hand to the provider and ask them to file the claim**.
If they don't, you file yourself. Any licensed provider in-country is eligible.
Recorded as read, never as advice. Noted plainly: the VA lists toll-free FMP
lines for a handful of countries and **Thailand is not among them**.

## Door 4 — contact vigor. DONE as a by-product.

The register carries the desk contacts the reads produced: Rajavej 052-011999 +
the FMP desk email and extension + its street address; Chiangmai Hospital
053-225222 / info@; Nakornping 053-999200 / info@; Chiangmai Ram 052-004601;
CR Prachanukroh 053-910600; Suan Dok's records office (053-935636), social
security (053-935170) and after-hours lines. Also corrected: **two stored
"official sites" are wrong** — mccormick.in.th no longer resolves, and
mflhospital.com now answers as somebody else's page.

## Door 5 — medical shelf hygiene. DONE, zero network.

27 merge pairs into `data/curated/merges.json` and 4 retags into
`data/curated/retags.json`, each with its receipt, folded by `import_all.py`:

- **The duplicate hospitals**: Bangkok CM ×2 → 1, Fang ×4 → 1, Lanna's three
  buildings → 1 campus, Chiang Khong ×3 → 1, plus 20 more district hospitals
  that were each in the catalogue twice — once from OSM, once from the MOPH
  open list. The keeper is whichever record holds the better facts; two
  (San Kamphaeng, Mae On) keep the **MOPH** record instead, because the OSM
  name carries a โรงพยาบาน typo.
- **The café filed as a hospital** — Kew Mar Pan Café. Its own crawled
  description reads **"First aid room"**: a first-aid point at a mountain-road
  café, typed healthcare, sitting on the medical shelf.
- **Three vets on the people-medicine shelf** — an unnamed "animal hospital",
  คำเที่ยง รักษาสัตว์, and โรงพยาบาลสัตว์แม่ออน — moved to `pets/vet`, which is
  what was interleaving every "hospital" search.

## Door 6 — the search-core mend. DONE at the root.

`shelves_motdang()` mined `clinic` → `['chang']` out of the chang teaser's own
English prose ("…the elephant clinic, poo paper…"): `words_en` split the phrase
and a bare premises word became a shelf key. `GENERIC_PREMISES` now drops bare
premises words (clinic, hospital, centre, school, office, service…) mined from
English teaser PROSE, while a shelf whose **own name** is one of them keeps it —
"Elephant Clinics & Hospitals" is entitled to say so. The Thai side never had
the bug, because คลินิกช้าง is one compound and does not come apart.
Mot Dang's `shelf_stops` guard stays as belt and braces.

## Door 7 — the desk sheet. Next; the register is its content.

Not built this pass. The register now holds the questions worth printing, and
`make_reader_sheets.py` is the instrument (the `/reader/hair-words.pdf`
precedent from WO-22).
