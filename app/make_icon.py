#!/usr/bin/env python3
"""Launcher icon: the ant red of the site, a white toilet pictogram drawn
from primitives (no emoji font to depend on), มดแดง's rounded-square sticker
shape. Writes every mipmap density the manifest asks for."""
import pathlib

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "android" / "res"

ANT = (193, 58, 46, 255)        # --ant
ANT_DARK = (143, 42, 33, 255)   # --ant-dark
PAPER = (255, 253, 247, 255)

DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
S = 8  # supersample


def draw_icon(size):
    n = size * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = n * 0.22
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=r, fill=ANT)
    # a soft inner rim, the sticker look
    d.rounded_rectangle([n * 0.03, n * 0.03, n * 0.97, n * 0.97],
                        radius=r * 0.9, outline=(255, 255, 255, 60),
                        width=max(1, n // 60))

    # WC pictogram: two figures, drawn from circles and bars
    def figure(cx, skirt):
        head_r = n * 0.075
        d.ellipse([cx - head_r, n * 0.18, cx + head_r, n * 0.18 + head_r * 2],
                  fill=PAPER)
        top = n * 0.37
        if skirt:
            d.polygon([(cx, top), (cx - n * 0.115, n * 0.62),
                       (cx + n * 0.115, n * 0.62)], fill=PAPER)
        else:
            d.rounded_rectangle([cx - n * 0.062, top, cx + n * 0.062, n * 0.62],
                                radius=n * 0.03, fill=PAPER)
        # legs
        for dx in (-n * 0.035, n * 0.035):
            d.rounded_rectangle([cx + dx - n * 0.021, n * 0.60,
                                 cx + dx + n * 0.021, n * 0.80],
                                radius=n * 0.02, fill=PAPER)

    figure(n * 0.345, skirt=False)
    figure(n * 0.655, skirt=True)
    # divider
    d.rounded_rectangle([n * 0.487, n * 0.20, n * 0.513, n * 0.78],
                        radius=n * 0.01, fill=(255, 255, 255, 150))
    return img.resize((size, size), Image.LANCZOS)


def main():
    for dpi, size in DENSITIES.items():
        out = RES / f"mipmap-{dpi}"
        out.mkdir(parents=True, exist_ok=True)
        draw_icon(size).save(out / "ic_launcher.png")
        print(f"  mipmap-{dpi}/ic_launcher.png ({size}px)")


if __name__ == "__main__":
    main()
