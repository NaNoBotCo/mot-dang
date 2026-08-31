# สบายรอบสอง — what is still in the reader's way · 2026-08-30

*Nan, after WO-42 shipped: "what else can be done to increase sabai and
usability?" — then, on the ordered list below, "start with the search guard."
**§1 BUILT (WO-43) and §2 BUILT (WO-44); §3–§5 remain a survey, not a build.** Every number below was
read off the built `docs/` of 2026-08-29 (22,175 pages) or the canonical
data. Nothing here is done.*

The WO-42 finding was that the site had no sign on the wall. These are the
next ones, and the first is the biggest single number on this page.

---

## 1. Search downloads 6.2 MB it does not use — and the new teaching waits behind it

`md.js` reads the query, then calls `await loadIndex()` **before it checks
whether there is one**. A reader who opens `search.html` with no query pays:

| file | size |
|---|---|
| `data/index.json` | **6,158 KB** |
| `data/search_segdict.txt` | 306 KB |
| `md.js` | 181 KB |
| `data/search_thesaurus.json` | 122 KB |
| `data/search_panels.json` | 40 KB |
| `data/search_shelves.json` | 30 KB |
| **total before anything paints** | **6,840 KB ≈ 36 s on a 1.5 Mbps link** |

The index is the one file that empty page has no use for. Worse, **the WO-42
start state — the pills that teach — renders only after all of it**, because
it sits inside the same `await`. The teaching I just built arrives thirty-six
seconds late on exactly the connections it was built for.

**The fix is a guard, not a rewrite.** If there is no query: render `start()`
from the panel file alone and return. 6,840 KB → **~250 KB, a 27× cut**, and
the pills paint at once. The index is still fetched the moment a query exists,
which is the only time it answers anything.

**And while that branch is open:** bake the same start state into
`search.html` at build time. Today that page's body is **27 characters** before
JavaScript runs — a heading and an empty `<ul>`. The no-JS reader gets nothing,
and so does every crawler and model, whose stated pain in `notes/empathy-map.md`
is client-rendered pages. Server-rendered, the doors exist for everyone and
md.js replaces them when the index lands. Two pages on the whole site carry a
`<noscript>` today.

### BUILT 2026-08-30 — WO-43, on Nan's "start with the search guard"

Both halves shipped, zero network:

**The guard.** `if(!q)return;` sits immediately after md.js reads the query,
before `loadIndex()`. Verified in the browser: opening `search.html` with no
query now fetches **no `index.json`, no thesaurus, no segdict, no panel file** —
`6,840 KB → 0 KB of search data`. With a query, nothing changed: `?q=ช้าง`
still fetches the index, still opens the elephant panel with its live count of
30, still lists 221 rows.

**The served doors.** `search_start_html()` in build.py renders the start state
at build time into `<ul id="results">`. `search.html`'s body went from **27
characters to 1,312**, carrying all 19 pills, and the page is 28 KB. It works
with scripts off, and every crawler and model now sees that the site has doors.
Two improvements fell out of moving it server-side: the bilingual pairs go
through `bi()`, so **the language toggle reaches the start state** (the JS
version emitted plain "th · en" text it could not touch), and the terms are
URL-encoded by Python rather than by hand.

The client-side `start()` is deleted rather than left as a second copy — the
served page is now the only definition, so the two cannot drift.

`tests/test_sabai.py` grew to **27 checks** and its teacher section now asks
the stronger question: not "can the script draw the doors" but "are the doors
in the page before any script runs". It also holds the guard itself
(`if(!q)return;` ahead of `loadIndex()`) and asserts the dead client-side copy
stays gone. All eleven suites re-run green; build 22,175 pp.

---

## 2. Two of the site's inks fail contrast — on exactly the small text

Measured against the paper (`#faf5ea`). 4.5:1 is the floor for body text.

| token | hex | ratio | used in | verdict |
|---|---|---|---|---|
| `--mute` | `#a08b6c` | **3.0:1** | 65 CSS rules | fails |
| `--gloss` | `#8a755b` | **4.0:1** | 28 CSS rules | fails |
| `--ink-soft` | `#544636` | 8.4:1 | — | fine |
| `--ant-dark` | `#8f2a21` | 7.7:1 | — | fine |

These are not decorative uses. `--mute` sets `.tinynote`, `.src`, `.cat`,
`.teaser`, `.eg`, `.photodesc`, `.adlabel` — the provenance lines, the source
credits, the captions. **The site's whole trust argument is written in its
least readable ink**, at its smallest size. `--gloss` sets `.herosub`, the
homepage's opening paragraph.

