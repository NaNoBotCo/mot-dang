"""WO-77 — the chrome glyphs: every mark the site's furniture draws, drawn.

Nan, 2026-09-08: *"Please draw the needful icons to fully kit my site out with
bespoke glyphs."* Same day, on the results doors: drawn icons, not system
emoji — an emoji is whatever the reader's phone decides it is, at whatever
size, in whatever palette.

build.ICON_SPRITE already holds the 27 category marks and a dozen chrome ones
(i-map, i-cal, i-search, i-route, i-pin, i-dice, i-lantern, i-loo …). What was
still emoji is the furniture: the ant itself (47 places in build.py), 📍 here,
🚶 walk, 🛵 ride, the weather family, 🎪 what is on, 💊 pharmacy, ⊘ not, ☰,
the filter rail. This module is the second half of that sprite. It draws the
same way — 24-grid, stroke only, `fill:none; stroke:currentColor` through the
`.rowicon` rule (build.py CSS), round caps — so a glyph from either half sits
beside one from the other and nobody can tell which file it came from.

Two contracts, both tested in tests/test_glyphs.py:

  · IDs never collide with build.ICON_SPRITE. A `<use>` resolves the first id
    it finds; a duplicate would silently draw the wrong picture.
  · Every glyph is decorative and carries no colour of its own. No `fill=`,
    no `stroke=` inside the sprite: colour is the row's, always. The one
    exception is the ant mark, which has a filled variant (i-ant-solid) for
    the logo tile, where it sits on the red at 48 px and a stroke would fuzz.

EMOJI maps each glyph to the emoji it replaces, so the swap in build.py is a
lookup and not a judgement, and a reviewer can grep for what is left.

Where it goes: page() writes `{ICON_SPRITE}` once per page; add `{glyphs.SPRITE}`
beside it. Nothing here runs a build.
"""

import functools
import re

# ── the drawings ─────────────────────────────────────────────────────────────
# One <g> per glyph. Margin 2.5 on the 24 grid; nothing heavier than three
# primitives unless the thing cannot be said in three. Keep strokes off the
# grid edge — the `.rowicon` stroke is 1.6 and a path at 0 or 24 is clipped.

