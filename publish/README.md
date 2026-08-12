# Publishing

The site is served out of an **R2 bucket by a Worker** (`worker.js`). GitHub is
not in the publish path at all, and neither is Cloudflare Pages.

## Why it changed

Pages pulled from the GitHub repo. When the GitHub account was suspended that
pipeline stopped — and because Pages keeps serving its last good build, nothing
appeared broken. The site just quietly stopped accepting new work, so pushes
that felt like shipping were shipping nothing.

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

## Still worth doing

`docs/` is committed, which is why `.git` is 2.8 GB and why every rebuild is a
27,000-file commit. Now that publishing no longer reads from git, the build
output does not need to be in it:

```bash
git rm -r --cached docs
echo "docs/" >> .gitignore
```

Left undone deliberately — it is a large history-affecting commit and the
GitHub account is suspended, so it should land when pushing is possible again.
Note it stops the growth but does not reclaim the 2.8 GB; that needs a history
rewrite, which is a separate and riskier job.

## Local test, no account needed

```bash
cd publish
npx wrangler r2 object put mot-dang-site/index.html --file=../docs/index.html --local
npx wrangler dev --local
```

`--local` gives a simulated R2 on disk. Worth exercising after any routing
change: `/`, `/toilets.html`, `/toilets`, `/cm/food/`, a missing path, a
`Range` request against the tile archive, and an `If-None-Match` revalidation.
