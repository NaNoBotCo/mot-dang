#!/usr/bin/env python3
"""/sites/doodles/ place data without a full build: docs/data/places.json → docs/data/doodles/
(doodles_layer.gallery). build.py writes the same files on every build;
this is for a day the build cannot run. Pictures a full build knows about (her own, ride
pictures) are not all loaded here, so a few places that show a photo may still be listed.

    python3 tools/doodle_gallery.py [docs-dir]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  place_slug, place_thumb
import doodles_layer  # noqa: E402


def main(a):
    docs = Path(a[0]) if a else ROOT / "docs"
    rows = []
    for r in json.loads((docs / "data/places.json").read_text()):
        if r.get("photo") or build.place_thumb(r["id"]):
            continue
        s = doodles_layer.place_scene(r)
        if s:
            rows.append((r, s, r.get("tags") or [], "%s/p/%s.html" % (r["province"], build.place_slug(r))))
    print(doodles_layer.gallery(docs, rows), "place portraits →", docs / "data/doodles")


if __name__ == "__main__":
    main(sys.argv[1:])
