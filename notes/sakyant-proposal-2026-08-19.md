# สักยันต์-รอยสัก — the tattoo shelf: making Mot Dang deep where it was thin

*WO-14. Written 2026-08-19 from a gemba of `data/canonical`, `data/curated`,
`data/categories.json`, the built `docs/cm/tattoo/` and the live
motdang.net/cm/tattoo/ page, plus the two wells that already sit on this
machine: wichaa's yant work and the photo-mine sak yant index.*

Nan's question: *"Can Mot Dang's already pretty great information about
tattoos and sak yant be even more enriched?"* The answer is yes, and the gap is
wider than "a bit more" — the rich material lives on wichaa and in the photo
index, and the Mot Dang shelf surfaces none of it.

## The measurement, before any proposal

- **34 records** — 30 Chiang Mai, 4 Chiang Rai — every one an OpenStreetMap
  `shop=tattoo` point, every one filed as `sub: studio` ("Modern studios").
- **Three of the four sub-shelves are empty on the live site**: สักยันต์ ·
  Sak Yant, เจาะ · Piercing, ลบรอยสัก · Removal all render as the
  ant-on-the-way. The shelf reads as *"Chiang Mai has no sak yant."*
- **Why สักยันต์ was empty**: its rule was `match: {lens: "sak-yant"}` and no
  record in either province has ever carried that lens. Its three siblings
  match on `sub`. The odd rule out was the empty shelf.
- **Field coverage**: phone 6/30 · website 6/30 · hours 10/30 · blurbs 0 ·
  prices 0 · photos 0. Chiang Rai's four carry nothing but a pin.
- **No prose on the shelf and no link** to wichaa.net/yant or to the sak-yant
  article. A reader who lands here never learns the other half exists.
