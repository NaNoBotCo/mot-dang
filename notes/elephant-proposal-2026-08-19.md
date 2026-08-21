# ช้าง — the register, the shelf, the city's elephant names: making Mot Dang and wichaa deep where they were empty

*2026-08-19. Nan: "I want to do an enrichment on elephant-related topics for
Motdang AND wichaa." This note is the measurement, the rule the shelf runs on,
and what was built the same day under WO-19. Read with `MARCHING-ORDERS.md`
WO-19; the reasoning is here and is not repeated there. The wichaa half is
`manuscript-wiki/content/entity-chang.md` and its registry rows in `wiki.py`.*

## The measurement, before any proposal

Elephants lived on this site as **place-names and nothing else.**

| What a reader asks | What the site held on 2026-08-19 evening |
|---|---|
| Which camps are there, and what happens at each? | **No camp.** Of 16,268 records, 66 carry ช้าง or "elephant" in the name and **not one is an elephant camp** — they are the city's elephant names (ช้างเผือก ×11, ดอยช้าง ×11, ช้างคลาน ×5, ช้างม่อย, ล่ามช้าง, ช้างค้ำ, พวกช้าง, เกาะช้าง, กื้ดช้าง…), two restaurants called Uncle Chang, four called Golden/Black/White Elephant, a poo-paper park, and Anantara's Chiang Rai resort. `crawl_overpass.py` has **never asked for `tourism=zoo`, `tourism=attraction` or `tourism=theme_park`** — so Maesa (1976), Elephant Nature Park, Patara and the whole Mae Taeng / Mae Wang / Mae Chaem valley, the busiest elephant country in the kingdom, were never fetched. Same shape as WO-12's `sport=muay_thai` = 0. |
| Does this one offer riding? bathing? shows? can I just watch? | Nothing to answer with. |
| Where is the elephant hospital? | Not in either province (Lampang) — and the site did not say so. |
| Is there an elephant day? | `festivals.json`: zero. Not even วันช้างไทย. |
| Why is the north gate the White Elephant Gate, and what is Wat Lam Chang? | The gate and the temple were records; the elephant in their names was invisible. |
| Does wichaa carry it? | **Yes, and nobody had looked.** The manuscript catalogue (6,986) holds **31 witnesses**: a ลักขณะช้าง elephant-marks treatise (Nan, ms 538), two สู่ขวัญช้าง rites (Nan, mss 367 and 4047 — the second from Wat Phra That Chang Kham itself), the six-tusked Chaddanta jataka in four copies, the local white-elephant jatakas (สีวิไชช้างเผือก ×3, สุวัณณะช้างเผือก ×2, ช้างโพง ×6, ช้างเจ็ดหัวเจ็ดหาง ×6 incl. a 147-page Mae Hong Son copy, ช้างสามงาปลาสามเงี่ยง ×3), an animal-marks compendium (Lampang, ms 5131: cattle, cat, tiger, lion, otter, elephant, mouse), a Phayao compendium with a section แปงช้างเผือก "making the white elephant" beside a rain-asking text — and in the 30 woven contributed volumes, a พระคาถามหาช้าง that makes others see you as an elephant, a ยันต์เทียน ๔ พญา with พระยาช้างเผือก among four albino lords, a คาถาพระเจ้าสอนช้าง with Nalagiri's name inside a working training formula, and a rachasi carved from ivory "that has broken a tree". **The horse entity (`ma`) scores 0 and the chicken 5; the elephant scores 31.** No article existed. |

So "elephant enrichment" is not a thin shelf made thicker. It is a shelf that did
not exist, on top of a corpus that turned out to be one of the richest animal
subjects in the archive.

## The rule this shelf runs on

Massage's rule was *never infer respectability*. Culture's was *never infer
whether a reader is allowed in, never infer price*. Muay thai's was *the venue
states its own nights*. The elephant's is:

