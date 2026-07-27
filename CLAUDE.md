# Mot Dang (มดแดง) — working notes for Claude

Thai-first CM+CR directory. Stdlib Python only. `importers/import_all.py` then
`build.py` → `docs/` (GitHub Pages). Full spec + roadmap in README.md.

Rules that bite:
- Empty categories are hidden by design — don't "fix" that.
- `data/curated/` is field truth: never let an importer or crawl overwrite it.
- No external requests, fonts, or scripts in published pages; OSM attribution stays.
- Before committing docs/: `grep -rl "/Users/" docs/` must be empty.
- Banned words in copy and code comments: "load-bearing", "honest" (user rule).
- Wording stays auspicious — no ominous names/labels in nav or titles.
- Public pushes only as NaNoBotCo, and only when the user says publish.
- Network crawls (Overpass etc.) need the user's go-ahead first.
