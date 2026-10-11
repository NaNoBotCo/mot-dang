#!/usr/bin/env python3
"""The Chiang Rai lodging register — 762 names the province wrote down.

WHY THIS EXISTS. The catalogue holds 2,177 lodging records across both
provinces and 2,174 of them come from one place: OpenStreetMap. Measured
2026-09-06 on data/canonical/*.json — 31% carry a phone, 21% an address, 17%
a website, 14% a Thai-script name, 4% opening hours. That is a map's idea of
the hotel trade, not the trade.

Chiang Rai's provincial administration publishes the actual licence roll.
สำนักงานจังหวัดเชียงราย dataset_20_08, sourced to ที่ทำการปกครองจังหวัดเชียงราย
(the DOPA provincial office that issues the licences), in three CSVs:

  _01  the yearly COUNT of ที่พัก, 2560–2565 — a yardstick, not a list
  _02  466 licensed hotels, each with อำเภอ, ตำบล and a licence class 1–4
  _03  296 non-hotel lodgings, each with a free-text ประเภท the province typed

Chiang Mai publishes no equivalent list. Its provincial catalogue carries
counts only (69_158, _67_76 — already harvested as yardsticks by
harvest_datagoth.py), so this file is Chiang Rai and says so in its name. The
Chiang Mai gap is a separate hunt.

WHAT IS TAKEN, and it is less than you would hope. A NAME, an อำเภอ, a ตำบล,
and the register's own word for what the place is. That is every column the
register has. There are no coordinates, no phone numbers, no street addresses,
no room counts and no dates in these files. Do not come back expecting this
importer to fill contacts; it cannot, and a comment promising otherwise would
send somebody hunting for a bug that is not there.

NOTHING IS FILTERED OUT. _03's ประเภท column is free text the province typed by
hand: โฮมสเตย์, ลานกางเต็นท์, บ้านน็อคดาวน์, ที่พักในสวนกาแฟ — and also
ร้านอาหาร, ห้องจัดเลี้ยง, ศูนย์การเรียนรู้, which are not lodging at all. Every
row is passed through with its kind string verbatim and `--report` prints the
tally. Deciding which of those is a place to sleep is the classifier's job
downstream, done in the open, not this file's job done silently. The kind
column is also 80-odd vernacular words for accommodation that no OSM tag holds.

THE LICENCE CLASS IS NOT GLOSSED ON DISK AS FACT. _02's ประเภทที่พัก is the
integer 1–4 and the register never says what those mean. `LICENCE_CLASSES`
below recites the ministerial regulation from memory and is written to the
output with `"verified": false`. It must not reach a page until somebody
fetches กฎกระทรวงฯ พ.ศ. 2551 and reads it. The practice is no statute
recited unfetched.

MANNERS. chiangrai.gdcatalog.go.th asks Crawl-Delay: 10 and disallows /api/,
so the drift guard goes through data.go.th's package_show (which allows /) and
never the provincial API. Twelve seconds between requests, four requests in a
whole run. Snapshot-first into cache/lodging_cr/, so a re-run costs them
nothing and --offline parses what is already down. Announced User-Agent
WITHOUT the word "bot" — the gdcatalog WAF 403s on that substring, measured
2026-08-19 and recorded in harvest_datagoth.py.

ENCODINGS. All three files measured 2026-09-06 as UTF-8 with a BOM. _text()
falls back to cp874/tis-620 anyway, same as harvest_datagoth, because the
Chiang Rai catalogue has served TIS-620 before.

    python3 importers/harvest_lodging_cr.py --dry-run
    python3 importers/harvest_lodging_cr.py
    python3 importers/harvest_lodging_cr.py --offline --report

Output: data/curated/lodging_cr.json — curated, so no crawl overwrites it,
owned wholesale by this file (the enrich.json arrangement), with the dataset
URL, resource URL, publisher and fetch date on every entry.
"""
import argparse
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "lodging_cr")
OUT = os.path.join(ROOT, "data", "curated", "lodging_cr.json")
TODAY = date.today().isoformat()

DATASET = "dataset_20_08"
PKG_SHOW = "https://data.go.th/api/3/action/package_show"
DATASET_PAGE = f"https://data.go.th/dataset/{DATASET}"
UA = "MotDang/1.0 (+https://motdang.net/about.html; 530kings@proton.me)"
DELAY = 12.0          # their robots.txt asks 10
TIMEOUT = 60

