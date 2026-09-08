#!/usr/bin/env python3
"""The search RESULTS PAGE — the half tests/test_search.py cannot see.

That file lifts the block between the `md:search-pipeline` markers, which is
deliberately free of DOM and network so it can run under node. Everything
AFTER those markers — the count, the status lines, the rich door, the rows,
the order they are written in — was untested, and on 2026-09-07 it showed:

    const partial = worst === 'partial';   // line 3681
    ...
    const worst = found.length ? ... ;     // line 3695

`const` in the temporal dead zone. Every search on the site threw
`ReferenceError: Cannot access 'worst' before initialization`, the result list
never rendered at all, and tests/test_search.py passed 32 of 33 cases while it
was broken, because the fault was four lines below where it stops looking.

So this file lifts the OTHER block, `md:search-render`, and runs pipeline and
render together against the real index under a hand-written DOM stub. It
asserts what a reader would see, not what the code contains:

  * the page renders at all, and writes rows into the list;
  * the page's own account of a failed match comes ABOVE the results, never
    under them (Michael's report, 2026-09-06);
  * a query that matched nothing whole opens no rich door;
  * a query about its own topic still does;
  * naming a landmark sorts by distance and says so (WO-68);
  * the declutter rules hold: no province chip when every row is in one
    province, no "wrong results?" line under a search that worked.

    /opt/homebrew/bin/python3.13 tests/test_search_page.py     (after a build)
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.environ.get("MD_DOCS", os.path.join(ROOT, "docs"))
INDEX = os.path.join(DOCS, "data", "index.json")
SHIPPED = os.path.join(ROOT, "assets", "searchcore.js")

PIPE_START = "// ---- md:search-pipeline — tests/test_search.py lifts this block ----"
RENDER_START = "// ---- md:search-render — tests/test_search_page.py lifts from here ----"
RENDER_END = "// ---- md:search-render ends ----"

# (query, [checks]) — each check is (name, predicate over the rendered page)
#
# `page` is a dict: html (what went into the list), count (the heading number),
# qual (the word beside it), rows (list of row texts), rowhtml (list of row
# HTML), first (the first row's text), err (a thrown error, or None).


def cases():
    def has(sub):
        return lambda p: sub in p["html"]

    def hasnt(sub):
        return lambda p: sub not in p["html"]

    def before(a, b):
        def f(p):
            i, j = p["html"].find(a), p["html"].find(b)
            return i >= 0 and j >= 0 and i < j
        return f

    return [
        ("parking for motorcycle near taphae gate", [
            ("renders at all", lambda p: p["err"] is None),
            ("writes rows", lambda p: len(p["rows"]) > 0),
            ("no elephant door over a failed match", hasnt("richdoor")),
            ("the top row is a car park",
             lambda p: "จอด" in p["first"] or "arking" in p["first"]),
        ]),
        ("parking near tha phae gate", [
            ("sorted by distance, and says so — as a 📍 chip, not a sentence",
             lambda p: "📍" in p["html"] and "measured from" not in p["html"]),
            ("the point chip is above the rows",
             before("📍", '<li class="rcard"')),
            # Either in a chip, or already in the name — a synthesised car
            # park is called "ลานจอดรถ · ใกล้ประตูท่าแพ 100 ม.", and printing
            # the same metres again beside it is the duplication this whole
            # pass is about.
            ("every row states its distance",
             lambda p: all("dist" in r for r in p["rowhtml"][:10])),
            ("and states exactly one — the row shows no OTHER landmark's bearing",
             lambda p: not any(re.search(r"ใกล้(ประตู|แจ่ง)", r) for r in p["rowhtml"])),
            ("nearest first",
             lambda p: _metres(p["rowhtml"]) == sorted(_metres(p["rowhtml"]))),
            ("no topic card over a question it does not answer",
             hasnt("richdoor")),
        ]),
        ("tha phae gate", [
            ("the landmark itself is the first row",
             lambda p: "Thapae Gate" in p["first"] or "ประตูท่าแพ" in p["first"]),
            ("a query that is ONLY a landmark keeps its topic card",
             has("richdoor")),
        ]),
        ("elephant", [
            ("a long list keeps the shelves and the footer",
             lambda p: "mdshort" not in p["bodyClasses"]),
            ("the door still opens for its own topic", has("richdoor")),
            ("a search that worked is not asked if it went wrong",
             hasnt("tellants")),
            ("the province IS named when the rows span both",
             lambda p: bool(re.search(r'· (เชียงใหม่|เชียงราย)</span>', p["html"]))),
        ]),
        ("rajavej hospital", [
            # P1 — Nan, 2026-09-07: "For 1-2 results, you shouldn't have to
            # long-scroll. Never." One result was 27 px of answer in a 1,484 px
            # page; the grid, the bar and the footer's links now stand down.
            ("a one-result answer gets a short page",
             lambda p: "mdshort" in p["bodyClasses"]),
            ("no province chip when every row is in one province",
             lambda p: not re.search(r'· (เชียงใหม่|เชียงราย)</span>', p["html"])),
            ("an exact match says nothing about how it matched",
             lambda p: "near spelling" not in p["html"]
             and "including words that mean the same thing" not in p["html"]),
        ]),
        # WO-69 — THE CARD (Michael, 2026-09-07)
        ("guitar", [
            ("every card carries at least two chips",
             lambda p: p["rows"] and all(r.count('class="rchip"') >= 2 for r in p["rowhtml"])),
            ("every chip is a filter link into search.html",
             lambda p: all(re.search(r'class="rchip" href="[^"]*search\.html\?(sub|cat|st|ar|tag|q)=', r) for r in p["rowhtml"])),
            ("a pinned card has its 📍", lambda p: all('class="rpin"' in r for r in p["rowhtml"] if 'data-lat=' in r)),
            ("no instruction anywhere", lambda p: not any(s in p["html"] for s in (
                "add a word to narrow", "put it to the ants", "Try one of these", "Type a shop",
                "cannot filter on it yet", "this looks like the word you meant", "closest first"))),
        ]),
        ({"q": "", "tag": ["zzznotatag"]}, [
            ("an unmet hard filter draws the count 0 and nothing else",
             lambda p: 'count">0<' in p["html"] and "richdoor" not in p["html"] and not p["rows"]),
        ]),
        ({"q": "", "tag": ["vegan"]}, [
            ("a filter with no words draws cards", lambda p: len(p["rows"]) > 0),
            ("the active filter is a removable chip", lambda p: 'class="rchip on"' in p["html"]),
        ]),
        ("#wifi coffee", [
            ("the lifted tag is an active chip", lambda p: 'class="rchip on"' in p["html"]),
            ("and rows still draw", lambda p: len(p["rows"]) > 0),
        ]),
        ("coffee near tha phae gate", [
            ("a where-question folds everything past the third row",
             lambda p: 'class="shelf fold"' in p["html"]),
            ("three cards stand before the fold",
             lambda p: p["html"].find('class="shelf fold"') > 0 and
             p["html"][:p["html"].find('class="shelf fold"')].count('<li class="rcard"') == 3),
        ]),
        ("zzzzqqqwwww", [
            # A search that found NOTHING is not a short answer: the shelves
            # and the way forward ARE the answer there, so the page keeps them.
            ("nothing found is not treated as a short answer",
             lambda p: "mdshort" not in p["bodyClasses"]),
            ("nothing found still offers the shelves", has("crawl-request")),
            ("and asks the reader what went wrong", has("tellants")),
        ]),
    ]


def _metres(rowhtml):
    """The distance chips, in metres, in the order the rows were written."""
    out = []
    for r in rowhtml:
        m = re.search(r'class="count dist">· ([\d.]+)\s*(ม\.|m|กม\.|km)', r)
        if not m:
            continue
        v = float(m.group(1))
        out.append(v * 1000 if m.group(2) in ("กม.", "km") else v)
    return out


def premise():
    if not os.path.exists(INDEX):
        sys.exit(f"✗ {INDEX} missing — run build.py first")
    if not os.path.exists(SHIPPED):
        sys.exit("✗ assets/searchcore.js missing — run search-core/sync.py")
    sys.path.insert(0, ROOT)
    try:
        import build
    except SyntaxError:
        sys.exit("✗ build.py does not parse — run this under "
                 "/opt/homebrew/bin/python3.13 (3.9 cannot read it)")
    for mark in (PIPE_START, RENDER_START, RENDER_END):
        if mark not in build.JS:
            sys.exit(f"✗ the marker {mark[:44]}… is gone from build.py's search "
                     f"page. The block moved and this test cannot find it — put "
                     f"the marker back around it, or point this file at where "
                     f"it went.")
    shipped = open(SHIPPED, encoding="utf-8").read()
    i = build.JS.index(PIPE_START)
    i = build.JS.index("\n", i) + 1
    j = build.JS.index(RENDER_START)
    pipeline = build.JS[i:j]
    k = build.JS.index("\n", j) + 1
    render = build.JS[k:build.JS.index(RENDER_END, k)]
    return shipped, pipeline + render, build.JS[:build.JS.index(shipped)]


def run(shipped, block, tables, queries):
    """Run pipeline+render per query under a DOM stub, return what was drawn."""
    harness = f"""'use strict';
