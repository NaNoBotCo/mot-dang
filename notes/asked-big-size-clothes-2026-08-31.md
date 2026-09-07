# big-size-clothes — ตัวใหญ่ ใส่ไซส์ใหญ่ ซื้อเสื้อผ้าที่ไหนได้บ้างในเชียงใหม่ ร้านไหนมีเกิน XL

*I'm a big person. Where in Chiang Mai can I actually buy clothes that fit — who stocks past XL?*

- asked_on: 2026-08-31
- via: Nan — "do a mot dang enrichment for large size men's and women's shoes and clothes"
- register: `data/curated/bigsize.json`
- sibling: `big-size-shoes` — a different question with a different answer, kept apart on purpose

## The measurement, before anything else

The catalogue held **14,665 records for Chiang Mai and 6,229 for Chiang Rai, and
zero clothes shops.** Not a thin shelf: no shelf. `shopping/clothes` and
`shopping/shoes` did not exist as keys in `data/categories.json` before today.

It was never OpenStreetMap's fault. The census taken 2026-08-07
(`cache/census/{cm,cr}-shop.csv`) counts:

| tag | CM | CR | held |
|---|---|---|---|
| `shop=clothes` | 134 | 72 | **0** |
| `shop=shoes` | 9 | 9 | **0** |
| `shop=boutique` | 8 | 2 | **0** |
| `shop=bag` | 7 | 1 | **0** |
| `shop=sports` | 23 | 3 | 1 |
| `shop=outdoor` | 13 | 1 | **0** |

`clothes` is the **sixth most common shop value in Chiang Mai** — ahead of
supermarket, ahead of car, ahead of bakery. The reason none of it was here is
one line long and it is in our own file: **`shop=clothes` and `shop=shoes` have
never appeared in `crawl_overpass.py` QUERIES, in any group, since the crawler
was written.** The `shopping` group asks for doityourself, hardware, gift,
second_hand, herbalist and healthcare=alternative, and not one of them is a
clothes shop.

Fifth sighting of the same lesson: เสริมสวย on sixty-two shopfronts, the notary,
ห้องเสื้อ on a hundred and twenty-six, ห้องซ้อม, and now this. **KNOWN_EMPTY can be
a fact about the question, not about the city.**

### And the one record that said it out loud was filed as a restaurant

Of 20,894 records in two provinces, exactly one names itself big-size:
**ร้านเสื้อผ้า The Bigsize**, OSM node 4358877280 — and it stood on the food shelf
as a Thai restaurant, because a mapper wrote `amenity=restaurant` and nothing
here ever read the name. ร้านเสื้อผ้า *is the first word of it*. Retagged in this
order (`data/curated/retags.json`) with the element's own name tag as the
receipt. The second-nearest record, บื๊กไซส์ชิกชิก, was read by WO-49 as a
repair shop — true, and only the half of the name after the comma.

## The question, in the trade's own word

`ไซส์ใหญ่` · `บิ๊กไซส์` · `คนอ้วน` · `สาวอวบ` · `ตัวใหญ่` · `ไซส์พิเศษ` · `พลัสไซส์`

**And the finding is that there is no such category anywhere.** Not in OSM's tag
vocabulary; not on CMHY.city, whose apparel index runs to 583 places across four
categories and has no big-size one; not on any Thai directory read for this
order. A shop that carries a 3XL is not a *kind* of shop in this city — it is an
ordinary shop that happens to hold the size, and the only place that fact is
written down is the shop's own name, its own hashtags, or its own description.

So `importers/read_bigsize_sites.py` does not filter a category. It reads all
four apparel categories whole and **scores** every record for the words. The
denominator is part of the answer.

## Sources (url · fetched · what it supports)

- `cache/census/{cm,cr}-shop.csv` · 2026-08-07 · the 282 elements above, and the zero
- `cache/overpass/{cm,cr}/clothing.json` · 2026-08-31 · the new crawl, this order's own
- https://www.cmhy.city/category/33-Personal/ · 2026-08-31 · 583 apparel places, 4 categories, no big-size category
- https://www.xlarge.co.th/pages/… (size chart) · 2026-08-31 · a Thai brand called XLARGE stops at XL; denim to a 36-inch waist; socks "ONE SIZE: US 7 ~ US 9"
- https://www.uniqlo.com/th/en/special-feature/extra-size/men · 2026-08-31 · XXL/3XL/4XL exist in Thailand and are **online-only**, with Click & Collect into a branch — read through a search index, not off the page (uniqlo.com timed out this fetcher twice; see *Attempted*)
- https://www.uniqlo.com/th/th/special-feature/click-and-collect · 2026-08-31 · the collect-in-branch half of that

