#!/usr/bin/env python3
"""publish/searchcore.js and assets/searchcore.js are one engine, two wrappings.

Both are written by search-core/sync.py from search-core/searchcore.js: assets/
gets the CommonJS copy build.py folds into md.js, publish/ gets the ES module
the site Worker imports (publish/edgesearch.js). The Worker answers
/api/v1/search and the page repaints over its rows, so a drift between the two
copies is a first paint that disagrees with the answer drawn a second later.

The ES copy is the CommonJS copy with the `module.exports` line taken out and
the export footer added, and nothing else. Both open with sync.py's
generated-file banner.

Run:  /usr/bin/python3 tests/test_searchcore_sync.py
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "searchcore.js"
PUBLISH = ROOT / "publish" / "searchcore.js"

# sync.py's own constants when the sibling checkout is here, so this test
# follows a change to the footer instead of going stale on it; the copies
# below are what sync.py held on 2026-09-11.
CJS_LINE = ("if (typeof module !== 'undefined' && module.exports) "
            "module.exports = SEARCHCORE;\n")
ESM_FOOTER = (
    "\nexport default SEARCHCORE;\n"
    "export { norm, loose, edits, slack, hasThai, Segmenter, Thesaurus,\n"
    "         SearchCore, Index, parseIntent, INTENT_RULES };\n"
)
BANNER_HEAD = "// GENERATED FILE — do not edit here.\n"

_sync = ROOT.parent / "search-core" / "sync.py"
if _sync.exists():
    _spec = importlib.util.spec_from_file_location("_sc_sync", _sync)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    CJS_LINE, ESM_FOOTER = _mod.CJS_LINE, _mod.ESM_FOOTER

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  " + name)
    else:
        failures.append(name)
        print("  FAIL " + name + (" — " + detail if detail else ""))


a = ASSETS.read_text()
p = PUBLISH.read_text()

check("assets/searchcore.js opens with the generated-file banner",
      a.startswith(BANNER_HEAD))
check("publish/searchcore.js opens with the generated-file banner",
      p.startswith(BANNER_HEAD))
check("assets/ carries the CommonJS export exactly once", a.count(CJS_LINE) == 1)
check("publish/ carries no CommonJS export", CJS_LINE not in p)
check("publish/ ends with the ES export footer", p.endswith(ESM_FOOTER))

want = a.replace(CJS_LINE, "") + ESM_FOOTER
if p != want:
    # The first line that differs, so a failure says where to look.
    wl, pl = want.splitlines(), p.splitlines()
    n = next((i for i, (x, y) in enumerate(zip(wl, pl)) if x != y),
             min(len(wl), len(pl)))
    got = pl[n] if n < len(pl) else "<end of file>"
    exp = wl[n] if n < len(wl) else "<end of file>"
    detail = "line %d: publish has %r, assets implies %r" % (n + 1, got[:80], exp[:80])
else:
    detail = ""
check("the two differ only by the CommonJS line and the ES footer", p == want,
      detail + " — run search-core/sync.py")

print()
if failures:
    print("%d check(s) failed" % len(failures))
    sys.exit(1)
print("all good — publish/searchcore.js is assets/searchcore.js as an ES module")