- **Every Chiang Mai tattoo record is also on the sights shelf.**
  `LENS_TO_CAT["tattoo"] = ["sights"]` in `importers/import_all.py` dates from
  before the tattoo category existed (the crawl's own comment says so: *"41
  tattoo records were sitting in 'sights' with no rule"*). The crawl fixed the
  shelf and left the lens mapping, so the 30 studios ride both shelves. All 31
  mueang-map tattoo points are inside the Overpass tattoo crawl, so the lens
  mapping adds nothing any more.
- **Misfiles**: หรรษา มินิกอล์ฟ / Hansa Minigolf (`cm-osm-node-11411206869`) is
  on the tattoo shelf because OpenStreetMap tags it `shop=tattoo` — the name
  says minigolf in Thai, English and German. "Tattoo", "Tattoo Studio",
  "Forever", "Solitary", "Ganesha" are real mapped points with near-nameless
  names. Chiang Rai's เล็กคิ้วสวย & สปา says eyebrows in Thai and "Lek Tattoo
  Parlor and Spa" in English — both, so both shelves.
- **The trade with no shelf at all**: สักคิ้ว-สักปาก — brow, lip and hairline
  tattoo, semi-permanent makeup. A larger trade in both towns than สำนัก sak
  yant, and zero records name it, because OSM records a beauty shop as
  `shop=beauty` and stops. Photo-mine #4 already holds one Chiang Mai shop
  with a price (1,299), a phone and a LINE.
- **The 17 Aug note said this shelf was filled.** It was not: the
  duplicate-node merge landed (`merges.json`) and `enrich.json` holds the
  Facebook/Instagram links; the lens and the prices never reached a curated
  file. Canonical is regenerated on every walk, so anything written there
  evaporates. This order writes to `data/curated/` only.

## The two wells, both already on disk

**wichaa.** `/yant` is LIVE — 36 named designs from the Lanna manuscripts,
entered by virtue, each citing slug and page. `/na` holds the 142 na. The
sak-yant linguistics article is live on its own Worker. `yant_practitioners.json`
holds the 17-master lineage map of the one operation that is also on this
shelf. None of it is linked from Mot Dang.

**photo-mine.** `photo-mine/out/sakyant/read_index.jsonl`, 209 entries, each a
screenshot Nan chose, read and indexed. For THIS shelf the seam is:

- Sak Yant Chiang Mai's own design-and-price book (heyzine, canonical URL
  captured at #138): ~50 named designs with in-house and at-temple prices. The
  rate card is regular — **1 hour 3,500–4,500 in-house / 6,000–7,000 at the
  temple; 2 hours 6,500 / 8,500 almost without exception; 3 hours 8,500–9,500
  / 10,500–11,500; a single na 2,000 / 5,000; a 6×8 cm turtle at 2,500 is the
  floor.** The price tracks time and size, never the design's power — a turtle
  for longevity and a Narai for kingship cost the same at the same size. The
  temple premium is transport and interpreting; the monk's offering is
  separate. (#23–#196)
- The maintenance doctrine in the operation's own words (#138): the ajarn
  charges the yant through the katha; the bearer keeps it by keeping the five
  precepts. *Any page about sak yant that omits this presents the practice as
  a purchase.*
- Two more Chiang Mai sak yant venues, not yet records: สักลายมือเศรษฐี
  อาจารย์ไก่ บารมีนาคราช (#171 — on the map as a *religious destination*, which
  is the right shelving: a สำนัก is not a studio) and Spiritual Sak Yant,
  Ajarn Vee (#212–214). Both need their own page read before they become
  records — never a scrape of Google or Facebook listings.
- One Chiang Mai cosmetic-tattoo shop with price + phone + LINE (#4) and one
  Chiang Rai laser-removal clinic at 599 with two phones (#5), both awaiting a
  pin and a fetched source.

## The rule this shelf runs on

1. **Three things are sold under one word, and the shelf keeps them apart.**
   A สำนัก or an ajarn charges a yant with a katha (สักยันต์, the shelf's
   promise: "สักยันต์ตามครูบาอาจารย์"). A studio inks designs, yant-shaped or
   not (ร้านสักสมัยใหม่). A beauty shop tattoos brows and lips (สักคิ้ว-สักปาก).
   A studio named after a yant design is a studio until its own page says an
   ajarn works there. Sak Yant Chiang Mai is a booking service with resident
   ajarns and temple visits, by its own description — the record says so.
2. **Two price sources, never welded.** The FAQ page frames by the hour; the
   design book frames by design, size and duration. Each is stated with its
   own date and `_pricesVerified: false`. A price is never welded to a duration
   the source did not pair it with (the shelf-card lesson). The temple figure
   is transport and interpreting; the offering to the monk is named as
   separate, never folded in.
3. **Curated outranks crawled, and says so.** Every correction to an OSM tag
   carries the evidence line and is appended to the fix ledger under มดเอง.
   Nothing is removed from a shelf without a receipt; upstream OSM is told
   where it can be.
4. **No screenshot is republished.** The photo index is mined as data — the
   no-republish rule in `photo-mine/bots/3a_sakyant_assayer.md` stands. Nan's
   own session photographs are cleared; when shown, Ajarn Dang and Ajarn
   Sak/Sek are credited by name with a link to sakyantchiangmai.com.
5. **No authenticity sort.** No ranking of studios into real and touristic; no
   "best sak yant"; a shelf lists and says what each door states.
6. **สักขาลาย is its own tradition**, not a section here. The Lanna
   waist-to-knee tattoo has its own notes on wichaa
   (`manuscript-wiki/content/_sak-kha-lai-notes.md`) and waits for its own
   order.

## What this order builds, pillar by pillar

### Locations — the shelf (zero network, built 2026-08-19)
- `categories.json`: สักยันต์ matches `sub: sak-yant` like its siblings; a
  fifth child **สักคิ้ว-สักปาก · Cosmetic tattoo** (`sub: cosmetic-tattoo`).
- `LENS_TO_CAT["tattoo"] = ["tattoo"]` — the 30 studios leave the sights shelf.
- `importers/audit_tattoo.py` — names + the crawl's own sub, zero network,
  prints the review lists, `--emit` → `shelves.json` / `retags.json` entries.
- `data/curated/retags.json` — a new, deliberately small curated layer: an
  OSM tag a person has read against the door and found wrong, with the
  evidence line. First entry: the minigolf.
- Sak Yant Chiang Mai as a curated record in `additions-chiang-mai.json`
  (same id, tier curated): `sub: sak-yant`, the rate card, the FAQ framing,
  the second phone, the resident-ajarn count, the doctrine, blurbs ไทย · EN,
  dated sources. No photo — the two Commons sak yant pictures are not of this
  shop.
- `known_facts()` gained a generic `priceCardTh/En/Via` row — "ราคาที่ประกาศ ·
  Published prices" with the unwalked mark — so any venue's own board can
  render, not only the muay thai ticket line.
- `data/curated/moved.json` + `write_moved_stubs()`: giving the business its
  own name back (OSM's name:en carried "Tatoo") moved the page slug; the old
  path forwards with a meta refresh and a canonical link, noindex, written
  only where the new page exists. The first entry in a file meant to stay short.
- Search tables re-mined and synced (`search-core/mine.py motdang`, `sync.py`):
  สักคิ้ว-สักปาก, brow, lip, cosmetic tattoo narrow to the shelf.
- `fixes.json` entries under มดเอง for the shelf, the minigolf and the sights
  double-listing.
- Verified in a scratch build (`build.DOCS` redirected, no lock taken): the
  shelf reads 29 with สักยันต์ (1) and, in Chiang Rai, สักคิ้ว-สักปาก (1); the
  band renders; the SYCM page shows the board and the second phone; the
  minigolf stands on sights; the draft question renders nowhere; the facets,
  asked, publish-gate and route tests pass.

### The question — `asked.json` (drafted 2026-08-19)
`sak-yant`: *สักยันต์ที่เชียงใหม่ ทำที่ไหน ราคาเท่าไหร่* — opened with
`asked_new.py`, `draft: true` until the two สำนัก have been read from their own
pages. The lead carries the three-things distinction, the rate-card logic and
the five-precepts doctrine; `ask_at_the_door` is the sentence that separates
a studio from a สำนัก.

### Culture — the band now, the primer next
- `yant_band()` in build.py, on the WO-12 `muaythai_band()` pattern: what
  wichaa.net/yant and the article ARE to this shelf, stated from this side
  with the fact that makes the join true — the นกคู่ sold on Arak Road is the
  ยันต์สาริกาคู่ of manuscript 6985, a century apart; the deer that looks back
  so she looks back; a na at 2,000 baht is the tradition's smallest unit and
  /na holds 142 of them.
- `/sakyant.html` — a primer on the `/muaythai.html` pattern: the three
  things, in-house vs temple and what each number is, ขันครู / ขันตั้ง, what to
  bring, the five precepts, the words with script/RTGS/tone, and the shelf's
  porch. Town-facing wording of what wichaa says scholar-facing. **Not built
  in this pass** — the asked page carries the core until it is.

## What this note is deliberately not proposing
- No crawl (Nan's go; Overpass already returns every `shop=tattoo` and
  `shop=piercing` there is — the rest fills by name and by walk).
- No scrape of Google Maps or Facebook listings for สำนัก — each from its own
  page, dated.
- No republishing of the design book's plates; prices and names only, cited
  to the canonical URL.
- No shelving of Gao Yord / Jin Bamboo / Line Point Bamboo under สักยันต์ on
  their names alone — leads for the web check, not facts.
- No facet yet — three places and the door sentence first.
- No สักขาลาย section.

## Open, in order of value
1. The two สำนัก from their own pages (อาจารย์ไก่ บารมีนาคราช; Spiritual Sak
   Yant / Ajarn Vee) → records → release the asked entry → card → reply.
2. The cosmetic shop (#4) and the removal clinic (#5) — pin + source → the
   two empty shelves fill; `removal` comes off KNOWN_EMPTY.
3. `/sakyant.html`, the primer, and the yant-practitioners lineage as a card
   on the SYCM page (Nan rates those bios; consent is settled).
4. The three bamboo/yant-named studios, each from its own page: does an ajarn
   work there, is a katha given — shelve only what they state.
5. The facet — three places first; the door sentence is already written
   (*ที่นี่มีอาจารย์ลงคาถาให้ไหมคะ/ครับ หรือสักลายอย่างเดียว*).
6. Tell OpenStreetMap about the minigolf and the "Tatoo" name:en.
7. `tests/test_search.py` fails before testing (its `const norm=` marker left
   build.py with the search-core move) and is in neither walk — retire or
   repoint it.
