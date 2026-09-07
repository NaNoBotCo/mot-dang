# The twenty follow-ups to WO-55 — what each one turned out to be · 2026-09-04/05

Nan's go: *"please add all of these one by one."* This is the ledger of the
twenty, in the order they were listed, with what each actually was once it
was opened. Work orders WO-58 (the shelves), WO-60 (the lens layer), WO-61
(BPO) and WO-62 (the last three tags) carry the details.

| # | item | what it was | where it landed |
|---|---|---|---|
| 1 | fill the physiotherapy shelf | the shelf matched nothing: OSM has no `healthcare=physiotherapist` here | 20 records, shelf builds |
| 2 | speech therapy | 0 names; CMU's own clinic states the whole service | `/speech.html`, 5 rows |
| 3 | hearing aids and audiology | the shops were already in the catalogue, unlabelled | `/hearing.html`, 10 rows, 6 records |
| 4 | prosthetics and orthotics | the **national** Prostheses Foundation is at Mae Rim | `/prosthetics.html`, 5 rows |
| 5 | special-education schools | five schools, and **every one of their websites is dead** | `/specialed.html`, 8 rows |
| 6 | dementia and memory care | CM Neuro's memory clinic + 12 homes long-care lacked | `/dementia.html`, 10 rows |
| 7 | stroke rehabilitation | the system's own word for the first six months is ระยะกลาง | `/stroke.html`, 9 rows |
| 8 | dialysis | one unit opens at **05:00** because a chair takes several rounds | `/dialysis.html`, 6 rows |
| 9 | dental, the largest silent shelf | 246 clinics with their own service tags | +157 records, shelf 258 |
| 10 | eye care | **the optician shelf held ONE record against 85 shops** | `/eyecare.html` + 78 on the shelf |
| 11 | vaccination and travel medicine | the state travel clinic, and Suan Dok is the north's only yellow-fever centre | `/vaccines.html`, 5 rows |
| 12 | mental-health counselling in English | three professions people fold into one errand | `/counselling.html`, 7 rows |
| 13 | vets and pet hospitals | grooming was 1 record; the trade is 47 | +165 records |
| 14 | the mend trades | **331 refusals that read like a trade directory** | `/mending.html` + 354 records |
| 15 | laundry and dry cleaning | 422 directory rows against 61 mapped | +375 records, shelf 457 |
| 16 | motorbike rental and licence school | **two transport offices that do different work** | `/driving.html` + 448 on motorbike |
| 17 | water delivery and cooking gas | the ส่งน้ำ trap: 23 irrigation canals | 352 records, shelf 370 |
| 18 | coworking and visa desks | mostly Thai accounting offices, not coworking | +84 records, professional 93 |
| 19 | funeral services and cremation | **155 of 156 CR "funeral directors" are village grounds** | `/funerals.html` + 278 grounds |
| 20 | the `making` crawl group | it HAD run — and eleven of its finds were dropped at import | fabric, antiques, jewelry, 4 handicraft names, musical instruments |

Item 20's memory note said the group had never run. It had, on 31 August,
under WO-51 — and the crawl's own finds were being thrown away by a
classifier with no rule for them. **A crawl that runs and then drops its
find is the same failure as a crawl that never runs, and harder to see.**

## The pattern under most of them

Six of the twenty were not missing data. They were **a rule that refused
what the crawl had already brought home**:

- `shop=optician` — no rule. 85 shops, one record on the shelf.
- `shop=musical_instrument` — no rule. All 23 music records were curated.
- `shop=fabric`, `antiques`, `jewelry` — no rule.
- `craft=shoemaker` → filed with the **tailors** since the first crawl.
- ล้างแอร์ — refused for saying *wash* rather than *mend*, and it is the
  most-called home trade in this city.
- `shop=funeral_directors` in Chiang Rai — believed, and it is wrong 155
  times out of 156.

The tell each time was the same: **a refusal list that reads like a trade
directory.** If the things being turned away have names, they are the trade.

## The traps, for the next person

- **ส่งน้ำ is an irrigation canal.** The name selector for water shops
  returned 23 คลองส่งน้ำ, the road beside one, and the Royal Irrigation
  Department's own office. Use น้ำดื่ม.
- **Same door means same TRADE.** A physio clinic matched a dental clinic
  68 m away; a neighbour is not a duplicate.
- **An ambulance tags itself with every errand it drives to** — "ส่งผู้ป่วย
  ฟอกไต" filed it as a dialysis clinic.
- **A dental hospital has "hospital" in its name.** The faculty's own, the
  largest in the north, was refused for that word.
- **A directory row's `website` is often a domain that died years ago.**
  bikkychiangmai.com is parked and link-health has said so since July; the
  record carried it and the publish gate refused the build. `cmhy_records`
  now checks link-health before writing the field and keeps the address in
  `attrs.deadSite` with the verdict and the Wayback copy.
- **drivingthailand.com is served in TIS-620** and reads as garbage unless
  decoded as cp874.
- `pgrep -f "python3 build.py"` **never matches** — the process is
  `.../Python build.py`. Wait on `cache/build.lock`.
- A `<<EOF` heredoc containing Thai needs `LANG=en_US.UTF-8` and a coding
  line, or Python 3.9 refuses the file.

## Still open

- **Chiang Rai** is thin on almost every new lens: the Thai directory read
  covers Chiang Mai only.
- **The Thai half of BPO** — cmhy category 200 was read and the records are
  on the professional shelf; the good ones are not written into the lens.
- **Two merges**: the blind schools appear twice each, once from a register
  and once from the map. CM Neuro's MOPH twin is still separate (a WO-55
  door).
- **Watch repair** (cmhy category 235) was not in the mend read.
- The `lab` harvest is the one job of the fifteen that never landed.
