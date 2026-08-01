# Push queue

What is waiting to go out, and what shipped last time.

## Waiting

Nothing. The working tree is clean and `main` matches `origin/main`.

## Last push — 2026-08-01, `240a67766`, 11,793 pages

Two days of work had been sitting local: `origin/main` was last updated
2026-07-30 20:57, three commits behind with roughly twenty thousand
uncommitted files on top. Six commits went out.

| Commit | What |
|---|---|
| `1b5e0f269` | ถนน/ซอย page tier — 891 roads, 354 sois, method and accuracy published |
| `e30a336f4` | Route planner — walking and riding as two networks |
| `ad3ea0961` | Facets — closed 13-word vocabulary, mirrored in the worker |
| `8cfd60ce1` | `addr:*` wired through (48 → 1,333 addresses); three shelves that read zero |
| `7899d4812` | Privacy notice, the birth chart, and the publish gate |
| `240a67766` | The rebuild |

Verified live: `/chart.html`, `/privacy.html`, `/chart.js`, `/bazi.js`,
`/data/solar_terms.json`, `/soi.html` all 200; the new nav on all 11,793
pages. IndexNow accepted 4,276 sitemap URLs — the first attempt returned 403
and the retry went through, so a single 403 there means try again before
believing the key is wrong.

## Before the next push

```bash
ps -eo pid,etime,command | grep "[b]uild.py"     # must return nothing
python3 build.py
python3 tests/test_publish_gate.py
python3 tests/test_facets.py && python3 tests/test_routing.py && python3 tests/test_moat_geometry.py && python3 tests/test_bazi_parity.py
git log origin/main..HEAD --format='%an <%ae>' | sort -u   # NaNoBotCo only
```

After pushing, `python3 importers/ping_indexnow.py`. A ten-thousand-file push
takes 2–3 minutes before new URLs stop 404-ing — use an `until` loop, not
chained sleeps.

Three things that cost time last round, all now rules in `CLAUDE.md`:

- **Two builds at once leave you with a mixed site.** About 1,400 pages kept an
  older nav and it was invisible by eye. Count a nav link against the page
  total.
- **A stale `.git/HEAD.lock`** can be a day old with no git process behind it.
  Check its age and `ps` before believing "another git process is running".
- **zsh eats backticks in `git commit -m`.** Multi-paragraph messages go
  through `git commit -F <file>`.

---

## Backlog

Ordered by what is closest to done.

1. **The mailing list.** The chart and the privacy notice have shipped, so the
   blocker is gone; what is left is the collecting half, and it needs
   infrastructure under your Cloudflare account. To build: a Worker endpoint on
   a **new** KV namespace (`mot-dang-claims` exposes a public `GET /claims`, so
   contact and birth data cannot live there), the two-store split (list =
   contact + consent record + unsubscribe token, no birth data; demographics =
   coarsened birth year+month, province, day-of-week, animal, sign, with no
   contact and no join key), a CSV export behind a shared secret, and
   unsubscribe. Then set `listEndpoint` in `data/config.json` and the form on
   `/chart.html` appears by itself. Sending marketing stays out of scope —
   collect consent, send later.
2. **Photos for the 479 wats that have coordinates and none.**
   `harvest_commons.py` is built and correct — it wants running against that
   set rather than arbitrary records.
3. **The four unfound พระประจำวันเกิด postures** — ถวายเนตร, ห้ามญาติ, อุ้มบาตร,
   รำพึง. Walk `Category:Buddha statues in Thailand` subcategories; a text
   search returns books that *mention* a posture, not images that depict it.
4. **Events, phase (b)** — the routine crawl for one-off dated events. Sources
   surveyed in `importers/EVENT_SOURCES.md`; the page says plainly it is not
   built rather than implying completeness.
5. **Rich alt text**, and highlighting external links worth following.
6. **A fix in `taoist-oracle`, not here:** `year_pillar` decides the 立春
   boundary by civil day while `month_pillar` decides it by solar instant, so
   they disagree for anyone born on 立春 day before the exact moment.
   `bazi.js` deliberately reproduces the civil-day rule to keep parity
   meaningful — fix upstream first, then regenerate.

### One open question, unanswered since 2026-07-29

`data/sources.json` publicly documents the Major Cineplex showtime endpoint,
including the trailing-slash trick that makes it answer. It can be trimmed to
"verified, see importer" and forced out of history if you would rather that
stayed private. Say the word either way.
