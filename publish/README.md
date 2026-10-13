# Publishing

The site is served out of an **R2 bucket by a Worker** (`worker.js`). GitHub is
not in the publish path at all, and neither is Cloudflare Pages.

## The public API lives in this Worker too

`worker.js` answers `/api/v1/*` in front of the bucket, and `api.js` beside it
holds every rule about what a query means — that split exists so
`tests/test_api_worker.js` can run the whole filter/sort/page path under plain
node against the real index, with no Cloudflare and no network.

There is no database. `api_layer.py` bakes `docs/api/v1/index.json` at build
time; the Worker parses it once per isolate and answers from memory. So the API
ships with a **content deploy**, not a Worker deploy — the Worker only needs
redeploying when the routing or the query rules change.

Every response, static file included, now carries `Access-Control-Allow-Origin: *`.
The licence has always said take it; until this the door was locked to anything
running in a browser.

Two tests guard the shape, and both should pass before a deploy:

```bash
python3 tests/test_api.py && node tests/test_api_worker.js
```

`test_api.py` is the key-stability lock: `/api/v1/` keys may be added to, never
removed, renamed or retyped, and it fails if `api_layer.py`, `api.js`,
`schema.json` and `openapi.json` stop agreeing. A breaking change is not
forbidden — it is a `/api/v2/`, and that test is where you find out.

## The fleet search