PUBLISHER = "สำนักงานจังหวัดเชียงราย"
AUTHORITY = "ที่ทำการปกครองจังหวัดเชียงราย"   # the ที่มา column on every row

# Which resource is which, matched on the filename the province uses. The
# resource UUIDs are NOT hardcoded: package_show is asked every run so a
# re-upload does not silently serve last year's file from a stale URL.
RESOURCES = [
    ("counts", "dataset_20_08_01", "ที่พัก — the yearly count, 2560–2565"),
    ("hotels", "dataset_20_08_02", "ประเภทโรงแรม — the licensed hotels"),
    ("others", "dataset_20_08_03", "ประเภทอื่น ๆ — everything else that lets rooms"),
]

# RECITED, NOT FETCHED. See the module docstring. Written out with
# verified:false so nothing downstream can print it by accident.
LICENCE_CLASSES = {
    "1": "ห้องพักอย่างเดียว / rooms only",
    "2": "ห้องพัก + บริการอาหาร / rooms and food service",
    "3": "ห้องพัก + อาหาร + ห้องประชุมสัมมนา หรือสถานบริการ / rooms, food, and either meetings or a licensed entertainment venue",
    "4": "ห้องพัก + อาหาร + ห้องประชุมสัมมนา + สถานบริการ / rooms, food, meetings and a licensed entertainment venue",
}


# ------------------------------------------------------------------ fetching

