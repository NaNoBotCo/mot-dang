#!/usr/bin/env python3
"""WO-78 — wire THE SECOND LINE into build.py and refine_layer.py, by anchor.

    python3 importers/apply_rowline_hook.py --check    # say what would change
    python3 importers/apply_rowline_hook.py            # apply
    python3 importers/apply_rowline_hook.py --no-index # apply without ph/w

WHY A SCRIPT, AGAIN. build.py was four minutes old and a build had been
running for eighteen when this was written, and refine_layer.py was three
minutes old — two other sessions in the same tree on the same morning. A
line-number diff rots before it can be applied. Every edit below finds its
anchor by TEXT, refuses if the anchor is missing or matches twice, and is
skipped when its result is already in place, so it can be run whenever the
lock is free and run twice without harm.

WHAT IT WIRES (Michael, 2026-09-08: "Records that appear in search / map /
discoverability should not require you to click them to see basic
information… rank/sort results according to tags and your own matching
criteria, without ever leaving the results page… most of the details could fit
on a line or 2… you need basic information about links in order to decide
whether clicking is worth the extra nav effort.")

  A. rowline_layer imported, its sheet folded into style.css, its JS appended
     to md.js, and both hashes taken over the joined text so the change busts
     its own cache.
  B. the result row's chip strip replaced by MDROW.line(): every tag and trade
     tag rather than one, the street AND the district rather than whichever
     came first, today's hours in words, the phone as a tel: link, the shop's
     own page with its host shown, and a +N that folds the rest open IN PLACE.
     The WO-69 three chips stay behind it as the fallback.
  C. `ph` and `w` on the index row — the only two fields on that line the
     index did not already carry. ~2.82 MB measured; --no-index leaves them
     out and the line renders everything else.
  D. refine's sort gains ตรงแท็กมากสุด / most tags matched, which REORDERS by
     how many of the reader's own tag terms a row carries and drops nothing,
     and its ครบที่สุด counts the two new fields.

AFTER APPLYING, before believing any of it:

    python3 tests/test_rowline.py            # 38 checks, no build needed
    python3 tests/test_refine.py             # 48 checks, no build needed
    python3 tests/test_tap.py
    MD_DOCS=<scratch> python3 tests/test_index_weight.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build.py"
REFINE = ROOT / "refine_layer.py"

# ---------------------------------------------------------------- build.py

ROW_ANCHOR = (
    "(ch.length?' <span class=\"rchips\">'+ch.map(c=>`<a class=\"rchip\" "
    "href=\"${RROOT}search.html${c[0]}\">${c[1]}</a>`).join(' ')+'</span>':'')+"
)
ROW_NEW = (
    "// WO-78 — THE SECOND LINE (rowline_layer.py). Everything this row\n"
    "// already held and threw away at render time: every tag and trade tag\n"
    "// rather than one, the street AND the district rather than whichever\n"
    "// came first, today's hours in words rather than only a lamp, the phone,\n"
    "// and the shop's own page. Michael, 2026-09-08: a reader has to be able\n"
    "// to tell from the LIST whether opening a result is worth the nav.\n"
    "// MDROW rides in md.js, so the only way it is missing is a half-written\n"
    "// deploy — in which case the WO-69 three chips are still drawn.\n"
    "(window.MDROW?window.MDROW.line(e,TAB,{root:RROOT})\n"
    ":" + ROW_ANCHOR[:-1] + ")+"
)

IDX_ANCHOR = '                idx_entry["lat"], idx_entry["lng"] = r["lat"], r["lng"]\n'
IDX_NEW = (
    '                idx_entry["lat"], idx_entry["lng"] = r["lat"], r["lng"]\n'
    "            # ☎ and 🌐 — WO-78. The two things on a result line that the\n"
    "            # index did not already carry, and the two a reader uses to\n"
    "            # finish on the list instead of opening the page: 60,921\n"
    "            # records hold a number and 70,730 hold their own page on the\n"
    "            # web, 52,678 of those a Facebook page, which for a Chiang Mai\n"
    "            # shop is very often the first-hand source. Digits only, and\n"
    "            # facebook.com/ stripped to f/ — 2.82 MB measured, against\n"
    "            # 2.05 MB for the address alone, which the street and district\n"
    "            # chips already say.\n"
    "            _ph = rowline_layer.index_phone(r)\n"
    "            if _ph:\n"
    '                idx_entry["ph"] = _ph\n'
    "            _wb = rowline_layer.index_web(r)\n"
    "            if _wb:\n"
    '                idx_entry["w"] = _wb\n'
)

EDITS = [
    # (file, name, anchor, replacement, marker that means "already done")
    (BUILD, "import rowline_layer",
     "import refine_layer\n",
     "import refine_layer\nimport rowline_layer\n",
     "import rowline_layer"),
    # These two used to reach into the CSS chain by naming the layer at the
    # end of it. That chain gains a layer every few days — trades_layer landed
    # in the middle of writing this — so a position in it is an anchor that
    # rots within the hour. Both now APPEND, and neither cares what the chain
    # holds or in what order.
    (BUILD, "the sheet joins style.css's hash",
     ["    _css_all += chr(10) + indexsplit_layer.CSS\n",
      "    MD_CSS_V = f\"{_asset_v(_css_all):08x}\"\n"],
     lambda a: "    _css_all += chr(10) + rowline_layer.CSS\n" + a,
     "_css_all += chr(10) + rowline_layer.CSS"),
    (BUILD, "md.js's version hashes what md.js actually ships",
     ['MD_JS_V = f"{_asset_v(JS):08x}"\n',
      'MD_JS_V = f"{_asset_v(JS + chr(10) + indexsplit_layer.js()):08x}"\n'],
     lambda a: a.replace("_asset_v(JS)", "_asset_v(JS + chr(10) + rowline_layer.JS)")
     .replace("_asset_v(JS + chr(10) + indexsplit_layer.js())",
              "_asset_v(JS + chr(10) + rowline_layer.JS "
              "+ chr(10) + indexsplit_layer.js())"),
     "chr(10) + rowline_layer.JS"),
    (BUILD, "MDROW rides in md.js, and its sheet is appended to style.css",
     ['    (DOCS / "md.js").write_text(JS)\n',
      '    (DOCS / "md.js").write_text(JS + "\\n" + indexsplit_layer.js())\n'],
     lambda a: a.replace('write_text(JS)',
                         'write_text(JS + "\\n" + rowline_layer.JS)')
     .replace('write_text(JS + "\\n" + indexsplit_layer.js())',
              'write_text(JS + "\\n" + rowline_layer.JS '
              '+ "\\n" + indexsplit_layer.js())')
     + '    # WO-78 — appended rather than joined into the CSS chain, for the\n'
       '    # reason in importers/apply_rowline_hook.py: that chain moves.\n'
       '    with (DOCS / "style.css").open("a") as _rl_fh:\n'
       '        _rl_fh.write("\\n" + rowline_layer.CSS)\n',
     '_rl_fh.write("\\n" + rowline_layer.CSS)'),
    (BUILD, "the result row draws the second line", ROW_ANCHOR, ROW_NEW,
     "window.MDROW.line(e,TAB,{root:RROOT})"),
]

INDEX_EDIT = (BUILD, "the index carries ph and w", IDX_ANCHOR, IDX_NEW,
              'idx_entry["ph"] = _ph')

# A dot and a row are the same record seen twice, so a mark carries the same
# two attributes the row does and tap.js's one reader serves both.
MARK_ANCHOR = """    return (' data-mdtap="1" data-n="%s"%s data-lat="%.5f" data-lng="%.5f"'
            ' data-href="%s" data-plan="%s"%s%s' % (
                att(name_text(r)),
                (' data-ne="%s"' % att(en)) if en else "",
                r["lat"], r["lng"], att(href), att(plan_key(r)),
                (' data-rank="%d"' % rank) if rank else "", extra))
