#!/usr/bin/env python3
"""Nightly Save Page Now for the doodles worth keeping (Nan 2026-10-13, C150 (b): "only good doodles").

Sends to the Internet Archive's Wayback Machine (Save Page Now):
  - https://motdang.net/doodles/ , every night;
  - each doodle in data/doodles/keep.json (the kept set, about 200 of 80,505: the in-use ones
    and the most ornate portraits, ranked by tools/doodle_keep.py and tools/doodle_truth.py),
    at https://motdang.net/doodles/d/?id=<id> -- one save each, then again when keep.json
    adds one. The other 80,000 are not sent.

    python3 tools/doodle_wayback.py                 up to 40 pages tonight
    python3 tools/doodle_wayback.py --max 5 --dry-run

Runs on motdang-server from cron (nan's crontab: 02:40 Bangkok, 19:40 UTC), copy at /srv/wayback/,
DOODLE_KEEP=/srv/mot-dang/data/doodles/keep.json. The ledger is
/srv/state/doodle-wayback.tsv there (date, url, result, snapshot). A 429 or 5xx ends the night;
the next night carries on from the ledger. Pace: one save every 15 seconds.
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEEP = Path(os.environ.get("DOODLE_KEEP") or ROOT / "data" / "doodles" / "keep.json")
LEDGER = Path(os.environ.get("DOODLE_WAYBACK_LEDGER") or "/srv/state/doodle-wayback.tsv")
if not LEDGER.parent.exists():
    LEDGER = Path.home() / ".claude" / "state" / "doodle-wayback.tsv"
BASE = "https://motdang.net/doodles/"
UA = "motdang-doodle-archive/1.0 (+https://motdang.net/doodles/)"
PACE = 15


def targets():
    ids = json.loads(KEEP.read_text(encoding="utf-8"))["ids"]
    return [BASE + "d/?id=" + urllib.parse.quote(i, safe="") for i in ids]


def saved():
    done = {}
    if LEDGER.exists():
        for ln in LEDGER.read_text(encoding="utf-8").splitlines():
            p = ln.split("\t")
            if len(p) >= 3 and p[2] == "ok":
                done[p[1]] = p[0]
    return done


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def save(url):
    """(result, snapshot url): ok | live-missing | throttled | fail:<why>."""
    try:
        live = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        urllib.request.urlopen(live, timeout=30).close()
    except urllib.error.HTTPError as e:
        return f"live-missing:{e.code}", ""
    except Exception as e:  # noqa: BLE001
        return f"fail:live {type(e).__name__}", ""
    op = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request("https://web.archive.org/save/" + url, headers={"User-Agent": UA})
    try:
        r = op.open(req, timeout=150)
        return "ok", r.headers.get("Content-Location", "") or r.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303):
            return "ok", e.headers.get("Location", "")
        if e.code in (429, 502, 503, 504):
            return "throttled", str(e.code)
        return f"fail:{e.code}", ""
    except Exception as e:  # noqa: BLE001
        return f"fail:{type(e).__name__}", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    today = datetime.date.today().isoformat()
    done = saved()
    todo = [BASE] + [u for u in targets() if u not in done]
    if BASE in done and done[BASE] == today:
        todo.remove(BASE)
    todo = todo[:a.max]
    print(f"{len(done)} saved before; tonight {len(todo)}")
    if a.dry_run:
        for u in todo[:8]:
            print("  ", u)
        return
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    new = not LEDGER.exists()
    with open(LEDGER, "a", encoding="utf-8") as f:
        if new:
            f.write("date\turl\tresult\tsnapshot\n")
        for i, u in enumerate(todo):
            res, snap = save(u)
            f.write(f"{today}\t{u}\t{res}\t{snap}\n")
            f.flush()
            print(f"  {res}  {u}")
            if res == "throttled":
                print("the Archive asked for a pause; the rest wait for tomorrow")
                break
            if i < len(todo) - 1:
                time.sleep(PACE)


if __name__ == "__main__":
    main()