`/find` (and the header box's `/search.html?q=`) is answered by `fleetsearch.js`
from a D1 database, `motdang-search`, bound as `SEARCH`. The index holds every
page of every site on the roster and is filled by `python3 fleetsearch/load.py`
— a content step, like `deploy.py`. `fleetsearch/README.md` has the query
language, the reload cost and the tests:

```bash
node tests/test_fleetsearch.js && node tests/test_fleetsearch_page.js && python3 tests/test_fleetsearch.py
```

## The edge count

The Worker writes one row per request into Cloudflare Analytics Engine. Nan's
decision, 2026-09-05 (`notes/arrivals-2026-09-05.txt`, A1): count arrivals
first-party — referrer host and landing path, no cookie, no third party,
aggregated.

Read it:

```bash
python3 traffic.py          # last 7 days
python3 traffic.py 30       # last 30
```

`traffic.py` reads back over the Analytics Engine SQL API with the fleet token
in `~/.config/nanobotco/keys.json`, which already carries Account Analytics
Read. Nothing to mint, nothing to paste.

**Why it lives in this Worker instead of traffic-eye.** traffic-eye is the
fleet's collector and it already does exactly this for the other sites, by
sitting in front of them on a route. A Cloudflare hostname belongs to exactly
one Worker, and `motdang.net/*` belongs to this one — so a route there was
never available. The classifier is vendored to `publish/classify.js` instead,
and the rows go to traffic-eye's own `traffic_eye` dataset in its blob order,
so its dashboard reads motdang.net alongside the rest.

That shared dataset is the thing to be careful with: **position is the schema**.
A row written with the blobs in a different order is not an error, it is a
wrong number that looks right. `tests/test_edge_count.mjs` compares the two
files' blob comments and fails when they drift.

**What a row cannot hold.** No IP, no cookie, no identifier of any kind, so two
requests by one reader are two rows that cannot be joined. The referrer is cut
to its host — a full referrer from a search engine carries the words somebody
typed — and the query string is dropped from the path for the same reason. The
test asserts each of those absences by sending the header and checking it does
not appear in the row.

**It cannot break the site.** `serve()` runs first and its response is returned
whatever happens after. The write goes through `waitUntil` inside a try/catch
whose failure path is to do nothing; an unbound binding, an Analytics Engine
outage, or an unfamiliar User-Agent all end with the reader getting the page.

**Categories are claims, not proof.** They come from the User-Agent, which is
self-declared — anything can call itself Googlebot. "human" means a browser's
User-Agent with no bot marker, which is the ceiling of what a count with no
cookie can know.

Deploying the count is a **Worker** deploy, not a content deploy:

```bash
export CLOUDFLARE_API_TOKEN=$(python3 -c "import json,pathlib;print(json.loads((pathlib.Path.home()/'.config/nanobotco/keys.json').read_text())['cloudflare']['api_token'])")
cd publish && npx wrangler deploy
```

**That deploy ends in a red error and has still worked.** The script uploads;
wrangler then reconciles `[[routes]]` against the zone, and the fleet token
carries Workers Scripts write but not Workers Routes write, so that last call
401s. The routes already exist and are untouched — first deploy done this way
(2026-09-08) was live and recording within a minute. The error only blocks
*changing* a route.

## Why it changed

Pages pulled from the GitHub repo, and because Pages keeps serving its last
good build, a pipeline that stops looks exactly like one that is working. The
site accepted no new work while pushes still felt like shipping. R2 removes
that failure mode: the sync either writes the objects or says why not.

Behind that sat a second wall: **Pages caps a project at 20,000 files and
`docs/` is 27,577** (13,514 pages, plus a `.json` sibling for every place, plus
images). Even with GitHub healthy, a full deploy no longer fit.

R2 has no object limit and no third-party git dependency, so both walls go at
once. The 116 MB basemap archive lives in the same bucket, served by the same
code path — which is also what the toilets map has been waiting on.

## One-time setup

```bash
cd publish
npx wrangler r2 bucket create mot-dang-site
npx wrangler deploy
```

Then in the Cloudflare dashboard: **Workers → mot-dang-site → Settings →
Domains**, add `motdang.net` and `www.motdang.net`. The zone is already on
Cloudflare, which is what makes a custom domain possible here.

Credentials for uploading — **never in the repo**. Either export:

```bash
export R2_ACCOUNT_ID=…
export R2_ACCESS_KEY_ID=…        # R2 → Manage API tokens → Object Read & Write
export R2_SECRET_ACCESS_KEY=…
```

or drop them in `~/.mot-dang-r2.json` as `{"accountId":…,"accessKeyId":…,"secretAccessKey":…}`
— the same arrangement as `~/.mot-dang-showtimes.json` and the LINE token.

## Every deploy after that

```bash
python3 build.py
python3 publish/deploy.py            # dry run — prints what would change
python3 publish/deploy.py --yes      # do it
```

Only changed files upload (compared by checksum, because `build.py` rewrites
every file every run so timestamps are useless here). The Worker is untouched
by a content deploy; it only needs redeploying when routing changes.

## Turning the basemap on

```bash
python3 publish/deploy.py --tiles --yes
```

then set `"url": "tiles/cm-cr.pmtiles"` in `data/basemap.json`, rebuild, deploy.
It ships with an empty url so that pages do not each pull a megabyte of
MapLibre only to 404 on tiles that are not hosted yet.

## The guard

`deploy.py` refuses to sync when `docs/` holds fewer than 20,000 files, and
refuses when any output contains a local `/Users/` path.

The first one matters more than it looks. `rclone sync` makes the bucket match
the source, which means it deletes whatever is in the bucket and not in
`docs/` — correct behaviour, and one bad build away from emptying the site,
because `build.py` wipes `docs/` at the start of every run. A build that dies
halfway leaves a real directory holding a handful of files, and syncing that is
indistinguishable from meaning to delete 27,000 pages.

### Announced cuts

A change that retires live files says how many in `publish/expected.json`,
committed with it:

```json
{"announced": [{"id": "tag-geojson-2026-10-11", "until": "2026-10-25",
                "why": "per-tag GeoJSON cut",
                "remove": {"data/c[mr]-tag-*.geojson": 2950},
                "add": {"data/": 2}}]}
```

A pattern is a prefix, or a glob when it holds `*`, `?` or `[`. At publish,
the deletions under each pattern are counted: more than 10% (or 5 files) over
the announced number refuses; fewer is logged and publishes. Deletions no
pattern covers still meet the fixed ceiling (500 on the server walk, 2,000 in
`deploy.py`). `add` is logged, never refused. A cut that landed within its
band is used up (`/srv/state/expected-done.txt` on the server,
`cache/expected-done.txt` here); one past `until` never applies. An
announcement cannot cover `vendor/`, `glyphs/` or `api/`.

### Deferred deletions

When either check refuses, the standing walk still publishes: `deploy.py
--defer-deletions` (or `--no-delete`, when the server walk's own check refused)
uploads new and changed files with `rclone copy` and deletes nothing. The keys
it kept are in `/srv/state/deferred.txt` on the server (`cache/deferred-deletions.txt`
here), the walk ledger gets a `deletions-deferred` line, and STATE.txt says so
until a publish deletes them. A tree that fails the whole-site check, a gate,
or the bucket listing still publishes nothing.

## Pictures: mot-dang-media

`streetphotos/`, `photos/`, `inat/` and `og/` (47,468 files, 5.3 GB on 2026-10-13) are served from the bucket `mot-dang-media` by the Worker in `worker-media/` (routes `motdang.net/{streetphotos,photos,inat,og}/*`, www too). The page URLs are the same. A key the bucket lacks goes on to the site Worker.

With `MD_MEDIA_BUCKET=1` the build copies none of the four into `docs/`; `media_layer.py` writes the list to `cache/media-manifest.txt`, `publish/media_sync.py sync` uploads what the bucket lacks or holds changed (copy only), and `deploy.py` and the deletion preview leave the four prefixes alone. `importers/publish_steps.sh` sets the variable when `media_sync.py probe` can write the bucket, and publishes the old way when it cannot. The copies already in `mot-dang-site` stay.

Off in one command: `cd worker-media && npx wrangler delete motdang-media --force`. This Worker goes, its routes with it, and the site Worker serves the four prefixes from `mot-dang-site` as before.

## Still worth doing

`docs/` is committed, which is why `.git` is 2.8 GB and why every rebuild is a
27,000-file commit. Now that publishing no longer reads from git, the build
output does not need to be in it:

```bash
git rm -r --cached docs
echo "docs/" >> .gitignore
```

Left undone deliberately — it is a large history-affecting commit, so it
wants a quiet moment when no build or publish is in flight.
Note it stops the growth but does not reclaim the 2.8 GB; that needs a history
rewrite, which is a separate and riskier job.

## Local test

```bash
cd publish
npx wrangler r2 object put mot-dang-site/index.html --file=../docs/index.html --local
npx wrangler dev --local
```

`--local` gives a simulated R2 on disk. Worth exercising after any routing
change: `/`, `/toilets.html`, `/toilets`, `/cm/food/`, a missing path, a
`Range` request against the tile archive, and an `If-None-Match` revalidation.
