# หอสมุด · หอศิลป์ · หัตถกรรม — the culture shelf, in three different states of neglect

Proposal, 2026-08-18. Status: **PLAN, plus step C staged.**
`importers/audit_culture.py` is written and has been run; its measured yields
are in the tables below. Nothing else is built. **Nothing is deployed.**
Scope set by Nan in two passes: libraries, museums, bookshops — then art
galleries, culturally important handicraft places, and studios.

Read alongside `notes/massage-granularity-proposal-2026-08-17.md`. That note is
the template this one follows: measure the shelf, name the mistake it lets a
reader make, give the tree children that describe the thing, mine only what the
place says about itself, and send the rest to a door survey.

---

## The measurement, before any proposal

13,910 records across CM + CR. Six domains were asked for. They are not in the
same condition, and the fix is different for each.

| Domain | Records | State |
|---|---|---|
| Museums | 58 | crawled, filed under one undifferentiated `sub` |
| Galleries | 14 | crawled, same — and conflated with studios |
| Art studios | 14 (lens) | half are the same 14 galleries, double-counted |
| Handicrafts | 85 (`shopping/crafts`) | a dragnet: latex factories, a barber, a guesthouse |
| Libraries | 20 (lens) | **never crawled.** Inherited from mueang-map, 2024 |
| Bookshops | **0** | **never crawled, and no shelf to be empty on** |

### 1. Bookshops: no ant was ever sent

`shop=books` appears nowhere in `importers/crawl_overpass.py:QUERIES`. Neither
does `shop=stationery`. There is no `bookshop` key in `data/categories.json`.
A reader looking for a bookshop on motdang.net does not meet an empty shelf —
they meet nothing, because the shelf does not exist.

This is the exact failure the crawler's own comment already documents for
home-services, community and business:

> Three whole categories were given shelves at launch and never a query, so
> they have sat at zero ever since: a reader saw "the ants are still
> collecting" where the truth was that no ant was ever sent.

Bookshops are one step worse — they were not even given the shelf.

### 2. Libraries: twenty records, seventeen of them a university's

`amenity=library` is likewise in no query group. The 20 library records are
lens points inherited from the mueang-map import (`importers/import_all.py:32`,
`"library": ["sights"]`). Of those 20:

- **17 are Chiang Mai University faculty libraries** — ห้องสมุดคณะสังคม,
  ห้องสมุดคณะวิจิตรศิลป์, ห้องสมุดคณะเกษตรศาสตร์, and so on down the faculty list.