"""
MARK_NEW = """    _ph = rowline_layer.index_phone(r) or ""
    _wb = rowline_layer.index_web(r) or ""
    return (' data-mdtap="1" data-n="%s"%s data-lat="%.5f" data-lng="%.5f"'
            ' data-href="%s" data-plan="%s"%s%s%s%s' % (
                att(name_text(r)),
                (' data-ne="%s"' % att(en)) if en else "",
                r["lat"], r["lng"], att(href), att(plan_key(r)),
                (' data-rank="%d"' % rank) if rank else "",
                (' data-ph="%s"' % att(_ph)) if _ph else "",
                (' data-w="%s"' % att(_wb)) if _wb else "", extra))
"""

MARK_EDIT = (BUILD, "a map mark carries the phone and the page too",
             MARK_ANCHOR, MARK_NEW, 'data-ph="%s"')

# ----------------------------------------------------------- refine_layer.py

SORT_ANCHOR = '''    ("full", "ครบที่สุด",    "most complete"),
)
'''
SORT_NEW = '''    ("full", "ครบที่สุด",    "most complete"),
    # WO-78 — the reader's own criteria, applied to the answer in front of
    # them. It counts how many of the tag terms they have actually asked for
    # each row carries, so an OR of two tags puts the rows carrying both on
    # top. It only ever REORDERS: a row carrying none of them scores nought
    # and sorts last, and a row that nobody has tagged is untagged, not
    # disqualified. Offered whether or not a tag is set — with none set every
    # row scores nought and the order is left exactly as it was found.
    ("tags", "ตรงแท็กมากสุด", "most tags matched"),
)
'''

FULLF_ANCHOR = "var FULLF=['e','r','st','ar','t','tt','f','hk','su','kd','lat'];\n"
FULLF_NEW = "var FULLF=['e','r','st','ar','t','tt','f','hk','su','kd','lat','ph','w'];\n"

SORTJS_ANCHOR = """  else if(s==='full')out.sort(function(a,b){return fullness(b)-fullness(a);});
"""
SORTJS_NEW = """  else if(s==='full')out.sort(function(a,b){return fullness(b)-fullness(a);});
  else if(s==='tags'){var want=list(st.u,'tag'),sc={};
    var score=function(e){if(sc[e.id]!=null)return sc[e.id];
      var mine=vals(e,'tag',T),have={},i,n=0;
      for(i=0;i<mine.length;i++)have[mine[i]]=1;
      for(i=0;i<want.length;i++)if(have[want[i]])n++;
      return (sc[e.id]=n);};
    // A stable sort by score alone: rows that tie keep the order the ranker
    // put them in, so this reorders the answer without discarding it.
    out.sort(function(a,b){return score(b)-score(a);});}