**The venue states what happens with its elephants — riding, bathing, shows,
hands-off, how many, where they are at night — or the page says nobody has
stated it. The law says what is registered. And this site never ranks a camp
into ethical and unethical, sanctuary and show.** "Sanctuary", "ethical" and
"rescue" are a venue's own words and render as the venue's words, in quotation,
with a date. There is no welfare score. A reader who wants to choose by a
standard is told what each standard IS — a legal register, a private audit, an
advocacy list, a membership — and which a camp holds is a question for the camp.

Why it has to be this strict: a wrong "unethical" is a slur on a named Karen
family's camp and its village, published at this site's scale; a wrong
"ethical" sends a reader somewhere under false comfort. Both are statements
about a named business. `feedback_no_tourist_framing` applies in full — the
family camp on a Mae Wang hillside and the 75-elephant park are both ปางช้าง,
and no line on this site sorts them into real and otherwise.

Four consequences, all in the data shape:

- `data/curated/elephants.json` carries, per venue, a `stated` block —
  `riding / bathing / shows / handsoff` — whose values are `no`, `yes`,
  `program`, `all` or **`unstated`**, with `stated_by: "venue"`, `source` and
  `fetched`. `"no"` is written only when the venue's own page says so in words.
  `"unstated"` renders in italics and the legend says it is neither a no nor a
  yes. A venue whose pages could not be read is in `unreachable`, by name, with
  what happened (403, DNS, 404).
- Each curated record carries `attrs.selfDescription` (what the venue calls
  itself, quoted), `ridingStated`, `elephantProgram`, `elephantsStated`, all
  with `programVia` = "venue website, read <date>"; `known_facts()` renders
  them under "calls itself", "riding", "with the elephants, in its words",
  "elephants, as stated". No facet is ticked from a name, a shelf or a website
  (`_chang_note` in facets.json); the 16-facet `chang` set is the door survey's
  script and the owner's to tick.
- Prices are the posted **spread**, never welded to a program the page did not
  pair them with (the shelf-card lesson), and carry `_pricesVerified: false`
  until somebody reads a board at a gate.
- The audit (`importers/audit_elephant.py`) reads NAMES and the crawl's own
  tags, and nothing else. Bare ช้าง is never a rule: ลุงช้าง is a nickname,
  Chang is a beer, ช้างเผือก / ช้างคลาน / ช้างม่อย / ดอยช้าง / เกาะช้าง /
  กื้ดช้าง are places, and โรงพยาบาลช้างเผือก is a hospital for people that
  begins with the letters โรงพยาบาลช้าง (fenced `(?!เผือก)`, the จังหวัด/วัด
  trap again). ช่าง with the other tone mark is a craftsman and never matches.
  A hostel called Baan Elephant Home is a hostel (LEADS, not CAMP); a resort
  "and Elephant Sanctuary" is a resort with a camp beside it and enters from
  its own page or its own name through shelves.json.

## What was built (2026-08-19), pillar by pillar

### The shelf

- **Tree, additive:** new top-level cat `chang` (ช้าง · Elephants) after
  `cooking`, three children — `camp` ปางช้าง-ศูนย์ช้าง (sub `elephant-camp`) ·
  `care` คลินิกช้าง-โรงพยาบาลช้าง (`elephant-care`) · `craft` ของช้าง
  (`elephant-craft`). Icon `i-chang` drawn into the sprite; schema.org
  `TouristAttraction`, with `VeterinaryCare` and `Store` through
  `SCHEMA_TYPE_SUB`. Nothing in KNOWN_EMPTY: all three children find records.
