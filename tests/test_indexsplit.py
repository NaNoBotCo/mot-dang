#!/usr/bin/env python3
"""The index in two files still adds up to the index.

The one question worth asking: after a real catalogue is split and the two
halves are merged back together by the SHIPPED JavaScript, is every row the
row it was? Everything else here is a corollary.

It runs against a real index — docs/data/index.json if a build has left one,
otherwise the live site's, fetched once and cached in the scratch dir. No
build needed.

    python3 tests/test_indexsplit.py
    MD_INDEX=/path/to/index.json python3 tests/test_indexsplit.py
"""
import json
import os
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import indexsplit_layer as S  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else "  — " + detail))
    if not ok:
        FAIL.append(name)


def load_index():
    p = os.environ.get("MD_INDEX")
    if p:
        return json.loads(Path(p).read_text()), p
    built = ROOT / "docs" / "data" / "index.json"
    if built.exists():
        return json.loads(built.read_text()), str(built)
    # The live index, as a last resort. curl and not urllib: the site is
    # behind Cloudflare and a request with no user agent gets a 403, which
    # looks like the file is missing when it is not.
    cached = Path(tempfile.gettempdir()) / "md-live-index.json"
    if not cached.exists():
        r = subprocess.run(["curl", "-sf", "--compressed", "-o", str(cached),
                            "https://motdang.net/data/index.json"])
        if r.returncode != 0 or not cached.exists():
            print("no index on disk and the live one could not be fetched — "
                  "build first, or point MD_INDEX at one")
            sys.exit(0)
    return json.loads(cached.read_text()), str(cached)


HARNESS = r"""'use strict';
const fs=require('fs');
const first=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const second=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
global.window={};
global.document=undefined;
__SPLIT__
window.MDIDX.merge(first,second);
/* provinces() is part of fill(); merge() alone must not invent one */
const derived=first.map(r=>window.MDIDX.PROV[r.p]).filter(Boolean).length;
for(const r of first)if(window.MDIDX.PROV[r.p])r.pv=window.MDIDX.PROV[r.p];
console.log(JSON.stringify({rows:first.length,derived,full:window.MDIDX.isFull()}));
fs.writeFileSync(process.argv[4],JSON.stringify(first));
"""


def main():
    if subprocess.run(["which", "node"], capture_output=True).returncode != 0:
        print("node not found — skipping")
        return 0
    rows, src = load_index()
    print(f"{len(rows):,} rows from {src}\n")

    first, second = S.split(rows)

    def gz(o):
        return len(zlib.compress(json.dumps(o, ensure_ascii=False).encode(), 6))

    was, now, rest = gz(rows), gz(first), gz(second)
    print("WHAT A READER PAYS BEFORE AN ANSWER")
    print(f"  before          {was:>10,} gzipped")
    print(f"  first file      {now:>10,}   ({100 * now / was:.0f}%)")
    print(f"  second file     {rest:>10,}   follows, not waited on")
    print(f"  saved           {was - now:>10,}   ({100 * (was - now) / was:.0f}%)\n")

    d = tempfile.mkdtemp()
    fp, sp, op = f"{d}/1.json", f"{d}/2.json", f"{d}/out.json"
    Path(fp).write_text(json.dumps(first, ensure_ascii=False))
    Path(sp).write_text(json.dumps(second, ensure_ascii=False))
    hp = f"{d}/h.js"
    Path(hp).write_text(HARNESS.replace("__SPLIT__", S.js()))
    p = subprocess.run(["node", hp, fp, sp, op], capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[:2000])
        return 1
    info = json.loads(p.stdout.strip().splitlines()[-1])
    merged = json.loads(Path(op).read_text())

    print("THE ROUND TRIP — the shipped JS merges the two halves back")
    check("every row survives", len(merged) == len(rows),
          f"{len(merged)} vs {len(rows)}")
    check("merge reports itself full", info["full"], "isFull() false")

    # Coordinates are rounded on purpose; everything else must be identical.
    diffs, coord_moved, worst = [], 0, 0.0
    for a, b in zip(rows, merged):
        for k in set(a) | set(b):
            va, vb = a.get(k), b.get(k)
            if k in ("lat", "lng"):
                if va is None and vb is None:
                    continue
                if va is None or vb is None:
                    diffs.append((a.get("id"), k, va, vb)); continue
                if va != vb:
                    coord_moved += 1
                    worst = max(worst, abs(va - vb))
                continue
            if va != vb:
                diffs.append((a.get("id"), k, va, vb))
    check("every other field is byte-identical after the round trip",
          not diffs, f"{len(diffs)} differ, e.g. {diffs[:3]}")
    # 1e-5 degrees of latitude is ~1.11 m; longitude at 18.8°N is ~1.05 m.
    metres = worst * 111_320
    check("no coordinate moves more than a metre and a half",
          metres < 1.5, f"worst {metres:.2f} m on {coord_moved:,} rows")
    print(f"    ({coord_moved:,} coordinates rounded, worst move {metres:.2f} m)")

    print("\nTHE RULES THIS MUST NOT BREAK")
    check("`pv` is derivable for every row that had one",
          info["derived"] == sum(1 for r in rows if r.get("pv")),
          f"{info['derived']} derived vs {sum(1 for r in rows if r.get('pv'))} held")
    check("`id` stays in the first file — events and the claim worker join on it",
          all("id" in r for r in first), "an id went missing")
    check("`s` stays in the first file — a drawn row is a link immediately",
          all(("s" in f2) == ("s" in r) for f2, r in zip(first, rows)), "a slug moved")
    check("a row with nothing to draw costs one byte, not two",
          any(x == 0 for x in second) or all(x for x in second),
          "empty rows are not 0")
    check("the second file carries no ids and no keys the first has",
          not any(isinstance(x, dict) and ({"id", "n", "s", "k"} & set(x)) for x in second),
          "duplicate keys in the second file")

    print("\nNO BUDGET IS ASSERTED HERE")
    # The 10 MB ceiling this work replaces was a module-level constant that
    # nobody agreed to and every later session inherited. So: no module-level
    # constant here may name itself a maximum, and `report()` may only build
    # a string. Checked on the parse tree, not by grepping for a word — this
    # test's own source contains the word.
    import ast
    tree = ast.parse((ROOT / "indexsplit_layer.py").read_text())
    ceilings = [t.id for n in tree.body if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)
                and ("MAX" in t.id or "MIN" in t.id or "BUDGET" in t.id
                     or "LIMIT" in t.id)]
    check("the module declares no ceiling of its own", not ceilings, str(ceilings))
    rep = next((n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "report"), None)
    check("report() only reports — it raises nothing and asserts nothing",
          rep is not None and not any(
              isinstance(x, (ast.Assert, ast.Raise)) for x in ast.walk(rep)),
          "report() can fail a build")

    print()
    if FAIL:
        print(f"{len(FAIL)} FAILED: " + "; ".join(FAIL))
        return 1
    print("all green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
