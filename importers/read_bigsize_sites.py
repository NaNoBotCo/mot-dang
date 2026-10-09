#!/usr/bin/env python3
"""WO-50 — read the clothing and shoe trade off CMHY.city, in Thai.

THE CATEGORY DOES NOT EXIST, WHICH IS THE FINDING. CMHY.city keeps six
apparel categories — เสื้อผ้าสตรี (102), เครื่องแต่งกาย (154), มือสอง (123),
รองเท้า (228), ห้องเสื้อ-ตัดชุด (153, taken by WO-49) and ร้านซ่อมผ้า (265,
same) — and NOT ONE of them is a big-size category. Neither is there one on
any Thai directory we have looked at. A shop that carries a 3XL or a 47 is not
a kind of shop here; it is an ordinary shop that happens to hold the size, and
the only place that fact is ever written down is the shop's own name, its own
tags, or its own description.

So this reader does not filter a category. It reads all four apparel
categories whole and then SCORES every record for the words the trade uses on
itself — ไซส์ใหญ่, บิ๊กไซส์, คนอ้วน, สาวอวบ, ตัวใหญ่, ไซส์พิเศษ, 2XL–10XL,
เบอร์ใหญ่, and the inch ranges (อก 40-60 นิ้ว). Everything is kept, scored or
not: the register needs the denominator as much as the hits, because "eleven
of two hundred and forty" is a fact about the city and "eleven" on its own is
a list.

Manners, same as every other reader here: snapshot-first into cache/bigsize/,
one page at a time, a pause between fetches, an identified User-Agent, stdlib
only. Delete a cached file to refetch it.

  python3 importers/read_bigsize_sites.py            # fetch what is missing
  python3 importers/read_bigsize_sites.py --report   # parse the cache, print the tally
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "bigsize"
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle one-off harvest)"
PAUSE = 3.0
BASE = "https://www.cmhy.city"

# The four apparel categories, in the directory's own numbering. 153 and 265
# are deliberately absent: WO-49 read both the day before and they are the
# tailoring register's, not this one's. A shop read twice into two registers
# is a duplicate wearing two hats.
CATEGORIES = {
    "102": ("33-Personal/102-Women-Clothing-Store", "เสื้อผ้าสตรี", "women's clothing"),
    "154": ("33-Personal/154-Clothing-Store", "เครื่องแต่งกาย", "clothing and apparel"),
    "123": ("33-Personal/123-Used-Clothing-Store", "เสื้อผ้า-เครื่องแต่งกาย(มือสอง)", "used clothing"),
    "228": ("33-Personal/228-Shoes-Store", "รองเท้า", "shoes"),
}

# The words the trade writes on itself. Thai retail is plain about this in a
# way English retail is not: คนอ้วน is an ordinary shop-sign word, not an
# insult, and a shop that carries the size says so in its own name because
# that is the only way a customer can tell from the street.
#
# อวบ is scored LOWER than the rest on purpose and never alone: it is a common
# word (ร้านอวบมือถือ is a phone shop in Chiang Rai, อวบอิ่ม is a restaurant in
# Chiang Mai), and both of those are already in this directory. It counts when
# it sits beside a clothing word.
BIG_WORDS = [
    ("ไซส์ใหญ่", 3), ("ไซซ์ใหญ่", 3), ("ไซส์ใหญ", 3), ("บิ๊กไซส์", 3), ("บิ๊กไซซ์", 3),
    ("big size", 3), ("bigsize", 3), ("plus size", 3), ("plussize", 3),
    ("คนอ้วน", 3), ("ตัวใหญ่", 2), ("ไซส์พิเศษ", 3), ("ไซซ์พิเศษ", 3),
    ("เบอร์ใหญ่", 3), ("ไซส์เท้าใหญ่", 3), ("สาวอวบ", 3), ("สาวไซส์", 2),
    ("2xl", 1), ("3xl", 2), ("4xl", 2), ("5xl", 2), ("6xl", 2),
    ("7xl", 2), ("8xl", 2), ("9xl", 2), ("10xl", 2), ("xxxl", 2),
    ("อวบ", 1),
]
# Shoe sizes a Thai shelf normally stops short of. 44 is the usual ceiling in
# a Thai shop; anything at or past 45 printed on a shop's own page is the shop
# telling you it holds what the street does not.
BIG_SHOE = re.compile(r"(?:เบอร์|ไซส์|ไซซ์|size)\s*(4[4-9]|5[0-2])\b", re.I)
# อก / เอว in inches — how the big-size trade actually states its range.
INCHES = re.compile(r"(?:อก|เอว|รอบอก|รอบเอว)\s*\d{2}\s*[-–]\s*(\d{2})")


def safe_url(url):
    """Percent-encode anything past ASCII, leaving an already-encoded URL alone."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((
        parts.scheme, parts.netloc,
        urllib.parse.quote(parts.path, safe="/%"),
        urllib.parse.quote(parts.query, safe="=&%"), parts.fragment))


