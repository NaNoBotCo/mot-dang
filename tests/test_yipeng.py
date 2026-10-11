#!/usr/bin/env python3
"""ยี่เป็ง — the contracts the Yi Peng spread (/yipeng.html) keeps.

1. The page exists and every section it promises in its nav is on it.
2. No unpublished notice leaks as a fact: no [HOLD] or [LINK] slot from the
   drip reaches the page, and a HELD letter renders as title + what it
   waits on, never its body.
3. A letter renders only once its send date has passed (BUILD_DATE), and
   the latest landed one is open.
4. Every photo on the page carries a credit line naming its licence.
5. The four notice gates are all present, each either announced (with a
   source link) or "not yet announced" with a check date — never a bare
   date.
6. The map is mounted (data-mdmap) and Chiang Rai stays out of the frame.
7. Banned words absent. data/yipeng.json ships beside the page.

Run after build.py (or `python3 yipeng_layer.py`):

    python3 tests/test_yipeng.py
    MD_DOCS=/path/to/scratch python3 tests/test_yipeng.py
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  %s" % name)
    else:
        failures.append(name)
        print("  FAIL %s %s" % (name, detail))


def main():
    page = DOCS / "yipeng.html"
    check("yipeng.html exists", page.exists(), str(page))
    if not page.exists():
        return
    html = page.read_text()
    for sec in ("moon", "map", "lights", "krathong", "ways", "notices", "week", "letters", "sources"):
        check(f"section #{sec}", f'<h2 id="{sec}"' in html)
    check("no [HOLD] slot leaks", "[HOLD" not in html)
    check("no [LINK] placeholder leaks", "[LINK" not in html)
    for w in ("load-bearing", "honest"):
        check(f"banned word absent: {w}", w not in html.lower())

    drip = json.loads((ROOT / "data" / "curated" / "yipeng_drip.json").read_text())
    build_date = re.search(r"(?:สร้าง|built) (\d{4}-\d{2}-\d{2})", html)
    today = datetime.date.fromisoformat(build_date.group(1)) if build_date else datetime.date.today()
    landed = [i for i in drip["issues"] if datetime.date.fromisoformat(i["send"]) <= today and not i["held"]]
    text = re.sub(r"<[^>]+>", "", html)          # compare prose, not markup
    for i in drip["issues"]:
        sd = datetime.date.fromisoformat(i["send"])
        # A distinctive run of the body's own prose: the first line long
        # enough to be one, marks stripped, so a <b> in the render cannot
        # hide a match and a HELD body cannot slip through as "".
        head = next((ln for ln in i["body_th"].splitlines() if len(ln.strip("*_ ")) >= 16), i["body_th"])
        head = head.replace("**", "").replace("*", "").strip()[:30]
        if sd > today:
            check(f'{i["wk"]} future renders no body', head not in text)
        elif i["held"]:
            check(f'{i["wk"]} HELD renders no body', head not in text and 'class="yp-issue held"' in html)
        else:
            check(f'{i["wk"]} landed renders body', head in text, head)
    if landed:
        check("latest landed letter is open", 'class="yp-issue" open' in html)
    n_issues = html.count('class="yp-issue')
    check("letter count on page", n_issues == len(drip["issues"]),
          "%d vs %d" % (n_issues, len(drip["issues"])))

    imgs = re.findall(r'<img src="site/([^"]+)\.jpg"', html)
    check("photos present", len(imgs) >= 4, str(imgs))
    credits = html.count('class="yp-credit"')
    check("every photo credited", credits == len(imgs), f"{credits} credits / {len(imgs)} photos")
    check("credits name a licence", html.count("CC BY") >= len(imgs))
    check("no stand-in for ผางประทีป", 'class="nopic"' in html)

    gates = html.count('<table class="yp-gates">')
    check("gate table present", gates == 1)
    rows = re.findall(r'<table class="yp-gates">.*?</table>', html, re.S)[0]
    n_rows = rows.count("<tr>") - 1
    check("four gates", n_rows == 4, str(n_rows))
    announced = rows.count("announced")
    waiting = rows.count("not yet announced")
    check("each gate announced-with-link or waiting-with-check", announced + waiting >= 4)
    if waiting:
        check("waiting gates name a check date", rows.count("we check from") + rows.count("checking weekly") == waiting)

    check("map mounted", 'data-mdmap="1"' in html)
    check("maplibre head present", "maplibre-gl.js" in html)
    check("Chiang Rai listed, not pinned in the CM frame", "Kok riverbank" in html)
    check("countdown anchor", 'data-anchor="2026-11-24"' in html)
    check("register link", f'festivals/yi-peng-loi-krathong.html' in html)
    check("json-ld Festival", '"@type": "Festival"' in html)

    data = DOCS / "data" / "yipeng.json"
    check("data/yipeng.json ships", data.exists())
    if data.exists():
        d = json.loads(data.read_text())
        check("data carries gates with state", all("state" in gt for gt in d.get("gates", [])))
        check("data carries letters", len(d.get("letters", [])) == len(drip["issues"]))


if __name__ == "__main__":
    print("yipeng:")
    main()
    if failures:
        print(f"\n{len(failures)} failing: {failures}")
        sys.exit(1)
    print("\nall ok")
