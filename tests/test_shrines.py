#!/usr/bin/env python3
"""The shrine register stands on what it can show, or this fails. WO-39.

    python3 tests/test_shrines.py
    MD_DOCS=/path/to/scratch python3 tests/test_shrines.py

Run after build.py. The rule it enforces is the proposal note's: the keeper
names the shrine; the calendar carries its source; nothing here awards
power. Concretely:

  1. every register row has a kind the register defines, a province the
     register defines, at least one name, and a confidence this file knows;
  2. a `recordId` (and every companion) resolves to a canonical record —
     a register row pointing at a record that is not there is a dead link
     with this site's name on it;
  3. a row marked `stated` carries at least one source with a `fetched`
     date — "stated" with nothing read is just an opinion wearing a chip;
  4. a row marked `awaiting_pin` truly has no pin through its records —
     a stale flag would tell readers a mapped shrine is unmapped;
  5. a `festival` tie points at a festival that exists in festivals.json;
  6. the shelf agrees: every sub=shrine record sits on cat wat, and the
     shelf is no longer empty (the emptiness was the finding this order
     opened with — going back would be a silent regression);
  7. the words reach it: the thesaurus rings city pillar ↔ หลักเมือง and
     the wat tree carries the shrine child;
  8. after a build, san.html + san.css + data/shrines.json exist, the page
     renders one row per register entry, and no unfilled None leaked.
"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = pathlib.Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))

fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)


reg = json.loads((ROOT / "data" / "shrines.json").read_text())
rows = reg.get("shrines", [])
kinds = set(reg.get("kinds", {}))
provinces = set(reg.get("provinces", {}))
CONF = {"record", "stated", "general-knowledge", "needs-verification"}

canonical = {}
for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
    for r in json.loads(f.read_text()):
        canonical[r["id"]] = r

festivals = {e.get("id") for e in json.loads(
    (ROOT / "data" / "festivals.json").read_text())["festivals"]}

keys = [s.get("key") for s in rows]
check(len(keys) == len(set(keys)), "register keys are not unique")
check(len(rows) >= 15, f"register unexpectedly small ({len(rows)} rows)")

for s in rows:
    k = s.get("key") or "?"
    check(s.get("kind") in kinds, f"{k}: kind {s.get('kind')} not defined")
    check(s.get("province") in provinces, f"{k}: province {s.get('province')} not defined")
    check(bool(s.get("nameTh") or s.get("nameEn")), f"{k}: no name at all")
    check(s.get("confidence") in CONF, f"{k}: confidence {s.get('confidence')} unknown")
    for rid in [s.get("recordId")] + (s.get("companionIds") or []):
        if rid:
            check(rid in canonical, f"{k}: record {rid} not in canonical")
    if s.get("confidence") == "stated":
        check(any(src.get("fetched") for src in s.get("sources") or []),
              f"{k}: stated, but no source carries a fetched date")
    if s.get("awaiting_pin"):
        pin = None
        for rid in [s.get("recordId")] + (s.get("companionIds") or []):
            r = canonical.get(rid or "")
            if r and r.get("lat") is not None:
                pin = rid
        check(pin is None, f"{k}: awaiting_pin, but {pin} carries a pin — stale flag")
    if s.get("festival"):
        check(s["festival"] in festivals,
              f"{k}: festival {s['festival']} not in festivals.json")

shelf = [r for r in canonical.values() if "shrine" in (r.get("sub") or [])]
check(len(shelf) >= 10, f"shrine shelf holds {len(shelf)} records — the empty "
                        "shelf was the finding this order opened with")
for r in shelf:
    check("wat" in (r.get("cat") or []),
          f"{r['id']}: sub=shrine but not on cat wat")

thes = json.loads((ROOT / "data" / "search_thesaurus.json").read_text())
check(any("city pillar" in g and "หลักเมือง" in g for g in thes["groups"]),
      "thesaurus: no city pillar ↔ หลักเมือง ring")
cats = json.loads((ROOT / "data" / "categories.json").read_text())
wat = [c for c in cats["categories"] if c["key"] == "wat"][0]
check(any(ch.get("key") == "shrine" for ch in wat.get("children", [])),
      "categories: wat has no shrine child")

if (DOCS / "index.html").exists():
    check((DOCS / "san.html").exists(), "built docs/ has no san.html")
    check((DOCS / "san.css").exists(), "built docs/ has no san.css")
    check((DOCS / "data" / "shrines.json").exists(),
          "built docs/ has no data/shrines.json")
    if (DOCS / "san.html").exists():
        html = (DOCS / "san.html").read_text()
        n_rendered = html.count('class="sn-row"')
        check(n_rendered == len(rows),
              f"san.html renders {n_rendered} rows for {len(rows)} register entries")
        check(">None<" not in html and "None</" not in html.replace("None</a", ""),
              "san.html leaks a Python None")
        check("sn-rule" in html, "san.html lost the rule box")

if fails:
    print(f"test_shrines: {len(fails)} failure(s)")
    for m in fails:
        print("  FAIL", m)
    sys.exit(1)
print(f"test_shrines: OK — {len(rows)} register rows, {len(shelf)} shelf records"
      + (", page checked" if (DOCS / "san.html").exists() else ", no build to check"))
