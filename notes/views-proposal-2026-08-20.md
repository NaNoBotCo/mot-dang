# วิว-น้ำตก — views and photo spots: the shelf that was thin, the doors the data is behind

*2026-08-20. Nan: "Enrich mot dang with views and photo ops. These are huge in
Chiang Mai. Not even sure where to look for data." This note is the
measurement, the rule, what was built the same day with no network at all, and
— the part actually asked for — where the data lives and which doors need her
go. Read with `MARCHING-ORDERS.md` WO-21. The audit is
`importers/audit_views.py`; run it any time, it fetches nothing.*

## The measurement, before any proposal

| What a reader asks | What the site held on 2026-08-20 morning |
|---|---|
| Where do I go for the view? | 103 `sights/viewpoint` records — **Chiang Mai 31, Chiang Rai 72.** The imbalance is crawl geometry, not geography: CR is in `WIDE_PROVINCES` and was asked province-wide; CM's `culture` group (the one carrying `tourism=viewpoint`) has only ever been asked on the near ring, and the views of Chiang Mai are on the doi by construction. **กิ่วแม่ปาน, แม่กำปอง (the village), ห้วยน้ำดัง, ผาช่อ and ดอยหลวงเชียงดาว appear nowhere in 16,300 records.** |
| The waterfalls? | **No waterfall shelf existed and no crawl had ever asked** — `waterway=waterfall`, `natural=peak` and `natural=cliff` appear in no query group. น้ำตก reached the catalogue only inside school names and two park gardens. Meanwhile WO-19's attraction dragnet (fetched 2026-08-20, Nan's go) had already CAUGHT แม่สา, บัวตอง, วชิรธาร, แม่ยะ, สิริภูมิ, หมอกฟ้า, ตาดหมอก, ขุนกรณ์ — and fenced every one into `cache/elephant_review_<prov>.txt`, which calls itself "the ready-made menu for a future attractions order." This is that order. |
| What does the spot itself state? | Nothing. All 103 carried no photo, no hours, no fee, and OSM's own `direction` (the bearing a mapper stood there and took) and `ele` (height) were dropped at import. |
| The cafe with the view? | 54 records on OTHER shelves claim a view in their own name — 28 food, 18 hotel, 5 realestate — and nothing joins them. `cache/views_claims_<prov>.txt` now lists every one. |
| A photograph? | `harvest_commons.py` — built 2026-07-29 and exactly the right instrument (geosearch around each record, licence and photographer handed to us in the metadata, plus an area sweep for well-photographed subjects we do not list) — has run ONCE, capped, 59 images, none of them at a viewpoint. |

## The rule this shelf runs on

Massage's rule was *never infer respectability*; the elephants', *the venue
states and nothing ranks it*. Here:

**The view is measured or stated, never awarded.** A bearing and a height are
measurements and render as measurements. A venue's "mountain view" is the
venue's own claim and renders as its claim — ชื่อบอกวิว, the name says so. A
Commons count is a count of freely-licensed photographs, dated. Nothing on
this site crowns a "best sunset", sorts spots into hidden and touristy, or
turns a westward bearing into a sunset promise — whether the horizon is open
at dusk is the venue's or the door survey's to state. Sorts stay distance and
alphabet, the same rule as the temples. Entry fees, when they come, are the
posted spread exactly as the gate posts it, `_pricesVerified: false` until a
person stands at one.

## Built today, zero network (the WO-19 fence, extended)

- **`importers/audit_views.py`** — the measurement above, five reports
  (SHELF · DROPPED · MENU · CLAIMS · NEVER), `--claims` writes the census
  files. Same contract as `audit_elephant.py`; the import borrows ITS rules,
  one copy.
- **`views_hit()` in `import_overpass.py`** — rides the elephants-file fence
  exactly as `chang_hit` does: a name that declares a waterfall or a
  viewpoint files onto `sights`; everything else stays in the review file,
  which remains the menu for whatever attractions order comes next;
  `classify()` stays unreachable from that file. Same lodging/food fence
  (น้ำตก is also a laab cousin — a restaurant wearing the word stays a
  restaurant), same `(closed)` fence, and every record stamped with the date
  its group was actually fetched, 2026-08-20.
- **18 waterfalls + 2 viewpoints entered**: the Inthanon set (วชิรธาร, แม่ยะ,
  แม่กลาง, สิริภูมิ), แม่สา, บัวตอง (the sticky one), หมอกฟ้า, ตาดหมอก,
  แม่กำปอง (the falls), ศรีสังวาลย์, ดอยโตน, แม่บัวคำ; CR ขุนกรณ์, ห้วยชมภู,
  ห้วยแม่ทราย; the bare-named CR จุดชมวิว and the Chiang Rai skywalk.