- **Sixteen curated records** in `additions-chiang-mai.json`, each from its
  own site, dated 2026-08-19, pins carrying the precision they earned — a
  venue's own map embed or JSON-LD → `approx` (Maesa/The Chang, Maetaeng
  Elephant Park & Clinic, Kerchor, Elephant Freedom Village, Happy Elephant
  Home); a road or tambon match from `geocode_local` → `approx` with the
  uncertainty (the ENP, EJS, Baanchang and Into the Wild booking offices in
  town, Elephant Parade at San Phi Suea); nothing → `needs-pin`, on /pins.html
  (Patara, Thai Elephant Home, ChangChill, Kindred Spirit, BEES, Chiang Dao).
  The gazetteer cannot reach Kuet Chang, Mae Win or Mae Suek at all — the
  hill tambons are outside its ground — which is the designed state, not a
  bug.
- **Audit → shelves.json:** `audit_elephant.py --emit` proposed one entry
  (Elephant Poopoopaper Park → craft); applied. The Anantara resort (CR) was
  added by hand with the GTAEF page as source — its own name says Elephant
  Sanctuary. CAMP by name = **0**, as expected: no crawl ever asked.
- **Facet set `chang`** (16: no riding / riding / bathing / feeding /
  hands-off / no shows / no hook / unchained at night / vet / papers shown /
  mahout program / overnight / volunteers / pickup / children / prices on
  show), `appliesToCat`, after cooking. Nothing ticked.
- **Search:** the teaser carries the vocabulary (ปางช้าง ศูนย์ช้าง ดูช้าง
  ป้อนช้าง อาบน้ำช้าง ควาญ ช้างเผือก คลินิกช้าง กระดาษมูลช้าง · camps
  sanctuaries mahouts white elephant poo paper). Re-mine of search-core is in
  the open list.

### The register — /chang.html (`elephant_layer.py`)

- **The table:** camp × riding · bathing · shows · hands-off · elephants ·
  posted — bold = the camp says so in words, italic *unstated* = the pages
  read did not say; then a card per venue with its self-description in
  quotation, its program in its own words, the posted spread with the
  unwalked mark, source, date and `stated by`. Then the unreachable (Chai Lai
  Orchid 403, Maetaman no site found, Ran-Tong 404, Elephant Rescue Park
  403, FAE 403, Anantara's own site 403, Four Seasons 403), the unconfirmed
  (Elephant Valley Thailand — two travel writers say closed May 2020; Ban
  Ruammit by name), the Chiang Rai line.
- **Two laws and the bodies, named as what they are:** ตั๋วรูปพรรณ under the
  Draught Animal Act B.E. 2482; wild elephants under the Wildlife Act B.E.
  2562; the Department of Tourism's voluntary camp standard; ACES (a private
  audit); World Animal Protection (an advocacy list — ChangChill says on its
  own site it works with them); the Thai Elephant Alliance (a membership).
  All `general-knowledge`, and the page awards none.
- **Lampang:** the National Elephant Institute / Thai Elephant Conservation
  Center with its four phones and stated programs (bathing 10 min, 1-day
  mahout, homestays, the advanced-mahout workshop), and FAE by name (403).
- **The city's elephant names:** fourteen landmark cards with the tradition
  each carries, marked *tradition holds* — the White Elephant Gate and its
  twin-elephant monument (no record yet — a pin errand), Wat Chiang Man's
  elephant-ringed chedi, Wat Chedi Luang's base, Wat Lam Chang "where the
  elephants were tethered", Wat Phra Singh's chedi, the Doi Suthep relic
  legend, Chang Khlan, Chang Moi, Wat Chang Kham (two readings), Wat Puak
  Chang, Kuet Chang, Nong Ap Chang, Doi Chang — then, live from the data, every
  record with the elephant in its name grouped by element (63 today).
