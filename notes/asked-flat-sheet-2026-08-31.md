# flat-sheet — ผ้าปูที่นอนแบบไม่รัดมุม (ผ้าปูทับตัวแบบที่ฝรั่งใช้) หาซื้อที่ไหนได้บ้าง

*Where can I buy a flat sheet — the loose top sheet farang sleep under, not the fitted kind?*

- asked_on: 2026-08-31
- via: other (Nan, from the groups)
- status: DRAFT (`draft: true` in data/asked.json — delete it when the four outputs exist)
- order: WO-46 · `notes/bedding-proposal-2026-08-31.md`

**This entry cannot leave draft yet, and the reason is structural rather than
lazy:** `find: {prov, sub}` resolves against tagged records, `sub: bedding`
holds zero, and no crawl has run. Register → shelf → question, WO-39's order.

## The question, in the trade's own word

Which Thai word does Chiang Mai actually sell this under? Search that, not the
reader's English. (ขัดขี้ไคล was the lesson: "Korean scrub" returned one paid
ad; the Thai word returned a trade with price boards.)

- word tried, **zero-network, against the catalogue only**: ผ้าปูที่นอน ·
  ผ้าปู · เครื่องนอน · ที่นอน · ผ้านวม · ปลอกผ้านวม · ปลอกหมอน · ผ้าคลุมเตียง ·
  ผ้าม่าน · รัดมุม · ผ้าเมตร · ร้านผ้า · ตัดเย็บ · ช่างเสื้อ · อุปกรณ์โรงแรม ·
  ผ้าโรงแรม · bedding · bed linen · flat sheet · top sheet · fitted sheet ·
  duvet · linen · mattress · fabric · textile · upholster · seamstress ·
  alteration · hotel supply
- **result: 0 records out of 20,778 across both provinces, in name and in every
  other field, in either script.** Only `textile` (2) and `ซักรีด` (2) survive.
  This is not a thin shelf. It is an absent one.
- names file: not written — there is nothing yet to reconcile. The names come
  out of the crawl, and the crawl has not run.

## Sources (url · fetched YYYY-MM-DD · what it supports)

- **None.** Nothing here was fetched. Every number above was measured against
  `data/canonical/cm.json` + `cr.json` on 2026-08-31, and every Thai word below
  is a reading rather than a source. Do not let any of it reach a page until a
  crawl or a walk stands behind it.

## Leads — name · what is missing · why it is not in the catalogue yet · the one act that clears it

- [ ] **The hospitality supply channel** — the strongest claim and the one that
      decides whether this shelf is five records or fifty. If Thai hotels bed
      with a top sheet, flat sheets are made and sold here at volume, into
      trade supply rather than onto a retail shelf, and the reader is simply in
      the wrong shop. Nothing in the catalogue names this trade in either
      script. **Clears with:** one crawl of ผ้าโรงแรม / อุปกรณ์โรงแรม suppliers,
      or one phone call to a hotel's housekeeping asking who supplies them.
- [ ] **ตลาดวโรรส `cm-osm-way-89039067`** — filed `market`/`fresh`. Warorot's
      ground floor is food; its upper floors are widely understood to be the
      cloth trade, and if that holds, a produce sub-category on that building
      hides the one address in the city most likely to answer this question.
      **NOT retagged**: `retags.json` requires evidence a person read, and the
      record carries a name, a pin and opening hours and nothing about cloth.
      **Clears with:** one walk, or one dated listing for a shop inside it.
- [ ] **กาดหลวง on a second record** — `ตลาดผลไม้ (กาดหลวง)`
      `cm-osm-node-5606185823`, 18.7909/99.0007, about 80 m from ตลาดวโรรส at
      18.7902/99.0005. กาดหลวง is the Northern name for Warorot itself, so
      these may be one market held twice, or the fruit hall as a genuinely
      separate thing. **Not merged** — `merges.json` takes human-confirmed
      pairs only. **Clears with:** standing in front of both.
- [ ] **The retail question, on shelves already in the catalogue** — HomePro
      San Sai `cm-osm-node-3540899196`, HomePro Ruamchok
      `cm-osm-way-1356111268`, โฮมโปร `cm-osm-way-77089898`, บุญถาวร
      `cm-osm-way-443374265`, Global House `cm-osm-way-89534266`, all
      `shopping/diy`, none tagged for bedding. **Clears with:** one walk down
      one bedding aisle, reading the shelf tags.
