#!/usr/bin/env python3
"""Wire the two-file index into build.py, by anchor.

    python3 importers/apply_indexsplit_hook.py --check
    python3 importers/apply_indexsplit_hook.py

Nan, 2026-09-08: *"1.5 mb before an answer is a problem that needs fixed."*
This is the client-side half of that — the cheap wins and the split, both
measured in indexsplit_layer.py's docstring, both worth 498 KB of 1,564 KB
together. It is a trim and the module says so; the fix is /api/v1.

WHY A SCRIPT, AND WHY EVERY EDIT HAS MORE THAN ONE ANCHOR. build.py is edited
by several sessions a day — while this was being written its mtime moved four
times and a `trades_layer` appeared in the middle of a line another hook was
aiming at. So each edit below lists CANDIDATE anchors and takes the first that
matches exactly once. Two of them exist because
`importers/apply_rowline_hook.py` may or may not have run first: the two hooks
touch the same two lines and must compose in either order.

WHAT IT WIRES
  A. indexsplit_layer imported and its JS appended to md.js beside MDROW's.
     No sheet: an earlier cut of the split needed a rule to reserve the second
     line's height, and then the cut moved so that nothing is ever missing.
  B. data/index.json is written in two parts — index.json (what answers) and
     index2.json (what draws), aligned by position — and the build log says
     what the change was worth in the bytes a reader actually pays.
  C. md.js's loadIndex() hands the first file straight to search and lets the
     second arrive on its own. A failed or slow second file costs the detail
     line, never the answer.

AFTER APPLYING:
    python3 tests/test_indexsplit.py
    python3 tests/test_rowline.py
    then a scratch build, then MD_DOCS=<scratch> python3 tests/test_index_weight.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build.py"

IDX_WRITE_ANCHOR = '''    (DOCS / "data" / "index.json").write_text(
        json.dumps(search_index, ensure_ascii=False))
'''
IDX_WRITE_NEW = '''    # THE INDEX IN TWO FILES (indexsplit_layer.py). The first answers, the
    # second draws — eleven fields that only matter once a row is on screen,
    # aligned to the first by POSITION so they cost no keys. Nan, 2026-09-08:
    # "1.5 mb before an answer is a problem that needs fixed."
    _idx_head, _idx_tail = indexsplit_layer.split(search_index)
    (DOCS / "data" / "index.json").write_text(
        json.dumps(_idx_head, ensure_ascii=False))
    (DOCS / "data" / "index2.json").write_text(
        json.dumps(_idx_tail, ensure_ascii=False))
    # Reported, never enforced. A number in a log is information; the same
    # number in an `if` is a rule nobody agreed to.
    print(indexsplit_layer.report(search_index, _idx_head, _idx_tail))
'''

LOAD_ANCHOR = ("async function loadIndex(){const r=await fetch(RROOT+"
               "'data/index.json');return r.json();}\n")
LOAD_NEW = (
    "// The index arrives in two parts. This returns the first the moment it\n"
    "// parses — the answer does not wait on the second — and MDIDX merges the\n"
    "// second in when it lands, then repaints the detail line and the 📍 on\n"
    "// the rows already drawn. A field that has not ARRIVED is never read as a\n"
    "// field the record does not HAVE: see indexsplit_layer.py.\n"
    "async function loadIndex(){const r=await fetch(RROOT+'data/index.json');\n"
    "const idx=await r.json();\n"
    "return window.MDIDX?window.MDIDX.fill(idx,RROOT):idx;}\n"
)

# (name, [candidate anchors], replacement built from the winning anchor, marker)
EDITS = [
    ("import indexsplit_layer",
     ["import refine_layer\nimport rowline_layer\n", "import refine_layer\n"],
     lambda a: a + "import indexsplit_layer\n",
     "import indexsplit_layer"),

    ("the index is written in two files",
     [IDX_WRITE_ANCHOR],
     lambda a: IDX_WRITE_NEW,
     "indexsplit_layer.split(search_index)"),

    ("loadIndex takes the first file and lets the second follow",
     [LOAD_ANCHOR],
     lambda a: LOAD_NEW,
     "window.MDIDX.fill(idx,RROOT)"),

    ("MDIDX rides in md.js beside MDROW",
     ['    (DOCS / "md.js").write_text(JS + "\\n" + rowline_layer.JS)\n',
      '    (DOCS / "md.js").write_text(JS)\n'],
     lambda a: a.rstrip("\n").replace(")\n", "")
     .replace('write_text(JS + "\\n" + rowline_layer.JS)',
              'write_text(JS + "\\n" + rowline_layer.JS + "\\n" + indexsplit_layer.js())')
     .replace('write_text(JS)',
              'write_text(JS + "\\n" + indexsplit_layer.js())') + "\n",
     "indexsplit_layer.js())"),

    # (An eleventh edit hashed md.js into MD_JS_V. The ?v= hashes were
    # dropped on 2026-09-10 — publish/worker.js revalidates css/js instead —
    # and MD_JS_V went with them.)
]


def apply(check):
    """Every edit or none. A half-split index is a site that answers nothing."""
    s = BUILD.read_text()
    done, todo, bad = [], [], []
    for name, anchors, build_new, marker in EDITS:
        if marker in s:
            done.append(name)
            continue
        hit = [a for a in anchors if s.count(a) == 1]
        if not hit:
            counts = ", ".join(str(s.count(a)) for a in anchors)
            bad.append(f"{name} — no candidate anchor matched once (counts: {counts})")
            continue
        a = hit[0]
        s = s.replace(a, build_new(a))
        todo.append(name + ("" if a is anchors[0] else "  [fallback anchor]"))
    for x in done:
        print(f"  = already wired: {x}")
    for x in todo:
        print(f"  + {x}")
    for x in bad:
        print(f"  ! {x}")
    if bad:
        print("\nREFUSED — nothing written.")
        return 1
    if not todo:
        print("\nnothing to do.")
        return 0
    if check:
        print(f"\n--check: {len(todo)} edits would be made, nothing written.")
        return 0
    BUILD.write_text(s)
    print("\nwrote build.py. Now:\n"
          "  python3 tests/test_indexsplit.py\n"
          "  python3 tests/test_rowline.py\n"
          "then a scratch build.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    sys.exit(apply(ap.parse_args().check))