"""

REFINE_EDITS = [
    (REFINE, "sort by the tags the reader asked for", SORT_ANCHOR, SORT_NEW,
     '("tags", "ตรงแท็กมากสุด", "most tags matched")'),
    (REFINE, "ครบที่สุด counts the phone and the page", FULLF_ANCHOR, FULLF_NEW,
     "'kd','lat','ph','w']"),
    (REFINE, "the tag sort itself", SORTJS_ANCHOR, SORTJS_NEW, "s==='tags'"),
]


def apply(edits, check):
    """Every edit or none. A half-wired build.py is worse than an unwired one.

    An anchor may be a list of CANDIDATES, and a replacement may be a callable
    taking the winning one. That is not neatness: apply_indexsplit_hook.py
    edits two of the same lines this does, and without candidates the two
    hooks composed in one order and refused in the other — a refusal you can
    only get past by knowing a secret order is a trap, not a safeguard.
    """
    texts, done, todo, bad = {}, [], [], []
    for path, name, anchor, new, marker in edits:
        if path not in texts:
            texts[path] = path.read_text()
        s = texts[path]
        if marker in s:
            done.append(name)
            continue
        cands = anchor if isinstance(anchor, (list, tuple)) else [anchor]
        hit = [a for a in cands if s.count(a) == 1]
        if not hit:
            counts = ", ".join(str(s.count(a)) for a in cands)
            bad.append(f"{path.name}: {name} — no anchor matched once "
                       f"(counts: {counts})")
            continue
        a = hit[0]
        texts[path] = s.replace(a, new(a) if callable(new) else new)
        todo.append(f"{path.name}: {name}"
                    + ("" if a is cands[0] else "  [fallback anchor]"))
    for line in done:
        print(f"  = already wired: {line}")
    for line in todo:
        print(f"  + {line}")
    for line in bad:
        print(f"  ! {line}")
    if bad:
        print("\nREFUSED — nothing written. An anchor moved; read the file and "
              "re-aim before running again.")
        return 1
    if not todo:
        print("\nnothing to do.")
        return 0
    if check:
        print(f"\n--check: {len(todo)} edits would be made, nothing written.")
        return 0
    for path, s in texts.items():
        path.write_text(s)
    print(f"\nwrote {len(texts)} file(s). Now:\n"
          "  python3 tests/test_rowline.py\n"
          "  python3 tests/test_refine.py\n"
          "  python3 tests/test_tap.py\n"
          "then a scratch build, then MD_DOCS=<scratch> python3 tests/test_index_weight.py")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-index", action="store_true",
                    help="leave ph and w off the index row (~2.82 MB); the "
                         "line still draws tags, place, hours and the fold")
    a = ap.parse_args()
    edits = list(EDITS) + list(REFINE_EDITS)
    if not a.no_index:
        edits.insert(len(EDITS), INDEX_EDIT)
        edits.insert(len(EDITS) + 1, MARK_EDIT)
    else:
        print("  (--no-index: ph and w left off the row)")
    return apply(edits, a.check)


if __name__ == "__main__":
    sys.exit(main())