- **The primer:** ปาง the word and the 1989 logging ban (*tradition holds*);
  the mahout, the hook, the questions you may ask; the white elephant and its
  seven marks, the flag, why the city has a gate named for it; money — the
  posted spread computed from the register, the "free pickup" inside the
  price; five questions at the gate; fifteen words with script/RTGS/tone; the
  roots (ช้าง Tai, คช ← gaja, หัตถี ← hatthī "with a hand", กุญชร, ไอยรา ←
  Airāvata); the national day and Lampang. Then the joins to wichaa stated
  from this side: `/a/entity_chang/`, `/a/entity_su_khwan/` (the su khwan a
  camp holds on 13 March is the same rite held for people),
  `/a/entity_vessantara/` (the white elephant that is rain), `/thairoots`.
- Nav: `ช้าง · Elephants` in the svcbar on every page; a band on the elephant
  shelf pages pointing at the register; llms.txt 🐘 section that tells a bot
  to read `stated` and `stated_by` before repeating a claim, and that this
  site draws no welfare verdict.

### Calendar

- **วันช้างไทย 13 March** in `festivals.json` — national, fixed,
  `general-knowledge` (Cabinet 26 May 1998; the date recalls 13 March 1963);
  canon 36 → 37, the test bumped on purpose. The festival's auspicious line
  points at the สู่ขวัญช้าง manuscripts.

### wichaa — the deep half

- `content/entity-chang.md` + the `chang` row in `ENTITIES` (aliases are
  compounds: `khwan cang`, `lakkhana cang`, `cang phueak/phoek/foek`, `cang
  pong/phong`, `cang cet hua/ho`, `cang sam nga/pai`, `cang satan(ta)`,
  `sattanta`, `phanya cang`, `, cang,` — **never bare `cang`** (Bojjhaṅga
  paritta, ms 1266/2083) and **never `chang`** (ตำนานช้างแส่น = Chiang Saen,
  mss 6863/6865; ประวัติปู่อ้ายทิพช้าง is a man) — verified witness by witness,
  31 rows), `ENTITY_HOOKS`, the glossary row, the thesaurus group. Story first:
  the Chaddanta jataka as the paritta tells it, the white elephant that chose
  Doi Suthep, then the treatise, the khwan rites, the kathas and yants, the
  names, the market, the joins back to Mot Dang's register.

## What this note is deliberately not proposing

