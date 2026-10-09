#!/usr/bin/env python3
"""The search matcher, exercised against the real index.

This exists because of a bug nobody would have found by reading the code. The
matcher tested the whole query as one unbroken substring, so `rajavej hospital`
scored zero against "Rajavej Chiang Mai Hospital" — the page was built, indexed
and linked, and simply could not be found by anyone typing its name. 5,190 of
the catalogue's names run three words or longer, so the same hole swallowed
`maharaj hospital`, `nimman coffee` and `dental clinic chiang mai`.

WHAT THIS RUNS IS WHAT THE SITE RUNS, and getting that wrong is the other half
of the story. The test used to lift the matcher out of build.py by slicing the
source between two lines of JavaScript. WO-4 moved the matcher to
search-core/searchcore.js, both anchors stopped existing, and every run from
2026-08-17 onward died on `ValueError: substring not found` before it reached a
single case — a test that was not testing anything, quietly, for three weeks.

So nothing is found by guessing at code any more. Three things are checked
before a case runs, and each one fails with an explanation rather than a
traceback:

  * assets/searchcore.js — the file the site ships — is loaded by node with
    require(), verbatim. No slicing.
  * build.py must still fold that exact file into the page script. If it stops,
    this test is no longer testing the shipped matcher and says so.
  * the page's own search pipeline is cut from build.JS between the
    `md:search-pipeline` markers, which name this file. Move the block and take
    the markers with it; delete them and the test reports what it lost.

The canonical copy in ../search-core/ is compared too, on the same terms
build.py uses: a stale assets/ copy means the rules being tested are not the
rules that were fixed.

    /opt/homebrew/bin/python3.13 tests/test_search.py     (after a build)
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.environ.get("MD_DOCS", os.path.join(ROOT, "docs"))
INDEX = os.path.join(DOCS, "data", "index.json")
SHIPPED = os.path.join(ROOT, "assets", "searchcore.js")
CANON = os.path.join(os.path.dirname(ROOT), "search-core", "searchcore.js")

MARK_START = "// ---- md:search-pipeline — tests/test_search.py lifts this block ----"
MARK_END = "// ---- md:search-pipeline ends ----"

# A tier is what the page TELLS the reader about the match it made: 'exact' is
# silent, and everything else prints a line saying the search widened. So the
# tier is part of the contract, not an implementation detail — a near-spelling
# match presented as an exact one has misled somebody about how well they were
# understood.
LOOSENED = ("thesaurus", "loose", "partial")

# (query, expect_id or None, expectation, note)
#   exact     — found, and the search did not have to widen to do it
#   loosened  — found, and the page says out loud that it widened
#   some      — finds something; which rows is the catalogue's business
#   none      — finds nothing, and must not fall back to finding everything
#   shelf:KEY — finds something AND the first row stands on that shelf. For a
#               query that cannot match every word by construction: "parking
#               for motorcycle near taphae gate" names a shelf, a vehicle and
#               a landmark, and no single row carries all four words, so the
#               tier is `partial` and the count is large and defensible. What the
#               reader is owed there is not a small number, it is a CAR PARK
#               AT THE TOP.
CASES = [
    ("rajavej hospital", "cm-osm-way-97675282", "exact",
     "the bug this file exists for: words with two others wedged between them"),
    ("Rajavej Hospital", "cm-osm-way-97675282", "exact", "case must not matter"),
    ("hospital rajavej", "cm-osm-way-97675282", "exact", "word order must not matter"),
    ("โรงพยาบาลราชเวช", "cm-osm-way-97675282", "exact",
     "Thai carries no spaces — one term, split by the segmenter"),
    ("rajavey hospitl", "cm-osm-way-97675282", "loosened",
     "two typos still land, and the page says it loosened"),
    ("maharaj hospital", None, "exact", "the same word-gap shape, different place"),
    ("wat phra singh", None, "exact", "a name that WAS contiguous must not regress"),
    ("", None, "none", "empty query finds nothing rather than everything"),
    ("   ", None, "none", "whitespace is not a search"),
    ("zzzzqqq", None, "none", "a real miss still misses — fuzziness must not match all"),
    # WO-4: a reader's spelling is widened through the thesaurus, and the
    # shelf/cuisine/road a place already carries is matched, not just its name.
    ("kow soi", None, "some", "romanisation drift — signage in this city uses all of them"),
    ("khaosoy", None, "some", "cross-script phonetic matching for khao soi"),
    ("rachawech", "cm-osm-way-97675282", "loosened", "cross-script phonetic match for ราชเวช"),
    ("ข้าวซอย", None, "some", "the same dish in Thai finds the same places"),
    ("coffee", None, "some", "the shelf is matched, not only names containing 'coffee'"),
    ("นวด", None, "some", "a Thai shelf word reaches the massage places"),
    ("temple", None, "some", "an English word for a Thai shelf"),
    # WO-67 (Michael, 2026-09-06). The catalogue held ZERO parking among
    # 22,351 places; the word was a constraint the engine ate and could not
    # act on. All three of these were "none" before the parking crawl.
    ("parking", None, "some", "the word he typed first now reaches a shelf"),
    ("ที่จอดรถ", None, "some", "and in Thai"),
    ("motorcycle parking", None, "some", "the specific ask, as a shelf not a name search"),
    ("parking for motorcycle near taphae gate", None, "shelf:parking",
     "Michael's query, verbatim — the top row must be a car park"),
    # 2026-09-10 — Nan, from River Tavern in Chiang Rai: "river tavern chiang
    # rai" found nothing. Two faults: the record is held (name only, no pin) and
    # was out of the index; and no row carried its own province, so the city
    # was two more words no name contained. A held row is now indexed on its
    # name and province, and a row carries its province words.
    ("river tavern chiang rai", "cr-curated-river-tavern", "exact",
     "a held record, found by name WITH its city attached"),
    ("river tavern", "cr-curated-river-tavern", "exact", "and without it"),
    ("River Tavern Chiangrai", "cr-curated-river-tavern", "exact", "one-word city"),
    ("ข้าวซอย เชียงราย", None, "province:cr",
     "the city narrows: every row is in the named province, not only the "
     "rows with the city in their NAME (live 2026-09-10: 9 of 85)"),
    ("khao soi chiang mai", None, "province:cm", "and the other city"),
    ("cafe", None, "no-city-chip", "a query naming no city lifts no province"),
    # 2026-09-10, from the first miss report (WO-84): the plain word for food
    # answered with two loose rows. The two-letter question words หา and ขอ,
    # and the vegan word เจ, were being cut out of the INSIDE of unspaced Thai
    # words. A Thai phrase is stripped only at a boundary now (search-core).
    ("อาหาร", None, "some", "the plain word for food reaches the food shelf"),
    ("ของกิน", None, "some", "ขอ must not be cut out of ของกิน"),
    ("วัดเจดีย์หลวง", None, "exact", "เจ must not be cut out of เจดีย์"),
    ("หา ร้านอาหาร", None, "some", "the question word goes, the food word stays whole"),
]

# WHICH RICH DOOR OPENED, which is the other half of what the reader sees.
# (query, expected panel id or None, note)
#
# This list exists because of one report. On 2026-09-06 "parking for
# motorcycle near taphae gate" opened the ELEPHANTS door — full width, with a
# count and lead sentences — above the page's own note that nothing had
# matched. The route was the mined shelf table, which had learnt `gate` as an
# elephant word from the chang teaser's phrase "the gate and the chedis that
# carry its name". A lifted shelf can no longer open a panel at all, and the
# teaser is now mined as a list rather than as prose (search-core mine.py).
#
# The first four are the regression. The rest are the other half of the
# contract: retiring the trigger must not have shut a door that should open.
PANEL_CASES = [
    ("parking for motorcycle near taphae gate", None,
     "THE REPORT: a query about parking must not open the elephant door"),
    ("chiang mai gate", None, "no gate in this city is an elephant camp"),
    ("ประตูช้างเผือก", "moat",
     "Chang Phueak Gate is a GATE — the moat door, never the elephant one; "
     "the chang panel's own delight line says the toponyms are not camps"),
    ("visa extension", "paper",
     "'extensions' reached the beauty shelf through the mined table, and beauty "
     "is listed above paper — so a visa extension opened a hair salon"),
    ("elephant", "chang", "the door still opens for the topic it is about"),
    ("ช้าง", "chang", "and in Thai"),
    ("ปางช้าง", "chang", "and for the word a Thai reader actually types"),
    ("นวด", "massage", "massage keeps its door"),
    ("มวยไทย", "muaythai", "muay thai keeps its door"),
    ("ตัดผม", "beauty", "beauty keeps its door"),
    ("คอนโด", "realestate", "real estate keeps its door"),
    ("เซเว่น", "seven", "the 7-Eleven door was never mined-shelf-triggered"),
    ("สนามบิน", "flights", "flights keeps its door"),
]


def premise():
    """Everything that has to be true before a case means anything.

    Returns (page_js, pipeline_js, notes) or exits with an explanation. The
    checks are the point: each one is a way this file could go back to testing
    nothing without anybody noticing.
    """
    notes = []
    if not os.path.exists(INDEX):
        sys.exit(f"✗ {INDEX} missing — run build.py first")
    if not os.path.exists(SHIPPED):
        sys.exit("✗ assets/searchcore.js missing — run search-core/sync.py")
    shipped = open(SHIPPED, encoding="utf-8").read()

    # A stale copy is the quiet failure: the site keeps building and keeps
    # serving matching rules that were fixed somewhere else weeks ago, and this
    # test keeps passing against the old ones.
    if os.path.exists(CANON):
        if open(CANON, encoding="utf-8").read() not in shipped:
            sys.exit("✗ assets/searchcore.js is STALE against search-core/ — "
                     "run search-core/sync.py, then rebuild")
    else:
        notes.append("search-core/ not checked out — parity with the canonical "
                     "copy was not verified")

    sys.path.insert(0, ROOT)
    try:
        import build  # noqa: E402  — imports cheap; build() runs only under __main__
    except SyntaxError:
        sys.exit("✗ build.py does not parse — run this under "
                 "/opt/homebrew/bin/python3.13 (3.9 cannot read it)")

    if shipped not in build.JS:
        sys.exit("✗ build.py no longer folds assets/searchcore.js into the page "
                 "script — this test would be exercising a matcher the site does "
                 "not serve. Check searchcore_js() in build.py.")
    if MARK_START not in build.JS or MARK_END not in build.JS:
        sys.exit("✗ the md:search-pipeline markers are gone from build.py's "
                 "search page. The block moved and this test cannot find it — "
                 "put the markers back around the pipeline, or point this file "
                 "at wherever it went.")

    i = build.JS.index(MARK_START)
    i = build.JS.index("\n", i) + 1
    pipeline = build.JS[i:build.JS.index(MARK_END, i)]
    return shipped, pipeline, notes


def run_cases(shipped, pipeline, queries):
    # MD_CATWORDS and MD_SUBWORDS are read out of the page script rather than
    # rebuilt here, for the same reason the pipeline is: a table typed twice is
    # a table that will disagree with itself.
    sys.path.insert(0, ROOT)
    import build
    tables = build.JS[:build.JS.index(shipped)]

    harness = f"""'use strict';
