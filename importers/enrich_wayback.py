#!/usr/bin/env python3
"""Recover contact facts from the archived copy of a place's dead website.

`enrich_sites.py` reads a place's own site. This reads the site a place USED to
have — the 325 links `check_links.py` found broken, 272 of which the Internet
Archive still holds a copy of. The shop is usually still there; it is the domain
that lapsed. Its old site printed a phone number, and that number is the only
first-hand contact fact left anywhere for 85 of these places.

Same practice as its sibling: first-hand only. An archived copy of the
place's OWN site is still the place's own words — nothing from a directory
site, nothing from Google or Facebook. And the same filling rule: only fields
the record is missing. This never overrules the crawl, which matters more here
than it does next door, because an archived fact can be much older than OSM's.

WHAT IS DIFFERENT, AND WHY IT NEEDS SAYING ON THE PAGE
A fact off a live site is current by construction. A fact off a 2014 snapshot
is not, and rendering the two identically would publish an eleven-year-old
phone number as though somebody had just answered it. So every field written
here carries `archivedOn` in its own provenance, the entry is licensed
`archived-official-site` rather than `official-site`, and `--max-age` refuses
snapshots past a chosen age outright. The date is the fact; the number is a
lead.

Politeness: the Internet Archive is a charity serving this for free. One
request at a time, two seconds apart, and a 429 backs off rather than retries
in a loop.

    python3 importers/enrich_wayback.py --limit 10 --dry-run   # look first
    python3 importers/enrich_wayback.py --limit 10             # then write
    python3 importers/enrich_wayback.py                        # the whole queue

Re-running is safe: a place already carrying a researched fact is skipped
unless --refresh, so an interrupted run picks up where it stopped.
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
from datetime import date
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_sites import (harvest, load_records, thai_phone,  # noqa: E402,F401
                          MAX_BYTES, mark_brand_scope)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEALTH = os.path.join(ROOT, "data", "linkhealth.json")
OUT = os.path.join(ROOT, "data", "curated", "enrich.json")
UA = ("MotDangBot/1.0 (+https://motdang.net/about.html; recovering contact facts "
      "from archived copies of dead business sites; 530kings@proton.me)")
PAUSE = 2.0
TIMEOUT = 40          # the Archive replays from cold storage; it is not quick
BROKEN = {"tls", "dns", "down", "timeout", "gone", "http-error", "server-error",
          "parked", "empty", "error"}


def raw_snapshot_url(wb_url, timestamp, original):
    """The `id_` modifier serves the archived bytes with no Archive toolbar.

    Without it the reply carries the Archive's own banner, scripts and links,
    and `harvest()` would happily read a facebook.com URL out of the toolbar
    and file it as the shop's page. Rebuilt from the timestamp rather than
    string-patched, because the stored URL shape is theirs to change.
    """
    if timestamp and original:
        return f"https://web.archive.org/web/{timestamp}id_/{original}"
    return wb_url


def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        ctype = (resp.headers.get("content-type") or "").lower()
        if "html" not in ctype and "xml" not in ctype:
            return None
        raw = resp.read(MAX_BYTES)
    for enc in ("utf-8", "cp874", "tis-620", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


# The sites in this queue are mostly hand-built and a decade old. They predate
# schema.org and tappable `tel:` links, which is all `harvest()` will take a
# number from — deliberately, because on a LIVE site a number loose in the text
# is as likely to be the web designer's as the shop's. Here that conservatism
# returns almost nothing: the Thapae Boutique House page says, in plain text,
# `Tel. +66 53 284 295` and nothing else. So this pass reads the text too, and
# earns the right to by being anchored rather than greedy.
ANCHOR = (r"(?:โทรศัพท์|โทรฯ|โทร\.?|เบอร์โทร|เบอร์|ติดต่อ|"
          r"Tel\.?|TEL\.?|Telephone|Phone|Mobile|มือถือ|Hotline|Call)")
# A credit line is where the person who built the site leaves their number.
CREDIT = re.compile(r"(?i)(web ?design|webdesign|hosting|host by|powered by|"
                    r"dedicated server|domain name|ออกแบบเว็บ|รับทำเว็บ|จัดทำโดย)")


def page_text(html):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", unescape(t))


def registrable(url):
    host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def harvest_text(html, site_url):
    """Phones and an email from the page's words, anchored to a contact label.

    Three guards, because this is the loose end of an otherwise strict system:
    the number must sit within 40 characters after a contact label; a candidate
    whose neighbourhood reads like a web-designer credit is dropped; and the
    first anchored number wins, since credits live at the foot of the page.
    """
    found, how = {}, {}
    text = page_text(html)

    for m in re.finditer(ANCHOR + r"[\s:]*([+\d][\d\s\-().]{6,20})", text):
        window = text[max(0, m.start() - 90):m.end() + 40]
        if CREDIT.search(window):
            continue
        p = thai_phone(m.group(1))
        if p:
            found["phone"] = p
            how["phone"] = "text after “%s”" % m.group(0).split()[0].strip(":. ")
            break

    # An address at the site's own domain is the business's own mailbox; the
    # designer's is at the designer's domain. That one test does the filtering
    # a keyword list would do badly.
    dom = registrable(site_url)
    for m in re.finditer(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)", text):
        if dom and (m.group(1).lower() == dom or dom.endswith(m.group(1).lower())):
            found.setdefault("attrs", {})["email"] = m.group(0)
            how["attrs"] = "email at the site's own domain"
            break
    return found, how


def merge_harvests(primary, primary_how, extra, extra_how):
    """Structured wins; text fills what it left empty."""
    out, how = dict(primary), dict(primary_how)
    for k, v in extra.items():
        if k == "attrs":
            a = dict(out.get("attrs") or {})
            for ak, av in v.items():
                a.setdefault(ak, av)
            out["attrs"] = a
            how.setdefault("attrs", extra_how.get("attrs", ""))
        elif k not in out:
            out[k] = v
            how[k] = extra_how.get(k, "")
    return out, how


def snapshot_age_years(timestamp):
    if not timestamp or len(timestamp) < 4:
        return 99.0
    y, m = int(timestamp[:4]), int(timestamp[4:6] or 1)
    today = date.today()
    return (today.year - y) + (today.month - m) / 12.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="stop after N places")
    ap.add_argument("--dry-run", action="store_true", help="print, write nothing")
    ap.add_argument("--refresh", action="store_true", help="revisit places already enriched")
    ap.add_argument("--only", help="one place id, for testing")
    ap.add_argument("--max-age", type=float, default=8.0,
                    help="refuse snapshots older than this many years (default 8; "
                         "0 means no limit). A phone number is a perishable fact.")
    args = ap.parse_args()

    health = json.load(open(HEALTH, encoding="utf-8"))
    links = health["links"]
    doc = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    recs = load_records()

    queue, too_old, no_copy = [], 0, 0
    for r in recs:
        site = (r.get("website") or "").strip()
        v = links.get(site)
        if not v or v.get("status") not in BROKEN:
            continue
        wb = v.get("wayback") or {}
        if not wb.get("url"):
            no_copy += 1
            continue
        a = r.get("attrs") or {}
        if r.get("phone") and r.get("hours") and (a.get("lineUrl") or a.get("facebook")):
            continue                      # nothing left to want
        if args.max_age and snapshot_age_years(wb.get("timestamp")) > args.max_age:
            too_old += 1
            continue
        queue.append((r, site, wb))

    if args.only:
        queue = [q for q in queue if q[0]["id"] == args.only]
    elif not args.refresh:
        queue = [q for q in queue if q[0]["id"] not in doc]
    if args.limit:
        queue = queue[:args.limit]

    print(f"🐜 {len(queue)} place(s) whose own site is dead but archived")
    if too_old:
        print(f"   {too_old} skipped: the only snapshot is older than "
              f"{args.max_age:g} years")
    if no_copy:
        print(f"   {no_copy} have no archived copy at all — nothing to read")

    today = date.today().isoformat()
    filled = blank = broke = 0
    for i, (r, site, wb) in enumerate(queue, 1):
        name = r.get("nameEn") or r.get("name") or r["id"]
        stamp = wb.get("timestamp") or ""
        shot = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}" if len(stamp) >= 8 else stamp
        url = raw_snapshot_url(wb["url"], stamp, site)
        try:
            html = get(url)
            time.sleep(PAUSE)
            if not html:
                broke += 1
                continue
            got, how = harvest(html, site)
            got, how = merge_harvests(got, how, *harvest_text(html, site))
        except urllib.error.HTTPError as e:
            broke += 1
            if e.code == 429:
                print(f"  {i:4}/{len(queue)} rate limited — resting 60s")
                time.sleep(60)
            else:
                print(f"  {i:4}/{len(queue)} http {e.code:<8} {name[:36]:36} {shot}")
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            broke += 1
            print(f"  {i:4}/{len(queue)} unreachable   {name[:36]:36} {str(e)[:32]}")
            continue
        except Exception as e:
            broke += 1
            print(f"  {i:4}/{len(queue)} unreadable    {name[:36]:36} {type(e).__name__}")
            continue

        # Holes only. An archived fact must never displace a crawled one: OSM's
        # copy may be years newer than the snapshot this came off.
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
            print(f"  {i:4}/{len(queue)} nothing to take {name[:34]:34} {shot}")
            continue

        # Per-field provenance carrying the snapshot date, so a page can say
        # "their old site, as it stood in 2021" instead of implying today.
        prov = {}
        for k in fields:
            if k == "attrs":
                for ak in fields["attrs"]:
                    prov[f"attrs.{ak}"] = {"src": url, "license": "archived-official-site",
                                           "fetched": today, "archivedOn": shot}
            else:
                prov[k] = {"src": url, "license": "archived-official-site",
                           "fetched": today, "archivedOn": shot}

        filled += 1
        keys = ", ".join(f"{k}={v}" if k != "attrs" else f"attrs[{'/'.join(v)}]"
                         for k, v in fields.items())
        print(f"  {i:4}/{len(queue)} ✔ {shot}  {name[:32]:32} {keys[:52]}")
        doc[r["id"]] = {"fields": fields, "src": url,
                        "license": "archived-official-site", "fetched": today,
                        "archivedOn": shot, "how": how, "prov": prov}
        # Written after every find, not once at the end. import_photos_commons
        # learned this the hard way: a single end-of-run write met a killed
        # process and 87 recovered facts went back in the bin. A pass this slow
        # WILL be interrupted sooner or later.
        if not args.dry_run:
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)

    brand = mark_brand_scope(doc)
    print(f"\n🐜 filled {filled} · nothing to take {blank} · unreadable {broke}")
    if brand:
        print(f"   {brand} share a site with another place and were marked brand-scope")
    if args.dry_run:
        print("   --dry-run: nothing written")
        return 0
    if filled:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"   -> {OUT}  ({len([k for k in doc if not k.startswith('_')])} enriched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
