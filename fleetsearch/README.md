# fleetsearch — one box over every site on the roster

`motdang.net/find` · `motdang.net/find?adv=1` · the header box on every page
(`/search.html?q=`) · `?fmt=json` for machines.

Every page of every site in `index/data/fleet.json` that has a build on this
disk, in one FTS5 index on D1, answered by the site Worker as plain HTML.

| piece | what |
|---|---|
| `crawl.py` | reads each site's build (`docs/`) → `cache/fleetsearch/pages.jsonl`; title, abstract, date, size, the page's own coordinate, tokenised text |
| `thumbs.py` | the picture beside each row: the page's own photo, else a map cell with its pin → `cache/fleetsearch/thumbs/`, copied to R2 under `tiles/find/` |
| `load.py` | pages.jsonl + thumbs.json → SQL chunks → the local twin (`fleet.sqlite`) and D1 (`motdang-search`) |
| `preview.js` | the real handler over the twin on localhost, thumbnails included (`node fleetsearch/preview.js`) |
| `../publish/fleetsearch.js` | the query language → FTS5 MATCH; the page; `/find` |
| `../publish/worker.js` | routes `/find`, `/search`, and `/search.html` when the query carries only fleet parameters |
| `../tests/test_fleetsearch.js` | the query language and the SQL it becomes, 39 cases |
| `../tests/test_fleetsearch_page.js` | the handler end to end over the twin, with the real dictionary, 35 cases |
| `../tests/test_fleetsearch.py` | the crawler, the wiring, every planned MATCH string run in SQLite, 25 cases |
| `../publish/ownfind.js` | people's own pages on the first page of an answer: asks the page maker, 400 ms at most, joins what the index lacks |
| `../tests/test_ownfind.js` | that module alone, and the handler over the twin with the page maker replaced by a function |
| `../tests/test_own_pages.py` | the feed, the match to a place record, the crawler's rows, the place-page layer |
| `../tests/test_geofence.js` | what a page says about where you are: the arithmetic, the compass, the rounding, 12 cases |

## The pin backfill is unfinished

2026-09-21: `keys.lat` / `keys.lon` are on the live table and **3,705 rows of an
intended 76,847 carry a coordinate**. The rest are waiting on Cloudflare: the
D1 import endpoint answered `502 Bad Gateway` and then locked the database —
`internal error [code: 7500]` to every query, `SELECT 1` included — and
motdang.net/find was down for 25 minutes before the half-built copy was
dropped. A 20 MB chunk that had taken 17 seconds was still running after ten
minutes.

Distance works for the rows that have one and is simply absent for the others,
which is the same rule the rest of the search holds to: unmeasured is not far.

To finish, when the platform is well:

```
python3 fleetsearch/load.py --remote --from 1     # 22 chunks, ~10 min
```

It will take the search down in bursts while it runs, because D1 locks the
database for each import. Run it at a quiet hour.

## Reload

```
python3 fleetsearch/crawl.py            # ~2½ min for 105k pages on 6 cores
python3 fleetsearch/thumbs.py --upload  # only what is new; the first run draws ~11,000 map cells
python3 fleetsearch/load.py             # SQL + twin (~1 min) + D1 (~10 min)
```

Run the crawl after a finished build: it reads each place's `.json` twin and
`docs/data/toilets.json`, both of which a build in flight has not written yet.

D1 takes the chunks through wrangler's import path, and **the database does not
answer queries while a chunk is importing** — wrangler says so on every chunk.
Every insert is `OR REPLACE`, because a chunk that half-applies and is retried
otherwise dies on its own primary key; the row counts of `pages`, `keys` and
`fts` are all checked against the crawl before anything is swapped in.
A full reload therefore costs a few minutes of `/find` answering 500s. Until a
delta loader exists (upsert changed pages through the query API), reload at a
quiet hour or accept the gap.

The standing walk (`importers/standing_walk.sh`) runs these three after each
publish it makes, unless a build is running, resumes a stopped D1 load once
from the chunk it names, and writes a row to `~/.claude/state/search-reload.tsv`.
The nightly task stands down when that file shows a reload in the last 20 hours.