const fs = require('fs'), path = require('path');
require({json.dumps(SHIPPED)});          // publishes globalThis.SEARCHCORE
const SEARCHCORE = globalThis.SEARCHCORE;
{tables}
const DOCS = {json.dumps(DOCS)};
const RROOT = '';
// The three ways the page reaches the network, and nothing else is stubbed —
// if the pipeline grows a fourth, node throws here instead of quietly skipping.
const read = rel => fs.readFileSync(path.join(DOCS, rel), 'utf8');
const mdJSON = async rel => JSON.parse(read(rel));
const fetch = async url => {{
  const p = path.join(DOCS, url);
  const ok = fs.existsSync(p);
  return {{ ok, text: async () => (ok ? read(url) : '') }};
}};
let INDEX_CACHE = null;   // parsed once; the pipeline rebuilds its own index
// Both halves. indexsplit_layer (2026-09-08) moved lat/lng/f/fx into
// data/index2.json, merged by POSITION on the page; a harness reading the
// first file alone sees no pins and every distance check fails.
const loadIndex = async () => (INDEX_CACHE ||= (() => {{
  const a = JSON.parse(read('data/index.json'));
  try {{ const b = JSON.parse(read('data/index2.json'));
    for (let i = 0; i < a.length && i < b.length; i++) if (b[i]) Object.assign(a[i], b[i]); }} catch (e) {{}}
  return a; }})());

