# exterminator — ปลวกขึ้นบ้าน หนูขึ้นฝ้า จะจ้างใครกำจัด ราคาประมาณเท่าไหร่

*Termites in the house, rats in the ceiling — who do you hire, and what does it cost?*

- asked_on: 2026-08-31
- via: Nan, 2026-08-31 — "they don't speak english much, but everyone—including
  farangs—need them if they stay in cm long-term. Motdang should make it easy to
  reach/locate/and hire these services."
- status: PUBLISHED

## The question, in the trade's own word

- word tried: **กำจัดปลวก** (kill termites), not กำจัดแมลง and emphatically not
  "exterminator". Every firm in two provinces names itself after the termite
  first and hangs rats, cockroaches, mosquitoes and bed bugs off that. The
  English word returns paid ads; the Thai word returns the trade with its
  price pages attached. Same lesson as ขัดขี้ไคล.
- Second useful word: **แมลงเม่า** — the winged alates that swarm a light after
  rain. That is what a householder actually sees, and it is what they should
  search when the ceiling has not yet given anything away.

## What was measured before anything was searched

The `crafts` crawl group already asks Overpass for `nwr["craft"]["name"]` across
both provinces. It returns **102 elements in Chiang Mai and 42 in Chiang Rai —
and zero `craft=pest_control` or `shop=pest_control`.** The whole
`home-services` category held **10 records**, every one of them a landscaper
arriving from `craft=gardener`.

So this is not KNOWN_EMPTY-because-nobody-asked. The ant was sent, it came back,
and the trade genuinely is not on the open map: it lives on Facebook, on LINE,
and on its own .co.th. Curated records, one firm at a time, is the only route —
the notary shape exactly.

## Sources (url · fetched 2026-08-31 · what it supports)