_G = {
    # ── the site's own marks ──────────────────────────────────────────────
    # THE ANT IS THE SITE'S OWN. Nan, 2026-09-08: "There is a proper SVG logo
    # for motdang.net (ant shape) already drawn." That drawing is build.ANT_SVG
    # — three bodies, six legs, two feelers, on a 480×320 card — and these two
    # are that geometry scaled onto the 24 grid (×0.088, from its own bounding
    # box), not a second ant. build.ANT_MARK is the same drawing at tile size.
    "i-ant": '<ellipse cx="9.9" cy="12.3" rx="3" ry="2.6"/><ellipse cx="14.3" cy="12.1" rx="1.9" ry="1.7"/><ellipse cx="19.4" cy="12" rx="3.7" ry="3.2"/><path d="M12.2 12.1 10.6 17M14.5 12.1 14.3 17.4M16.6 12.1 18.5 17M12.2 11.6 9.9 7.4M14.5 11.4 14.6 7M16.6 11.6 19 7.5"/><path d="M8.3 10.7Q5.7 8.1 3.7 8.6M8.8 9.8Q6.7 7 4.8 6.7"/>',
    # The same ant with the bodies filled: the logo tile only.
    "i-ant-solid": '<ellipse cx="9.9" cy="12.3" rx="3" ry="2.6" fill="currentColor"/><ellipse cx="14.3" cy="12.1" rx="1.9" ry="1.7" fill="currentColor"/><ellipse cx="19.4" cy="12" rx="3.7" ry="3.2" fill="currentColor"/><path d="M12.2 12.1 10.6 17M14.5 12.1 14.3 17.4M16.6 12.1 18.5 17M12.2 11.6 9.9 7.4M14.5 11.4 14.6 7M16.6 11.6 19 7.5"/><path d="M8.3 10.7Q5.7 8.1 3.7 8.6M8.8 9.8Q6.7 7 4.8 6.7"/>',
    # The old city: the moat as a rounded square, the city inside it.
    "i-moat": '<rect x="3" y="3" width="18" height="18" rx="3"/><rect x="7.5" y="7.5" width="9" height="9" rx="1"/>',
    # A city gate: wall, crenellation, the arch you walk through.
    "i-gate": '<path d="M3 20.5V8h18v12.5"/><path d="M3 8V5h3v3M9 8V5h6v3M18 8V5h3v3"/><path d="M8.5 20.5v-6a3.5 3.5 0 0 1 7 0v6"/><path d="M2 20.5h20"/>',
    # ── where ─────────────────────────────────────────────────────────────
    # Here: a crosshair, not a pin. A pin says "a place"; this says "you".
    # The ring: how far. A dashed circle around a centre — the radius control
    # on the results rail and the ring on the map.
    "i-ring": '<circle cx="12" cy="12" r="8.5" stroke-dasharray="3 2.3"/><circle cx="12" cy="12" r="1.6"/>',
    "i-here": '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="1.4"/><path d="M12 2.5v3.5M12 18v3.5M2.5 12H6M18 12h3.5"/>',
    "i-compass": '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5Z"/><path d="M12 3v1.5M12 19.5V21M3 12h1.5M19.5 12H21"/>',
    "i-walk": '<circle cx="13" cy="4.3" r="1.8"/><path d="M11 21.5 12.5 15l-2-2.2.8-4.5 3 1.2 3.4 3.2"/><path d="M9.2 12.8 7 14.6l-1.2 4"/><path d="M14 15.5l1.2 2 2.8 4"/>',
    "i-scooter": '<circle cx="5.5" cy="17.5" r="2.6"/><circle cx="18.5" cy="17.5" r="2.6"/><path d="M8.1 17.5h4.4l1.5-6H8"/><path d="M14 11.5 16.5 6h3"/><path d="M13.9 15.8 18 17.5"/>',
    "i-bus": '<rect x="4" y="3.5" width="16" height="14.5" rx="2.5"/><path d="M4 12h16M8 3.5v8.5M16 3.5v8.5"/><circle cx="8" cy="20" r="1.5"/><circle cx="16" cy="20" r="1.5"/>',
    "i-road": '<path d="M9 3 5 21M15 3l4 18"/><path d="M12 5v2.5M12 10.5V13M12 16v2.5" stroke-dasharray="none"/>',
    "i-doi": '<path d="m2.5 19 6-10 3.6 5.4"/><path d="m8.5 19 6.5-11 6.5 11Z"/><path d="M13.2 12.6 15 11l1.8 1.6"/>',
    "i-water": '<path d="M2.5 8.5c2.4 0 2.4-2 4.8-2s2.4 2 4.8 2 2.4-2 4.8-2 2.4 2 4.6 2"/><path d="M2.5 13.5c2.4 0 2.4-2 4.8-2s2.4 2 4.8 2 2.4-2 4.8-2 2.4 2 4.6 2"/><path d="M2.5 18.5c2.4 0 2.4-2 4.8-2s2.4 2 4.8 2 2.4-2 4.8-2 2.4 2 4.6 2"/>',
    "i-onsen": '<path d="M4 13.5h16l-1.2 5a3 3 0 0 1-2.9 2.3H8.1a3 3 0 0 1-2.9-2.3Z"/><path d="M8.5 10c0-1.5 1.4-1.8 1.4-3.2S8.5 4.5 8.5 3M12 10c0-1.5 1.4-1.8 1.4-3.2S12 4.5 12 3M15.5 10c0-1.5 1.4-1.8 1.4-3.2S15.5 4.5 15.5 3"/>',
    # ── when ──────────────────────────────────────────────────────────────
    # What is on: a marquee. The lantern (build) is a festival; this is any
    # night with a stage.
    "i-tent": '<path d="M3 11c3-1.6 6-4 9-7.5 3 3.5 6 5.9 9 7.5"/><path d="M4.5 10.5 3.5 20.5h17l-1-10"/><path d="M9.5 20.5v-5a2.5 2.5 0 0 1 5 0v5"/><path d="M12 3.5V2"/>',
    "i-clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.5l3.5 2"/>',
    "i-lamp": '<path d="M12 2.5v3"/><path d="M8 11.5a4 4 0 1 1 8 0c0 2-1.5 2.8-1.5 4.5h-5c0-1.7-1.5-2.5-1.5-4.5Z"/><path d="M9.8 18.5h4.4M10.5 21h3"/>',
    "i-fullmoon": '<circle cx="12" cy="12" r="9"/><circle cx="9" cy="9.5" r="1.6"/><circle cx="14.5" cy="14" r="2.2"/><circle cx="15.5" cy="8" r=".9"/>',
    "i-sparkle": '<path d="M12 3c.6 4.6 3.4 8.4 9 9-5.6.6-8.4 4.4-9 9-.6-4.6-3.4-8.4-9-9 5.6-.6 8.4-4.4 9-9Z"/>',
    "i-party": '<path d="m4 20 4-11 7 7Z"/><path d="M8.5 9.5 15 16"/><path d="M14 4.5c1.2 1.4 1.2 3 0 4.5M17.5 3l.5 2.5M20.5 7.5 18 8.5M18.5 12.5c1.4-.2 2.6.4 3 1.5"/>',
    # ── weather and air ───────────────────────────────────────────────────
    "i-sun": '<circle cx="12" cy="12" r="4.5"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
    "i-cloud": '<path d="M7 18.5a4 4 0 0 1-.6-7.95A5.5 5.5 0 0 1 17 9.5a4.5 4.5 0 0 1 .5 9Z"/>',
    "i-cloudsun": '<path d="M8.5 19.5a3.5 3.5 0 0 1-.5-6.96A4.8 4.8 0 0 1 17.2 11a3.9 3.9 0 0 1 .3 7.8Z"/><path d="M6.5 8.6a3.6 3.6 0 0 1 6.6-1.4"/><path d="M8 2.5v1.8M2.5 8H4.3M4 4l1.3 1.3M12 4l-1.3 1.3"/>',
    "i-rain": '<path d="M7 15a4 4 0 0 1-.6-7.95A5.5 5.5 0 0 1 17 6a4.5 4.5 0 0 1 .5 9Z"/><path d="m8.5 17.5-1 3M12.5 17.5l-1 3M16.5 17.5l-1 3"/>',
    "i-storm": '<path d="M7 14a4 4 0 0 1-.6-7.95A5.5 5.5 0 0 1 17 5a4.5 4.5 0 0 1 .5 9Z"/><path d="m13 13-2.5 4h3l-2.5 4.5"/>',
    "i-haze": '<path d="M3 8h18M5 12h14M3 16h18M7 20h10"/>',
    "i-wind": '<path d="M3 9h11a2.5 2.5 0 1 0-2.5-2.5"/><path d="M3 13h15a2.5 2.5 0 1 1-2.5 2.5"/><path d="M3 17h7a2 2 0 1 1-2 2"/>',
    # PM2.5: what you cannot see, drawn as what it is — particles in the air.
    "i-air": '<path d="M3 9.5h9M3 14.5h13"/><circle cx="16" cy="6.5" r="1"/><circle cx="19.5" cy="10" r="1.4"/><circle cx="7" cy="19" r="1.2"/><circle cx="19" cy="17.5" r="1"/><circle cx="12.5" cy="18.5" r=".8"/>',
    # ── people, things, doors ─────────────────────────────────────────────
    "i-pill": '<rect x="3" y="8.5" width="18" height="7" rx="3.5" transform="rotate(-35 12 12)"/><path d="m9.2 7.9 5.6 8.2" transform="rotate(0)"/>',
    "i-sos": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v5M12 16v5M3 12h5M16 12h5"/>',
    "i-lotus": '<path d="M12 20c-2.5-2-4-5-4-9 0-3 1.6-5.5 4-7 2.4 1.5 4 4 4 7 0 4-1.5 7-4 9Z"/><path d="M12 20c-4.4 0-8-2.4-9.5-6 3-.6 6-.2 8.5 1.6"/><path d="M12 20c4.4 0 8-2.4 9.5-6-3-.6-6-.2-8.5 1.6"/>',
    "i-pan": '<circle cx="9.5" cy="13" r="6.5"/><path d="M15.5 10.5 21 5.5"/><circle cx="9.5" cy="13" r="2"/>',
    "i-coffee": '<path d="M4 8h12v6a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5Z"/><path d="M16 10h2a2.5 2.5 0 0 1 0 5h-2"/><path d="M3 21.5h15"/><path d="M8 5c0-1 .8-1.2.8-2M11.5 5c0-1 .8-1.2.8-2"/>',
    "i-toy": '<rect x="2.5" y="7" width="19" height="11" rx="5"/><path d="M7.5 10.5v4M5.5 12.5h4"/><circle cx="16" cy="11.2" r=".9"/><circle cx="18.2" cy="13.6" r=".9"/>',
    "i-camera": '<path d="M3 8.5h4l1.5-2.5h7L17 8.5h4v11H3Z"/><circle cx="12" cy="13.5" r="3.2"/>',
    "i-phone": '<path d="M5.5 3.5h3.2l1.6 4-2 1.6a11.5 11.5 0 0 0 6.6 6.6l1.6-2 4 1.6v3.2A1.5 1.5 0 0 1 19 20C11 19.5 4.5 13 4 5a1.5 1.5 0 0 1 1.5-1.5Z"/>',
    "i-globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "i-chat": '<path d="M4 5.5h16v10H10l-4.5 3.5v-3.5H4Z"/><path d="M8 9h8M8 12h5"/>',
    "i-megaphone": '<path d="M3.5 10v4l10 4V6Z"/><path d="M13.5 8.5a3.5 3.5 0 0 1 0 7"/><path d="M6 18.5 7 21h3l-.6-3.2"/>',
    "i-link": '<path d="M10 14 14 10"/><path d="M8.5 15.5 6.4 17.6a3 3 0 0 1-4.2-4.2l3.5-3.5a3 3 0 0 1 4.2 0"/><path d="m15.5 8.5 2.1-2.1a3 3 0 0 1 4.2 4.2l-3.5 3.5a3 3 0 0 1-4.2 0"/>',
    "i-share": '<circle cx="18" cy="5.5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="18.5" r="2.5"/><path d="m8.2 10.8 7.6-4.1M8.2 13.2l7.6 4.1"/>',
    "i-download": '<path d="M12 3v11M7.5 10 12 14.5 16.5 10"/><path d="M4 16v3.5h16V16"/>',
    "i-tag": '<path d="M3 3h8.5L21 12.5 12.5 21 3 11.5Z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "i-note": '<path d="M5 21h14"/><path d="m15.5 3.5 4 4L9 18H5v-4Z"/><path d="m13 6 4 4"/>',
    "i-gear": '<circle cx="12" cy="12" r="3.2"/><circle cx="12" cy="12" r="7.2" stroke-dasharray="2.6 3.06"/><path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.8 1.8M16.7 16.7l1.8 1.8M5.5 18.5l1.8-1.8M16.7 7.3l1.8-1.8"/>',
    "i-grid": '<rect x="3.5" y="3.5" width="7" height="7" rx="1.2"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.2"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.2"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.2"/>',
    "i-live": '<circle cx="12" cy="12" r="2"/><path d="M8.5 15.5a5 5 0 0 1 0-7M15.5 8.5a5 5 0 0 1 0 7"/><path d="M5.7 18.3a9 9 0 0 1 0-12.6M18.3 5.7a9 9 0 0 1 0 12.6"/>',
    "i-heart": '<path d="M12 20.5 4.4 12.9a4.5 4.5 0 0 1 6.4-6.4l1.2 1.2 1.2-1.2a4.5 4.5 0 0 1 6.4 6.4Z"/>',
    "i-flower": '<circle cx="12" cy="12" r="2.4"/><path d="M12 9.6c-1.8-2.6-1.2-6 0-6.6 1.2.6 1.8 4 0 6.6ZM14.3 10.3c3-1 5.9.8 5.9 2.1-.9 1-4.2 1.3-5.9-2.1ZM13.4 13.7c2.9 1.3 3.6 4.7 2.6 5.6-1.3.3-4.1-1.7-2.6-5.6ZM10.6 13.7c-1.5 3.9-4.3 5.9-5.6 5.6-1-.9-.3-4.3 2.6-5.6ZM9.7 10.3c-3.9-1.5-5.9-4.5-5.6-5.9 1.3-.5 4.3.9 5.6 5.9Z"/>',
    "i-flag": '<path d="M5 21V4"/><path d="M5 4.5c4-2 8 2 13 0v9c-5 2-9-2-13 0"/>',
    # Thumbs up and down: the doodle votes (/doodles/ and the front band), accuracy and aesthetics.
    "i-thumb-up": '<path d="M7.5 10.5v10H4.5a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1Z"/><path d="M7.5 10.5 11 3.5a2.3 2.3 0 0 1 2.6 2.8L13 9.5h5.6a2 2 0 0 1 2 2.4l-1.4 7a2 2 0 0 1-2 1.6H7.5"/>',
    "i-thumb-down": '<path d="M7.5 13.5v-10H4.5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1Z"/><path d="M7.5 13.5 11 20.5a2.3 2.3 0 0 0 2.6-2.8L13 14.5h5.6a2 2 0 0 0 2-2.4l-1.4-7a2 2 0 0 0-2-1.6H7.5"/>',
    # ── controls ──────────────────────────────────────────────────────────
    "i-menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "i-x": '<path d="m6 6 12 12M18 6 6 18"/>',
    "i-check": '<path d="m4.5 12.5 4.5 4.5L19.5 6.5"/>',
    "i-minus": '<path d="M5 12h14"/>',
    # NOT: the ⊘ on a chip. Circle and slash, the slash going the way a
    # "no" sign goes everywhere in Thailand.
    "i-not": '<circle cx="12" cy="12" r="8.5"/><path d="m6 6 12 12"/>',
    "i-warn": '<path d="M12 3.5 21.5 20h-19Z"/><path d="M12 9.5v5M12 17.2v.3"/>',  # stylecheck: allow — icon name
    "i-refresh": '<path d="M20 12a8 8 0 0 1-14.3 4.9"/><path d="M4 12a8 8 0 0 1 14.3-4.9"/><path d="M18.3 3.5v3.6h-3.6M5.7 20.5v-3.6h3.6"/>',
    # Filter: three sliders. The rail on the results page is these, with a
    # count on each; the word "filter" is never printed.
    "i-filter": '<path d="M4 7h16M4 12h16M4 17h16"/><circle cx="9" cy="7" r="1.8" fill="var(--paper,#fff)"/><circle cx="15" cy="12" r="1.8" fill="var(--paper,#fff)"/><circle cx="7" cy="17" r="1.8" fill="var(--paper,#fff)"/>',
    "i-sort": '<path d="M7 4v16M3.5 16.5 7 20l3.5-3.5"/><path d="M17 20V4M13.5 7.5 17 4l3.5 3.5"/>',
    "i-near": '<path d="M12 21.4s6.4-6.6 6.4-11a6.4 6.4 0 1 0-12.8 0c0 4.4 6.4 11 6.4 11Z"/><path d="M9.5 10.2h5M12 7.7v5"/>',
    "i-zoom-in": '<circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4.5 4.5M8 11h6M11 8v6"/>',
    "i-zoom-out": '<circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4.5 4.5M8 11h6"/>',
    "i-layers": '<path d="m12 3.5 9 4.5-9 4.5-9-4.5Z"/><path d="m3 12.5 9 4.5 9-4.5M3 16.5l9 4.5 9-4.5"/>',
    "i-list": '<path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4.5" cy="6" r="1.2"/><circle cx="4.5" cy="12" r="1.2"/><circle cx="4.5" cy="18" r="1.2"/>',
    "i-back": '<path d="M15 5 8 12l7 7"/>',
    "i-arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    # ── guide me: the turn ahead, and the voice that says it ─────────────
    "i-turn-left": '<path d="M16 20v-8a3 3 0 0 0-3-3H6"/><path d="M9.5 5.5 6 9l3.5 3.5"/>',
    "i-turn-right": '<path d="M8 20v-8a3 3 0 0 1 3-3h7"/><path d="M14.5 5.5 18 9l-3.5 3.5"/>',
    "i-bear-left": '<path d="M15 20v-6L8 7"/><path d="M8 12V7h5"/>',
    "i-bear-right": '<path d="M9 20v-6l7-7"/><path d="M16 12V7h-5"/>',
    "i-uturn": '<path d="M8 20V9a4 4 0 0 1 8 0v4"/><path d="M12.5 10 16 13.5 19.5 10"/>',
    "i-straight": '<path d="M12 20V5"/><path d="M7.5 9.5 12 5l4.5 4.5"/>',
    "i-volume": '<path d="M4 9.5v5h3.5L12 18V6L7.5 9.5Z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
    "i-volume-off": '<path d="M4 9.5v5h3.5L12 18V6L7.5 9.5Z"/><path d="m16 9.5 5 5m0-5-5 5"/>',
    # ── the long tail the sweep meets ─────────────────────────────────────
    "i-mail": '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="m3.5 7 8.5 6.5L20.5 7"/>',
    "i-plane": '<path d="M10.5 13.5 3 11l1.5-1.5 6.5 1 5-5.5a1.6 1.6 0 0 1 2.3 2.3l-5.5 5 1 6.5L12.3 20l-2.5-7"/><path d="M6.5 17.5 4 20"/>',
    "i-basket": '<path d="M3 10h18l-1.8 9a2 2 0 0 1-2 1.5H6.8a2 2 0 0 1-2-1.5Z"/><path d="M8 10l3-6M16 10l-3-6M9 13.5v4M12 13.5v4M15 13.5v4"/>',
    "i-fuel": '<path d="M4 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16"/><path d="M4 21h10M6.5 6.5h5v4h-5Z"/><path d="M14 9h2.5a1.5 1.5 0 0 1 1.5 1.5V17a1.5 1.5 0 0 0 3 0v-6.5L18.5 8"/>',
    "i-yinyang": '<circle cx="12" cy="12" r="9"/><path d="M12 3a4.5 4.5 0 0 1 0 9 4.5 4.5 0 0 0 0 9"/><circle cx="12" cy="7.5" r="1.1"/><circle cx="12" cy="16.5" r="1.1"/>',
    "i-beer": '<path d="M5 6h10v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2Z"/><path d="M15 9h2.5a1.5 1.5 0 0 1 1.5 1.5v4a1.5 1.5 0 0 1-1.5 1.5H15"/><path d="M5 6c0-2 1.5-3 3.5-3S12 4 12 4s1-1.5 3-1v3"/><path d="M8 10v8M11.5 10v8"/>',
    "i-wheelchair": '<circle cx="9" cy="4" r="1.6"/><path d="M9 7v6h5l3 5"/><path d="M9 10h4"/><path d="M6.5 12.5a5 5 0 1 0 7.2 6.4"/>',
    "i-print": '<path d="M7 8V3.5h10V8"/><rect x="3" y="8" width="18" height="9" rx="2"/><path d="M7 14h10v6.5H7Z"/><circle cx="17.5" cy="11.5" r=".7"/>',
    "i-needle": '<path d="M4 20 16.5 7.5"/><path d="M14.5 5.5a2.5 2.5 0 1 1 3.5 3.5"/><circle cx="17.2" cy="6.8" r=".9"/><path d="M4 20c2-4 3-6 4-7"/>',
    "i-trans": '<circle cx="12" cy="13" r="4"/><path d="M12 17v4.5M9.5 19.5h5"/><path d="M14.8 10.2 19 6M15.5 6H19v3.5"/><path d="M9.2 10.2 5 6M8.5 6H5v3.5"/>',
    "i-question": '<circle cx="12" cy="12" r="9"/><path d="M9.3 9.5a2.7 2.7 0 1 1 3.9 2.4c-.9.5-1.2 1-1.2 2M12 17.2v.3"/>',
    "i-atm": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M6.5 14.5h4"/>',
    "i-document": '<path d="M6 3h8l4 4v14H6Z"/><path d="M14 3v4h4M9 12h6M9 15.5h6"/>',
    "i-plus-circle": '<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8M8 12h8"/>',
}