- **`sights` gains a น้ำตก · Waterfalls child**; schema.org publishes the real
  `Waterfall` type (a TouristAttraction fallback would be less true than the
  thing itself). Sub labels reach the search index by the WO-4 machinery, so
  "น้ำตก" and "waterfall" now answer.
- **`direction` and `ele` are kept at import and rendered** by
  `known_facts()`: หันไปทาง · Faces (degrees collapse to the eight winds —
  ±22.5° is what a compass rose already claims; anything murkier renders
  nothing rather than something almost right) and ความสูงจากระดับน้ำทะเล ·
  Elevation. Four pages carry a bearing today, ten a height; every future
  crawl keeps them for free.
- Scratch build 20,371 pages; publish_gate / asked / alt_text / facets /
  plan_routes all PASS; no `/Users/` leaks.

## Where the data lives — the doors, numbered for a go

Every door below was read, not guessed; none is fetched until Nan says the
number. (1) and (2) are the big ones and both are gentle.

1. **A wide `views` crawl group** — `tourism=viewpoint`,
   `waterway=waterfall["name"]`, `natural=peak["name"]` (the named doi), in
   `WIDE_GROUPS`, both provinces, one selector per query as the manners
   require. This is what brings กิ่วแม่ปาน, ห้วยน้ำดัง, ผาช่อ and
   ดอยหลวงเชียงดาว in — the near ring can never see them, the same way it
   could never see the elephant camps. Modest: three selectors, snapshot-first.
2. **Re-run `harvest_commons.py`, uncapped, both passes.** The by-place pass
   photographs the shelf we now hold (licence and photographer arrive in the
   metadata; nothing is copied, thumbnails hot-link with credit). The AREA
   pass is the photo-op instrument nobody else has: it answers "which subjects
   in these two provinces are heavily photographed under a free licence" —
   evidence of where people actually stand and shoot, with no tracking, no
   platform scraping, no guessing. Keyless API, gentle by design.
3. **Thailand Tourism Directory** (WO-17, standing): attractions are Type 1 of
   its 28,500 listings — จุดชมวิว and น้ำตก categories with phone · LINE ·
   hours · coords. Step 0 is unchanged: Nan registers for the API key.
4. **The WO-16 small fetches already measured**: CR `eco` — 38 attractions
   WITH PHONES (the doi attractions are exactly what that list holds); CM
   `dataset_10_0510` "recommended attractions" (CC-BY, catalogued, resource is
   a URL list — needs one look). Both awaiting the same go they were.
5. **DNP park pages, light web checks** (~8 parks: อินทนนท์, สุเทพ-ปุย,
   ออบหลวง, ห้วยน้ำดัง, ศรีลานนา, ขุนแจ, แม่ตะไคร้, ลำน้ำกก): the posted
   entry-fee spread as the gate posts it, gate hours, and the named viewpoints
   inside each park. Robots and terms read first, urllib with the identifying
   UA and 3 s spacing, exactly as the WO-19 venue reads were done. This is
   also where a stated ทะเลหมอก season may come from — the park's own page,
   dated, never our meteorology.
6. **The cross-shelf `view` tag** (WO-15 machinery): 54 measured name-claims,
   families `ชื่อบอกวิว · view (by its own name)` — the venue's name is the
   venue's claim and `tagVia` says so. Zero network; renders pills on ~54
   pages and two tag pages per province. Say go and it ships; say wait and
   the census files keep.
7. **Her own pictures.** `data/curated/image_picks.json` reaches shelves
   through `art()` on four axes; a season/topic pick for the น้ำตก and
   viewpoint shelf heads is hers to choose, never a bot's. And the door
   survey's script — fee posted, gate hours, road, songthaew, parking, drone
   rules posted, sunrise/sunset AS STATED — wants her wording the same way
   the toilets sentences and the WO-2b class sentences do.

## Postscript, 2026-08-21 — the seed list was the wrong instrument

The NEVER report above asked a **fifteen-name seed list** whether it was
present. That is the pattern [[feedback_known_empty_can_be_wrong]] and
[[feedback_mine_full_breadth]] both warn about, written into the README ground
rules the same day this note was, so the audit was rebuilt to read every
record's own name instead. Three things fell out, none of them visible before.