- ~~No crawl~~ **The crawl ran on 2026-08-20 (Nan's go)** — see the postscript
  at the end of this note. The rest of this section still stands.
- **No scrape** of Facebook, Google Maps, TripAdvisor or the OTAs for camps,
  prices or "ethics" — login walls, their terms, and not first-hand.
- **No welfare verdict, no ranking, no "recommended" list.** Ever. Not even
  a sort by hands-off — the column is there; the reader sorts.
- **No nameTh invented** for the camps: none of the sites read states a Thai
  name, and an invented transliteration is a larger error than an absent one
  (the names.json rule). The blurbs carry the Thai.
- **No Lampang records** — the hospital and the institute are outside both
  provinces and are named in the primer with their phones instead.

## Open, in order of value

1. ~~The Overpass ask~~ **DONE 2026-08-20** — see the postscript. Remaining
   from it: the CR `tourism=zoo` selector never answered (both mirrors 5xx —
   the cache file says `incomplete`); re-run
   `python3 importers/crawl_overpass.py cr --fetch --group elephants` on a
   calmer day.
2. **Pins:** three `needs-pin` camps remain (BEES, ChangChill, Kindred
   Spirit — none in OSM) and the White Elephant Monument, on /pins.html. The
   hill tambons need a ride, not a gazetteer.
3. **The door survey** — the 16 facets' `ask_th`/`ask_en` are its script;
   the "five questions" card is the reader's version.
4. **Prices walked:** one gate read clears the mark for that venue.
5. **The unreachable by another door:** Chai Lai Orchid, Maetaman, Ran-Tong,
   Elephant Rescue Park — their sites refuse bots or are gone; a phone call or
   a LINE message from a person is the next source, dated.
6. **Chiang Rai:** Ban Ruammit by a visit; Anantara's own program page by a
   person's browser; Elephant Valley Thailand's closure confirmed at the gate.
7. **Reader sheet** `chang-words` / `chang-expect` in `reader_sheets.json` —
   the primer is the copy; a money sheet waits on (4).
8. **Share card:** `make_shelf_cards.py` draws `shelf-cm-chang*.png` on its
   next run (needs Chrome); until then the page falls back to the brand card.
9. **Search re-mine** so ปางช้าง / "elephant sanctuary" narrow to the shelf.
10. **The wichaa side's own open list** is in `entity-chang.md`'s closing
    section — the ลักขณะช้าง treatise (ms 538) read leaf by leaf is the one
    that would make the Mot Dang primer's "seven marks" a citation instead of
    *tradition holds*.

---

## Postscript, 2026-08-20 — the Overpass ask, run and folded

Nan's go, the evening after the note. New `elephants` crawl group
(`tourism=zoo` · `theme_park` · `attraction["name"]`), WIDE in both provinces
— the camps are in Mae Taeng, Mae Wang, Mae Chaem and Chiang Dao, all far
outside CM's near ring, so a near-ring ask would have been asking the moat.

**The fence, because attraction is a dragnet.** Elements from this one group
never reach `classify()`: `import_overpass.chang_hit()` (borrowing
`audit_elephant.py`'s name rules — one copy, never two) takes only
elephant-declaring names into `chang`, and everything else — 212 CM + 78 CR
elements: waterfalls, gardens, tiger parks, hot springs, the Karen long-neck
village, night markets — goes to `cache/elephant_review_<prov>.txt`, the
ready-made menu for a future attractions order. A mapper's "(closed 2022)" in
a name is honoured (Chok Chai Elephant Camp stays out, in the review file).

**What came back.** CM 234 elements → **21 camps**; CR 79 → **1** (the zoo
selector never answered — cache says `incomplete`, re-run when Overpass is
calmer). Three review rows were real camps the compounds missed — Elephant
Adventure Sanctuary, Elephant Pride Sanctuary, ศูนย์ฝึกช้างเชียงดาว — so the
CAMP_RULES gained `adventure|pride|ศูนย์ฝึกช้าง`, each verified against a
named witness and against canonical (zero false hits), the alias discipline.

**Reconciled.** Eight merges in `merges.json`, keep = curated (the register
rows and the live URLs), drop = the OSM duplicates, whose refs now ride in
`sources`: Maesa (name+phone+site all match; adopts the surveyed pin and its
Thai sign-name ปางช้างแม่สา), ENP (two adjacent ways; pin is now the park at
Kuet Chang, the office stays in the address), Patara (OSM maps two sites 2.5
km apart — pin is the older survey, pinNote states the second), Thai Elephant
Home and Chiang Dao ETC (both needs-pin → surveyed pins), Happy Elephant Home
(OSM 59 m from the venue's own embed — the two sources agree), EJS (name-
certain merge; the OSM node sits east of the Mae Wang valley, so the pin
STAYS the office rather than adopting an unexplained point), and one
OSM-internal pair (Elephant Pride mapped twice, same phone — the Thai-named,
website-carrying node kept). **`elephant Freedom` (node/9830593117) was NOT
merged** with Elephant Freedom Village: 2.7 km from the venue's own map
embed, no contacts — same name, unproven same place; the door survey settles
it.

**The shelf after:** 18 → **30 records** (28 CM + 2 CR — Ruammit Elephant
Camp on the Kok river entered from the survey, and the Anantara resort keeps
its two doors). 26 camps; needs-pin 6 → 3. Thirteen camps carry no register row —
twelve from the survey (Doiinthanon, Elephant retirement park, New Elephant
Home, Kanta, Hug, Adventure, Pride, Camp Chi, Ghok Dee, Jamlearn, elephant
Freedom, Ruammit) plus the Anantara resort — and /chang.html says so under
"on the shelf; the ants have not yet read the venue's own pages", which is
the register's honest gap, stated in words.
