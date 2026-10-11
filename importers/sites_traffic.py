#!/usr/bin/env python3
"""People visits per site in the register, last 30 days → data/sites_traffic.json.

The browser beacon (Cloudflare's account-level rumPageloadEventsAdaptiveGroups) is the
people count: crawlers do not run the script it rides on. A visit counts toward the
card whose href is the longest prefix of the page's path, so /sites/many-hands/th/
counts for Many Hands. sites_layer.best() reads the file for "most read"; when the
fetch fails the old file stays, and a missing file only leaves that lane empty.

Needs ~/.config/nanobotco/keys.json → cloudflare.api_token, account_id.
"""
import datetime
import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sites_layer  # noqa: E402

OUT = ROOT / "data" / "sites_traffic.json"
DAYS = 30
Q = """query($a:String!,$f:AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject!){viewer{
accounts(filter:{accountTag:$a}){rumPageloadEventsAdaptiveGroups(limit:10000,filter:$f){
sum{visits} dimensions{requestPath}}}}}"""


def fetch():
    k = json.load(open(os.path.expanduser("~/.config/nanobotco/keys.json")))["cloudflare"]
    today = datetime.date.today()
    f = {"requestHost": "motdang.net",
         "date_geq": str(today - datetime.timedelta(days=DAYS - 1)), "date_leq": str(today)}
    body = json.dumps({"query": Q, "variables": {"a": k["account_id"], "f": f}}).encode()
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=body,
                                 headers={"Authorization": "Bearer " + k["api_token"],
                                          "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=90))
    if d.get("errors"):
        raise RuntimeError(str(d["errors"])[:300])
    return d["data"]["viewer"]["accounts"][0]["rumPageloadEventsAdaptiveGroups"]


def main():
    try:
        rows = fetch()
    except Exception as e:  # network, token, schema — keep what is on disk
        print("sites_traffic: kept the last file (%s)" % e)
        return 0
    hrefs = sorted((c["href"] for c in sites_layer.cards() if not c["href"].startswith("http")),
                   key=len, reverse=True)
    visits = {}
    for r in rows:
        path = r["dimensions"]["requestPath"].lstrip("/")
        for h in hrefs:
            if path == h.rstrip("/") or path.startswith(h):
                visits[h] = visits.get(h, 0) + r["sum"]["visits"]
                break
    OUT.write_text(json.dumps({"generated": datetime.date.today().isoformat(), "days": DAYS,
                               "source": "Cloudflare browser beacon, motdang.net",
                               "visits": dict(sorted(visits.items(), key=lambda kv: -kv[1]))},
                              ensure_ascii=False, indent=1) + "\n")
    print("sites_traffic: %d sites with visits → %s" % (len(visits), OUT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
