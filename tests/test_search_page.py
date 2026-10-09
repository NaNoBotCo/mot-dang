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
    province, no "wrong results?" line under a search that worked;
  * a row draws its marks as glyphs, never stock emoji, and carries no
    open-<day> chip — both through the fallback chips and through MDROW;
  * the front page's remembered city (md-city) never narrows a search;
  * a failed index fetch leaves a way forward in the list.

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
# The shop's clock (WMIN, mdOpen, mdWhen) sat inside the pipeline until
# 2026-09-23, when it moved above the search block so plan.html could read
# opening hours too. The rows still read it, so it is lifted with them.
CLOCK_START = "// ---- md:clock — tests/test_search_page.py lifts this beside the pipeline ----"
CLOCK_END = "// ---- md:clock ends ----"

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
        # 2026-09-10 — Nan: "When search results do appear, they announce
        # 'we lack information on this place' — NO WE DO NOT. SILENCE." The
        # state family (Phone number held, Facebook page held, A thin entry,
        # Not pinned yet, No way to reach it) no longer rides into a row.
        ("khao soi", [
            ("no row announces what the record holds or lacks",
             lambda p: not any(s in p["html"] for s in (
                 "Phone number held", "Facebook page held", "Website held",
                 "Opening hours held", "A thin entry", "Not pinned yet",
                 "No way to reach it", "Name only", "ข้อมูลยังบาง", "มีเบอร์โทร",
                 "มีเพจเฟซบุ๊ก", "ยังไม่ได้ปักหมุด", "ยังไม่มีช่องทางติดต่อ"))),
            ("the wait bar is gone once the rows are drawn",
             lambda p: "mdseeking" not in p["bodyClasses"]),
        ]),
        # 2026-09-10 — River Tavern, Chiang Rai: a held record found by name
        # with its city attached, drawn as a plain card, no "no pin" badge.
        ("river tavern chiang rai", [
            ("the held record is the first row",
             lambda p: "River Tavern" in p["first"]),
            ("a one-result answer gets a short page",
             lambda p: "mdshort" in p["bodyClasses"]),
            ("the city is an active, removable chip",
             lambda p: 'class="rchip on"' in p["html"] and "Chiang Rai" in p["html"]),
            ("and nothing on the row announces a lack",
             lambda p: "no pin" not in p["html"] and "ยังไม่มีพิกัด" not in p["html"]),
        ]),
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
            ("a row's tag chip draws its mark as a glyph", _glyphed),
            ("and no row prints a stock emoji", _no_emoji),
        ]),
        # The page draws rows through MDROW (rowline_layer.py): every tag, the
        # phone, the web host. The harness loads it for these cases.
        ({"q": "", "tag": ["vegan"], "mdrow": True}, [
            ("MDROW draws rows", lambda p: len(p["rows"]) > 0 and 'class="rline"' in p["html"]),
            ("its chips and ☎ come out as glyphs", _glyphed),
            ("and no row prints a stock emoji", _no_emoji),
        ]),
        ({"q": "", "tag": ["open-sunday"]}, [
            ("rows draw", lambda p: len(p["rows"]) > 0),
            ("no row carries an open-<day> chip", _no_day_chip),
        ]),
        ({"q": "", "tag": ["open-sunday"], "mdrow": True}, [
            ("rows draw", lambda p: len(p["rows"]) > 0),
            ("no MDROW row carries an open-<day> chip", _no_day_chip),
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
            # 2026-09-10: the rail and the sponsor box stand down under a 0.
            ("nothing found is its own state: body.mdnone",
             lambda p: "mdnone" in p["bodyClasses"]),
        ]),
    ]


# U+1F300–1FAFF, U+2600–27BF and the flag letters — the stock emoji a row
# must not print. The name and the English name are the record's own words
# and are left out of the look.
_EMO = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F1E6-\U0001F1FF]")


def _marks(r):
    r = re.sub(r'<a class="rname".*?</a>', "", r, flags=re.S)
    return re.sub(r'<span class="count en[^"]*" lang="en">.*?</span>', "", r, flags=re.S)


def _no_emoji(p):
    bad = [_EMO.findall(_marks(r)) for r in p["rowhtml"]]
    return bool(p["rowhtml"]) and not any(bad)


def _glyphed(p):
    return any('class="rowicon"' in _marks(r) for r in p["rowhtml"])


def _no_day_chip(p):
    day = re.compile(r"tag=open-(mon|tues|wednes|thurs|fri|satur|sun)day")
    return bool(p["rowhtml"]) and not any(day.search(r) for r in p["rowhtml"])


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
    for mark in (PIPE_START, RENDER_START, RENDER_END, CLOCK_START, CLOCK_END):
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
    c = build.JS.index(CLOCK_START)
    clock = build.JS[c:build.JS.index(CLOCK_END, c)]
    return shipped, clock + pipeline + render, build.JS[:build.JS.index(shipped)]