# The emoji each glyph stands in for, where one exists. Grep target for the
# swap: an emoji in build.py that is in this table has a drawn replacement.
EMOJI = {
    "🐜": "i-ant", "📍": "i-here", "🧭": "i-compass", "🚶": "i-walk", "🛵": "i-scooter",
    "🚌": "i-bus", "🛣": "i-road", "⛰": "i-doi", "🌊": "i-water", "♨": "i-onsen",
    "🎪": "i-tent", "🕐": "i-clock", "🏮": "i-lantern", "🌕": "i-fullmoon", "✨": "i-sparkle",
    "🎉": "i-party", "☀": "i-sun", "🌤": "i-cloudsun", "⛅": "i-cloudsun", "☁": "i-cloud",
    "🌧": "i-rain", "🌦": "i-rain", "⛈": "i-storm", "🌫": "i-haze", "🌬": "i-wind",
    "💊": "i-pill", "🆘": "i-sos", "🙏": "i-lotus", "🍳": "i-pan", "☕": "i-coffee",
    "🧩": "i-toy", "📷": "i-camera", "☎": "i-phone", "📞": "i-phone", "🌐": "i-globe",
    "💬": "i-chat", "📣": "i-megaphone", "🔗": "i-link", "🏷": "i-tag", "📝": "i-note",
    "⚙": "i-gear", "📡": "i-live", "🧡": "i-heart", "👍": "i-thumb-up", "👎": "i-thumb-down", "❤": "i-heart", "🌸": "i-flower",
    "☰": "i-menu", "✕": "i-x", "✓": "i-check", "⊘": "i-not", "🚫": "i-not", "⚠": "i-warn",  # stylecheck: allow — icon name
    "🔁": "i-refresh", "🔄": "i-refresh", "🔀": "i-refresh", "🎲": "i-dice", "🗺": "i-map", "🗓": "i-cal",
    # the long tail
    "⬇": "i-download", "📤": "i-download", "📦": "i-download", "💾": "i-download",
    "✉": "i-mail", "📩": "i-mail", "📮": "i-mail", "✈": "i-plane", "🧺": "i-basket",
    "⛽": "i-fuel", "☯": "i-yinyang", "🍺": "i-beer", "♿": "i-wheelchair", "🖨": "i-print",
    "🪡": "i-needle", "⚧": "i-trans", "❓": "i-question", "🏧": "i-atm", "💳": "i-atm",
    "📄": "i-document", "📜": "i-document", "🧾": "i-document", "📋": "i-list", "📊": "i-list",
    "🍽": "i-food", "🍚": "i-food", "🥣": "i-food", "🌶": "i-food", "🏯": "i-moat",
    "🏥": "i-health", "⚕": "i-health", "🕰": "i-clock", "🕒": "i-clock", "🕘": "i-clock",
    "📱": "i-phone", "📲": "i-phone", "✆": "i-phone", "🛏": "i-bed", "🖼": "i-camera",
    "😎": "i-moon", "🌅": "i-sun", "🔆": "i-sun", "🌱": "i-leaf", "🍃": "i-leaf",
    "⭐": "i-star", "✦": "i-sparkle", "🔮": "i-sparkle", "🏠": "i-home2", "🏘": "i-home2",
    "✏": "i-note", "💡": "i-lamp", "🎓": "i-school", "📚": "i-book", "🚐": "i-bus",
    "🚉": "i-bus", "🚕": "i-scooter", "🚰": "i-water", "🌨": "i-rain", "❄": "i-rain",
    "🌡": "i-sun", "💛": "i-heart", "✂": "i-beauty", "💈": "i-beauty", "🐕": "i-pet",
    "🏋": "i-fit", "🧹": "i-broom", "🌳": "i-park", "🤝": "i-people", "👯": "i-people",
    "🫂": "i-people", "🏬": "i-shop", "🎟": "i-tent", "🎋": "i-party", "🪙": "i-coin",
    "💱": "i-swap", "🧠": "i-health", "🖐": "i-check", "🗑": "i-x", "☸": "i-lotus",
    "🪷": "i-lotus", "🏳": "i-flag", "🪵": "i-tools", "🔌": "i-tools", "🥇": "i-star",
    "♪": "i-live", "🎱": "i-dice", "🌀": "i-refresh", "🏙": "i-moat", "🗂": "i-grid",
    "📅": "i-cal", "🔎": "i-search", "🔍": "i-search", "🚻": "i-loo", "🛕": "i-wat",
    "🏪": "i-shop", "🛍": "i-gift", "🩺": "i-health", "🍜": "i-food", "🏃": "i-fit",
    "🔧": "i-tools", "🛠": "i-tools", "💆": "i-spa", "🥊": "i-glove", "🐘": "i-chang",
    "🎬": "i-film", "🌙": "i-moon", "★": "i-star", "📌": "i-pin", "🏦": "i-bank",
}