- 3 are libraries a member of the public can actually use:
  หอสมุดแห่งชาติรัชมังคลาภิเษก (the National Library's Chiang Mai branch),
  ห้องสมุดประชาชนอำเภอเมืองเชียงใหม่ (the district public library, which sits at a wat),
  and TCDC — already double-shelved as coworking by the 2026-08-07 sweep.
- **Chiang Rai has zero libraries.** A whole province.
- **All 20 carry no hours, no phone, no website.** Zero of twenty, on all three.

For a library that is not a detail. *Is it open, and am I allowed in* is
substantially the whole record. The shelf currently answers neither, and its
headline reading is "Chiang Mai University's internal libraries," which is not
what anyone who taps ห้องสมุด is looking for.

Also worth stating plainly: libraries are filed under **`sights`**. A faculty
library is not a sight. Nobody visits ห้องสมุดคณะเศรษฐศาสตร์ on a day out.

### 3. Museums and galleries: the massage shelf's problem exactly

72 records, two children, `museum` (58) and `gallery` (14). A reader cannot
tell apart:

- พิพิธภัณฑสถานแห่งชาติ เชียงใหม่ — the national museum, Fine Arts Department
- พิพิธภัณฑ์วัดเกตการาม — a temple's own collection in its ho trai
- Hmong Culture Museum / พิพิธภัณฑ์หมู่บ้านชาวเขา — ethnographic halls
- Art in Paradise — a paid trick-art photo attraction
- Elephant Poopoopaper Park — a paper workshop with a tour
- คุ้มเจ้าบุรีรัตน์ — a historic Lanna house
- Northern Telecoms of Thailand Museum — a single-subject corporate museum
- Gallery Seescape / SAC Residency — artist-run non-commercial spaces
- Suvannabhumi Art Gallery — a commercial dealer that sells what is on the wall

All 72 say `museum` or `gallery` and stop. **OSM itself already says more than
we keep:** `museum=history` (6), `museum=art` (5), `museum=railway` (1),
`museum=nature` (1) are on the raw elements in `cache/overpass/` and are
dropped at import — only `tourism=gallery` survives, as `attrs.discipline`.
`fee` (9) and `wheelchair` (6) do survive and nothing renders them as a shelf.

**The studio double-count.** 7 of the 14 `art-studio` lens records are the same
records as 7 of the 14 `gallery` records. The lens and the sub are two names for
one thing here, and `sights/art-studio` and `museums-galleries/gallery` are two
doors onto a mostly-identical list. That wants settling, not extending.

### 4. Handicrafts: the shelf that describes almost nothing it holds

`shopping/crafts` holds 85 records, gathered by `craft=*` + `shop=gift` +
`shop=second_hand`. What is actually on it:

Genuinely significant — วัวลายศิลป์ (Wualai silver), ห.ส.น.เตาเม็งราย (Mengrai
Kilns, celadon), Sop Moei Arts (Karen textile, fair trade), Thai Tribal Crafts,
Vila Cini (Lanna silk), Weave Artisan Society, Kang Wat.

Also on the same shelf — S.N. Latex and Karaked Latex (tourist mattress
showrooms), 053 Chemical Brothers Tattoo & Barber, Elephant parade guesthouse,
Anusarn Market, Dogs siam, Herb Basics (a cosmetics chain), Сувениры и открытки.

And here is the finding that matters most:

> **The craft clusters Chiang Mai is internationally known for are, as records,
> absent — and name-matching for them returns health stations.**

- **เครื่องเขิน — Lanna lacquerware — has ZERO records.** A craft with its own
  museum in this city, and the directory has never heard of it.
- **บ้านถวาย** (Ban Tawai, the woodcarving village) — one record for the whole village.
- **บ่อสร้าง** (Bo Sang umbrellas) — one real record. The other 26 "matches" for
  ร่ม are รพ.สต. ร่มเกล้า and a restaurant called เรือนร่มไม้.
- **วัวลาย** (Wualai silver) — one real record. Most "matches" are the health
  stations *on Wualai Road*.
- **สันกำแพง** (San Kamphaeng silk) — the matches are โรงพยาบาลสันกำแพง and
  San Kamphaeng Animal Hospital.

This is the airport failure again, in a domain where it costs more. The
crawler's own note says the directory's only "Airport" records were a petrol
station and a hotel with the word in their names, and a landmark list built by
name-matching happily pinned one of them. Here, a list built by name-matching
pins a health station as a silver workshop.

---

## The mistake this shelf currently lets a reader make

Four, and they are not the massage shelf's four:

1. **Turns up at a library that was never open to them.** Faculty libraries at
   CMU want a student card. The reader has driven across town.
2. **Turns up at a museum on the wrong day.** 26 of 72 carry hours; the other
   46 are silent, and small temple and village museums here are genuinely
   shut more often than they are open.
3. **Pays a ticket they did not expect, or pays a different price than the
   person in front of them.** Two-tier คนไทย/ต่างชาติ pricing is normal and
   openly posted at Thai museums. It is not stated anywhere on this site, and a
   directory that is price-forward everywhere else goes quiet here.
4. **Goes to "a handicraft village" and arrives at a coach-park showroom** —
   or, the other way round, never learns that the workshop behind the shop lets
   you watch the work, which is the entire reason to go.

Note what is *not* on that list: nothing about authenticity. Per the standing
rule, this shelf will not sort places into real-craft and tourist-craft. A
showroom that buys in stock and a workshop that carves on site are **different
in a way you can see from the pavement** — *is anyone making anything here,
today* — and that is the distinction to record. Not which one deserves respect.

---

## The governing rule for this shelf

The massage shelf's rule was: never infer respectability. The equivalent here,
and it is the one thing in this proposal that is not negotiable:

> **Never infer whether a reader is allowed in, and never infer what something
> costs.** Access and price are stated by the institution or read off a board
> at the door by a person, or they are not stated. A library with no access
> note is not "public" and not "restricted" — it is a library we have not asked
> about yet.

The reason is the same shape as the medical shelf's: a wrong "no" stops someone
going. A wrong "yes, public" sends a person on a bus to a locked faculty door.
Absent is not false, and `data/facets.json` already says so in its own header.

Second rule, narrower: **"culturally important" is not a facet.** Nan's ask
names culturally important handicraft places, and they are real — but
importance is not a field this directory will hold, because the moment it is a
field it is a ranking, and the house has refused rankings everywhere else
(`CLAUDE.md:234`, temples are never ranked; the ant rank is never weighted).
What this shelf can carry instead, all of it checkable:

- **the craft, named in Kammuang/Thai with its own word** — เครื่องเขิน,
  ศิลาดล, กระดาษสา, ตุงล้านนา, เครื่องเงินวัวลาย, ร่มบ่อสร้าง
- **whether the making happens on site**, and whether a visitor may watch
- **the register**: OTOP tier, ผลิตภัณฑ์ GI, ครูศิลป์ของแผ่นดิน / ครูช่าง
  designations from SACICT — these are *paperwork*, awarded by a named body on
  a dated certificate, exactly like the สบส. licence on the massage shelf
- **the cluster it belongs to** — บ้านถวาย, บ่อสร้าง, วัวลาย, สันกำแพง — as a
  place-relation, the same way `attrs.nextDoor` already works

Importance then reads off the register and the cluster, sourced and dated,
without this site ever awarding it.

---

## What to build

Six domains, four moves each, in the order they pay.

### A. Ask for the tags nobody ever asked for  *(one network fetch, Nan's go)*

New query group in `importers/crawl_overpass.py`. Nothing here is exotic; these
are the tags OSM actually uses in these two provinces.

```
"reading":  amenity=library, shop=books, shop=stationery, shop=newsagent
"making":   craft=* (already partly via "crafts"), shop=art, shop=pottery,
            shop=musical_instrument, shop=fabric, shop=jewelry + craft=jeweller,
            tourism=artwork["name"], shop=antiques
"culture":  + museum=*, historic=* refinement (existing group, extended)
```

Expected yield is genuinely unknown and this note will not guess it. It is one
Overpass call per province per group, cached under `cache/overpass/`, and
**it does not run until Nan says run it.**

### B. Give the tree children that describe the thing

**New cat `read` — อ่าน-หนังสือ · Books & Libraries.** Libraries leave `sights`,
where they never belonged.

| key | ไทย | English | filled by |
|---|---|---|---|
| `library-public` | ห้องสมุดประชาชน | Public libraries | crawl + register |
| `library-national` | หอสมุดแห่งชาติ | National Library | curated, 1 record |
| `library-university` | ห้องสมุดมหาวิทยาลัย | University libraries | crawl (the 17) |
| `library-temple` | ห้องสมุดวัด-หอไตร | Temple libraries | curated + wichaa join |
| `library-childrens` | ห้องสมุดเด็ก | Children's libraries | door survey |
| `library-foreign` | ห้องสมุดภาษาต่างประเทศ | Foreign-language libraries | curated (AUA, BC, AF) |
| `bookshop-new` | ร้านหนังสือ | Bookshops | crawl |
| `bookshop-used` | หนังสือมือสอง | Secondhand books | name + door |
| `bookshop-foreign` | หนังสือภาษาอังกฤษ | English-language books | name + door |
| `bookshop-dhamma` | หนังสือธรรมะ | Dhamma books | curated |
| `stationery` | เครื่องเขียน-หนังสือเรียน | Stationery & textbooks | crawl |

**`museums-galleries` gets real children**, and the studio double-count is
settled by making `art-studio` mean *a working studio*, not *a gallery seen
from another angle*:

`museum-national`, `museum-temple`, `museum-local` (ศูนย์การเรียนรู้ชุมชน),
`museum-ethnographic` (ชาติพันธุ์), `museum-house` (บ้านโบราณ-คุ้ม),
`museum-subject` (single-subject), `gallery-commercial` (sells the work),
`gallery-artistrun` (หอศิลป์-พื้นที่ศิลปะ, does not), `art-studio` (someone
works here), `attraction-paid` (Art in Paradise and its kin — a real category,
named without sneering).

**New cat `crafts` — หัตถกรรม-งานฝีมือ**, lifted out of `shopping` where it is
currently a gift-shop dragnet. Children by **craft**, because the craft is what
a person searches for:

`silver` (เครื่องเงิน), `lacquer` (เครื่องเขิน), `celadon` (ศิลาดล-เครื่องปั้น),
`woodcarving` (แกะสลักไม้), `textile` (ผ้าทอ-ผ้าชาติพันธุ์), `sa-paper`
(กระดาษสา), `umbrella` (ร่มบ่อสร้าง), `tung` (ตุงล้านนา), `silk` (ผ้าไหม),
`bamboo-rattan` (จักสาน), `metal-nielloware`, `craft-village` (the clusters
themselves, as places).

The latex showrooms, the barber and the guesthouse go back to the shelves they
belong on via `data/curated/shelves.json` — additive, never subtractive, same
discipline as the coworking sweep.

### C. Mine only what the place says about itself

`importers/audit_culture.py` — new, zero-network, read-only, `--emit` prints
`shelves.json`-ready entries, the exact contract of `audit_massage.py` and
`audit_shelves.py`. It reads three things and nothing else:

1. the record's **own name** (ห้องสมุดประชาชน→public, มือสอง→used, ศิลาดล→celadon)
2. **OSM's own subtag** where it exists (`museum=history`, `craft=potter`)
3. **the operator** where OSM states it (กศน., กรมศิลปากร, มหาวิทยาลัย)

**Built and run, 2026-08-18. Measured yield, 59 entries proposed across 191
candidate records:**

| report | reads | of | note |
|---|---|---|---|
| LIBRARY | 15 | 20 | 13 university, 1 national, 1 public |
| MUSEUM | 26 | 72 | 36% — 21 off names, 5 more off OSM's `museum=*` |
| CRAFT | 13 | 85 | 15% — and four crafts read **zero** (below) |
| BOOKS | 5 | — | whole-corpus scan; all 5 crawled under another tag |
| STRAYS | 8 | 85 | craft-shelf records whose own name says otherwise |

A fifth to a third, exactly as the massage precedent predicted. The rest wait
for someone at the door, and a shelf that says nothing about a place nobody has
visited is the true output.

**Four crafts read zero and all four are real here:** เครื่องเขิน (lacquer),
แกะสลักไม้ (woodcarving), ตุงล้านนา (tung), จักสาน (bamboo/rattan). These are the
`lacquer` argument from the proposal above, now measured rather than asserted.

**Three findings the auditor turned up that are worth fixing on their own:**

- **บ้านถวาย is filed as `market/fresh`.** Ban Tawai — the woodcarving village,
  an OTOP village of national standing — is in this directory as a wet market,
  and it is the only record the whole village has.
- **Two of the twenty "libraries" are not libraries.** อาคารเฉลิมพระเกียรติใหม่
  and อาคารพาวเวอร์ส ฮอลล์ are buildings on a campus that the mueang-map lens
  marked as libraries. They should come off the shelf.
- **ซีเจ.เครื่องเขียน, a stationery shop, is filed as `food/thai`** — a Thai
  restaurant. ลิขิตศิลป์ เครื่องเขียน is filed under `shopping/diy` and
  ไอเดีย เครื่องเขียน under `essentials/convenience`. Three stationery shops,
  three different wrong shelves, because there is no right one.

**Two regex traps found while writing it, both now fenced and commented in the
source**, because both would have shipped wrong claims quietly:

- `(?<!ห)วัด` — **จังหวัด, the word for province, ends in the letters วัด**, so
  "พิพิธภัณฑสถานแห่งชาติ จังหวัดเชียงใหม่" read as a *temple* museum. Thai has
  no spaces to fence on; the trap is a bare substring. (The fence is ห, not จัง:
  จังหวัด is จ ั ง ห ว ั ด.)
- `\bse-ed\b` — the SE-ED bookshop chain written with an optional separator
  (`\bse\s*-?\s*ed\b`) matches the ordinary English word **"Seed"**, and filed
  Liberated Seed Roasters as a bookshop.

### D. The facets — the questions no crawl can answer

New `reading` facet set in `data/facets.json`, `appliesToCat: ["read",
"museums-galleries", "crafts"]` (the mechanism massage added on 2026-08-17).
Every one carries `ask_th`/`ask_en` — those strings are the door survey's
script, and nothing renders them, by design.

**Access** — เข้าฟรีทุกคน · ต้องเป็นสมาชิก · ต้องมีบัตรนักศึกษา · ต้องนัดล่วงหน้า
**Money** — ค่าเข้า · ทำบุญตามศรัทธา (donation box) · **ราคาคนไทย/ต่างชาติต่างกัน**
(stated as a fact with both numbers, per the price-forward rule — it is a
posted board, not an accusation)
**Reading** — ยืมได้ (lending) vs. อ่านในห้องสมุด (reference only) · มุมเด็ก ·
โต๊ะอ่านเงียบ · ปลั๊กไฟ · wifi · แอร์
**Looking** — ป้ายภาษาอังกฤษ (English labels) · ถ่ายรูปได้ · wheelchair
**Making** — ทำให้ดูหน้าร้าน (work happens on site) · เข้าชมการผลิตได้ (you may
watch) · เวิร์กชอปสำหรับผู้มาเยือน (workshop you can join) · ส่งของได้ (they ship)
**Register** — OTOP tier · GI · ครูศิลป์ของแผ่นดิน/ครูช่าง · จดทะเบียนวิสาหกิจชุมชน

No "no certificate seen" facet, no "not open to the public" facet. Same reason
the medical shelf has no absence facets: a rule about a named institution built
from one person's afternoon is testimony it cannot support.

### E. KNOWN_EMPTY, with a reason per shelf

`tests/test_facets.py` fails the build on a child that finds nothing, unless it
is listed with a reason. Expect `library-childrens`, `bookshop-dhamma`,
`museum-house`, `tung`, `lacquer` and several craft keys to land there on day
one — and the reason for `lacquer` is worth writing out in full, because a
shelf that reads "the ants are still collecting" is the honest statement for a
craft that certainly exists in this city and that OSM has never tagged.

### F. The join nobody else can make  *(the reason to do this at all)*

wichaa.net holds **6,990 manuscripts**, stamped with รหัสวัด via
`project_wat_registry`'s join key, and Mot Dang holds 596 wat records keyed the
same way. Temple libraries — หอไตร — are the physical buildings those
manuscripts live in.

So: a `library-temple` or `museum-temple` record can carry
`attrs.holdsManuscripts` and link straight to that wat's holdings on wichaa,
using a join key that already exists on both sides. `importers/link_wichaa.py`
is already the house pattern for exactly this.

**No other directory in the world can express that**, and it is the same
argument ตอกเส้น and ย่ำขาง made for the massage shelf: the tree can say
something true here that no imported taxonomy has a slot for.

### G. A reader sheet, only if the copy earns it

The massage note's own lesson — *the copy decided the count, not the plan.*
One candidate, and it should not be written until B–D are real:
**craft-words**, the recognition sheet — เครื่องเขิน, ศิลาดล, กระดาษสา, ตุง,
จักสาน, with the word, the RTGS, the tone-marked reading and what the object
actually is. Two sides of one A4, enforced by `page_count()`, no
`overflow: hidden` on `.page`.

---

## What this note is deliberately not proposing

- **No authenticity sort.** No real-craft/tourist-craft, no "genuine artisan"
  badge. On site vs. not on site is visible; deserving is not.
- **No importance ranking.** The register and the cluster carry it, sourced.
- **No inferred access.** A university library is not marked closed to the
  public until somebody asks at the desk.
- **No guessed prices.** Any band that ships unwalked gets the
  `_pricesVerified: false` DRAFT stamp, same as the massage sheets.
- **No re-derived contacts.** WO-1's correction stands as a standing warning:
  do not claim a source fixes contactability until it has been measured.

## Order of work, and where it stops

1. **B** (the tree) and **C** (the auditor) need no network and no decisions
   from anyone. Stage them.
2. **A** (the crawl) is one confirmed fetch and gates most of the fill.
3. **D** (facets) can be staged behind B.
4. **E** follows whatever A and C actually return.
5. **F** is a join against wichaa and is the highest-value item here.
6. **G** waits.

Nothing in this note ends in a deploy. `python3 publish/deploy.py --yes` is
Nan's move and always has been.
