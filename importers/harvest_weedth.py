#!/usr/bin/env python3
"""Names and addresses of cannabis shops from weed.th, and nothing else.

WHY THIS EXISTS. OpenStreetMap has 33 cannabis shops across Chiang Mai and
Chiang Rai. The trade is twenty times that. weed.th publishes a sitemap listing
678 shops in Chiang Mai and 161 in Chiang Rai, and their robots.txt invites
crawlers explicitly (Crawl-delay: 1, nothing disallowed but /current-location).
That is the plain city data nobody else bothered to write down.

WHAT IS TAKEN, and it is less than you would hope. Measured on three shop pages
before a single line of this was written: the server HTML carries a schema.org
Store block with `name`, `address` and an `image` URL. It does NOT carry the
phone, the opening hours or the coordinates — those are behind a button and
arrive from somewhere this never looks. So this importer takes a NAME and an
ADDRESS. Do not come back expecting it to fill contacts; it cannot, and a
comment promising otherwise would send somebody hunting for a bug that is not
there.

WHAT IS NEVER TAKEN. The pages carry a rating and a wall of reviews, and both
are refused — not skipped for convenience, refused. This site holds no ratings
by rule (CLAUDE.md), and these particular ones are Google's: every review
author links to google.com/maps/contrib/. Thailand is the SEO capital of the
world and a Google rating on a Chiang Mai shopfront is not evidence about that
shop. Republishing them would import somebody else's manipulated numbers and
stamp our name on them. `_strip_refused()` removes them at parse time so they
cannot reach a record even by accident, and there is a test for it.

MANNERS. Their robots.txt asks for 1 second between requests. This waits
EIGHT, because 839 pages is a lot to ask of somebody else's server and we are
in no hurry. Snapshot-first into cache/weedth/, so an interrupted run resumes
and a re-run costs them nothing. One page per shop, ever. A User-Agent that
says who we are and where to complain.

    python3 importers/harvest_weedth.py --dry-run --limit 5
    python3 importers/harvest_weedth.py --limit 50
    python3 importers/harvest_weedth.py

Output: data/curated/weedth.json — curated, so no crawl overwrites it, with the
source URL and fetch date on every entry.
"""
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "weedth")
OUT = os.path.join(ROOT, "data", "curated", "weedth.json")
SITEMAP = "https://weed.th/sitemap.xml"
BASE = "https://weed.th"
UA = ("MotDangBot/1.0 (+https://motdang.net/about.html; "
      "Chiang Mai + Chiang Rai directory; 530kings@proton.me)")
DELAY = 8.0          # their robots.txt asks 1; eight is the polite answer
TIMEOUT = 25
CITIES = {"chiang-mai": "cm", "chiang-rai": "cr"}

SHOP_URL = re.compile(
    r"^https://weed\.th/shop/([0-9a-f-]{36})/(chiang-mai|chiang-rai)/(.+)$")

# Everything here is refused on purpose. See the module docstring.
REFUSED = ("review", "reviews", "aggregateRating", "ratingValue", "ratingCount",
           "bestRating", "worstRating")


def _strip_refused(node):
    """Remove ratings and reviews from a parsed schema.org block, recursively.

    Done at parse time rather than at write time so a refused field cannot
    survive into a record through some later path nobody thought about.
    """
    if isinstance(node, dict):
        return {k: _strip_refused(v) for k, v in node.items() if k not in REFUSED}
    if isinstance(node, list):
        return [_strip_refused(v) for v in node]
    return node


def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "th,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


_rp = None


def allowed(url):
    """Read their robots.txt once and believe it."""
    global _rp
    if _rp is None:
        _rp = urllib.robotparser.RobotFileParser()
        try:
            _rp.parse(get(BASE + "/robots.txt").splitlines())
        except Exception:
            _rp = False
        time.sleep(DELAY)
    if _rp is False:
        return True
    try:
        return _rp.can_fetch(UA, url)
    except Exception:
        return True


