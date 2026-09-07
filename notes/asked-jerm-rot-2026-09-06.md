# jerm-rot — เจิมรถมอเตอร์ไซค์ใหม่ ไปวัดไหนในเชียงใหม่ วันไหน เสียเท่าไหร่

*Where in Chiang Mai do you take a new motorbike to be blessed — which temple, which day, what does it cost?*

- asked_on: 2026-09-06
- via: walk
- status: DRAFT (`draft: true` in data/asked.json — delete it when the four outputs exist)

## The question, in the trade's own word

Which Thai word does Chiang Mai actually sell this under? Search that, not the
reader's English. (ขัดขี้ไคล was the lesson: "Korean scrub" returned one paid
ad; the Thai word returned a trade with price boards.)

- word tried: **เจิมรถ** — the anointing of a vehicle. This is the word. "blessing"
  in English returns nothing; `data/search_thesaurus.json` already carries
  blessing → เจิม, but no record, shelf or facet anywhere on the site holds it,
  so the site answers this question with nothing today.
  Adjacent and NOT the same: สะเดาะเคราะห์ (fate-loosening), ทำบุญรถใหม่,
  พุทธาภิเษก (consecration of images).
- `python3 importers/reconcile_names.py _incoming/asked-jerm-rot-names.txt` → not run yet

## Sources (url · fetched YYYY-MM-DD · what it supports)

**Nan, first-hand, 2026-09-06 — the strongest thing in this file.**
- The motorbike **dealers** send buyers to วัดดวงดี: "this is the wat everyone
  goes to to get their motorcycles blessed, according to the dealers." Grade:
  told-of, plural dealers, reported by Nan.
- She has been **twice**, for her own blessings: "if you need a bike blessed they
  do it all day long." Grade: **first-hand, walked, ×2.** This is the only
  current word on hours anywhere in this file.
- The page she gave: https://www.facebook.com/profile.php?id=100064278386228
  · fetched 2026-09-06 → วัดดวงดี / WatDuangDee, ต.ศรีภูมิ อ.เมือง เชียงใหม่.
  The fetch returned the page identity only — not days, not donation.

**The place is already in the catalogue.** `cm-osm-way-261339003` — วัดดวงดี,
ONAB code 03500101010, ต.ศรีภูมิ, วัดราษฎร์ / มหานิกาย, founded BE 1910
(1367 CE), per `data/curated/wat_registry.json`. It already carries a story hook
(`data/curated/story_hooks.json`, th.wikipedia, fetched 2026-08-08): the
auspicious name, the Three Kings a few steps west, the CS 859 inscription, the
carved woodwork. **That hook says nothing about เจิมรถ.** That is the gap.

- https://mgronline.com/local/detail/9560000041355 · fetched 2026-09-06 ·
  **MGR Online / ผู้จัดการ, published 5 Apr 2013.** Press, Chiang Mai, dated,
  and it features วัดดวงดี by name as the เจิมรถ temple.
  - assistant abbot, quoted: "บางวันเคยมีผู้ที่นำรถยนต์มาเจิมรวมแล้วมากกว่า 50 คัน"
    — 10–20 vehicles a day before the รถคันแรก scheme, over 50 on some days after.
  - **Thursday and holidays** are the days people choose; **Tuesday is avoided.**
  - "ห้ามดื่มเหล้าเบียร์เด็ดขาด" — no alcohol, said flatly by the monks.
  - Cars and motorcycles both.
  - **It is 13 years old.** It supports the practice, the volume, the day-custom
    and the alcohol rule. It supports nothing about today's hours or donation.
- wongnai review page; two lemon8 posts · fetched 2026-09-06 · all three frame
  วัดดวงดี as the เจิมรถ temple. Directory and social grade — corroboration only.
  Not first-hand, and per the enrich.json readme they never enter enrich.json.