- https://www.unipest.co.th/ — Unipest, CM head office + CR branch, FDA reg
  83/2539, TPMA training, ISO 9001:2015 (all the company's own claims)
- https://www.xn----twfazco1ewc0ci3ay1d3dn1d9k7bwfwd.com/catalog/item/… — GB
  Pest Control, San Kamphaeng, bait + pipe + injection, no published price
- https://www.minibug-insect.com/17248937/… — Mini Bug CM branch, hours, tax id,
  the service map
- https://www.minibug-insect.com/17973932/… — Mini Bug CR branch, 48-hour
  response, its own service map
- https://ikari-pco.com/ — Ikari CM, the only firm naming ตัวเรือด (bed bugs);
  Thai-only site, no English claimed
- https://greennanothai.com/ — Green Nano Thai, Hang Dong, English-first site,
  herbal-nano method, 12-month guarantee ("proven safe by Thai health
  authorities" — recorded as their claim, not repeated in our voice)
- https://www.happyhouse.co.th/promotion/termite-control — Happy House, the one
  published price: 3,900 first visit, from 6,900; 1-year workmanship guarantee
- https://www.mtpservicegroup.com/กำจัดปลวกเชียงใหม่/ + https://www.mtptermite.com/
  — Mitrapap Service Group CM branch. TWO DIFFERENT ADDRESSES on the company's
  own two pages, same day, same phone (see Discrepancies)
- https://www.firesaver-cg.com/productList.php?cat=64 — Firesaver Chiang Rai;
  fire-safety shop with a termite line
- https://www.yellowpages.co.th/…Rentokil-Initial-Thailand-Co-Ltd… — Rentokil CM
  address and phone, THIRD-PARTY only (see Attempted)
- https://hazard.fda.moph.go.th/our-service/category/pco-01 — the licence: type-3
  hazardous-substances permission, the ผู้ควบคุมการใช้วัตถุอันตรายเพื่อใช้รับจ้าง,
  the 3-year retrain, and the two public lookups at excercitium.fda.moph.go.th
- https://www.homechemical.co.th/service-charge-calculation/ — how the trade
  prices: per LINEAR METRE of perimeter (LM); bait 400–700/LM, chemical
  150–280/LM

## Attempted, and refused — printed, never guessed at

- **https://www.rentokil.com/th/local-branches/pest-control-chiangmai — HTTP 403**,
  both the Thai and English paths. Their record is therefore `confidence:
  third-party`, carries `readRefused` in attrs, and its blurb says so in both
  languages rather than passing a directory listing off as the company's word.
- **http://pca.fda.moph.go.th/…content_id=268 — DNS does not resolve.** The FDA
  consumer page on pest-control registration is gone from where it was indexed;
  the licence facts come from hazard.fda.moph.go.th instead.

## Discrepancies recorded rather than resolved

- **cm-curated-mtp-service-group** publishes 427/4 หมู่ 4 on its branch page and
  145/2 หมู่ 6 ถนนวงแหวน 121 on the group page — both ต.หนองจ๊อม อ.สันทราย,
  identical phone. Neither is pinned; the record says "confirm the address when
  you book", in both languages, and the pair is in `pest.json -> discrepancies`.

## Decision

- found **11** (cm 8, cr 3) / gap: no
- shelf: **`home-services/pest-control`** — `กำจัดปลวก-แมลง-หนู` / Pest Control,
  `match: {sub: pest-control}`. The trade has its own word, so it earns a child.
  The home-services teaser was retuned to name it (three trades → four).
- facet set: **`pest`**, `appliesTo: ["pest-control"]`, 14 facets, **10 new keys**
  in worker FACET_KEYS — `fdalicence termite rodent bedbug mosquito baitsystem
  pipesystem herbal warranty petsafe`; `english priceboard booking card` already
  existed. Every `ask_th` is a sentence for the PHONE or for LINE, because this
  trade has no door to stand at. `fdalicence` is positive-only on the `hsscert`
  rule. `herbal` records that a firm *says* it works without chemicals, never
  that it does. `petsafe` wants a NUMBER OF HOURS, not a reassurance.
- register: **data/curated/pest.json** — the licence regime, the pricing method,
  the vocabulary, the nine phone sentences, the attempted list, the
  discrepancies. Its `_readme` carries the two-voices rule (see the snake note).
- NOT recorded, and why:
  - no efficacy claims in our voice — three firms make them and all three are
    quoted as theirs;
  - `first` pins three, each for a stated reason written on the card
    (publishes a licence number / publishes a price / works in English);
  - **six records left `needs-pin`** rather than pinned. `geocode_local` can only
    reach postcode centroids for ต้นเปา, หนองผึ้ง, สันผักหวาน, หนองจ๊อม, ท่าสาย and
    บ้านดู่ — 3.3 to 12.5 km of uncertainty. A 12 km circle is not a pin. Three
    are pinned and say how: Unipest CM on Chotana Rd (street, 280 m), Happy
    House (tambon+amphoe, 592 m), Unipest CR (tambon+amphoe, 540 m).

## Prices

All `_pricesVerified: false`. Only one firm publishes a number at all (Happy
House, 3,900 first visit). The LM rate ranges are the trade's published method,
not a quotation anybody was given. The page says both, twice.

## The four outputs

- [x] records with dated sources in data/curated/additions-*.json → import_all.py
      (cm 8, cr 3; `cm: 234 curated shelf addition(s) applied`)
- [x] entry in data/asked.json filled (find / lead / notes), `draft` deleted
- [x] `make_shelf_cards.py --only asked-exterminator` → build.py → test_asked.py PASS
- [ ] `python3 make_post.py exterminator` — the reply, when Nan wants to post it

## Doors left open, each needing a walk or a call

- **Nobody's price has been read off a real quotation.** One firm's written quote
  for one real house turns the whole pricing note from published to walked.
- **The FDA register has not been queried for any of these eleven.**
  excercitium.fda.moph.go.th takes a company name; eleven lookups would turn
  `fdalicence` from "they say so on their site" (1 firm) into measured fact
  across the shelf. That is the single highest-value next act on this shelf.
- **English is claimed by exactly one firm** (Green Nano Thai, by having an
  English site). Whether any of the other ten can work in English is unknown and
  the facet is therefore absent rather than false — ten phone calls settle it.
- Six pins. A photograph of any of these shopfronts with its own coordinates
  closes one each.

- **`attrs.phoneAlt` renders nowhere.** Nine of these eleven firms publish two to
  four numbers and `channels()` takes one: `phone` is split on `;` and only the
  first survives, so a second number has no home in the schema. The extra
  numbers are written into the blurbs, where a reader does get them, and
  `phoneAlt` carries them as data for whoever renders a second row. It is
  recorded here as a known dead field rather than left to be rediscovered — the
  same trade this file makes everywhere else.