**1. The roll was giving a false green.** ภูชี้ฟ้า — the most famous sea-of-mist
viewpoint in Chiang Rai — read `present`. It is present: as **two register rows,
neither with a pin, neither on any view shelf.** A reader who searches the name
finds it; a reader browsing viewpoints never does. The report now separates
`findable` (on a view shelf AND pinned) from `present`, and names what is
missing. ดอยตุง (6 records) and ผาฮี้ (5) read the same way. **Present is not
findable** and this file said otherwise for a day.

**2. HIDING — 11 declaring names on shelves a view-seeker never opens**, and the
useful part is that they are three different things, now sorted rather than
lumped: **SPOT** (5 — candidates, incl. แก่งผาได and a จุดชมวิว filed under no
child), **CONTAINER** (5 — วนอุทยานน้ำตกบัวตอง is the forest park that *holds*
the falls; moving it onto the waterfall shelf would say a park is a waterfall),
**STATION** (1 — ชุมชนบ้านแม่ต๋ำน้ำตก is a village named for the falls). Plus 9
STRAYS held out by the toponym guard: โรงเรียนบ้านน้ำตกแม่กลาง is a school,
วัดน้ำตกแม่กลาง a temple, บ้านถ้ำ a cave *village*. Bare ดอย, ม่อน, ผา and ยอด are
never matched at all — ดอยเต่า and ดอยสะเก็ด are อำเภอ, ผาสุก means wellbeing.
→ `cache/views_review_<prov>.txt`. Deliberately **not** a shelves.json `--emit`:
every other audit here can emit because a shop's sign states its trade, but a
falls is a place in the landscape and the same name sits on the park around it,
the ranger office at its gate and the village down the road.

**3. The register door is already open, and half-used.** `cr-dgth-eco-*` records
are in the catalogue — **35 Chiang Rai attractions, every one with a phone**,
harvested by the WO-23 hot-springs session. Only the hot springs were given a
sub. **261 records sit on the sights shelf matching no child** (cm 27, cr 234),
including ภูชี้ฟ้า, ภูชี้ดาว, ถ้ำเสาหินพญานาค, สิงห์ปาร์ค and **Nan's own
Chiang Rai clock tower**. The register's one type field says
`แหล่งท่องเที่ยวเชิงนิเวศ` for all of them, so it cannot sort them and nothing
was auto-shelved.

**And the cross-source pairs are complementary, not duplicates.** น้ำตกขุนกรณ์:
the eco row holds the **phone** and no pin, the OSM node holds the **pin** and no
phone. สิงห์ปาร์ค the same. This is the school/medical dupes pattern with the
sides swapped — worth settling by hand, never by id.

**Also written:** `cache/views_dupes_cm.txt` — one real pair on the waterfall
shelf itself (Siribhume Waterfall / น้ำตกสิริภูมิ, 205 m). Proposed, never
folded; which id survives is a real choice.

**The `view` tag (door 6) did not ship, on purpose.** `data/tags.json` derives
every one of its 76 tags from an attribute, a facet or geometry, and derives
**none** from a name — its own comment says so in words. A name-claimed view
would be the first, and overturning that quietly in order to ship a tag is
the wrong trade. Either the claim becomes an `attr` with provenance (`viewClaim`,
the way `brand` works) and the existing `attr` rule reads it, or the tag waits.
Nan's call; the census keeps in `cache/views_claims_<prov>.txt` (55).

## Open for a human

- **The Siriphum cluster**: OSM holds three nodes around the same falls
  (สิริภูมิ ×2 spellings + "Siribhume", and one whose Thai says สิริภูมิ while
  its English says Sirithan — a different falls on the same road). Real
  duplicates are PROPOSED, never folded: they want a
  `data/curated/merges.json` eye, same as the school pairs.
- **The nameless 152**: the culture cache holds 45 CM + 107 CR
  `tourism=viewpoint` elements with NO name, skipped by the
  no-shelf-for-the-nameless rule. That rule is right for a directory; but
  WO-20's maps could DRAW them as a layer without listing them — a map may
  show what a directory does not name. Nan's call whether that thread gets
  pulled.
- `cache/views_claims_<prov>.txt` — the 54, for the tag go.
- `cache/elephant_review_<prov>.txt` — now 270 rows, still the menu for the
  REST of the attractions (hot springs, gardens, canyons, the Grand Canyon
  water parks — ผาช่อ and the canyons deliberately did NOT enter today:
  a canyon is not a viewpoint, and a wrong shelf is worse than a wait).
