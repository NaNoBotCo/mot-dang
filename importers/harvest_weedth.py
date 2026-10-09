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

WHAT IS NEVER TAKEN. The pages carry a rating and a wall of reviews. The
rating is refused — not skipped for convenience, refused. This site holds no
ratings by rule (CLAUDE.md), and these particular ones are Google's: every
review author links to google.com/maps/contrib/. Thailand is the SEO capital
of the world and a Google rating on a Chiang Mai shopfront is not evidence
about that shop. Republishing them would import somebody else's manipulated
numbers and stamp our name on them. `_strip_refused()` removes ratings and
review text at parse time so they cannot reach a record even by accident, and
there is a test for it.

THE ONE THING READ OUT OF A REVIEW, AND WHY (Nan, 2026-09-21). She searched
the live site for kratom, got one shop, and said to read the reviews for it.
`offers_from_reviews()` runs BEFORE the strip and takes one thing: whether a
visitor said they bought a named product here. It returns product keys and a
count. No text, no author, no date, no rating, no link — none of it reaches an
entry, a record or a page, and the wording of a review is never republished.

A review is not a name, an address, an hour or a neighbour, which is what the
offers field forbids inferring from; it is somebody saying what they walked
out with. It is also the weakest source in OFFER_VIA and prints as one.

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


# Product keys read out of review text, and the wordings that earn each.
# Latin needs a word boundary so "Kratom" never lights up inside another word.
# Thai bare กระท่อม is the leaf HERE and a hut almost everywhere else — every
# page in this cache is a cannabis shop's, so the source calibrates the word,
# the same guard tags_mine.earn_by_name() uses. Do not lift this table onto
# the open corpus: 35 of the 37 กระท่อม names in the two provinces are farm
# shelters (notes/kratom-2026-09-21.txt).
OFFER_WORDS = {
    "kratom": (re.compile(r"\b(?:kratom|krathom|ketum)\b", re.I),
               re.compile(r"ใบกระท่อม|น้ำกระท่อม|น้ำท่อม|ใบท่อม|กระท่อม")),
}

# A customer ASKING whether a shop sells something is not evidence that it
# does. Measured 2026-09-21: "มีน้ำท่อมขายไหมครับ" on ร้าน Color Beauty — a
# beauty salon — was the only thing that put it on the kratom list.
_ASKING = re.compile(
    r"ไหม|มั้ย|มัย|หรือเปล่า|รึเปล่า|ป่าว|"
    r"do you have|do they have|does anyone|anyone know|is there any|"
    r"any .{0,12}\?", re.I)

# Clause enough to hold one statement. Thai does not space its words, so the
# split is on punctuation and line ends only.
_CLAUSE = re.compile(r"[.!?\n·•]+|(?<=[ก-๙])\s{2,}")


def offers_from_reviews(store):
    """Product keys a visitor said they bought here — {key: mentions}.

    Reads `reviewBody` and nothing else, returns keys and counts and nothing
    else. The text does not leave this function.
    """
    out = {}
    reviews = store.get("review") if isinstance(store, dict) else None
    for rv in (reviews if isinstance(reviews, list) else []):
        body = rv.get("reviewBody") if isinstance(rv, dict) else None
        if not isinstance(body, str):
            continue
        for clause in _CLAUSE.split(unescape(body)):
            if _ASKING.search(clause):
                continue
            for key, pats in OFFER_WORDS.items():
                if any(p.search(clause) for p in pats):
                    out[key] = out.get(key, 0) + 1
    return out


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


