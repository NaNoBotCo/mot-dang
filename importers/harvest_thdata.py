#!/usr/bin/env python3
"""Read thdata.co, in Thai, for either province — the hours source Chiang Rai never had.

WHY THIS EXISTS
Counted 2026-09-18: Chiang Mai carries opening hours on 4,007 records, Chiang
Rai on 400. Tracing the receipts, 1,808 of Chiang Mai's came from cmhy.city —
a Chiang Mai directory, harvested 2026-09-04, which has no Chiang Rai edition.
Overture publishes no hours column at all (its places schema was read at source
the same day: id, categories, confidence, websites, emails, socials, phones,
brand, addresses, names, sources, operating_status, taxonomy, bbox — no hours).
So Chiang Rai's gap is not a thinner province. It is one harvest that was only
ever run on one city.

thdata.co publishes both. Sampled 25 Chiang Rai place pages on 2026-09-18:
hours stated on 20, phone on 19. Every page carries a JSON-LD block with the
Thai name, a street address down to ตำบล/อำเภอ, and exact coordinates.

MANNERS — the same as read_paper_sites.py and cmhy.py
Snapshot-first into cache/thdata/, one page at a time, a pause between fetches,
an identified User-Agent, stdlib only. A page already in the cache is never
fetched twice.

    python3 importers/harvest_thdata.py cr massage-spa barber   # fetch + parse
    python3 importers/harvest_thdata.py cr --all                # every category below
    python3 importers/harvest_thdata.py cr --report             # parse the cache only

Writes _incoming/thdata-<prov>.json. It does NOT touch data/canonical — the
match-and-fill against the catalogue is the next step and belongs behind the
build lock.
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "thdata"
OUT = ROOT / "_incoming"
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle harvest, snapshot-first)"
PAUSE = 2.5
BASE = "https://thdata.co"

PROVINCES = {"cr": "chiang-rai", "cm": "chiang-mai"}

# The directory's own category slugs. Thai name as the site prints it, so a
# note can say what was read in the directory's words.
CATEGORIES = {
    "massage-spa":    "นวดและสปา",
    "barber":         "ร้านตัดผมชาย",
    "beauty-salon":   "ร้านเสริมสวย",
    "bar-nightlife":  "บาร์ / สถานที่กลางคืน",
    "cafe":           "ร้านกาแฟ",
    "laundry":        "ร้านซักรีด",
    "car-repair":     "อู่ซ่อมรถ",
    "motorcycle-repair": "ร้านซ่อมมอเตอร์ไซค์",
    "hardware":       "ร้านฮาร์ดแวร์",
    "veterinary":     "สัตวแพทย์",
}

MAX_PAGES = 40          # a category that never runs out is a bug, not a jackpot


def fetch(url, name):
    """Cached GET. Returns the text, or None if the site said no."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / name
    if f.exists():
        return f.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        t = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        print(f"    {e.code} {url}")
        return None
    except Exception as e:
        print(f"    {type(e).__name__} {url}")
        return None
    f.write_text(t, encoding="utf-8")
    time.sleep(PAUSE)
    return t


def ld_blocks(page):
    out = []
    for b in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        try:
            d = json.loads(b)
        except Exception:
            continue
        out += d if isinstance(d, list) else [d]
    return out


def business(blocks):
    """The LocalBusiness block, whatever subtype the site chose to call it."""
    skip = {"Organization", "WebPage", "BreadcrumbList", "FAQPage", "WebSite", "ImageObject"}
    for d in blocks:
        t = d.get("@type")
        t = t[0] if isinstance(t, list) and t else t
        if isinstance(t, str) and t not in skip and d.get("name"):
            return d
    return None


def faq_facts(blocks):
    """thdata puts hours and phone in its FAQ block, and says plainly when it
    has neither. 'ยังไม่มีข้อมูล…' is a stated absence, not a value."""
    out = {}
    for d in blocks:
        if d.get("@type") != "FAQPage":
            continue
        for q in d.get("mainEntity", []) or []:
            name = q.get("name", "")
            ans = (q.get("acceptedAnswer") or {}).get("text", "")
            ans = html.unescape(re.sub(r"<[^>]+>", " ", ans))
            ans = re.sub(r"\s+", " ", ans).strip()
            if not ans or "ยังไม่มี" in ans:
                continue
            if "เปิดกี่โมง" in name:
                out["hours"] = ans
            elif "เบอร์โทร" in name:
                out["phone"] = ans
            elif "อยู่ที่ไหน" in name:
                out["address"] = ans
    return out


def read_place(path):
    page = fetch(BASE + path, "p-" + re.sub(r"[^a-zA-Z0-9]", "", path)[-60:] + ".html")
    if not page:
        return None
    blocks = ld_blocks(page)
    b = business(blocks) or {}
    geo = b.get("geo") or {}
    addr = b.get("address") or {}
    facts = faq_facts(blocks)
    rec = {
        "url": BASE + path,
        "name": b.get("name"),
        "type": b.get("@type"),
        "lat": geo.get("latitude"), "lng": geo.get("longitude"),
        "address": addr.get("streetAddress") or facts.get("address"),
        "locality": addr.get("addressLocality"),
        "postcode": addr.get("postalCode"),
        "phone": b.get("telephone") or facts.get("phone"),
        "hours": b.get("openingHours") or facts.get("hours"),
        "sourceUpdated": (b.get("dateModified") or "")[:10],
    }
    return rec if rec["name"] else None


def read_category(prov_slug, cat):
    seen, places = set(), []
    for page_no in range(1, MAX_PAGES + 1):
        url = f"{BASE}/th/{cat}/{prov_slug}/" + (f"?page={page_no}" if page_no > 1 else "")
        page = fetch(url, f"cat-{cat}-{prov_slug}-{page_no}.html")
        if not page:
            break
        links = [l for l in dict.fromkeys(re.findall(r'href="(/th/p/[^"#?]+)"', page))]
        fresh = [l for l in links if l not in seen]
        if not fresh:
            break
        seen.update(fresh)
        for l in fresh:
            r = read_place(l)
            if r:
                r["cat"] = cat
                places.append(r)
        print(f"    page {page_no}: {len(fresh)} places (running {len(places)})", flush=True)
    return places


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0] not in PROVINCES:
        sys.exit("usage: harvest_thdata.py {cr|cm} [category …|--all] [--report]")
    prov = args.pop(0)
    prov_slug = PROVINCES[prov]
    report_only = "--report" in args
    cats = list(CATEGORIES) if ("--all" in args or report_only) else [a for a in args if a in CATEGORIES]
    if not cats:
        sys.exit("name a category, or --all. Known: " + ", ".join(CATEGORIES))

    all_places = []
    for c in cats:
        print(f"  {c} — {CATEGORIES[c]}", flush=True)
        all_places += read_category(prov_slug, c)

    OUT.mkdir(exist_ok=True)
    out = OUT / f"thdata-{prov}.json"
    out.write_text(json.dumps({
        "source": "thdata.co", "province": prov, "read": time.strftime("%Y-%m-%d"),
        "categories": {c: CATEGORIES[c] for c in cats},
        "places": all_places,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    n = len(all_places)
    with_h = sum(1 for p in all_places if p.get("hours"))
    with_p = sum(1 for p in all_places if p.get("phone"))
    with_g = sum(1 for p in all_places if p.get("lat"))
    print(f"\n{n} places -> {out}")
    if n:
        print(f"  hours {with_h} ({with_h/n:.0%}) · phone {with_p} ({with_p/n:.0%}) · exact pin {with_g} ({with_g/n:.0%})")


if __name__ == "__main__":
    main()
