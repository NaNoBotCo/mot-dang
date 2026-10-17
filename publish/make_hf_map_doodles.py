#!/usr/bin/env python3
"""The map doodles as a Hugging Face dataset: publish/hf/map-doodles/, pushed by hf_push.py.

    python3 publish/make_hf_map_doodles.py
    python3 publish/hf_push.py publish/hf/map-doodles NaNoBotCo/map-doodles

images/<id>.png (256 px, rendered from the SVG by rsvg-convert) with images/metadata.jsonl, so the
dataset viewer shows each drawing beside its names, tags and point; svg/ and the manifest ride along.
"""
import json
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "assets" / "sites" / "map-doodles"
OUT = ROOT / "publish" / "hf" / "map-doodles"

CARD = """---
license: cc-by-4.0
pretty_name: Map Doodles
language:
- en
- th
size_categories:
- n<1K
tags:
- maps
- icons
- svg
- landmarks
- openstreetmap
- wikidata
- illustration
- thailand
configs:
- config_name: default
  data_dir: images
---

# Map Doodles · ภาพวาดสำหรับแผนที่

250 hand-drawn SVG map marks for places anywhere on earth: **%(landmarks)d landmarks** drawn as themselves (the Eiffel Tower, the moai of Rapa Nui, Wat Arun, the Taj Mahal…) and **%(kinds)d kinds of place** (wat, spirit house, songthaew, lighthouse, mosque, fuel station…). Made for the maps of [Mot Dang](https://motdang.net), a city guide to Chiang Mai and Chiang Rai.

Gallery and world map: https://motdang.net/sites/map-doodles/ · source and loader: https://github.com/NaNoBotCo/map-doodles

## Fields (`images/metadata.jsonl`, one row per drawing)

| field | what |
|---|---|
| `file_name` | the 256 px PNG rendered from `svg/<id>.svg` |
| `id` | kebab-case id, also the SVG file name |
| `en`, `th` | name in English and Thai |
| `group` | `landmark` or `kind` |
| `region` | landmarks: thailand, southeast-asia, east-asia, south-asia, middle-east-north-africa, africa, europe, north-america, latin-america, oceania |
| `set` | kinds: nature, wildlife, faith, heritage, structure, transport, civic, leisure, food, shopping, stay, active, amenity |
| `osm` | kinds: the OpenStreetMap tags a place carries when this drawing fits it (`key=value`, `+` joins tags that must all match) |
| `cc`, `city`, `lat`, `lng`, `wd`, `wiki` | landmarks: country code, city, point, Wikidata id, English Wikipedia title |

Each SVG is 64 × 64 and stands on its bottom centre (32, 60), the map point.

## Credit and licence

Drawings and data: CC BY 4.0, credit **"NaN · Mot Dang (motdang.net)"**. Drawn as SVG code by Claude (Anthropic) for Mot Dang, October 2026.

## ภาษาไทย

ภาพวาด 250 ภาพ สำหรับวางบนแผนที่ที่ไหนก็ได้ในโลก ทำขึ้นสำหรับแผนที่ของมดแดง แต่ละภาพมีชื่อภาษาไทยและอังกฤษ แท็ก OpenStreetMap หรือรหัส Wikidata และพิกัด ใช้ได้ภายใต้สัญญาอนุญาต CC BY 4.0 โดยให้เครดิต "NaN · Mot Dang (motdang.net)"
"""

KEYS = ("id", "en", "th", "group", "region", "set", "osm", "cc", "city", "lat", "lng", "wd", "wiki")


def main():
    rows = json.loads((SITE / "map-doodles.json").read_text())
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "images").mkdir(parents=True)
    shutil.copytree(SITE / "svg", OUT / "svg")
    for name in ("map-doodles.json", "map-doodles.svg"):
        shutil.copy2(SITE / name, OUT / name)
    with (OUT / "images" / "metadata.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            png = OUT / "images" / (r["id"] + ".png")
            subprocess.run(["rsvg-convert", "-w", "256", "-h", "256", "-o", str(png), str(SITE / "svg" / (r["id"] + ".svg"))],
                           check=True)
            row = {"file_name": png.name}
            row.update({k: r.get(k) for k in KEYS})
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    n = {"landmarks": sum(r["group"] == "landmark" for r in rows), "kinds": sum(r["group"] == "kind" for r in rows)}
    (OUT / "README.md").write_text(CARD % n, encoding="utf-8")
    print("%s: %d drawings" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
