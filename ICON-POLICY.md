# Icon policy — sprites, not emoji

Client 2026-09-26: "We have proprietary svg icon sprites for all that stuff,
switch from emoji, create a policy, stage cleanup everywhere."

## The rule

No emoji in shipped UI. Every glyph comes from the sprite sheet
`docs/icons.svg` (ids `i-*`). Emoji stay only in prose Nan writes and in
`data/` content she authored.

## How to render one

Same-origin `<use>`, sized in a wrapper, coloured by `currentColor`:

```html
<svg class="rowicon" aria-hidden="true" focusable="false" width="18" height="18"
     viewBox="0 0 24 24"><use href="/icons.svg#i-camera"></use></svg>
```

CSS the wrapper needs (already in the site stylesheet; Worker-served pages —
`/find`, `/api` — carry their OWN CSS, so add it there):

```css
.rowicon{fill:none;stroke:currentColor;stroke-width:1.6;
  stroke-linecap:round;stroke-linejoin:round}
```

A glyph that labels something gets `role="img"` + `aria-label`; a decorative
one gets `aria-hidden="true"`. Never an icon alone where the text carried
meaning — the icon rides beside the word, it does not replace it.

## Mapping — the emoji in the tree today → the sprite

| was | means | sprite |
|-----|-------|--------|
| 📷 | photo | `i-camera` |
| ☎️ | phone / contact | `i-phone` |
| 🚻 | toilet | `i-loo` |
| 🎪 | event | `i-party` |
| 🕘 | opening hours | `i-clock` |
| 🟢 | open now | `i-clock` + `.is-open` (green state) — see gaps |
| 💬 | LINE / chat | `i-chat` |
| 🌐 | website | `i-globe` |
| ✉️ | email | `i-mail` |
| 📍 | use my position | `i-near` |
| 🔍 | search | `i-search` |
| sort control | | `i-sort` |
| refine / filter control | | `i-filter` |
| grid / list view toggle | | `i-grid` / `i-list` |
| clear · none · yes · warn | | `i-x` · `i-not` · `i-check` · `i-warn` |
| a place pin / a gate / a car park | | `i-pin` · `i-gate` · `i-park` |

## Gaps to settle during cleanup

- **open-now marker.** `i-clock` also carries "hours". Either a green state
  class on the clock, or a new `i-dot` symbol. Her call at swap time.
- **brand / social marks** (Facebook ⓕ, IG ◎, X 𝕏, TikTok ♪, YouTube ▶,
  WhatsApp ✆). Not in the proprietary sheet. Options: add brand symbols, or
  drop to a short text label. Not sprited until decided — do not invent one.

## Cleanup — staged, relaxed pace

Per-surface, each its own small change, tests green each time. Fleet search
(`publish/fleetsearch.js` `HAS_LABEL` / `WAY_LABEL`) rides with the curation
rebuild (WO-97), since those rows are being redrawn anyway. Register: WO-98.
First swap also proves same-origin `<use href="/icons.svg#…">` renders on a
Worker-served page (docs pages already do; `/find` has not used the sheet yet).