// WO-69: a case is a query string, or {{q, tag, sub, cat, st, ar, near}} —
// the filters the page reads beside q. F and QS are what search.html builds
// from location.search; here they are built from the spec.
async function search(spec) {{
  const S = (typeof spec === 'string') ? {{q: spec}} : (spec || {{}});
  const q = S.q || '';
  const F = {{tag: S.tag || [], sub: S.sub || [], cat: S.cat || [], st: S.st || [], ar: S.ar || [],
             near: Array.isArray(S.near) ? {{lat: S.near[0], lng: S.near[1]}} : null}};
  F.any = !!(F.tag.length || F.sub.length || F.cat.length || F.st.length || F.ar.length || F.near);
  const QS = '?' + ['q','tag','sub','cat','st','ar'].filter(k => (k==='q'?q:(F[k]||[]).length))
    .map(k => k + '=' + encodeURIComponent(k==='q'?q:F[k].join(','))).join('&');
{pipeline}
  return {{
    n: found.length,
    filters: (typeof FT !== 'undefined') ? FT.map(x => (x.none != null ? 'none:' + x.none : (x.t != null ? 't:' + TAB.tags[x.t][0] : 'tt:' + TAB.trade[x.tt][0])) + (x.soft ? '~' : '') + (x.dropped ? '!' : '')) : [],
    tags: found.slice(0, 50).map(r => (r.doc.t || []).map(i => TAB.tags[i][0])),
    metres: found.slice(0, 50).map(r => r.m == null ? null : Math.round(r.m)),
    qFor: (typeof qFor !== 'undefined') ? qFor : q,
    ids: hits.map(e => e.id),
    provs: found.slice(0, 200).map(r => r.doc.p),
    pv: (typeof pv !== 'undefined') ? pv : null,
    tier: found.length ? found[0].tier : null,
    coverage: found.length ? found[0].coverage : null,
    notes: an.notes,
    top: found.length ? (found[0].doc.e || found[0].doc.n) : null,
    topsu: found.length ? (found[0].doc.su || []) : [],
    // Which rich door the query opened, and whether the engine had to loosen.
    // Both are things the READER sees, so both are part of the contract —
    // see PANEL_CASES and the note above it.
    panel: (typeof panel !== 'undefined' && panel) ? panel.id : null,
    shelves: (typeof wantShelves !== 'undefined') ? [...wantShelves].sort() : [],
  }};
}}

