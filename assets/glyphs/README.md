# glyphs — the label type for the live basemap, self-hosted

MapLibre cannot draw a label without somewhere to fetch the font from, and the
usual answer is Protomaps' public font host. That was the one third-party
request left on this site: a page with a map on it told a server that is not
ours that somebody was looking at a map, on a site whose front page promises it
follows nobody around. Self-hosting the tiles and then renting the lettering
settles nine tenths of the question and leaves the tenth showing.

So the four ranges the labels here actually need are kept in the repo, copied
into `docs/glyphs/` by `build.py`, and served from our own bucket like
everything else.

| range | what it carries |
|---|---|
| `0-255` | Basic Latin + Latin-1 — the `name:en` line, and the digits |
| `256-511` | Latin Extended-A — the diacritics in romanised place names |
| `3584-3839` | **Thai, U+0E00–U+0E7F** — the `name` line, which here is the Thai one |
| `8192-8447` | General punctuation — the dashes and quotes that appear in names |

Source: `https://protomaps.github.io/basemaps-assets/fonts/Noto Sans Regular/`,
fetched 2026-08-20. Noto Sans is licensed **SIL OFL 1.1**, the same licence as
the faces in `assets/fonts/`, and it may be redistributed this way.

**The stack is named `NotoSans`, deliberately without the spaces** the upstream
directory has. MapLibre substitutes `{fontstack}` into the glyph URL verbatim
from the style's `text-font`, so a name with spaces has to survive percent-
encoding through a worker and a bucket to reach a directory that also has
spaces in it. Renaming it costs nothing — the name is only a key that the style
and these directories have to agree on — and removes a whole class of "why are
there no labels" failure. If the stack is ever renamed again, rename the folder
in the same commit.

**Checking a range is real before trusting it:** a 404 and an empty-but-present
range look identical once MapLibre has swallowed the error — the symptom is
labels that never draw and no message anywhere. Ask for the bytes:

```bash
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' https://motdang.net/glyphs/NotoSans/3584-3839.pbf
```

A populated Thai range is about 57 KB. A few hundred bytes means the range is
there but has no Thai in it, which on this site is the same as broken.