const fs = require('fs'), path = require('path');
require({json.dumps(SHIPPED)});
const SEARCHCORE = globalThis.SEARCHCORE;
{tables}
const DOCS = {json.dumps(DOCS)};
const RROOT = '';
const read = rel => fs.readFileSync(path.join(DOCS, rel), 'utf8');
const mdJSON = async rel => {{
  try {{ return JSON.parse(read(rel)); }} catch (e) {{ return null; }}
}};
const fetch = async url => {{
  const p = path.join(DOCS, url);
  const ok = fs.existsSync(p);
  return {{ ok, text: async () => (ok ? read(url) : '') }};
}};
let INDEX_CACHE = null;
const loadIndex = async () => (INDEX_CACHE ||= JSON.parse(read('data/index.json')));

// The smallest DOM that this block actually touches. Deliberately NOT jsdom:
// the point is to run the shipped code, and a stub that throws on anything
// unexpected tells us the moment the block reaches for something new.
function stubDoc() {{
  const el = (cls) => ({{
    className: cls || '', textContent: '', innerHTML: '', hidden: false,
    children: [],
    insertAdjacentHTML(where, h) {{ this.innerHTML += h; }},
    insertBefore(node) {{ this.innerHTML = (node.outerHTML || '') + this.innerHTML; }},
    appendChild() {{}},
    get firstChild() {{ return null; }},
    parentNode: {{ insertBefore() {{}} }},
    nextSibling: null,
  }});
  const box = el('dir'), count = el('count'), qual = el('count');
  // P1 sets body.mdshort. A stub that lacks `body` would throw here, which is
  // the whole reason this file exists.
  const cls = new Set();
  const body = {{ classList: {{
    toggle: (c, on) => (on ? cls.add(c) : cls.delete(c)),
    add: c => cls.add(c), remove: c => cls.delete(c),
    contains: c => cls.has(c) }} }};
  return {{
    box, count, qual, body, _cls: cls,
    getElementById: id => (id === 'results' ? box : id === 'rescount' ? count
                           : id === 'resqual' ? qual : null),
    querySelectorAll: () => [],
    createElement: () => {{ const e = el(); e.outerHTML = ''; return e; }},
    createDocumentFragment: () => ({{ appendChild() {{}} }}),
  }};
}}

