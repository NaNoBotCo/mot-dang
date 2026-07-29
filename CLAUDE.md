# Mot Dang (มดแดง) — working notes for Claude

Thai-first CM+CR directory. Stdlib Python only. `importers/import_all.py` then
`build.py` → `docs/` (GitHub Pages). Full spec + roadmap in README.md.

Pipeline order: `importers/import_all.py` → `make_og_cards.py` (optional, needs
Chrome + Pillow, writes `assets/og/`) → `build.py` → push →
`importers/ping_indexnow.py`.

Rules that bite:
- Empty categories are hidden by design — don't "fix" that.
- `data/curated/` is field truth: never let an importer or crawl overwrite it.
- No external requests, fonts, or scripts in published pages; OSM attribution stays.
- Before committing docs/: `grep -rl "/Users/" docs/` must be empty.
- Banned words in copy and code comments: "load-bearing", "honest" (user rule).
- Wording stays auspicious — no ominous names/labels in nav or titles.
- Ant rank is 0–9, one per field present (`ANT_FIELDS` in build.py). Never weight
  it, never let an advertiser move it — the whole point is that it is readable
  off the page. The freshness ant needs a human touch, not a bulk crawl.
- `wat.svg` stands in only for `wat`/`sights`; everything else gets `ant.svg`.
- `data/curated/honours.json` — royal temple grades and food marks. Nothing goes
  in `royal`/`food` without a fetched source URL; leads live in `unverified` and
  are never rendered. Every food mark carries `edition` and the badge prints the
  year, because those lists change annually.
- data/line.json holds the LINE OA id; empty means the LINE blocks stay hidden.
- Public pushes only as NaNoBotCo, and only when the user says publish.
- Network crawls (Overpass etc.) need the user's go-ahead first.