def get(url, maxb=6_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(maxb)


def _text(raw):
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def pkg_show(refetch=False, offline=False):
    """The dataset record from data.go.th, cached. The provincial catalogue's
    own /api/ is Disallow: in its robots.txt; this asks data.go.th instead."""
    p = os.path.join(CACHE, f"pkg_{DATASET}.json")
    if os.path.exists(p) and not refetch:
        return json.load(open(p))
    if offline:
        raise SystemExit(f"--offline but no snapshot at {p}; run once online first")
    url = PKG_SHOW + "?" + urllib.parse.urlencode({"id": DATASET})
    doc = json.loads(get(url).decode("utf-8", "replace"))["result"]
    os.makedirs(CACHE, exist_ok=True)
    json.dump(doc, open(p, "w"), ensure_ascii=False)
    time.sleep(DELAY)
    return doc


def pick(doc, frag):
    """The resource whose download URL carries this filename fragment."""
    for r in doc.get("resources", []):
        if frag in (r.get("url") or ""):
            return r
    return None


def snapshot(key, res, refetch=False, offline=False, dry=False):
    """Fetch a CSV once into cache/lodging_cr/<key>.csv and return its rows."""
    p = os.path.join(CACHE, f"{key}.csv")
    if not os.path.exists(p) or refetch:
        if offline:
            raise SystemExit(f"--offline but no snapshot at {p}")
        if dry:
            print(f"  would fetch {res['url']}")
            return []
        raw = get(res["url"])
        os.makedirs(CACHE, exist_ok=True)
        open(p, "wb").write(raw)
        time.sleep(DELAY)
    rows = list(csv.DictReader(_text(open(p, "rb").read()).splitlines()))
    return rows


def col(row, *names):
    """The province's headers carry stray spaces; match on the stripped key."""
    clean = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
    for n in names:
        if n in clean and clean[n]:
            return clean[n]
    return ""


# ------------------------------------------------------------------- parsing

def parse_hotels(rows, res):
    out = []
    for r in rows:
        name = col(r, "ชื่อโรงแรม", "ชื่อสถานประกอบการ")
        if not name:
            continue
        out.append({
            "name": name,
            "province": "cr",
            "amphoe": col(r, "อำเภอ"),
            "tambon": col(r, "ตำบล"),
            "register": "hotel-licence",
            "licenceClass": col(r, "ประเภทที่พัก", "ประเภท") or None,
            "kindTh": None,
            "authority": col(r, "ที่มา") or AUTHORITY,
            "resource_url": res["url"],
            "fetched": TODAY,
        })
    return out


def parse_others(rows, res):
    out = []
    for r in rows:
        name = col(r, "ชื่อโรงแรม", "ชื่อสถานประกอบการ")
        if not name:
            continue
        out.append({
            "name": name,
            "province": "cr",
            "amphoe": col(r, "อำเภอ"),
            "tambon": col(r, "ตำบล"),
            "register": "other-accommodation",
            "licenceClass": None,
            # Verbatim, unjudged. Some of these are not lodging; see the
            # docstring. The classifier decides downstream, in the open.
            "kindTh": col(r, "ประเภท", "ประเภทที่พัก") or None,
            "authority": col(r, "ที่มา") or AUTHORITY,
            "resource_url": res["url"],
            "fetched": TODAY,
        })
    return out


def parse_counts(rows, res):
    out = []
    for r in rows:
        year = col(r, "ปี")
        val = col(r, "ค่าข้อมูล", "จำนวน")
        if not (year and val):
            continue
        out.append({
            "year_be": year,
            "item": col(r, "รายการ"),
            "value": int(val.replace(",", "")) if val.replace(",", "").isdigit() else val,
            "unit": col(r, "หน่วย"),
            "authority": col(r, "ที่มา") or AUTHORITY,
            "resource_url": res["url"],
            "fetched": TODAY,
        })
    return out


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true",
                    help="ask for every file again instead of using snapshots")
    ap.add_argument("--offline", action="store_true",
                    help="parse cache/lodging_cr/ only; make no requests")
    ap.add_argument("--dry-run", action="store_true",
                    help="say what would be fetched and write nothing")
    ap.add_argument("--report", action="store_true",
                    help="print the vernacular kind tally and the amphoe spread")
    args = ap.parse_args()

    doc = pkg_show(refetch=args.refetch, offline=args.offline)
    licence = (doc.get("license_title") or doc.get("license_id") or "").strip()

    records, counts, meta = [], [], {}
    for key, frag, note in RESOURCES:
        res = pick(doc, frag)
        if not res:
            print(f"  !! {frag} not in package_show — the province re-cut the "
                  f"dataset; look at {DATASET_PAGE} before trusting this run")
            continue
        rows = snapshot(key, res, refetch=args.refetch,
                        offline=args.offline, dry=args.dry_run)
        meta[key] = {"note": note, "resource_url": res["url"],
                     "resource_name": res.get("name"), "rows": len(rows),
                     "fetched": TODAY}
        if args.dry_run and not rows:
            continue
        if key == "hotels":
            records += parse_hotels(rows, res)
        elif key == "others":
            records += parse_others(rows, res)
        else:
            counts = parse_counts(rows, res)
        print(f"  {key:7} {len(rows):4} rows  {note}")

    if args.dry_run:
        print("dry run — nothing written")
        return

    out = {
        "_comment":
            "The Chiang Rai provincial lodging register — licensed hotels and "
            "everything else that lets rooms, as ที่ทำการปกครองจังหวัดเชียงราย "
            "wrote them down. Owned wholesale by "
            "importers/harvest_lodging_cr.py (the enrich.json arrangement); "
            "hand-kept truth goes in OTHER curated files. NAME, อำเภอ and "
            "ตำบล only — the register carries no coordinates, phones, "
            "addresses or room counts. kindTh is the province's own free text, "
            "passed through unjudged: some rows are not lodging. Chiang Mai "
            "publishes no equivalent list, only counts.",
        "generated": TODAY,
        "dataset": DATASET,
        "dataset_url": DATASET_PAGE,
        "publisher": PUBLISHER,
        "authority": AUTHORITY,
        "licence": licence or None,
        "sources": meta,
        "licence_classes": {
            "_comment": "RECITED FROM MEMORY, NOT FETCHED. The register gives "
                        "the integer only. Do not print this until somebody "  # stylecheck: allow — operator note
                        "fetches กฎกระทรวงกำหนดประเภทและหลักเกณฑ์การประกอบ"
                        "ธุรกิจโรงแรม พ.ศ. 2551 and reads it.",
            "verified": False,
            "classes": LICENCE_CLASSES,
        },
        "counts": counts,
        "records": records,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(records)} lodgings, "
          f"{len(counts)} count rows)")

    if args.report:
        import collections
        hot = [r for r in records if r["register"] == "hotel-licence"]
        oth = [r for r in records if r["register"] == "other-accommodation"]
        print(f"\nlicensed hotels {len(hot)} · other accommodation {len(oth)}")
        print("licence class:",
              collections.Counter(r["licenceClass"] for r in hot).most_common())
        print(f"amphoe: {len({r['amphoe'] for r in records})} distinct")
        print("\nthe province's own words for a place to sleep "
              "(verbatim, unjudged):")
        for k, n in collections.Counter(
                r["kindTh"] for r in oth if r["kindTh"]).most_common():
            print(f"  {n:3}  {k}")


if __name__ == "__main__":
    main()
