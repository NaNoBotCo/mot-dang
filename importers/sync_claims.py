#!/usr/bin/env python3
"""Pull live owner claims from the Cloudflare Worker into data/claims.json.

Claims are self-reported contact facts an owner enters at /claim.html — they
publish instantly on the worker (see worker/worker.js) but only reach the
built site on the next `python3 build.py`, same two-step shape as
check_links.py writing data/linkhealth.json. Static site, no live calls on
page load: this script is the one place that talks to the worker.

    python3 importers/sync_claims.py
"""
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_URL = "https://mot-dang-claims.nanobotco.workers.dev"
OUT = os.path.join(ROOT, "data", "claims.json")
UA = "MotDangClaimSync/1.0 (+https://motdang.net/claim.html)"


def main():
    req = urllib.request.Request(WORKER_URL + "/claims", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read())
    claims = {c["placeId"]: c for c in payload.get("claims", [])}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"generated": payload.get("generated", ""), "claims": claims}, fh,
                   ensure_ascii=False, indent=1, sort_keys=True)
    print(f"🐜 {len(claims)} live claim(s) -> {OUT}")


if __name__ == "__main__":
    main()
