# WO-24 — คำตอบก่อนลิงก์: the rich doors, and the namesake split

Nan, 2026-08-20, after typing "elephant" into the live search: *"Let's just
pre-stage some rich information for some of these terms, without just
defaulting to 'here's a list of links'. Another thing. I think all the place
names with Chang in them are not differentiated well for this term. Might be
a systemic problem, for multiple terms."*

Two deficiencies, one page. Both fixed in search.html's own logic — searchcore
and the mined tables are untouched, so no parity run, no rollout queue.

## 1. The rich door

`data/curated/search_panels.json` — curated field truth, one card per topic
the site already keeps a whole page for. When a query names such a topic, the
card renders ABOVE the rows: glyph, bilingual title, a live count from the
index the page just loaded, one or two sentences that follow each shelf's own
discipline (the venue states / no rankings / stated-vs-likely), fact chips,
door pills, and where it earns one a quiet delight line. Ten panels ship:
chang · muaythai · cooking · beauty · womens-health · toilets · festivals ·
flights · massage · wat.

Triggers, three kinds, any one is enough — first panel to speak wins, so the
file stays ordered narrow to broad:

- **shelves** — a key the mined table lifted from the query. Only for topics
  where every mined word names the topic itself. The lesson that set this
  rule: the mined table sends มังสวิรัติ to the cooking shelf (the shelf HAS a
  vegetarian child), and a class panel over a dinner search answers the wrong
  question. `tests/test_search.py` holds the guard case.
- **variants** — checked against each term's expansions, so the thesaurus does
  the reach: จ๊าง arrives at the chang panel through ช้าง with no Northern
  Thai listed in the panel file.
- **query** — normalized substrings of the whole query, for compounds the
  segmenter takes apart (เรียนทำอาหาร → เรียน + ทำ + อาหาร) and multi-word
  names (yi peng).

A panel's `shelves` also JOIN the score lift once it triggers, which is how
วัด raises the wat shelf although no mined table carries the bare word.

Build-side: build.py shape-checks the file (every reader-facing string must be
a `[th, en]` pair, ids unique) and refuses the build otherwise, then publishes
it as `data/search_panels.json`, fetched by search.html alongside the three
search tables. A reader with the JSON unreachable gets exactly the old page.

## 2. The namesake split

66 place names in the catalogue carry ช้าง — ช้างเผือก, ช้างคลาน, ดอยช้าง —
and none of them is a camp (the WO-19 measurement). They used to interleave
with the camps for the exact query where the camps are the point. Now, when a
query names a shelf at all (`wantShelves` non-empty), the rows split:

- on-shelf rows first, grouped under their category headers as before;
- everything else files behind a full-width header — *ชื่อพ้อง · namesakes —
  places carrying the word in their name* — with its own true count, still
  grouped by category inside.

The split is systemic, not elephant-special: "coffee" files Coffee Hardware
under namesakes below the cafés the same way. A query that names no shelf
keeps the single list it always had. The membership test is the curated
category codes, not the match field — so it cannot drift from what the shelf
pages themselves say.

## Tests

`tests/test_search.py` was ALSO repaired: its extraction markers dated from
before the search-core adoption (`const norm=s=>s.toLowerCase()` no longer
exists in build.py), so the whole file failed at HEAD without measuring
anything. New markers wrap the block from table set-up to the first DOM write,
which now covers panel choice and the partition. All fifteen old queries kept;
eleven new ones cover the doors, the namesake anchor (โรงพยาบาลช้างเผือก, the
human hospital, resolved from the index by name so a re-crawl cannot rot it),
the Northern form, and the มังสวิรัติ overfire guard. The test also walks
every internal door href against the built site.

## Found on the way, and what was done about each

- **hotspring_layer.py (WO-23, in flight) had a Python 3.9 f-string
  SyntaxError** — the apostrophe-in-`bi()`-in-`f'…'` shape WO-19 documented —
  and build()'s guarded layer region resumes at the tags layer when a layer
  import raises, so cooking.html, beauty.html and womens-health.html silently
  stopped building with it. The deploy sync then deletes what the build did
  not write: **beauty.html and womens-health.html were 404 on the LIVE site**
  when checked (cooking.html still answered — an edge-cache ghost). Fixed by
  the same concatenation lift the earlier block in that file already used;
  `cache/walk-rest` held publishing while broken, cleared once the rebuild
  carried all four pages. A layer import that takes three sibling pages down
  with it and still exits 0 is worth a harder look one day: per-layer guards,
  or a publish-gate check that yesterday's root pages still exist.
- **zzzzqqq loose-matches SK House** (key one edit apart) — three rows, not
  the catalogue. test_search now caps it at 5 rather than pretending zero is
  achievable under current slack; the key-precision idea is filed in
  search-core's SEARCH.md gaps.
- **ทำอาหาร segments to ทำ + อา + ร** (not in the thesaurus, so not
  protected) — the rows are noise even while the panel opens correctly by
  query substring. Filed in SEARCH.md gaps with the eval.py ask.
- **มังสวิรัติ returns zero**: intent lifts it into `filters`, no term
  survives. The cooking panel correctly stays shut (the overfire guard), and
  the vegetarian-gets-nothing behaviour is filed in SEARCH.md gaps.

## Open / future

- Stats chips baked from each register (camps · no-riding-stated · needs-pin)
  would make the chang door richer still; needs a build-time join, filed for a
  future order.
- `data/asked.json` reader questions could door from panels of their topic.
- Per-panel og cards via make_shelf_cards.py, so a shared search URL carries
  the door.
- More panels as more topic pages exist (hot springs when WO-23 lands its
  board; views when WO-21's doors get their go).
