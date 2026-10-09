#!/usr/bin/env python3
"""Nets: every member page shows every other member, and nothing dead.

    python3 tests/test_nets.py

No build needed: net_layer is bound to the canonical data with stand-in helpers.

  1. every jewel id is a record in data/canonical/, and no id appears twice in a net;
  2. every jewel carries a Thai and an English line, and every net names its sources;
  3. each member's page links to every other member once and marks itself, unlinked;
  4. a place outside every net renders nothing.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import net_layer  # noqa: E402

H = {"bi": lambda th, en: "%s|%s" % (th, en), "esc": str,
     "att": lambda s: str(s).replace('"', "&quot;"),
     "name_bi": lambda r: r.get("name") or r["id"],
     "reading": lambda th: th}


def main():
    data = {p: json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text())
            for p in ("cm", "cr")}
    # A curated addition reaches data/canonical/ at the next import_all run.
    for p, f in (("cm", "additions-chiang-mai.json"), ("cr", "additions-chiang-rai.json")):
        seen = {r["id"] for r in data[p]}
        data[p] += [r for r in json.loads((ROOT / "data" / "curated" / f).read_text())
                    if r["id"] not in seen]
    href = {r["id"]: "%s/p/%s" % (p, r["id"]) for p, recs in data.items() for r in recs}
    net_layer.bind(data, href)
    fails = []
    for key, net in net_layer.load().items():
        ids = [j["id"] for s in net["strands"] for j in s["jewels"]]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            fails.append("%s: repeated %s" % (key, sorted(dup)))
        missing = [i for i in ids if i not in href]
        if missing:
            fails.append("%s: no record for %s" % (key, missing))
        if not net.get("sources"):
            fails.append("%s: no sources" % key)
        for s in net["strands"]:
            for j in s["jewels"]:
                if not (j.get("th") and j.get("en")):
                    fails.append("%s: %s lacks a Thai or English line" % (key, j["id"]))
        present = [i for i in ids if i in href]
        for i in present:
            html = net_layer.block({"id": i}, H)
            linked = re.findall(r'href="\.\./\.\./(?:cm|cr)/p/([^"]+)\.html"', html)
            if i in linked:
                fails.append("%s: %s links to itself" % (key, i))
            # A place in several nets shows each of them, and is marked once in each.
            mine = net_layer.nets_of(i)
            want = [x for _, n in mine for s in n["strands"] for x in (j["id"] for j in s["jewels"])
                    if x in href and x != i]
            if sorted(linked) != sorted(want):
                fails.append("%s: %s does not show the whole net" % (key, i))
            if html.count('class="here"') != len(mine):
                fails.append("%s: %s is not marked once per net" % (key, i))
    if net_layer.block({"id": "not-a-member"}, H):
        fails.append("a non-member rendered a net")
    for f in fails:
        print("FAIL", f)
    print("nets: %s" % ("ok" if not fails else "%d failures" % len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
