# WO-35 — ชั้นที่โตเกินหน้าเดียว: the food index becomes a hub · 2026-08-26

*Item 2 of Nan's "one at a time" from the same navigation survey as WO-34.
Zero network — one rule and one page-shape in `build.py`, no data touched.*

## What was measured

`cm/food/index.html` was **4.2 MB**: all 4,151 food places on one page,
4,227 links, twenty brand folds — while ten sub-shelves (thai, cafe,
street-food, vegetarian…) stood fully built in folders beside it, each row
listed twice on the site. On the connections this site is for, the second
click most visitors make cost a minute of download. The children were also
measured before anything moved: **the 11 food children cover 4,151 of 4,151
cm records** (cr: 1,129 of 1,163, the 34 strays handled below), so no
record loses its place on the shelf by this change.

## The rule (not a food special-case, but only food crosses it today)

`HUB_MAX_ROWS = 2500`, and the gate is double: a shelf goes hub **only when
it is past 2,500 rows AND its children cover ≥ 90 % of it**. Today that is
cm food alone — essentials (1,992), medical (1,526), school (1,493), hotel
(1,465) all sit under the bar, and wat (1,497) has no real children so the
coverage gate holds it back regardless. When a shelf grows past the bar the
next build flips it with no one remembering to.

## The hub page (what replaces the wall)

Same art band, h1 with count, category bands, map — then instead of 4,151
rows: **one line per sub-shelf** (Yahoo genre — bold link, count in parens,
three doors as a taste: "อาหารไทย (count) — เช่น …"). Below that:

- **ยังไม่เข้าชั้นย่อย · Not yet on a sub-shelf** — any record no child
  matches, listed in full right on the hub. (cm food has zero today; cr
  food, with its 34 strays, is under the row bar and stays a plain listing
  — but the section is there for the day any hub shelf has strays.)
  Nothing silently vanishes into "the children have it".
- **📜 รายชื่อครบทั้งชั้น · the complete roll** — `food/all.html`, every
  row on one page with the toolbar and sorts, **its weight printed on the
  door** ("~4.1 MB") so nobody on a hilltop connection opens it unwarned.
  `noindex,follow` — the sub-shelves are the indexed copy of every row, so
  search engines see each place once, not twice.

Sub-shelf pages, place pages, GeoJSON, search index, tags: untouched.

## Only Nan can decide (for later, none done)

1. **Lower the bar?** At 1,400, essentials · medical · school · hotel go
   hub too (their indexes are 1.5–2.3 MB). Same mechanism, zero new code —
   one number. Wat would need children first (it has one).
2. **Split the two big children?** thai (1.7 MB) and cafe (1.4 MB) are the
   next-largest pages on the site; a by-neighbourhood split inside a
   sub-shelf is its own order.
3. **Three example doors per child** — keep, drop, or make five?
