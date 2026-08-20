# น้ำพุร้อน — hot springs: the shelf that held zero, and the whole north

*2026-08-20. Nan: "Please BIGLY enrich hot springs — don't limit yourself to
cm and cr proper. the whole north is ok." That sentence is the go for this
order's fetches, scoped to hot springs, and it widens the frame past the two
provinces for the first time. This note is the measurement, the rule, and the
shape of the build. Read with `MARCHING-ORDERS.md` WO-23. The audit is
`importers/audit_hotsprings.py`; run it any time, it fetches nothing.*

## The measurement, before any proposal

| What a reader asks | What the site held on 2026-08-20, evening |
|---|---|
| The famous one — สันกำแพง? | **Not in the catalogue.** Chiang Mai, 12,951 records, holds ZERO hot springs. น้ำพุร้อนสันกำแพง, โป่งเดือด, เทพพนม, the Fang springs — none. The only CM record wearing the word is a school in Mae On. |
| Chiang Rai's? | Three arrived 2026-08-20 with WO-16's eco list — ป่าตึง, แม่ขะจาน, ห้วยทรายขาว — with PHONES but **no pins and no sub**, so they sit under `sights` where no child shelf can show them. Plus a resort named after one and a public park wearing the name. |
| Why zero? | **No crawl group has ever asked `natural=hot_spring`** — same failure this file's genre keeps finding (waterfalls, libraries, restaurants): the shelf was never empty, it was never given the chance to be. Meanwhile the WO-19 attraction dragnet already CAUGHT น้ำพุร้อนสันกำแพง (way/95223020), โป่งเดือด, เทพพนม (mapper's spelling น้ำพร้อน), and CR's แม่ขะจาน by name, and fenced every one into `cache/elephant_review_<prov>.txt`, "the menu for a future attractions order". The views order (WO-21) took the waterfalls off that menu; this order takes the springs. |
| Can search find them? | `search_thesaurus.json` already rings hot spring ↔ hotspring ↔ น้ำพุร้อน ↔ บ่อน้ำร้อน. The ring works; it points at an empty shelf. |
| Pai? แจ้ซ้อน? | Off the map by construction — the directory is CM+CR. But a reader soaking is a reader on a day trip, and the springs she actually weighs against each other are ท่าปาย (Mae Hong Son), แจ้ซ้อน (Lampang), ภูซาง (Phayao) beside สันกำแพง and แม่ขะจาน. Nan's widening makes that comparison a page. |

## The rule this shelf runs on

The elephants' rule was *the venue states and nothing ranks it*; the views',
*measured or stated, never awarded*. Here, both at once:

**The spring states; the measurement carries its source; nothing is awarded.**
A temperature is a measurement and renders with who measured it (the
department's survey, the park's own sign) — never rounded into "very hot".
An egg-boiling minute is the operator's own posted claim. A fee is the posted
spread exactly as the gate posts it, `_pricesVerified: false` until a person
stands at one. What the water is said to be good for is the operator's or the
tradition's claim and renders as a claim — this site gives no health advice.
No spring is crowned; no line sorts them into natural and commercial, hidden
and touristy. Sorts stay distance, province and alphabet.

## The shape

Two frames, one order:

1. **CM + CR — full records.** A `hotsprings` crawl group (WIDE, both
   provinces, area-clipped TH-50/TH-57, never a bbox) with four selectors:
   `natural=hot_spring`; `amenity=public_bath` (named); the Thai compounds
   `น้ำพุร้อน|บ่อน้ำร้อน|โป่งน้ำร้อน|โป่งเดือด|ธารน้ำร้อน`; the Latin
   `hot ?spring|onsen`. **Import is fenced** like the elephants file:
   `springs_hit()` borrows `audit_hotsprings.py`'s rules (one copy);
   `natural=hot_spring` states the thing itself; a name-declared element with
   lodging/food tags stays that business (Hot Spring House Resort is a
   hotel); a village wearing the spring's name (`place=*`) stays a village;
   everything undeclared goes to `cache/hotspring_review_<prov>.txt` and
   `classify()` is unreachable. `sights` gains a `hot-spring` child
   (น้ำพุร้อน). JSON-LD `BodyOfWater` — schema.org has no narrower
   HotSpring type. The five already-caught elements file from the WO-19
   cache with no fetch, the same ride views_hit took.

2. **The whole north — the register and the board.** `harvest_hotsprings.py`
   asks the SAME selectors in the other fifteen provinces of ภาคเหนือ,
   one selector per query, area-clipped per province so every entry's
   province is true by construction: แม่ฮ่องสอน TH-58, ลำปาง TH-52, ลำพูน
   TH-51, น่าน TH-55, พะเยา TH-56, แพร่ TH-54, อุตรดิตถ์ TH-53, ตาก TH-63,
   สุโขทัย TH-64, พิษณุโลก TH-65, พิจิตร TH-66, เพชรบูรณ์ TH-67, กำแพงเพชร
   TH-62, นครสวรรค์ TH-60, อุทัยธานี TH-61. Snapshot-first into
   `cache/hotsprings/<prov>.json`, the crawler's own manners imported from
   `crawl_overpass.py` (12 s pauses, mirror rotation, OverpassRemark, the
   asked-twice zero). The register `data/hotsprings.json` holds every
   northern spring — CM/CR rows carrying their record ids, the rest carrying
   their coordinates and sources — and `/namphuron.html` renders it grouped
   by จังหวัด, counts in the Yahoo manner, distance sorts client-side.
   A province with nothing stays unprinted (empty categories hidden by
   design).

3. **What each spring states — curated.** `data/curated/hotsprings.json`:
   for the springs a reader plans a day around, the stated facts with
   fetched sources — the department's measured temperature where its open
   dataset carries one, the park's posted fee spread, hours, pools/private
   baths/egg baskets as the operator's own words. Leads that could not be
   read stay in `unverified` and never render (the honours.json rule).
   `.go.th` refusals are expected (chiangmaipao.go.th and tourismthailand.org
   both 403 bots) and are recorded as what happened, not guessed around.

4. **The trio gets whole.** The CR eco springs merge onto their OSM elements
   where the crawl lands them (merges.json, eyes on every pair): the OSM
   keeper brings the pin, the eco record brings the phone, sources union.
   Subs assigned by the same one-copy name rules at the opendata import.

## Sources, ranked by what they state

| Source | States | Standing |
|---|---|---|
| OSM `natural=hot_spring` + names (area-clipped) | the spot, the pin, sometimes fee/hours | the frame, both frames |
| data.go.th CKAN (กรมทรัพยากรธรณี / DMR, if the inventory is posted) | measured temperature, geology | to check this order — WO-16's harvester genre |
| WO-16 CR eco list (already on disk) | phones, addresses | folded; merges pending pins |
| Park/PAO pages (สันกำแพง อบจ.เชียงใหม่; DNP for แจ้ซ้อน, ห้วยน้ำดัง, ดอยผ้าห่มปก, ไทรงาม) | fee spread, hours, pools | light reads; refusals recorded |
| TAT / tourismthailand.org | — | 403s bots (measured 2026-07-29); not asked |

## What runs on this go

`crawl_overpass.py` gains the group and fetches it for cm and cr;
`harvest_hotsprings.py` walks the fifteen; `import_all.py` folds; the audit
prints SHELF / MENU / REVIEW / NORTH; the layer builds the board; the gates
run; the walk ships what clears. The crawler's User-Agent drops the dead
repository link and carries motdang.net, so a server operator who looks us
up finds a live site (the No-GitHub rule reaching the one string it had
missed).
