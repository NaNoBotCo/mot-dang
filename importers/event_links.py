#!/usr/bin/env python3
"""A link for every upcoming event that has one to give — data/event_links.json.

Each event goes down a ladder and stops at the first rung with a live link:

  1. event   the link its source gave (data/events.json `url`)
  2. series  the link kept for its series in data/curated/event_series.json —
             a weekly night found once is found for every week after; the key
             is the title and the venue, normalised (series_key())
  3. venue   the matched venue's own website, from the place records
             (data/canonical/<province>.json `website`)

Every link is checked with importers/check_links.check() and the verdict kept
in cache/event_links/checks.json for CHECK_DAYS, so a rerun fetches only what
is new or stale. A dead link (gone, dns, down, parked, empty, http-error) drops
the event to the next rung; a social page or a door shut to the checker
(walled) is kept, because a person can still open it. A link that failed only
by timing out or a server error keeps its last good verdict.

Series links come in through --propose: a TSV of candidates (from a research
job or a person), each fetched and accepted only when the page names the event
or its venue. What no rung answers is written to cache/event_links_todo.tsv,
one row per series, for the next research job.

    python3 importers/event_links.py                 # resolve, check, write
    python3 importers/event_links.py --propose f.tsv # title<TAB>venue<TAB>url<TAB>note<TAB>event|host
    python3 importers/event_links.py --report        # counts by rung, the todo list

Build reads data/event_links.json and makes no network call.
"""
import csv
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "importers"))
import check_links  # noqa: E402

EVENTS = os.path.join(ROOT, "data", "events.json")
EXTRAS = os.path.join(ROOT, "data", "curated", "event_extras.json")
SERIES = os.path.join(ROOT, "data", "curated", "event_series.json")
OUT = os.path.join(ROOT, "data", "event_links.json")
CACHE = os.path.join(ROOT, "cache", "event_links")
CHECKS = os.path.join(CACHE, "checks.json")
TODO = os.path.join(ROOT, "cache", "event_links_todo.tsv")
HORIZON = 56
CHECK_DAYS = 7
SHOWN = {"ok", "social", "walled", "redirect-offsite", "moved-social"}
TRANSIENT = {"timeout", "server-error", "error", "tls"}


def _j(p, default=None):
    try:
        with open(p) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _dump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def _n(s):
    return re.sub(r"[^0-9a-z฀-๿]+", "", (s or "").lower())


def series_key(title, venue):
    """A weekly night's name and place, without the date words a source adds."""
    t = re.sub(r"\((?:every|weekly|ทุก)[^)]*\)|\b(?:every|weekly)\s+\w+day\b", "", (title or "").lower())
    return _n(t) + "@" + _n(venue)


def upcoming():
    ev = (_j(EVENTS, {}) or {}).get("events", [])
    ex = _j(EXTRAS, {}) or {}
    seen = {e["uid"] for e in ev}
    rows = ev + [r for r in ex.get("add", []) if isinstance(r, dict) and r.get("uid") not in seen]
    over = ex.get("events", {})
    today, horizon = date.today().isoformat(), (date.today() + timedelta(days=HORIZON)).isoformat()
    out = []
    for e in rows:
        e = dict(e, **{k: v for k, v in over.get(e["uid"], {}).items() if v})
        s = e.get("start") or ""
        if s and s[:10] <= horizon and (e.get("end") or s)[:10] >= today:
            out.append(e)
    return out


def venue_sites(rows):
    """uid → the matched venue's website, by the build's own matcher."""
    import front_layer
    places, web = [], {}
    for prov in ("cm", "cr"):
        for r in _j(os.path.join(ROOT, "data", "canonical", prov + ".json"), []) or []:
            if r.get("lat") is None:
                continue
            places.append({"id": r["id"], "name": r.get("name"), "nameEn": r.get("nameEn"), "lat": r["lat"], "lng": r["lng"],
                           "province": r.get("province") or prov, "geoPrecision": r.get("geoPrecision"), "slug": r.get("id")})
            if r.get("website"):
                web[r["id"]] = r["website"]
    find = front_layer.venue_finder(places)
    out = {}
    for e in rows:
        v = find(e.get("venue_name"), e.get("city") or "")
        if v and v["id"] in web:
            out[e["uid"]] = web[v["id"]]
    return out


def checker():
    book = _j(CHECKS, {}) or {}
    cut = (date.today() - timedelta(days=CHECK_DAYS)).isoformat()

    def fresh(url):
        old = book.get(url)
        return bool(old and old.get("checkedAt", "") >= cut)

    def run(urls):
        """The stale ones checked, eight at a time (check_links.check never raises)."""
        todo = sorted({u for u in urls if u and not fresh(u)})
        with ThreadPoolExecutor(max_workers=8) as pool:
            for u, v in zip(todo, pool.map(check_links.check, todo)):
                old = book.get(u)
                if v.get("status") in TRANSIENT and old and old.get("status") in SHOWN:
                    v = dict(old, recheck=v.get("status"))
                book[u] = v
        return book
    return run, lambda: _dump(book, CHECKS)


