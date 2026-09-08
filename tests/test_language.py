#!/usr/bin/env python3
"""The language toggle: that it works, and that the page does not flash.

WHAT WENT WRONG, MEASURED ON THE LIVE SITE 2026-09-08 (Nan and Michael: "the
language toggle on motdang.net fails a lot"):

  * `<body>` shipped with no class, and the stored choice was applied by
    md.js — 248 KB, and the LAST tag on every page. A reader who had chosen
    English got a fully painted bilingual page first and the switch after it,
    on every navigation. On the connections this site is for, that is seconds.
  * 408 Thai runs and 966 Latin runs across 59 sampled pages sat outside any
    `.th`/`.en` span, so they showed identically in all three modes.
  * bi("API", "API") printed "API · API".

The fixes are cheap and each of them is one line away from coming back, so
each of them is a check here.

    python3 tests/test_language.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FAIL = []
SRC = open(os.path.join(ROOT, "build.py"), encoding="utf-8").read()


def want(cond, why):
    if not cond:
        FAIL.append(why)


# ---------------------------------------------------------------------------
# 1. Before first paint, on <html>, or it flashes
# ---------------------------------------------------------------------------
head = SRC[SRC.find("<html lang=\"th\""):SRC.find("{extra_head}</head>")]
want("md-lang" in head,
     "the head has no inline script reading md-lang — the choice is applied "
     "after paint again, which is the flash this file exists to stop")
want("classList.add('lang-" in head or 'classList.add("lang-' in head,
     "the head script does not add a lang class")
want('class="lang-both"' in SRC[:SRC.find("</head>") + 200] or
     '<html lang="th" class="lang-both"' in SRC,
     "the served <html> carries no lang-both — a reader with scripts off "
     "gets Thai only, when the site's default is both")

# The class must be on <html>: <body> does not exist while the head runs.
want("html.lang-" in SRC, "no html.lang- rules in the stylesheet")
want("body.lang-" not in SRC,
     "a body.lang- selector is back; the pre-paint script cannot reach <body>")
want("const B=document.documentElement" in SRC,
     "md.js sets the language on document.body again")

# ---------------------------------------------------------------------------
# 2. Nothing may hide or show a language except through a lang class
# ---------------------------------------------------------------------------
css = "\n".join(re.findall(r'"""(.*?)"""', SRC, re.S))
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)      # a comment is not a selector
for m in re.finditer(r"([^{}\n][^{}]*)\{([^{}]*)\}", css):
    sel, decl = m.group(1).strip(), m.group(2)
    if "display" not in decl:
        continue
    if not re.search(r"\.(th|en)\b", sel):
        continue
    if "lang-" in sel or ".solo" in sel:
        continue
    if sel.strip() in (".en",) or ">.th" in sel:
        continue                                   # the base rule, and the separator
    FAIL.append(f"unguarded display rule on a language span: {sel!r} {{{decl.strip()[:60]}}}")

# ---------------------------------------------------------------------------
# 3. A word that is the same in both languages prints once
# ---------------------------------------------------------------------------
sys.path.insert(0, ROOT)
os.environ.setdefault("MD_NO_BUILD", "1")
_bi = re.search(r"def bi\(th, en.*?\n(?=\ndef )", SRC, re.S)
want(_bi and "th.strip() == en.strip()" in _bi.group(0),
     'bi() no longer collapses an identical pair — "API · API" is back')

# ---------------------------------------------------------------------------
# 4. On the built pages, if there are any
# ---------------------------------------------------------------------------
THAI = re.compile(r"[฀-๿]")
docs = os.path.join(ROOT, "docs")
pages = sorted(glob.glob(os.path.join(docs, "cm", "p", "*.html")))[:200]
if pages:
    no_class = [p for p in pages
                if '<html lang="th" class="lang-both"' not in open(p, encoding="utf-8").read()]
    want(not no_class,
         f"{len(no_class)} built page(s) ship without class=\"lang-both\" on <html>")

    # A <dd> whose whole value is Thai with no language span is a value the
    # toggle cannot reach and an English reader cannot read.
    bare = []
    for p in pages:
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r"<dd[^>]*>(.*?)</dd>", s, re.S):
            body = m.group(1)
            txt = re.sub(r"<[^>]+>", "", body)
            if THAI.search(txt) and 'class="th' not in body and 'class="bi"' not in body:
                bare.append((os.path.basename(p), txt.strip()[:40]))
    if bare:
        FAIL.append(f"{len(bare)} <dd> value(s) print Thai with no language mark, "
                    f"e.g. {bare[:3]}")
    print(f"  checked {len(pages)} built place pages")
else:
    print("  built pages: skipped — docs/cm/p is empty")

# ---------------------------------------------------------------------------
if FAIL:
    print(f"\nFAIL — {len(FAIL)} problem(s):\n")
    for f in FAIL:
        print("  *", f)
    sys.exit(1)
print("OK — the toggle is applied before paint and every language span is guarded")