def get(url, name):
    """Snapshot-first. Returns the HTML, or None if the fetch failed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if path.exists():
        return path.read_text()
    try:
        # PERCENT-ENCODE THE PATH. CMHY builds a place slug out of the shop's
        # own name, so a shop with a French or a Thai character in its name
        # gives a URL that urllib refuses outright — it encodes the request
        # line as ASCII and raises. One shop called Amitié stopped a 583-page
        # read dead at 220 with a UnicodeEncodeError, which is a crash, not a
        # source that would not answer, and it must not look like one.
        html = None
        with urllib.request.urlopen(
                urllib.request.Request(safe_url(url), headers={"User-Agent": UA}),
                timeout=45) as r:
            html = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            UnicodeError, ValueError) as e:
        # PRINTED, NOT SWALLOWED. A page that would not answer is a fact about
        # the source and belongs in the note, not in a silent gap in the count.
        print(f"  !! {url} — {e}", flush=True)
        return None
    path.write_text(html)
    time.sleep(PAUSE)
    return html


def listing_places(html):
    """Every /place/ URL on a category page, in page order, deduped."""
    seen, out = set(), []
    for href in re.findall(r'href="(https://www\.cmhy\.city/place/\d+[^"]*)"', html):
        if href not in seen:
            seen.add(href)
            out.append(href)
    return out


def listing_cards(html):
    """name + tag badges per card — the tags are where the trade names itself."""
    cards = {}
    for block in html.split("<!--BEGIN ITEM LIST-->")[1:]:
        m = re.search(r'href="(https://www\.cmhy\.city/place/\d+[^"]*)"[^>]*>([^<]+)<', block)
        if not m:
            continue
        tags = re.findall(r'badge[^>]*>#([^<]+)<', block)
        cards[m.group(1)] = {"name": m.group(2).strip(),
                             "tags": [t.strip() for t in tags]}
    return cards


def local_business(html):
    """The JSON-LD LocalBusiness block. CMHY publishes geo, phone and dates."""
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                         html, re.S):
        raw = m.group(1).strip()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "LocalBusiness":
            return obj
    return None


def description(html):
    """The shop's own paragraph, if it wrote one."""
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return (m.group(1).strip() if m else "")


def score(text):
    """How loudly does this record say it carries the size? Words + numbers."""
    low = text.lower()
    hits, points = [], 0
    for word, w in BIG_WORDS:
        if word in low:
            hits.append(word)
            points += w
    shoe = BIG_SHOE.findall(text)
    if shoe:
        hits += [f"เบอร์{s}" for s in shoe]
        points += 3
    inch = INCHES.findall(text)
    for top in inch:
        if int(top) >= 44:
            hits.append(f"อก/เอว ถึง {top} นิ้ว")
            points += 3
    # อวบ alone is a name, not a size. It counts only in company.
    if hits == ["อวบ"]:
        return 0, []
    return points, hits


def harvest():
    index = {}
    for cid, (slug, th, en) in CATEGORIES.items():
        page, urls = 1, []
        while True:
            q = "" if page == 1 else f"?page={page}"
            html = get(f"{BASE}/category/{slug}/{q}", f"cat-{cid}-p{page}.html")
            if html is None:
                break
            found = listing_places(html)
            cards = listing_cards(html)
            new = [u for u in found if u not in index]
            for u in found:
                index.setdefault(u, {"cats": [], **cards.get(u, {"name": "", "tags": []})})
                if cid not in index[u]["cats"]:
                    index[u]["cats"].append(cid)
                if not index[u].get("tags") and u in cards:
                    index[u]["tags"] = cards[u]["tags"]
            print(f"  {th} ({cid}) page {page}: {len(found)} places, {len(new)} new")
            if not found or page > 12:
                break
            page += 1
        del urls
    print(f"index: {len(index)} distinct places across {len(CATEGORIES)} categories")
    (CACHE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
    return index


def read_places(index):
    out = []
    for i, (url, meta) in enumerate(sorted(index.items()), 1):
        pid = re.search(r"/place/(\d+)", url).group(1)
        html = get(url, f"place-{pid}.html")
        if html is None:
            continue
        lb = local_business(html) or {}
        desc = description(html)
        blob = " ".join([meta.get("name", ""), " ".join(meta.get("tags", [])),
                         lb.get("name", ""), desc])
        pts, hits = score(blob)
        geo = lb.get("geo") or {}
        addr = lb.get("address") or {}
        out.append({
            "id": pid, "url": url,
            "name": lb.get("name") or meta.get("name", ""),
            "tags": meta.get("tags", []), "cats": meta.get("cats", []),
            "phone": lb.get("telephone", ""), "site": lb.get("url", ""),
            "lat": geo.get("latitude", ""), "lng": geo.get("longitude", ""),
            "street": addr.get("streetAddress", ""),
            "amphoe": addr.get("addressLocality", ""),
            "postcode": addr.get("postalCode", ""),
            "modified": lb.get("dateModified", ""),
            "desc": desc, "points": pts, "hits": hits,
        })
        if i % 25 == 0:
            print(f"  read {i}/{len(index)}", flush=True)
    (CACHE / "places.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def report(rows):
    n = len(rows)
    hit = [r for r in rows if r["points"] > 0]
    gps = [r for r in rows if r["lat"]]
    tel = [r for r in rows if r["phone"]]
    fresh = [r for r in rows if r["modified"][:4] in ("2025", "2026")]
    print(f"\n{n} apparel places read from CMHY.city")
    print(f"  {len(gps)} with their own published GPS")
    print(f"  {len(tel)} with a phone")
    print(f"  {len(fresh)} updated in 2025 or 2026")
    print(f"  {len(hit)} say a big-size word on their own page\n")
    for r in sorted(hit, key=lambda r: -r["points"]):
        print(f"  [{r['points']}] {r['name']}")
        print(f"       {' · '.join(r['hits'])}")
        print(f"       {r['url']}")


def main():
    if "--report" in sys.argv and (CACHE / "places.json").exists():
        report(json.loads((CACHE / "places.json").read_text()))
        return
    index = harvest()
    rows = read_places(index)
    report(rows)


if __name__ == "__main__":
    main()
