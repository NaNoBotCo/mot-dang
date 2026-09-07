# บ้านถวาย — the carving village · WO-51 · 2026-08-31

Nan's ask, 31 Aug 2026: *"a deep dive/enrichment on the woodcarvers' village
(OTOP royal program) south of Chiang Mai. Add everything you find to
motdang.net."*

Built the same day: `/tawai.html`, register `data/curated/carve.json`, layer
`carve_layer.py`, gate `tests/test_tawai.py`, search panel `tawai`, one
`shelves.json` fix, and an llms.txt section.

---

## What the directory held before this order

Measured live, and the layer re-measures every build so these sentences
correct themselves:

| measure | value |
|---|---|
| records within 2.5 km of the Ban Tawai pin | **82** |
| of those, on a shelf a carving shop would land on | **2** (a craft shop and a gallery; neither says carving) |
| of those, whose own name says it carves | **0** |
| records anywhere named บ้านถวาย | **1**, filed `market/fresh` |
| records province-wide whose name says carving/handicraft | **7**, of which the one at Ban Tawai is the village's own name on the market pin |
| records named บ้านเหมืองกุง (the pottery village on the same road) | **0** |
| the province's own 2567 count, Hang Dong souvenir/OTOP outlets | **148** |

WO-10 found the first of these in August and filed it as finding #1: *"บ้านถวาย
is filed as `market/fresh`. The woodcarving village is in this directory as a
wet market, and that one record is all the village has."* This order does not
fix it by re-keying anything — it ADDS `shopping`/`crafts` to the record
through `shelves.json`, the Hub 53 move, so the market shelf and its URL
survive. **The entry is written but not yet applied: it lands on the next
`importers/import_all.py`, which was deliberately not run because another
session's `clothing` crawl (WO-50) was writing into `cache/overpass/` while
this order was being built.**

## The steak trap

`teak`, case-insensitive, returns **71** records here. **58** are steakhouses,
because *steak* contains *teak*. The remaining 13 are cafes, guesthouses,
resorts, a public garden (ลานต้นสัก, which really is a teak stand) and a temple
that romanises as **Pha Teak** (วัดผาแตก). Wood shops among all 71: **zero**.

Same family as the two traps already in CLAUDE.md — `(?<!ห)วัด`, because
จังหวัด ends in the letters วัด, and `\bse-ed\b`, which matched the English
word Seed and filed a coffee roaster as a bookshop. The difference: this one
is not confined to our code. Any reader typing "teak" into any search box has
it, which is why the number is printed on the page instead of quietly fixed.

## The thesis the page is built on

The best source found is twenty years old and critical: ผู้จัดการ's 2549 case
study, **"ทุนใหญ่กลืนโอทอปชุมชนต้นแบบ"** — big capital swallowing the model OTOP
community. It carries the numbers nothing else does:

- 200-odd shops along the irrigation canal belonging to villagers;
- ~4,000 people fed by the trade across the tambon's nine villages;
- a 3×4 m room let at **10,000+ baht** to an incoming trader and **~1,000** to
  a villager;
- a carved dragon at **800 baht** in a canal shop and **3,000** at a frontage
  shop;
- the annual fair, held 29 Jan–4 Feb for fifteen or sixteen years, moved to
  31 Dec 2548–2 Jan 2549 to suit the Night Safari's opening.

That is why the page's spine is **the chain of hands** rather than a shop
list: สล่า (the carver) → แกะสลัก (the block) → เดินเส้น·แต่งลาย (the line work)
→ ลงรักปิดทอง (lacquer and gold) → ทำเก่า (the ageing) → หน้าร้าน (the
shopfront). Six separate people, and the documented price move is at the
sixth. The page states where a reader is standing on that chain. It does not
say who ought to be allowed to sell — that is not ours to award, and the
figures are dated 2549 on the page every time they appear.

The line work is the detail that pays for the whole section: it did NOT come
from the carving shop. A women's group learned the patterns at the Chiang Mai
cultural centre and married them to the wood, which is why a Ban Tawai piece
reads as a Ban Tawai piece.

## The royal question, answered plainly

Nan's ask said "OTOP royal program". OTOP is **not** royal: a government
programme from 2544 (2001), run by the Community Development Department of
the Interior Ministry. Ban Tawai was made Thailand's first **หมู่บ้าน OTOP
ต้นแบบ** in 2547 (2004) and the first **หมู่บ้านท่องเที่ยว OTOP** by the Office
of Tourism Development.

Two things on this page ARE royal-adjacent and they are different in kind, so
the page keeps all three apart rather than blurring them:

1. the village's own naming legend, which attaches to **พระนางจามเทวี** — a
   story a village tells about itself, filed as that;
2. **ครูช่างศิลปหัตถกรรม**, the SACIT master-craftsman title — a state register,
   held here by **นายยรรยงค์ คำยวง**, 2562, in wood, for Ramakien carving.

## The fair drifts, and that is the page's one practical warning

It runs on the **fiscal** year. 34th: 23–26 January 2568. 35th: 26–28 December
2568 — twice inside one calendar year. Anything that prints "every January"
is wrong. The register carries both editions and `tests/test_tawai.py` fails
if the editions list ever collapses to a single month, because that would make
the warning unreadable.

## What refused us, printed on the page

The WO-33 rule, applied: three sources are named as refusals rather than
quietly dropped or, worse, paraphrased as if read.

- `radiochiangmai.prd.go.th` — the source for the 35th fair's 26–28 Dec range.
  **Host did not resolve from this network on 31 Aug 2026.** The opening date
  of 26 Dec is separately carried by the Chiang Mai PAO coverage, which does
  resolve, so the claim is corroborated even though its best source is not
  reachable from here.