def run(shipped, block, tables, queries):
    """Run pipeline+render per query under a DOM stub, return what was drawn."""
    import rowline_layer
    rowjs = rowline_layer.JS
    harness = f"""'use strict';
const fs = require('fs'), path = require('path');
require({json.dumps(SHIPPED)});
const SEARCHCORE = globalThis.SEARCHCORE;
// md.js defines window.mdIcon; mdGlyphs reads it off globalThis.
globalThis.mdIcon = (n) => '<svg class="rowicon" aria-hidden="true"><use href="#' + n + '"></use></svg>';
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
// Both halves — indexsplit_layer (2026-09-08) moved lat/lng/f/fx into
// data/index2.json, merged by POSITION on the page; a harness reading the
// first file alone sees no pins and every distance check fails.
const loadIndex = async () => {{
  const a = JSON.parse(read('data/index.json'));
  try {{ const b = JSON.parse(read('data/index2.json'));
    for (let i = 0; i < a.length && i < b.length; i++) if (b[i]) Object.assign(a[i], b[i]); }} catch (e) {{}}
  return a; }};

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
  // mdSolo wraps a lone name for the language toggle; identity is enough here.
  // `window` exists in the page and not in node — the render half reads
  // window.MDROW / MDREFINE / MDMAP, all optional, so an empty one is the
  // page without its add-ons. (Both were missing: every case THREW from the
  // day the card shipped, and the file said 35 checks failed on a page that
  // rendered fine. 2026-09-10.)
  const mdSolo = (s) => String(s == null ? '' : s);
  const window = {{}};
  if (S.mdrow) {{
{rowjs}
  }}
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
    # THE STYLESHEET IS NOT VERSIONED ANY MORE (Nan, 2026-09-10). It was,
    # because the Worker served it with a seven-day max-age and P1/P2 once
    # deployed clean and never appeared in a browser. The fingerprint sat in
    # 96,000 pages and made every CSS edit a full re-upload; now the Worker
    # serves css/js with stale-while-revalidate (publish/worker.js cacheFor),
    # so the plain name is right and a ?v= creeping back is the regression.
    src = open(os.path.join(ROOT, "build.py"), encoding="utf-8").read()
    ok = 'href="{r}style.css">' in src and 'style.css?v=' not in src
    print(f"    {'✓' if ok else '✗'} the stylesheet URL is plain (no ?v=)")
    bad += not ok
    for name, rule in CSS_CONTRACTS:
        ok = rule in build.CSS
        print(f"    {'✓' if ok else '✗'} {name}")
        bad += not ok
    return bad


def check_lost():
    """The index or a table fetch rejects. The handler is the .catch() on the
    search IIFE, just past the render marker; it runs here under stubs."""
    import build
    src = build.JS
    print("  a failed fetch:")
    try:
        i = src.index(RENDER_END)
        j = src.index(".catch(", i) + len(".catch(")
        k = src.index("\n// ---- THE OUTCOME BEACON", j)
        handler = src[j:k].rstrip()
        assert handler.endswith(");}")
        handler = handler[:-3]
    except (ValueError, AssertionError):
        print("    ✗ cannot find the search's .catch() after the render marker")
        return 1
    js = """'use strict';
const mdBi = (th, en) => th + ' · ' + en;
function lost(search, cls, before) {
  const resBox = { className: cls, innerHTML: before || '',
    insertAdjacentHTML(w, h) { this.innerHTML = w === 'afterbegin' ? h + this.innerHTML : this.innerHTML + h; } };
  const location = { search, href: 'https://motdang.net/search.html' + search };
  const document = { body: { classList: { remove() {} } } };
  const RROOT = '';
  const console = { error() {} };
  const h = eval('(' + HANDLER + ')');
  h(new TypeError('Failed to fetch'));
  return resBox.innerHTML;
}
console.log(JSON.stringify([
  lost('?q=pad%20thai', 'dir', ''),
  lost('?tag=vegan', 'dir', '<li class="richdoor">doors</li>'),
  lost('?q=pad%20thai', 'dir cards', '<li class="rcard">row</li>'),
]));
""".replace("HANDLER", json.dumps(handler))
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as fh:
        fh.write(js)
        hpath = fh.name
    try:
        proc = subprocess.run(["node", hpath], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(hpath)
    if proc.returncode:
        print("    ✗ the handler threw under node:\n" + (proc.stderr or proc.stdout)[-1500:])
        return 1
    typed, filt, drawn = json.loads(proc.stdout)
    checks = [
        ("an emptied list gets one shelf row",
         typed.count('<li class="shelf">') == 1),
        ("that retries the same address",
         'href="https://motdang.net/search.html?q=pad%20thai"' in typed and "connection lost" in typed),
        ("and sends no reader to /api/v1/search, which answers JSON",
         "api/v1/search" not in typed),
        ("a filter with no words gets no edge link, and keeps its doors",
         "api/v1/search" not in filt and filt.startswith('<li class="shelf">') and "doors" in filt),
        ("a list the render already wrote is left alone",
         drawn == '<li class="rcard">row</li>'),
    ]
    bad = 0
    for name, ok in checks:
        print(f"    {'✓' if ok else '✗'} {name}")
        bad += not ok
    return bad


# The boot, above the pipeline marker, is not run here; these hold its lines.
JS_CONTRACTS = [
    ("a filter with no words keeps the served doors until rows exist",
     "if(q)resBox.innerHTML='';"),
]


def check_js():
    import build
    print("  boot contracts:")
    bad = 0
    for name, line in JS_CONTRACTS:
        ok = line in build.JS
        print(f"    {'✓' if ok else '✗'} {name}")
        bad += not ok
    # 2026-09-11: the front page's remembered city was read here as a soft
    # province filter and taken out the same day — with home set to Chiang
    # Mai, "mae sai" answered 200 Chiang Mai namesakes and none of Chiang
    # Rai's own district. The front page keeps md-city for itself.
    ok = "md-city" not in build.JS
    print(f"    {'✓' if ok else '✗'} the search script does not read the front page's md-city")
    bad += not ok
    return bad


def main():
    shipped, block, tables = premise()
    cs = cases()
    got = run(shipped, block, tables, [q for q, _ in cs])
    if got is None:
        return 1
    bad = check_css() + check_js() + check_lost()
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
