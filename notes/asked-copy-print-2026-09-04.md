# copy-print — ถ่ายเอกสาร ปริ้นงาน เข้าเล่ม ใกล้ฉันที่ไหน ร้านไหนเปิดดึก ปริ้นจากมือถือได้ไหม

*Where can I photocopy, print from my phone and get a report bound — and which shops are open late?*

- asked_on: 2026-09-04
- via: other (Nan's enrichment ask — "copy shops and document preparation services")
- status: BUILT 2026-09-04 (WO-54). Sister question: `asked-document-prep-2026-09-04.md`.

## What the measurement said

The directory held **zero** copy shops in 20,700 records. Not thin — absent,
and for the WO-50 reason: `shop=copyshop` had never been in any crawl group.
The census in `cache/census/` already knew:

| tag | CM | CR | in the directory before today |
|---|---|---|---|
| shop=copyshop | 43 | 12 | 0 |
| amenity=copyshop | 1 | 1 | 0 |
| craft=printer | 1 | 0 | 0 |
| office=visa | 1 | 0 | 0 |
| office=translation | 0 | 1 | 0 |
| shop=stationery | 21 | 9 | crawled (`reading` group) |

The one copy shop that had slipped in — "Printing, internet service" — was
filed under `repair/tech`. New crawl group `paper` (province-wide, both
provinces, `WIDE_GROUPS`): **47 elements CM, 13 CR**. One OSM record carries
the name ร้านถ่ายเอกสาร under `shop=paint` (node 4358880543) — a tagging slip
the name regex caught; it stays where OSM put it until somebody reads the
shopfront (`retags.json` takes evidence a person read).

Read in Thai: CMHY.city keeps five paper-trade categories — 79 ร้านถ่ายเอกสาร,
80 โรงพิมพ์ (five pages), 78 รับแปลเอกสาร, 95 ร้านถ่ายรูป, 73 อุปกรณ์สำนักงาน —
**523 distinct places** across them, read whole by
`importers/read_paper_sites.py` into `cache/paper/`. The tally is in
`data/curated/paper.json` → `counts`.

## The rule of where — in the shops' own names

A copy shop stands at the gate of whichever office wants the copies. Two shops
say it on their own listing: **ลานนาก็อปปี้ — "ย้ายไป หน้าอาคารประกันสังคม"**
(moved to the front of the Social Security building) and **ดับเบิ้ลเอ หน้าค่าย
ป.พัน 7** at ดอนแก้ว, which the third-party list glosses as "near the provincial
government centre". Others carry the gate in brackets: [ชั้น 2 บิ๊กซีหางดง],
[ตลาดแม่เหียะ], [ในราชภัฏเชียงใหม่], (ข้างโรงอาหาร), [แยกหนองหอย]. Same shape as
the uniform-tailor rule in WO-49: the trade does not cluster into a quarter.

## The rule measured, not just quoted (second pass, same day)

Zero network, off `data/canonical`: the distance from every copy shop to the
nearest government office, school, university or hospital record, with the
7-Eleven shelf as the control.

| | copy shops | within 150 m | within 300 m | median | 7-Elevens within 150 m | median |
|---|---|---|---|---|---|---|
| CM | 157 | **64 (41%)** | 125 | 181 m | 119 of 516 (23%) | 267 m |
| CR | 10 | 5 | 7 | 130 m | 37 of 210 (18%) | 342 m |

The nearest six in CM are 5–25 m from a nursing faculty, a school, a college
of dramatic arts and a market — the gate rule holds at the scale a person
walks. It is on the page as one sentence.

## Second pass — what the cache still had in it

- **313 of 522 CMHY pages carry `openingHoursSpecification`** (the directory
  spells Tuesday "Tueday" on every one). `hours_of()` in the builder turns it
  into an OSM string; **268 records now carry hours** that were blank an hour
  earlier. No network.
- **96 pages had a JSON slip in their LocalBusiness block** so `json.loads`
  refused the whole thing and a shop with a street, two phones and a
  postcode read as "no address, no GPS". A lenient regex read recovered
  them: 523/523 now have GPS, 464 a phone — and the first version of that
  read took the breadcrumb's `"name": "ธุรกิจ"` as 94 shops' names. Caught
  by printing the tally, purged, regenerated. **A lenient parser needs the
  same tally check as a strict one.**
- **The photo shelf exists**: `essentials/photo` ร้านถ่ายรูป-รูปติดบัตร, 58
  records, `idphoto` ticked from the shop's own tags (11). A camera-lens shop
  sits on the same shelf under the same CMHY heading; the facet is what
  separates them, and the shelf name says which half the reader wants.
- **Reader sheet** `paper-words` (10th): the counter sentences, three blocks,
  prices marked as-posted. `assets/reader/paper-words.pdf`.
- A copy shop that also tags #แปลเอกสาร is a copy shop with `certtrans`, not a
  translation counter — the trade is what the shop is FOR.

## Prices (all `_pricesVerified: false`)

- **1 baht/page B&W, 50 satang past 100 pages** — a Santitham shop's own board,
  read off a Lemon8 review post dated 2025-01-07
  (`lemon8-app.com/@copyshopchiangmai/7457145908644430343`). The sister post
  (`…/7457144891240546824`) names the shop **ร้านถ่ายเอกสาร 35 สต.** — the
  per-sheet price IS the shop name; CMHY lists a second, **45 ส.ต.**
- No going rate for colour or binding anywhere read; the page says "ask".
- **24 hours**: เพื่อนถ่ายเอกสาร-นิมมานฯ, 8/20 ถนน 2 เชียงราย, สุเทพ, 081 169 7979
  — teenaidee.com list dated 2023-12-27 and babform.com, both third-party. The
  facet 🌙 `open24` is ticked only from a shop's OWN page/tag.

## Sources (url · fetched · what it supports)

- cache/census/*.csv · on disk · the six tag counts above
- cache/overpass/{cm,cr}/paper.json · 2026-09-04 · the OSM half, 47 + 13
- https://www.cmhy.city/category/71-Business/79-Copy-Center/ (+80, 78, 95, 73)
  · 2026-09-04 · the Thai directory half; every record cites its own /place/ URL
  with the directory's `dateModified`
- https://www.teenaidee.com/service/copyshop/118/ · 2026-09-04 · 15 named CM
  shops with hours (article dated 2023-12-27); third-party, used for hours only
- https://www.babform.com/ร้านปริ้นเอกสารเชียงใหม่/ · 2026-09-04 · 10 named
  shops with hours; third-party. Its Chiang Rai page is a **404**.
- https://www.yellowpages.co.th/search?q=ถ่ายเอกสาร&location=เชียงราย ·
  2026-09-04 · **403** to a plain fetch — Chiang Rai copy shops are OSM only.

## Open

- **Prices unwalked.** One receipt from any counter makes the 1-baht line ours.
- **Chiang Rai beyond OSM**: Yellow Pages refuses a fetch; the 12 OSM shops
  carry no hours. A walk past Central Chiang Rai's G floor answers both
  questions at once (the immigration branch is there — see the sister note).
- `shop=paint` node 4358880543 named ร้านถ่ายเอกสาร — read the shopfront, retag.
