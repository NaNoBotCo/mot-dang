# ศาล-ศาลเจ้า-หลักเมือง — the shrines: the shelf the wat category promised · WO-39 · 2026-08-27

*Nan's ask: "a deep dive and enrichment for mot dang on spirit houses and
shrines around Chiang Mai and Chiang Rai." This note is the measurement, the
rule, and the shape. Read with `MARCHING-ORDERS.md` WO-39. The audit is
`importers/audit_shrines.py`; run it any time, it fetches nothing. No crawl
runs on this order — the group is STAGED and waits for Nan's go.*

## The measurement, before any proposal

| What a reader asks | What the site held on 2026-08-27, evening |
|---|---|
| ศาลเจ้าใกล้กาดหลวง? | **Not in the catalogue.** ศาลเจ้าปุงเถ่ากง — the oldest Chinese shrine in Chiang Mai, พ.ศ. 2419 carved on its roof beam, by the flower market, in เทศบาลนครเชียงใหม่'s own telling — is absent from 20,699 records. So are ศาลเจ้ากวนอู and ศาลเจ้าแม่ทับทิม beside the Ping. The one Chinese-shrine hit in all of Chiang Mai city is a housing project named after one. |
| ศาลหลักเมืองเชียงใหม่? | The answer is a page nobody has: Chiang Mai keeps no freestanding city-pillar shrine — the pillar is เสาอินทขีล inside วัดเจดีย์หลวง, and the corner shrine ศาลเจ้าพ่อหลักเมืองแจ่งกระต๊ำ guards the moat's south-east angle. Both ARE in the catalogue — filed under bare `wat` and `sights` where no shelf can say what they are. |
| The category? | The top shelf has been named **วัด-สิ่งศักดิ์สิทธิ์ / Wats & Sacred Places** since launch, and in 2,680 records it holds 2,677 with no sub at all. Its ONE child (ศาลพระภูมิ, `lens: spirit-house`) holds ONE record. The second thing the shelf's own name promises has never had a place to stand. |
| Why zero? | **No crawl group has ever asked for a shrine.** `historic=wayside_shrine` appears in no query; `amenity=place_of_worship` was never asked for ANY religion (the 2,084-strong wat shelf is the ONAB register's fold plus mueang-map's import). The culture group's `nwr["historic"]["name"]` dragnet swept exactly THREE named shrines inside the near ring — Kuan Imm Palace, พิฆเนศวรเทวาลัย, one ศาลพระภูมิ — and the `["name"]` filter held every unnamed one out. |
| How big is the hole? | The census (cache/census/, 2026-08-07) counts `place_of_worship` **1,595 in TH-50, 700 in TH-57** — churches, mosques, ศาลเจ้า and วัด together; it has no `historic` file and no religion split, so the wayside-shrine count is UNMEASURED until the staged group runs. `shop=religion` (สังฆภัณฑ์, spirit-house dealers): CM 1, CR 10 — the trade is barely mapped anywhere. |
| What DID arrive, despite everything? | Thirteen real public shrines, read out of the names in Thai: two city pillars (เสาสะดือเมืองเชียงราย at วัดพระธาตุดอยจอมทอง — wikidata Q6667224, inception 1987 — and ศาลหลักเมืองแม่สาย), the founder-king shrines (ศาลเจ้าปู่พญาแสนภู at Chiang Saen, หอพญามังราย in the old city, พระราชานุสาวรีย์พญามังราย in Chiang Rai), three ศาลสมเด็จพระนเรศวรมหาราช, two Chinese shrines out of town (บ้านถ้ำปลา แม่สาย; จี้กงหน่ำพิ้งเกาะ from WO-16's religious list, pinless), a Ganesha devalaya and a Ganesha shrine, Kuan Imm Palace. Most sit under bare `wat`, visible only in the alphabet river of 2,680 temples. |
| Can search find them? | The mined thesaurus already rings shrine ↔ spirit house ↔ ศาล ↔ ศาลพระภูมิ ↔ ศาลเจ้า ↔ หอผี — the ring works; it points at an empty shelf (the น้ำพุร้อน situation exactly). What it lacks is the pillar family (หลักเมือง, อินทขีล, สะดือเมือง, "city pillar") and the devalaya words — a reader typing "city pillar" gets nothing on the way to a record that exists. |

## The strays, each one witnessed (the fences the audit owns)

Reading ศาล across 20,699 names in the shop's own language finds every trap
worth fencing, and each fence below carries its witness:

- **ศาลา is not ศาล.** ศาลาธรรม (way/311213404) is a dhamma pavilion;
  ศาลากลาง is the provincial hall. The match is `ศาล` not followed by `า`.
- **The courts.** ศาลแขวงเชียงดาว, ศาลอุทธรณ์ภาค 5, ศาลเยาวชนฯ (all in
  cache/overpass/cm/government.json) — and แยกศาลเด็ก, the intersection the
  post office is named for. Court words after ศาล fence the record out.
- **…ไพศาล embeds ศาล.** บริษัทเวชไพศาลฟาร์ม่า is a pharmacy;
  โรงเรียนคริสเตียนไพศาลศาสตร์ is a school. ไพศาล (vast) ends in the letters
  ศ-า-ล, so bare ศาล must anchor to the name's start or a boundary.
- **เจ้าพ่อหลวง is the King.** Six OBEC schools named
  โรงเรียนเจ้าพ่อหลวงอุปถัมภ์/เจ้าแม่หลวงอุปถัมภ์ are royal-patronage
  schools, not shrines. The หลวงอุปถัมภ์ compound fences.
- **หน้าศาลเจ้า is a place BESIDE the shrine.** ขาหมูแสนคำ (หน้าศาลเจ้าแม่จัน)
  is a pork-leg stall giving directions — the locative words หน้า/ใกล้/ข้าง/
  ตรงข้าม before ศาล mean the name is borrowing the landmark. (And note what
  that name proves: the Mae Chan shrine is real enough to navigate by, and
  absent from the directory that lists the stall.)
- **Namesakes.** ทับทิมทอง is two restaurants; ร้านเจกวนอิม is a เจ shop;
  บ้านเอื้ออาทรเจ้าแม่กวนอิม is public housing named after the temple nearby;
  ดอยศาลเจ้าศรีสมบูรณ์ is a PEAK named for the shrine on it and keeps its
  peak shelf.

## The rule this shelf runs on

The elephants' rule was *the venue states*; the springs', *the measurement
carries its source*. Here:

**The keeper names the shrine; the calendar carries its source; nothing here
awards power.** A shrine's kind (ศาลเจ้า, หลักเมือง, เทวาลัย, หอ) is read off
its own name and keeper, never assigned by us. What a shrine is said to be
good for asking is the tradition's claim and renders as a claim — this site
promises no blessings and gives no ranking of sacredness, no "ศักดิ์สิทธิ์
ที่สุด", no top-ten for wish-granting. Rites and festival ties carry dates
from named sources (the festivals.json discipline — `inthakhin`,
`chinese-new-year`, `suep-chata-mueang` already stand). **Public shrines
only:** a household's ศาลพระภูมิ in a private compound is home practice, not
directory material — what enters is what stands in public ground or welcomes
visitors. And the toilets' two-voices rule holds: a mapped shrine is a point
we are certain of; what a KIND of shrine is (what a หอเสื้อบ้าน is, why a
spirit house is retired to a wat) is class knowledge and renders as the
primer's voice, never as a claim about one address.

## The shape

1. **The child.** `wat` gains `shrine` (ศาลเจ้า-ศาลหลักเมือง / Shrines &
   City Pillars), `match: {sub: "shrine"}`, beside the existing ศาลพระภูมิ
   child. The thirteen found records reach it through
   `data/curated/shelves.json` — the WO-22 arrangement, each entry sourced
   `osm name: <the sign>` (or the open list that carries it), because the
   sign is the keeper's own word.
2. **The register.** `data/shrines.json`, the festivals.json genre: the
   shrines a reader plans around, each row carrying kind, province,
   `recordId` where the catalogue holds the place, the rite tie by festival
   id, `confidence` per row (`record` / `stated` with a fetched source /
   `general-knowledge` / `needs-verification`), and sources with read dates.
   Seeded 2026-08-27 with the canon both provinces actually navigate by:
   อินทขีล and แจ่งกระต๊ำ, ปุงเถ่ากง (เทศบาลนครเชียงใหม่'s own article, read
   today), ปู่แสะย่าแสะ (th.wikipedia, read today — rite เดือน ๙ เหนือ, shrine
   at ดอยคำ), the Mangrai and Saen Phu and Naresuan shrines, both navels,
   แม่สาย's pillar, the Chinese shrines of both towns, วัดห้วยปลากั้ง's 69 m
   เจ้าแม่กวนอิม (th.wikipedia, read today). What could not be read stays in
   `unverified` and never renders (the honours.json rule) — silpa-mag 403s
   bots; the Inthakhin Wikipedia title 404s and its facts stand on
   festivals.json's own entry plus the วัดเจดีย์หลวง article.
3. **The page.** `/san.html` (shrine_layer.py, the namphuron shape): the
   drawn two-province map, the register grouped by kind, and the primer —
   ศาลพระภูมิ vs ศาลเจ้าที่, what a ศาลเจ้า is and who keeps it, หลักเมือง /
   อินทขีล / สะดือเมือง and the เสื้อเมือง idea, the เทวาลัย, and the one
   class fact every Thai reader already knows and no crawl will ever hold:
   where spirit houses go to retire (the wat wall, the sacred tree, the
   สามแพร่ง) — told as tradition, sourced to the words, promising nothing.
   Words-you-will-meet closes it, thairoots-linked like the springs page.
4. **Search.** Thesaurus rings: shrine/joss house/ศาลเจ้า/ศาลเจ้าพ่อ/ศาลเจ้าแม่;
   city pillar/lak mueang/ศาลหลักเมือง/เสาหลักเมือง/หลักเมือง/อินทขีล/สะดือเมือง;
   spirit house/ศาลพระภูมิ/ศาลเจ้าที่.
5. **STAGED, NOT RUN — the crawl group.** `shrines` in `crawl_overpass.py`
   (WIDE, both provinces area-clipped — the pillars live in แม่สาย and
   เชียงแสน, not the ring): `historic=wayside_shrine`;
   `place_of_worship` religion taoist / confucian / hindu; `shop=religion`
   (the trade); the Thai compounds ศาลเจ้า|ศาลหลักเมือง|ศาลพระภูมิ|เทวาลัย.
   `shrines_hit()` fences at import, one copy in audit_shrines.py, the
   springs arrangement exactly. **It has not run and will not run without
   Nan's word** — network crawls need the go-ahead, and this order was given
   none. The register and shelf stand on what is already on disk.

## Doors deliberately not opened (named so they stay doors)

- **Churches and mosques.** The place_of_worship census remainder
  (~hundreds in both provinces) is its own order with its own reader — not
  smuggled in under a shrine sub.
- **The monuments.** อนุสาวรีย์ครูบาศรีวิชัย (CR) sits under `wat`;
  สามกษัตริย์ and the Mengrai monument are venerated daily and are
  monuments. Whether "venerated monument" is register material or a retag is
  Nan's call; this order only reports it.
- **The trade shelf.** Spirit-house makers and sellers (ร้านศาลพระภูมิ,
  สังฆภัณฑ์) — 11 mapped in OSM across both provinces; the staged group asks
  for them, and a shelf waits until real records exist.
- **The wichaa join.** 42 rite manuscripts (ท้าวทังสี่, สูตถอน — the
  un-consecration rites) sit transcribed in the manuscript corpus; where
  they surface on wichaa.net is Nan's call, and this page links no URL that
  is not live today.
- **The asked card.** ศาลเจ้าแม่จัน has a pork-leg stall navigating by it —
  the day a reader asks "ศาลเจ้าที่แม่จันชื่ออะไร", the asked.json loop
  answers with this register behind it.

## What runs on this go

Zero fetches beyond the five light reads above (all dated in the register's
sources; the two refusals recorded). The audit prints SHELF / FILED / STRAYS /
LIST / NEVER; shelves.json seats the thirteen; the register and page build;
the gates run; the walk ships what clears. The crawl group waits at the door
with its fence already hung.
