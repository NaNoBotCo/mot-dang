# document-prep — เอกสารที่ต้องแปล รับรอง หรือทำเรื่องวีซ่า ไปทำที่ไหนในเชียงใหม่ ต้องเตรียมอะไรบ้าง

*Where do I get a document translated, legalized or a visa form prepared in Chiang Mai, and what do I bring?*

- asked_on: 2026-09-04
- via: other (Nan's enrichment ask — "copy shops and document preparation services")
- status: BUILT 2026-09-04 (WO-54). Sister question: `asked-copy-print-2026-09-04.md`.
  The seal half already has its own page (`asked-notary-2026-08-28.md`) and is
  linked, not restated.

## Three trades, one English phrase

"Document preparation" in a farang's mouth is three counters:

1. **The immigration errand** — TM.7 extension, TM.47 90-day report, TM.30
   residence notice. Done by the reader at immigration; the copy shop at the
   gate makes the copies and fills the form (`formhelp`). A paid agent who
   files it (`visaagent`) is a courier; the state fee does not change.
2. **Translation** — a certified translation (`certtrans`) from a translation
   counter. CMHY lists 15 under รับแปลเอกสาร; **3 are language schools**
   (อิจิบัง, พจนศึกษา, NILC) and are refused, not re-shelved. Most of the rest
   carry วีซ่า in their tags: the translation and visa-consulting trades share
   a desk here.
3. **The seal** — MFA legalization (นิติกรณ์) or a Lawyers Council notarial
   attorney. WO-40's page; one door on this page points there.

## The doors, read from their own pages

- **Chiang Mai Immigration, main office** — 71 M.3 Airport Rd, Suthep, 50200;
  Mon–Fri 08:30–16:30; 1178 / 053-277-190. Source:
  chiangmai.immigration.go.th (address) · CMHY /place/30685 (hours, GPS
  18.7682625, 98.9679190). OSM way 822791365 already in the catalogue.
- **Chiang Mai Immigration, Central Chiang Mai (Central Festival) 2nd floor**
  — opened **2022-06-06**; Mon–Fri 09:00–17:00; short extensions, 90-day,
  TM30, re-entry. Source: CMHY /place/32420 (2026-09-04); CMU Business School
  visa sheet (Nov 2022) names both offices and both hour sets. OSM node
  12619518873 "Chiang Mai Immigration (2nd floor)" at 18.8070, 99.0182 — that
  IS Central Festival; `enrich.json` now gives it its Thai name, hours, phone.
- **Promenada branch CLOSED** — "moved back to the main office as of March 25,
  2020" per CMHY /place/5449 (dateModified 2022-06-06). Half the English web
  still sends readers there; the page says so.
- **Chiang Rai Immigration** — main office 117 M.10 เวียงพางคำ, แม่สาย,
  053-731008 (OSM node 2193469948). **City branch moved 2023-09-18** from the
  PAO to **Central Chiang Rai, G floor, "next to the Passport Office", Robinson
  side**, Mon–Fri 08:30–16:30, ext. 14 — chiangrai.immigration.go.th, its own
  announcement. No OSM record → `cr-curated-immigration-central-chiangrai`,
  pinned at the passport office (way 401955473), `geoPrecision: approx`.
- **TM.7 form** (bangkok.immigration.go.th, 2021 PDF, read with pdftotext):
  "รูปถ่าย ขนาด 4 x 6 ซม. / Photograph 4 x 6 cm." and "APPLICATION FEE IS NON
  REFUNDABLE UNDER ALL CIRCUMSTANCES". **Fee page** (Immigration Division 1,
  curl 2026-09-04): "Extension for Visa 1,900 baht · Re-Entry Permit Single
  Entry 1,000 baht · Multiple Entry 3,800 baht". WebFetch gets 403 on both
  immigration.go.th pages; curl with a browser UA reads them.
