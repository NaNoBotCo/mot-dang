#!/usr/bin/env python3
"""Bake cinema showtimes for Chiang Mai and Chiang Rai into data/showtimes.json.

How this reaches the site is deliberately not published here.

So this is the site's own AJAX call, made politely and once per cinema-day,
cached to disk. No headless browser, stdlib only, same snapshot-first shape as
check_links.py.

    python3 importers/make_showtimes.py            # fetch what is stale
    python3 importers/make_showtimes.py --days 5   # look further ahead
    python3 importers/make_showtimes.py --refetch  # ignore the cache

SF Cinema is not here: it answers automated requests with 403 and no
equivalent endpoint was found. Its screens still appear in the catalogue, just
without times, which is the correct thing to show rather than a guess.
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "showtimes")
OUT = os.path.join(ROOT, "data", "showtimes.json")
ENDPOINT = "[removed]"
PAUSE = 3.0
STALE_HOURS = 12

# Major/EGV screens in the two provinces, with the chain's own cinema ids
# (read from its /home/[removed]/all/ fragment).
CINEMAS = [
    {"id": "91", "province": "cm", "th": "เมเจอร์ เซ็นทรัลเฟสติวัล เชียงใหม่",
     "en": "Major Central Festival Chiang Mai"},
    {"id": "92", "province": "cm", "th": "ไอแมกซ์ เลเซอร์ เซ็นทรัลเฟสติวัล เชียงใหม่",
     "en": "IMAX Laser Central Festival Chiang Mai"},
    {"id": "40", "province": "cm", "th": "เมเจอร์ เชียงใหม่ แอร์พอร์ต",
     "en": "Major Chiang Mai Airport"},
    {"id": "61", "province": "cr", "th": "เมเจอร์ เซ็นทรัล เชียงราย",
     "en": "Major Central Chiang Rai"},
    {"id": "188", "province": "cr", "th": "เมเจอร์ บิ๊กซี เชียงราย",
     "en": "Major Big C Chiang Rai"},
]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept-Language": "th,en;q=0.9",
}

MOVIE_RE = re.compile(r'bscbbm-cover-title">\s*(.+?)\s*</div>', re.S)
TIME_RE = re.compile(r'data-showtime="(\d+)"[^>]*>\s*((?:[01]?\d|2[0-3]):[0-5]\d)\s*<')
BLOCK_RE = re.compile(r'bscbbm-cover-title">')
DUR_RE = re.compile(r'bscbbm-cover-time">.*?([\d]{2,3})\s*นาที', re.S)
CATE_RE = re.compile(r'bscbbm-cover-cate">.*?</img>?\s*([^<]{2,80})', re.S)


def fetch(cinema_id, day):
    body = urllib.parse.urlencode({
        "[removed]": "", "[removed]": cinema_id,
        "[removed]": "normal", "[removed]": "[removed]",
        "[removed]": day,
    }).encode()
    hdrs = dict(HEADERS)
    hdrs["Referer"] = f"https://www.majorcineplex.com/booking2/search_showtime/cinema={cinema_id}/"
    req = urllib.request.Request(ENDPOINT, data=body, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def cached(cinema_id, day, refetch):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"major-{cinema_id}-{day}.json")
    if not refetch and os.path.exists(path):
        age = (time.time() - os.path.getmtime(path)) / 3600.0
        if age < STALE_HOURS:
            with open(path) as fh:
                return json.load(fh)["body"], True
    body = fetch(cinema_id, day)
    with open(path, "w") as fh:
        json.dump({"fetched": datetime.now().isoformat(timespec="seconds"), "body": body}, fh)
    time.sleep(PAUSE)
    return body, False


def parse(markup):
    """One HTML fragment -> [{title, duration, category, times:[...]}].

    The fragment repeats a cover block per film, then that film's times, so
    splitting on the cover-title marker keeps each film's times with the film.
    """
    out = []
    parts = BLOCK_RE.split(markup)
    titles = MOVIE_RE.findall(markup)
    for title, seg in zip(titles, parts[1:]):
        times = sorted({t for _sid, t in TIME_RE.findall(seg)})
        if not times:
            continue
        dur = DUR_RE.search(seg)
        cate = CATE_RE.search(seg)
        out.append({
            "title": html.unescape(re.sub(r"<[^>]+>", "", title)).strip(),
            "minutes": int(dur.group(1)) if dur else None,
            "category": html.unescape(cate.group(1)).strip().rstrip("/ ") if cate else None,
            "times": times,
        })
    return out


def main():
    refetch = "--refetch" in sys.argv
    days = 3
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    today = date.today()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(days)]

    cinemas, failures = [], []
    for c in CINEMAS:
        by_day = {}
        for day in dates:
            try:
                markup, was_cached = cached(c["id"], day, refetch)
                films = parse(markup)
                if films:
                    by_day[day] = films
                print(f"   {'cache' if was_cached else 'fetch'}  {c['en'][:34]:<36} "
                      f"{day}: {len(films)} film(s)")
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as ex:
                failures.append((c["id"], day, str(ex)))
                print(f"   FAIL   {c['en'][:34]:<36} {day}: {ex}")
        if by_day:
            cinemas.append({**c, "days": by_day,
                            "url": f"https://www.majorcineplex.com/booking2/"
                                   f"search_showtime/cinema={c['id']}"})

    total = sum(len(f["times"]) for c in cinemas for d in c["days"].values() for f in d)
    with open(OUT, "w") as fh:
        json.dump({"generated": date.today().isoformat(),
                   "source": "Major Cineplex (majorcineplex.com)",
                   "dates": dates, "cinemas": cinemas}, fh, ensure_ascii=False, indent=1)
    print(f"🐜 {len(cinemas)} cinema(s), {total} screening(s) -> {OUT}")
    if failures:
        print(f"⚠  {len(failures)} fetch(es) failed")


if __name__ == "__main__":
    main()