(async () => {{
  const out = [];
  for (const q of JSON.parse(process.argv[2])) {{
      console.error("running query:", q);
      out.push(await search(q));
  }}
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
        print("HARNESS PATH:", hpath)
    if proc.returncode:
        print("✗ the shipped matcher failed to run under node:\n"
              + (proc.stderr or proc.stdout)[-2000:])
        return None
    return json.loads(proc.stdout)


def _every_tagged(slug):
    def f(r):
        if r["n"] < 1:
            return False, " — found nothing"
        missing = [t for t in r["tags"] if slug not in t]
        return (not missing), (f" — {len(missing)} of the first {len(r['tags'])} rows lack {slug!r}" if missing else "")
    return f


def _sorted_metres(r):
    m = [x for x in r["metres"] if x is not None]
    return (r["n"] >= 1 and m == sorted(m)), ("" if m == sorted(m) else f" — metres not ascending: {m[:6]}")


FILTER_CASES = [
    ({"q": "", "tag": ["vegan"]}, _every_tagged("vegan"),
     "tag= with no words: the filter is the query, every row carries the tag"),
    ({"q": "cafe", "tag": ["vegan"]}, _every_tagged("vegan"),
     "tag= narrows a word search hard"),
    ({"q": "#vegan"}, lambda r: (r["qFor"] == "" and "t:vegan" in r["filters"] and r["n"] >= 1,
                                 f" — qFor={r['qFor']!r} filters={r['filters']}"),
     "#word is lifted out of the box into a filter"),
    ({"q": "vegan cafe"}, lambda r: ("t:vegan~" in r["filters"] and r["n"] >= 1 and all("vegan" in t for t in r["tags"]),
                                     f" — filters={r['filters']}"),
     "a lifted constraint becomes a soft tag filter (route 2)"),
    ({"q": "cafe", "tag": ["zzznotatag"]}, lambda r: (r["n"] == 0, f" — found {r['n']}"),
     "an unknown hard tag answers zero, never everything"),
    ({"q": "cafe", "near": [18.7876, 98.9931]}, _sorted_metres,
     "near= sorts by metres from the point"),
    ({"q": "", "sub": ["cafe"]}, lambda r: (r["n"] >= 50, f" — found {r['n']}"),
     "sub= alone lists the sub-shelf"),
    # WO-69's third route may read a bare shelf word as a SOFT tag (`~`), which
    # narrows only when it can and never changes the words; the contract here
    # is that no HARD filter appears and the query text is untouched.
    ("rajavej hospital", lambda r: (all(f.endswith("~") or f.endswith("~!") for f in r["filters"]) and r["qFor"] == "rajavej hospital", f" — filters={r['filters']} qFor={r['qFor']!r}"),
     "a plain query lifts no hard filter and is not changed"),
    # WO-70 — the rare word is the question
    ("best place to buy a Martin guitar", lambda r: (any("guitar" in i for i in r["ids"][:3]), f" — top three {r['ids'][:3]}"),
     "a guitar shop outranks two hundred cafés that matched `buy`"),
    ("cheap tok sen massage old city", lambda r: (r["n"] >= 1 and any("tok" in (i or "") or "massage" in (i or "") for i in r["ids"][:3]), f" — top three {r['ids'][:3]}"),
     "a sentence is not punished for its extra words"),
    ("วัดเจดีย์หลวง", lambda r: (not any("vegan" in f for f in r["filters"]) and r["n"] >= 1, f" — filters={r['filters']}"),
     "a temple named for its chedi is not a vegan search (2026-09-10)"),
]


def main():
    shipped, pipeline, notes = premise()
    for n in notes:
        print(f"  note: {n}")
    got = run_cases(shipped, pipeline, [c[0] for c in CASES])
    if got is None:
        return 1

    bad = 0
    for (q, want_id, want, note), r in zip(CASES, got):
        why = ""
        if want.startswith("shelf:"):
            shelf = want.split(":", 1)[1]
            ok = r["n"] >= 1 and shelf in (r["topsu"] or [])
            if not ok:
                why = (" — found nothing" if not r["n"] else
                       f" — top row is {r['top']!r}, on {r['topsu']!r}, not {shelf!r}")
        elif want.startswith("province:"):
            prov = want.split(":", 1)[1]
            off = [p for p in r["provs"] if p != prov]
            ok = r["n"] >= 1 and r["pv"] == prov and not off
            if not ok:
                why = (" — found nothing" if not r["n"] else
                       f" — pv={r['pv']!r}, {len(off)} of {len(r['provs'])} rows outside {prov!r}")
        elif want == "no-city-chip":
            ok = r["n"] >= 1 and r["pv"] is None
            if not ok:
                why = f" — pv={r['pv']!r}"
        elif want == "none":
            ok = r["n"] == 0
            if not ok:
                why = f" — found {r['n']}, e.g. {r['top']!r} at tier {r['tier']!r}"
        else:
            ok = r["n"] >= 1
            if not ok:
                why = " — found nothing"
            if ok and want_id and want_id not in r["ids"]:
                ok, why = False, f" — {want_id} not among the {len(r['ids'])} shown"
            if ok and want == "exact" and r["tier"] != "exact":
                ok, why = False, f" — matched at tier {r['tier']!r}, not exact"
            if ok and want == "loosened" and r["tier"] not in LOOSENED:
                ok, why = False, (f" — tier {r['tier']!r}: the page never tells the "
                                  "reader it widened")
            # A loosened tier that returns the whole catalogue is not a search.
            # A strict match on a shelf word is a different thing: "coffee"
            # really does reach thousands of cafes, and capping this at 200
            # would forbid the shelf matching WO-4 added.
            # `thesaurus` is left out of the cap on purpose (2026-09-10): a
            # synonym comes from a table, not from slack — "kow soi" reaching
            # every khao soi place through the ข้าวซอย group is the same answer
            # as typing the shelf word, and the shelf holds 322 of them.
            if ok and r["tier"] in ("loose", "partial") and r["n"] > 200:
                ok, why = False, (f" — loosened to {r['n']}; a loosened tier must "
                                  "not return the catalogue")
        print(f"  {'✓' if ok else '✗'} {q!r:22} n={r['n']:<6} "
              f"tier={r['tier'] or '-':10} {note}{why}")
        bad += not ok

    # The rich doors. Run as their own pass so a panel failure reads as a
    # panel failure — the two contracts fail for different reasons and get
    # fixed in different files (search_panels.json vs the matcher).
    print("\n  rich doors — which panel the query opens:")
    pg = run_cases(shipped, pipeline, [c[0] for c in PANEL_CASES])
    if pg is None:
        return 1
    for (q, want_panel, note), r in zip(PANEL_CASES, pg):
        ok = r["panel"] == want_panel
        why = "" if ok else f" — opened {r['panel']!r}, wanted {want_panel!r}"
        print(f"  {'✓' if ok else '✗'} {q!r:42} panel={str(r['panel']):10} {note}{why}")
        bad += not ok

    # WO-69 — the filters and the tag lift. A tag is a filter, not a word:
    # tag= narrows, #word lifts, a lifted constraint (vegan) narrows softly
    # (never to nothing), near= sorts by metres, and an unmet hard filter
    # answers zero rather than everything.
    print("\n  filters — tag= / #word / near= (WO-69):")
    fg = run_cases(shipped, pipeline, [c[0] for c in FILTER_CASES])
    if fg is None:
        return 1
    for (spec, test, note), r in zip(FILTER_CASES, fg):
        try:
            ok, why = test(r)
        except Exception as e:  # noqa: BLE001
            ok, why = False, f" — {e!r}"
        print(f"  {'✓' if ok else '✗'} {json.dumps(spec, ensure_ascii=False)[:44]:44} n={r['n']:<6} {note}{why}")
        bad += not ok

    print(f"\n{'✓ search matcher OK' if not bad else f'✗ {bad} search case(s) failed'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