# Category → glyph, for the one category build.CAT_ICON leaves label-only.
CAT_ICON_MORE = {"school": "i-school"}

# The eight front-page paths, re-keyed to drawn marks (nownear_layer.PATHS
# carries emoji in column two; this is the same table with the glyph id).
PATHS = (
    ("cm/shopping/", "i-gift", "ช้อปปิ้ง", "shopping"),
    ("cm/medical/clinic/", "i-health", "คลินิก", "clinics"),
    ("cm/food/", "i-food", "ของกิน", "food"),
    ("cm/sport/", "i-fit", "กีฬา-ฟิตเนส", "sport"),
    ("cm/repair/", "i-tools", "ช่าง", "trades"),
    ("cm/transport/", "i-bus", "เดินทาง", "getting around"),
    ("cm/medical/pharmacy/", "i-pill", "ร้านยา", "pharmacies"),
    ("cm/massage/", "i-spa", "นวด", "massage"),
)


def sprite(ids=None):
    """The <svg><defs> block. `ids` limits it to a subset (a page that draws
    three glyphs need not carry seventy); None is the whole set."""
    keys = list(_G) if ids is None else [k for k in _G if k in set(ids)]
    body = "\n".join(f'<g id="{k}">{_G[k]}</g>' for k in keys)
    return ('<svg aria-hidden="true" focusable="false" width="0" height="0" '
            'style="position:absolute" xmlns="http://www.w3.org/2000/svg"><defs>\n'
            + body + "\n</defs></svg>")


