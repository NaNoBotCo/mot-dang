#!/usr/bin/env python3
"""Who asked for the pages — read the edge count.

    python3 traffic.py            # last 7 days
    python3 traffic.py 30         # last 30 days
    python3 traffic.py 1 cr       # last day, chiangrai.motdang.net if it exists

WHERE THE NUMBERS COME FROM
The site Worker writes one row per request into Cloudflare Analytics Engine
(publish/worker.js, foot of the file). This reads them back over the SQL API
with the fleet token in ~/.config/nanobotco/keys.json, which already carries
Account Analytics Read — no new token, nothing to paste.

WHAT THE NUMBERS ARE, AND ARE NOT
Categories come from the User-Agent, which is self-declared. Anything can call
itself Googlebot, so every line here is a claim the caller made about itself,
not a proof. Read "human" as "asked for the page with a browser's User-Agent
and no bot marker" — that is the honest ceiling of what a first-party count can
know without a cookie, and there is no cookie.

Retention is 90 days at the edge; asking for more than that returns what exists.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

KEYS_PATH = Path.home() / ".config" / "nanobotco" / "keys.json"
DATASET = "traffic_eye"
DEFAULT_HOST = "motdang.net"


def sql(query: str) -> list[dict]:
    """One query against the Analytics Engine SQL API."""
    keys = json.loads(KEYS_PATH.read_text())
    cf = keys.get("cloudflare") or {}
    token, account = cf.get("api_token"), cf.get("account_id")
    if not token or not account:
        sys.exit(f"no cloudflare api_token/account_id in {KEYS_PATH}")
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/analytics_engine/sql",
        data=query.encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("data", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        if e.code in (401, 403):
            sys.exit("the token was refused. It needs Account · Account Analytics · Read.\n" + body)
        sys.exit(f"HTTP {e.code}: {body}")


def q(select: str, where: str, days: int, host: str, group: str, limit: int = 20) -> list[dict]:
    """SUM(_sample_interval * double1) everywhere: Analytics Engine samples
    under load, and a bare COUNT(*) would silently under-report when it does."""
    return sql(
        f"SELECT {select}, SUM(_sample_interval * double1) AS n FROM {DATASET} "
        f"WHERE blob1 = '{host}' AND timestamp > NOW() - INTERVAL '{days}' DAY {where} "
        f"GROUP BY {group} ORDER BY n DESC LIMIT {limit}"
    )


def bar(n: float, top: float, width: int = 34) -> str:
    return "#" * max(1, round(width * n / top)) if top and n else ""


def table(title: str, rows: list[dict], label: str, note: str = "") -> None:
    print(f"\n{title}")
    if note:
        print(f"  {note}")
    if not rows:
        print("  (nothing recorded)")
        return
    top = max(float(r["n"]) for r in rows)
    for r in rows:
        n = float(r["n"])
        name = str(r[label])[:52] or "(blank)"
        print(f"  {name:<52} {int(n):>8}  {bar(n, top)}")


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    host = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_HOST

    total = q("blob1 AS site", "", days, host, "site", 1)
    if not total:
        print(f"No rows for {host} in the last {days} days.")
        print("Either the Worker carrying the count is not deployed yet, or")
        print("nothing has asked for a page since it was. `npx wrangler tail")
        print("mot-dang-site` shows requests arriving in real time.")
        return

    n_total = int(float(total[0]["n"]))
    print(f"\n{host} — last {days} day{'s' if days != 1 else ''} — {n_total:,} requests")
    print("=" * 68)

    cats = q("blob2 AS category", "", days, host, "category", 12)
    human = sum(float(r["n"]) for r in cats if r["category"] == "human")
    table("WHO ASKED", cats, "category",
          f"people {human/n_total*100:.1f}% · machines {(1-human/n_total)*100:.1f}%")

    table("BY NAME", q("blob3 AS agent", "", days, host, "agent", 20), "agent",
          "self-declared — a scraper can call itself anything")

    table("PEOPLE, BY DAY",
          q("toDate(timestamp) AS day", "AND blob2 = 'human'", days, host, "day", 60),
          "day")
    table("MACHINES, BY DAY",
          q("toDate(timestamp) AS day", "AND blob2 != 'human'", days, host, "day", 60),
          "day")

    table("WHERE PEOPLE CAME FROM",
          q("blob7 AS ref", "AND blob2 = 'human' AND blob7 NOT IN ('', '(same site)')",
            days, host, "ref", 20),
          "ref", "referrer host only; a direct visit records nothing and is not here")

    table("WHAT PEOPLE LANDED ON",
          q("blob4 AS path", "AND blob2 = 'human' AND blob7 != '(same site)'",
            days, host, "path", 20),
          "path", "first page of a visit, not every page of it")

    table("WHAT THE AI CRAWLERS READ",
          q("blob4 AS path", "AND blob2 = 'ai'", days, host, "path", 15), "path")

    table("COUNTRIES, PEOPLE ONLY",
          q("blob5 AS country", "AND blob2 = 'human'", days, host, "country", 15), "country")

    table("MISSES — a link somebody followed that is not there",
          q("blob4 AS path", "AND blob6 = '404'", days, host, "path", 20), "path")

    print()


if __name__ == "__main__":
    main()
