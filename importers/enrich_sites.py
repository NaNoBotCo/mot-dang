#!/usr/bin/env python3
"""Read each place's own website and fill in the contact facts it publishes.

The crawl gives us what OpenStreetMap holds, and OSM holds a phone number for
14% of the catalogue. But 998 places gave OSM a website, and a business's own
site nearly always prints the number that OSM lacks. This walks those sites and
lifts the contact block off them.

First-hand only. The place's own domain, its own LINE Official Account, its own
schema.org block — nothing from a directory site's copy, nothing from Google or
Facebook listing pages. Every field lands in data/curated/enrich.json with the
URL it was read off and the date, so any line on the built site can be traced
back to the page that said it.

Politeness, because these are small businesses' servers:
  - robots.txt is fetched once per host and obeyed
  - one request at a time, one second between hosts, one page per place
  - a User-Agent that says who we are and where to complain
  - anything slow or broken is skipped, never retried in a loop

    python3 importers/enrich_sites.py --limit 20 --dry-run   # look first
    python3 importers/enrich_sites.py --limit 20             # then write
    python3 importers/enrich_sites.py                        # the whole queue

Re-running is safe: a place already carrying a researched fact is skipped unless
--refresh is passed, so an interrupted run picks up where it stopped.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date, timezone, datetime
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "data", "canonical")
OUT = os.path.join(ROOT, "data", "curated", "enrich.json")
UA = "MotDangBot/1.0 (+https://motdang.net/about.html; directory enrichment; 530kings@proton.me)"
PAUSE = 1.0          # seconds between requests
TIMEOUT = 20
MAX_BYTES = 1_500_000

# Hosts that host other people's listings rather than their own. A phone number
# found on one of these is somebody's copy of a fact, not the fact — and some of
# them we are asked to leave alone outright.
NOT_FIRST_HAND = (
    "facebook.com", "instagram.com", "google.", "goo.gl", "tripadvisor.",
    "agoda.", "booking.com", "airbnb.", "foursquare.com", "wongnai.com",
    "grab.com", "foodpanda.", "shopee.", "lazada.", "linktr.ee",
    "web-pra.com", "uamulet.com", "patreon.com",
)


# ---- fetching -------------------------------------------------------------

_robots = {}


def allowed(url):
    """Ask robots.txt once per host, and believe it. A host that will not tell
    us is treated as a yes for a single page — that is the conventional read of
    a missing robots.txt, and we only ever ask for one page."""
    p = urllib.parse.urlparse(url)
    host = f"{p.scheme}://{p.netloc}"
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(host + "/robots.txt")
        # Fetched by hand rather than rp.read(), which takes no timeout and will
        # sit on a host that accepts the connection and then never answers —
        # one such host stalls the whole queue.
        try:
            req = urllib.request.Request(host + "/robots.txt", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as resp:
                rp.parse(resp.read(200_000).decode("utf-8", "replace").splitlines())
        except Exception:
            rp = None
        _robots[host] = rp
        time.sleep(PAUSE)
    rp = _robots[host]
    if rp is None:
        return True
    try:
        return rp.can_fetch(UA, url)
    except Exception:
        return True


def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "th,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        ctype = resp.headers.get("Content-Type", "")
        if "html" not in ctype and "xml" not in ctype:
            return None, resp.geturl()
        raw = resp.read(MAX_BYTES)
    enc = "utf-8"
    m = re.search(rb'charset=["\']?([\w\-]+)', raw[:4000], re.I)
    if m:
        enc = m.group(1).decode("ascii", "ignore")
    try:
        return raw.decode(enc, "replace"), resp.geturl()
    except LookupError:
        return raw.decode("utf-8", "replace"), resp.geturl()


# ---- extraction -----------------------------------------------------------

def strip_tags(html):
    html = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html)))


def thai_phone(raw):
    """Normalise to how a Thai number is written and dialled here: 0XX-XXXXXX.

    +66 is unwound to the leading zero, because that is what is printed on the
    door and what a local phone expects. Anything that is not a plausible Thai
    landline or mobile is dropped rather than guessed at — a wrong number on a
    hospital listing is worse than a blank one.
    """
    d = re.sub(r"[^\d+]", "", raw or "")
    if d.startswith("+66"):
        d = "0" + d[3:]
    elif d.startswith("66") and len(d) >= 11:
        d = "0" + d[2:]
    d = re.sub(r"\D", "", d)
    if not d.startswith("0"):
        return None
    if len(d) == 10:                       # mobile: 08X / 09X / 06X
        return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    if len(d) == 9:
        # Bangkok alone has a two-digit area code. Everywhere else — 053 for
        # Chiang Mai, 052 for the newer Chiang Mai block — takes three, and
        # splitting those as 02-style prints a number nobody can dial.
        return f"02-{d[2:]}" if d.startswith("02") else f"{d[:3]}-{d[3:]}"
    return None


def jsonld_blocks(html):
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
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
                yield cur
                stack.extend(v for v in cur.values() if isinstance(v, (dict, list)))


def harvest(html, page_url):
    """Pull the contact block off one page. Structured data first — a schema.org
    telephone is a claim the site makes on purpose, while a number loose in the
    text may belong to the web designer in the footer."""
    found, how = {}, {}

    for node in jsonld_blocks(html):
        t = node.get("@type")
        t = " ".join(t) if isinstance(t, list) else str(t or "")
        if "Person" in t and "Organization" not in t:
            continue
        tel = node.get("telephone")
        if tel and "phone" not in found:
            p = thai_phone(tel if isinstance(tel, str) else str(tel))
            if p:
                found["phone"], how["phone"] = p, "schema.org"
        oh = node.get("openingHours") or node.get("openingHoursSpecification")
        if oh and isinstance(oh, str) and "hours" not in found:
            found["hours"], how["hours"] = oh, "schema.org"

    # tel: links are the next most deliberate signal — somebody made it tappable.
    if "phone" not in found:
        tels = re.findall(r'href=["\']tel:([^"\']+)', html, re.I)
        for t in tels:
            p = thai_phone(t)
            if p:
                found["phone"], how["phone"] = p, "tel: link"
                break

    attrs = {}
    line = re.search(r'https?://(?:page\.)?line\.me/[^\s"\'<>)]+', html, re.I)
    if line:
        u = unescape(line.group(0)).split("?")[0]
        if not u.rstrip("/").endswith("line.me"):
            attrs["lineUrl"] = u
    # The first Facebook link on a page is as often a share button, a tracking
    # pixel, or the theme author's page as it is the shop's own. The shop's own
    # is the one repeated — header, footer, contact block — so take the most
    # repeated handle rather than the first one seen.
    def social(host, pat, skip):
        hits = [h for h in re.findall(pat, html) if h.lower() not in skip]
        if not hits:
            return None
        return max(sorted(set(hits)), key=hits.count)

    fb = social("facebook", r'https?://(?:www\.|m\.|web\.)?facebook\.com/([A-Za-z0-9.\-]{3,})',
                {"tr", "sharer", "plugins", "dialog", "profile.php", "share.php",
                 "pages", "groups", "events", "photo.php", "watch", "help", "policies"})
    if fb:
        attrs["facebook"] = f"https://www.facebook.com/{fb}/"
    ig = social("instagram", r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{2,})',
                {"p", "reel", "reels", "explore", "accounts", "stories", "tv"})
    if ig:
        attrs["instagram"] = f"https://www.instagram.com/{ig}/"
    mail = re.search(r'href=["\']mailto:([^"\'?]+)', html, re.I)
    if mail and "@" in mail.group(1):
        attrs["email"] = mail.group(1).strip()
    if attrs:
        found["attrs"], how["attrs"] = attrs, "page links"
    return found, how


# ---- the pass -------------------------------------------------------------

def as_url(v):
    """OSM's `website` is free text, and 57 of the 1,003 that carry one arrive
    with no scheme — "www.stuffchiangmai.com", "facebook.com/paperplanecnx".

    urllib raises ValueError on those before a single byte is fetched. That
    landed in this importer's catch-all as "unreadable", which reads exactly
    like a malformed page, so 57 places were counted as visited-and-broken
    without ever having been asked. check_links.py already assumes http:// for
    the same values; matching it means one place's website is the same string
    in both files rather than two spellings of one address.
    """
    v = (v or "").strip()
    if v and not re.match(r"^[a-z][a-z0-9+.-]*://", v, re.I):
        return "http://" + v
    return v


def first_hand(url):
    """Is this the place's own domain, rather than somebody's listing of it?

    A URL WITH NO SCHEME HAS NO NETLOC. urlparse("m.facebook.com") puts the
    whole thing in `path` and leaves `netloc` empty, so the blocklist matched
    nothing and this returned True — a Facebook page passed as a first-hand
    source. Two records in the beauty shelf carry exactly that shape (WO-22,
    2026-08-21), and the mistake is silent in the one place this repo is least
    willing to be wrong about: where a fact came from. A missing scheme is
    assumed to be https, which is what every other reader of these fields does.
    """
    if "//" not in url:
        url = "https://" + url.lstrip("/")
    host = urllib.parse.urlparse(url).netloc.lower()
    return not any(b in host for b in NOT_FIRST_HAND)


def load_records():
    out = []
    for f in sorted(os.listdir(CANON)):
        if f.endswith(".json"):
            out += json.load(open(os.path.join(CANON, f), encoding="utf-8"))
    return out


def wants(r):
    """Worth a visit: it published a website, and we are missing something the
    site probably prints."""
    a = r.get("attrs") or {}
    return bool(r.get("website")) and not (
        r.get("phone") and r.get("hours") and (a.get("lineUrl") or a.get("facebook")))


def mark_brand_scope(doc):
    """One site serving many places gives brand facts, not branch facts.

    Sixteen Bangchak stations share bangchak.co.th; eleven university buildings
    share one faculty site; ten MK branches share one corporate page. Head
    office's switchboard is a WRONG number for the station on your soi, and its
    opening hours are not that branch's hours — so both are dropped where a
    source is shared. The brand's Facebook and email survive, because a branch
    pointing at its brand's page is honest and the site already knows how to
    label that ("เว็บของแบรนด์ · Brand site").

    Returns how many entries were re-scoped.
    """
    by_src = {}
    for pid, e in doc.items():
        if pid.startswith("_"):
            continue
        by_src.setdefault(e.get("src"), []).append(pid)

    n = 0
    for src, pids in by_src.items():
        if len(pids) < 2:
            continue
        for pid in pids:
            e = doc[pid]
            fields = e.get("fields") or {}
            dropped = [k for k in ("phone", "hours") if k in fields]
            for k in dropped:
                fields.pop(k)
            e["scope"] = "brand"
            e["shared_with"] = len(pids) - 1
            if dropped:
                e["dropped"] = dropped
            if not fields:
                e["fields"] = {}
            n += 1
    # An entry left with nothing to say is not worth publishing.
    for pid in [p for p, e in doc.items()
                if not p.startswith("_") and not (e.get("fields") or {})]:
        del doc[pid]
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="stop after N places")
    ap.add_argument("--dry-run", action="store_true", help="print, write nothing")
    ap.add_argument("--refresh", action="store_true", help="revisit places already enriched")
    ap.add_argument("--only", help="one place id, for testing")
    ap.add_argument("--cat", help="one category key, e.g. cannabis — walk that "
                                  "shelf's sites and leave the rest of the "
                                  "queue for another day")
    args = ap.parse_args()

    doc = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    recs = load_records()
    queue = [r for r in recs if wants(r) and first_hand(as_url(r["website"]))]
    if args.only:
        queue = [r for r in recs if r["id"] == args.only and r.get("website")]
    elif not args.refresh:
        queue = [r for r in queue if r["id"] not in doc]
    if args.cat:
        queue = [r for r in queue if args.cat in (r.get("cat") or [])]
    if args.limit:
        queue = queue[:args.limit]

    print(f"🐜 {len(queue)} place(s) to visit "
          f"({sum(1 for r in recs if r.get('website')):,} carry a website at all)")
    today = date.today().isoformat()
    filled, blank, refused, broke = 0, 0, 0, 0

    for i, r in enumerate(queue, 1):
        url = as_url(r["website"])
        name = r.get("nameEn") or r.get("name") or r["id"]
        try:
            if not allowed(url):
                refused += 1
                print(f"  {i:4}/{len(queue)} robots says no  {name[:38]:38} {url[:50]}")
                continue
            html, final = get(url)
            time.sleep(PAUSE)
            if not html:
                broke += 1
                continue
            got, how = harvest(html, final)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            broke += 1
            print(f"  {i:4}/{len(queue)} unreachable    {name[:38]:38} {str(e)[:40]}")
            continue
        except Exception as e:                      # a malformed page is not fatal
            broke += 1
            print(f"  {i:4}/{len(queue)} unreadable     {name[:38]:38} {type(e).__name__}")
            continue

        # Only fields the record is actually missing. The crawl's value stands
        # unless it is absent; this pass fills holes, it does not overrule OSM.
        fields = {}
        for k in ("phone", "hours"):
            if got.get(k) and not r.get(k):
                fields[k] = got[k]
        if got.get("attrs"):
            have = r.get("attrs") or {}
            new = {k: v for k, v in got["attrs"].items() if not have.get(k)}
            if new:
                fields["attrs"] = new
        if not fields:
            blank += 1
            print(f"  {i:4}/{len(queue)} nothing new    {name[:38]:38}")
            continue

        filled += 1
        keys = ", ".join(f"{k}={v}" if k != "attrs" else f"attrs[{'/'.join(v)}]"
                         for k, v in fields.items())
        print(f"  {i:4}/{len(queue)} ✔ {name[:38]:38} {keys[:70]}")
        doc[r["id"]] = {"fields": fields, "src": final, "license": "official-site",
                        "fetched": today, "how": how}

    brand = mark_brand_scope(doc)
    print(f"\n🐜 filled {filled} · nothing to take {blank} · robots refused {refused} · "
          f"unreachable {broke}")
    if brand:
        print(f"   {brand} place(s) share a site with another and were marked brand-scope "
              f"— their phone and hours were dropped as head-office facts")
    if args.dry_run:
        print("   --dry-run: nothing written")
        return
    if filled:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"   -> {OUT}  ({len([k for k in doc if not k.startswith('_')])} enriched)")
        print("   now: python3 build.py")


if __name__ == "__main__":
    sys.exit(main())
