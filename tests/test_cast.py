#!/usr/bin/env python3
"""The cast avatars hold together when a platform crops them.

    python3 tests/test_cast.py

No build, no browser. Checks what make_cast.py draws, not the PNGs:

1. Every avatar and the bug is well-formed SVG with a bilingual <title>.
2. The comb's top and both mustache tips land inside the inscribed circle,
   so Facebook's and Instagram's round crop takes background only.
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import make_cast  # noqa: E402


def placed(x, y):
    # the avatar's character transform: translate(512 540) scale(1.14) translate(-512 -500)
    return 512 + 1.14 * (x - 512), 540 + 1.14 * (y - 500)


def main():
    fails = []
    for e in make_cast.EXPRS:
        svg = make_cast.avatar_svg(e)
        root = ET.fromstring(svg)
        t = root.find("{http://www.w3.org/2000/svg}title")
        if t is None or "/" not in (t.text or ""):
            fails.append(f"{e}: no bilingual <title>")
    ET.fromstring(make_cast.bug_svg())
    # comb top (100 + its 36 px drop), mustache tips (782 and its mirror, 546)
    for label, (x, y) in {"comb top": (512, 136), "right tip": (782, 546),
                          "left tip": (242, 546)}.items():
        px, py = placed(x, y)
        r = math.hypot(px - 512, py - 512)
        if r > 500:
            fails.append(f"{label} at r={r:.0f} falls outside the round crop")
    for f in fails:
        print("FAIL", f)
    print("ok" if not fails else f"{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
