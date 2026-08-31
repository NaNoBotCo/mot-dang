# notary — จะรับรองเอกสารแบบโนตารี (Notary) ในเชียงใหม่ ไปที่ไหนได้บ้าง

*Where can I get a document notarized in Chiang Mai?*

- asked_on: 2026-08-28
- via: other (Nan's enrichment ask — "Notarial services in Mot Dang")
- status: BUILT — draft deleted the day the four outputs existed

## The question, in the trade's own word

The trade keeps THREE words, one per door, and no door uses the reader's word:

- **โนตารี / โนตารีพับลิค** — the counter word at private law offices (from Latin
  *notarius* via English). The registered title is ทนายความผู้ทำคำรับรองลายมือชื่อ
  และเอกสาร — Lawyers Council registration, the certificate framed on the wall.
- **นิติกรณ์** (ní-tì-kɔɔn) — the government's word: the MFA legalization seal.
  Nobody's shopfront says it; the reader who needs it doesn't know it yet.
- **notarial services** — the consulate's word, ACS window, US-bound papers only.

Census, full breadth (20,699 names, both scripts): **0** carry
notary/โนตารี/รับรองเอกสาร/นิติกรณ์. `business/professional` held **5 records**
(1 CM — a visa agency; 4 CR lawyer offices, none stating notarial work). The US
Consulate and the MFA desk were not in the catalogue at all. A แปล (translation)
name-scan meets only namesakes — schools and wats named แปลง — the WO-24 lesson
again: this page IS the coverage.

- words tried: โนตารี · notary · รับรองเอกสาร · รับรองลายมือชื่อ · นิติกรณ์ ·
  ทนาย · กฎหมาย · law/legal · แปล · กงสุล/consulate · apostille
- `python3 importers/reconcile_names.py _incoming/asked-notary-names.txt` →
  9 matched lines / 1 absent. The PRESENT rows for the consulate/MFA/Siam Legal
  were junk matches on the word เชียงใหม่ (a train station took them all); the
  real entities were absent. The 4 CR lawyer offices matched clean.

## Sources (url · fetched YYYY-MM-DD · what it supports)

- https://aphiwatlaw.com/notary-chiang-mai/ · 2026-08-28 · Aphiwat Bualoi record
  entire: address (room 3i, fl 3, 191 Huay Kaew, opposite Kad Rincome/MAYA, free
  parking), 064-932-1365, info@aphiwatlaw.com, EN/TH, same-day if morning, "fee
  depends on the document", Lawyers Council notarial registration (B.E. 2566)
  displayed, document types (visa papers, passport copies, POA, life
  certificates, degrees, company documents).
- https://consular.mfa.go.th/th/publicservice/สถานที่ให้บริการรับรองนิติกรณ์เอกสาร ·
  2026-08-28 · CM legalization desk location: "ศูนย์การค้าเซ็นทรัล เชียงใหม่
  แอร์พอร์ต ชั้น 5 (ฝั่งโรบินสัน)", Mo–Fr 09:00–16:00, 053-112-748, online queue.
- https://info.go.th/procedure/94e56d14-f82f-4203-8916-a84631e0af15/view ·
  2026-08-28 · the fees, quoted: "บริการแบบปกติ 200 บาท ต่อ 1 ตราประทับรับรอง
  นิติกรณ์" (2 business days) · "บริการแบบด่วน 400 บาท" (same-day; express window
  08:30–09:30, eligible document types listed by departmental announcement).
  Chiang Mai passport office named among the five service points.
- https://qlegal.consular.go.th · queue booking (named by both MFA pages).
- https://th.usembassy.gov/acs-chiang-mai/ · 2026-08-28 · **REFUSED** — answers a
  plain fetch with "Technical Difficulties". Its search listing the same day
  states the NEW address (131 Moo 4 Chiang Mai–Lampang Superhighway, T. Nong Pa
  Khrang), notarials by appointment, acschn@state.gov.
- https://th.usembassy.gov/acs-service-fees/ · 2026-08-28 · **REFUSED** (same
  refusal). Search listing: US$50 per seal, dollars/baht/major cards.
- https://en.wikipedia.org/wiki/Consulate_General_of_the_United_States,_Chiang_Mai ·
  2026-08-28 · the new compound: $284M, groundbreaking 2020, Ennead Architects,
  "expected to open in 2024".
- Nominatim/OSM · 2026-08-28 · **OSM still pins the consulate at the old
  Wichayanon Rd compound** (way office=diplomatic at 18.7940, 98.9987) — the
  reason the record ships `needs-pin` with the go-by-the-address warning instead
  of a wrong map pin.
