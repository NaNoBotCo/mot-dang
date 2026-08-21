#!/usr/bin/env python3
"""Launcher icon: the view's own arrow, amber on black.

The icon is the thing she taps with gloves on at the start of a ride, so it is
the arrow and nothing else — same shape and same amber as the screen it opens,
drawn from primitives rather than a font so there is nothing to depend on.
Writes every mipmap density the manifest asks for.
"""
import pathlib

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "android" / "res"

BLACK = (0, 0, 0, 255)
AMBER = (255, 176, 32, 255)

DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
S = 8  # supersample


def draw_icon(size):
    n = size * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = n * 0.22
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=r, fill=BLACK)
    # a hairline rim so the icon has an edge on a black launcher wallpaper,
    # where a black square would otherwise be a hole
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=r,
                        outline=(255, 176, 32, 70), width=max(1, n // 90))
    # the arrow, the same proportions as the path in index.html
    cx, cy, k = n / 2.0, n / 2.0, n * 0.0072
    d.polygon([(cx + 0 * k, cy - 38 * k), (cx + 30 * k, cy + 26 * k),
               (cx + 0 * k, cy + 10 * k), (cx - 30 * k, cy + 26 * k)],
              fill=AMBER)
    return img.resize((size, size), Image.LANCZOS)


def main():
    for name, size in DENSITIES.items():
        out = RES / f"mipmap-{name}"
        out.mkdir(parents=True, exist_ok=True)
        draw_icon(size).save(out / "ic_launcher.png")
        print(f"  mipmap-{name}/ic_launcher.png  {size}x{size}")


if __name__ == "__main__":
    main()
