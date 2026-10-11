#!/usr/bin/env python3
"""A still of each cover doodle, for pages without a picture of their own.

Draws every kind in assets/front/doodles.js once, at 1200×630, with headless
Chrome (the drawings are canvas code) → assets/doodles/<kind>.png. No moon in
a still: tonight's moon is wrong on any other night. front_layer.bake copies
them to docs/front/doodles/ (doodles_layer.copy).

    python3 make_doodle_stills.py [kind ...]
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

import doodles_layer
from make_og_cards import find_chrome

ROOT = Path(__file__).resolve().parent
W, H, SHOT_H = 1200, 630, 800


def page(kind, ridge):
    # skyline.js (MDSKY, the shared landscape) first when present, as on the page
    js = "\n".join(f.read_text() for f in (ROOT / "assets/front/skyline.js", ROOT / "assets/front/doodler.js", ROOT / "assets/front/doodles.js")
                   if f.exists())
    return ("<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#000}"
            "canvas{display:block}</style><canvas id=c width=%d height=%d></canvas><script>%s</script>"
            "<script>MDDOODLES.draw(%s, document.getElementById('c').getContext('2d'), %d, %d, 4000, null, %s);</script>"
            % (W, H, js, json.dumps(kind), W, H, json.dumps(ridge)))


def main(want):
    ridge_f = ROOT / "docs/front/ridge.json"
    ridge = json.loads(ridge_f.read_text()) if ridge_f.exists() else None
    chrome, out = find_chrome(), doodles_layer.STILLS
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="doodles-"))
    for kind in want or doodles_layer.kinds():
        src, dest = tmp / "d.html", out / (kind + ".png")
        src.write_text(page(kind, ridge), encoding="utf-8")
        subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                        "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, SHOT_H),
                        "--screenshot=" + str(dest), src.as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Image.open(dest).crop((0, 0, W, H)).convert("RGB").save(dest, optimize=True)
        print(kind, "→", dest.relative_to(ROOT), dest.stat().st_size // 1024, "kB")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
