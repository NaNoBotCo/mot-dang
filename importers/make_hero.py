#!/usr/bin/env python3
"""Nan's own frames for the front page.

Reads data/curated/hero_picks.json (uuid, slug, pool, scene; the coordinates
stay in that file), finds each frame's 1024 px preview in the Photos library
on this Mac, and writes docs/site/hero/<slug>.jpg and .webp plus
docs/site/hero/index.json.

The index carries slug, pool, scene, width, height, the iconic flag, and —
only for a frame marked pub in the picks — a coordinate rounded to three
decimals, about 110 metres. That is what lets the page prefer a picture of
the ground the reader is standing on. A frame with pub false ships no
coordinate at all.

    python3 importers/make_hero.py
"""
import json, pathlib, subprocess, sys
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = pathlib.Path.home() / "Pictures" / "Photos Library.photoslibrary" / "resources" / "derivatives"
OUT = ROOT / "docs" / "site" / "hero"
PICKS = ROOT / "data" / "curated" / "hero_picks.json"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = json.loads(PICKS.read_text())["rows"]
    out, missing = [], []
    for r in rows:
        u = r["uuid"]
        src = LIB / u[0] / f"{u}_1_105_c.jpeg"
        if not src.exists():
            missing.append(r["slug"]); continue
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        jpg, webp = OUT / f'{r["slug"]}.jpg', OUT / f'{r["slug"]}.webp'
        im.save(jpg, "JPEG", quality=82, optimize=True, progressive=True)
        im.save(webp, "WEBP", quality=76, method=6)
        row = {"slug": r["slug"], "pool": r["pool"], "scene": r["scene"],
               "w": im.width, "h": im.height}
        if r.get("ic"):
            row["ic"] = 1
        if r.get("bg"):
            row["bg"] = 1
        if r.get("pub"):
            row["la"] = round(r["lat"], 3)
            row["lo"] = round(r["lon"], 3)
        out.append(row)
    (OUT / "index.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
    kb = sum(p.stat().st_size for p in OUT.glob("*.webp")) // 1024
    print(f"{len(out)} frames, {kb} KB of webp; missing: {missing or 'none'}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
