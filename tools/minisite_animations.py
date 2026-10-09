#!/usr/bin/env python3
"""Her minisites that animate, and which of them the doodle library has taken in (Nan, 2026-10-02:
"anytime we do a minisite with animations, grab those too").

Looks through every project in ~/Developer/claude code projects/ for a published page (index.html at
the root, or in docs/, out/site/ or build/site/) whose own scripts draw on a canvas or SVG frame by frame
(requestAnimationFrame, <animate>, CSS keyframes on drawn shapes). data/curated/minisite_harvest.json
records each one: harvested (into which doodle), or left out and why. New ones come back as pending.

    python3 tools/minisite_animations.py            # the pending list
    python3 tools/minisite_animations.py --all      # every animated minisite and its state
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = Path.home() / "Developer/claude code projects"
LEDGER = ROOT / "data/curated/minisite_harvest.json"
PAGES = ("index.html", "docs/index.html", "out/site/index.html", "build/site/index.html", "site/index.html")
MOVES = re.compile(r"requestAnimationFrame|<animate\b|<animateTransform|@keyframes", re.I)
DRAWS = re.compile(r"getContext\(\s*['\"]2d|<canvas|<svg", re.I)


def animated(project):
    """The page and the script files that make it move, or None."""
    for rel in PAGES:
        page = project / rel
        if not page.exists():
            continue
        texts = [page.read_text(errors="ignore")]
        for src in re.findall(r'<script[^>]+src="([^"]+\.js)"', texts[0]):
            f = (page.parent / src).resolve()
            if f.is_file() and PROJECTS in f.parents:
                texts.append(f.read_text(errors="ignore"))
        allt = "\n".join(texts)
        if MOVES.search(allt) and DRAWS.search(allt):
            return str(page.relative_to(PROJECTS))
    return None


def main(a):
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"sites": {}}
    rows = []
    for p in sorted(x for x in PROJECTS.iterdir() if x.is_dir() and not x.name.startswith(".")):
        if p.name == "mot-dang":
            continue
        page = animated(p)
        if not page:
            continue
        st = led["sites"].get(p.name) or {"state": "pending"}
        rows.append((p.name, page, st))
    for name, page, st in rows:
        if "--all" in a or st["state"] == "pending":
            print("%-28s %-10s %s" % (name, st["state"], st.get("doodle") or st.get("why") or page))
    if "--all" not in a:
        print(sum(1 for r in rows if r[2]["state"] == "pending"), "pending of", len(rows), "animated minisites")


if __name__ == "__main__":
    main(sys.argv[1:])
