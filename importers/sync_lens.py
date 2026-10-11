#!/usr/bin/env python3
"""Push each lens's search door and thesaurus out to where search reads them.

A lens JSON (data/curated/lens/<key>.json) carries its own `panel` (the rich
door search.html lays over the rows) and `thesaurus` groups. Search reads
panels from data/curated/search_panels.json and the thesaurus from
search-core's hand file, so this copies them across — upsert by panel id,
placed after the `ot` panel (narrow before broad, the WO-24 rule), and
thesaurus groups appended only when no word of the group is already known.

  python3 importers/sync_lens.py           # sync every lens
  python3 importers/sync_lens.py --check   # exit 1 if a lens is out of step

Run search-core/rollout.sh afterwards so the tables mine, sync and prove
parity; a build picks them up on its own.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PANELS = ROOT / "data" / "curated" / "search_panels.json"
HAND = ROOT.parent / "search-core" / "data" / "hand.thesaurus.json"
ANCHOR = "ot"


def main():
    check = "--check" in sys.argv
    lenses = [json.loads(p.read_text(encoding="utf-8"))
              for p in sorted((ROOT / "data" / "curated" / "lens").glob("*.json"))]
    lenses = [l for l in lenses if not l.get("draft")]
    panels = json.loads(PANELS.read_text(encoding="utf-8"))
    ids = [p["id"] for p in panels["panels"]]
    drift, changed = [], False
    for lens in lenses:
        panel = lens.get("panel")
        if not panel:
            continue
        panel = dict(panel)
        panel.setdefault("id", lens["key"])
        panel.setdefault("doors", [])
        if not any(d.get("href") == f'{lens["key"]}.html' for d in panel["doors"]):
            panel["doors"].insert(0, {"href": f'{lens["key"]}.html', "main": True,
                                      "label": [f'หน้า{lens["title"][0]}', f'the {lens["title"][1]} page']})
        if panel["id"] in ids:
            i = ids.index(panel["id"])
            if panels["panels"][i] != panel:
                drift.append(panel["id"])
                panels["panels"][i] = panel
                changed = True
        else:
            anchor = ids.index(ANCHOR) + 1 if ANCHOR in ids else len(ids)
            panels["panels"].insert(anchor, panel)
            ids.insert(anchor, panel["id"])
            drift.append(panel["id"])
            changed = True
    if changed and not check:
        PANELS.write_text(json.dumps(panels, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"panels: {', '.join(drift)} written")
    elif drift:
        print(f"panels out of step: {', '.join(drift)}")

    if HAND.exists():
        hand = json.loads(HAND.read_text(encoding="utf-8"))
        known = {w for g in hand for w in g}
        added = []
        for lens in lenses:
            for group in lens.get("thesaurus") or []:
                if any(w in known for w in group):
                    continue
                hand.append(group)
                known.update(group)
                added.append(group[0])
        if added and not check:
            HAND.write_text(json.dumps(hand, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"thesaurus: {len(added)} group(s) added ({', '.join(added)}) — run search-core/rollout.sh")
        elif added:
            print(f"thesaurus groups missing: {', '.join(added)}")
            drift += added
    if check and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
