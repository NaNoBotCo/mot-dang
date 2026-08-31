# WO-36 — ย่าน: the bar lowered, the children split · 2026-08-26

*Nan's numbered go on WO-35's held call 1 ("Go ahead with this, and also
split the children"). Zero network — one number, one curated file, one
page-shape.*

## Part 1 — the bar: HUB_MAX_ROWS 2,500 → 1,400

Nan's go, verbatim mechanism from WO-35. Four more shelves flip to hubs:
**essentials · medical · school · hotel** (their indexes were 1.5–2.3 MB).
The coverage gate still holds wat back (one child) and leaves every cr
shelf a plain listing (largest is under the bar). Nothing new was written
for this — it is the number the mechanism was built to take.

## Part 2 — the children split, and what was measured first

Three children stand past 1,000 rows: **food/thai (1,609) · food/cafe
(1,301) · school/government (1,064)**, at 1.7 / 1.4 MB pages (schools
similar). The spine was measured before it was chosen:

- **The road graph failed the job.** STREET_OF reaches 838 of 1,609 thai
  records (52%) across 289 streets averaging three places each — that is
  289 pages of three rows plus a 771-row "road not known" wall.
- **tambon/amphoe attrs: zero** on these records. **Addresses: 366 of
  2,910**, amphoe named in 28. Both dead ends, both printed here so nobody
  re-walks them.
- **What every record has is a pin** — so the spine is **ย่าน**, the named
  parts of town people say out loud, as a curated file:
  `data/curated/zones.json`. Ten boxes for the city (the moat rectangle and
  its named quarters — เมืองเก่า, วัวลาย, ช้างคลาน, ช้างม่อย, ริมปิง,
  นิมมาน, สันติธรรม, ห้วยแก้ว, สุเทพ, หนองหอย) and ten circles for the
  amphoe seats (แม่ริม, สันทราย-แม่โจ้, ดอยสะเก็ด, สันกำแพง, สารภี, หางดง,
  แม่แตง-เชียงดาว, ฝาง-แม่อาย, จอมทอง-ฮอด, แม่ออน). First match wins,
  boxes before circles.

## The anchor rule (how hand-drawn bounds stay honest)

Every city zone names **anchors** — places from our own records that must
fall inside it: the moat rectangle is proven by วัดพระสิงห์ and
วัดเจดีย์หลวง standing in it, วัวลาย by วัดศรีสุพรรณ, ริมปิง by
วัดเกตการาม, นิมมาน by ข้าวซอยนิมมาน. `check_zone_anchors` runs inside
build() and **refuses the whole build** if an anchor drifts outside its
zone; `importers/audit_zones.py` is the standalone witness and prints the
census. Today: 10 anchors OK, and 1,528 of 14,490 cm records (10.5%) land
in no zone — they go to the **รอบนอก fallback page**, "we have not named
this zone yet" being a fact and not a failure, the road graph's own rule.
(The first draft borrowed วัดเจ็ดยอด as an anchor for two zones it sits
between; the check caught it and the anchors were re-picked from records
that actually stand inside — the rule earned its keep before the first
build.)

## The page shape

A split child mirrors the parent hub exactly: `food/thai/index.html`
becomes zone lines (bold link · count · three doors as a taste), each zone
a real listing page at `yan-<zone>.html` with toolbar, sorts and facets;
the complete roll keeps existing at `all.html` — noindex,follow, weight
printed on the door. Nothing renamed, no record unlisted.

## Only Nan can decide (for later, none done)

1. **Zone names and bounds are hers to edit** — zones.json is curated data,
   not code; adding แม่วาง or splitting สันติธรรม from ช้างเผือก is a JSON
   edit plus anchors, and the build checks the anchors.
2. **cr zones** — the file has no cr entry, so cr never splits. Chiang Rai
   zone names are a separate sitting.
3. **Wire zones into the "By neighbourhood" sort** on unsplit shelves
   (today it uses roads-then-tambon and reaches half the rows) — separate
   order, touches md.js.
