#!/usr/bin/env python3
"""A share card for each page of /doodles/: one doodle of that kind, drawn at 1200×630.

The /doodles/ pages are the gallery app, so a link to one showed the same card.jpg
whatever it held. This draws one doodle per category~kind from the repository
(data/doodles/, with the drawing code its version was made by) with headless Chrome
→ assets/doodles-cards/<category>~<kind>.jpg, and one per category from its first
kind. doodlerepo_layer.emit copies them to docs/doodles/cards/ and names each in
its page's og:image. Redraws only cards that are missing unless --all.

    python3 make_doodle_cards.py [--all] [category~kind ...]
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

import doodlerepo_layer as R
from make_og_cards import find_chrome

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "doodles-cards"
W, H, SHOT_H = 1200, 630, 800


def picks():
    """{category~kind: (id, row, params, rank)}: the newest live doodle of each kind (the newest gone one when
    none is live), and each category's first kind."""
    vers, gone, params = R.load()
    best = {}
    for i, vs in vers.items():
        last = vs[-1]
        k = last["c"] + "~" + (last.get("sub") or "")
        rank = (i not in gone, last["d"], i)   # a live doodle first, then the newest
        if k not in best or rank > best[k][3]:
            best[k] = (i, last, params.get(last["ph"]), rank)
    for k in sorted(best):
        c = k.split("~")[0]
        best.setdefault(c + "~", best[k])
    return best


def page(row_id, row, p, engine):
    return ("<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#000}canvas{display:block}</style>"
            "<canvas id=c width=%d height=%d></canvas><script>%s</script><script>"
            "var cv=document.getElementById('c');cv._dpr=1;"
            "MDREPO.draw(cv,%s,4000,null);</script>"
            % (W, H, engine, json.dumps({"id": row_id, "c": row["c"], "p": p})))


def main(args):
    redo = "--all" in args
    want = [a for a in args if not a.startswith("--")]
    chrome = find_chrome()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="doodle-cards-"))
    made = 0
    for k, (i, row, p, _) in sorted(picks().items()):
        dest = OUT / (k + ".jpg")
        if (want and k not in want) or (dest.exists() and not redo and not want):
            continue
        eng = R.STORE / "engines" / (row["e"] + ".js")
        if not eng.exists():
            print(k, "— no drawing code", row["e"])
            continue
        src, shot = tmp / "d.html", tmp / "d.png"
        src.write_text(page(i, row, p, eng.read_text()), encoding="utf-8")
        subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                        "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, SHOT_H),
                        "--screenshot=" + str(shot), src.as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Image.open(shot).crop((0, 0, W, H)).convert("RGB").save(dest, quality=82, optimize=True)
        made += 1
        print(k, "→", dest.relative_to(ROOT), dest.stat().st_size // 1024, "kB")
    shutil.rmtree(tmp, ignore_errors=True)
    print(made, "cards drawn")


if __name__ == "__main__":
    main(sys.argv[1:])
