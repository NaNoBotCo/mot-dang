# WO-37 — learn/ → sport/: the slug that said classes over a shelf of gyms · 2026-08-26

*Item 3 of Nan's "one at a time" navigation survey ("start what's next.
slugs?"). Zero network.*

## What was measured

The `learn` category holds **105 cm records — 104 of them sub=gym** (cr: 16),
labeled "กีฬา-ฟิตเนส · Sport & Fitness", with one child ("Muay Thai & Gyms").
It began as a classes shelf and drifted: cooking classes and schools grew
their own categories and left the gyms behind, while the slug never moved.
Two smaller lies rode along with it: the schema.org type said
`EducationalOrganization` (a gym is not one) and the shelf icon was a book.

## What was done — a real rename, not a label patch

- **`data/categories.json`**: key `learn` → `sport`; the Thai and English
  labels were already right and did not move.
- **Records**: 105 cm + 16 cr + 1 curated addition re-shelved by JSON
  transform (`cat` arrays only — a blind sed would have eaten
  "Baan Norn P**learn**", which is why it wasn't one).
- **Importers**: `import_overpass.py` classify (×2), `enrich_wikipedia.py`,
  `geocode_local.py` containers (×2), `audit_shelves.py` — so the next crawl
  re-derives `sport`, not `learn`.
- **`build.py`**: schema.org type → `SportsActivityLocation`; new `i-fit`
  dumbbell sprite replaces the book on this shelf.
- **`make_og_cards.py`**: 📚 → 🏋️; shelf cards regenerated.
- **Search**: `search_shelves.json` word→shelf routes updated (ยิม, ฟิตเนส,
  muay, language, …). The thesaurus keeps the *word* "learn" — people search
  words, not slugs.
- **`publish/worker.js`**: `/cm/learn/*` and `/cr/learn/*` → **301** to the
  same path under `sport/`. First redirect rule the worker has ever carried;
  a rename must never eat a bookmark or a search result, and 301 tells
  crawlers to move their index.

## Stakes

The chore was ~10 files and a redirect. The worst case of leaving it: every
future feature keyed on the category (tags, search panels, asked cards)
inherits a slug that lies, and the eventual rename costs more each month —
this was the cheapest day it would ever be.

## Left as history, on purpose

`data/curated/shelves.json` keeps the note "was gym/learn" — provenance of a
past correction, true when written.
