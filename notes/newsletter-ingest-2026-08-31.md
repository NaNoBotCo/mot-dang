# WO-45 — the weekly newsletter parsed, and the 62 venues no crawl had

Nan, 2026-08-31: *"Please use this content for motdang.net … I bet some of the
locations mentioned don't even show up on crawl. Find out what/where they are
and add all available details, everywhere. Be EXHAUSTIVE."*

Source: the 31 August 2026 issue of the weekly Chiang Mai events newsletter,
39 pages, forwarded as PDF. Text extracted with `pdftotext -layout` and kept at
`_incoming/newsletter/2026-08-31.txt` (that folder is gitignored — per-machine
material, like `cache/`).

The instinct was right. **62 of the venues this one issue names did not exist
in the 14,493-record catalogue in any spelling, in either script.**

## What the issue was worth, measured

| | before | after |
|---|---|---|
| events.json | 82 | 401 |
| contact_leads.json | 4 venues | 99 venues |
| leads with a phone / Facebook / LINE | 0 / 0 / 0 | 50 / 37 / 22 |
| place pages with a "what's on here" band | 0 | 89 |
| catalogue records (cm) | 14,493 | 14,558 |
| venue_aliases.json keys | 4 | 148 |

The issue itself: 67 dated listings, 122 weekly fixtures under weekday headers,
21 notices → **319 events and 139 contact leads**. Every crawled source
combined, on the same run, gave 82 events and 4 leads.

## What was taken, and what was deliberately left

The body text is venue-supplied press-release copy the compiler pastes in. It
is not his writing and it is not ours, and `data/sources.json` has said since
2026-07-29 to treat this as *"a discovery feed for NEW sources … not as a thing
to copy."* So the parser takes the **facts** a listing is made of — when,
where, how much, how to book — and generates every `description` from those
fields. No sentence of the source's prose is copied through.

The prose is still read, for the two things only a newsletter carries: the
first-party contact details a venue types into its own release, and the names of
places nothing else has heard of.

**Notices are not events.** A standing hotel offer is a promotion with no date;
the section yields contact leads only.

## The parse

`importers/read_newsletter.py`. Stdlib only, no network — the issue arrives as
email, so there is nothing to fetch. `harvest_events.py` calls it as a local
source, which puts it under the same validate / atomic / never-destructive
write discipline (WO-41 Phase 2) as every fetched feed: a bad parse is refused
rather than published.

Two things the PDF does that no rule fully solves:

- **Page seams.** `pdftotext` puts a blank line at every page break, splitting
  one listing in two. Rejoining is right at 30 of 39 seams and wrong at 9,
  where the page genuinely starts a new listing. Those 9 are pinned per issue
  in `ISSUES`, hand-verified against the PDF, because a wrong join silently
  merges two events and that is worse than a parse that stops.
- **A weekday header with no blank line of its own** rides the tail of the
  block above it. On this issue that was "Sunday" — which is why Saturday first
  parsed with 41 items and Sunday with 0.

**A weekly fixture is a rule, not a date.** The newsletter states the weekday
and not the dates. Each weekly item is emitted `recurring: True` with the
stated `weekday`, then projected onto its next **two** occurrences, each marked
`from_rule: True`. Two covers the gap to the next issue; the next issue
restates the rule, so nothing here outlives the source that asserted it. Same
discipline as `festival_dates.json`'s "a rule is not a date".

## Where the pins came from

19 listings carried a Google Maps link the venue itself published. Following
the redirect names the place and, for 11 of them, gives coordinates. Those are
`geoPrecision: exact`, and **every one of them cites the link it came from** —
a pin without a citation is an assertion.

The rest went through `importers/geocode_local.py` on the stated address, whose
tier sets the precision honestly: landmark → `approx`, street → `block`,
anything coarser is not a pin and the record says `needs-pin` and keeps the
address. Final spread over the 62: **11 exact, 12 block, 6 approx, 33
needs-pin.** No geocoding service was called; the note in that file's
docstring forbids it and Nominatim's terms forbid the bulk use anyway.

**Two refusals worth keeping:**

- **Addresses that were our inference and not the issue's statement were
  removed rather than pinned.** The Gymkhana Club's road, Anantara's road, the
  Marriott's road, Chotana Mall's tambon — all guesses of mine, all deleted, all
  now `needs-pin`. Fewer pins, every one defensible.
- **Kad Kriangkrai's gazetteer answer was refused outright.** The address
  resolves to Chotana Road with a confident ±280 m — 12 km south of the Mae Rim
  market Google's own link names. The address is kept, the pin is not.

## Venue→place matching, listed as "not built yet" on 2026-07-29

Built, and not fuzzy. Fuzzy was tried before and produced Araksa Tea Garden →
"Garden Restaurant". What shipped is `match_venue()`'s three strict tiers plus a
much larger `venue_aliases.json` (4 keys → 148), with the newsletter's own
naming folded first in `read_newsletter.CANON` — a venue writes itself "The
Mellowship 20:30" one week and "The Mellowship Jazz Club" the next.

Result: **all 95 venues resolve; 100% of newsletter events carrying a venue
string land on a place record** — 231 of 231.

**One trap, and it cost 6 of 90 matches until it was found.** Alias KEYS are
looked up as `_vnorm(venue_string)` — lower-cased, every non-alphanumeric
character collapsed to a space. A key written `UN Irish Pub & Restaurant` or
`The Duke's` can never be hit. Keys go in normalised now, and `_vnorm` keeps the
acute in `café`, so that spelling needs its own key beside `cafe`.