## What the crawl actually returned

**CM 106 elements** — 78 clothes, 11 sports, 8 shoes, 6 outdoor, 3 bag, 2
boutique. **CR 42**, all six selectors first time. The `boutique` selector gave
up on the CM run after six rests (Overpass 500) and the group was correctly
marked `incomplete`; it was retried through the crawler's own `fetch_wide`, and
merged, and the flag is cleared — the file is not short and does not say it is.

**The shelves, from zero this morning:**

| | CM | CR |
|---|---|---|
| `shopping/clothes` | **79** | **32** |
| `shopping/shoes` | **8** | **4** |
| `shopping/sports-shop` | **17** (was 1) | **5** (was 0) |

**145 records on three shelves that between them held one.**

The named-only filter is doing its job: 134 census `shop=clothes` became 76 with
a name. An unnamed clothes node is a dot, not a shop anyone can go to.

**Nine records looked misfiled from their names. Eight of them were not, and
that is the more useful result.** Every one was checked against the element's
own tags before anything was touched:

| record | looked like | its own tags said | verdict |
|---|---|---|---|
| doi cycling studio | a bike shop | `clothes=sports;cycling_apparel` | **correct** — it sells cycling clothing |
| Munee Hostel | a hostel | `clothes=women` + `check_date=2026-02-08` | **left** — somebody surveyed it and wrote women's clothes |
| 360 องศาฟิตเนส | a gym | `shop=sports` + `sport=fitness;treadmill;spinning` | ambiguous — a gym or a shop selling the machines |
| kayaking Center | a tour operator | `shop=sports` + `sport=canoe` | ambiguous |
| ChiangMai Rock Climbing Adventures | a climbing wall | `shop=outdoor` + `description=bouldering` | ambiguous — may be both |
| شنجماي المنتجع ("Chiang Mai resort") | a resort | `shop=sports`, and nothing else at all | no evidence either way |
| DECATHLON CHIANGMAI | a fourth Decathlon | `amenity=cafe` + `cuisine=coffee_shop;tea` + `name:en=Eplus Bspase` | **correct as a café** — its Thai name field holds the landmark it stands beside, 35 m from the real Decathlon |
| ร้านเสื้อผ้า The Bigsize | a clothes shop | `amenity=restaurant` and **no** cuisine, hours or anything else | **retagged** — the name is the whole receipt |
| Motorbike & car rent 080-2464381 | a car rental | `shop=outdoor`, and one other tag: that name | **retagged** to `transport/rental` |

**Two retags out of nine suspicions.** A record only comes off a shelf when its
own element carries the receipt; a name that reads wrong to me is a lead, not
evidence. The four ambiguous ones stay where the mapper put them and are written
down here instead, which is what this table is for.

Also on the clothes shelf, correctly tagged but a different trade: two fabric
shops, two screen printers, a dressmaking *school*, and two tailors WO-49
already holds. Those are OSM's `shop=clothes` being a broad tag, not an error.

**A false-positive trap worth recording.** The word for the Shan is **ไทยใหญ่**
— literally "big Thai" — and Chiang Mai has at least five shops selling ชุดไทยใหญ่,
Shan dress. A naive substring search for ใหญ่ files every one of them as a
big-size shop. `read_bigsize_sites.py` scores whole words and gave them zero,
which is the only reason they are not on this page.

## And the Thai directory: one in five hundred and eighty-three

`read_bigsize_sites.py` read all 583 apparel places CMHY.city carries across its
four apparel categories — **474 with their own published GPS, 332 with a phone,
184 updated in 2025 or 2026** — and scored every one of them for the words the
trade uses on itself.

**Exactly one says a big-size word on its own page.**

> **ปุ้มปุ้ย บิ๊กไซส์ (สาขาคำเที่ยง)** — its own trade tags are `เสื้อผ้าบิ๊กไซส์`
> and `เสื้อผ้าสาวอวบอ้วน`; ถ.ตลาดคำเที่ยง ต.ป่าตัน; 081-169-2099; its own
> published GPS. Recorded as `cm-curated-pom-pui-big-size-kham-thiang`.

Two independent routes meet on this one shop: the Thai directory has it, and a
search of the Facebook trade surfaces the same business as ร้านปุ้มปุ้ย เสื้อผ้า
สาวอวบอ้วน บิ๊กไซส์เชียงใหม่, linking to the same page the directory names.
"(สาขาคำเที่ยง)" says branch, so there is more than one.

