#!/usr/bin/env python3
"""Write the monthly traffic note for motdang.net.

    python3 notes/traffic_note.py            # last 31 days, writes the note
    python3 notes/traffic_note.py 2026-09-18 # as at that date

The figure is Cloudflare Workers invocations for the mot-dang-site Worker, which
sits in front of every request the site serves. Zone analytics — page views,
unique visitors, the country and user-agent split — needs a token with
Zone > Analytics > Read, which the fleet token does not carry. Until it does,
this counts requests and says so rather than implying visitors.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

KEYS = pathlib.Path.home() / ".config" / "nanobotco" / "keys.json"
HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = "mot-dang-site"
DAYS = 31

QUERY = """query($acct:String!,$start:Time!,$end:Time!,$script:string){
 viewer{ accounts(filter:{accountTag:$acct}){
  workersInvocationsAdaptive(limit:2000,
    filter:{datetime_geq:$start, datetime_leq:$end, scriptName:$script},
    orderBy:[date_ASC]){
    sum{requests errors}
    dimensions{date status}
  }}}}""".replace("$script:string", "$script:String")


def pull(end):
    creds = json.load(open(KEYS))["cloudflare"]
    start = end - dt.timedelta(days=DAYS)
    body = json.dumps({"query": QUERY, "variables": {
        "acct": creds["account_id"],
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": SCRIPT}}).encode()
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql", data=body,
        headers={"Authorization": "Bearer " + creds["api_token"],
                 "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("errors"):
        sys.exit("Cloudflare: " + str(d["errors"])[:300])
    return d["data"]["viewer"]["accounts"][0]["workersInvocationsAdaptive"], start


def main():
    end = (dt.datetime.strptime(sys.argv[1], "%Y-%m-%d")
           if len(sys.argv) > 1 else dt.datetime.now()).replace(microsecond=0)
    rows, start = pull(end)

    byday, bystatus = {}, {}
    for r in rows:
        d, s = r["dimensions"]["date"], r["dimensions"]["status"]
        byday[d] = byday.get(d, 0) + r["sum"]["requests"]
        bystatus[s] = bystatus.get(s, 0) + r["sum"]["requests"]
    if not byday:
        sys.exit("no data in the window")
    days = sorted(byday.items())
    total = sum(byday.values())
    # The first and last day in the window are partial — the window is a
    # timestamp, not midnight — so a peak or a low read off them says nothing.
    whole = days[1:-1] if len(days) > 2 else days
    peak, quiet = max(whole, key=lambda x: x[1]), min(whole, key=lambda x: x[1])

    out = [
        "MOTDANG.NET — TRAFFIC, MEASURED",
        f"{start:%Y-%m-%d} to {end:%Y-%m-%d} ({len(days)} days with data)",
        f"Source: Cloudflare Workers analytics, workersInvocationsAdaptive, script {SCRIPT}.",
        f"Pulled {end:%Y-%m-%d %H:%M}. Nothing here is estimated.",
        "",
        f"  {total:>12,}  requests",
        f"  {total // len(days):>12,}  a day on average",
        f"  {peak[1]:>12,}  the peak day, {peak[0]}",
        f"  {quiet[1]:>12,}  the quietest, {quiet[0]}",
        "",
        "  Peak and low exclude the first and last day, which are partial.",
        "",
        "  by outcome",
    ]
    for s, n in sorted(bystatus.items(), key=lambda x: -x[1]):
        out.append(f"  {n:>12,}  {s}")
    out += [
        "",
        "WHAT THIS NUMBER IS NOT",
        "  Edge requests, not people. A page fetches several API files, so one",
        "  reader makes several requests.",
        "  The split between crawlers, AI readers and people is not instrumented",
        "  on this zone. traffic-eye answers that question and is not attached;",
        "  the route is written and commented out in",
        "  traffic-eye/wrangler.collector.toml.",
        "",
        "DAILY",
    ]
    for d, n in days:
        out.append(f"  {d}  {n:>9,}")

    path = HERE / f"traffic-{end:%Y-%m}.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{total:,} requests over {len(days)} days -> {path}")


if __name__ == "__main__":
    main()
