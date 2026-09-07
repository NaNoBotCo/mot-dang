# data/curated/lens — the graded registers, one file each

Drawn by `lens_layer.py` (one renderer, many lenses); `build.py` loops over
every `*.json` here, writes `/<key>.html`, adds a row to the care shelf and
takes index keywords from `rows[]`. `importers/sync_lens.py` copies each
lens's `panel` into `data/curated/search_panels.json` and its `thesaurus`
groups into search-core's hand file. `importers/audit_lens.py` exits 1 on a
register that would print a wrong page.

THE RULE (care · trans-health · adhd · longcare · ot, unchanged): the grade
rides every row and is the point.

- `stated` — the place's OWN words on its own site or poster: sentence, url, date.
- `listed` — a dated third-party directory row (cmhy.city) that names the
  service. Not the place's words; printed as exactly that much.
- `route` — the door this care ordinarily runs through, whose own page was
  read and does NOT say the word. Ring first.

No price the page did not read. A licence is a register row, not a rating.
Absent is silence, not a 'no'. A page is a record, not a pamphlet.

Fields: `key` `glyph` `nav [th,en]` `title [th,en]` `h1 [th,en]` `desc [th,en]`
`intro [th,en]` `sections [[key,th,en]…]` `for {key:[th,en]}`
`census [[th,en,regex]…]` (counted live over crawled names)
`rows [{key,section,for[],grade,name_th,name_en,placeIds[],site,phone,hours,note_th,note_en,evidence,src,fetched}]`
`registers [{key,th,en,url,note_th,note_en,fetched}]` `glossary [[th,rtgs,en]…]`
`unread [{name,ref,reason}]` `links [[href,th,en]…]`
`index {base, for:{key:words}}` `panel {…}` `thesaurus [[…]…]` `draft` (renders nowhere).
