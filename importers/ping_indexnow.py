#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam, Naver) that a build has landed.

Run this AFTER pushing docs/ — it announces URLs that must already be live.
The key lives in build.py as INDEXNOW_KEY and is published at /<key>.txt;
this script reads it back out so the two can never drift apart.

    python3 importers/ping_indexnow.py            # sitemap-wide, batched
    python3 importers/ping_indexnow.py cm/p/x.html cm/food/index.html
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://motdang.net/"
HOST = "motdang.net"
ENDPOINT = "https://api.indexnow.org/IndexNow"
BATCH = 10000  # IndexNow's documented per-request ceiling

KEY = re.search(r'INDEXNOW_KEY = "([0-9a-f]+)"',
                (ROOT / "build.py").read_text()).group(1)


def urls_from_sitemap():
    sm = (ROOT / "docs" / "sitemap.xml").read_text()
    return re.findall(r"<loc>(.*?)</loc>", sm)


def ping(urls):
    body = json.dumps({"host": HOST, "key": KEY,
                       "keyLocation": f"{BASE}{KEY}.txt",
                       "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def main():
    urls = ([BASE + a.lstrip("/") for a in sys.argv[1:]] if len(sys.argv) > 1
            else urls_from_sitemap())
    if not (ROOT / "docs" / f"{KEY}.txt").exists():
        sys.exit("key file missing from docs/ — run build.py first")
    for i in range(0, len(urls), BATCH):
        chunk = urls[i:i + BATCH]
        print(f"pinging {len(chunk):,} urls -> {ping(chunk)}")


if __name__ == "__main__":
    main()