def _unescape_values(node):
    """HTML-unescape the strings INSIDE a parsed block, never the JSON text."""
    if isinstance(node, str):
        return unescape(node)
    if isinstance(node, dict):
        return {k: _unescape_values(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_unescape_values(v) for v in node]
    return node


def store_block_raw(html_text):
    """The schema.org Store block as the page wrote it, ratings and all.

    The only caller that may hold this is the one line below that strips it,
    and offers_from_reviews(), which reads review text and returns counts.

    PARSE FIRST, UNESCAPE AFTER. This used to HTML-unescape the script text
    and then parse it, which works until a reviewer types a double quote:
    weed.th writes that as &quot; inside the JSON string, unescaping turned it
    back into a bare " in the middle of a JSON string, and the whole block
    failed to parse. The shop then had no Store block and was dropped from the
    harvest entirely. Measured over the 839 cached pages on 2026-09-21: 113
    blank before, 84 after, **29 shops recovered** — The Living Room, Fat Jim,
    Chiangmai 420, and HERBAL Garden Home: Cannabis and Kratom among them. A
    page that only parses the old way is still read that way.

    The name check is the other half: some pages carry a second, nameless
    Store block, and popping the stack could reach it first and return a shop
    with no name, which the caller counts as blank just the same.
    """
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
                         html_text, re.S | re.I):
        text = m.group(1).strip()
        try:
            doc = json.loads(text)
        except Exception:
            try:
                doc = json.loads(unescape(text))
            except Exception:
                continue
        stack = [doc]
        while stack:
            cur = stack.pop()
            if isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, dict):
                if str(cur.get("@type", "")) in ("Store", "LocalBusiness") \
                        and cur.get("name"):
                    return _unescape_values(cur)
                stack.extend(v for v in cur.values() if isinstance(v, (dict, list)))
    return None


def store_block(html_text):
    """The schema.org Store block, with ratings and reviews already gone."""
    raw = store_block_raw(html_text)
    return _strip_refused(raw) if raw is not None else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--reparse", action="store_true",
                    help="re-read every cached page and rewrite the entries; "
                         "fetches nothing, so a new field mined from the "
                         "cache costs their server nothing")
    args = ap.parse_args()

    os.makedirs(CACHE, exist_ok=True)
    doc = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    shops = shop_urls()
    todo = [s for s in shops
            if args.refetch or args.reparse
            or not os.path.exists(os.path.join(CACHE, s[0] + ".html"))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"🐜 weed.th: {len(shops)} shops in the sitemap "
          f"(cm {sum(1 for s in shops if s[1]=='cm')}, "
          f"cr {sum(1 for s in shops if s[1]=='cr')}); "
          f"{len(todo)} to fetch at {DELAY:g}s apart")
    if todo and not allowed(todo[0][3]):
        print("   robots.txt says no — stopping."), exit(1)

    today, got, blank, broke, offered = date.today().isoformat(), 0, 0, 0, 0
    for i, (uuid, prov, slug, url) in enumerate(todo, 1):
        path = os.path.join(CACHE, uuid + ".html")
        if os.path.exists(path) and not args.refetch:
            # --reparse never reaches get(); a cached page is the whole input.
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
        raw = store_block_raw(page)
        st = _strip_refused(raw) if raw is not None else None
        if not st or not st.get("name"):
            blank += 1
            continue
        entry = {
            "name": st["name"].strip(),
            "province": prov,
            "src": url,
            "fetched": today,
        }
        # Keys and counts. The reviews themselves stay in `raw`, which goes
        # out of scope on the next turn of this loop.
        seen_offers = offers_from_reviews(raw)
        if seen_offers:
            entry["offers"] = seen_offers
            offered += 1
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

    doc["_note"] = ("Names and addresses, and on some entries an `offers` count "
                    "of the products a visitor said they bought — keys and "
                    "counts, never the wording. Ratings and review text are "
                    "refused at parse time — see importers/harvest_weedth.py. "
                    "Fetched one page per shop, 8s apart, robots.txt obeyed.")
    print(f"\n🐜 kept {got} · no Store block {blank} · unreachable {broke} "
          f"· a visitor named a product on {offered}")
    if args.dry_run:
        print("   --dry-run: nothing written")
        return
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"   -> {OUT}  ({sum(1 for k in doc if not k.startswith('_'))} shops)")


if __name__ == "__main__":
    main()
