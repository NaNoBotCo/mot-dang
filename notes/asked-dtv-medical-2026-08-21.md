# dtv-medical — ขอแผนการรักษา ประวัติการนัด และหนังสือรับรองจากโรงพยาบาลสำหรับวีซ่า DTV สายรักษาพยาบาล ได้ที่ไหน และมีใครดูแลเอกสารต่อเนื่องให้บ้าง

*Where can I get the treatment plan, appointment records and hospital letters a medical DTV needs — and who will keep that paperwork current for extensions?*

- asked_on: 2026-08-21
- via: walk
- status: DRAFT (`draft: true` in data/asked.json — delete it when the four outputs exist)

## The question, in the trade's own word

Which Thai word does Chiang Mai actually sell this under? Search that, not the
reader's English. (ขัดขี้ไคล was the lesson: "Korean scrub" returned one paid
ad; the Thai word returned a trade with price boards.)

- word tried:
- `python3 importers/reconcile_names.py _incoming/asked-dtv-medical-names.txt` →

## Sources (url · fetched YYYY-MM-DD · what it supports)

-

## Leads — name · what is missing · why it is not in the catalogue yet · the one act that clears it

- [ ]

## Decision

- found N / gap:
- shelf (child key, in the trade's word) or none:
- facet (key + ask_th/ask_en) or none — remember the three places + KNOWN_EMPTY:
- what was NOT recorded, and why:

## Prices

All `_pricesVerified: false` until somebody reads a board on the street.

## The four outputs

- [ ] records with dated sources in data/curated/additions-*.json → `importers/import_all.py`
- [ ] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [ ] `python3 make_shelf_cards.py --only asked-dtv-medical` → `build.py` → `tests/test_asked.py`
- [ ] `python3 make_post.py dtv-medical` pasted back