def shop_urls():
    """(uuid, province, slug, url) for every Chiang Mai / Chiang Rai shop."""
    path = os.path.join(CACHE, "sitemap.xml")
    if os.path.exists(path):
        xml = open(path, encoding="utf-8", errors="replace").read()
    else:
        xml = get(SITEMAP)
        os.makedirs(CACHE, exist_ok=True)
        open(path, "w", encoding="utf-8").write(xml)
        time.sleep(DELAY)
    out, seen = [], set()
    for u in re.findall(r"<loc>(.*?)</loc>", xml):
        m = SHOP_URL.match(u)
        if not m:
            continue
        uuid, city, slug = m.group(1), m.group(2), urllib.parse.unquote(m.group(3))
        if uuid in seen:
            continue
        seen.add(uuid)
        out.append((uuid, CITIES[city], slug, u))
    return out


def store_block(html_text):
    """The schema.org Store block, with ratings and reviews already gone."""
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
                         html_text, re.S | re.I):
        try:
            doc = json.loads(unescape(m.group(1).strip()))
        except Exception:
            continue
        stack = [doc]
        while stack:
            cur = stack.pop()
            if isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, dict):
                if str(cur.get("@type", "")) in ("Store", "LocalBusiness"):
                    return _strip_refused(cur)
                stack.extend(v for v in cur.values() if isinstance(v, (dict, list)))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refetch", action="store_true")
    args = ap.parse_args()

    os.makedirs(CACHE, exist_ok=True)
    doc = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    shops = shop_urls()
    todo = [s for s in shops
            if args.refetch or not os.path.exists(os.path.join(CACHE, s[0] + ".html"))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"🐜 weed.th: {len(shops)} shops in the sitemap "
          f"(cm {sum(1 for s in shops if s[1]=='cm')}, "
          f"cr {sum(1 for s in shops if s[1]=='cr')}); "
          f"{len(todo)} to fetch at {DELAY:g}s apart")
    if todo and not allowed(todo[0][3]):
        print("   robots.txt says no — stopping."), exit(1)

    today, got, blank, broke = date.today().isoformat(), 0, 0, 0
    for i, (uuid, prov, slug, url) in enumerate(todo, 1):
        path = os.path.join(CACHE, uuid + ".html")
        if os.path.exists(path) and not args.refetch:
            page = open(path, encoding="utf-8", errors="replace").read()
        else:
            try:
                page = get(url)
            except Exception as e:
                broke += 1
                print(f"  {i:4}/{len(todo)} unreachable  {slug[:40]:40} {str(e)[:34]}")
                time.sleep(DELAY)
                continue
            open(path, "w", encoding="utf-8").write(page)
            time.sleep(DELAY)
        st = store_block(page)
        if not st or not st.get("name"):
            blank += 1
            continue
        entry = {
            "name": st["name"].strip(),
            "province": prov,
            "src": url,
            "fetched": today,
        }
        addr = st.get("address")
        if isinstance(addr, str) and addr.strip():
            entry["address"] = addr.strip()
        img = st.get("image")
        if isinstance(img, list) and img:
            img = img[0]
        if isinstance(img, str) and img.startswith("http"):
            # Recorded as a POINTER, never downloaded and never republished as
            # ours. Their CDN, their bandwidth, their picture.
            entry["photoRef"] = img
        doc[uuid] = entry
        got += 1
        if i % 25 == 0 or i == len(todo):
            print(f"  {i:4}/{len(todo)}  kept {got}")

    doc["_note"] = ("Names and addresses only. Ratings and reviews are refused "
                    "at parse time — see importers/harvest_weedth.py. "
                    "Fetched one page per shop, 8s apart, robots.txt obeyed.")
    print(f"\n🐜 kept {got} · no Store block {blank} · unreachable {broke}")
    if args.dry_run:
        print("   --dry-run: nothing written")
        return
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"   -> {OUT}  ({sum(1 for k in doc if not k.startswith('_'))} shops)")


if __name__ == "__main__":
    main()
