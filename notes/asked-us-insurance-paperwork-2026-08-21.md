# us-insurance-paperwork — โรงพยาบาลไหนในเชียงใหม่ออกใบเสร็จภาษาอังกฤษแบบแยกรายการ และช่วยกรอกแบบฟอร์มเบิกประกันสหรัฐฯ (FMP / CHAMPVA) ให้ผู้ป่วยได้เอง

*Which Chiang Mai hospitals issue itemized English receipts and will complete US insurance and VA claim forms (FMP, CHAMPVA) with little or no help from the patient?*

- asked_on: 2026-08-21
- via: walk
- status: DRAFT (`draft: true` in data/asked.json — delete it when the four outputs exist)

## The question, in the trade's own word

Which Thai word does Chiang Mai actually sell this under? Search that, not the
reader's English. (ขัดขี้ไคล was the lesson: "Korean scrub" returned one paid
ad; the Thai word returned a trade with price boards.)

- word tried:
- `python3 importers/reconcile_names.py _incoming/asked-us-insurance-paperwork-names.txt` →

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
- [ ] `python3 make_shelf_cards.py --only asked-us-insurance-paperwork` → `build.py` → `tests/test_asked.py`
- [ ] `python3 make_post.py us-insurance-paperwork` pasted back
