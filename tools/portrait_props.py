#!/usr/bin/env python3
"""Which portrait props to draw next (data/curated/portrait_props.json, assets/front/doodler-props.js).

    python3 tools/portrait_props.py            # reach of every prop, the next three to draw, unmapped tags
    python3 tools/portrait_props.py --next 3   # only the ids of the next three, one per line
    python3 tools/portrait_props.py --sample <prop> [n]   # place ids that would wear it, for doodler_sheet.py

Reach = photo-less places with a portrait scene whose tags call for the prop, read from the last
build's docs/data/places.json. Unmapped tags: the commonest tags on those places, from the
tags.json families that say what a place has or does (DRAWABLE), that no prop names yet.
"""
import collections
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import doodles_layer  # noqa: E402

PROPS_F = ROOT / "data/curated/portrait_props.json"
DRAWABLE = {"cuisine", "diet", "pay", "comfort", "hours", "access", "honours", "medical", "fuel"}   # tags.json families


def drawable_tags():
    doc = json.loads((ROOT / "data/tags.json").read_text())
    return {t["slug"] for t in doc.get("tags", []) if t.get("family") in DRAWABLE} - {"open-monday", "open-sunday"}


def portrait_places():
    rows = json.loads((ROOT / "docs/data/places.json").read_text())
    ci = json.loads((ROOT / "data/commons_images.json").read_text())
    band = {os.path.basename(f)[:-4] for f in glob.glob(str(ROOT / "assets/band/place/*.jpg"))}
    for r in rows:
        if r.get("photo") or r["id"] in band or (ci.get(r["id"]) or {}).get("file"):
            continue
        sc = doodles_layer.place_scene(r)
        if sc:
            yield r, sc


def main(a):
    props = json.loads(PROPS_F.read_text())["props"]
    reach, tagn, sample = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    mapped = {t for p in props.values() for t in p.get("tags") or ()}
    cand = drawable_tags() - mapped
    for r, sc in portrait_places():
        ts = set(r.get("tags") or ())
        for k, p in props.items():
            if ts & set(p.get("tags") or ()) and sc not in (p.get("not_scenes") or ()):
                reach[k] += 1
                if len(sample[k]) < 40:
                    sample[k].append((r["id"], sc))
        for t in ts & cand:
            tagn[t] += 1
    todo = sorted((k for k in props if not props[k].get("drawn")), key=lambda k: -reach[k])
    if "--next" in a:
        print("\n".join(todo[:int(a[a.index("--next") + 1])]))
        return
    if "--sample" in a:
        k = a[a.index("--sample") + 1]
        n = int(a[a.index("--sample") + 2]) if len(a) > a.index("--sample") + 2 else 6
        seen, out = set(), []
        for pid, sc in sample[k]:        # one per scene first, so the sheet shows the prop in several settings
            if sc not in seen:
                seen.add(sc)
                out.append(pid)
        out += [pid for pid, _ in sample[k] if pid not in out]
        print(" ".join("p=" + x for x in out[:n]))
        return
    print("drawn:")
    for k in sorted((k for k in props if props[k].get("drawn")), key=lambda k: -reach[k]):
        print("  %-10s %6d  %s" % (k, reach[k], props[k]["drawn"]))
    print("to draw, by reach:")
    for k in todo:
        print("  %-10s %6d  %s" % (k, reach[k], ", ".join(props[k]["tags"])))
    print("next three:", " ".join(todo[:3]) or "none mapped — map more from the tags below")
    print("commonest unmapped tags on photo-less portrait places:")
    for t, n in tagn.most_common(40):
        print("  %6d  %s" % (n, t))


if __name__ == "__main__":
    main(sys.argv[1:])