Same hue, darkened only until they pass — nothing else about the palette moves:

- `--mute` `#a08b6c` → **`#816e53`** (4.5:1)
- `--gloss` `#8a755b` → **`#816d55`** (4.5:1)

Two tokens. It lifts every page at once.

### BUILT 2026-08-30 — WO-44, on Nan's "ok sounds good"

Two token values, and a gate so they cannot drift back.

**What shipped.** `--mute` `#a08b6c` → **`#7d6b51`**, `--gloss` `#8a755b` →
**`#685845`**. Both are the same hue, darkened only; between them they carry
91 rules and **every single one is a `color:`** — no border, no background, no
shadow — so nothing structural moved, only readability.

**Why not the values in §2 above.** Those were computed against the paper
alone. Checking properly, muted text also sits on `--card` and on the
`--card-alt` the chips and bands use, and `#816e53` fell to **4.3:1** there —
still under the floor. The shipped values clear 4.5:1 on **all three** light
surfaces (mute 4.7 / 5.0 / 4.5; gloss 6.3 / 6.7 / 6.0).

**Why the two are not the same colour.** Pushing both to the floor collapses
them into near-identical values and spends a level of the palette to buy
contrast. `--gloss` was darkened proportionally instead, so the ladder keeps
four distinguishable steps, quietest last:

| ink | hex | on the paper |
|---|---|---|
| `--ink` | `#2a1e16` | 14.9:1 |
| `--ink-soft` | `#544636` | 8.4:1 |
| `--gloss` | `#685845` | 6.3:1 |
| `--mute` | `#7d6b51` | 4.7:1 |

A `--soft`-floor variant was computed and rejected: it would have put
`--gloss` at 8.0:1 against `--ink-soft`'s 8.4 — the same colour, in effect.

**The one thing still short, written down rather than left to be
rediscovered.** `--mute` on a `--soft` (`#e3d5bc`) background is **3.5:1**, and
a few bands do put muted text there (`.myhint`, `.mtband`, `.planhero .hnum`,
`.festwhen`, `.widgetbox .wtitle`). `--soft` is 49 borders to 24 backgrounds,
so **the fix belongs to those five bands, not to the token** — either give
their inner text `--ink-soft`, or lighten the background for the background
uses only. Not done; `tests/test_contrast.py` asserts the exemption so it
stays visible.

**`tests/test_contrast.py`** — 26 checks that read the tokens **out of the
shipped stylesheet** rather than from numbers copied into the test: the 4.5
floor for all four inks across all three light surfaces, the ladder's order
*and* that no two neighbours collapse (>1.15× apart), the written-down
`--soft` exemption, and that both quiet inks remain `color:`-only so a future
edit cannot quietly make one a border. Twelve suites green; build 22,175 pp.

**And the gold, on Nan's "do the gold-ink fix too".** `--gold` `#c08a2d` was
doing two jobs at once. As decoration — the ‧ bead after a band label, the
underline on a hovered header link, the watermark on the dark side card — 2.8:1
is fine, because nothing there is read. As **text** it was the hero's "Kept up
daily…" hello line at **2.79:1** and the counts on the nine doors and the care
shelf at **2.99:1**, all of it around 13 px. Measured in the live DOM, not
inferred from the stylesheet — which mattered, because `.heroeyebrow` inherits
its colour from a rule 230 lines away from the one that sets its size, and the
first reading of the CSS attributed it to the wrong place.

**`--gold-ink` `#8e6621`** — the same **38° hue**, carried down to 4.5:1 on
card-alt, 4.7 on the paper, 5.1 on the card. Three rules swapped
(`.heroeyebrow`, `.doorcard .n`, `.careshelf .n`); `--gold` keeps the bead, the
underline and the watermark and stays exactly the colour it was. Verified live:
hero eyebrow **2.79 → 4.74**, both counts **2.99 → 5.07**, bead still
`#c08a2d`. It still reads as gold — a warm amber, distinct from both the ant
red beside it and the ink-soft grey under it.

The gate grew a rule for the split: `--gold-ink` must clear the floor on every
light surface, must keep gold's hue (within 2°), and **`--gold` may stay under
the floor only where nothing is read** — an allow-list of exactly two selectors,
the bead and the watermark. That check caught its own first draft, which read
`text-decoration-color:var(--gold)` as a text colour; the regex now refuses a
`-color:` property, and the underline is correctly left alone as decoration.

