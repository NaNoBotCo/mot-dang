# WO-33 — ของฝากที่เดินทางได้ · souvenirs and the wild things

> Nan's ask, 2026-08-26: "an enrichment on the conservation and protection
> status of animals and plants in thailand — this is a problem for travelers
> at airports. content can go on motdang.net."
> Built same day: `data/curated/wildlife.json` + `souvenir_layer.py` →
> `/souvenir.html` + `souvenir.css`, `importers/audit_wildlife.py`,
> `souvenir` search panel (16th), WO-33 row on the status board.

## The design

Same skeleton as WO-31 (ADHD), because it is the same failure mode on a new
subject: three questions folded into one rumour, and the folding is what
hurts people. Kept apart on the page:

1. **WHICH CLASS a thing sits in** — Thai law's tiers (สงวน · คุ้มครอง ·
   ควบคุม) and the CITES appendix. Fixed, published, checkable. The page
   links the registers and the CITES checklist rather than copying lists,
   because the lists demonstrably move (below).
2. **WHAT PAPER exists where one does** — nursery orchids and farmed
   crocodile leather travel every day on documents the seller arranges.
   The question belongs at the till, not the check-in desk.
3. **WHAT HAS NO PAPER for a traveller at all** — ivory above everything:
   lawfully sold inside Thailand under its own registration act, and still
   nothing puts a piece of it on a plane. *Legal to buy here is not legal
   to fly with* is the page's one rule.

The frame stays auspicious: the h1 is the things that DO
travel well (silk, celadon, Bo Sang umbrellas — the `ok` row exists so the
page opens a door instead of wagging a finger), no penalty tables, and the
questions are phrased for the shop counter.

## What was measured (live in the layer, printed by the audit)

- 20,702 records scanned. **0** say in their own name they are a farm or
  nursery for these goods; **12** sit on the souvenir/OTOP/handicraft rows;
  **39** bare-word hits for เสือ/ผีเสื้อ/กล้วยไม้ are nearly all namesakes
  (ตำบลสันผีเสื้อ, Tiger Mart, orchid hotels) — the WO-24 namesake lesson,
  measured again. The venues where a traveller actually meets these goods
  (the Mae Rim orchid farms, the animal shows) mostly are not in the
  catalogue under those words at all — a crawl-gap worth a future door.

## Sources read 2026-08-26 (all cited in wildlife.json with dates)

- **DNP legal affairs** — portal.dnp.go.th/Content/LegalAffairs?contentId=22540
  — the 2019 act (TH+EN) and the subordinate set: preserved-species royal
  decree B.E. 2567; protected-species ministerial regulation B.E. 2567
  **with a 2nd edition B.E. 2569 (this year — the reason no list is copied
  onto the page)**; controlled-wildlife announcements B.E. 2568.
- **The 2567 decree** (dl.parliament.go.th/handle/20.500.13072/622056,
  gazette เล่ม 141 ตอน 58 ก, 24 ก.ย. 2567, in force +60 days): adds the
  blue whale and the helmeted hornbill → **preserved list is 21 now, not
  the 19 the 2019 act is remembered for**. Web copy everywhere still says
  19; the register says 21 with the decree cited.
- **Thai Customs, guidelines for airport passengers** (customs.go.th,
  fetched and quoted): "Reserved animals or CITES-listed wildlife" sits on
  the PROHIBITED list in so many words; permits — plants → Department of
  Agriculture, live animals → Department of Livestock Development.
- **cites.dnp.go.th** — Thailand's CITES e-permit portal (DNP), TH/EN,
  tel 02-561-4838 — linked as the permit door.
- **checklist.cites.org** — the convention's own species list, linked as
  the check-it-yourself tool, with per-item deep links (Elephas, Panthera,
  Eretmochelys, Scleractinia, Nycticebus, Paphiopedilum, Orchidaceae,
  Crocodylus siamensis, Dalbergia, Troides, Naja).
- **Elephant Ivory Tusks Act B.E. 2558** — FAO-mirrored unofficial
  translation (faolex.fao.org/docs/pdf/tha167051.pdf): the domestic
  registration scheme that makes the legal-to-buy-here trap real.

## Refused a read, printed as refusals

- cites.org/eng/parties/country-profiles/th/national-authorities — 403.
- cites.org/eng/node/2597 (Thailand's plant-export-permit procedures) —
  403. The customs page's own DoA line stands in.

## Doors not walked (for Nan's numbered go, if wanted)

1. **The venue gap** — orchid farms, butterfly/snake/crocodile shows are
   largely absent from the catalogue (census: 0 farm-named). A narrow
   Overpass group or curated additions would give the page real places to
   point at, and the elephant register (WO-19) the sibling it deserves.
2. **A reader sheet** (`souvenir-words.pdf`) in the beauty/care mould —
   the till questions, printable.
3. **wichaa cross-link** — the amulet-materials angle (เขี้ยว, งา in
   เครื่องราง) is wichaa's territory; a sourced paragraph there could point
   here for the airport half.

## For the record

- Scratch build 22,100 pp (another session held docs/ — WO-32 longcare +
  a medicine-airport layer landed the same day). alt-text, asked, search
  all PASS against the scratch DOCS.
- Publish gate FAILS at HEAD on **WO-32's** longcare.html → a live href to
  theriverrehab.com, which link-health holds as broken — the exact WO-31
  dead-ref scenario; that layer wants its links through an `out_a()`.
  Flagged, not fixed here: that session was mid-flight while this order
  built, and touching a live order's layer from the side is how two builds
  end up wearing each other's mistakes.
