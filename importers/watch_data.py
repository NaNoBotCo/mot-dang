#!/usr/bin/env python3
"""Check that the morning's gathering actually gathered something.

The walk has always checked exit codes, and an exit code is a poor witness. A
fetcher that loses its source, gets a 403, or parses a page whose markup moved
will often write the file it promised, stamp it with today's date, and exit 0 —
with nothing inside. On 2026-08-16 all three of these were true at once and had
been for a while:

    events.json      75 events -> 0, refetched every morning
    showtimes.json   183 screenings -> 0 cinemas
    finance.json     {"generated": today} and nothing else

The site published all three. Every page said "updated today" and meant it. The
festival harvester, meanwhile, had not run since 2026-07-29 because nothing in
the walk called it, and nothing was watching for its silence either.

So this asks two questions of every file the walk is responsible for: is the
stamp recent enough for how often that source actually changes, and is there
anything in it. A source that has gone quiet is reported by name. Exit is
non-zero if anything is stale or hollow, so the walk can say so out loud
instead of moving on.

    python3 importers/watch_data.py           # report, exit 1 if anything is wrong
    python3 importers/watch_data.py --quiet   # only complain, say nothing when well
"""
import json
import os
import sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# file, stamp key(s), how many days may pass before silence is suspicious, and
# what must not be empty. max_age follows how often the SOURCE really changes,
# not how often we would like it to: the lottery draws twice a month, link
# health is a slow sweep, and the sky is baked half a year ahead.
CHECKS = [
    ("weather.json",        ["generated"],              2,  [("cities", 1)]),
    ("air.json",            ["generated"],              2,  [("places", 1)]),
    ("finance.json",        ["generated"],              3,  [("fx.rates", 1),
                                                             ("gold", 1),
                                                             ("crypto", 1)]),
    ("events.json",         ["generated"],              3,  [("events", 1)]),
    ("showtimes.json",      ["generated"],              3,  [("cinemas", 1)]),
    ("festival_dates.json", ["generated"],             10,  [("rows", 1)]),
    ("lottery.json",        ["draw.date", "generated"], 35, [("draw", 1)]),
    ("linkhealth.json",     ["generated"],             45,  [("links", 1)]),
    ("fortune.json",        ["generated"],             60,  [("days", 1)]),
    ("sky.json",            ["generated"],             60,  [("days", 1)]),
    # A claim count of zero is a true fact about the world, not a broken
    # fetcher — only its freshness is checked.
    ("claims.json",         ["generated"],              3,  []),
]


def dig(doc, path):
    v = doc
    for part in path.split("."):
        v = v.get(part) if isinstance(v, dict) else None
    return v


def size(v):
    if v is None:
        return 0
    if isinstance(v, (list, dict, str)):
        return len(v)
    return 1


def age_days(stamp):
    if not stamp:
        return None
    s = str(stamp)[:10]
    try:
        return (date.today() - datetime.strptime(s, "%Y-%m-%d").date()).days
    except ValueError:
        return None


def main():
    quiet = "--quiet" in sys.argv
    problems, lines = [], []

    for fname, stamps, max_age, required in CHECKS:
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            problems.append(f"{fname} is missing entirely")
            continue
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            problems.append(f"{fname} will not parse ({type(e).__name__})")
            continue

        stamp = next((dig(doc, k) for k in stamps if dig(doc, k)), None)
        days = age_days(stamp)
        notes = []
        if days is None:
            problems.append(f"{fname} carries no readable date stamp")
            notes.append("no stamp")
        elif days > max_age:
            problems.append(f"{fname} has gone quiet — {days} days old, "
                            f"expected within {max_age}")
            notes.append(f"{days}d old")

        for path_key, least in required:
            n = size(dig(doc, path_key))
            if n < least:
                problems.append(f"{fname} is hollow — {path_key} holds {n}, "
                                f"expected at least {least}")
                notes.append(f"{path_key}={n}")

        mark = "✗" if notes else "✓"
        lines.append(f"  {mark} {fname:22} {str(stamp)[:10]:12} "
                     f"{'· '.join(notes)}")

    if not quiet or problems:
        print("🐜 what the walk brought home")
        print("\n".join(lines))
    if problems:
        print(f"\n🐜 {len(problems)} thing(s) need a look:")
        for p in problems:
            print(f"   - {p}")
        return 1
    if not quiet:
        print("\n🐜 every source spoke today")
    return 0


if __name__ == "__main__":
    sys.exit(main())
