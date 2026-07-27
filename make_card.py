#!/usr/bin/env python3
"""Brand og:image card (1200x630) -> assets/card.png (build.py copies into docs/).

Text is limited to baseline-only Thai ("มดแดง" has no above/below vowels) plus
English, because this Pillow lacks complex-text shaping (no raqm). Per-item Thai
cards wait until we render cards with a real shaping engine.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
PAPER, INK, ANT, DARK = "#FBF6EE", "#2A1E16", "#C2401C", "#8F2E13"
FONT = "/Library/Fonts/Arial Unicode.ttf"

img = Image.new("RGB", (W, H), PAPER)
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
import os
os.makedirs("assets", exist_ok=True)
img.save(out)
print("wrote", out)
