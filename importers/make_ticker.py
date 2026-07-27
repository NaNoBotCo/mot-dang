#!/usr/bin/env python3
"""Bake the home-page news ticker. Reads a cached RSS file if present
(refresh: curl https://www.chiangmainews.co.th/feed/ -o cache/cmnews.xml),
always includes the house items. Output: data/ticker.json (folded into docs/ by build.py).
No network here — fetching is a separate, deliberate act.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOUSE = [
    {"th": "🐜 มดแดงเปิดรัง — สารบัญเมืองเชียงใหม่·เชียงราย ฉบับปฐมฤกษ์",
     "en": "🐜 Mot Dang opens the nest — first edition of the CM·CR city directory",
     "url": "index.html"},
    {"th": "★ ของดีเชียงราย: Leila's Designer Consignment และ River Tavern",
     "en": "★ Chiang Rai gems: Leila's Designer Consignment and River Tavern",
     "url": "cr/index.html"},
]


def rss_items(xml_path, limit=6):
    text = Path(xml_path).read_text(encoding="utf-8", errors="replace")
    items = []
    for m in re.finditer(r"<item>(.*?)</item>", text, re.S):
        chunk = m.group(1)
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", chunk, re.S)
        l = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", chunk, re.S)
        if t and l:
            title = re.sub(r"\s+", " ", t.group(1)).strip()
            items.append({"th": title, "en": title, "url": l.group(1).strip(),
                          "src": "เชียงใหม่นิวส์"})
        if len(items) >= limit:
            break
    return items


def main():
    cache = ROOT / "cache" / "cmnews.xml"
    items = list(HOUSE)
    if cache.exists():
        items += rss_items(cache)
    else:
        print("note: no cache/cmnews.xml — ticker ships house items only", file=sys.stderr)
    (ROOT / "data" / "ticker.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ticker: {len(items)} items")


if __name__ == "__main__":
    main()