**Two parser fixes came out of chasing the last few percent.** `at the Gymkhana
Club` was skipped entirely, because the pattern demanded a capital immediately
after "at" and an English writer puts a lower-case article in front of a name —
that one listing was the club's only appearance. And two strings named a real
place badly ("Big Bad Wolf Sale" is a book fair held at Chiang Mai Hall;
"Payap Life Long Learning Center Time" had swept up the word "Time:"), both
folded in `CANON`.

**Five records were written and then removed as duplicates** the catalogue
already held under another name — CFCNX, Soi Dog Blues, Stories, สนามกีฬาเทศบาล
ตำบลสุเทพ (18 m from the pin the rugby club's own map link gives) and Duke's
Ruamchok. Each became an alias instead.

## The gaps this closed

Biggest surprises, all confirmed absent under both scripts before being added:
**Chiang Mai Marriott Hotel**, **Cross Chiang Mai Riverside**, **Anantara
Chiang Mai Resort**, the **Gymkhana Club**, **Seven Fountains
Jesuit Retreat Center**, **Sand Creek Golf Course**, **Old Chiangmai Cultural
Center**, and **Chiang Mai Hall inside Central Airport Plaza** — the mall itself
is still absent; the catalogue held six pharmacies inside it and not the
building.

`_missing_from_catalogue` went 5 → 2. Attika Studio and Lecker Café & Bistro are
records; **Araksa Tea Garden** was closed in passing from the Payap lead that
had been sitting in `contact_leads.json` since July. Still open: **Bua Bhat
Factory** (a phone, no address) and **NARIT Astronomy Park** (อุทยานดาราศาสตร์
สิรินธร — nothing in either province's crawl carries NARIT or สดร in any
spelling).

## Contacts onto places that already existed

`data/curated/enrich.json`, whose bar is first-hand sources. A venue-supplied
release is not a directory's scrape of a listing — it is the venue's own words,
one hop — and the entries say exactly that in their `license`. **37 existing
records gained a channel they lacked: 22 phones, 13 emails, 13 Facebook pages,
13 LINE contacts, 2 WhatsApp groups, 4 websites.** Only fields the record
lacked; nothing overwritten.

**Campaign links were not taken as `website`.** Favola's `marriotth.tl` menu
shortlink, the InterContinental's truncated offer URL, and buddhadailywisdom
for วัดทุงยู (the retreat organiser, not the temple). Where the host *was* the
venue's own, only the origin was kept — a seasonal path 404s long before the
domain does.

## Three defects the newsletter's data exposed in older code

1. **`event_when()` printed `%H:%M` unconditionally.** A listing that states a
   day and no hour rendered as *"Every Monday at 00:00"* — the site telling
   readers a yoga class starts at midnight. The iCal and tribe feeds always
   carry a real time, so nothing had ever shown it. It honours `all_day` now.
2. **`dedupe_leads()` copied five fields** and dropped Facebook, Instagram,
   LINE, WhatsApp and the maps pin on the floor — while LINE ranks second only
   to the phone in `channels()`. A field that function does not copy is a field
   the catalogue never sees.
3. **My own first pass filed LINE as `attrs.line`.** `channels()` reads
   `lineId` (an @handle) and `lineUrl` (a lin.ee link); a channel filed as plain
   `line` renders as nothing at all. 22 LINE contacts were silently invisible
   until the keys were corrected. `phone` is semicolon-separated by house
   convention, so a venue that prints three numbers now keeps all three.

Time parsing earned its own fix twice: **"6-11pm" was reading as 23:00**,
because the meridiem sits only on the end of the range — that put Game Tree's
Catan night five hours late. And **"12 noon until 3pm" read as 15:00**, opening
a listing after it ended.

## Sources this issue turned up

- **runlah.com — verified, and the best find.** Event pages are server-rendered
  and carry a complete schema.org `SportsEvent` block: name, `startDate` with
  the +07:00 offset, and a nested Place naming the province. No key, no JS. Its
  *index* is client-rendered (213 words), so slugs still have to come from
  somewhere — for now, this newsletter.
- **sansatan.com — verified.** Race pages server-render 1,399 words with dates,
  distances and fees. No JSON-LD, so it needs a parser rather than a reader.
- **thailandexhibition.com — unverified.** HTTP 200 but 294 words of extractable
  text; no working index path found.
- **ticketmelon.com — blocked.** URLError from this machine, so nothing about
  its content has been measured. Recorded as blocked, not empty.
- **shutupwrite.com — client-rendered.** Its JSON-LD is Organization
  boilerplate with no event data, so runlah's route does not work here.

## Held for Nan

- **The partnership is still unanswered** — offered 2026-07-28, nothing as of
  2026-08-31. Two issues have now been mined without one. That is a fork, not a
  standing decision: ask again, ask differently, or keep mining.
- **Central Airport Plaza itself** is still not a record. The two FDA pharmacy
  pins inside it disagree by 4 km, so neither can be borrowed, and the mall's
  own address was not in the issue.
- **The next issue costs one paste.** Drop the text at
  `_incoming/newsletter/YYYY-MM-DD.txt` and run `harvest_events.py`. Its page
  seams will need one hand-verified pass into `ISSUES` — about ten minutes.
- **1 Instagram and 3 WhatsApp group links** in this issue reached no record,
  because the listing that carried them named no venue the parser could pin.
  A tail worth leaving until a second issue shows whether it repeats.
- **Pre-existing and untouched:** `tests/test_shelf_cards.py` fails on 6 orphan
  og cards (`shelf-cm-learn`, `-learn-gym`, `-transport-station`, and the cr
  three). Verified unrelated — `learn` is a cat on 0 records and `station` a sub
  on 0 records in both provinces. Left for its own sitting.