**Told-of only — NOT records.** Pantip 13117783 lists nine old-city temples an
owner was weighing: ดับภัย, เชียงยืน, หมื่นล้าน, ลอยเคราะห์, ชัยมงคล,
หมื่นเงินกอง, ชัยพระเกียรติ, ดวงดี, เชียงมั่น. Read that list carefully — it is
the auspicious-name ไหว้พระ ๙ วัด circuit, the practice `data/merit.json`
already carries, not nine temples known to do เจิมรถ. A forum poster's shortlist
is not a shelf. Any of the eight becomes a record when somebody stands there.

## Leads — name · what is missing · why it is not in the catalogue yet · the one act that clears it

- [ ] **วัดดวงดี** — the record exists; the เจิมรถ fact is not attached to it.
      Not in the catalogue as a blessing place because no field on
      `cm-osm-way-261339003` carries the practice. Clears when the fact lands on
      the record — but WHERE it lands is a question for Nan, below.
- [ ] **Hours and donation at วัดดวงดี today** — nothing dated on this disk.
      Nan's "all day long" is current and walked; the 50-cars-a-day and the
      Thursday/Tuesday custom are 2013. Clears on one walk past, or the temple's
      own page stating it.
- [ ] **A second and third door** — the dealers' referral says วัดดวงดี is the
      default, not the only one. A one-record answer is a thin answer. Clears by
      asking a dealer which others they name. NOT by promoting the Pantip nine.

## Decision

**OPEN — this is Nan's, not mine. Two forks, written out:**

**Fork 1 — SETTLED 2026-09-06, by Nan.** It was never a fork; it was a rule
nobody owned. `enrich.json`'s readme said "never a scrape of Google or Facebook
listings" — that line entered in commit 8f2a6acc4c (2026-08-16) beside
enrich_sites.py, propagated from `notes/sakyant-proposal-2026-08-19.md`, and
names no decider. Nan, 2026-09-06: **"I am sure I PERSONALLY would not have made
such a rule… I don't clutch pearls about scraping."** The readme is rewritten to
the distinction that actually holds — a directory's listing card is the
directory's copy; a page the place itself writes and runs is its own site,
whichever company hosts it. In this city that is usually Facebook, and the
2026-08-16 own-site pass found 341 of 747 websites dead.

**Done:** `data/curated/enrich.json` now carries `cm-osm-way-261339003` with the
temple's own page, `license: official-site`, fetched 2026-09-06. The page's
content sits behind a login wall, so only the identity and the link were taken —
no hours, no phone, no donation off it.

**Fork 2 — does เจิมรถ earn a facet, or is it one sentence on one temple?**
asked_new deliberately did not stub a shelf or facet, and it is right not to:
today the answer is ONE place. A facet with one member is an empty shelf with a
name. Options: (a) no facet — the answer page and a line on the temple carry it;
(b) a facet now, with `KNOWN_EMPTY` carrying the reason; (c) hold the facet until
a second and third door are walked. Recommend (c) — but it is hers.

- found N / gap: **1 recorded (วัดดวงดี), first-hand.** Not a gap.
- shelf: none stubbed — see Fork 2.
- facet: none stubbed — see Fork 2.
- what was NOT recorded, and why: the Pantip nine (a merit circuit, not a
  เจิมรถ list); the wongnai and lemon8 pages (directory/social grade,
  corroboration only).

## Prices

All `_pricesVerified: false` until somebody reads a board on the street.
**No price is known here.** A temple takes a donation, not a fee, and no source
on this disk states an amount. Do not invent a range and do not carry over a
figure from another temple — the question asks "เสียเท่าไหร่" and the honest
answer today is that we do not know yet.

## The four outputs

- [ ] records with dated sources in data/curated/additions-*.json → `importers/import_all.py`
- [ ] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [ ] `python3 make_shelf_cards.py --only asked-jerm-rot` → `build.py` → `tests/test_asked.py`
- [ ] `python3 make_post.py jerm-rot` pasted back