**What one-in-583 means, said carefully:** not that Chiang Mai has one big-size
shop — the evening trade at กาดหน้ามอ is real and this is not it — but that
**the trade does not write the fact anywhere a directory can read it.** Which is
why this order builds an honest `clothes` shelf and does not invent a big-size
one: a size claim we made on a shop's behalf would be the one thing on the page
nobody could check.

## The answer, and why it is not a list of shops

Three routes, and a reader needs to be told which one they are on:

1. **Buy it — Thai big-size retail.** Real, and better than its reputation: the
   Thai trade runs to 5XL–10XL and states its range in **inches** (อก 40–60 นิ้ว),
   not in letters. It is overwhelmingly women's — สาวอวบ, ชุดคนอ้วน — and in Chiang
   Mai it trades **at กาดหน้ามอ and The Chiang Mai Complex, in the evening,
   16:00–22:00**. That is the mechanism behind its absence from every map: a
   stall that opens at six is invisible to a daytime survey. Third-party until
   somebody walks it — Facebook would not serve its own pages to this fetcher.
2. **Buy it — the international chains.** The crawl found Uniqlo, H&M ×2,
   American Eagle, Lacoste, McOutlet, Sportsworld. **The Uniqlo answer is the
   one worth printing and it is counter-intuitive:** Thailand's XXL/3XL/4XL are
   an online line and are *not stocked in branches* — walking into Central
   Festival gets you nothing past XL — but Click & Collect delivers the extra
   size to that same branch. The shop is right and **the door is wrong**.
3. **Have it made.** This directory learned 67 tailors yesterday (WO-49). For a
   shirt at any size this is cheaper and better than a rail, and it is the whole
   men's answer, because there is no men's equivalent of the สาวอวบ trade here.

## The rule the page exists to teach

**Ask in inches, not in letters.** Thai clothing is sold by อก (chest) and เอว
(waist) in นิ้ว; S/M/L/XL sits on top as decoration and every brand draws it
differently. The cleanest proof is a Thai brand *called* XLARGE whose published
chart stops at XL, whose denim stops at a 36-inch waist, and whose socks are
"ONE SIZE: US 7 ~ US 9".

And **ฟรีไซส์ is not a size — it is a ceiling with a friendly name.** The only
useful reply to it is *กี่นิ้วคะ*.

## Decision

- found: shelf `shopping/clothes` created and filled from the new crawl; no separate
  big-size shelf, because **no such category exists** and inventing one would put
  a shop on it on our authority rather than on its own
- shelf: `clothes` (เสื้อผ้า-เครื่องแต่งกาย), `shoes` (รองเท้า), `sports-shop`
  (ชุดกีฬา-อุปกรณ์กีฬา) — three children added to `shopping`, above `tailor`, because a
  reader who can buy off a shelf should not be sent to have something made
- facet: none. A `bigsize` facet would need a size read off a rail, and nobody
  has walked one. Written into the register as the first lead instead.
- NOT recorded: the individual Facebook/Instagram/TikTok sellers as directory
  records — every address and hour available for them today is a search-index
  summary rather than a thing read off the shop, so they are leads for a walk
  and they do not get pins.
- NOT recorded: a letter-to-letter conversion table. It would be the most
  shareable thing on the page and the most likely to send somebody home with a
  shirt that does not fit.

## Prices

All `_pricesVerified: false`. The only figure carried is the Kaidee listing's
"from 200 ฿" for Fattyshop, which is old and unverified and is in the register
as a lead, not on the page.

## Attempted, printed, not guessed

- `facebook.com/bigsizechiangmai` and the other shop pages — served a title line
  and nothing else, login-walled. Their locations and hours are third-party.
- `uniqlo.com/th/…` — timed out this fetcher twice, from two different paths.
  The extra-size facts are the search index's reading of Uniqlo's own pages.
- A Thai shoe conversion table found by search returned **EU 44 = 24.6 cm**,
  which is about a 39. Not used. Recorded because it is the shape of the hazard.

## The four outputs

- [x] shelf children in `data/categories.json`; `clothing` group in `crawl_overpass.py`;
      classification in `import_overpass.py`; retag + shelves for The Bigsize
- [x] register `data/curated/bigsize.json`
- [x] entry in `data/asked.json` filled, `draft` deleted
- [x] `make_shelf_cards.py` → `build.py` → `tests/test_asked.py` **PASS**
