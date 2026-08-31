#!/usr/bin/env python3
"""Bake cinema showtimes for Chiang Mai and Chiang Rai into data/showtimes.json.

The chain's own site is the source. It is read politely, once per cinema-day,
cached to disk — stdlib only, no headless browser, same snapshot-first shape as
check_links.py.

    python3 importers/make_showtimes.py            # fetch what is stale
    python3 importers/make_showtimes.py --days 5   # look further ahead
    python3 importers/make_showtimes.py --refetch  # ignore the cache

HOW IT REACHES THE SITE IS NOT IN THIS REPO. The request recipe — the address,
the form it takes, and the screen ids — lives in a config file outside the tree
at ~/.mot-dang-showtimes.json, the same arrangement as the LINE channel token,
and for the same reason: it is ours to use, not ours to publish. Without that
file this importer explains itself and exits, and everything else still builds.

The file looks like this, and `python3 importers/make_showtimes.py --template`
will print it:

    {
      "endpoint": "https://…",
      "referer":  "https://…{cinema}…",
      "form":     {"<field>": "{cinema}", "<field>": "{day}", "<field>": "fixed"},
      "cinemas":  [{"id": "…", "province": "cm", "th": "…", "en": "…"}]
    }

SF Cinema is not here: it answers automated requests with 403 and no
equivalent route was found. Its screens still appear in the catalogue, just
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

import ingest      # shared write discipline (WO-41 Phase 2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "showtimes")
OUT = os.path.join(ROOT, "data", "showtimes.json")
CONF_FILE = os.path.expanduser("~/.mot-dang-showtimes.json")
PAUSE = 3.0
STALE_HOURS = 12

TEMPLATE = {
    "endpoint": "https://example/the/post/target/",
    "referer": "https://example/per-cinema/page/{cinema}/",
    # Real field names go here. {cinema} and {day} are substituted per request;
    # anything else is sent as written.
    "form": {"field-that-takes-the-cinema": "{cinema}",
             "field-that-takes-the-date": "{day}",
             "any-other-field": "its fixed value"},
    "cinemas": [{"id": "0", "province": "cm", "th": "ชื่อโรง", "en": "Screen name"}],
}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept-Language": "th,en;q=0.9",
}


def conf():
    """The request recipe, or a clear explanation of what is missing."""
    if not os.path.exists(CONF_FILE):
        sys.exit(
            f"No showtime config at {CONF_FILE}.\n\n"
            "The address this importer posts to, the form it sends, and the\n"
            "screen ids are deliberately kept out of the repository. Put them\n"
            "in that file (chmod 600) to run this importer.\n\n"
            "    python3 importers/make_showtimes.py --template\n\n"
            "prints the shape it expects. Every other importer works without it.")
    with open(CONF_FILE) as fh:
        c = json.load(fh)
    missing = [k for k in ("endpoint", "form", "cinemas") if not c.get(k)]
    if missing:
        sys.exit(f"{CONF_FILE} is missing: {', '.join(missing)}")
    return c

MOVIE_RE = re.compile(r'bscbbm-cover-title">\s*(.+?)\s*</div>', re.S)
TIME_RE = re.compile(r'data-showtime="(\d+)"[^>]*>\s*((?:[01]?\d|2[0-3]):[0-5]\d)\s*<')
BLOCK_RE = re.compile(r'bscbbm-cover-title">')
DUR_RE = re.compile(r'bscbbm-cover-time">.*?([\d]{2,3})\s*นาที', re.S)
CATE_RE = re.compile(r'bscbbm-cover-cate">.*?</img>?\s*([^<]{2,80})', re.S)


def fetch(c, cinema_id, day):
    """Post the configured form. {cinema} and {day} are the only placeholders."""
    form = {k: v.format(cinema=cinema_id, day=day) for k, v in c["form"].items()}
    hdrs = dict(HEADERS)
    if c.get("referer"):
        hdrs["Referer"] = c["referer"].format(cinema=cinema_id)
    req = urllib.request.Request(c["endpoint"], data=urllib.parse.urlencode(form).encode(),
                                 headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def cached(c, cinema_id, day, refetch):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"major-{cinema_id}-{day}.json")
    if not refetch and os.path.exists(path):
        age = (time.time() - os.path.getmtime(path)) / 3600.0
        if age < STALE_HOURS:
            with open(path) as fh:
                return json.load(fh)["body"], True
    body = fetch(c, cinema_id, day)
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
    if "--template" in sys.argv:
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2))
        print(f"\nSave as {CONF_FILE} (chmod 600).")
        return
    conf_ = conf()
    refetch = "--refetch" in sys.argv
    days = 3
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    today = date.today()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(days)]

    cinemas, failures = [], []
    for c in conf_["cinemas"]:
        by_day = {}
        for day in dates:
            try:
                markup, was_cached = cached(conf_, c["id"], day, refetch)
                films = parse(markup)
                if films:
                    by_day[day] = films
                print(f"   {'cache' if was_cached else 'fetch'}  {c['en'][:34]:<36} "
                      f"{day}: {len(films)} film(s)")
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as ex:
                failures.append((c["id"], day, str(ex)))
                print(f"   FAIL   {c['en'][:34]:<36} {day}: {ex}")
        if by_day:
            # The public booking page for that screen — what a reader clicks.
            # Derived from the configured per-cinema page rather than spelled
            # out here, so this file names no address at all.
            cinemas.append({**c, "days": by_day,
                            "url": conf_["referer"].format(cinema=c["id"]).rstrip("/")})

    total = sum(len(f["times"]) for c in cinemas for d in c["days"].values() for f in d)
    # WO-41 Phase 2. This file published 0 cinemas for weeks in August, dated
    # today every morning. A cinema list with nothing in it is never a fact
    # about the town.
    ingest.write(OUT, {"generated": date.today().isoformat(),
                       "source": "Major Cineplex (majorcineplex.com)",
                       "dates": dates, "cinemas": cinemas},
                 count=len(cinemas), min_rows=1,
                 sources_failed=[str(f) for f in failures],
                 label="showtimes.json")
    print(f"   {total} screening(s)")
    if failures:
        print(f"⚠  {len(failures)} fetch(es) failed")


if __name__ == "__main__":
    main()
