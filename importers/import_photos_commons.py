#!/usr/bin/env python3
"""Pull real, properly-licensed wat photos out of mueang-map's existing Commons
crawl (data/canonical/osm*.json, field 'media' — already resolved & attributed,
no new discovery needed) into assets/photos/. One photo per record, snapshot-
first (skips ids that already have a file), gentle pause between downloads,
identified User-Agent. Credits (author/license/source) land in
assets/photos/credits.json so build.py can render proper attribution.

  python3 importers/import_photos_commons.py
"""
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUEANG_MAP = ROOT.parent / "mueang-map" / "data" / "canonical"
PHOTOS = ROOT / "assets" / "photos"
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; one-time Commons photo import)"
PAUSE = 0.4

SOURCES = {"cm": "osm.json", "cr": "osm-chiang-rai.json"}


def target_id(province, record):
    """Mirror import_all.py's import_mueang_map() id scheme exactly."""
    src = (record.get("sources") or [{}])[0]
    ref = src.get("ref", f"mm/{record['id']}")
    return f"{province}-osm-" + ref.replace("/", "-")


def ext_of(url):
    for e in (".jpeg", ".jpg", ".png", ".webp"):
        if url.lower().split("?")[0].endswith(e):
            return ".jpg" if e == ".jpeg" else e
    return ".jpg"


def main():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    credits_path = PHOTOS / "credits.json"
    credits = json.loads(credits_path.read_text()) if credits_path.exists() else {}

    fetched = skipped = failed = 0
    for province, fname in SOURCES.items():
        data = json.loads((MUEANG_MAP / fname).read_text())
        for r in data:
            media = r.get("media")
            if not media:
                continue
            mid = target_id(province, r)
            m = media[0]
            existing = list(PHOTOS.glob(f"{mid}.*"))
            if existing:
                # File's already here (maybe from an earlier interrupted run) —
                # still worth backfilling credits, which are cheap to redo.
                if mid not in credits:
                    credits[mid] = {
                        "author": m.get("author"), "license": m.get("license"),
                        "licenseUrl": m.get("licenseUrl"), "source": m.get("source"),
                        "credit": m.get("credit"),
                    }
                    credits_path.write_text(json.dumps(credits, ensure_ascii=False, indent=1))
                skipped += 1
                continue
            url = m.get("thumb") or m.get("url")
            if not url:
                continue
            fname_out = mid + ext_of(url)
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    (PHOTOS / fname_out).write_bytes(resp.read())
            except Exception as e:
                print(f"  {mid}: FAILED — {e}")
                failed += 1
                continue
            credits[mid] = {
                "author": m.get("author"), "license": m.get("license"),
                "licenseUrl": m.get("licenseUrl"), "source": m.get("source"),
                "credit": m.get("credit"),
            }
            credits_path.write_text(json.dumps(credits, ensure_ascii=False, indent=1))
            fetched += 1
            print(f"  {mid}: {fname_out} ({m.get('license')})")
            time.sleep(PAUSE)
    print(f"done — fetched {fetched}, already had {skipped}, failed {failed}")


if __name__ == "__main__":
    main()