---

## 3. Heavy pages a reader reaches with no warning

WO-35/36 built the right mechanism — a shelf past the bar becomes a hub, and
its complete roll sits behind a door **with its MB printed on it**. Two kinds
of page fall outside it:

- **wat**, held back by the 90 %-coverage gate: `cm/wat/index.html` is
  **1,365 KB, 1,511 places**; `cr/wat/index.html` 1,173 KB. On a directory for
  this city, the wat shelf is not an edge case.
- **tags**, which never had a hub rule at all: `cm/tag/old-city.html`
  **1,441 KB, 1,327 places**; `cm/tag/wifi.html` 1,172 KB;
  `cm/tag/maha-nikaya.html` 1,153 KB.

**32 pages exceed 600 KB.** Compare `cm/hotel/index.html`, which flipped to a
hub and is now 117 KB. Cheapest honest fix first: print the weight on the door
wherever it is over ~500 KB, the way `all.html` already does — a reader on a
hilltop deserves the same warning whether the page is called `all.html` or
`wat/index.html`. The hub treatment for tags is the larger, later move.

## 4. The site's own job is unmet on ~86 % of pages

| | Chiang Mai (14,493) | Chiang Rai (6,209) |
|---|---|---|
| phone | 2,122 (**14 %**) | 1,033 (**16 %**) |
| opening hours | 2,120 (14 %) | 382 (6 %) |
| website | 936 (6 %) | 226 (3 %) |
| **LINE** | **0** | **0** |

`notes/empathy-map.md` says the product is "the phone ringing directly — his
own number on the page, nobody in between." On six pages in seven there is no
number to ring. **And LINE — how this country actually contacts a shop, and
persona 1's entire working day — stands at zero across 20,702 records**, while
the header has carried a `เติมเบอร์-ไลน์ · Add contacts` door all along.

The interface half of this is already right: a page with no number says
*ช่วยเติมให้ครบได้ฟรี · help fill in the rest, free* and links `claim.html`
with the record's id prefilled. So this is not a UI defect — it is the supply
problem the UI was built to solve, and no amount of navigation work moves it.
It belongs on this list because **it is the ceiling every other improvement
runs into**, and because the QR handouts already exist to attack it.

## 5. Three broken links in 39,120

Link integrity is otherwise excellent — 328 pages scanned, every real `href`
resolved. The three:

1. `reader/adhd-words.pdf` ← `adhd.html`, which offers *"ดาวน์โหลดแผ่นคำที่ใช้
   ที่เคาน์เตอร์ (PDF) · Download the desk sheet"*. `reader/` holds
   `care-words.pdf` and `hair-words.pdf`; the ADHD sheet was never generated
   (`make_reader_sheets.py` is in the repo). The reader most helped by printed
   words to hand across a counter is the one who gets a 404.
2. `wats.html` ← `fixed.html` — a stale link inside the fix log.
3. `cm/medical/physio/index.html` ← `longcare.html` — a curated door pointing
   at a shelf the empty-categories rule correctly hides. The rule is right; the
   door should know about it.

## Measured and found healthy — no work needed

- **Tap targets**: `.chip` carries `min-height` 42–52 px everywhere.
- **The skiplink**: present and first, ahead of the 35 links that precede
  `#content` on every page. WO-34's banding plus this is enough.
- **Images**: 128/153 sampled carry `width`+`height`; no meaningful shift.
- **The `learn/` slug-label mismatch** (2026-08-26 survey item 3) is already
  resolved — the directory is `sport/` and nothing links the old slug.

## The order I would take them

1. **The search guard** (§1) — biggest number, smallest diff, and it is what
   makes WO-42's teaching actually arrive. Same sitting: server-render the
   start state so no-JS readers and models get it too.
2. **The two ink tokens** (§2) — two values, whole site, and the readability
   of every provenance line the site's honesty rests on.
3. **The weight on the door** (§3) — one rule, applied where the hub rule
   cannot reach.
4. **The three links + the missing ADHD sheet** (§5) — an afternoon.
5. **LINE and phone coverage** (§4) — not a build; a campaign, and Nan's call
   on how to run it.

Open from before and untouched: the three WO-34 header trims, the root → `/cm/`
re-root before Chiang Rai, and the WO-42 held items (chipbar chip, hero wording,
pill set, primary-shelf rule for the crumb, the two questions to the commenters).