async function drawn(spec) {{
  const S = (typeof spec === 'string') ? {{q: spec}} : (spec || {{}});
  const q = S.q || '';
  const F = {{tag: S.tag || [], sub: S.sub || [], cat: S.cat || [], st: S.st || [], ar: S.ar || [],
             near: Array.isArray(S.near) ? {{lat: S.near[0], lng: S.near[1]}} : null}};
  F.any = !!(F.tag.length || F.sub.length || F.cat.length || F.st.length || F.ar.length || F.near);
  const QS = '?' + ['q','tag','sub','cat','st','ar'].filter(k => (k==='q'?q:(F[k]||[]).length))
    .map(k => k + '=' + encodeURIComponent(k==='q'?q:F[k].join(','))).join('&');
  const doc = stubDoc();
  const document = doc;
  const resBox = doc.box;
  const mdBi = (th, en) => th + ' · ' + en;
  let err = null;
  try {{
{block}
  }} catch (e) {{ err = String(e && e.message || e); }}
  const html = doc.box.innerHTML;
  const bodyClasses = [...doc._cls];
  // WO-69: a row is a card
  const rowhtml = html.match(/<li class="rcard"[^>]*>[\\s\\S]*?<div class="rpanel" hidden><\\/div><\\/li>/g) || [];
  const strip = s => s.replace(/<[^>]*>/g, '').trim();
  return {{ err, html, bodyClasses, count: doc.count.textContent, qual: doc.qual.innerHTML,
           rows: rowhtml.map(strip), rowhtml,
           first: rowhtml.length ? strip(rowhtml[0]) : '' }};
}}