- https://www.hcch.net/en/instruments/conventions/status-table/?cid=41 ·
  2026-08-28 · Thailand row: accession 30-VI-2026, entry into force 28-II-2027.
- https://www.siam-legal.com/notary-public-chiangmai.php · 2026-08-28 ·
  **REFUSED** (403 to a plain fetch) — stands as a lead, not a record.
- https://www.ktptranslationcenter.com/notarypublic-chiangrai.html · 2026-08-28 ·
  the CR receipt: "Notary Public in Chiang Rai" page carries a **Bangkok**
  address (Udomsuk 46, Bangna) and a mail-in flow — the province's name worn by
  a courier service. Filed as the reason CR gets a sentence, not a record.

## Leads — name · what is missing · why not in the catalogue yet · the one act that clears it

- [ ] Siam Legal International (2F Curve Mall, Chang Klan, 053-818-306) — own
  site 403s a plain fetch, so no dated own-page source; the note hands readers
  the phone number. Clears with one call or one visit (WO-24 discipline: no
  record without the venue's own words).
- [ ] The four CR lawyer offices (`cr-osm-way-1469683070`, `-960771470`,
  `-960771475`, `-963829106`) — signs say ทนายความ, none says โนตารี. One call
  each with the note's sentence; any yes becomes `attrs.facets.notary` + a dated
  `phoned` source.
- [ ] Certified-translation shops (the MFA chain's first stop) — the name-scan
  found only แปลง namesakes; the trade exists off-map. Its own asked-key morning
  (`translation`), not this one.
- [ ] US federal-benefit forms at the consulate — fee treatment stated nowhere
  fetchable; the note says "say so when booking" and stops. Clears at the window.

## Decision

- found 3 / gap: no (three doors is an answer, not a gap)
- shelf: none new — `business/professional` (ทนาย-บัญชี) already exists and now
  holds its first CM record with the trade's word on its own page
- facet: `professional` set added (WO-40) — **notary** 🖋 new key
  (ask_th "มีทนายความผู้ทำคำรับรองลายมือชื่อและเอกสาร (โนตารี) ประจำสำนักงานไหม" /
  ask_en "Is a Lawyers Council–registered notarial services attorney on staff?")
  + english/booking/card, keys that already exist. Three places carry the set's
  shelf (6 on `professional` after import); notary ticked on 1 (Aphiwat,
  `notaryVia: own-site`). worker.js FACET_KEYS += `notary` — **redeploy is
  Nan's move; until then the key filters harmlessly** (the WO-27/38 arrangement).
- `show: "phone"` (the asked_new stub default) **removed, deliberately**: these
  doors are appointment- and queue-based — the consulate books online and
  answers acschn@state.gov, and hiding it for lacking a phone number would
  drop the one door US-bound papers need. The pap-smear rationale runs the
  other way here.
- what was NOT recorded, and why: no private-attorney price spread (no page
  states numbers; "depends on the document" is what the one fetched page says —
  printing a guessed ฿ range would be the typed reply that's wrong the day it's
  walked) · no RON vendor names (state-by-state; the note teaches the question,
  not a brand) · no CR notarial record (see the KTP receipt) · Lawyers Council
  regulation year recited only as Aphiwat's own page states it (B.E. 2566
  displayed certificate) — the B.E. 2551 origin story circulates on third-party
  law-office blogs, none authoritative enough to recite.

## Prices

All `_pricesVerified: false`: MFA ฿200/seal (2 business days) · ฿400 express —
official manual, not yet stood at the counter · US$50/consular seal — embassy
fee page via its search listing (page itself refuses plain fetches) · private
attorney: no number printed anywhere fetched; "ask with the document in hand."

## The four outputs

- [x] records with dated sources in data/curated/additions-chiang-mai.json
  (cm-curated-aphiwat-bualoi-law · cm-curated-mfa-legalization-desk ·
  cm-curated-us-consulate-chiangmai) → `importers/import_all.py`
- [x] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [x] `python3 make_shelf_cards.py --only asked-notary` → `build.py` →
  `tests/test_asked.py`
- [ ] `python3 make_post.py notary` pasted back (Nan's move)

## Also in this order (WO-40)

`notary` search panel (19th) — triggers on the trade's three vocabularies plus
apostille/POA/proof-of-life phrasings, prices in the facts strip, doors to the
asked page and both professional shelves. The consulate record carries the
moved-compound warning as reader-facing text: **most maps still pin the old
Wichayanon compound; go by the address, not an old pin.**
