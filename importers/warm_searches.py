#!/usr/bin/env python3
"""เตรียมไว้ให้ — what readers have asked, answered before the next one asks.

Nan, 2026-09-18: "if there's been a search for something on motdang.net,
motdang should learn from it and prepare for a similar search in the future."

THE OTHER HALF OF THE MISS LOOP. box_misses.py (WO-84) reads the same table for
what the box could NOT answer, and hands it to a person as vocabulary to write.
This reads it for what the box CAN answer and hands it to the machine: every
question that has been asked is asked again, here, so the answer is already
sitting in the colo when the next reader types it.

WHY THIS WORKS AT ALL, and it is worth writing down because the number is
large. /api/v1/search is answered by a Worker that has to parse a 69 MB index
it cannot keep (228 MB of heap against a 128 MB isolate), and then fetch a
posting list per word from R2. Measured from Chiang Mai 2026-09-18:

    a question nobody has asked      1.7 s (filters) · 4-6 s (words)
    the same question asked again    70-120 ms

The whole difference is worker.js's colo cache. A cache only helps the second
asker — so this makes the site itself the first asker, for every question a
real reader has already typed.

WHAT IT IS NOT. It does not teach the engine anything: a word the index cannot
read is still a word it cannot read, and that is box_misses.py's list and a
person's job. This only moves the cost of a known question off the reader.

COLO-LOCAL, AND SAY SO. Cloudflare's cache is per colo. Run from Chiang Mai
this warms the colo Chiang Mai readers land on, which is the one that matters;
run from elsewhere it warms elsewhere. The report prints the cf-ray colo so the
log says which city was made ready.

    python3 importers/warm_searches.py               # last 14 days, top 120
    python3 importers/warm_searches.py --days 30 --top 300
    python3 importers/warm_searches.py --dry         # list them, ask nothing
"""
import collections
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
WLA = ROOT.parent / "white-label-ai"
OUT = ROOT / "_incoming"
SITE = "https://motdang.net"
TODAY = datetime.date.today().isoformat()
# THE KEY IS THE WHOLE URL, CHARACTER FOR CHARACTER. worker.js keys the colo
# cache on `new Request(url.href)`, so a warm run that differs from the page by
# one byte warms a question nobody will ask. Two ways that happened while this
# was being written, both silent:
#
#   the ORDER of the parameters — the page builds `limit` first and then `q`
#     (build.py's first-paint block), so `?q=…&limit=40` is a different key
#     from the `?limit=40&q=…` a reader actually sends;
#   the ENCODING of a space — URLSearchParams writes `+`, and a warm run that
#     writes `%20` warms nothing.
#
# So the URL is assembled the way the page assembles it, in that order, with
# quote_via=quote_plus, and page_url() below is the only place it is built.
PAGE_LIMIT = "40"
UA = "MotDangWarm/1.0 (+https://motdang.net/api/; warming our own answers)"
PAUSE = 0.15


def query(sql):
    """One SQL statement against the remote D1, through wrangler — the same
    handshake box_misses.py uses, and the same token file."""
    env = dict(os.environ)
    keys = pathlib.Path.home() / ".config/nanobotco/keys.json"
    if keys.exists():
        try:
            env["CLOUDFLARE_API_TOKEN"] = json.load(open(keys))["cloudflare"]["api_token"]
        except Exception:
            pass
    out = subprocess.run(["npx", "wrangler", "d1", "execute", "white-label-ai", "--remote",
                          "--json", "--command", sql],
                         cwd=WLA, env=env, capture_output=True, text=True, timeout=180)
    if out.returncode:
        sys.exit("wrangler d1 failed:\n" + (out.stderr or out.stdout)[-800:])
    txt = out.stdout[out.stdout.index("["):] if "[" in out.stdout else "[]"
    doc = json.loads(txt)
    return (doc[0] or {}).get("results", []) if doc else []


def page_url(q):
    """The URL the results page itself would send for this question — the same
    parameters, in the same order, encoded the same way."""
    parts = [("limit", PAGE_LIMIT), ("q", q)]
    return SITE + "/api/v1/search?" + urllib.parse.urlencode(
        parts, quote_via=urllib.parse.quote_plus)


def ask(url):
    """GET it, and report what the edge said. Never raises: a question that
    cannot be warmed is a line in the report, not a stopped run."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            return {"ms": round((time.time() - t0) * 1000),
                    "code": r.status,
                    "edge": r.headers.get("x-md-edge") or r.headers.get("cf-cache-status") or "-",
                    "colo": (r.headers.get("cf-ray") or "-").split("-")[-1],
                    "bytes": len(body)}
    except Exception as e:
        return {"ms": round((time.time() - t0) * 1000), "code": 0,
                "edge": "fail", "colo": "-", "bytes": 0, "err": str(e)[:120]}


def main():
    days, top, dry = 14, 120, "--dry" in sys.argv
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])

    rows = query(f"SELECT q, n FROM box_log WHERE site = 'motdang' "
                 f"AND ts >= datetime('now', '-{days} days') ORDER BY ts DESC LIMIT 5000")
    # RANKED BY REPEATS, because the point is the NEXT reader: a question two
    # hundred people have asked is two hundred readers who will not wait, and
    # one somebody typed once is one. A question that found nothing is skipped
    # — warming an empty answer spends a request to make "no" arrive faster,
    # and box_misses.py is already carrying that list somewhere it can be
    # answered properly.
    asked = collections.Counter()
    for r in rows:
        q = (r.get("q") or "").strip()
        if not q or int(r.get("n") or 0) == 0:
            continue
        asked[q] += 1
    picks = asked.most_common(top)
    if not picks:
        print(f"nothing to warm — no answered searches in the last {days} days")
        return 0

    print(f"🐜 {len(rows):,} searches logged · {len(asked):,} distinct answered · "
          f"warming the top {len(picks)}")
    if dry:
        for q, c in picks:
            print(f"  {c:4}  {q}")
        return 0

    OUT.mkdir(exist_ok=True)
    log, slow, warmed, colos = [], 0, 0, collections.Counter()
    for q, c in picks:
        url = page_url(q)
        got = ask(url)
        colos[got["colo"]] += 1
        if got["code"] == 200:
            warmed += 1
            if got["ms"] > 1000:
                slow += 1
        log.append({"q": q, "asked": c, **got})
        print(f"  {got['ms']:6} ms  {got['edge']:5}  {c:4}x  {q[:54]}")
        time.sleep(PAUSE)

    med = sorted(x["ms"] for x in log)[len(log) // 2] if log else 0
    (OUT / f"warm-searches-{TODAY}.json").write_text(
        json.dumps({"pulled": TODAY, "days": days, "asked": len(asked),
                    "warmed": warmed, "median_ms": med, "runs": log},
                   ensure_ascii=False, indent=1))
    print(f"\n{warmed}/{len(picks)} warmed · median {med} ms · {slow} took over a second "
          f"· colo {', '.join(k for k, _ in colos.most_common(3))}")
    print(f"_incoming/warm-searches-{TODAY}.json")
    print("Run it after a deploy: a content deploy changes the answers and the "
          "cached ones go stale on their own five minutes later.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