def resolve():
    rows = upcoming()
    series = (_j(SERIES, {}) or {}).get("series", {})
    sites = venue_sites(rows)
    run, save = checker()
    links, todo, tally = {}, {}, {"event": 0, "series": 0, "venue": 0, "none": 0}
    ladders = {}
    for e in rows:
        key = series_key(e.get("title"), e.get("venue_name"))
        ladders[e["uid"]] = (key, [("event", e.get("url")),
                                   ("series:" + (series.get(key) or {}).get("kind", "event"), (series.get(key) or {}).get("url")),
                                   ("venue", sites.get(e["uid"]))])
    for i in range(3):                       # a rung at a time: a lower rung is checked only where the upper failed
        book = run(lad[i][1] for uid, (k, lad) in ladders.items() if uid not in links)
        for uid, (k, lad) in ladders.items():
            rung, url = lad[i]
            if uid in links or not url:
                continue
            v = book.get(url) or {}
            if v.get("status") in SHOWN:
                r, _, kind = rung.partition(":")
                # host: a page of whoever runs or hosts it (the venue's site, a studio's Facebook), not of this event
                links[uid] = {"url": url, "rung": r, "kind": kind or ("host" if r == "venue" else "event"),
                              "status": v["status"], "checked": v.get("checkedAt")}
    for e in rows:
        key, got = ladders[e["uid"]][0], links.get(e["uid"])
        tally[got["rung"] if got else "none"] += 1
        if not got or got["kind"] == "host":
            t = todo.setdefault(key, {"title": e.get("title", ""), "venue": e.get("venue_name") or "",
                                      "city": e.get("city") or "cm", "dates": [], "has": got["kind"] if got else ""})
            t["dates"].append((e.get("start") or "")[:10])
    save()
    _dump({"generated": date.today().isoformat(), "tally": tally, "links": links,
           "judged": sorted(e["uid"] for e in rows)}, OUT)
    os.makedirs(os.path.dirname(TODO), exist_ok=True)
    with open(TODO, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["title", "venue", "city", "dates", "has", "key"])
        for k, t in sorted(todo.items(), key=lambda kv: -len(kv[1]["dates"])):
            w.writerow([t["title"], t["venue"], t["city"], " ".join(sorted(set(t["dates"]))), t["has"], k])
    return tally, len(todo)


def page_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": check_links.UA, "Accept": "text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=check_links.TIMEOUT) as r:
        raw = r.read(400_000).decode("utf-8", "ignore")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).lower()


def names_it(text, title, venue):
    """The page names the event (most of its long words) or its venue."""
    words = [w for w in re.findall(r"[a-z฀-๿]{4,}", (title or "").lower()) if w not in {"with", "from", "night", "every"}]
    hit = sum(1 for w in words if w in text)
    if words and hit >= max(1, (len(words) * 2 + 2) // 3):
        return "names the event (%d of %d words)" % (hit, len(words))
    v = _n(venue)
    if len(v) >= 6 and v in _n(text):
        return "names the venue"
    return ""


def propose(path):
    """title<TAB>venue<TAB>url<TAB>note<TAB>kind — each checked, each kept only if its page names it.
    kind: event (a page for this event; the default) or host (the page of whoever runs or hosts it)."""
    doc = _j(SERIES, None) or {"_note": "", "series": {}}
    kept, refused = 0, []
    with open(path, newline="") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) < 3 or row[0] == "title" or not row[2].startswith("http"):
                continue
            title, venue, url, note = row[0], row[1], row[2].strip(), (row[3] if len(row) > 3 else "")
            kind = "host" if len(row) > 4 and row[4].strip() == "host" else "event"
            v = check_links.check(url)
            if v.get("status") not in SHOWN:
                refused.append((title, url, v.get("status")))
                continue
            why = "a social page; a person checks it" if v["status"] in ("social", "moved-social") else ""
            if not why:
                try:
                    why = names_it(page_text(url), title, venue)
                except Exception as e:  # noqa: BLE001
                    why = "walled to the checker (%s)" % type(e).__name__ if v["status"] == "walled" else ""
            if not why:
                refused.append((title, url, "the page names neither the event nor its venue"))
                continue
            doc["series"][series_key(title, venue)] = {"title": title, "venue": venue, "url": url,
                                                       "found": date.today().isoformat(), "by": note or "proposed",
                                                       "evidence": why, "kind": kind}
            kept += 1
    _dump(doc, SERIES)
    print("kept %d" % kept)
    for t, u, why in refused:
        print("  refused  %s  %s  (%s)" % (t[:50], u, why))


def main():
    if "--propose" in sys.argv:
        propose(sys.argv[sys.argv.index("--propose") + 1])
    if "--report" in sys.argv and os.path.exists(OUT):
        d = _j(OUT, {})
        print("links", d.get("tally"))
        with open(TODO) as fh:
            print(fh.read())
        return 0
    tally, n = resolve()
    print("event links: %(event)d from the source, %(series)d from the series list, %(venue)d the venue's site, %(none)d none" % tally)
    d = _j(OUT, {})
    print("  of those, the host's page rather than the event's: %d" % sum(1 for x in d.get("links", {}).values() if x.get("kind") == "host"))
    print("%d series still without an event link: %s" % (n, os.path.relpath(TODO, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