- **Translation prices** (`_pricesVerified: false`):
  - Centa Care, 8/39 M.1 Soi 8 Chang Khian Rd, Chang Phueak — "English to
    Thai : 350 THB/page (approx. 200 words)", "Legalization / Authentication
    service at Consular Department, MFA: Starts from 1800 Baht per page",
    "Notarial Services Attorney Starts from 1,000 Baht / Page". centa-care.com
    · 2026-09-04.
  - JSN Translation, Mae Rim — "เริ่มต้นที่ 300 บาท" for ID/house registration,
    "500 บาทขึ้นไป" multi-page official. jsntranslationservice.com · 2026-09-04.
  - Chiangmai Translation Service, 134 ถนนโชตนา, 053-215602, Mon–Sat 08:00–17:00
    — no prices; states foreigner marriage registration, MFA/embassy
    certification, Non-O and retirement visa help. cmt-translation.com · 2026-09-04.
  - MFA seal 200 / 400 express — WO-40's info.go.th source, not re-fetched.
- **Chiang Rai translation**: OSM holds exactly one — บ้านแปลภาษา, node
  9847655396 (`office=translation`, crawled today). Every web page titled
  "แปลเอกสารเชียงราย" (KTP /store/p27, NYC, Exact, AMKO, masterpiece) is a
  Bangkok firm; masterpiecetranslation.com's "Chiang Mai" page carries a
  Bangkok address too. Recorded as the finding, not as records.
- **VFS Global** — `office=visa`, OSM node 6235387371, now on `essentials/visa`
  via the new classify rule. It is an outbound-visa application centre, not
  a Thai-visa agent; the shelf label covers both and the record's own name
  says which.

## Second pass

- **Nine CMHY translation/visa counters now have records with street, phone,
  GPS and (for most) hours** — the lenient JSON-LD read above recovered them:
  ลานนาการแปล (ถ.อินทวโรรส), ไทยเฟิร์ส (ตรงข้ามวัดอุปคุต ถ.ท่าแพ), เอเชีย
  (4/4 ถ.อินทวโรรส), สตาร์วีซ่า ×2 (ถ.วิชยานนท์ / โครงการเชียงใหม่บิสซิเนส), มีเดีย
  (ถ.ท่าแพ), โซลชายน์ (ถ.วิชยานนท์), ฤทธิชัย ทนายความ (ถ.ท่าแพ), ไนท์ วีซ่า
  (โครงการปันนา ถ.ห้วยแก้ว, `visa`). **Tha Phae / Inthawarorot is the
  translation quarter** — four counters on two streets — which is the one
  trade in this order that DOES cluster, because the customer is a walk-in
  with a paper in hand, not an office with a gate.
- **Modus Language Services** (72/3 ถ.ทิพย์เนตร หายยา, Mo–Fr 09:30–17:30) from
  its own site; no GPS published → `needs-pin`. Centa Care and Chiangmai
  Translation Service lend their pins from the CMHY rows and keep their
  first-hand sources.
- **Photo sizes by country** on the page: TH 4×6 cm (TM.7), UK 45×35 mm /
  head 29–34 mm / last month (gov.uk, fetched), US 2×2 in / 6 months
  (travel.state.gov 403 to both WebFetch and curl; the page says so and
  tells the reader to confirm there).

## Open

- **A photo of the Central Festival immigration counter** and one of Central
  Chiang Rai G floor: the two records most readers will actually walk to.
- **One translation receipt** — turns 350/page into a walked price.
- **บ้านแปลภาษา (CR)**: phone and hours are blank on OSM; one call or walk.
- **The visa-agent trade in CM** (ไนท์ วีซ่า, สตาร์วีซ่า ×2, โซลชายน์, เจอนี่ เควสท์)
  is on the `translation`/`visa` shelves by their own tags; whether any files
  TM.7 on a reader's behalf is a door-survey question (`visaagent`), asked,
  never assumed.
