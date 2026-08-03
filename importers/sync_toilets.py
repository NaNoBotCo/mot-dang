#!/usr/bin/env python3
"""Pull passer-by toilet reports from the Cloudflare Worker into
data/toilet_reports.json.

Sibling of sync_claims.py and the same two-step shape: the worker publishes a
report the moment somebody sends it, and it reaches the built site on the next
`python3 build.py`. The build itself never calls the network.

A report is not a claim and does not live with them. An owner claim locks a
record; a report is one closed-vocabulary word about one place from whoever
walked past, and worker.js keeps it in its own `toilet:` keyspace with no
capability token for exactly that reason. See putToiletReport there.

A missing worker or an empty answer leaves the existing file alone rather than
writing an empty one over real reports — this runs before every build, and a
network blip must not quietly erase what people sent.

    python3 importers/sync_toilets.py
"""
import json
import os
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_URL = "https://mot-dang-claims.nanobotco.workers.dev"
OUT = os.path.join(ROOT, "data", "toilet_reports.json")
UA = "MotDangToiletSync/1.0 (+https://motdang.net/toilets.html)"


def main():
    req = urllib.request.Request(WORKER_URL + "/toilets", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        have = os.path.exists(OUT)
        print(f"🐜 worker unreachable ({err}) — "
              + ("keeping the reports already on disk" if have
                 else "no reports file yet, nothing written"))
        return 0

    reports = payload.get("reports", {})
    if not reports and os.path.exists(OUT):
        existing = json.load(open(OUT)).get("reports", {})
        if existing:
            print(f"🐜 worker returned 0 reports but {len(existing)} are on disk — "
                  "keeping them; run with an empty data/toilet_reports.json to reset")
            return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"generated": payload.get("generated", ""), "reports": reports}, fh,
                  ensure_ascii=False, indent=1, sort_keys=True)
    print(f"🐜 {len(reports)} toilet report(s) -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
