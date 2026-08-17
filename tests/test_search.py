#!/usr/bin/env python3
"""The search matcher, exercised against the real index.

This exists because of a bug nobody would have found by reading the code. The
matcher tested the whole query as one unbroken substring, so `rajavej hospital`
scored zero against "Rajavej Chiang Mai Hospital" — the page was built, indexed
and linked, and simply could not be found by anyone typing its name. 5,190 of
the catalogue's names run three words or longer, so the same hole swallowed
`maharaj hospital`, `nimman coffee` and `dental clinic chiang mai`.

The matcher is JavaScript living inside build.py, so the test lifts that exact
block out and runs it under node against docs/data/index.json. No reimplementing
the logic in Python — a paraphrase would pass while the shipped code failed.

    python3 tests/test_search.py          (after a build)
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build.py")
INDEX = os.path.join(os.environ.get("MD_DOCS", os.path.join(ROOT, "docs")), "data", "index.json")

START = "const norm=s=>s.toLowerCase()"
END = "const hits=found.slice(0,200)"

# (query, expect_id or None, expected mode, note)
CASES = [
    ("rajavej hospital", "cm-osm-way-97675282", "",
     "the bug this file exists for: words with two others wedged between them"),
    ("Rajavej Hospital", "cm-osm-way-97675282", "", "case must not matter"),
    ("hospital rajavej", "cm-osm-way-97675282", "", "word order must not matter"),
    ("โรงพยาบาลราชเวช", "cm-osm-way-97675282", "",
     "Thai carries no spaces — one term, matched as it always was"),
    ("rajavey hospitl", "cm-osm-way-97675282", "near",
     "two typos still land, and the page says it loosened"),
    ("maharaj hospital", None, "", "the same word-gap shape, different place"),
    ("wat phra singh", None, "", "a name that WAS contiguous must not regress"),
    ("", None, "", "empty query finds nothing rather than everything"),
    ("   ", None, "", "whitespace is not a search"),
    ("zzzzqqq", None, "", "a real miss still misses — fuzziness must not match all"),
    # WO-4: a reader's spelling is widened through the thesaurus, and the
    # shelf/cuisine/road a place already carries is matched, not just its name.
    ("kow soi", None, "", "romanisation drift — signage in this city uses all of them"),
    ("ข้าวซอย", None, "", "the same dish in Thai finds the same places"),
    ("coffee", None, "", "the shelf is matched, not only names containing 'coffee'"),
    ("นวด", None, "", "a Thai shelf word reaches the massage places"),
    ("temple", None, "", "an English word for a Thai shelf"),
]


def extract_js():
    src = open(BUILD, encoding="utf-8").read()
    i = src.index(START)
    j = src.index(END, i)
    return src[i:src.index("\n", j)]


def main():
    if not os.path.exists(INDEX):
        print(f"✗ {INDEX} missing — run build.py first")
        return 1
    js = extract_js()
    # The matcher widens a reader's spelling through data/search_thesaurus.json,
    # so the test loads the REAL groups. Pointing it at a stub would let a
    # broken group ship green.
    thes_path = os.path.join(ROOT, "data", "search_thesaurus.json")
    thes = json.load(open(thes_path, encoding="utf-8"))["groups"] \
        if os.path.exists(thes_path) else []
    # The shelf words live in one table rather than in every entry, so the
    # harness needs them too — matching on the shelf is half of what WO-4 added.
    cfg = json.load(open(os.path.join(ROOT, "data", "categories.json"), encoding="utf-8"))
    catwords = {c["key"]: f'{c["th"]} \u00b7 {c["en"]}' for c in cfg["categories"]}
    subwords = {}
    for c in cfg["categories"]:
        for ch in c.get("children") or []:
            k = (ch.get("match") or {}).get("sub") or ch.get("key")
            if k:
                subwords.setdefault(k, f'{ch.get("th","")} {ch.get("en","")}'.strip())
    harness = (
        "import fs from 'fs';\n"
        f"const MD_THESAURUS={json.dumps(thes, ensure_ascii=False)};\n"
        f"const MD_CATWORDS={json.dumps(catwords, ensure_ascii=False)};\n"
        f"const MD_SUBWORDS={json.dumps(subwords, ensure_ascii=False)};\n"
        f"const idx=JSON.parse(fs.readFileSync({json.dumps(INDEX)},'utf8'));\n"
        "function search(q){\n" + js + "\n"
        "return {mode,n:found.length,ids:hits.map(e=>e.id)};}\n"
        "const out=JSON.parse(process.argv[2]).map(q=>search(q));\n"
        "console.log(JSON.stringify(out));\n")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        proc = subprocess.run(["node", path, json.dumps([c[0] for c in CASES])],
                              capture_output=True, text=True, timeout=120)
    finally:
        os.unlink(path)
    if proc.returncode:
        print("✗ matcher failed to run under node:\n" + proc.stderr[-800:])
        return 1
    got = json.loads(proc.stdout)

    bad = 0
    for (q, want_id, want_mode, note), r in zip(CASES, got):
        ok = True
        if want_id:
            ok = want_id in r["ids"]
        elif q.strip() and q != "zzzzqqq":
            ok = r["n"] >= 1
        else:
            ok = r["n"] == 0
        if ok and want_mode is not None:
            ok = r["mode"] == want_mode
        # A LOOSENED tier that returns the whole catalogue is not a search —
        # that is what this guard was for. A strict match on a shelf word is a
        # different thing: "coffee" really does reach 1,976 cafes, and capping
        # the guard at 200 would have forbidden the shelf matching WO-4 added.
        if ok and r["mode"] and r["n"] > 200:
            ok = False
            note += f" (loosened to {r['n']} — a loosened tier must not return the catalogue)"
        print(f"  {'✓' if ok else '✗'} {q!r:22} n={r['n']:<5} mode={r['mode'] or '-':6} {note}")
        bad += not ok
    print(f"\n{'✓ search matcher OK' if not bad else f'✗ {bad} search case(s) failed'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