## What goes in

- **Sites**: every roster site in `index/data/fleet.json` with a build on this
  disk — the repo named in `repo`, its `docs/`, `dist/`, `site/`, `public/` or
  root. A site served inside another site's build (motdang.net/muay-thai/ is
  `mot-dang/docs/muay-thai`) is read from that folder, once, under its own id.
  `crawl.py`'s `SITES` holds the builds a repo name does not lead to. The crawl
  prints the roster sites with no build.
- **Pages other Workers render** (the Anthill, the home-help board):
  `extra_pages.json`. An entry with `"fetch": true` is read over HTTP at crawl
  time; its listed text stands in when it does not answer. `"brand"` names a
  section whose name its subpages carry.
- **People's own pages** (sites.motdang.net, made with the page maker):
  `crawl.py` reads the public feed `https://sites.motdang.net/feed.json` into
  rows under the site id `sites` (title, tagline, about, address, every menu
  item with its price, the kind in Thai and English, the pin, the cover as the
  picture, hours as a lamp, an event date). A feed that does not answer falls
  back to the last good copy, `cache/fleetsearch/own_pages_feed.json`.
  `/find` also asks `https://sites.motdang.net/api/find?q=&lat=&lng=` on page
  one of a best-match or nearest answer, beside the index query, for at most
  400 ms; what it returns and the index lacks joins after the first two rows
  with an "own page" mark, and any fault leaves the answer as it was
  (`OWN_FIND_URL=""` in the Worker's vars switches the call off).
  `importers/own_pages.py` reads the same feed for the place records.
- **Left out**: redirect stubs (`http-equiv=refresh`), pages with `noindex`
  in any robots meta except a Mot Dang place page (its place's one page), and
  a copy of a page that claims another's canonical under the same name. A page
  of its own that claims its list's canonical (each Ghost stop) keeps its own
  address.
- **Taken out of each page before a word is read** (`deboil.CHROME_CLASSES`):
  share, sponsor and advertise boxes, the Grab button, add-to-plan, nearest
  toilet, around here, the anthill link, the emergency strip, the Mot Dang
  net. The site's name leaves the end of the title the index matches on
  (`deboil.brand_suffix`); the title a reader sees keeps it. Measured on the
  twin 2026-10-03, before → after: รังมด 75,871 → 2, grab 68,474 → 41,
  garden restaurant 14,745 → 657, anthill 21 → 5, mot dang 86,571 → 718.

## Filtering and sorting

Both doors carry the same controls, and on the results page they are a bar of
links with the count each one leads to:

| control | values |
|---|---|
| เรียง · Sort | best match · newest · oldest · A–Z · nearest · most detail · soonest event |
| ประเภท · Type | places · lists · other pages |
| มี · Has | photo · contact · toilet · events · hours · open now |
| หมวด · Section | the breadcrumb's first two steps, counted |
| คำอยู่ที่ · Words in | anywhere · the title · the address |
| ปรับปรุง · Updated | any time · 7 days · 30 days · a year |
| ไซต์ · Site | every site, counted on this answer |

Parameters: `sort=new|old|az|near` · `in=title|url` · `since=7d|30d|1y` (or
`from=` and `to=` on the boolean form) · `site=` · `n=10|20|50` · `near=lat,lng`. Every link and both
boxes carry the lot, so a filter never drops the query and a results address is
a bookmark. Changing a filter returns to page one.

Three rules the page holds to:

- **A count is the count you get.** The site counts are taken with every other
  filter applied; the date counts with the site filter applied. A bucket that
  holds the whole answer narrows nothing and is not offered — most of Mot Dang
  carries the date of the nightly build.
- **A sort other than relevance orders the window the reader can reach** — the
  best 1,000 matches, which is also as deep as the pager goes — and the page
  says so whenever the answer is larger than that.
- **The words-in filter stands down** when the query already names a column
  (`title:` or `url:`), because FTS5 lets the outer filter win and a `url:`
  term inside a title-only search would quietly match nothing.

## What a row holds

Above the title, the site and the page's own breadcrumb (its BreadcrumbList,
without the front page and without itself; Mot Dang's Thai shelf names get
their English from `data/categories.json`). Beside it, a 72 px picture: the
page's own photo when it has one — a share card, logo or drawing does not
count — else a 1.2 km piece of Mot Dang's basemap with the pin drawn in CSS.
Under the abstract, one line of what the listing holds:

| part | from |
|---|---|
| ☎️ 💬 🌐 ways to reach it, counted | the place's `.json` twin (`channels`), or schema.org telephone / email / sameAs |
| 🚻 a toilet | the toilet minisite: a report or recorded facet, Nan's word (`data/toilets.json` `stated`), the tier's habit — else the nearest one within 400 m of an exact pin. Links to `/toilets.html` |
| 🎪 events to come | the place page's "what is on here" calendar entries, or schema.org Event; weekly ones roll forward |
| 🟢 open now · 🕘 hours listed | the week schedule from `data/open_lamps.json` via the twin; closed is not said |
| 📶🅿️… recorded facts | the twin's `facets`, with `data/facets.json` icons |

Filters and sorts that come with it: `kind=place|list|page` (Type),
`has=photo,contact,toilet,events,hours,open` (switches that add up), `sec=`
(Section: the first two breadcrumb steps), `sort=rich` (most detail) and
`sort=soon` (soonest event, offered when the answer holds one). The facet
counts all come from one grouped query per answer.

## Where you are

73% of the corpus carries its own coordinate — the crawler reads the page's
`geo.position` meta or the single GeoCoordinates in its JSON-LD, and a page
publishing more than one distinct coordinate is a directory, so it gets none.
Those pins sit in `keys`, and `sort=near` orders by squared distance with
longitude scaled by cos(latitude), so a place due east is not ranked nearer
than one the same distance north. A page with no pin is unmeasured, not far:
it sorts last and is never dropped.

The position comes from Cloudflare's guess at the request unless `near=lat,lng`
says otherwise. **The guess is a city, not a person** — measured 2026-09-21, it
placed a connection 6 km from the house it was sent from — so a distance drawn
from it is rounded to "nearby" under 1.5 km and to whole kilometres above, and
the page says whose guess it is. A tap on the position button asks the browser
for a real fix and reloads with `near=`; that tap is the one script the results
page carries, and it is written only when a distance is on offer.

`publish/worker.js` draws the same distinction on every page of the site: it
fills `meta[name=md-where]` with `city|lat|lon|tz|country`, and on a page that
publishes its own coordinate it writes a line under the heading saying how far
away it is and which way. One streaming pass, no second fetch, no rebuild — the
JSON-LD is in the head and every heading comes after it. A page carrying a
reader's city is marked `private` so no shared cache may hold it.

`keys` is why this is fast: a narrow twin of `pages` (id, site, host, lastmod,
title) that the sorts and facets join instead of the fat rows. A covering index
on `pages` did not do it — for a rowid table SQLite prefers the primary key and
reads the whole row anyway, and the broadest sorted query took nine seconds.

## The query language

Simple box: words are ANDed; `+word` must appear; `-word` must not; `"a
phrase"` is exact; `word*` is a prefix; `title:` `url:` `site:` narrow. When
every word finds nothing the page tries the words split apart (a Thai
compound), then any word, then synonyms from the fleet thesaurus — and says
which step answered. `lucky=1` goes to the first page found.

Boolean box (`adv=1`, or upper-case operators in the simple box): `AND OR NOT
NEAR ( ) "…" *` with FTS5's own precedence — NOT, then AND, then OR — plus a
site select and a date range.

Thai runs are split with `docs/data/search_segdict.txt` on both sides — the
indexer in Python, the Worker in JS through `searchcore.js` — and sent as a
phrase. The FTS5 tokenizer is told that Thai vowel and tone marks are letters
(`categories 'L* N* Co Mn Mc'`); without that a bare consonant matches inside
every word that carries a mark.

## Measured

See `notes/altavista-2026-09-21.txt` for the live numbers at first deploy.