- `asaconservationaward.com` — the architects' association's own page for Wat
  Ton Kwen's 2532 award, **connection reset**. The award is cited through Thai
  PBS instead of from the granting body.
- `gotoknow.org` — the ผะหญาล้านนา page deriving **สล่า** from Burmese สย่า
  (ဆရာ, teacher/master). **403 to a plain fetch.** So the note splits: the
  meaning and the name-prefix usage are cited to a reachable source, and the
  etymology is given as an attributed reading rather than a settled fact.

## The section the souvenir page could not carry

**A carved Buddha is not a carved elephant, in law.** `souvenir.html`'s
`finethings` row says handicraft is what "the law leaves wide open" — true of
the elephant, false of the Buddha. Buddha and sacred images sit under
**พ.ร.บ.โบราณสถาน โบราณวัตถุ ศิลปวัตถุ และพิพิธภัณฑสถานแห่งชาติ พ.ศ. 2504**
(amended 2535), which is neither the wood rules nor CITES.

From the Department of International Trade Promotion's own procedure sheet
(*ขั้นตอนการส่งออก โบราณวัตถุ พระพุทธรูป เทวรูป*, last updated Sept 2560 — the
page dates it, because a fee table with no edition reads as current forever):

- the licence is **form ศก.6**, filed with the **สำนักพิพิธภัณฑสถานแห่งชาติ,
  กรมศิลปากร**, 14th floor Thanalongkorn Building, Bangkok, 02-446-8054–56;
- **proof you own it** — a lawful receipt, an ใบอนุโมทนาบัตร, or a letter from
  the abbot of the temple where the image was venerated. *This is the sentence
  that makes "can I have a receipt?" worth saying at the till,* and it is why
  that ask is on the page and on the printed sheet;
- two colour photographs, 3×5 or 4×6 inches, per item; a passport copy;
- **2,000 baht** per piece if the Fine Arts Department judges it Ayutthaya or
  older, **1,000** if later;
- **two days in Bangkok, five to seven in the provinces** — longer than most
  visitors have left;
- and what the sheet lists as exportable: replicas and new products (it states
  an item under five years old does not require permission) and **newly made
  Buddha and sacred images**. A piece carved last month at Ban Tawai is in that
  category, not the antiquities one.

The page turns all of that into one question for the shopkeeper: not "can this
be shipped" — that always gets a yes — but **"do you file the ศก.6, or do I?"**

The souvenir page now points here from its wood row (`see_href` on the
`wildlife.json` row, rendered by a guarded one-liner in `souvenir_layer.py`;
a row without the field renders exactly as before). That is the reciprocal-link
contract `chang.html` and `hom.html` already keep.

## The paper version

`carve-words` — a printed A4 reader sheet, `assets/reader/carve-words.pdf`,
the ninth in `reader_sheets.json`, four blocks: who does which part · the wood
· at the till · if you buy a Buddha image. Published into the built site (third
sheet to be, after hair-words and care-words) on the same argument as those
two: the person who needs these words is on a footpath in Hang Dong with a
shopkeeper waiting. Two of the words on it — **พะยูง** and **พระพุทธรูป** —
change what may lawfully leave the country, which is not a thing to recall from
memory at the till.

## Where this joins the rest of the site

- **`souvenir.html`** holds the carry-flags, the four legal tiers and the CITES
  sources. This page does **not** restate them. It adds only the woods actually
  worked here — ไม้สัก, จามจุรี/ฉำฉา, มะม่วง, กระท้อน, มะกอก, and the two
  regulated ones, พะยูง and กฤษณา — and `tests/test_tawai.py` fails if this
  page's flag for a Dalbergia or Aquilaria row ever disagrees with
  `wildlife.json`'s wood row. Two pages disagreeing about paperwork is worse
  than either page alone.
- **One law worth its line:** พ.ร.บ.ป่าไม้ (ฉบับที่ 8) พ.ศ. 2562 rewrote
  section 7 so that no tree grown on titled land is restricted timber. Teak
  off a plantation and teak off the forest floor stopped being the same object
  in law, and this is the supply-side fact behind everything on the shelves.
- **The road, not the village.** Nan's ask said "south of Chiang Mai", and
  Route 108 carries three things in 15 km: บ้านเหมืองกุง's pottery (Moo 7, Nong
  Khwai — founders deported from Mueang Pu and Mueang Sat in Kengtung, the
  น้ำต้น water jar, 200 years, and **zero records in this directory**), วัดต้นเกว๋น
  (built c. 1856–1869, ASA conservation award 2532, and its four-porch pavilion
  has a job: the Phra That Si Chom Thong relic rested and was bathed there on
  the 60 km road into the city), and then บ้านถวาย.

## Open, and deliberately not done

- **The pottery village has no record at all.** That is a crawl question, not
  a page question, and it belongs to WO-10's `making` group rather than being
  smuggled in here. The page prints the zero and the sentence removes itself
  the day a record arrives.
- **No shop list, no prices walked.** Guides publish tidy price bands and
  village-wide opening hours; no source with standing carries either, so both
  sit in `unverified` and neither is printed as fact.
- **How many สล่า are still at the bench today** — no count was found anywhere,
  and the page says so rather than reaching for the shop count as a proxy.
- **The craft-words reader sheet** (WO-10 item G) is still not built. The
  vocabulary now exists in `carve.json` under `hands`, which is what a sheet
  would be built from.
- **A field visit would settle most of the unverified list in one afternoon** —
  the songthaew fare, whether the two centres keep different hours, and whether
  the canal shops still outnumber the frontage ones twenty years after the
  case study said they did.
