# Event + contact sources — the map, 2026-07-29

Machine-readable version: `data/sources.json` (20 sources). That file is the
one the importer reads; this is the reasoning behind it.

Built by reading one issue of the weekly Chiang Mai events newsletter
(27 July 2026, 33 pages) exhaustively and then fetching everything it points
at. Every status below is what was actually fetched on 2026-07-29, never what
a source claims about itself.

## What this is for

Two outputs, not one, because the sources carry both:

1. **Events** — what is on and when.
2. **Contact leads** — phone / LINE / email / website for a venue. Contact
   coverage sits at 19%, so a source that also states a museum's phone number
   is doing double duty. `data/contact_leads.json` is that stream.

Run: `python3 importers/harvest_events.py` (`--list` to see the registry,
`--refetch` to ignore the cache). Snapshot-first into `cache/events/`, same
shape as `check_links.py`, so `build.py` never makes a network call.

## About the newsletter

The body text is venue-supplied press-release copy the compiler pastes in —
not his own writing. So the thing worth having is not the text: it is the
**distribution list of who sends releases in**, which no crawl reproduces.
Partnership offered 2026-07-28, unanswered as of 2026-07-29. Treat each issue
as a discovery feed for new sources to add to the registry.

Worth copying outright: his four-part split sorts by **decay rate** —
dated events / recurring weekly / notices / promotions. Those want different
refresh cadences, which is why `cadence` is a field in the registry.

## Verified working (7)

| Source | Method | Yield | Cadence |
|---|---|---|---|
| **Payap Lifelong Learning** | JSON REST | 53 events + venue phones | weekly |
| **Meetup** (3 groups) | iCal | 22 events | weekly |
| Chiang Mai Citylife CityNow | HTML | events to Nov 2026 | weekly |
| JOG&JOY running calendar | HTML table | CM races w/ province column | monthly |
| Alliance Française Chiang Mai | HTML | events to Aug 2026 + contacts | monthly |
| Chiang Mai Bridge Club | HTML | near-daily, Mon/Wed/Fri | quarterly |
| Buddha Daily Wisdom (Wat Tung Yu) | HTML | retreats to Jan 2027 + LINE id | monthly |

**Payap is the best source found**, which matters because extension courses
there are popular. `/wp-json/tribe/events/v1/events?per_page=50` — The Events
Calendar plugin API, 53 events over 2 pages, confirmed by direct urllib fetch.
Each event carries title, description, start/end + timezone, cost with
currency, categories, image and url; the nested **venue** object carries
address, city, province, zip, **phone** and **website**, and the **organizer**
object carries **email**. That is where the contact leads come from — real CM
venues with real numbers (Bua Bhat Factory 053 446 291, Chiang Mai National
Museum 053221308, Araksa Tea Garden + araksatea.com). Two fallbacks also
verified: `.ics` at `/events/?ical=1`, and `/feed/` — but note `/feed/` is the
**blog**, write-ups of past activities, not the course calendar. Do not
mistake one for the other.

**Meetup** is `https://www.meetup.com/{group}/events/ical/` — no key, no OAuth,
no JavaScript, weekly recurrences pre-expanded. Two traps worth knowing:

- The group *HTML* pages render client-side and report "0 upcoming events" to
  a plain fetch. The iCal endpoint is the only sane path.
- **The feeds carry no `LOCATION` property at all** — measured, 0 across all
  three Chiang Mai feeds. The venue survives only in prose. The importer
  recovers ~54% from a `**Location:**` line in the description or an `@`/`at`
  tail on the title, and marks each `venue_from: title|description|feed` so an
  inferred venue is never mistaken for a stated one.

Discovery is automatable: `meetup.com/find/?location=th--Chiang-Mai` *is*
server-rendered, so new group slugs can be found and added. Three more are
already visible and not yet harvested: `make-new-friends-in-chiang-mai`,
`creative-writing-meet-up`, `ai-engineers-in-thailand`.

**Correction carried forward:** chiangmaicitylife.com's `/feed/` really is dead
(1 item, 2023-08-10) and category feeds 404 — but the *site* is alive, with
events into November 2026. A previous session concluded "stale, don't bother"
from the feed alone. That was wrong about the site.

## Blocked, walled or unusable (9)

- **chiangmainext.com** — 403. Flagged in the newsletter's Notices as a *new*
  Chiang Mai calendar, so potentially the highest-value lead here.
  **Needs a human look in a real browser.**
- **onenimman.com** — 403 on www, apex and /whats-on. Painful: One Nimman hosts
  the White Market (Thu–Sun) plus six weekly classes.
- **chiangmaipao.go.th** — 403. The assumption that a `.go.th` would be
  crawl-tolerant was wrong.
- **tourismthailand.org** — 403.
- **allticket.com** — HTTP 200 but an empty JS shell; even `/sitemap.xml`
  returns the same header fragment.
- **chiangmaiexpatsclub.com** — Google Sites; nav renders, page bodies do not.
- **luma.com** — client-rendered, no JSON-LD, no feed found.
- **alliance-francaise.or.th** — expired TLS certificate (the CM branch at
  afchiangmai.com is fine and is what the registry points at).
- **pitchero.com/clubs/chiangmaicobras** — reachable and server-rendered but
  last fixture is 2025-11-13, ~8 months stale. Contacts only.
- **Facebook / Instagram / WhatsApp** — login-walled. A large share of events
  exist only here. This is a structural ceiling on coverage, not a bug to fix.
  What *is* extractable without logging in is the page **identity** as a
  contact field and claim target.

## Contact-only, refresh rarely

realspacecm.com (+66 96 717 4878), maawellnessretreat.com
(wa.me/66843615688), chiangmaiholistic.com (LINE @cmholistic, two phones,
email). Plus 7 LINE Official Account handles and 7 `lin.ee` short links
harvested from one issue — @kantarychiangmai, @interconchiangmai,
@137pillarshouse, @cmholistic, @skuggavineyard, @crossriverside,
@anantarachiangmai — which confirms the gemba finding that LINE is the real
Thai-facing channel, and feeds `channels()` where LINE already ranks second
after phone.

## Design consequence

Most recurring events happen at venues **already in the catalogue** — Moment's
Notice, Paapu House, The Moat House, Archers, Game Tree, Free Bird, Rare Finds,
attika Studio, One Nimman, 4Seas Nimman, CFCNX, Bailamos, Jing Jai Market, and
Wat Tung Yu among them. So events should attach to **place ids** as a
"what's on here" band on the place page, rather than living in a separate
listings silo. That gives a venue owner a concrete reason to claim their page —
to keep their own weekly night correct — which is the missing pull identified
in the 2026-07-29 gemba walk.

Venue→place matching is **not built yet**. It is the next step, and the real
blocker is that Meetup venue strings are prose ("CMU", "Spice Garden,
Chiang Mai") that will need fuzzy matching against 10,281 records.
