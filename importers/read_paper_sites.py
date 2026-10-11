#!/usr/bin/env python3
"""WO-54 — read the paper trades off CMHY.city, in Thai.

Five categories in the directory's own numbering: 79 ร้านถ่ายเอกสาร (copy
centre), 80 โรงพิมพ์ (printing shop), 78 รับแปลเอกสาร (translation), 95
ร้านถ่ายรูป (photo studio — where the passport photo comes from), and 73
อุปกรณ์สำนักงาน-เครื่องเขียน (office equipment and stationery, which is the
same counter as the copy shop on most Thai high streets). Everything is
kept and SCORED for the words the trade writes on itself — ถ่ายเอกสาร,
ปริ้น, เข้าเล่ม, เคลือบ, แปล, รับรอง, วีซ่า, รูปติดบัตร — so the register
carries the denominator, not just the hits.

Manners as read_bigsize_sites.py: snapshot-first into cache/paper/, one page
at a time, a pause between fetches, an identified User-Agent, stdlib only.

  python3 importers/read_paper_sites.py            # fetch what is missing
  python3 importers/read_paper_sites.py --report   # parse the cache, print the tally
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
CACHE = ROOT / "cache" / "paper"
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle one-off harvest)"
PAUSE = 3.0
BASE = "https://www.cmhy.city"

# The four apparel categories, in the directory's own numbering. 153 and 265
# are deliberately absent: WO-49 read both the day before and they are the
# tailoring register's, not this one's. A shop read twice into two registers
# is a duplicate wearing two hats.
CATEGORIES = {
    "79": ("71-Business/79-Copy-Center", "ร้านถ่ายเอกสาร", "copy centre"),
    "80": ("71-Business/80-Printing-Shop", "โรงพิมพ์", "printing shop"),
    "78": ("71-Business/78-Translate-Service", "รับแปลเอกสาร", "translation"),
    "95": ("71-Business/95-Photo-Center", "ร้านถ่ายรูป", "photo studio"),
    "73": ("71-Business/73-Office-EquipmentStationery", "อุปกรณ์สำนักงาน-เครื่องเขียน", "office equipment and stationery"),
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
TRADE_WORDS = [
    ("ถ่ายเอกสาร", 3), ("ก๊อปปี้", 2), ("copy", 1), ("ปริ้น", 2), ("ปริ๊น", 2),
    ("print", 1), ("เข้าเล่ม", 3), ("เคลือบ", 2), ("สแกน", 2), ("แฟกซ์", 1),
    ("พิมพ์งาน", 3), ("รับพิมพ์", 2), ("ไวนิล", 2), ("นามบัตร", 2), ("สติ๊กเกอร์", 1),
    ("แปลเอกสาร", 3), ("รับแปล", 3), ("รับรองเอกสาร", 3), ("กงสุล", 3), ("โนตารี", 3),
    ("notary", 3), ("วีซ่า", 3), ("visa", 3), ("ใบขับขี่", 2),
    ("รูปติดบัตร", 3), ("รูปด่วน", 2), ("ถ่ายรูปติดบัตร", 3), ("passport", 2),
    ("ด่วน", 1), ("24 ชม", 2), ("24 ชั่วโมง", 2),
]
# Shoe sizes a Thai shelf normally stops short of. 44 is the usual ceiling in
# a Thai shop; anything at or past 45 printed on a shop's own page is the shop
# telling you it holds what the street does not.
PAPER_SIZE = re.compile(r"(?:A[0-4]|เอ[0-4])\b", re.I)
# อก / เอว in inches — how the big-size trade actually states its range.
PER_SHEET = re.compile(r"(?:แผ่นละ|หน้าละ|ใบละ)\s*(\d{1,3})")


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
    # WO-54b. 96 of 522 pages carry the same block with a JSON slip in it
    # (an unescaped quote in the shop's own name is the usual one), so
    # json.loads refuses the lot and a shop with a street, two phones and a
    # postcode read as "no address". Lenient second read: the fields we use,
    # by regex, off the raw script text.
    raw = " ".join(m.group(1) for m in re.finditer(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S))
    if '"streetAddress"' not in raw and '"telephone"' not in raw:
        return None
    def grab(key):
        m = re.search(r'"%s"\s*:\s*"([^"]*)"' % key, raw)
        return m.group(1).strip() if m else ""
    # No "name" here on purpose: the first "name" in that script is the
    # breadcrumb (ธุรกิจ), and 94 shops were named "Business" by it once.
    # The listing card's name (read_places falls back to it) is the shop's.
    out = {"telephone": grab("telephone"), "url": grab("url"),
           "dateModified": grab("dateModified"), "description": grab("description"),
           "address": {"streetAddress": grab("streetAddress"),
                       "addressLocality": grab("addressLocality"),
                       "postalCode": grab("postalCode")},
           "_lenient": True}
    lat, lng = grab("latitude"), grab("longitude")
    if lat and lng:
        out["geo"] = {"latitude": lat, "longitude": lng}
    return out


def description(html):
    """The shop's own paragraph, if it wrote one."""
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return (m.group(1).strip() if m else "")


def score(text):
    """How loudly does this record say it carries the size? Words + numbers."""
    low = text.lower()
    hits, points = [], 0
    for word, w in TRADE_WORDS:
        if word in low:
            hits.append(word)
            points += w
    sizes = PAPER_SIZE.findall(text)
    if sizes:
        hits += sorted(set(x.upper() for x in sizes))
        points += 2
    for price in PER_SHEET.findall(text):
        hits.append(f"ราคาต่อแผ่น {price}")
        points += 3
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
    print(f"\n{n} paper-trade places read from CMHY.city")
    print(f"  {len(gps)} with their own published GPS")
    print(f"  {len(tel)} with a phone")
    print(f"  {len(fresh)} updated in 2025 or 2026")
    print(f"  {len(hit)} say a trade word on their own page\n")
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
