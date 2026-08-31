#!/usr/bin/env python3
"""WO-42 — the sign is up and stays up. Zero network.

The defect this file exists for: readers kept saying "I really like
motdang.net but I don't know how to use it", and the reason was measurable.
what.html — the page written for exactly that reader, six refusals and
fifteen tappable plates — had ZERO inbound links on 2026-08-29. Not in the
header, not in the footer, not on the homepage, not on the 404. It could
only be SENT, and the people saying this had arrived on their own.

A link that nothing enforces is a link the next work order deletes by
accident, so the wiring is a gate rather than a memory:

  THE SIGN     what.html is reachable from the shell itself — the มดแดง
               family of the header and the footer — which puts it on every
               page of the site, and from the hero and the 404 besides.
  THE TEACHER  search.html opened with no query renders the curated panels
               as words to type. It used to render nothing at all: the
               richest instrument on the site taught a hesitating reader
               nothing about itself. WO-43 moved that rendering out of md.js
               and into the served HTML, and guarded the empty query so it
               no longer downloads a 6.2 MB index to answer nobody — so the
               checks below ask for the doors BEFORE any script runs.
  THE TRAIL    a place page's crumbs carry the shelf it stands on, in the
               nav and in the BreadcrumbList, so the way out is the way in.

Nothing here fetches, and nothing here builds the whole site: the shell and
the layers are called directly.

    python3 tests/test_sabai.py
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build            # noqa: E402  (module-level loads; build() not called)

# The 404 check below EMITS a page, and this file takes no build lock. Pointed
# at a throwaway directory it cannot land in docs/ while a real build owns it.
_tmp = tempfile.TemporaryDirectory()
build.DOCS = Path(_tmp.name)

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


# ------------------------------------------------------------- the sign
print("the sign — what.html reachable from the shell, so from every page")
shell = build.page("ทดสอบ · test", "<p>body</p>", depth=0, path="test.html")
svcbar = re.search(r'<div class="svcbar">(.*?)\n  </div>', shell, re.S)
groups = svcbar.group(1).split('<span class="svcgrp">')[1:] if svcbar else []
ants = [g for g in groups if "The ants" in g]
check("the header's five families are intact", len(groups) == 5, len(groups))
check("the มดแดง family carries the door",
      bool(ants) and 'href="what.html"' in ants[0])
check("the footer carries it too (a reader at the bottom is still a reader)",
      shell.count('href="what.html"') >= 2)

deep = build.page("ทดสอบ · test", "<p>body</p>", depth=2, path="cm/p/test.html")
check("a page two levels down reaches it by the right relative root",
      '"../../what.html"' in deep)

# ------------------------------------------------------------ the hero
print("the hero — one line of orientation, and a door on it")
hero = build.hero_html("สารบัญเมือง", "A city directory")
check("the orientation line renders", 'class="herostart"' in hero)
check("its door is what.html", re.search(
    r'class="herostart"(?:(?!</p>).)*?href="what\.html"', hero, re.S) is not None)
check("it is styled — a colour and a size of its own, not inherited",
      ".herostart{" in build.CSS)
check("no popup, no modal, no tour: the intervention is a sentence",
      not re.search(r"herostart[^}]*position:\s*fixed", build.CSS))

# --------------------------------------------------------------- the 404
print("the 404 — the reader who mistyped is also a reader who is new")
build.build_notfound_page()
nf = (build.DOCS / "404.html").read_text()
check("the first-time line points at what.html", 'href="/what.html"' in nf)

# ------------------------------------------------------------ the teacher
# WO-43 moved this from md.js into the served HTML. The old checks asked
# whether the SCRIPT could draw the doors; these ask the stronger thing —
# that the doors are in the page before a script runs at all.
print("the teacher — search.html with no query, served not scripted")
panels_doc = json.loads(
    (ROOT / "data" / "curated" / "search_panels.json").read_text())
start = build.search_start_html(panels_doc)
check("the start state is rendered at build time", 'class="richdoor"' in start)
check("every panel that can supply a word becomes a pill",
      start.count('class="pdoor"') == len(panels_doc["panels"]),
      f'{start.count(chr(34)+"pdoor"+chr(34))} pills')
check("the pills are search queries, so a tap fills the box and opens a card",
      "search.html?q=" in start)
check("their terms are url-encoded (they are Thai)", "%E0%B8" in start)
check("the start state also offers what.html to a reader who is more lost",
      'href="what.html"' in start)
check("its bilingual pairs go through bi(), so the language toggle reaches it",
      'class="bi"' in start)

js = build.JS
check("md.js GUARDS the empty query — no index fetch for a reader who typed nothing",
      re.search(r"if\(!q\)return;\s*(//[^\n]*\n\s*)*const idx=await loadIndex\(\)",
                js) is not None)
check("the dead client-side start state is gone", "const start=()=>" not in js)
check("a real query still gets the panel and the no-hit doors",
      "panelHtml+doors()" in js)

print("every curated panel can supply a word to type")
panels = json.loads(
    (ROOT / "data" / "curated" / "search_panels.json").read_text())["panels"]
mute = [p["id"] for p in panels
        if not ((p.get("variants") or []) + (p.get("query") or []))]
check(f"all {len(panels)} panels carry a variant or a query", not mute, mute)
check("and every one of them carries the bilingual title the pill shows",
      all(isinstance(p.get("title"), list) and len(p["title"]) == 2
          for p in panels))

# -------------------------------------------------------------- the trail
print("the trail — the shelf is a rung, not only a table row")
prov = build.PROVINCES[0]
rec = next((r for r in build.load()[prov["key"]]
            if any(c in build.CATS for c in r.get("cat", []))), None)
if rec is None:
    check("a record with a known shelf exists to test", False)
else:
    cat = next(c for c in rec["cat"] if c in build.CATS)
    html = build.detail_page(rec, prov)
    crumbs = re.search(r'<nav class="crumbs">(.*?)</nav>', html, re.S)
    check("the crumb nav renders", crumbs is not None)
    trail = crumbs.group(1) if crumbs else ""
    check("it carries four rungs, home › province › shelf › place",
          trail.count("›") == 3, trail.count("›"))
    check("the shelf rung links where the หมวด row has always linked",
          f'href="../{cat}/index.html"' in trail)
    ld = [json.loads(m) for m in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
    bc = next((d for d in ld if d.get("@type") == "BreadcrumbList"), None)
    check("the machine reader gets the same four rungs", bc is not None
          and len(bc["itemListElement"]) == 4, bc and len(bc["itemListElement"]))
    check("and the shelf rung is an absolute URL it can follow",
          bc is not None
          and bc["itemListElement"][2]["item"].endswith(f"/{cat}/index.html"))

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all sabai checks passed")
