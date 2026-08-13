#!/usr/bin/env python3
"""Brand og:image card (1200x630) -> assets/card.png (build.py copies into docs/).

Text is limited to baseline-only Thai ("มดแดง" has no above/below vowels) plus
English, because this Pillow lacks complex-text shaping (no raqm). Per-item Thai
cards wait until we render cards with a real shaping engine.

The ground is the old city itself — the moat square, the Ping, the sois — drawn
from our own tiles by map_ground.py and held back under a paper wash so the
name stays the loudest thing on it. This is the card that unfurls for every
link that has no card of its own, which makes it the single most-seen picture
the site owns; a directory that claims to know every soi should show some.
With no tile archive on the machine it falls back to the plain cream card it
has always been.
"""
import os

from PIL import Image, ImageDraw, ImageFont

import map_ground

W, H = 1200, 630
PAPER, INK, ANT, DARK = "#FBF6EE", "#2A1E16", "#C2401C", "#8F2E13"
FONT = "/Library/Fonts/Arial Unicode.ttf"

# The old city, framed so the moat square lands in the right-hand two-thirds —
# the half of the card the wash leaves clear. Centred on the moat itself and
# then pushed west, because the picture has to be composed around the words
# rather than the words dropped onto the middle of a map.
CENTER = (18.7884, 98.9761)
SPAN_M = 2700

img = Image.new("RGB", (W, H), PAPER)

ground = map_ground.shared()
if ground.available:
    # Full-strength ground here, not faded: fade blends towards paper, and the
    # moat — the one thing on this card that has to survive — is a pale blue
    # that goes to nothing three steps in. The wash below does the quieting,
    # and it quiets the half of the card where the words are instead of all
    # of it.
    base = ground.picture(CENTER, (W, H), span_m=SPAN_M, contrast=1.45,
                          credit=False, scale=False)
    if base is not None:
        img = base
        # A paper wash, heavy at the left where the name sits and clearing to
        # nothing at the right. Drawn as a mask rather than a flat opacity so
        # the map is genuinely visible on one side of the card instead of
        # uniformly murky across all of it.
        wash = Image.new("L", (W, 1))
        for x in range(W):
            t = x / (W - 1)
            wash.putpixel((x, 0), int(255 * max(0.0, min(1.0, 1.15 - 1.65 * t))))
        img = Image.composite(Image.new("RGB", (W, H), PAPER), img,
                              wash.resize((W, H)))
        map_ground.credit_mark(img)

d = ImageDraw.Draw(img)

# double rule top and bottom, like the site header
for y in (36, 44):
    d.line([(60, y), (W - 60, y)], fill=ANT, width=4)
for y in (H - 44, H - 36):
    d.line([(60, y), (W - 60, y)], fill=ANT, width=4)


def ant(cx, cy, s, color=INK):
    """A little walking ant: three body circles, legs, antennae."""
    for i, (dx, r) in enumerate([(-1.6, 0.55), (-0.4, 0.42), (0.9, 0.7)]):
        x = cx + dx * s
        d.ellipse([x - r * s, cy - r * s, x + r * s, cy + r * s], fill=color)
    for dx in (-0.9, -0.1, 0.7):
        d.line([(cx + dx * s, cy), (cx + (dx - 0.5) * s, cy + 1.3 * s)], fill=color, width=max(2, s // 8))
        d.line([(cx + dx * s, cy), (cx + (dx + 0.4) * s, cy + 1.3 * s)], fill=color, width=max(2, s // 8))
    d.line([(cx + 1.3 * s, cy - 0.5 * s), (cx + 2.0 * s, cy - 1.2 * s)], fill=color, width=max(2, s // 9))
    d.line([(cx + 1.5 * s, cy - 0.4 * s), (cx + 2.3 * s, cy - 0.9 * s)], fill=color, width=max(2, s // 9))


ant(200, 300, 60, ANT)

title = ImageFont.truetype(FONT, 170)
sub = ImageFont.truetype(FONT, 52)
small = ImageFont.truetype(FONT, 38)

d.text((360, 190), "มดแดง", font=title, fill=ANT)
d.text((90, 452), "Chiang Mai · Chiang Rai city directory", font=sub, fill=INK)
d.text((90, 530), "knows every soi, like a red ant", font=small, fill=DARK)

# a trail of little ants walking the bottom rule
for i, x in enumerate(range(950, 1120, 60)):
    ant(x, H - 80, 14, DARK)

out = "assets/card.png"
os.makedirs("assets", exist_ok=True)
img.quantize(colors=256, dither=Image.Dither.NONE).save(out, optimize=True)
print("wrote", out)
