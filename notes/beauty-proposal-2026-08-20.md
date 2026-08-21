# WO-22 — เสริมสวย-ตัดผม: the barber correction, the words, and the doors

*2026-08-20. Zero-network half BUILT. The doors below await a numbered go.*

Nan's ask, verbatim: *"Do whatever you can to enrich mot dang for beauty/barbers.
particularly interested in afro textured hair, americana/british style barber shops
with hipsters, hair extensions, braids, updos, digital perms, high tech hair studios,
and people who make house calls."*

Eight axes. This note records what was measured, what was built without touching
the network, and what each remaining axis is actually blocked on — because the
answer differs sharply between them, and three of the eight cannot be answered by
any amount of crawling.

---

## 1. What the measurement found

`importers/audit_beauty.py` (new, zero network) reads every record's own name.

| axis | names that declare it | on the shelf before | after |
|---|---|---|---|
| barber | **59** | 6 | **62** |
| salon (เสริมสวย) | **62** | 0 | **62** |
| extensions / braids | 1 | 0 | 1 |
| nails | 15 | 9 | 18 |
| digital perm / rebond / updo | **0** | — | — |
| afro / textured / curly | **0** | — | — |
| house calls | **0** | — | — |
| "high tech" studio | **0** | — | — |

Two of those lines are bugs that had been sitting in front of readers, and four
are honest holes.

**The barber shelf held six shops in a city with sixty-two.** OpenStreetMap sets
`hairdresser=barber` on 6 of the 371 hairdresser/beauty points in the snapshot, so
6 is what the classifier filed. Fifty-three more shops put BARBER on their own
shopfront — สุเทพบาร์เบอร์, Sweeney Todds, Backstreet Barber Shop, Cutlers,
เมืองใหม่บาร์เบอร์, Rebel House, Lemme 184, ปุ๊ บาร์เบอร์ — and every one of them sat
on ร้านทำผม, indistinguishable from a blow-dry counter.

**The salon shelf held none at all**, and was on `KNOWN_EMPTY` with the reason
*"no OSM signal separates a salon from a hairdresser"*. That was true about the
tags and false about the shops. เสริมสวย is THE Thai word for a women's salon and
it was in sixty-two names the whole time. The signal was never in the tag; it was
on the sign, in Thai. **The lesson is worth keeping: before a shelf is declared
unfillable, read the names — in the language the shop wrote them.**

**The four zeros are real and are not a crawl problem.** Across all 18,686 records
in both provinces, not one shopfront says perm, updo, afro, textured, or house
call. There is no name rule waiting to be written. Those axes are answered by the
shop stating it, by an owner ticking their own facets, or by somebody standing at
the door — and by nothing else. `audit_beauty.py` prints all four counts every run
so the hole stays visible instead of being quietly forgotten (same discipline as
GEAR in `audit_muaythai.py`, which is also expected-zero).

### The เปีย guard

เปีย alone means a braid, and a bare เปีย rule files **fifteen** places in this
catalogue as braiding salons: บ้านเปียง, ยางเปียง and เปียงหลวง are Northern Thai
village names, so it would have caught five health stations, four temples, three
schools and a bakery (ซีเปียวพาณิชย์). Only the compound ถักเปีย is ever a rule.
The strays print every run so the guard can be seen working — same shape as the
หมวย/มวย guard.

---

## 2. What was built (all zero-network)

1. **`importers/audit_beauty.py`** — eight reports + `--emit`, the เปีย stray guard.
2. **126 shelf corrections folded** into `data/curated/shelves.json`, each sourced
   `osm name: <the shop's own sign>`. Barber 6 → 62, salon 0 → 62, nails 9 → 18,
   extensions 0 → 1.
3. **`beauty/extensions`** (ต่อผม-ถักเปีย) added to `data/categories.json`.
4. **The `beauty` facet set** — 30 questions in `data/facets.json`, covering every
   one of Nan's eight axes: `textured`, `braids`, `extensions`, `wigs`, `updo`,
   `digiperm`, `rebond`, `colour`, `bleach`, `fade`, `razorshave`, `beard`,
   `scalpcheck`, `treatment`, `keratin`, `housecall`, and the rest.
5. **Three OSM tags rescued.** `male`, `female` and `unisex` are the only three
   things OpenStreetMap knows about a hair shop beyond its existence, and the
   import threw all three away on every run. 26 shops now state who they cut for.
   Only `yes` counts — `male=no` is a real and different statement and this layer
   cannot render an absence, so it is left silent rather than mis-rendered.
6. **`data/curated/beauty.json`** — the services register, shape defined, empty
   and saying so, with its read queue generated from the records.