SPRITE = sprite()
IDS = tuple(_G)

# The ids build.ICON_SPRITE already draws. Listed here rather than imported —
# build.py runs the whole site's top level on import — and pinned by
# tests/test_glyphs.py against the real sprite so the two cannot drift.
BUILD_IDS = (
    "i-wat", "i-food", "i-spa", "i-health", "i-bank", "i-bed", "i-school", "i-market",
    "i-gift", "i-home2", "i-ride", "i-tools", "i-beauty", "i-ink", "i-glove", "i-chang",
    "i-khrok", "i-pet", "i-book", "i-fit", "i-broom", "i-people", "i-shop", "i-film",
    "i-museum", "i-park", "i-star", "i-leaf", "i-search", "i-me", "i-plus", "i-claim",
    "i-lantern", "i-cal", "i-dice", "i-coin", "i-swap", "i-moon", "i-route", "i-loo",
    "i-pin", "i-map",
)
KNOWN = frozenset(IDS) | frozenset(BUILD_IDS)


def icon(name, size=22, cls="rowicon", label=None):
    """One <use>. Decorative by contract — beside a label — unless `label`
    is given, in which case the svg itself is the accessible name (a door
    with no words beside it: the map and calendar doors in the masthead)."""
    if name not in KNOWN:
        return ""
    a11y = (f'role="img" aria-label="{label}"' if label
            else 'aria-hidden="true" focusable="false"')
    return (f'<svg class="{cls}" {a11y} width="{size}" height="{size}" '
            f'viewBox="0 0 24 24"><use href="#{name}"></use></svg>')


