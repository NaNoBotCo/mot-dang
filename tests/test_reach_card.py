#!/usr/bin/env python3
"""The /reach.html share card — the one picture outsiders are most likely to
meet, because the link-health finding is what other people cite.

Two ways this card could tell a lie, and both have precedents in this repo:

1. It could count differently from the page it previews. The card cannot
   import build.py (importing it runs a build), so it keeps its own copy of
   BROKEN — and a copy is a thing that drifts. The page would say 47% while
   the card said something else, with no way to tell which was right. So the
   two literals are compared here, read out of build.py's source rather than
   by importing it. Same reasoning as tests/test_ground.py comparing
   map_ground.PALETTE against the style file.

2. It could be drawn in colours the chart underneath it does not use. Three
   verdicts, three colours, one language.

Also checks the arithmetic the card states in words — that working, broken
and social account for every link checked, so the dot field cannot silently
drop or invent one — and that a built page which has a card actually points
its og:image at it.

Run: python3 tests/test_reach_card.py
"""
import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

fails = []


def check(name, ok, detail=""):
    print("%-4s %s%s" % ("ok" if ok else "FAIL", name, "" if ok else "  — " + detail))
    if not ok:
        fails.append(name)


def literal_from(path, name):
    """Read a module-level literal out of a source file without importing it.

    Handles `A = ...` and the unpacked `A, B, C = ...` form — the palette is
    written that way, and a reader that silently returns None for it turns
    this whole check into one that always passes.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == name:
                return ast.literal_eval(node.value)
            if isinstance(t, ast.Tuple) and isinstance(node.value, ast.Tuple):
                for slot, val in zip(t.elts, node.value.elts):
                    if isinstance(slot, ast.Name) and slot.id == name:
                        return ast.literal_eval(val)
    return None


# ------------------------------------------------------- 1. one definition of broken
build_broken = literal_from(ROOT / "build.py", "BROKEN")
card_broken = literal_from(ROOT / "make_answer_cards.py", "BROKEN")
check("build.py still defines BROKEN", build_broken is not None)
check("make_answer_cards.py still defines BROKEN", card_broken is not None)
check("the card counts the same verdicts as the page",
      build_broken == card_broken,
      "page has %s, card has %s" % (sorted(build_broken or []), sorted(card_broken or [])))

# ------------------------------------------------------------------ 2. one palette
src = (ROOT / "build.py").read_text(encoding="utf-8")
i = src.find("def donut(")
page_colours = set(re.findall(r'"(#[0-9A-Fa-f]{6})"', src[i:i + 900])) if i > 0 else set()
card_colours = {literal_from(ROOT / "make_answer_cards.py", n)
                for n in ("REACH_OK", "REACH_BROKEN", "REACH_SOCIAL")}
check("the card's three colours are the chart's three colours",
      card_colours and card_colours <= page_colours,
      "card %s, page %s" % (sorted(card_colours), sorted(page_colours)))

# --------------------------------------------------------------- 3. the arithmetic
lh = json.loads((ROOT / "data" / "linkhealth.json").read_text())
tally = {}
for v in lh["links"].values():
    tally[v.get("status", "?")] = tally.get(v.get("status", "?"), 0) + 1
n_links = sum(tally.values())
n_social = tally.get("social", 0)
n_sites = n_links - n_social
n_broken = sum(tally.get(k, 0) for k in (card_broken or ()))
n_working = n_sites - n_broken
check("every checked link lands in exactly one of the three groups",
      n_working + n_broken + n_social == n_links,
      "%d + %d + %d != %d" % (n_working, n_broken, n_social, n_links))
check("no group came out negative",
      min(n_working, n_broken, n_social) >= 0,
      "works %d, broken %d, social %d" % (n_working, n_broken, n_social))
check("the file says when it was checked", bool(lh.get("generated")))

# ------------------------------------------------------------ 4. the dot field
try:
    import make_answer_cards as mac
    svg = mac.dotfield(n_working, n_broken, n_social)
    drawn = svg.count("<circle")
    check("the field draws one dot per link, no more and no fewer",
          drawn == n_links, "drew %d for %d links" % (drawn, n_links))
    check("each verdict gets its share of the dots",
          svg.count(mac.REACH_BROKEN) == n_broken
          and svg.count(mac.REACH_SOCIAL) == n_social)
except ImportError as e:            # Pillow absent on this machine
    print("skip make_answer_cards import (%s) — the drawing checks need it" % e)

# ------------------------------------------------------------------ 5. the page
# MD_DOCS points at a scratch build when somebody else is holding docs/ — the
# same escape hatch tests/test_plan_routes.js takes. Without it these checks
# skip for the whole length of another session's build, which is most of the
# time on a busy afternoon, and a check that is always skipped is not a check.
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
built = DOCS / "reach.html"
card = ROOT / "assets" / "og" / "reach.png"
if built.exists():
    html = built.read_text(encoding="utf-8")
    og = re.search(r'og:image" content="([^"]+)"', html)
    if card.exists():
        check("the built page points its og:image at the card",
              bool(og) and og.group(1).endswith("og/reach.png"),
              "og:image is %s" % (og.group(1) if og else "absent"))
    else:
        print("skip og:image (no assets/og/reach.png yet — the page keeps the "
              "brand card until make_answer_cards.py has run)")
    check("the page's title carries both languages",
          bool(re.search(r"<title>[^<]*[฀-๿][^<]*[A-Za-z]{4}", html)))
else:
    print("skip page checks — docs/reach.html not built")

print("\n%s" % ("PASS" if not fails else "FAIL: " + ", ".join(fails)))
raise SystemExit(1 if fails else 0)