7. **`beauty_layer.py` → `/beauty.html`** — the words (22 terms with RTGS, tone and
   root; 5 whole sentences), both shelves, the textured-hair answer, and a printed
   census of the silence.
8. **`worker/worker.js`** — 20 new facet keys accepted from owners and passers-by.

### What the page refuses to do

It does not sort barbers into the hip ones and the ordinary ones, the farang ones
and the Thai ones. Sixty-two shops put BARBER on the sign and they are listed
together, alphabetically, unranked — exactly as the elephant camps are. A reader
can read a shopfront. Nan's "americana/british style with hipsters" is a real and
findable thing, and the honest way to serve it is the shop's own name plus the
facets it states (`razorshave`, `fade`, `beard`, `priceboard`), never a vibe verdict
attached to somebody's livelihood.

And it does not guess at textured hair. A wrong yes sends somebody with tightly
coiled hair to a chair where nobody has handled it before, which is a worse
outcome than an honest "nobody has told us yet".

---

## 3. The doors — each needs Nan's numbered go

**1. Widen the `beauty` Overpass group.** It is two selectors today,
`shop=hairdresser` and `shop=beauty`. Unqueried and directly relevant:
`shop=hairdresser_supply` (wig and extension suppliers — Nan's extensions axis),
`shop=wig`, `shop=cosmetics`, and `craft=hairdresser` (how a stylist working out
of their own home is tagged — Nan's house-call axis). One Overpass call per
province. *Note: `craft=hairdresser` is likely to return zero here — the crafts
group already queries `craft=*` with a name and none appeared — so it is worth
running once to close the question, not worth hoping on.*

**2. Read the 18 shops that already have a page.** 18 beauty records carry a
website, a Facebook page or a LINE link. Those are the first 18 rows of
`data/curated/beauty.json`, and the fastest way to get real service data onto the
site. Listed on `/beauty.html` under the register.

**3. The door survey.** The 30 facets exist so somebody can walk Nimman,
Santitham and the moat and tick them. This is the only door that answers
textured hair, digital perms and house calls at any scale, because those four
axes have no other source in existence. Fifteen shops on one afternoon would put
this site ahead of every other directory of this city on a question none of them
even asks.

**4. TTD (WO-17).** The Thailand Tourism Directory's spa/beauty category carries
phone, LINE and hours. Blocked on the same API key as WO-17; folds the same way.

**5. A data-quality bug spotted in passing, no go needed.** `Akshaya E Centre`
sits on `beauty/hair` with the website `akshaya.kerala.gov.in`, which is an Indian
state government e-service portal. Almost certainly a bad OSM record. Worth a
`retags.json` entry with a receipt, or an upstream fix when somebody has an editor
open.

---

## 4. What Nan asked for, axis by axis

| Nan's ask | where it now lives | state |
|---|---|---|
| afro / textured hair | facet `textured`, the gap panel on /beauty.html, the sentence to ask | **measured at zero and said so** — door 3 |
| americana/british barbers | the barber shelf, 6 → 62; facets `razorshave`, `fade`, `beard` | **built**, unranked by design |
| hair extensions | shelf `beauty/extensions`; facets `extensions`, `wigs` | shelf built (1 shop); doors 1 + 3 |
| braids | facet `braids`; the word ถักเปียแถว on the page | built; doors 1 + 3 |
| updos | facet `updo`; the word เกล้าผม with its root | built; door 3 |
| digital perms | facet `digiperm`; ดัดดิจิตอล + ดัดวอลลุ่ม on the page | built; door 3 |
| high-tech hair studios | facets `scalpcheck`, `keratin`, `treatment` | built; door 3 |
| house calls | facet `housecall`; ไปทำถึงที่ + the sentence to ask | built; doors 1 + 3 |

Five of the eight are fully served by the words alone, today, with no network:
a person who can say ดัดดิจิตอล, ถักเปียแถว, เกล้าผม, ต่อผม and ไปทำถึงที่ can get all
five in this city from shops that already exist and simply never wrote it down.

---

# Postscript — all four doors run, 2026-08-21

Nan's go: *"go on all four doors."* What each one actually returned.

## Door 1 — widen the `beauty` Overpass group · RUN, and it closed a question

Four selectors added to `crawl_overpass.QUERIES["beauty"]`, refetched for both
provinces (`--group beauty --fetch`; CM near-ring, CR province-wide).

| selector | Chiang Mai | Chiang Rai |
|---|---|---|
| `shop=hairdresser_supply` | **0** | **0** (asked twice) |
| `shop=wig` | **0** | **0** (asked twice) |
| `craft=hairdresser` | **0** | **0** (asked twice) |
| `shop=cosmetics` | 33 | 8 — **not filed** |

**Zero new hair shops of any kind.** The extension-and-wig supply trade and the
stylist working from her own front room are simply not in OpenStreetMap here.
That settles something worth settling: the extensions and house-call questions
cannot be answered by crawling *at all*, only by a shop stating it or a person
asking at a door. A question closed, not a crawl that failed.

The cosmetics haul is left in the cache and filed nowhere. ร้านเครื่องสำอาง is
retail, not a chair, and this shelf is called เสริมสวย-ทำผม; more than half the
answer is unnamed, and several rows are massage venues wearing a cosmetics tag
("Sense Massage & Spa", "massage by ex-prisoners", "Jera Thai massage school")
that would have arrived as name-duplicates of places we already hold. A
cosmetics shelf, if ever wanted, belongs under `shopping` as its own decision.
The finding is written into the crawler beside the selectors so nobody re-runs
the experiment hoping for a different answer.

## Door 2 — read the shops' own pages · RUN, one real row

New: `importers/read_beauty_sites.py`. Same manners as `enrich_sites.py`
(robots asked and obeyed, one page per shop, a second between requests) and the
same first-hand rule — which is what cut this door down:

- **18 records carry a link, but only 8 are the shop's own domain.** Ten are
  Facebook, Instagram or LINE. `enrich_sites.NOT_FIRST_HAND` has always
  excluded those, a login wall is not a statement by a shop, and my own read
  queue of "18 shops to read" was therefore overstated by more than half — the
  same class of error as the barber shelf, a number that flattered itself.
  `/beauty.html` now counts the two apart.
- Of the 8: three domains no longer resolve, one timed out, one is refused by
  robots.txt. **Four pages were read.**
- Three of the four state none of the services asked about (an Indian state
  e-service portal mis-filed on the hair shelf, a listed pharmaceuticals
  company, a Chiang Rai retreat).
- **One shop states six services in its own words: New York, New York** —
  digital perm, Japanese straightening, colour, keratin, hair treatment,
  wedding hair. Every claim is stored with the sentence it was read from.

That single row moves **`digiperm` and `updo` from zero to one** — two of the
eight axes now have a named shop, where the whole catalogue had none. It also
proves the register works end to end: read → `stated` → facet pill on the
shop's own page, provenance `site`, which now sits between an OSM tag and a
person at the door in `FACET_SRC_NOTE`.

Fixed in passing: `enrich_sites.first_hand()` returned **True** for a URL with
no scheme, because `urlparse("m.facebook.com")` leaves `netloc` empty and the
blocklist matched nothing. Two beauty records carry exactly that shape. The bug
was silent in the one place this repo is least willing to be wrong — where a
fact came from — and it affected every importer using that helper, not just
this one.

## Door 3 — the door survey · THE INSTRUMENT IS BUILT; the walk is Nan's

A survey needs somebody on a footpath, and that is not something this session
can do. What it can do is make the walk cheap, so: **`assets/reader/hair-words.pdf`**,
two A4 sides, black only, Thai set large enough to point at across a counter —
the same discipline as the massage, muay and cooking sheets, and measured to
two sides with `--measure` rather than guessed.

Front: a cut, and the chemical words nobody can improvise (ดัดดิจิตอล and why
ดัดผม alone gets you a cold perm). Back: extensions, cornrows and updos; the
coiled-hair question with its follow-up; money and the house-call phrase. Plus
**what the door tells you before you ask** — the price board, the digital perm
machine visible from the street (no machine, no digital perm, whatever the
answer at the counter), and the photo wall, which is evidence a question cannot
get. Published at `/reader/hair-words.pdf` and linked from `/beauty.html`; the
other four sheets stay print-only, which is their WO's call.

## Door 4 — TTD spa/beauty · BLOCKED, and it was always the weakest door

The keyed API (`api.thailandtourismdirectory.go.th/openapi/read`) needs an
APIKey and SecretKey. `~/.config/nanobotco/keys.json` holds no TTD key, and the
aggregators note already settled whose job that is: *"Accounts are yours to
create, not mine."* Step 0 of WO-17 is unchanged and it is Nan's.

The open alternative — MOTS's "รายการสปา" extract on data.go.th, Open Data
Common — is real, and we do hold a `data_go_th` key. But the note recorded the
dataset's *name* and never its id, the key's base (`opend.data.go.th`) serves
the portal's HTML at the CKAN paths, and guessing endpoint shapes is not a
method. The precise unblock: note the dataset id from the data.go.th catalogue
page, and `harvest_datagoth.SOURCES` folds it in one line.

Worth saying plainly even when it opens: **TTD's spa category is 406 listings
nationally, and it is spa, not hair.** It would grow `beauty-spa` and would not
answer a single one of the eight axes Nan asked about. Doors 2 and 3 are where
those answers live.
