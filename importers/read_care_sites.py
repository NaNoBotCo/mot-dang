#!/usr/bin/env python3
"""Read each care anchor's OWN site for what it states. WO-25, door 1.

Same manners and the same first-hand rule as enrich_sites.py, which this
imports rather than reimplements: robots.txt asked once per host and obeyed,
an identified User-Agent, a pause between every request, nothing retried in a
loop. Hospitals run bigger servers than one-chair barbershops, but the manners
do not change with the size of the building.

VERIFY BEFORE BELIEVING. Most care anchors carry no website in the crawl, so
data/curated/care_targets.json lists CANDIDATE urls — stored ones first,
guesses after. A candidate counts as the hospital's own site only when the
fetched page carries one of the target's `expect` tokens (its own Thai name,
or its English name); a target with `expect_also` must ALSO match one of
those (Rajavej without เชียงใหม่ could be a namesake hospital in another
province). A guess that fails is recorded in the manifest as what it was —
a wrong turn — and never read as the hospital.

WHAT THIS WRITES. Snapshots only: cache/care/<key>/*.html (+ at most two
keyword-matched PDFs per site, package price lists mostly travel as PDF), and
cache/care/manifest.json saying what was fetched, what verified, and why.
It deliberately does NOT write data/curated/care.json — the register is
curated by hand from the snapshots, every claim carrying the exact src url
and fetched date, the same discipline as the hot-springs register. A page
that does not mention a service is silence, never a "no".

    python3 importers/read_care_sites.py --dry-run     # look first
    python3 importers/read_care_sites.py               # fetch what is stale
    python3 importers/read_care_sites.py --only rajavej
    python3 importers/read_care_sites.py --refresh     # ignore snapshot age

Snapshot-first: a page fetched within STALE_DAYS is not asked for again
unless --refresh. Re-running is safe and cheap.
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import enrich_sites as es  # noqa: E402  (robots, get, PAUSE, UA, strip_tags)

TARGETS = ROOT / "data" / "curated" / "care_targets.json"
CACHE = ROOT / "cache" / "care"
MANIFEST = CACHE / "manifest.json"
STALE_DAYS = 7
MAX_SUBPAGES = 6
MAX_PDFS = 2
PDF_CAP = 3_000_000

# The rooms this order cares about, as they appear on hospital nav bars.
# Matched against the href AND the link text; Thai terms are compounds.
DOOR_WORDS = re.compile(
    r"คลินิก|แผนก|ศูนย์|บริการ|ตรวจสุขภาพ|แพ็คเกจ|แพ็กเกจ|แพคเกจ|โปรแกรม"
    r"|ประกัน|สิทธิ|ต่างชาติ|ต่างประเทศ|นานาชาติ|ติดต่อ|เวชระเบียน|ค่ารักษา"
    r"|clinic|center|centre|department|service|package|check\s?-?up|program"
    r"|insurance|international|contact|price|charge|visa|treatment|provider"
    r"|claim|medical\s+record", re.I)


def slug(url):
    s = re.sub(r"^https?://", "", url.strip("/"))
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s)
    return s[:120] or "page"


def fresh(path):
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < STALE_DAYS * 86400


def note(entries, **kw):
    kw.setdefault("fetched", date.today().isoformat())
    entries.append(kw)
    flag = "✓" if kw.get("ok") else "·"
    print(f"  {flag} {kw.get('key','?'):18} {kw.get('note','')}  {kw.get('url','')}")


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fetch_pdf(url):
    req = urllib.request.Request(url, headers={"User-Agent": es.UA,
                                               "Accept": "application/pdf"})
    with urllib.request.urlopen(req, timeout=es.TIMEOUT) as resp:
        if "pdf" not in resp.headers.get("Content-Type", ""):
            return None
        return resp.read(PDF_CAP)


def page_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:160] if m else ""


def verified(target, html):
    blob = html.lower()
    if not any(t.lower() in blob for t in target.get("expect", [])):
        return False
    also = target.get("expect_also")
    if also and not any(t.lower() in blob for t in also):
        return False
    return True


def door_links(html, base):
    """Same-host links whose href or text names a room this order reads."""
    out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.{0,120}?)</a>',
                         html, re.I | re.S):
        href, text = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        if href.startswith(("mailto:", "tel:", "javascript:", "line:")):
            continue
        full = urllib.parse.urljoin(base, href)
        if urllib.parse.urlparse(full).netloc != urllib.parse.urlparse(base).netloc:
            continue
        if not DOOR_WORDS.search(href) and not DOOR_WORDS.search(text):
            continue
        full = full.split("#")[0]
        if full in seen or full.rstrip("/") == base.rstrip("/"):
            continue
        seen.add(full)
        out.append(full)
    return out


def walk_target(t, entries, refresh):
    key = t["key"]
    home_html, home_url = None, None
    for cand in t.get("urls", []):
        snap = CACHE / key / (slug(cand) + ".html")
        if not refresh and fresh(snap):
            home_html, home_url = snap.read_text(encoding="utf-8"), cand
            if verified(t, home_html):
                note(entries, key=key, url=cand, ok=True, note="home (snapshot)",
                     file=str(snap.relative_to(ROOT)), title=page_title(home_html))
                break
            home_html = None
            continue
        if not es.allowed(cand):
            note(entries, key=key, url=cand, ok=False, note="robots.txt says no")
            continue
        try:
            html, final = es.get(cand)
        except Exception as e:
            note(entries, key=key, url=cand, ok=False,
                 note=f"unreachable ({e.__class__.__name__})")
            time.sleep(es.PAUSE)
            continue
        time.sleep(es.PAUSE)
        if not html:
            note(entries, key=key, url=cand, ok=False, note="not an html page")
            continue
        save(snap, html)
        if verified(t, html):
            home_html, home_url = html, final or cand
            note(entries, key=key, url=cand, ok=True, note="home VERIFIED",
                 file=str(snap.relative_to(ROOT)), title=page_title(html))
            break
        note(entries, key=key, url=cand, ok=False, title=page_title(html),
             note="fetched but NOT this hospital — candidate rejected",
             file=str(snap.relative_to(ROOT)))
    if not home_html:
        note(entries, key=key, url="", ok=False,
             note="UNRESOLVED — no candidate verified; needs a human turn")
        return

    pdfs = 0
    for link in door_links(home_html, home_url or t["urls"][0])[:MAX_SUBPAGES]:
        is_pdf = link.lower().endswith(".pdf")
        snap = CACHE / key / (slug(link) + ("" if is_pdf else ".html"))
        if not refresh and fresh(snap):
            note(entries, key=key, url=link, ok=True, note="room (snapshot)",
                 file=str(snap.relative_to(ROOT)))
            continue
        if not es.allowed(link):
            note(entries, key=key, url=link, ok=False, note="robots.txt says no")
            continue
        try:
            if is_pdf:
                if pdfs >= MAX_PDFS:
                    continue
                raw = fetch_pdf(link)
                if raw:
                    snap.parent.mkdir(parents=True, exist_ok=True)
                    snap.write_bytes(raw)
                    pdfs += 1
                    note(entries, key=key, url=link, ok=True, note="pdf saved",
                         file=str(snap.relative_to(ROOT)))
            else:
                html, _ = es.get(link)
                if html:
                    save(snap, html)
                    note(entries, key=key, url=link, ok=True, note="room read",
                         file=str(snap.relative_to(ROOT)), title=page_title(html))
                else:
                    note(entries, key=key, url=link, ok=False, note="not html")
        except Exception as e:
            note(entries, key=key, url=link, ok=False,
                 note=f"unreachable ({e.__class__.__name__})")
        time.sleep(es.PAUSE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    doc = json.loads(TARGETS.read_text(encoding="utf-8"))
    targets = [t for t in doc["targets"]
               if not args.only or t["key"] == args.only]
    if args.dry_run:
        for t in targets:
            print(f"{t['key']:20} {len(t.get('urls', []))} candidate(s)  "
                  f"{t.get('urls', [''])[0]}")
        return 0

    entries = []
    started = datetime.now().isoformat(timespec="seconds")
    for t in targets:
        print(f"— {t['key']} ({t.get('name_en', '')})")
        walk_target(t, entries, args.refresh)

    CACHE.mkdir(parents=True, exist_ok=True)
    old = []
    if MANIFEST.exists() and (args.only or not entries):
        old = json.loads(MANIFEST.read_text(encoding="utf-8")).get("entries", [])
        keep = {t["key"] for t in targets}
        old = [e for e in old if e.get("key") not in keep]
    MANIFEST.write_text(json.dumps(
        {"run": started, "entries": old + entries}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    ok = sum(1 for e in entries if e.get("ok"))
    print(f"\n{ok}/{len(entries)} fetches landed → {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
