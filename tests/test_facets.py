#!/usr/bin/env python3
"""The facet vocabulary is written down in three places. Keep them one list.

data/facets.json is the schema. worker/worker.js validates against a hardcoded
copy, because a Cloudflare Worker cannot read the repo at request time. build.py
renders the ticks from the schema. If those drift, the failure is silent in the
worst possible way: a contributor stands in a shop, ticks "has a bakery", presses
save, gets a success message — and the worker quietly discards the key it does
not recognise. Nobody is told, and the fact is lost.

So this test is the thing that makes the duplication safe.

    python3 tests/test_facets.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def main():
    schema = json.loads((ROOT / "data" / "facets.json").read_text())
    sets = schema["sets"]
    print(f"facet schema: {len(sets)} set(s)")

    keys = set()
    for s in sets:
        for f in s["facets"]:
            check(f'{s["key"]}/{f["key"]} has both languages',
                  bool(f.get("th") and f.get("en")))
            check(f'{s["key"]}/{f["key"]} has an icon', bool(f.get("icon")))
            check(f'{s["key"]}/{f["key"]} has a question to ask a passer-by',
                  bool(f.get("ask_th") and f.get("ask_en")))
            keys.add(f["key"])

    # ---- worker vocabulary ------------------------------------------------
    js = (ROOT / "worker" / "worker.js").read_text()
    m = re.search(r"const FACET_KEYS = new Set\(\[(.*?)\]\)", js, re.S)
    check("worker declares FACET_KEYS", bool(m), "regex found no FACET_KEYS block")
    if m:
        wkeys = set(re.findall(r"'([a-z0-9]+)'", m.group(1)))
        missing = keys - wkeys
        extra = wkeys - keys
        check("worker accepts every schema facet", not missing,
              f"worker would silently drop: {sorted(missing)}")
        check("worker accepts nothing the schema lacks", not extra,
              f"worker accepts unknown keys: {sorted(extra)}")

    # ---- importer rules point at real facets ------------------------------
    imp = (ROOT / "importers" / "import_fixtures.py").read_text()
    for key in re.findall(r'\("([a-z0-9]+)", "[a-z_:]+", lambda', imp):
        check(f"importer rule '{key}' names a real facet", key in keys)

    # ---- a claim can never be opened by ticks alone -----------------------
    # Ticking a box must not lock a shop out of its own listing. This is the
    # one facet rule with a victim if it breaks, so it is asserted, not trusted.
    check("facets alone cannot create a claim",
          "FIELDS.some(([k]) => fields[k] !== undefined)" in js,
          "create-mode guard no longer requires a contact field")

    shelves()

    print()
    if failures:
        print(f"{len(failures)} failure(s): {failures}")
        return 1
    print("all facet checks passed")
    return 0


# Shelves that expect a sub nobody emits are invisible in the worst way: the
# shelf renders as a muted "the ants are still collecting" wireframe, which
# reads as "we have none of these" when in fact we had 35 tattoo studios, 56
# beauty salons and 40 vegetarian kitchens all along. Nothing errors, nothing
# logs, and the records sit in the data being findable only by search.
#
# So every {sub:} rule must either match records or be on this list, which is
# the set of shelves deliberately left waiting for data that does not exist in
# OSM yet. Adding a name here is a decision; forgetting one is a bug.
KNOWN_EMPTY = {
    ("beauty", "salon"),      # no OSM signal separates a salon from a hairdresser
    ("tattoo", "piercing"),   # shop=piercing is queried; none are mapped here yet
    ("tattoo", "removal"),    # needs curated field truth; OSM has no tag for it
}


def shelves():
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    subs = set()
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if not f.exists():
            continue
        for r in json.loads(f.read_text()):
            for cat in r.get("cat") or []:
                for s in r.get("sub") or []:
                    subs.add((cat, s))

    print("\nshelf rules")
    for c in cats["categories"]:
        for ch in c.get("children", []):
            m = ch.get("match") or {}
            if "sub" not in m:
                continue
            key = (c["key"], ch["key"])
            live = (c["key"], m["sub"]) in subs
            if live or key in KNOWN_EMPTY:
                continue
            near = sorted(s for (cat, s) in subs if cat == c["key"])
            check(f'{c["key"]}/{ch["key"]} finds records', False,
                  f"match sub={m['sub']!r} matches nothing; "
                  f"subs present here: {near}")

    # The mirror: records that reach no shelf at all are equally invisible,
    # just from the other direction. Asked per RECORD, not per (cat, sub) pair
    # — a place carrying cat ['sights','tattoo'] is on a shelf as soon as
    # either category claims its sub, and complaining about the other one would
    # be a false alarm every time.
    claimed = {(c["key"], (ch.get("match") or {}).get("sub"))
               for c in cats["categories"] for ch in c.get("children", [])}
    homeless = {}
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if not f.exists():
            continue
        for r in json.loads(f.read_text()):
            subs_ = r.get("sub") or []
            cats_ = r.get("cat") or []
            if not subs_ or not cats_:
                continue            # no sub at all: it lives on the parent shelf
            if any((c, s) in claimed for c in cats_ for s in subs_):
                continue
            for c in cats_:
                for s in subs_:
                    homeless[(c, s)] = homeless.get((c, s), 0) + 1
    for (cat, s), n in sorted(homeless.items()):
        if n >= 25:
            check(f"{cat}/{s} ({n} records) reaches a shelf", False,
                  "no child of any of these records' categories claims this sub")


if __name__ == "__main__":
    sys.exit(main())