- [ ] **The word รัดมุม** — *rát mum*, "binds the corner", the fitted sheet; the
      flat one would then be ไม่รัดมุม or แบบเรียบ. If the retail shelf tag
      sorts by that word the whole problem is vocabulary, exactly as with
      ขัดขี้ไคล. **Unverified.** **Clears with:** a photograph of one shelf tag.
- [ ] **ผ้าเมตร plus a hem** — cloth by the metre, hemmed by an alterations
      shop, gives any size for the price of the cloth. Depends on the
      alterations trade becoming visible first — see the retag below.

## Decision

- found N / gap: **neither yet.** Not `gap: true`: a gap entry publishes
  "nobody does this", and the finding here is that the catalogue cannot see a
  trade, which is a different sentence and possibly a false one. It stays a
  plain draft until a crawl earns one or the other.
- shelf (child key, in the trade's word): **three opened**, named for the trade
  and not for the asker — `shopping/bedding` (เครื่องนอน-ผ้าปูที่นอน) and
  `shopping/fabric` (ผ้าเมตร-ร้านผ้า), both wireframe at 0 records, plus
  `shopping/alterations` (ซ่อมแซม-แก้เสื้อผ้า) split out of `shopping/tailor`,
  which was relabelled ร้านตัดสูท-ตัดชุด / Tailors and now holds 9.
- facet (key + ask_th/ask_en) or none: **none.** The facet this question wants
  is "sells flat, not only fitted", and a facet is ticked by somebody standing
  at a door. Three places and a survey sentence first — same reasoning that
  left `scrubglove` empty on the ขัดขี้ไคล shelf.
- **what was NOT recorded, and why:**
  - Warorot's cloth floor — no receipt, see the lead above.
  - Any hotel-linen supplier — the whole channel is a hypothesis.
  - Any "sells flat sheets" flag on the five DIY anchors. Carrying bedding is
    not evidence of carrying flat sheets, and a department store is not a
    witness to its own aisles until somebody reads them.
  - A thesaurus group for ผ้าโรงแรม / hotel linen. The other eight groups went
    in; that one asserts a trade term nobody has confirmed.

## What WAS done, on evidence

- **`cm-osm-node-13298710901` retagged** `sub: tailor → alterations`. Its own
  name says the trade in both languages — name=รับซ่อมแซม เสื้อผ้า, name:en=
  repair clothes — while its only shop tag is `craft=tailor`, which OSM uses
  for the whole needle trade. Read in `cache/overpass/cm/crafts.json`, crawled
  2026-07-27. `cat` untouched; the receipt travels in the record's own sources,
  and `data/fixes.json` carries the reader-facing line.
- **Eight groups added to `search-core/data/hand.thesaurus.json`**, then
  `mine.py motdang` + `sync.py`. "flat sheet" now reaches ผ้าปูที่นอน; there is
  nothing behind it yet, which is the correct state — the word works the day
  the first record lands. ผ้าห่ม was deliberately left out of the sheet group:
  a blanket is not a sheet, and the mined table already pairs it with
  "blanket". flat/top/fitted DO sit beside ผ้าปูที่นอน as hyponyms rather than
  synonyms, which stretches that file's contract on purpose — Thai carries one
  generic word where English carries three specific ones, and that asymmetry is
  the whole reason the reader finds nothing.

## Prices

None recorded. All `_pricesVerified: false` until somebody reads a board on the
street.

## The plain answer that goes on the page regardless

A duvet cover with no quilt inside **is** a flat sheet, sewn shut on three
sides. In this climate that is what a great many people who miss a top sheet
actually wanted; it costs nothing and it is already in every shop. A page that
withholds it to sell a harder answer is not being useful.

And the framing to refuse: this explains a supply channel, not a national
habit. No "Thais don't use these" sentence, in either language.

## The four outputs

- [ ] records with dated sources in data/curated/additions-*.json → `importers/import_all.py`
- [ ] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [ ] `python3 make_shelf_cards.py --only asked-flat-sheet` → `build.py` → `tests/test_asked.py`
- [ ] `python3 make_post.py flat-sheet` pasted back
