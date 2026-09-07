# ผ้าปูที่นอนแบบไม่รัดมุม — the flat sheet, and the trade that would have it

Nan, 2026-08-31: *"Getting farang style flat sheets in thailand is very
challenging. Thais just use fitted and duvet cover. Can motdang help the
handful of farangs who refuse to adapt to this reality?"*

This is the ขัดขี้ไคล shape again, and the answer is probably the same one:
the catalogue is being searched in the wrong language, and the trade is being
looked for in the wrong channel. Both halves are stated here as **claims to be
tested**, not findings. Nothing below has been walked, phoned, or crawled.

## The census — this part is measured

20,778 records across both provinces (cm 14,566 · cr 6,212). Every one of
these words returns **zero**, in name and in every other field, in either
script:

    ผ้าปูที่นอน · ผ้าปู · เครื่องนอน · ที่นอน · ผ้านวม · ปลอกผ้านวม
    ปลอกหมอน · ผ้าคลุมเตียง · ผ้าม่าน · รัดมุม · ผ้าเมตร · ร้านผ้า
    ตัดเย็บ · ช่างเสื้อ · อุปกรณ์โรงแรม · ผ้าโรงแรม
    bedding · bed linen · flat sheet · top sheet · fitted sheet · duvet
    linen · mattress · fabric · upholster · seamstress · alteration

Two words survive: **textile** (2) and **ซักรีด** (2, laundry-press). The
thesaurus holds `["blanket","ผ้าห่ม"]` and an alterations group
(`ตัดเย็บ · ช่างเสื้อ · ซ่อมเสื้อผ้า · ร้านตัดเสื้อ`) and nothing at all for
sheets, bedding, or cloth sold by the metre.

**Home textiles are not a thin shelf on this site. They are an absent one.**

### The tailor row, which is the tell

`shopping/tailor` holds 10 records in Chiang Mai. Nine are bespoke-suit shops
with English signage — Ambassador Suits, Unique Suits, Mr. Armani, Universal
Tailor, New Moda, You & Me, Siam Collection, plus a shoe repair stall and a
bootmaker. Exactly one is named in Thai: **รับซ่อมแซม เสื้อผ้า**
(`cm-osm-node-13298710901`), "clothing repairs accepted", which is a sign and
not a business name.

The neighbourhood alterations trade — the woman with a machine in a shophouse,
who would hem a rectangle of cloth into a sheet for the price of a coffee — is
invisible because OSM tagged the category in English and the crawl inherited
the tag. Same mechanism as the barbers going 6 → 62 under WO-22.

### Two defects this turned up on the way

- **ตลาดวโรรส** (`cm-osm-way-89039067`) is filed `market` / `fresh`. Warorot's
  ground floor is food; its upper floors are the cloth trade. A produce
  sub-category on that building hides the one place in the city most likely to
  answer this question. Not a missing record — a mis-shelved one.
- **กาดหลวง**, the Northern name for that same market, is carried by a
  *different* record — `ตลาดผลไม้ (กาดหลวง)` (`cm-osm-node-5606185823`). Two
  records, one trade name. This is not merged here: `merges.json` takes
  human-confirmed pairs only, and one of these may be the fruit hall as a
  distinct thing. It is an open lead, and a phone call or a walk settles it.

## The hypothesis — three claims, none of them checked

**1. The flat sheet here is a trade item, not a retail one.** Thai hotels bed
with a top sheet. If that holds, flat sheets are manufactured and sold in this
country at volume — into the hospitality supply chain, not onto the HomePro
shelf, where households buy fitted-plus-duvet-cover because that is how
households here sleep. The reader is not facing a shortage. They are standing
in the wrong shop.

**2. The retail word is รัดมุม.** *rát mum*, "binds the corner" — the fitted
sheet. If the shelf tag sorts by that word, then the flat sheet is
**ไม่รัดมุม** or **แบบเรียบ** (*mâi rát mum* / *bàep rîap*, not-corner-bound /
plain type), and the whole problem is a vocabulary problem end to end. Same as
ขัดขี้ไคล: search in English, get nothing; search in the trade's own word, get
a trade.

**3. Cloth by the metre plus a hem is the cheapest route and gives any size.**
ผ้าเมตร / ขายผ้าเป็นเมตร. This one depends on defect 1 and the tailor row
above being fixed first — the shops that would sew it are the ones the
catalogue cannot currently see.

**Every Thai term in this section is my reading, not a source.** None has been
confirmed against a shop sign, a price board, or a Thai-language listing. The
crawl exists to prove or kill them, and the words go in the register only where
something dated backs them.

## The build — zero-network, and it can be done now

1. **New sub-categories** under `shopping`: `bedding` (เครื่องนอน) and
   `fabric` (ผ้า-ผ้าเมตร); `alterations` (ตัดเย็บ-ซ่อมแซมเสื้อผ้า) split out
   from `tailor`, which keeps the suit shops. Wireframe shelves until records
   exist — the build never fabricates content for an empty child.
2. **The thesaurus group** the site has never had, added to
   `data/search_thesaurus.json` so that typing "flat sheet" reaches anything at
   all once records land. This is the same file WO-47 proposes to publish, and
   this entry is its first proof.
3. **Re-shelve ตลาดวโรรส** from `fresh` to a market record that names the cloth
   floor. One curated override; the OSM record is not edited.
4. **`data/curated/bedding.json`** — the register scaffold, empty, with its
   field contract written: what a shop states about size, whether it sells flat
   at all, whether it sells to walk-ins or only to trade.
5. **The asked entry** `flat-sheet`, drafted with its `ask_at_the_door`
   sentence and left in draft. It cannot ship: `find: {prov, sub}` resolves
   against tagged records, and there are none yet. Register → shelf → the
   question. Same order as WO-39.

## The crawl — waits on Nan's go, as always

Targets, in the order they are worth the fetch: hotel-linen and hospitality
supply (the strongest claim, and the one that decides whether this shelf is
five records or fifty) · the Warorot cloth floor · ผ้าเมตร shops · the
alterations trade in Thai · the four DIY anchors already on file, for whether
they carry ไม่รัดมุม at retail (HomePro San Sai, HomePro Ruamchok, โฮมโปร,
บุญถาวร, Global House — all `shopping/diy`, none tagged for bedding).

## What must not be claimed

- **No shop gets a "sells flat sheets" flag from an inference.** A department
  store carrying bedding is not evidence it carries flat sheets. That fact
  comes off a shop's own statement, a price board, a dated listing, or a
  reader who just bought one — and it carries which of those it was.
- **Zero is not absence.** If the crawl finds nothing, the page says the
  catalogue holds nothing confirmed, not that Thailand has no flat sheets.
- **No "Thais don't use these" framing.** The page explains a supply channel,
  not a national habit, and it is read in both languages.

## The plain answer that belongs on the page anyway

A duvet cover with no quilt inside **is** a flat sheet, sewn shut on three
sides. In this climate that is what a great many people who miss a top sheet
actually wanted. It costs nothing, it is already in every shop, and a page
that withholds it in order to sell a harder answer is not being useful.

## The reusable lesson

Third time now: ขัดขี้ไคล, the barbers, and this. A trade is not missing from
Chiang Mai because a directory in English cannot find it. The fix was never a
better crawl — it was asking what the shops call it.
