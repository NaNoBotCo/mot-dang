#!/usr/bin/env python3
"""Census: what does OSM hold in our provinces that no crawl selector asks for?

The catalog grows one errand at a time when it grows by accident — the food
category asked only for cafes for weeks, coworking selectors missed StarWork
(tagged office=company), shop=bed went unrequested until a mattress errand.
This script asks the question systematically: for each key (shop, amenity,
leisure, office, craft, tourism, healthcare), fetch a CSV of that key's VALUES
across TH-50 and TH-57 (area-clipped, same manners as crawl_overpass.py: one
selector per query, 12 s pauses, mirror rotation), tally them, and diff the
tally against every key=value selector in crawl_overpass.py GROUPS.

Output: a ranked table of unrequested values with counts — each row is a shelf
the city already stocks that the directory has never asked about. Snapshot-first
into cache/census/; delete a file to refetch it.

Reading the report: a big count is not automatically a shelf. amenity=bench is
not a listing. The report is a menu for a person, not a work order for a bot.
"""
import csv
import io
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "census"
MIRRORS = ["https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]
PAUSE = 12
KEYS = ["shop", "amenity", "leisure", "office", "craft", "tourism", "healthcare"]
PROVINCES = {"cm": "TH-50", "cr": "TH-57"}
UA = "motdang-census/1.0 (contact: 530kings@proton.me; one selector per query, 12s pauses)"


def fetch(key, prov, iso):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{prov}-{key}.csv"
    if path.exists():
        return path.read_text()
    q = (f'[out:csv("{key}";false)][timeout:180];'
         f'area["ISO3166-2"="{iso}"]->.a;nwr["{key}"](area.a);out;')
    body = urllib.parse.urlencode({"data": q}).encode()
    last = None
    for attempt in range(6):  # de 504s routinely; crawl_overpass needed 6 too
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=200) as r:
                text = r.read().decode("utf-8", "replace")
            path.write_text(text)
            time.sleep(PAUSE)
            return text
        except Exception as e:  # noqa: BLE001 — mirrors 504 routinely; report the last one
            last = e
            time.sleep(PAUSE * (attempt + 2))
    raise SystemExit(f"census: {prov}/{key} failed on both mirrors: {last}")


def requested_selectors():
    """Every key=value pair any GROUPS/WIDE_GROUPS selector asks Overpass for."""
    src = (ROOT / "importers" / "crawl_overpass.py").read_text()
    return set(re.findall(r'nwr\["([a-z_:]+)"="([a-z_;]+)"\]', src))


def main():
    asked = requested_selectors()
    asked_values = {}
    for k, v in asked:
        asked_values.setdefault(k, set()).add(v)
    print(f"selectors in crawl_overpass.py: {len(asked)} key=value pairs\n")
    for key in KEYS:
        tally = Counter()
        for prov, iso in PROVINCES.items():
            text = fetch(key, prov, iso)
            for row in csv.reader(io.StringIO(text)):
                if row and row[0]:
                    tally[row[0]] += 1
        have = asked_values.get(key, set())
        missing = [(v, n) for v, n in tally.most_common() if v not in have and n >= 5]
        print(f"== {key}: {len(tally)} distinct values, "
              f"{len(have)} requested, {len(missing)} unrequested with n>=5")
        for v, n in missing[:25]:
            print(f"   {n:5}  {key}={v}")
        if len(missing) > 25:
            print(f"   ... {len(missing) - 25} more (see cache/census/)")
        print()


if __name__ == "__main__":
    main()