(async () => {{
  const out = [];
  for (const q of JSON.parse(process.argv[2])) out.push(await drawn(q));
  console.log(JSON.stringify(out));
}})();
"""
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(harness)
        hpath = fh.name
    try:
        proc = subprocess.run(["node", hpath, json.dumps(queries)],
                              capture_output=True, text=True, timeout=900)
    finally:
        os.unlink(hpath)
    if proc.returncode:
        print("✗ the search page failed to run under node:\n"
              + (proc.stderr or proc.stdout)[-2500:])
        return None
    return json.loads(proc.stdout)


# P2 and P1 are enforced in the STYLESHEET, where the render test cannot see
# them: the markup still carries both units and both bars, and CSS decides
# which is shown. A rule deleted by accident would leave every check in this
# file passing while the page went back to repeating itself. So the rules are
# contracts too.
CSS_CONTRACTS = [
    ("P2 — a unit is not doubled in ไทย+EN",
     "html.lang-both .dist .en{display:none}"),
    ("P2 — …nor any other computed value (WO-69)",
     "html.lang-both .u .en{display:none}"),
    ("WO-69 — the card has its rules",
     "li.rcard{"),
    ("P1 — a short answer drops the grid, the bar and the footer's links",
     "body.mdshort .chipbar,body.mdshort .svcbar,"),
    ("P1 — the OSM credit is NOT inside what P1 hides",
     ".footnav"),
]


def check_css():
    import build
    bad = 0
    print("  stylesheet contracts:")
    # THE STYLESHEET MUST BE VERSIONED. It is served with a seven-day
    # max-age, so an unversioned URL means a returning reader keeps the CSS
    # they already had for a week — and a layout fix reaches first-time
    # visitors only. P1 and P2 deployed clean and did not appear in a browser
    # for exactly this reason.
    src = open(os.path.join(ROOT, "build.py"), encoding="utf-8").read()
    ok = 'style.css?v={MD_CSS_V}' in src
    print(f"    {'✓' if ok else '✗'} the stylesheet URL carries its content hash")
    bad += not ok
    for name, rule in CSS_CONTRACTS:
        ok = rule in build.CSS
        print(f"    {'✓' if ok else '✗'} {name}")
        bad += not ok
    return bad


def main():
    shipped, block, tables = premise()
    cs = cases()
    got = run(shipped, block, tables, [q for q, _ in cs])
    if got is None:
        return 1
    bad = check_css()
    for (q, checks), p in zip(cs, got):
        print(f"\n  {q!r}  — {len(p['rows'])} rows, count {p['count']!r}"
              + (f", qualifier {p['qual']!r}" if p["qual"] else ""))
        if p["err"]:
            print(f"    ✗ THREW: {p['err']}")
            bad += len(checks)
            continue
        for name, fn in checks:
            try:
                ok = bool(fn(p))
            except Exception as e:                      # noqa: BLE001
                ok, name = False, f"{name} — check itself failed: {e}"
            print(f"    {'✓' if ok else '✗'} {name}")
            bad += not ok
    print(f"\n{'✓ search page OK' if not bad else f'✗ {bad} page check(s) failed'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
