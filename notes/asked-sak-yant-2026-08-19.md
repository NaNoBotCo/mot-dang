# sak-yant — สักยันต์ที่เชียงใหม่ ไปสักที่ไหน ราคาเท่าไหร่ ที่ร้านกับที่วัดต่างกันยังไง

*Where do you get a sak yant in Chiang Mai, what does it cost, and what is the difference between the studio and the temple?*

- asked_on: 2026-08-19
- via: walk (Nan's brief of 2026-08-19 — "can the tattoo / sak yant information be even more enriched"; WO-14)
- status: DRAFT (`draft: true` in data/asked.json — delete it when the four outputs exist)

## The question, in the trade's own word

Which Thai word does Chiang Mai actually sell this under? Search that, not the
reader's English.

- word tried: สักยันต์ (the trade), สำนักสัก / สำนักสักยันต์ (the door), อาจารย์สัก,
  สักลายมือเศรษฐี (a สำนัก's own sign, photo-mine #171). NOT bare สัก (teak, "a
  single") and NOT bare ยันต์ (สุริยันต์ is a personal name) — see the guard in
  `importers/audit_tattoo.py`.
- `importers/audit_tattoo.py` over canonical 2026-08-19: SAMNAK 1 (Sak Yant
  Chiang Mai), LEADS 3 (Gao Yord / Jin Bamboo / Line Point Bamboo — design and
  technique names, not the trade), COSMETIC 1 (Chiang Rai), REMOVAL 0,
  MISFILES 1 (the minigolf, retagged), NAMELESS 5.
- `_incoming/asked-sak-yant-names.txt` — not written; the names below come from
  the photo index, not a search engine, and each needs its own page read first.

## Sources (url · fetched YYYY-MM-DD · what it supports)

- https://heyzine.com/flip-book/c90a912dc3.html · read 2026-08-17 from the
  owner's screenshots, indexed photo-mine/out/sakyant/read_index.jsonl #23–#196
  · Sak Yant Chiang Mai's design-and-price book: 37 priced designs, in-house /
  at-temple columns, the regular rate card (1 h 3,500–4,500 / 6,000–7,000 · 2 h
  6,500 / 8,500 · 3 h 8,500–9,500 / 10,500–11,500 · na 2,000 / 5,000 · 6×8 cm
  2,500 / 5,000). Canonical URL given by the operation itself (#138).
- https://sakyantchiangmai.com/sak-yant-masters-in-chiang-mai/ · 2026-08-17 ·
  17 practitioners (12 ajarn, 5 monks), teachers, temples, years in the robe —
  `manuscript-wiki/data/yant_practitioners.json`; self-reported.
- https://sakyantchiangmai.com/sak-yant-tattoo-faq/ · NOT fetched in this pass
  · linked by the operation (#138). The 2026-08-17 session note put its hourly
  framing at 2,000–3,500/h in-house with temple visits 3,500 first + 2,000 each
  additional (transport/interpreting; offering separate) — **unsourced on disk,
  so not on the record and not on the page. Re-read at the network step and
  state it beside the book's card, never welded.**
- OSM nodes 5703615419 + 6215394985 · 2026-07-27 · name, address, hours, two
  phones, website, email, payment.
- The operation's own message to a client, 2026-08 (photo-mine #138) · the
  five-precepts maintenance statement and "a handout is given to every client"
  — paraphrased on the record, never reproduced.

## Leads — name · what is missing · why it is not in the catalogue yet · the one act that clears it

- [ ] **สักลายมือเศรษฐี เชียงใหม่ อาจารย์ไก่ บารมีนาคราช** (photo-mine #171) ·
      missing: pin, own page, phone · why: known only from a Google Maps
      screenshot (rated 4.9/10, "religious destination", ~17 min by motorbike
      from San Klang, a หอพักบ้านอาจารย์ nearby) — a listing, not the สำนัก's
      own word · clears: find its own Facebook page or site, read it, pin from
      its stated address; shelve sub `sak-yant` as a สำนัก (not studio).
- [ ] **Spiritual Sak Yant, Ajarn Vee** (photo-mine #212–214) · missing:
      everything but the name and a credited turtle yant · why: seen only as a
      photo credit · clears: own page → record → `sak-yant`.
- [ ] **Gao Yord Tattoo / Jin Bamboo Tattoo / Line Point Bamboo Tattoo** (on the
      studio shelf) · missing: whether an ajarn works there and a katha is given
      · why: a design or technique name is branding · clears: each from its own
      page; add `sak-yant` only if it states the ajarn.
- [ ] **สักปาก น้องสาวชมพู เชียงใหม่ — By Natcha beauty** (photo-mine #4) ·
      cosmetic tattoo, 1,299, phone 064-470-8762, LINE NATCHABEAUTY · missing:
      pin + a dated source URL · clears: page → `cm-curated-natchabeauty`,
      sub `cosmetic-tattoo`, `_pricesVerified: false`.
- [ ] **Cher proud clinic ศัลยกรรม** (photo-mine #5, Chiang Rai) · laser
      removal of brow tattoo 599, phones 061-6213546 / 092-4463996 · missing:
      pin + source · clears: page → record under medical + `tattoo-removal`;
      then ("tattoo","removal") comes off KNOWN_EMPTY.
- [ ] The Sak Yant Chiang Mai FAQ re-read (above).

## Decision

- found 1 / gap: no — one listing today, the shelf is live; two more สำนัก
  are leads, not records.
- shelf (child key, in the trade's word): `tattoo/sak-yant` (already existed,
  now matches `sub: sak-yant`); new sibling `tattoo/cosmetic` (สักคิ้ว-สักปาก,
  `sub: cosmetic-tattoo`) for the trade that had no shelf.
- facet: none — three places and the door sentence first. The door sentence
  is written: *ที่นี่มีอาจารย์ลงคาถาให้ไหมคะ/ครับ หรือสักลายอย่างเดียว*.
- what was NOT recorded, and why: the two สำนัก (no own page read); the FAQ
  hourly figures (unsourced on disk); the design plates (never republished);
  any real-vs-touristic sort (refused on purpose).

## Prices

All `_pricesVerified: false` until somebody reads a board on the street. The
book's card is on the record as `priceCardTh/En` + `priceCardVia`; rendered by
`known_facts()` as "ราคาที่ประกาศ · Published prices" with the unwalked mark.

## The four outputs

- [x] records with dated sources in data/curated/additions-*.json →
      `importers/import_all.py` (Sak Yant Chiang Mai, curated, same OSM id)
- [ ] entry in data/asked.json filled (find / lead / notes) — **filled; `draft`
      stays until the two สำนัก are read** (the first note's sentence about
      "one listing" is rewritten on release)
- [ ] `python3 make_shelf_cards.py --only asked-sak-yant` → `build.py` →
      `tests/test_asked.py`
- [ ] `python3 make_post.py sak-yant` pasted back