_VS = "\ufe0f"


# Every key of EMOJI is one code point, so one pass of one character class
# finds them all. Until 2026-10-10 this sorted the 168-entry table and searched
# the text once per entry, for every text node of every page: 2,600 of a
# 5,678-second build on motdang-build.
_EMOJI_ONE = re.compile("[" + "".join(re.escape(e) for e in EMOJI) + "]")
assert all(len(e) == 1 for e in EMOJI), "a multi-character emoji key needs an alternation, not a class"


@functools.lru_cache(maxsize=None)
def _icon_once(g, size, cls):
    return icon(g, size, cls)


def emoji_to_icon(text, size=22, cls="rowicon"):
    """Swap every emoji this table knows for its glyph. For chrome strings
    only — never run it over a record's own name or a reader's words."""
    out = text.replace(_VS, "")
    return _EMOJI_ONE.sub(lambda m: _icon_once(EMOJI[m.group(0)], size, cls), out)


# The page-level sweep. Visible text nodes only: not <script>, <style>,
# <title>, <textarea> or <option> bodies (an svg inside those is either
# broken code or printed markup), and never attribute values.
_SKIP = re.compile(r"(?is)(<(script|style|title|textarea|option)\b[^>]*>.*?</\2>)")
_TEXT = re.compile(r">([^<]*)<")
_ANY = re.compile("[" + "".join(re.escape(e) for e in sorted(EMOJI, key=len, reverse=True)) + _VS + "]")


def sweep_html(html, size=18, cls="rowicon"):
    """Every stock emoji in the page's text that has a glyph, drawn."""
    if not _ANY.search(html):
        return html
    parts = _SKIP.split(html)
    out = []
    for i, part in enumerate(parts):
        # split() with one capturing group yields text, match, group, text…
        if i % 3 == 1:
            out.append(part)
            continue
        if i % 3 == 2:
            continue
        out.append(_TEXT.sub(lambda m: (">" + emoji_to_icon(m.group(1), size, cls) + "<")
                             if _ANY.search(m.group(1)) else m.group(0), part))
    return "".join(out)


if __name__ == "__main__":
    import sys
    print(f"{len(_G)} glyphs · {len(EMOJI)} emoji mapped", file=sys.stderr)
    print(SPRITE)
